from decimal import Decimal

import pytest

from src.comptaprivee.tax_rules_2025 import (
    CANADA_EMPLOYMENT_AMOUNT_MAX_2025,
    EI_MAX_QUEBEC_2025,
    FEDERAL_BPA_MAX_2025,
    FEDERAL_BPA_MIN_2025,
    QPP_SECOND_ADDITIONAL_MAX_EMPLOYEE_2025,
    QUEBEC_ABATEMENT_RATE,
    QUEBEC_BPA_2025,
    decomposer_rrq_ba_2025,
    deduction_travailleur_quebec_2025,
    impot_federal_brut_2025,
    impot_quebec_brut_2025,
    montant_canadien_emploi_2025,
    montant_personnel_base_federal_2025,
    valider_rrq_bb_2025,
)


def test_impot_federal_premiere_tranche_2025() -> None:
    assert impot_federal_brut_2025(
        Decimal("50000")
    ) == Decimal("7250.00")


def test_impot_federal_deux_tranches_2025() -> None:
    assert impot_federal_brut_2025(
        Decimal("60000")
    ) == Decimal("8857.50")


def test_impot_quebec_premiere_tranche_2025() -> None:
    assert impot_quebec_brut_2025(
        Decimal("50000")
    ) == Decimal("7000.00")


def test_impot_quebec_deux_tranches_2025() -> None:
    assert impot_quebec_brut_2025(
        Decimal("60000")
    ) == Decimal("8737.25")


def test_bpa_federal_maximum_2025() -> None:
    assert montant_personnel_base_federal_2025(
        Decimal("100000")
    ) == FEDERAL_BPA_MAX_2025


def test_bpa_federal_minimum_2025() -> None:
    assert montant_personnel_base_federal_2025(
        Decimal("300000")
    ) == FEDERAL_BPA_MIN_2025


def test_bpa_federal_reduction_progressive_2025() -> None:
    assert montant_personnel_base_federal_2025(
        Decimal("215648")
    ) == Decimal("15333.50")


def test_montant_canadien_emploi_plafonne_2025() -> None:
    assert montant_canadien_emploi_2025(
        Decimal("52000")
    ) == CANADA_EMPLOYMENT_AMOUNT_MAX_2025


def test_deduction_travailleur_quebec_plafonnee_2025() -> None:
    assert deduction_travailleur_quebec_2025(
        Decimal("52000")
    ) == Decimal("1420.00")


def test_decomposer_rrq_ba_maximum_2025() -> None:
    base, premiere = decomposer_rrq_ba_2025(
        Decimal("4339.20")
    )

    assert base == Decimal("3661.20")
    assert premiere == Decimal("678.00")


def test_rrq_bb_maximum_2025() -> None:
    assert valider_rrq_bb_2025(
        Decimal("396")
    ) == QPP_SECOND_ADDITIONAL_MAX_EMPLOYEE_2025


def test_constantes_officielles_2025() -> None:
    assert QUEBEC_BPA_2025 == Decimal("18571")
    assert QUEBEC_ABATEMENT_RATE == Decimal("0.165")
    assert EI_MAX_QUEBEC_2025 == Decimal("860.67")


def test_rrq_ba_trop_eleve_est_refuse() -> None:
    with pytest.raises(ValueError):
        decomposer_rrq_ba_2025(
            Decimal("5000")
        )


def test_rrq_bb_trop_eleve_est_refuse() -> None:
    with pytest.raises(ValueError):
        valider_rrq_bb_2025(
            Decimal("500")
        )
