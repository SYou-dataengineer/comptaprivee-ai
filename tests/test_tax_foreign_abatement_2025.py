"""Régression T1 Québec 2025 : 40500 ne modifie pas 42900/44000."""

from dataclasses import replace
from decimal import Decimal as D

import fitz
import pytest

from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025, formater_estimation_fiscale_2025,
)
from src.comptaprivee.tax_foreign_investment_2025 import (
    CreditImpotEtranger2025, appliquer_credit_impot_etranger_2025,
)
from src.comptaprivee.tax_reconciliation_2025 import calculer_rapprochement_fiscal_2025
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
from tests.test_tax_foreign_investment_2025 import dossier, profil, profil_credit
from tests.test_tax_estimation_2025 import _dossier_52000


def estimation(montant="0"):
    return calculer_estimation_fiscale_2025(
        dossier("10000", "1500", emploi=True),
        profil_placement_etranger=profil(),
        profil_credit_impot_etranger=profil_credit(montant, "0"),
    )


def test_40500_100_preserve_42900_et_abattement():
    sans, avec = estimation(), estimation("100")
    for e in (sans, avec):
        assert e.federal.impot_federal_de_base == D("6100.30")
        assert e.rapprochement.impot_federal_de_base == D("6100.30")
        assert e.rapprochement.abattement_quebec == D("1006.55")
    assert avec.federal.impot_federal_apres_credit_etranger == D("6000.30")
    assert avec.rapprochement.impot_federal_apres_credit_etranger == D("6000.30")
    assert sans.rapprochement.impot_total_preliminaire == D("11249.11")
    assert avec.rapprochement.impot_total_preliminaire == D("11149.11")
    assert (avec.rapprochement.remboursement_estime - avec.rapprochement.solde_estime
            - sans.rapprochement.remboursement_estime + sans.rapprochement.solde_estime) == D("100")


@pytest.mark.parametrize("demande,utilise", [("0", "0"), ("100", "100"),
    ("6100.30", "6100.30"), ("7000", "6100.30")])
def test_plafond_40500_et_abattement_remboursable(demande, utilise):
    e = estimation()
    credit = replace(e.credit_impot_etranger, ligne_40500=D(demande))
    f, q = appliquer_credit_impot_etranger_2025(e.federal, e.quebec, credit)
    r = calculer_rapprochement_fiscal_2025(e.base, f, q)
    ref = calculer_rapprochement_fiscal_2025(e.base, e.federal, e.quebec)
    assert f.impot_federal_de_base == D("6100.30")
    assert f.credit_etranger_ligne_40500 == D(utilise)
    assert f.impot_federal_apres_credit_etranger == D("6100.30") - D(utilise)
    assert r.abattement_quebec == ref.abattement_quebec == D("1006.55")
    assert ref.impot_total_preliminaire - r.impot_total_preliminaire == D(utilise)
    if D(utilise) == D("6100.30"):
        assert f.impot_federal_apres_credit_etranger == 0
        assert r.impot_federal_apres_abattement == -D("1006.55")


def test_sans_credit_etranger_inchange():
    e = calculer_estimation_fiscale_2025(_dossier_52000())
    assert e.federal.credit_etranger_ligne_40500 == 0
    assert e.federal.impot_federal_apres_credit_etranger == D("4401.90")
    assert e.rapprochement.abattement_quebec == D("726.31")
    assert e.rapprochement.impot_federal_apres_abattement == D("3675.59")


def test_trace_ordre_et_montants_42900_40500_44000():
    trace = construire_trace_calcul_fiscal_2025(estimation("100"))
    lignes = {x.libelle: x for x in trace.lignes}
    noms = [x.libelle for x in trace.lignes]
    base = lignes["Impôt fédéral de base"]
    assert base.montant == D("6100.30")
    assert "ligne 42900, avant 40500" in base.formule
    assert lignes["Crédit impôt étranger ligne 40500"].montant == D("100")
    assert lignes["Impôt fédéral après ligne 40500"].montant == D("6000.30")
    assert lignes["Abattement Québec"].montant == D("1006.55")
    assert "42900" in lignes["Abattement Québec"].formule
    assert noms.index("Impôt fédéral de base") < noms.index("Crédit impôt étranger ligne 40500")
    assert noms.index("Crédit impôt étranger ligne 40500") < noms.index("Impôt fédéral après ligne 40500") < noms.index("Abattement Québec")


def test_pdf_et_resume_40500(tmp_path):
    e = estimation("100")
    p = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "rapport.pdf")
    with fitz.open(p) as doc:
        pdf = "\n".join(page.get_text() for page in doc)
    for texte in (pdf, formater_estimation_fiscale_2025(e)):
        texte = texte.replace("\xa0", " ")
        for attendu in ("42900 avant crédit étranger", "40500", "6 100,30", "6 000,30", "1 006,55"):
            assert attendu in texte


def test_json_sans_nouveau_champ_recalcule_abattement(tmp_path):
    e = estimation("100")
    p = sauvegarder_dossier_fiscal(e.dossier, estimation=e, destination=tmp_path / "d.json")
    assert "impot_federal_apres_credit_etranger" not in p.read_text(encoding="utf-8")
    charge = charger_dossier_fiscal(p)
    recalcul = calculer_estimation_fiscale_2025(
        charge.dossier, profil_placement_etranger=charge.profil_placement_etranger,
        profil_credit_impot_etranger=charge.profil_credit_impot_etranger,
    )
    assert recalcul == e
