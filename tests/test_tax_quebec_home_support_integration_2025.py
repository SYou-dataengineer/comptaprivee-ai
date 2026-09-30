"""Maintien à domicile 458 : intégration sans double comptage."""
from dataclasses import replace
from decimal import Decimal as D
import json

import fitz
import pytest

from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025 as calcul, formater_estimation_fiscale_2025,
)
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, dossier_fiscal_depuis_contenu
from src.comptaprivee.tax_calculation_trace_2025 import (
    construire_trace_calcul_fiscal_2025, formater_trace_calcul_fiscal_2025,
)
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from src.comptaprivee.tax_quebec_home_support_2025 import MaintienDomicileQuebec2025
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_quebec_home_support_2025 import profil


def test_json_faits_seuls_rechargement_et_ancien_dossier(tmp_path):
    d = _dossier_52000()
    e = calcul(d, maintien_domicile_quebec=profil())
    f = sauvegarder_dossier_fiscal(d, estimation=e, destination=tmp_path / "6j.json")
    brut = json.loads(f.read_text(encoding="utf-8"))
    c = dossier_fiscal_depuis_contenu(brut)
    assert c.maintien_domicile_quebec == profil()
    assert calcul(c.dossier, maintien_domicile_quebec=c.maintien_domicile_quebec) == e
    assert not {"revenu_familial", "credit", "montant", "base_maintien_domicile_quebec"} & brut["maintien_domicile_quebec"].keys()
    with pytest.raises(ValueError, match="divergent"):
        sauvegarder_dossier_fiscal(d, estimation=e, maintien_domicile_quebec=profil(naissance="1949-01-01"),
            destination=tmp_path / "refus.json")
    brut.pop("maintien_domicile_quebec")
    ancien = dossier_fiscal_depuis_contenu(brut)
    assert ancien.maintien_domicile_quebec == MaintienDomicileQuebec2025()
    assert calcul(ancien.dossier, maintien_domicile_quebec=ancien.maintien_domicile_quebec) == calcul(d)


@pytest.mark.parametrize("champ,valeur", [("credit", "356"), ("activer", 1), ("autonomie_confirmee", False)])
def test_chargement_json_refuse_faits_invalides(tmp_path, champ, valeur):
    f = sauvegarder_dossier_fiscal(_dossier_52000(), maintien_domicile_quebec=profil(), destination=tmp_path / "6j.json")
    brut = json.loads(f.read_text(encoding="utf-8"))
    brut["maintien_domicile_quebec"][champ] = valeur
    with pytest.raises(ValueError):
        dossier_fiscal_depuis_contenu(brut)






from tests.test_tax_workers_benefit_2025 import dossier_20000


@pytest.mark.parametrize("dossier", [dossier_20000, _dossier_52000])
@pytest.mark.parametrize("retenues", [True, False])
def test_credit_remboursable_une_fois_et_impots_inchanges(dossier, retenues):
    d = dossier()
    if not retenues:
        d = replace(d, donnees_validees=tuple(replace(v, valeur_validee=D(0))
            if (v.type_document, v.case) in (("T4", "22"), ("RL-1", "E")) else v for v in d.donnees_validees))
    a, b = calcul(d), calcul(d, maintien_domicile_quebec=profil())
    assert a.federal == b.federal and a.quebec == b.quebec and a.revenu == b.revenu
    ra, rb = a.rapprochement, b.rapprochement
    assert rb.remboursement_estime-rb.solde_estime == ra.remboursement_estime-ra.solde_estime+D(234)
    assert rb.credit_maintien_domicile_quebec_ligne_458 == D(234)
    assert rb.abattement_quebec == ra.abattement_quebec


def test_reer_recalcule_275_et_reduction_hors_profil_refusee():
    from tests.test_tax_pension_income_2025 import dossier_pensions, profil_pensions
    from tests.test_tax_reer_interface_storage_2025 import _reer_5000
    d = dossier_pensions(montant="75000")
    with pytest.raises(ValueError, match="71010"):
        calcul(d, profil_pensions=profil_pensions(age=75), maintien_domicile_quebec=profil())
    e = calcul(d, profil_pensions=profil_pensions(age=75), maintien_domicile_quebec=profil(), ajustement_reer=_reer_5000())
    assert e.resultat_maintien_domicile_quebec.revenu_familial_275 == D(70000)
    assert e.resultat_maintien_domicile_quebec.credit_ligne_458 == D(234)


