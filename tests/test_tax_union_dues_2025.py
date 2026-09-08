from decimal import Decimal

import pytest

from src.comptaprivee.tax_union_dues_2025 import (
    CotisationsSyndicalesProfessionnelles2025,
    aucune_cotisation_syndicale_2025,
    base_credit_quebec_cotisations_2025,
    credit_quebec_cotisations_2025,
    deduction_federale_cotisations_2025,
    valider_cotisations_syndicales_2025,
)


def _cotisations_valides():
    return CotisationsSyndicalesProfessionnelles2025(
        montant_federal_admissible=Decimal("600"),
        montant_quebec_admissible=Decimal("600"),
        source_federale="T4 case 44",
        source_quebec="RL-1 case F",
        valide_par_comptable=True,
        sources_dedoublonnees=True,
    )


def test_zero_est_accepte():
    valeur = aucune_cotisation_syndicale_2025()
    assert valider_cotisations_syndicales_2025(valeur) == valeur


def test_montant_federal_negatif_refuse():
    with pytest.raises(ValueError):
        valider_cotisations_syndicales_2025(
            CotisationsSyndicalesProfessionnelles2025(
                montant_federal_admissible=Decimal("-1")
            )
        )


def test_montant_quebec_negatif_refuse():
    with pytest.raises(ValueError):
        valider_cotisations_syndicales_2025(
            CotisationsSyndicalesProfessionnelles2025(
                montant_quebec_admissible=Decimal("-1")
            )
        )


def test_validation_comptable_obligatoire():
    with pytest.raises(ValueError):
        valider_cotisations_syndicales_2025(
            CotisationsSyndicalesProfessionnelles2025(
                montant_federal_admissible=Decimal("600"),
                source_federale="T4 case 44",
                sources_dedoublonnees=True,
            )
        )


def test_sources_dedoublonnees_obligatoires():
    with pytest.raises(ValueError):
        valider_cotisations_syndicales_2025(
            CotisationsSyndicalesProfessionnelles2025(
                montant_federal_admissible=Decimal("600"),
                source_federale="T4 case 44",
                valide_par_comptable=True,
            )
        )


def test_source_federale_obligatoire():
    with pytest.raises(ValueError):
        valider_cotisations_syndicales_2025(
            CotisationsSyndicalesProfessionnelles2025(
                montant_federal_admissible=Decimal("600"),
                valide_par_comptable=True,
                sources_dedoublonnees=True,
            )
        )


def test_source_quebec_obligatoire():
    with pytest.raises(ValueError):
        valider_cotisations_syndicales_2025(
            CotisationsSyndicalesProfessionnelles2025(
                montant_quebec_admissible=Decimal("600"),
                valide_par_comptable=True,
                sources_dedoublonnees=True,
            )
        )


def test_droits_adhesion_refuses():
    valeur = _cotisations_valides()
    valeur = CotisationsSyndicalesProfessionnelles2025(
        **{
            **valeur.__dict__,
            "inclut_droits_adhesion": True,
        }
    )
    with pytest.raises(ValueError):
        valider_cotisations_syndicales_2025(valeur)


def test_taxes_remboursables_quebec_refusees():
    valeur = _cotisations_valides()
    valeur = CotisationsSyndicalesProfessionnelles2025(
        **{
            **valeur.__dict__,
            "inclut_taxes_remboursables_quebec": True,
        }
    )
    with pytest.raises(ValueError):
        valider_cotisations_syndicales_2025(valeur)


def test_deduction_federale_est_le_montant_valide():
    assert deduction_federale_cotisations_2025(
        _cotisations_valides()
    ) == Decimal("600.00")


def test_base_credit_quebec_est_le_montant_valide():
    assert base_credit_quebec_cotisations_2025(
        _cotisations_valides()
    ) == Decimal("600.00")


def test_credit_quebec_est_dix_pour_cent():
    assert credit_quebec_cotisations_2025(
        _cotisations_valides()
    ) == Decimal("60.00")
