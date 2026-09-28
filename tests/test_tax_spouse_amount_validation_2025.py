"""Les revenus de 30300 doivent être des Decimal finis avant toute opération."""
from decimal import Decimal

import pytest

from src.comptaprivee.tax_federal_spouse_2025 import (
    montant_ligne_30300_2025,
    valider_montant_conjoint_federal_2025,
)
from tests.test_tax_federal_spouse_2025 import _profil


@pytest.mark.parametrize("champ", [
    "revenu_net_contribuable_ligne_23600", "revenu_net_conjoint_2025",
])
@pytest.mark.parametrize("valeur", [
    Decimal("NaN"), Decimal("sNaN"), Decimal("Infinity"), Decimal("-Infinity"),
    "5000", 5000, 5000.0, None, True,
])
@pytest.mark.parametrize("actif", [False, True])
def test_revenus_non_finis_et_types_incorrects_refuses(champ, valeur, actif):
    profil = _profil(reclamer_montant=actif, **{champ: valeur})
    with pytest.raises(ValueError, match="Decimal fini"):
        valider_montant_conjoint_federal_2025(profil)
    with pytest.raises(ValueError, match="Decimal fini"):
        montant_ligne_30300_2025(profil)


def test_revenus_finis_conservent_le_calcul_30300():
    assert montant_ligne_30300_2025(_profil()) == Decimal("11129.00")
    assert montant_ligne_30300_2025(_profil(reclamer_montant=False)) == 0
