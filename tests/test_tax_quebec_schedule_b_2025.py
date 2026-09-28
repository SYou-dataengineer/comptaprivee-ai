from dataclasses import replace
from decimal import Decimal as D
import json
import fitz
import pytest

from tests.test_tax_living_alone_2025 import _profil as profil_seule
from tests.test_tax_age_retirement_integration_2025 import _profil_age_retraite as profil_age
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_pension_income_2025 import dossier_pensions, profil_pensions
from src.comptaprivee.tax_quebec_schedule_b_2025 import calculer_annexe_b_combinee_2025 as annexe
from src.comptaprivee.tax_age_retirement_2025 import montant_ligne_361_age_retraite_2025
from src.comptaprivee.tax_living_alone_2025 import montant_ligne_361_personne_vivant_seule_2025
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calcul, formater_estimation_fiscale_2025
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, dossier_fiscal_depuis_contenu
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025


def profils(revenu="50095"):
    return (profil_seule(revenu_familial_net=D(revenu), aucun_montant_age_ou_retraite=False,
                combinaison_annexe_b_confirmee=True),
            profil_age(revenu_familial_net=D(revenu), aucun_montant_personne_vivant_seule=False,
                combinaison_annexe_b_confirmee=True))


@pytest.mark.parametrize("revenu,reduction,montant,credit", [
    ("0", "0", "9504", "1330.56"), ("42090", "0", "9504", "1330.56"),
    ("42090.01", "0", "9504", "1330.56"), ("50095", "1500.94", "8003.06", "1120.43"),
    ("92778", "9504", "0", "0"), ("110000", "12733.13", "0", "0")])
def test_annexe_officielle_une_seule_reduction(revenu, reduction, montant, credit):
    r = annexe(*profils(revenu))
    assert r.total_ligne_30 == D(9504)
    assert (r.personne_seule, r.age, r.retraite) == (D(2128), D(3906), D(3470))
    assert (r.reduction_ligne_31, r.ligne_361, r.credit) == (D(reduction), D(montant), D(credit))


def test_composantes_facultatives_et_supplement_mensuel():
    s, a = profils("42090")
    assert annexe(s, replace(a, reclamer_revenus_retraite=False, revenu_ligne_122=D(0))).ligne_361 == D(6034)
    assert annexe(s, replace(a, reclamer_age=False)).ligne_361 == D(5598)
    s = replace(s, reclamer_additionnel_monoparental=True, enfant_majeur_etudes_admissible=True,
        aucun_droit_allocation_famille_decembre=True, mois_allocation_famille_2025=3)
    r = annexe(s, a)
    assert r.additionnel_monoparental == D("1970.24")
    assert r.ligne_361 == D("11474.24")


@pytest.mark.parametrize("cote,kw", [
    (0, {"combinaison_annexe_b_confirmee": False, "aucun_montant_age_ou_retraite": True}),
    (1, {"combinaison_annexe_b_confirmee": False, "aucun_montant_personne_vivant_seule": True}),
    (0, {"revenu_familial_net": D(50000)}), (0, {"aucun_conjoint_31_decembre_2025": False}),
    (1, {"resident_quebec_canada_toute_annee": False}), (0, {"aucun_montant_age_ou_retraite": True}),
    (1, {"aucun_montant_personne_vivant_seule": True}), (0, {"valide_par_comptable": False}),
    (1, {"valide_par_comptable": "oui"}), (0, {"source": 123}), (1, {"source_age": ""}),
    (0, {"revenu_familial_net": D("NaN")}), (1, {"revenu_ligne_122": D("1.001")}),
    (0, {"revenu_familial_net": D("1E9999")}), (0, {"mois_allocation_famille_2025": True}),
    (1, {"reclamer_age": False, "reclamer_revenus_retraite": False}),
    (0, {"combinaison_annexe_b_confirmee": 1}), (0, {"reclamer_montant": False}),
])
def test_combinaison_invalide_refusee(cote, kw):
    p = list(profils()); p[cote] = replace(p[cote], **kw)
    with pytest.raises(ValueError): annexe(*p)


def test_calculs_isoles_refusent_double_reduction_et_ancien_mode_inchange():
    s, a = profils()
    for fonction, p in ((montant_ligne_361_age_retraite_2025, a),
                        (montant_ligne_361_personne_vivant_seule_2025, s)):
        with pytest.raises(ValueError): fonction(p)
    assert annexe(profil_seule(), profil_age()) is None
    assert montant_ligne_361_age_retraite_2025(profil_age()) == D("5875.06")
    with pytest.raises(ValueError): annexe(s, a, revenu_net=D(1))


