"""Intégration de la prime 456 et des avances 441, sans double comptage."""
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
from src.comptaprivee.tax_quebec_work_premium_2025 import PrimeTravailQuebec2025
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_quebec_work_premium_2025 import profil


def test_json_faits_seuls_rechargement_et_ancien_dossier(tmp_path):
    d = _dossier_52000()
    e = calcul(d, prime_travail_quebec=profil())
    f = sauvegarder_dossier_fiscal(d, estimation=e, destination=tmp_path / "6i.json")
    brut = json.loads(f.read_text(encoding="utf-8"))
    c = dossier_fiscal_depuis_contenu(brut)
    assert c.prime_travail_quebec == profil()
    assert calcul(c.dossier, prime_travail_quebec=c.prime_travail_quebec) == e
    assert not {"revenu_familial", "credit", "montant", "base_prime_travail_quebec"} & brut["prime_travail_quebec"].keys()
    with pytest.raises(ValueError, match="divergent"):
        sauvegarder_dossier_fiscal(d, estimation=e, prime_travail_quebec=profil(droit_376_confirme=True),
            destination=tmp_path / "refus.json")
    brut.pop("prime_travail_quebec")
    ancien = dossier_fiscal_depuis_contenu(brut)
    assert ancien.prime_travail_quebec == PrimeTravailQuebec2025()
    assert calcul(ancien.dossier, prime_travail_quebec=ancien.prime_travail_quebec) == calcul(d)


@pytest.mark.parametrize("champ,valeur", [("credit", "356"), ("activer", 1), ("citoyennete_confirmee", False)])
def test_chargement_json_refuse_faits_invalides(tmp_path, champ, valeur):
    f = sauvegarder_dossier_fiscal(_dossier_52000(), prime_travail_quebec=profil(), destination=tmp_path / "6i.json")
    brut = json.loads(f.read_text(encoding="utf-8"))
    brut["prime_travail_quebec"][champ] = valeur
    with pytest.raises(ValueError):
        dossier_fiscal_depuis_contenu(brut)




from tests.test_tax_workers_benefit_2025 import dossier_20000


@pytest.mark.parametrize("avances", ["0", "500", "5000"])
@pytest.mark.parametrize("dossier", [dossier_20000, _dossier_52000])
def test_effet_net_unique_et_impots_de_base_inchanges(avances, dossier):
    d = dossier()
    avant = calcul(d)
    e = calcul(d, prime_travail_quebec=profil(avances_rl19_a=D(avances)))
    assert e.federal == avant.federal
    assert e.quebec == avant.quebec
    assert e.revenu == avant.revenu
    r, r0 = e.rapprochement, avant.rapprochement
    credit = e.resultat_prime_travail_quebec.credit_ligne_456
    assert r.remboursement_estime-r.solde_estime == r0.remboursement_estime-r0.solde_estime + credit-D(avances)
    assert r.credit_prime_travail_quebec_ligne_456 == credit
    assert r.avances_prime_travail_quebec_ligne_441 == D(avances)


def test_reer_change_275_pas_revenu_travail():
    from tests.test_tax_reer_interface_storage_2025 import _reer_5000
    e = calcul(dossier_20000(), prime_travail_quebec=profil(), ajustement_reer=_reer_5000())
    r = e.resultat_prime_travail_quebec
    assert r.base.revenu_travail_ligne_29 == D(20000)
    assert r.base.revenu_familial_ligne_54 == D(13635)
    assert r.credit_ligne_456 == D("1084.02")


def test_act_et_solidarite_conservent_leurs_bases():
    from tests.test_tax_workers_benefit_2025 import profil as act
    from tests.test_tax_quebec_solidarity_2025 import profil as solidarite
    kw = dict(allocation_travailleurs=act(), solidarite_quebec=solidarite(naissance="1990-12-31"))
    a = calcul(dossier_20000(), **kw)
    b = calcul(dossier_20000(), **kw, prime_travail_quebec=profil(naissance="1990-12-31"))
    assert a.resultat_allocation_travailleurs == b.resultat_allocation_travailleurs
    assert a.base_solidarite_quebec == b.base_solidarite_quebec
    with pytest.raises(ValueError, match="Naissance prime"):
        calcul(dossier_20000(), **kw, prime_travail_quebec=profil())


