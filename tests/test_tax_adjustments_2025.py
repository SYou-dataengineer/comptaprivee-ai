from decimal import Decimal

import pytest

from src.comptaprivee.tax_adjustments_2025 import (
    AjustementReer2025,
    deduction_reer_federale_2025,
    deduction_reer_quebec_2025,
    valider_ajustement_reer_2025,
)


def _valide():
    return AjustementReer2025(
        deduction_reer=Decimal("5000"),
        plafond_reer_confirme=Decimal("8000"),
        source_plafond_reer="Avis de cotisation / T1028 ARC",
        valide_par_comptable=True,
    )


def test_reer_zero_est_accepte():
    ajustement = AjustementReer2025()
    assert valider_ajustement_reer_2025(ajustement) == ajustement


def test_reer_negatif_est_refuse():
    with pytest.raises(ValueError):
        valider_ajustement_reer_2025(
            AjustementReer2025(
                deduction_reer=Decimal("-1")
            )
        )


def test_reer_exige_validation_comptable():
    with pytest.raises(ValueError):
        valider_ajustement_reer_2025(
            AjustementReer2025(
                deduction_reer=Decimal("1000"),
                plafond_reer_confirme=Decimal("2000"),
                source_plafond_reer="T1028",
            )
        )


def test_reer_exige_source_plafond():
    with pytest.raises(ValueError):
        valider_ajustement_reer_2025(
            AjustementReer2025(
                deduction_reer=Decimal("1000"),
                plafond_reer_confirme=Decimal("2000"),
                valide_par_comptable=True,
            )
        )


def test_reer_ne_depasse_pas_plafond():
    with pytest.raises(ValueError):
        valider_ajustement_reer_2025(
            AjustementReer2025(
                deduction_reer=Decimal("5000"),
                plafond_reer_confirme=Decimal("4000"),
                source_plafond_reer="Avis de cotisation",
                valide_par_comptable=True,
            )
        )


def test_transfert_reer_est_refuse():
    with pytest.raises(ValueError):
        valider_ajustement_reer_2025(
            AjustementReer2025(
                deduction_reer=Decimal("1000"),
                plafond_reer_confirme=Decimal("2000"),
                source_plafond_reer="T1028",
                valide_par_comptable=True,
                inclut_transfert_reer=True,
            )
        )


def test_remboursement_rap_reep_est_refuse():
    with pytest.raises(ValueError):
        valider_ajustement_reer_2025(
            AjustementReer2025(
                deduction_reer=Decimal("1000"),
                plafond_reer_confirme=Decimal("2000"),
                source_plafond_reer="T1028",
                valide_par_comptable=True,
                inclut_remboursement_rap_reep=True,
            )
        )


def test_reer_ordinaire_est_identique_federal_quebec():
    ajustement = _valide()
    assert deduction_reer_federale_2025(
        ajustement
    ) == Decimal("5000")
    assert deduction_reer_quebec_2025(
        ajustement
    ) == Decimal("5000")
