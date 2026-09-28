from dataclasses import replace
from decimal import Decimal as D
import json
import fitz
import pytest
from src.comptaprivee.tax_donation_carryforward_2025 import (
    ReportDonFederal2025 as Report, ReportsDonsFederaux2025, CONFIRMATIONS_REPORTS_DONS,
    valider_reports_dons_federaux_2025, calculer_reports_dons_federaux_2025,
)
from src.comptaprivee.tax_donations_2025 import DonsBienfaisance2025, valider_dons_bienfaisance_2025, credit_federal_dons_2025
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calcul
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from tests.test_tax_donations_2025 import _dons_valides
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_top_up_integration_2025 import verifier_t1


def profil(**kw):
    v = dict(activer=True, reports=(Report(2024, D(1000), "Reçus 2024 fictifs"), Report(2020, D(1000), "Reçus 2020 fictifs")),
        montant_reclame=D(1500), source="Choix comptable fictif", **{nom: True for nom in CONFIRMATIONS_REPORTS_DONS})
    v.update(kw)
    return ReportsDonsFederaux2025(**v)


def dons(**kw):
    return replace(_dons_valides(), aucun_report_anterieur=False, reports_federaux=profil(**kw))


def repartir(p=None, courant="1000", net="50000"):
    return calculer_reports_dons_federaux_2025(p or profil(), dons_2025=D(courant), revenu_net=D(net))


def test_priorite_anciens_et_report_par_annee():
    r = repartir()
    assert r.disponible == D(3000)
    assert r.plafond_75 == D(37500)
    assert r.utilisations == ((2020, D(1000)), (2024, D(500)))
    assert r.reports_futurs == ((2024, D(500)), (2025, D(1000)))
    assert r.expiration_2020 == 0
    assert r.disponible == r.montant_reclame + sum((x[1] for x in r.reports_futurs), D(0)) + r.expiration_2020


def test_expiration_2020_choix_zero_et_partiel():
    r = repartir(profil(montant_reclame=D(0)))
    assert r.utilisations == () and r.expiration_2020 == D(1000)
    assert r.reports_futurs == ((2024, D(1000)), (2025, D(1000)))
    r = repartir(profil(montant_reclame=D("999.99")))
    assert r.expiration_2020 == D("0.01")
    assert r.utilisations == ((2020, D("999.99")),)
    assert repartir(profil(montant_reclame=D(3000))).reports_futurs == ()


def test_plafond_disponible_net_zero_et_vide():
    assert repartir(ReportsDonsFederaux2025()).disponible == 0
    assert repartir(profil(montant_reclame=D(0)), net="0").plafond_75 == 0
    assert repartir(profil(montant_reclame=D(750)), net="1000").montant_reclame == D(750)
    for p, net in ((profil(montant_reclame=D("750.01")), "1000"),
                   (profil(montant_reclame=D("3000.01")), "50000")):
        with pytest.raises(ValueError, match="dépasse"):
            repartir(p, net=net)


@pytest.mark.parametrize("nom", CONFIRMATIONS_REPORTS_DONS)
@pytest.mark.parametrize("valeur", [False, "true"])
def test_confirmations(nom, valeur):
    with pytest.raises(ValueError):
        repartir(profil(**{nom: valeur}))


@pytest.mark.parametrize("valeur", [D(-1), D("NaN"), D("sNaN"), D("Infinity"), D("-Infinity"), D("1.001"), D("1e100"), "1", 1.0, True])
@pytest.mark.parametrize("champ", ["montant_reclame", "report"])
def test_montants_invalides(champ, valeur):
    p = profil(montant_reclame=valeur) if champ == "montant_reclame" else profil(reports=(Report(2020, valeur, "Source"),))
    with pytest.raises(ValueError):
        repartir(p)


@pytest.mark.parametrize("annee", [2019, 2025, True, "2024", 2024.0])
def test_annees_invalides(annee):
    with pytest.raises(ValueError):
        repartir(profil(reports=(Report(annee, D(1000), "Source"),)))


@pytest.mark.parametrize("reports", [(Report(2020, D(1), "a"), Report(2020, D(2), "b")), (None,), [], (Report(2020, D(0), "a"),), (Report(2020, D(1), " "),)])
def test_reports_invalides(reports):
    with pytest.raises(ValueError):
        repartir(profil(reports=reports))


def test_activation_sources_contradictions():
    for p in (profil(activer=False), profil(activer="true"), profil(source=" "), profil(source=None)):
        with pytest.raises(ValueError):
            repartir(p)
    with pytest.raises(ValueError, match="contradictoire"):
        valider_dons_bienfaisance_2025(replace(dons(), aucun_report_anterieur=True))
    with pytest.raises(ValueError, match="disponibles"):
        credit_federal_dons_2025(dons(montant_reclame=D(3001)), D(52000))


@pytest.mark.parametrize("valeur", [D(-1), D("NaN"), D("Infinity"), "500", 500.0])
def test_revenu_invalide(valeur):
    with pytest.raises(ValueError):
        calculer_reports_dons_federaux_2025(profil(), dons_2025=D(1000), revenu_net=valeur)


def test_estimation_choix_pas_double_application_quebec_inchange():
    avant = calcul(_dossier_52000(), dons_bienfaisance=_dons_valides())
    e = calcul(_dossier_52000(), dons_bienfaisance=dons())
    c = e.federal.credits_federaux_complets
    assert c.credit_dons_ligne_34900 == D(406)
    assert c.annexe9_ligne22 == D(29)
    assert e.revenu == avant.revenu and e.quebec == avant.quebec
    assert e.dons_bienfaisance.montant_admissible_federal == D(1000)
    assert e.resultat_reports_dons.plafond_75 == D("38636.25")
    verifier_t1(e)
    zero = calcul(_dossier_52000(), dons_bienfaisance=dons(montant_reclame=D(0)))
    assert zero.federal.credits_federaux_complets.credit_dons_ligne_34900 == 0
    assert zero.federal.credits_federaux_complets.annexe9_ligne22 == 0
    assert zero.quebec == e.quebec


