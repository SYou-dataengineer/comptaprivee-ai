"""Soutien aux aînés 463 : intégration sans double comptage."""
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
from src.comptaprivee.tax_quebec_senior_support_2025 import SoutienAinesQuebec2025
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_quebec_senior_support_2025 import profil


def test_json_faits_seuls_rechargement_et_ancien_dossier(tmp_path):
    d = _dossier_52000()
    e = calcul(d, soutien_aines_quebec=profil())
    f = sauvegarder_dossier_fiscal(d, estimation=e, destination=tmp_path / "6j.json")
    brut = json.loads(f.read_text(encoding="utf-8"))
    c = dossier_fiscal_depuis_contenu(brut)
    assert c.soutien_aines_quebec == profil()
    assert calcul(c.dossier, soutien_aines_quebec=c.soutien_aines_quebec) == e
    assert not {"revenu_familial", "credit", "montant", "base_soutien_aines_quebec"} & brut["soutien_aines_quebec"].keys()
    with pytest.raises(ValueError, match="divergent"):
        sauvegarder_dossier_fiscal(d, estimation=e, soutien_aines_quebec=profil(naissance="1950-01-01"),
            destination=tmp_path / "refus.json")
    brut.pop("soutien_aines_quebec")
    ancien = dossier_fiscal_depuis_contenu(brut)
    assert ancien.soutien_aines_quebec == SoutienAinesQuebec2025()
    assert calcul(ancien.dossier, soutien_aines_quebec=ancien.soutien_aines_quebec) == calcul(d)


@pytest.mark.parametrize("champ,valeur", [("credit", "356"), ("activer", 1), ("citoyennete_confirmee", False)])
def test_chargement_json_refuse_faits_invalides(tmp_path, champ, valeur):
    f = sauvegarder_dossier_fiscal(_dossier_52000(), soutien_aines_quebec=profil(), destination=tmp_path / "6j.json")
    brut = json.loads(f.read_text(encoding="utf-8"))
    brut["soutien_aines_quebec"][champ] = valeur
    with pytest.raises(ValueError):
        dossier_fiscal_depuis_contenu(brut)




from tests.test_tax_workers_benefit_2025 import dossier_20000


@pytest.mark.parametrize("dossier", [dossier_20000, _dossier_52000])
@pytest.mark.parametrize("retenues", [True, False])
def test_credit_remboursable_une_fois_sans_modifier_impots(dossier, retenues):
    d = dossier()
    if not retenues:
        d = replace(d, donnees_validees=tuple(replace(v, valeur_validee=D(0))
            if (v.type_document, v.case) in (("T4", "22"), ("RL-1", "E")) else v for v in d.donnees_validees))
    a, b = calcul(d), calcul(d, soutien_aines_quebec=profil())
    assert a.federal == b.federal and a.quebec == b.quebec and a.revenu == b.revenu
    ra, rb = a.rapprochement, b.rapprochement
    credit = b.resultat_soutien_aines_quebec.credit_ligne_463
    assert rb.remboursement_estime-rb.solde_estime == ra.remboursement_estime-ra.solde_estime+credit
    assert rb.credit_soutien_aines_quebec_ligne_463 == credit
    assert rb.abattement_quebec == ra.abattement_quebec


def test_reer_recalcule_275_et_credit():
    from tests.test_tax_reer_interface_storage_2025 import _reer_5000
    a = calcul(_dossier_52000(), soutien_aines_quebec=profil())
    b = calcul(_dossier_52000(), soutien_aines_quebec=profil(), ajustement_reer=_reer_5000())
    assert a.resultat_soutien_aines_quebec.revenu_familial_275 - b.resultat_soutien_aines_quebec.revenu_familial_275 == D(5000)
    assert b.resultat_soutien_aines_quebec.credit_ligne_463 - a.resultat_soutien_aines_quebec.credit_ligne_463 == D(270)


def test_prime_et_solidarite_cumul_sans_confusion():
    from tests.test_tax_quebec_work_premium_2025 import profil as prime
    from tests.test_tax_quebec_solidarity_2025 import profil as solidarite
    kw = dict(prime_travail_quebec=prime(naissance="1955-12-31"), solidarite_quebec=solidarite(naissance="1955-12-31"))
    a = calcul(dossier_20000(), **kw)
    b = calcul(dossier_20000(), soutien_aines_quebec=profil(), **kw)
    assert a.resultat_prime_travail_quebec == b.resultat_prime_travail_quebec
    assert a.base_solidarite_quebec == b.base_solidarite_quebec
    assert b.rapprochement.remboursement_estime-a.rapprochement.remboursement_estime == D(2000)
    with pytest.raises(ValueError, match="Naissance soutien"):
        calcul(dossier_20000(), soutien_aines_quebec=profil(naissance="1950-01-01"), **kw)


def test_famille_refusee():
    from tests.test_tax_quebec_childcare_2025 import profil as garde
    with pytest.raises(ValueError, match="familiale"):
        calcul(_dossier_52000(), soutien_aines_quebec=profil(), frais_garde_quebec=garde())


def test_trace_pdf_et_source_longue(tmp_path):
    e = calcul(dossier_20000(), soutien_aines_quebec=profil(source="W"*2000))
    trace = formater_trace_calcul_fiscal_2025(construire_trace_calcul_fiscal_2025(e))
    resume = formater_estimation_fiscale_2025(e)
    f = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "soutien.pdf")
    with fitz.open(f) as pdf:
        texte = " ".join(p.get_text() for p in pdf)
        for p in pdf:
            assert all(0 <= b[0] < b[2] <= p.rect.width and 0 <= b[1] < b[3] <= p.rect.height for b in p.get_text("blocks"))
    for sortie in (trace, resume, texte):
        sortie = " ".join(sortie.split())
        for attendu in ("18635.00", "Ligne 463", "2000.00", "convention monétaire générale", "27835", "5,40"):
            assert attendu in sortie



def test_age_pensions_rapproche_et_credits_retraite_inchanges():
    from tests.test_tax_pension_income_2025 import dossier_pensions, profil_pensions
    d = dossier_pensions()
    a = calcul(d, profil_pensions=profil_pensions(age=70))
    b = calcul(d, profil_pensions=profil_pensions(age=70), soutien_aines_quebec=profil())
    assert a.montants_age_retraite == b.montants_age_retraite
    assert a.credits_federaux_age_pension == b.credits_federaux_age_pension
    assert a.federal == b.federal and a.quebec == b.quebec
    assert b.resultat_soutien_aines_quebec.credit_ligne_463 == D(2000)
    with pytest.raises(ValueError, match="Naissance soutien"):
        calcul(d, profil_pensions=profil_pensions(age=69), soutien_aines_quebec=profil())


def test_naissance_carriere_rapprochee():
    from tests.test_tax_quebec_career_extension_2025 import profil as carriere
    with pytest.raises(ValueError, match="Naissance soutien"):
        calcul(_dossier_52000(), soutien_aines_quebec=profil(), prolongation_carriere_quebec=carriere(naissance="1950-01-01"))
    e = calcul(_dossier_52000(), soutien_aines_quebec=profil(), prolongation_carriere_quebec=carriere(naissance="1955-12-31"))
    assert e.resultat_soutien_aines_quebec.revenu_familial_275 == e.revenu.revenu_net_quebec
