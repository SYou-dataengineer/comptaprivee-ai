"""Régression : refuser les montants non finis avant toute comparaison fiscale."""
from dataclasses import replace
from decimal import Decimal as D
import pytest
from src.comptaprivee.tax_tuition_2025 import valider_frais_scolarite_2025
from src.comptaprivee.tax_medical_expenses_2025 import valider_frais_medicaux_2025
from tests.test_tax_tuition_integration_2025 import _scolarite_3000
from tests.test_tax_federal_top_up_integration_2025 import medical


@pytest.mark.parametrize("fabrique,valider", [
    (_scolarite_3000, valider_frais_scolarite_2025),
    (medical, valider_frais_medicaux_2025),
])
@pytest.mark.parametrize("champ", ["montant_admissible_federal", "montant_admissible_quebec"])
@pytest.mark.parametrize("valeur", [D("NaN"), D("sNaN"), D("Infinity"), D("-Infinity"), 500, 500.0, "500", True])
def test_montants_invalides_refuses_explicitement(fabrique, valider, champ, valeur):
    with pytest.raises(ValueError, match="Decimal fini"):
        valider(replace(fabrique(), **{champ: valeur}))


@pytest.mark.parametrize("fabrique,valider", [
    (_scolarite_3000, valider_frais_scolarite_2025),
    (medical, valider_frais_medicaux_2025),
])
def test_decimal_fini_conserve_sans_changement_arrondi(fabrique, valider):
    p = replace(fabrique(), montant_admissible_federal=D("1000.001"))
    assert valider(p) == p
