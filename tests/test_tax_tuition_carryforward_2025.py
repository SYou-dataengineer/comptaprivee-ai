from dataclasses import replace
from decimal import Decimal as D
import json
import fitz
import pytest
from src.comptaprivee.tax_tuition_carryforward_2025 import (
    ReportsScolariteFederaux2025, CONFIRMATIONS_REPORTS_SCOLARITE,
    calculer_reports_scolarite_federaux_2025, valider_reports_scolarite_federaux_2025,
)
from src.comptaprivee.tax_tuition_2025 import FraisScolarite2025, valider_frais_scolarite_2025, credit_federal_frais_scolarite_2025
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calcul
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from tests.test_tax_tuition_integration_2025 import _scolarite_3000
from tests.test_tax_workers_benefit_2025 import dossier_20000
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_top_up_integration_2025 import verifier_t1


def profil(**kw):
    v = dict(activer=True, report_avis_2024=D(1000), source="Avis ARC 2024 et rapprochement fictifs",
             **{nom: True for nom in CONFIRMATIONS_REPORTS_SCOLARITE})
    v.update(kw)
    return ReportsScolariteFederaux2025(**v)


def frais(**kw):
    return replace(_scolarite_3000(), montant_admissible_quebec=D(0),
                   aucun_report_anterieur=False, reports_federaux=profil(**kw))


def montant(p=None, **kw):
    v = dict(frais_nets_2025=D(3000), revenu_imposable=D(20000), impot_brut=D(2900), base_ligne105=D(19000))
    v.update(kw)
    return calculer_reports_scolarite_federaux_2025(p or profil(), **v)


def test_vide_priorite_et_reports():
    assert montant(ReportsScolariteFederaux2025()).ligne_32300 == 0
    r = montant()
    assert r.report_anterieur_utilise == D(1000)
    assert r.frais_2025_utilises == 0
    assert r.report_futur == D(3000)
    r = montant(base_ligne105=D(18000))
    assert r.report_anterieur_utilise == r.frais_2025_utilises == D(1000)
    assert r.report_futur == D(2000)
    assert montant(base_ligne105=D(21000)).report_futur == D(4000)


def test_capacite_premiere_tranche_et_suivante():
    assert montant(revenu_imposable=D(57375), base_ligne105=D(50000)).capacite_annexe11 == D(7375)
    assert montant(revenu_imposable=D(70000), impot_brut=D("10907.51"), base_ligne105=D(50000)).capacite_annexe11 == D("25224.21")


def test_report_seul_et_utilisation_complete():
    r = montant(frais_nets_2025=D(0), base_ligne105=D(0))
    assert r.ligne_32300 == D(1000)
    assert r.report_futur == 0
    assert montant(base_ligne105=D(0)).ligne_32300 == D(4000)


@pytest.mark.parametrize("valeur", [D(-1), D("NaN"), D("sNaN"), D("Infinity"), D("-Infinity"), D("1.001"), 1.5, "5"])
def test_report_invalide(valeur):
    with pytest.raises(ValueError):
        montant(profil(report_avis_2024=valeur))


@pytest.mark.parametrize("champ", ["frais_nets_2025", "revenu_imposable", "impot_brut", "base_ligne105"])
@pytest.mark.parametrize("valeur", [D(-1), D("NaN"), D("Infinity"), "5"])
def test_operandes_invalides(champ, valeur):
    with pytest.raises(ValueError):
        montant(**{champ: valeur})


@pytest.mark.parametrize("nom", list(CONFIRMATIONS_REPORTS_SCOLARITE))
def test_confirmations_obligatoires(nom):
    for valeur in (False, "true"):
        with pytest.raises(ValueError):
            montant(profil(**{nom: valeur}))


def test_activation_source_et_contradictions():
    for kw in ({"activer": False}, {"activer": "true"}, {"source": ""}, {"source": None}):
        with pytest.raises(ValueError):
            montant(profil(**kw))
    with pytest.raises(ValueError, match="contradictoire"):
        valider_frais_scolarite_2025(replace(frais(), aucun_report_anterieur=True))
    with pytest.raises(ValueError, match="annexe 11"):
        credit_federal_frais_scolarite_2025(frais())


