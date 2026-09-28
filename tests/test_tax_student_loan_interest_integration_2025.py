from dataclasses import replace
from decimal import Decimal as D
import json

import fitz
import pytest

from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calcul, formater_estimation_fiscale_2025
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from src.comptaprivee.tax_student_loan_interest_2025 import InteretsPretEtudiant2025
from tests.test_tax_student_loan_interest_2025 import profil
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_top_up_integration_2025 import dossier_70000, medical, verifier_t1


def test_sans_31900_historique_inchange():
    sans = calcul(_dossier_52000())
    assert sans == calcul(_dossier_52000(), interets_pret_etudiant=InteretsPretEtudiant2025())
    assert sans.rapprochement.impot_total_preliminaire == D("8088.95")
    assert sans.federal.impot_federal_de_base == D("4401.90")
    assert "31900" not in dict(sans.federal.credits_federaux_complets.montants_par_ligne)


def test_31900_unique_et_revenus_inchanges():
    sans = calcul(_dossier_52000())
    avec = calcul(_dossier_52000(), interets_pret_etudiant=profil())
    assert avec.revenu == sans.revenu  # total, net, imposable des deux juridictions
    assert avec.quebec == sans.quebec
    c = avec.federal.credits_federaux_complets
    assert c.base_ligne_33500 == D("22157.08")
    assert c.credit_ligne_33800 == c.total_credits_ligne_35000 == D("3212.78")
    assert c.credit_compensatoire_ligne_34990 == 0
    assert avec.federal.impot_federal_de_base == D("4256.90")
    assert avec.rapprochement.abattement_quebec == D("702.39")
    assert avec.resultat_interets_pret_etudiant.reduction_42900 == D(145)
    assert sans.rapprochement.impot_total_preliminaire - avec.rapprochement.impot_total_preliminaire == D("121.08")
    assert avec.resultat_interets_pret_etudiant.reduction_federale_apres_40500_et_abattement == D("121.08")
    verifier_t1(avec)


def test_31900_declenche_34990_exactement():
    d = dossier_70000()
    sans = calcul(d, frais_medicaux=medical("35000"))
    avec = calcul(d, frais_medicaux=medical("35000"), interets_pret_etudiant=profil(interets_payes_2025=D(3000), montant_reclame_31900=D(3000)))
    assert sans.federal.credits_federaux_complets.credit_ligne_33800 == D("8021.03")
    assert sans.federal.top_up_credit == 0
    c = avec.federal.credits_federaux_complets
    assert c.credit_ligne_33800 == D("8456.03")
    assert c.credit_compensatoire_ligne_34990 == D("4.71")
    assert c.total_credits_ligne_35000 == D("8460.74")
    assert avec.federal.impot_federal_de_base == D("2310.44")
    assert avec.resultat_interets_pret_etudiant.augmentation_35000 == D("439.71")
    assert avec.revenu == sans.revenu
    verifier_t1(avec)


def test_scolarite_ligne105_non_modifiee_par_31900():
    from tests.test_tax_tuition_integration_2025 import _scolarite_3000
    options = dict(frais_scolarite=replace(_scolarite_3000(), montant_admissible_quebec=D(0)))
    sans = calcul(_dossier_52000(), **options)
    avec = calcul(_dossier_52000(), interets_pret_etudiant=profil(), **options)
    assert dict(avec.federal.credits_federaux_complets.montants_par_ligne)["32300"] == D(3000)
    assert sans.federal.impot_federal_de_base - avec.federal.impot_federal_de_base == D(145)


@pytest.mark.parametrize("demande", ["0", "100", "1000"])
def test_40500_reste_apres_42900(demande):
    from tests.test_tax_foreign_investment_2025 import dossier, profil as etranger, profil_credit
    # Le module crédit étranger garde ses propres validations d'admissibilité.
    options = dict(profil_placement_etranger=etranger(), profil_credit_impot_etranger=profil_credit(demande, "0"))
    d = dossier("10000", "1500", emploi=True)
    sans = calcul(d, **options)
    e = calcul(d, interets_pret_etudiant=profil(), **options)
    verifier_t1(e)
    assert e.federal.impot_federal_de_base == D("5955.30")
    assert e.rapprochement.abattement_quebec == D("982.62")
    assert sans.rapprochement.impot_total_preliminaire - e.rapprochement.impot_total_preliminaire == e.resultat_interets_pret_etudiant.reduction_federale_apres_40500_et_abattement