def test_famille_et_autres_revenus_refuses():
    from tests.test_tax_quebec_childcare_2025 import profil as garde
    from tests.test_tax_estimation_2025 import _validee
    with pytest.raises(ValueError, match="familiale"):
        calcul(dossier_20000(), prime_travail_quebec=profil(), frais_garde_quebec=garde())
    d = dossier_20000()
    d = replace(d, donnees_validees=d.donnees_validees + (replace(d.donnees_validees[0], type_document="RL-1", case="O", valeur_validee=D(100)),))
    with pytest.raises(ValueError):
        calcul(d, prime_travail_quebec=profil())


def test_trace_resume_pdf_exact_et_cent_sans_regle_rq_presumee(tmp_path):
    from src.comptaprivee.tax_quebec_work_premium_2025 import NOTE_ARRONDI_6I
    e = calcul(dossier_20000(), prime_travail_quebec=profil(droit_376_confirme=True, avances_rl19_a=D(500)))
    trace = formater_trace_calcul_fiscal_2025(construire_trace_calcul_fiscal_2025(e))
    resume = formater_estimation_fiscale_2025(e)
    f = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "prime_6i.pdf")
    with fitz.open(f) as pdf:
        texte = " ".join(p.get_text() for p in pdf)
        for p in pdf:
            assert all(0 <= b[0] < b[2] <= p.rect.width and 0 <= b[1] < b[3] <= p.rect.height for b in p.get_text("blocks"))
    for sortie in (trace, resume, texte):
        sortie = " ".join(sortie.split())
        for attendu in ("18635.00", "20000.00", "2173.63", "500.00", "ligne 456", "ligne 441", "Bouclier fiscal 460 non calculé", NOTE_ARRONDI_6I):
            assert attendu in sortie



def test_avances_a_c_h_distinctes_et_credit_non_net():
    from tests.test_tax_reconciliation_2025 import _modules
    from src.comptaprivee.tax_reconciliation_2025 import calculer_rapprochement_fiscal_2025 as rapprocher
    modules = _modules()
    avant = rapprocher(*modules)
    apres = rapprocher(*modules, credit_prime_travail_quebec=D("584.02"),
        avances_prime_travail_quebec=D(5000), avances_garde_quebec=D(600), avances_aidante_quebec=D(700))
    assert apres.impot_total_preliminaire - avant.impot_total_preliminaire == D(6300)
    assert apres.remboursement_estime - apres.solde_estime == avant.remboursement_estime - avant.solde_estime + D("584.02") - D(6300)
    assert apres.abattement_quebec == avant.abattement_quebec
    assert apres.impot_federal_apres_abattement == avant.impot_federal_apres_abattement


def test_211_soustrait_une_fois_et_ne_change_pas_275():
    d = dossier_20000()
    case211 = replace(next(v for v in d.donnees_validees if v.type_document == "RL-1"), case="211", valeur_validee=D(10000))
    d = replace(d, donnees_validees=d.donnees_validees+(case211,))
    e = calcul(d, prime_travail_quebec=profil())
    assert e.resultat_prime_travail_quebec.base.revenu_travail_ligne_29 == D(10000)
    assert e.resultat_prime_travail_quebec.base.revenu_familial_ligne_54 == D(18635)
    assert e.resultat_prime_travail_quebec.credit_ligne_456 == D("280.10")


def test_source_longue_pdf_sans_debordement(tmp_path):
    e = calcul(dossier_20000(), prime_travail_quebec=profil(source="W" * 2000))
    f = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "long.pdf")
    with fitz.open(f) as pdf:
        for p in pdf:
            assert all(0 <= b[0] < b[2] <= p.rect.width for b in p.get_text("blocks"))
