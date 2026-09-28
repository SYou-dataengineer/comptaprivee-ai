from dataclasses import replace
from decimal import Decimal as D
import json
import fitz
import pytest
from src.comptaprivee.tax_quebec_student_interest_2025 import (
    InteretsEtudiantsQuebec2025, CONFIRMATIONS_6B, calculer_interets_quebec_2025 as moteur,
    interets_quebec_vers_dict, interets_quebec_depuis_dict)
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calcul, formater_estimation_fiscale_2025
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, dossier_fiscal_depuis_contenu
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_student_loan_interest_2025 import profil as federal


def profil(**kw):
    return replace(InteretsEtudiantsQuebec2025(interets_payes_2025=D(1000), solde_inutilise_1998_2024=D(2000),
        reclamation_385=D(1200), source="Annexe M 2024 fictive et intérêts payés 2025 vérifiés",
        **{nom: True for nom in CONFIRMATIONS_6B}), **kw)


@pytest.mark.parametrize("demande,credit,report", [("0", "0", "3000"), ("1200", "240", "1800"),
    ("3000", "600", "0"), ("0.03", "0.01", "2999.97")])
def test_annexe_m_et_taux_20(demande, credit, report):
    r = moteur(profil(reclamation_385=D(demande)))
    assert r.disponible_ligne_52 == D(3000)
    assert (r.ligne_385, r.credit_385, r.report_ligne_62) == (D(demande), D(credit), D(report))
    assert r.ligne_389 == r.ajout_credit_389 == r.credit_385


def test_reports_quebec_sans_expiration_et_paiement_personne_liee():
    r = moteur(profil(interets_payes_2025=D(0), source="Intérêts payés par un parent en 1998, jamais utilisés"))
    assert r.disponible_ligne_52 == D(2000) and r.report_ligne_62 == D(800)


@pytest.mark.parametrize("champ", list(CONFIRMATIONS_6B))
@pytest.mark.parametrize("v", [False, "oui", 1])
def test_confirmations_obligatoires_et_strictes(champ, v):
    with pytest.raises(ValueError): moteur(profil(**{champ: v}))


@pytest.mark.parametrize("champ", ["interets_payes_2025", "solde_inutilise_1998_2024", "reclamation_385"])
@pytest.mark.parametrize("v", [D("-1"), D("NaN"), D("sNaN"), D("Infinity"), D("1E9999"), D("1.001"), 1.5, True, "100"])
def test_montants_invalides(champ, v):
    with pytest.raises(ValueError): moteur(profil(**{champ: v}))


@pytest.mark.parametrize("kw", [{"reclamation_385": D("3000.01")}, {"source": " "}, {"source": None}])
def test_depassement_et_source(kw):
    with pytest.raises(ValueError): moteur(profil(**kw))


def test_arrondi_commun_ligne389():
    r = moteur(profil(interets_payes_2025=D("0.02"), solde_inutilise_1998_2024=D(0), reclamation_385=D("0.02")), base_medicale_381=D("0.02"))
    assert r.credit_385 == D(0)  # deux crédits arrondis séparément donneraient zéro à tort
    assert r.ligne_388 == D("0.04") and r.ligne_389 == r.ajout_credit_389 == D("0.01")


def test_revenu_federal_et_rapprochement():
    d = _dossier_52000()
    base = calcul(d, interets_pret_etudiant=federal())
    e = calcul(d, interets_pret_etudiant=federal(), interets_etudiants_quebec=profil())
    assert e.revenu == base.revenu and e.federal == base.federal
    assert e.resultat_interets_pret_etudiant == base.resultat_interets_pret_etudiant
    assert base.quebec.impot_quebec_preliminaire - e.quebec.impot_quebec_preliminaire == D(240)
    assert e.rapprochement.remboursement_estime - base.rapprochement.remboursement_estime == D(240)


