from dataclasses import replace
from decimal import Decimal as D
import json
import fitz
import pytest

from src.comptaprivee.tax_training_credit_2025 import (
    Formation2025, CONFIRMATIONS_FORMATION, credit_formation_2025, valider_formation_2025,
)
from src.comptaprivee.tax_tuition_2025 import FraisScolarite2025, valider_frais_scolarite_2025
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calcul
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from tests.test_tax_tuition_integration_2025 import _scolarite_3000
from tests.test_tax_estimation_2025 import _dossier_52000


def profil(**kw):
    valeurs = dict(frais_canadiens=D(3000), plafond_avis_2025=D(750), age_fin_2025=35,
                   source="T2202 et avis ARC 2024, plafond 2025", reclamer_maximum=True,
                   **{nom: True for nom in CONFIRMATIONS_FORMATION})
    valeurs.update(kw)
    return Formation2025(**valeurs)


def frais(**kw):
    return replace(_scolarite_3000(), formation=profil(**kw), credit_canadien_formation_non_reclame=False)


def test_vide_et_choix_de_ne_pas_reclamer():
    assert credit_formation_2025(Formation2025()) == 0
    assert credit_formation_2025(profil(reclamer_maximum=False)) == 0


@pytest.mark.parametrize("age", [26, 65])
def test_ages_admissibles(age):
    assert credit_formation_2025(profil(age_fin_2025=age)) == D(750)


@pytest.mark.parametrize("age", [25, 66, -1, 121, True, "35"])
def test_ages_refuses(age):
    with pytest.raises(ValueError):
        credit_formation_2025(profil(age_fin_2025=age))


@pytest.mark.parametrize("champ", ["frais_canadiens", "plafond_avis_2025"])
@pytest.mark.parametrize("montant", [D(-1), D("NaN"), D("sNaN"), D("Infinity"), D("-Infinity"), D("1.001"), 1.5, "5"])
def test_montants_invalides(champ, montant):
    with pytest.raises(ValueError):
        credit_formation_2025(profil(**{champ: montant}))


@pytest.mark.parametrize("nom", list(CONFIRMATIONS_FORMATION))
def test_confirmations(nom):
    for valeur in (False, "true"):
        with pytest.raises(ValueError):
            credit_formation_2025(profil(**{nom: valeur}))


@pytest.mark.parametrize("source", ["", "  ", None])
def test_source_obligatoire(source):
    with pytest.raises(ValueError):
        valider_formation_2025(profil(source=source))


def test_plafond_et_arrondi():
    assert credit_formation_2025(profil(frais_canadiens=D("1000.01"))) == D("500.01")
    assert credit_formation_2025(profil(plafond_avis_2025=D(1500))) == D(1500)
    with pytest.raises(ValueError):
        credit_formation_2025(profil(plafond_avis_2025=D("1500.01")))


def test_frais_bruts_et_confirmations_coherentes():
    with pytest.raises(ValueError, match="contradictoire"):
        valider_frais_scolarite_2025(replace(frais(), credit_canadien_formation_non_reclame=True))
    with pytest.raises(ValueError, match="frais fédéraux"):
        valider_frais_scolarite_2025(frais(frais_canadiens=D(4000)))
    with pytest.raises(ValueError, match="Québec"):
        valider_frais_scolarite_2025(replace(frais(), montant_admissible_quebec=D(0)))


def test_estimation_sans_double_comptage_et_anciens_resultats():
    d = _dossier_52000()
    ancien = calcul(d, frais_scolarite=_scolarite_3000())
    e = calcul(d, frais_scolarite=frais())
    assert e.revenu == ancien.revenu
    assert e.frais_scolarite.montant_admissible_federal == D(3000)
    assert e.frais_scolarite.montant_net_federal == e.frais_scolarite.montant_net_quebec == D(2250)
    c = e.federal.credits_federaux_complets
    assert dict(c.montants_par_ligne)["32300"] == D(2250)
    assert "45350" not in dict(c.montants_par_ligne)
    assert ancien.federal.credits_federaux_complets.credit_ligne_33800 - c.credit_ligne_33800 == D("108.75")
    assert e.quebec.impot_quebec_preliminaire - ancien.quebec.impot_quebec_preliminaire == D(60)
    r = e.rapprochement
    assert r.credit_formation_ligne_45350 == D(750)
    assert r.remboursement_estime - r.solde_estime == r.retenues_totales + r.remboursements_cotisations_totaux + D(750) - r.impot_total_preliminaire
    assert r.abattement_quebec == (e.federal.impot_federal_de_base * D(".165")).quantize(D(".01"))
    assert calcul(d) == calcul(d, frais_scolarite=FraisScolarite2025())