def test_dons_courants_superieurs_plafond_reportables_et_reer_reduit_plafond():
    from tests.test_tax_donations_integration_2025 import _reer_5000
    f = replace(_dons_valides("40000"), montant_admissible_quebec=D(0), reports_federaux=profil(reports=(), montant_reclame=D("38636.25")))
    e = calcul(_dossier_52000(), dons_bienfaisance=f)
    assert e.resultat_reports_dons.reports_futurs == ((2025, D("1363.75")),)
    with pytest.raises(ValueError, match="75 %"):
        calcul(_dossier_52000(), dons_bienfaisance=f, ajustement_reer=_reer_5000())


def test_report_seul_stockage_recalcul_ancien_json_et_divergence(tmp_path):
    d = DonsBienfaisance2025(reports_federaux=profil())
    e = calcul(_dossier_52000(), dons_bienfaisance=d)
    assert e.federal.credits_federaux_complets.credit_dons_ligne_34900 == D(406)
    f = sauvegarder_dossier_fiscal(e.dossier, estimation=e, destination=tmp_path / "cas.json")
    c = charger_dossier_fiscal(f)
    assert c.dons_bienfaisance == d
    assert calcul(c.dossier, dons_bienfaisance=c.dons_bienfaisance) == e
    brut = json.loads(f.read_text(encoding="utf-8"))
    p = brut["dons_bienfaisance"]["reports_federaux"]
    assert p["montant_reclame"] == "1500.00" and p["reports"][0]["montant"] == "1000.00"
    assert "reports_futurs" not in p
    with pytest.raises(ValueError, match="diffère"):
        sauvegarder_dossier_fiscal(e.dossier, estimation=e, dons_bienfaisance=DonsBienfaisance2025(), destination=tmp_path / "refus.json")
    del brut["dons_bienfaisance"]["reports_federaux"]
    f.write_text(json.dumps(brut), encoding="utf-8")
    assert charger_dossier_fiscal(f).dons_bienfaisance.reports_federaux == ReportsDonsFederaux2025()


@pytest.mark.parametrize("valeur", [[], {"inconnu": 1}, {"activer": "true"}, {"montant_reclame": "NaN"}, {"reports": {}}, {"reports": [{"annee": 2020, "montant": "1", "source": "a", "credit": "2"}]}])
def test_json_invalide(tmp_path, valeur):
    f = sauvegarder_dossier_fiscal(_dossier_52000(), destination=tmp_path / "cas.json")
    brut = json.loads(f.read_text(encoding="utf-8"))
    brut["dons_bienfaisance"]["reports_federaux"] = valeur
    f.write_text(json.dumps(brut), encoding="utf-8")
    with pytest.raises(ValueError):
        charger_dossier_fiscal(f)


def test_trace_pdf_report_seul(tmp_path):
    e = calcul(_dossier_52000(), dons_bienfaisance=DonsBienfaisance2025(reports_federaux=profil(montant_reclame=D(500))))
    trace = construire_trace_calcul_fiscal_2025(e)
    assert next(x for x in trace.lignes if x.libelle == "Dons 2020 expirant après 2025").montant == D(500)
    assert next(x for x in trace.lignes if x.libelle == "Crédit fédéral pour dons").montant == D(116)
    assert [x.ordre for x in trace.lignes] == list(range(1, len(trace.lignes) + 1))
    f = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "cas.pdf")
    with fitz.open(f) as pdf:
        texte = "\n".join(p.get_text() for p in pdf)
        for p in pdf:
            for x0, y0, x1, y1, *_ in p.get_text("blocks"):
                assert 0 <= x0 < x1 <= p.rect.width
                assert 0 <= y0 < y1 <= p.rect.height
    assert "ligne 34900 : 116.00" in texte
    assert "Dons 2024 reportables après 2025 : 1000.00" in texte
    assert "Solde 2020 expirant après 2025, non reportable : 500.00" in texte
    assert "Reçus 2020 fictifs" in texte


def test_compensation_recalculee_sur_dons_reclames_seulement():
    from tests.test_tax_federal_top_up_integration_2025 import dossier_70000, medical
    zero = calcul(dossier_70000(), frais_medicaux=medical(), dons_bienfaisance=dons(montant_reclame=D(0)))
    cent = calcul(dossier_70000(), frais_medicaux=medical(), dons_bienfaisance=dons(montant_reclame=D(100)))
    c = cent.federal.credits_federaux_complets
    assert c.annexe9_ligne22 == D("14.50")
    assert c.credit_dons_ligne_34900 == D("14.50")
    assert c.credit_compensatoire_ligne_34990 > zero.federal.credits_federaux_complets.credit_compensatoire_ligne_34990 > 0
    verifier_t1(zero)
    verifier_t1(cent)


def test_janvier_fevrier_deja_reclame_refuse_avec_reports():
    with pytest.raises(ValueError, match="2024"):
        calcul(_dossier_52000(), dons_bienfaisance=replace(dons(), inclut_dons_jan_fev_2025=True, dons_jan_fev_deja_reclames_2024=True))


@pytest.mark.parametrize("valeur", [D("NaN"), D("Infinity"), D(-1), D("1.001")])
def test_dons_courants_invalides(valeur):
    with pytest.raises(ValueError):
        calculer_reports_dons_federaux_2025(profil(), dons_2025=valeur, revenu_net=D(50000))