def test_aucun_impot_ne_restitue_pas_les_interets_reclames():
    from tests.test_tax_pension_income_2025 import dossier_pensions, profil_pensions
    e = calcul(dossier_pensions(montant="1000"), profil_pensions=profil_pensions(), interets_etudiants_quebec=profil())
    assert e.quebec.impot_quebec_preliminaire == 0
    assert e.resultat_interets_quebec.report_ligne_62 == D(1800)
    assert e.resultat_interets_quebec.ligne_385 == D(1200)


def test_medical_et_interets_arrondis_ensemble_dans_estimation():
    from tests.test_tax_medical_expenses_integration_2025 import _frais_3000
    frais = replace(_frais_3000(), montant_admissible_quebec=D("1502.87"))
    p = profil(interets_payes_2025=D("0.02"), solde_inutilise_1998_2024=D(0), reclamation_385=D("0.02"))
    sans = calcul(_dossier_52000(), frais_medicaux=frais)
    e = calcul(_dossier_52000(), frais_medicaux=frais, interets_etudiants_quebec=p)
    assert e.resultat_interets_quebec.ligne_388 == D("0.04")
    assert sans.quebec.impot_quebec_preliminaire - e.quebec.impot_quebec_preliminaire == D("0.01")


def test_json_inference_recalcul_et_divergence(tmp_path):
    d = _dossier_52000(); e = calcul(d, interets_etudiants_quebec=profil())
    f = sauvegarder_dossier_fiscal(d, estimation=e, destination=tmp_path / "interets_quebec.json")
    brut = json.loads(f.read_text(encoding="utf-8"))
    assert brut["interets_etudiants_quebec"]["solde_inutilise_1998_2024"] == "2000"
    c = dossier_fiscal_depuis_contenu(brut)
    assert c.interets_etudiants_quebec == profil()
    assert calcul(c.dossier, interets_etudiants_quebec=c.interets_etudiants_quebec).quebec == e.quebec
    with pytest.raises(ValueError, match="divergent"):
        sauvegarder_dossier_fiscal(d, estimation=e, interets_etudiants_quebec=profil(reclamation_385=D(0)), destination=tmp_path / "refus.json")
    brut.pop("interets_etudiants_quebec")
    assert dossier_fiscal_depuis_contenu(brut).interets_etudiants_quebec == InteretsEtudiantsQuebec2025()


@pytest.mark.parametrize("champ,valeur", [("reclamation_385", 1.5), ("solde_inutilise_1998_2024", True),
    ("interets_payes_2025", "NaN"), ("valide_par_comptable", "oui"), ("source", 1),
    ("credit_derive", "240"), ("reclamation_385", "3001")])
def test_json_types_et_cles_stricts(champ, valeur):
    brut = interets_quebec_vers_dict(profil()); brut[champ] = valeur
    with pytest.raises(ValueError): interets_quebec_depuis_dict(brut)


def test_vide_historique_et_json():
    p = InteretsEtudiantsQuebec2025()
    assert moteur(p).disponible_ligne_52 == 0
    assert interets_quebec_depuis_dict(None) == interets_quebec_depuis_dict({}) == p
    assert calcul(_dossier_52000(), interets_etudiants_quebec=p) == calcul(_dossier_52000())


def test_trace_resume_et_pdf(tmp_path):
    e = calcul(_dossier_52000(), interets_etudiants_quebec=profil())
    trace = str(construire_trace_calcul_fiscal_2025(e))
    assert "1200" in trace and "1800" in trace and "389" in trace and "20 %" in trace
    resume = formater_estimation_fiscale_2025(e)
    assert "INTÉRÊTS ÉTUDIANTS QUÉBEC" in resume and "sans expiration" in resume
    f = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "interets_quebec_6b.pdf")
    with fitz.open(f) as pdf:
        texte = "\n".join(p.get_text() for p in pdf)
        for p in pdf:
            assert all(0 <= b[0] < b[2] <= p.rect.width and 0 <= b[1] < b[3] <= p.rect.height for b in p.get_text("blocks"))
    for attendu in ("ANNEXE M / LIGNE 385", "240.00", "1800.00", "1200.00", "1998", "validation comptable"):
        assert attendu in texte
