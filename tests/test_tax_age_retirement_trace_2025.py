from decimal import Decimal

from src.comptaprivee.tax_calculation_trace_2025 import (
    construire_trace_calcul_fiscal_2025,
)
from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
)
from tests.test_tax_age_retirement_integration_2025 import (
    _profil_age_retraite,
)
from tests.test_tax_estimation_2025 import _dossier_52000


def _trace():
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        montants_age_retraite=_profil_age_retraite(),
    )
    return construire_trace_calcul_fiscal_2025(estimation)


def test_trace_ajoute_une_ligne_age_retraite():
    base = construire_trace_calcul_fiscal_2025(
        calculer_estimation_fiscale_2025(_dossier_52000())
    )
    trace = _trace()

    assert len(trace.lignes) == len(base.lignes) + 1


def test_trace_ligne_361_age_retraite():
    trace = _trace()
    ligne = next(
        x
        for x in trace.lignes
        if x.libelle == "Crédit Québec — âge / revenus de retraite"
    )

    assert ligne.section == "QUÉBEC"
    assert ligne.montant == Decimal("822.51")
    assert "annexe B / ligne 361" in ligne.source
    assert "Date de naissance validée" in ligne.source
    assert "RL-2 / feuillet retraite validé" in ligne.source


def test_trace_formule_age_retraite():
    trace = _trace()
    ligne = next(
        x
        for x in trace.lignes
        if x.libelle == "Crédit Québec — âge / revenus de retraite"
    )
    formule = (
        ligne.formule
        .replace("\xa0", " ")
        .replace("\u202f", " ")
    )

    assert "3 906,00 $" in formule
    assert "3 470,00 $" in formule
    assert "5 875,06 $" in formule
    assert "42 090 $" in formule
    assert "18,75 %" in formule
    assert "14 %" in formule


def test_trace_impot_quebec_mentionne_age_retraite():
    trace = _trace()
    ligne = next(
        x
        for x in trace.lignes
        if x.libelle == "Impôt Québec préliminaire"
    )

    assert "âge/retraite ligne 361" in ligne.formule


def test_trace_resultat_reflète_credit_age_retraite():
    trace = _trace()

    assert trace.resultat == "Remboursement estimé"
    assert trace.montant_resultat == Decimal("6433.56")


def test_trace_numerotation_continue():
    trace = _trace()

    assert [x.ordre for x in trace.lignes] == list(
        range(1, len(trace.lignes) + 1)
    )
