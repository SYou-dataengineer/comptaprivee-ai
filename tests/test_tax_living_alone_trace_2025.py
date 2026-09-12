from decimal import Decimal

from src.comptaprivee.tax_calculation_trace_2025 import (
    construire_trace_calcul_fiscal_2025,
)
from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_living_alone_integration_2025 import _profil_simple


def _trace():
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        personne_vivant_seule=_profil_simple(),
    )
    return construire_trace_calcul_fiscal_2025(estimation)


def test_trace_ajoute_une_ligne_personne_vivant_seule():
    base = construire_trace_calcul_fiscal_2025(
        calculer_estimation_fiscale_2025(_dossier_52000())
    )
    trace = _trace()
    assert len(trace.lignes) == len(base.lignes) + 1


def test_trace_ligne_361():
    trace = _trace()
    ligne = next(
        x for x in trace.lignes
        if x.libelle == "Crédit Québec — personne vivant seule"
    )
    assert ligne.section == "QUÉBEC"
    assert ligne.montant == Decimal("87.79")
    assert "annexe B / ligne 361" in ligne.source
    assert "Bail et factures validés" in ligne.source


def test_trace_formule_ligne_361():
    trace = _trace()
    ligne = next(
        x for x in trace.lignes
        if x.libelle == "Crédit Québec — personne vivant seule"
    )
    assert "627,06 $" in ligne.formule
    assert "14 %" in ligne.formule
    assert "42 090 $" in ligne.formule
    assert "18,75 %" in ligne.formule


def test_trace_impot_quebec_mentionne_ligne_361():
    trace = _trace()
    ligne = next(
        x for x in trace.lignes
        if x.libelle == "Impôt Québec préliminaire"
    )
    assert "personne vivant seule ligne 361" in ligne.formule


def test_trace_resultat_reflete_credit_familial():
    trace = _trace()
    assert trace.resultat == "Remboursement estimé"
    assert trace.montant_resultat == Decimal("5698.84")


def test_trace_numerotation_continue():
    trace = _trace()
    assert [x.ordre for x in trace.lignes] == list(
        range(1, len(trace.lignes) + 1)
    )
