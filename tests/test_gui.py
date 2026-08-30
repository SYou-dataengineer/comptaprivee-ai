"""Tests de la logique de l'interface graphique locale."""

from decimal import Decimal

import pytest

from src.comptaprivee.gui import ApplicationComptaPrivee


def test_convertir_montant_francais() -> None:
    """Vérifie un montant utilisant une virgule."""
    resultat = ApplicationComptaPrivee.texte_vers_montant(
        "1 149,75 $"
    )

    assert resultat == Decimal("1149.75")


def test_convertir_montant_avec_devise() -> None:
    """Vérifie un montant contenant la devise CAD."""
    resultat = ApplicationComptaPrivee.texte_vers_montant(
        "2500.00 CAD"
    )

    assert resultat == Decimal("2500.00")


def test_refuser_un_montant_invalide() -> None:
    """Vérifie qu'une valeur incorrecte est refusée."""
    with pytest.raises(ValueError, match="Montant invalide"):
        ApplicationComptaPrivee.texte_vers_montant("montant inconnu")