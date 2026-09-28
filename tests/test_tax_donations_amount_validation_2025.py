"""Les valeurs non finies doivent être refusées avant toute comparaison fiscale."""
from dataclasses import replace
from decimal import Decimal as D
import pytest
from src.comptaprivee.tax_donations_2025 import (
    valider_dons_bienfaisance_2025, credit_federal_dons_2025, credit_quebec_dons_2025,
)
from tests.test_tax_donations_2025 import _dons_valides

INVALIDES = [D("NaN"), D("sNaN"), D("Infinity"), D("-Infinity"), 1000, 1000.0, "1000", True]


@pytest.mark.parametrize("champ", ["montant_admissible_federal", "montant_admissible_quebec"])
@pytest.mark.parametrize("valeur", INVALIDES)
def test_dons_types_et_non_finis_refuses(champ, valeur):
    with pytest.raises(ValueError, match="Decimal fini"):
        valider_dons_bienfaisance_2025(replace(_dons_valides(), **{champ: valeur}))


@pytest.mark.parametrize("calcul", [credit_federal_dons_2025, credit_quebec_dons_2025])
@pytest.mark.parametrize("valeur", INVALIDES)
def test_revenu_types_et_non_finis_refuses(calcul, valeur):
    with pytest.raises(ValueError, match="Decimal fini"):
        calcul(_dons_valides(), valeur)


def test_arrondi_legacy_inchange():
    dons = _dons_valides("1000.001")
    assert valider_dons_bienfaisance_2025(dons) == dons
    assert credit_federal_dons_2025(dons, D(52000)) == D("261.00")
    assert credit_quebec_dons_2025(dons, D(52000)) == D("232.00")
