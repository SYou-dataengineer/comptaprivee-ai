from dataclasses import replace
from decimal import Decimal as D
import pytest

from src.comptaprivee.tax_disability_2025 import (
    CreditDeficience2025, supplement_handicap_mineur_2025,
    montant_federal_handicap_2025, credit_federal_handicap_2025,
)
from tests.test_tax_disability_2025 import _credit_valide


def mineur(**kw):
    return replace(_credit_valide(quebec=False, age_18_plus_au_1_janvier_2025=False,
        naissance_federale="2010-02-03", source_soins_federaux="Pièces de soins et absence de réclamation vérifiées",
        soins_federaux_valides=True), **kw)


@pytest.mark.parametrize("naissance,soins,supplement", [
    ("2007-12-31", "0", "0"), ("2008-01-01", "0", "5914"),
    ("2025-12-31", "3464", "5914"), ("2010-01-01", "3464.01", "5913.99"),
    ("2010-01-01", "9377.99", "0.01"), ("2010-01-01", "9378", "0"),
    ("2010-01-01", "15000", "0"), ("1980-01-01", "5000", "0"),
])
def test_bornes_annexe_federale(naissance, soins, supplement):
    assert supplement_handicap_mineur_2025(naissance, D(soins)) == D(supplement)


@pytest.mark.parametrize("soins", [D("NaN"), D("sNaN"), D("Infinity"), D("-Infinity"),
    D(-1), D("1.001"), D("1e100"), True, "10", 1.0])
def test_soins_invalides(soins):
    with pytest.raises(ValueError):
        montant_federal_handicap_2025(mineur(soins_reclames_federaux=soins))


@pytest.mark.parametrize("naissance", ["", "2026-01-01", "2025-02-30", "20080101", True, None])
def test_naissance_invalide(naissance):
    with pytest.raises(ValueError):
        montant_federal_handicap_2025(mineur(naissance_federale=naissance))


@pytest.mark.parametrize("kw", [
    {"soins_federaux_valides": False}, {"soins_federaux_valides": "oui"},
    {"source_soins_federaux": ""}, {"source_soins_federaux": True},
    {"age_18_plus_au_1_janvier_2025": True}, {"reclamer_federal": False},
    {"reclamer_quebec": True},
])
def test_validations_et_quebec_distinct(kw):
    with pytest.raises(ValueError):
        montant_federal_handicap_2025(mineur(**kw))


def test_montant_et_credit_pur():
    assert montant_federal_handicap_2025(mineur()) == D(16052)
    assert credit_federal_handicap_2025(mineur()) == D("2327.54")
    assert montant_federal_handicap_2025(mineur(naissance_federale="2007-12-31")) == D(10138)
    assert montant_federal_handicap_2025(_credit_valide()) == D(10138)
    assert montant_federal_handicap_2025(CreditDeficience2025()) == 0


def test_json_brut_et_legacy():
    from src.comptaprivee.tax_case_storage import _credit_deficience_vers_dict, _credit_deficience_depuis_dict
    brut = _credit_deficience_vers_dict(mineur(soins_reclames_federaux=D(4000)))
    assert brut["soins_reclames_federaux"] == "4000.00"
    assert _credit_deficience_depuis_dict(brut) == mineur(soins_reclames_federaux=D(4000))
    ancien = _credit_deficience_vers_dict(_credit_valide())
    for n in ("naissance_federale", "soins_reclames_federaux", "source_soins_federaux", "soins_federaux_valides"):
        del ancien[n]
    assert _credit_deficience_depuis_dict(ancien) == _credit_valide()


@pytest.mark.parametrize("v", ["NaN", "Infinity", "-1", "1.001", True, 1.0, None])
def test_json_soins_invalides(v):
    from src.comptaprivee.tax_case_storage import _credit_deficience_vers_dict, _credit_deficience_depuis_dict
    brut = _credit_deficience_vers_dict(mineur())
    brut["soins_reclames_federaux"] = v
    with pytest.raises(ValueError):
        _credit_deficience_depuis_dict(brut)


def test_estimation_recalcule_31600_et_33800():
    from tests.test_tax_estimation_2025 import _dossier_52000
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calculer
    e = calculer(_dossier_52000(), credit_deficience=mineur())
    lignes = dict(e.federal.credits_federaux_complets.montants_par_ligne)
    assert lignes["31600"] == D(16052)
    adulte = calculer(_dossier_52000(), credit_deficience=_credit_valide(quebec=False))
    assert e.quebec == adulte.quebec
    assert e.revenu == adulte.revenu
    assert e.federal.credits_federaux_complets.base_ligne_33500 - adulte.federal.credits_federaux_complets.base_ligne_33500 == D(5914)


def test_stockage_inference_divergence_et_pdf(tmp_path):
    import fitz
    from tests.test_tax_estimation_2025 import _dossier_52000
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calculer
    from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
    from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
    from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
    e = calculer(_dossier_52000(), credit_deficience=mineur())
    f = sauvegarder_dossier_fiscal(e.dossier, estimation=e, destination=tmp_path / "mineur.json")
    assert charger_dossier_fiscal(f).credit_deficience == mineur()
    with pytest.raises(ValueError, match="divergent"):
        sauvegarder_dossier_fiscal(e.dossier, estimation=e, credit_deficience=_credit_valide(quebec=False), destination=f)
    trace = construire_trace_calcul_fiscal_2025(e)
    ligne = next(l for l in trace.lignes if l.libelle == "Crédit fédéral pour personnes handicapées")
    assert ligne.montant == D("2327.54") and "16052" in ligne.formule
    pdf = exporter_rapport_fiscal_pdf_2025(e, destination=tmp_path / "mineur.pdf")
    with fitz.open(pdf) as document:
        texte = "".join(page.get_text() for page in document)
    assert "2010-02-03" in texte and "16052.00" in texte and "5914.00" in texte