def test_remboursable_meme_sans_impot():
    from src.comptaprivee.tax_reconciliation_2025 import calculer_rapprochement_fiscal_2025
    e = calcul(_dossier_52000())
    r = calculer_rapprochement_fiscal_2025(e.base, replace(e.federal, impot_federal_de_base=D(0)),
        replace(e.quebec, impot_quebec_preliminaire=D(0)), credit_formation=D(750))
    assert r.remboursement_estime == r.retenues_totales + D(750)


def test_stockage_brut_recalcul_ancien_divergence(tmp_path):
    e = calcul(_dossier_52000(), frais_scolarite=frais())
    f = sauvegarder_dossier_fiscal(e.dossier, estimation=e, destination=tmp_path / "cas.json")
    charge = charger_dossier_fiscal(f)
    assert charge.frais_scolarite == e.frais_scolarite
    assert calcul(charge.dossier, frais_scolarite=charge.frais_scolarite) == e
    contenu = json.loads(f.read_text(encoding="utf-8"))
    assert contenu["frais_scolarite"]["formation"]["plafond_avis_2025"] == "750.00"
    with pytest.raises(ValueError, match="diffère"):
        sauvegarder_dossier_fiscal(e.dossier, estimation=e, frais_scolarite=_scolarite_3000(), destination=tmp_path / "refus.json")
    del contenu["frais_scolarite"]["formation"]
    contenu["frais_scolarite"]["credit_canadien_formation_non_reclame"] = True
    f.write_text(json.dumps(contenu), encoding="utf-8")
    assert charger_dossier_fiscal(f).frais_scolarite.formation == Formation2025()


@pytest.mark.parametrize("valeur", [{"inconnu": 1}, {"reclamer_maximum": "true"}, {"frais_canadiens": "NaN"}, {"age_fin_2025": "35"}, []])
def test_json_formation_invalide(tmp_path, valeur):
    f = sauvegarder_dossier_fiscal(_dossier_52000(), destination=tmp_path / "cas.json")
    contenu = json.loads(f.read_text(encoding="utf-8"))
    contenu["frais_scolarite"]["formation"] = valeur
    f.write_text(json.dumps(contenu), encoding="utf-8")
    with pytest.raises(ValueError):
        charger_dossier_fiscal(f)


def test_trace_pdf(tmp_path):
    e = calcul(_dossier_52000(), frais_scolarite=frais())
    trace = construire_trace_calcul_fiscal_2025(e)
    ligne = next(x for x in trace.lignes if x.libelle == "Crédit formation remboursable 45350")
    assert ligne.montant == D(750)
    assert "45350" in trace.formule_resultat
    assert [x.ordre for x in trace.lignes] == list(range(1, len(trace.lignes) + 1))
    f = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "formation.pdf")
    with fitz.open(f) as pdf:
        texte = "\n".join(page.get_text() for page in pdf)
        for page in pdf:
            for x0, y0, x1, y1, *_ in page.get_text("blocks"):
                assert 0 <= x0 < x1 <= page.rect.width
                assert 0 <= y0 < y1 <= page.rect.height
    assert "Ligne 45350 remboursable : 750.00" in texte
    assert "T2202 et avis ARC" in texte


def test_net_inferieur_100_ne_reapplique_pas_seuil_sur_net():
    p = replace(frais(frais_canadiens=D(150)), montant_admissible_federal=D(150), montant_admissible_quebec=D(150))
    e = calcul(_dossier_52000(), frais_scolarite=p)
    assert e.frais_scolarite.montant_net_federal == D(75)
    assert dict(e.federal.credits_federaux_complets.montants_par_ligne)["32300"] == D(75)


def test_formation_recalcule_34990():
    from tests.test_tax_federal_top_up_integration_2025 import dossier_70000, medical, verifier_t1
    d = dossier_70000()
    avant = calcul(d, frais_scolarite=_scolarite_3000(), frais_medicaux=medical("35000"))
    apres = calcul(d, frais_scolarite=frais(), frais_medicaux=medical("35000"))
    assert avant.federal.top_up_credit > apres.federal.top_up_credit
    assert apres.rapprochement.credit_formation_ligne_45350 == D(750)
    verifier_t1(apres)


def test_formation_et_40500():
    from tests.test_tax_foreign_investment_2025 import dossier, profil as etranger, profil_credit
    from tests.test_tax_federal_top_up_integration_2025 import verifier_t1
    e = calcul(dossier("10000", "1500", emploi=True), frais_scolarite=frais(),
               profil_placement_etranger=etranger(), profil_credit_impot_etranger=profil_credit("1000", "0"))
    verifier_t1(e)
    assert e.rapprochement.credit_formation_ligne_45350 == D(750)


def test_scolarite_report_necessaire_reste_refuse():
    with pytest.raises(ValueError, match="report"):
        calcul(_dossier_52000(), frais_scolarite=replace(frais(), montant_admissible_federal=D(100000)))