def estimation():
    s, a = profils("50000")
    a = replace(a, revenu_ligne_122=D(50000))
    d = dossier_pensions(montant="50000")
    e = calcul(d, profil_pensions=profil_pensions(age=65), personne_vivant_seule=s, montants_age_retraite=a)
    return d, e


def test_integration_revenus_federal_impot_quebec_et_json(tmp_path):
    d, e = estimation()
    base = calcul(d, profil_pensions=profil_pensions(age=65), montants_age_retraite=replace(
        e.montants_age_retraite, combinaison_annexe_b_confirmee=False, aucun_montant_personne_vivant_seule=True))
    r = annexe(e.personne_vivant_seule, e.montants_age_retraite)
    assert r.ligne_361 == D("8020.87") and r.credit == D("1122.92")
    assert e.revenu == base.revenu and e.federal == base.federal
    # Le profil pensions applique déjà âge/retraite : l'ajout combiné vaut 2128 × 14 %.
    assert base.quebec.impot_quebec_preliminaire - e.quebec.impot_quebec_preliminaire == D("297.92")
    assert base.rapprochement.impot_total_preliminaire - e.rapprochement.impot_total_preliminaire == D("297.92")
    f = sauvegarder_dossier_fiscal(d, estimation=e, destination=tmp_path / "annexe_b.json")
    c = dossier_fiscal_depuis_contenu(json.loads(f.read_text(encoding="utf-8")))
    assert c.personne_vivant_seule == e.personne_vivant_seule and c.montants_age_retraite == e.montants_age_retraite
    assert calcul(c.dossier, profil_pensions=c.profil_pensions, personne_vivant_seule=c.personne_vivant_seule,
        montants_age_retraite=c.montants_age_retraite).quebec == e.quebec
    with pytest.raises(ValueError, match="diverg"):
        sauvegarder_dossier_fiscal(d, estimation=e, personne_vivant_seule=profil_seule(), destination=tmp_path / "refus.json")


@pytest.mark.parametrize("profil,champ,valeur", [
    ("personne_vivant_seule", "combinaison_annexe_b_confirmee", "oui"),
    ("montants_age_retraite", "combinaison_annexe_b_confirmee", False),
    ("personne_vivant_seule", "valide_par_comptable", 1),
    ("montants_age_retraite", "revenu_familial_net", "50001"),
    ("personne_vivant_seule", "revenu_familial_net", True),
    ("montants_age_retraite", "credit_calcule", "1000"),
])
def test_json_refuse_incoherence_ou_types(tmp_path, profil, champ, valeur):
    d, e = estimation()
    f = sauvegarder_dossier_fiscal(d, estimation=e, destination=tmp_path / "strict.json")
    brut = json.loads(f.read_text(encoding="utf-8")); brut[profil][champ] = valeur
    with pytest.raises(ValueError): dossier_fiscal_depuis_contenu(brut)


def test_ancien_json_et_age_seul_sans_retraite(tmp_path):
    s, a = profils()
    a = replace(a, reclamer_revenus_retraite=False, revenu_ligne_122=D(0))
    e = calcul(_dossier_52000(), personne_vivant_seule=s, montants_age_retraite=a)
    assert annexe(s, a).ligne_361 == D("4533.06")
    f = sauvegarder_dossier_fiscal(_dossier_52000(), destination=tmp_path / "ancien.json")
    brut = json.loads(f.read_text(encoding="utf-8"))
    for nom in ("personne_vivant_seule", "montants_age_retraite"):
        if nom in brut: brut[nom].pop("combinaison_annexe_b_confirmee", None)
    c = dossier_fiscal_depuis_contenu(brut)
    assert not c.personne_vivant_seule.combinaison_annexe_b_confirmee
    assert not c.montants_age_retraite.combinaison_annexe_b_confirmee


def test_trace_resume_pdf_une_section_et_sources(tmp_path):
    _, e = estimation()
    resume = formater_estimation_fiscale_2025(e)
    trace = str(construire_trace_calcul_fiscal_2025(e))
    assert "8020.87" in trace and "1122.92" in trace and "réduction unique" in trace.lower()
    assert resume.count("ANNEXE B COMBINÉE") == 1
    assert "ÂGE / REVENUS DE RETRAITE — QUÉBEC 2025" not in resume
    f = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "annexe_b_combinee.pdf")
    with fitz.open(f) as pdf:
        texte = "\n".join(p.get_text() for p in pdf)
        for p in pdf:
            assert all(0 <= b[0] < b[2] <= p.rect.width and 0 <= b[1] < b[3] <= p.rect.height for b in p.get_text("blocks"))
    assert texte.count("ANNEXE B COMBINÉE") == 1
    for attendu in ("8020.87", "1122.92", "Bail et factures", "Date de naissance", "RL-2"):
        assert attendu in texte