def test_impot_nul_ne_consomme_pas_reports_automatiquement():
    p = profil(montant_reclame_31900=D(0), reports=((2020, D(200)), (2024, D(300))))
    e = calcul(_dossier_52000(), frais_medicaux=medical("100000"), interets_pret_etudiant=p)
    assert e.federal.impot_federal_de_base == 0
    r = e.resultat_interets_pret_etudiant
    assert r.utilises_par_annee == ()
    assert r.non_reclames_par_annee == ((2020, D(200)), (2024, D(300)), (2025, D(1000)))
    assert r.non_reclames_encore_reportables_2026 == D(1300)
    assert e.interets_pret_etudiant == p


def test_reclamation_sans_credit_utilisable_est_explicite():
    e = calcul(_dossier_52000(), frais_medicaux=medical("100000"), interets_pret_etudiant=profil())
    r = e.resultat_interets_pret_etudiant
    assert r.ligne_31900 == D(1000)
    assert r.augmentation_35000 > 0
    assert r.reduction_42900 == 0
    assert e.interets_pret_etudiant.interets_payes_2025 == D(1000)
    assert "gaspiller" in formater_estimation_fiscale_2025(e)


def test_json_roundtrip_et_ancien(tmp_path):
    p = profil(reports=((2020, D(300)), (2024, D(500))))
    e = calcul(_dossier_52000(), interets_pret_etudiant=p)
    fichier = sauvegarder_dossier_fiscal(e.dossier, estimation=e, destination=tmp_path / "d.json")
    contenu = json.loads(fichier.read_text(encoding="utf-8"))
    assert contenu["interets_pret_etudiant"]["interets_payes_2025"] == "1000.00"
    charge = charger_dossier_fiscal(fichier)
    assert calcul(charge.dossier, interets_pret_etudiant=charge.interets_pret_etudiant) == e
    del contenu["interets_pret_etudiant"]
    fichier.write_text(json.dumps(contenu), encoding="utf-8")
    assert charger_dossier_fiscal(fichier).interets_pret_etudiant == InteretsPretEtudiant2025()
    with pytest.raises(ValueError, match="diffère"):
        sauvegarder_dossier_fiscal(e.dossier, estimation=e, interets_pret_etudiant=InteretsPretEtudiant2025(), destination=tmp_path / "refus.json")
    assert not (tmp_path / "refus.json").exists()


@pytest.mark.parametrize("invalide", [
    {"inconnu": 1}, {"report_2019": "50"}, {"interets_payes_2025": "NaN"},
    {"reports": [{"annee": 2019, "montant": "50"}]},
    {"reports": [{"annee": 2020, "montant": "50", "inconnu": 1}]},
    {"reports": "2020"}, {"valide_par_comptable": "true"},
    {"interets_payes_2025": "50"}, {"montant_reclame_31900": "-1"},
])
def test_json_invalide_refuse(tmp_path, invalide):
    f = sauvegarder_dossier_fiscal(_dossier_52000(), destination=tmp_path / "d.json")
    contenu = json.loads(f.read_text(encoding="utf-8"))
    contenu["interets_pret_etudiant"] = invalide
    f.write_text(json.dumps(contenu), encoding="utf-8")
    with pytest.raises(ValueError):
        charger_dossier_fiscal(f)


def test_trace_pdf_et_resume(tmp_path):
    e = calcul(_dossier_52000(), interets_pret_etudiant=profil(reports=((2020, D(300)), (2024, D(500)))))
    trace = construire_trace_calcul_fiscal_2025(e)
    lignes = {x.libelle: x for x in trace.lignes}
    assert lignes["Ligne fédérale 31900"].montant == D(1000)
    assert lignes["Intérêts 2020 réclamés"].montant == D(300)
    assert lignes["Intérêts 2024 réclamés"].montant == D(500)
    assert lignes["Intérêts 2025 réclamés"].montant == D(200)
    assert lignes["Ligne fédérale 31900"].ordre < lignes["Base ligne 33800"].ordre
    assert lignes["Économie fédérale réelle 5B"].montant == D("121.08")
    assert [x.ordre for x in trace.lignes] == list(range(1, len(trace.lignes) + 1))
    f = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "5b.pdf")
    with fitz.open(f) as pdf:
        texte = "\n".join(page.get_text() for page in pdf)
        for page in pdf:
            for x0, y0, x1, y1, *_ in page.get_text("blocks"):
                assert 0 <= x0 < x1 <= page.rect.width
                assert 0 <= y0 < y1 <= page.rect.height
    for sortie in (texte, formater_estimation_fiscale_2025(e)):
        assert "Ligne fédérale 31900 : 1000.00" in sortie
        assert "Année 2020 effectivement réclamée : 300.00" in sortie
        assert "Année 2024 effectivement réclamée : 500.00" in sortie
        assert "Source : Relevé gouvernemental" in sortie
        assert "121.08" in sortie