def test_estimation_ancien_guard_et_nouveau_report():
    d = dossier_20000()
    with pytest.raises(ValueError, match="report"):
        calcul(d, frais_scolarite=replace(_scolarite_3000(), montant_admissible_quebec=D(0)))
    e = calcul(d, frais_scolarite=frais())
    r = e.resultat_reports_scolarite
    assert r.capacite_annexe11 == D("983.20")
    assert r.report_anterieur_utilise == D("983.20")
    assert r.frais_2025_utilises == 0
    assert r.report_futur == D("3016.80")
    assert dict(e.federal.credits_federaux_complets.montants_par_ligne)["32300"] == D("983.20")
    assert e.federal.impot_federal_de_base == 0
    assert e.revenu == calcul(d).revenu
    verifier_t1(e)


def test_ancien_json_report_seul_stockage_et_divergence(tmp_path):
    f = FraisScolarite2025(reports_federaux=profil(report_avis_2024=D(500)))
    e = calcul(_dossier_52000(), frais_scolarite=f)
    assert e.resultat_reports_scolarite.ligne_32300 == D(500)
    fichier = sauvegarder_dossier_fiscal(e.dossier, estimation=e, destination=tmp_path / "cas.json")
    c = charger_dossier_fiscal(fichier)
    assert c.frais_scolarite == f
    assert calcul(c.dossier, frais_scolarite=c.frais_scolarite) == e
    contenu = json.loads(fichier.read_text(encoding="utf-8"))
    assert contenu["frais_scolarite"]["reports_federaux"]["report_avis_2024"] == "500.00"
    assert "report_futur" not in contenu["frais_scolarite"]["reports_federaux"]
    with pytest.raises(ValueError, match="diffère"):
        sauvegarder_dossier_fiscal(e.dossier, estimation=e, frais_scolarite=FraisScolarite2025(), destination=tmp_path / "refus.json")
    del contenu["frais_scolarite"]["reports_federaux"]
    fichier.write_text(json.dumps(contenu), encoding="utf-8")
    assert charger_dossier_fiscal(fichier).frais_scolarite.reports_federaux == ReportsScolariteFederaux2025()


@pytest.mark.parametrize("valeur", [{"inconnu": 1}, {"activer": "true"}, {"report_avis_2024": "NaN"}, []])
def test_json_invalide(tmp_path, valeur):
    f = sauvegarder_dossier_fiscal(_dossier_52000(), destination=tmp_path / "cas.json")
    contenu = json.loads(f.read_text(encoding="utf-8"))
    contenu["frais_scolarite"]["reports_federaux"] = valeur
    f.write_text(json.dumps(contenu), encoding="utf-8")
    with pytest.raises(ValueError):
        charger_dossier_fiscal(f)


def test_report_frais_courants_apres_formation():
    from tests.test_tax_training_credit_2025 import frais as formation
    p = replace(formation(), reports_federaux=profil(report_avis_2024=D(100000)), aucun_report_anterieur=False)
    e = calcul(_dossier_52000(), frais_scolarite=p)
    r = e.resultat_reports_scolarite
    assert r.frais_2025_nets == D(2250)
    assert r.frais_2025_utilises == 0
    assert r.report_futur == D(102250) - r.report_anterieur_utilise
    assert e.rapprochement.credit_formation_ligne_45350 == D(750)
    verifier_t1(e)


def test_trace_pdf_utilise_et_report(tmp_path):
    e = calcul(dossier_20000(), frais_scolarite=frais())
    trace = construire_trace_calcul_fiscal_2025(e)
    assert next(x for x in trace.lignes if x.libelle == "Scolarité réclamée 32300").montant == D("983.20")
    assert next(x for x in trace.lignes if x.libelle == "Report scolarité fédéral futur").montant == D("3016.80")
    assert [x.ordre for x in trace.lignes] == list(range(1, len(trace.lignes) + 1))
    f = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "reports.pdf")
    with fitz.open(f) as pdf:
        texte = "\n".join(page.get_text() for page in pdf)
        for page in pdf:
            for x0, y0, x1, y1, *_ in page.get_text("blocks"):
                assert 0 <= x0 < x1 <= page.rect.width
                assert 0 <= y0 < y1 <= page.rect.height
    assert "Ligne 32300 : 983.20" in texte
    assert "Report fédéral futur calculé : 3016.80" in texte