def test_cumul_soutien_prime_solidarite_et_naissances():
    from tests.test_tax_quebec_senior_support_2025 import profil as soutien
    from tests.test_tax_quebec_work_premium_2025 import profil as prime
    from tests.test_tax_quebec_solidarity_2025 import profil as solidarite
    kw = dict(soutien_aines_quebec=soutien(naissance="1950-01-01"), prime_travail_quebec=prime(naissance="1950-01-01"),
        solidarite_quebec=solidarite(naissance="1950-01-01", vit_seul_toute_annee=True))
    a = calcul(dossier_20000(), **kw)
    b = calcul(dossier_20000(), maintien_domicile_quebec=profil(), **kw)
    assert a.resultat_soutien_aines_quebec == b.resultat_soutien_aines_quebec
    assert a.resultat_prime_travail_quebec == b.resultat_prime_travail_quebec
    assert a.base_solidarite_quebec == b.base_solidarite_quebec
    assert b.rapprochement.remboursement_estime-a.rapprochement.remboursement_estime == D(234)
    with pytest.raises(ValueError, match="Naissance maintien"):
        calcul(dossier_20000(), maintien_domicile_quebec=profil(naissance="1949-01-01"), **kw)


def test_famille_et_cohabitation_refusees():
    from tests.test_tax_quebec_childcare_2025 import profil as garde
    from tests.test_tax_quebec_caregiver_2025 import profil as aidante
    from tests.test_tax_quebec_solidarity_2025 import profil as solidarite
    for kw in (dict(frais_garde_quebec=garde()), dict(personne_aidante_quebec=aidante()),
            dict(solidarite_quebec=solidarite(naissance="1950-01-01"))):
        with pytest.raises(ValueError, match="Maintien"):
            calcul(_dossier_52000(), maintien_domicile_quebec=profil(), **kw)


def test_avance_rl19_d_detectee_refusee():
    d = dossier_20000()
    d = replace(d, donnees_validees=d.donnees_validees + (replace(d.donnees_validees[0], type_document="RL-19", case="D", valeur_validee=D(100)),))
    # Le garde-fou documentaire existant peut refuser le feuillet avant le contrôle 6K.
    with pytest.raises(ValueError, match="RL-19 D|hors périmètre"):
        calcul(d, maintien_domicile_quebec=profil())


def test_medical_agrege_refuse_pour_prevenir_double_usage():
    from src.comptaprivee.tax_medical_expenses_2025 import FraisMedicaux2025
    m = FraisMedicaux2025(montant_admissible_federal=D(2000), montant_admissible_quebec=D(2000),
        source_federale="Reçus fictifs", source_quebec="Reçus fictifs", valide_par_comptable=True,
        recus_confirmes=True, remboursements_soustraits=True, periode_12_mois_fin_2025_confirmee=True,
        aucune_periode_deja_reclamee=True, profil_individuel_sans_conjoint_dependant=True)
    with pytest.raises(ValueError, match="cumul de frais médicaux"):
        calcul(_dossier_52000(), maintien_domicile_quebec=profil(), frais_medicaux=m)


def test_trace_pdf_et_source_longue(tmp_path):
    e = calcul(dossier_20000(), maintien_domicile_quebec=profil(source="W"*2000))
    trace = formater_trace_calcul_fiscal_2025(construire_trace_calcul_fiscal_2025(e))
    resume = formater_estimation_fiscale_2025(e)
    f = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "maintien.pdf")
    with fitz.open(f) as pdf:
        texte = " ".join(p.get_text() for p in pdf)
        for p in pdf:
            assert all(0 <= b[0] < b[2] <= p.rect.width and 0 <= b[1] < b[3] <= p.rect.height for b in p.get_text("blocks"))
    for sortie in (trace, resume, texte):
        sortie = " ".join(sortie.split())
        for attendu in ("18635.00", "Ligne 458", "234.00", "convention", "71010", "19500", "7605", "280.80", "12 mois", "Janvier", "Décembre"):
            assert attendu.lower() in sortie.lower()
