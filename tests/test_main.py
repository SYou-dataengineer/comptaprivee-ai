"""Tests du point d'entrée de ComptaPrivée AI."""

from src.comptaprivee.main import afficher_bienvenue


def test_afficher_bienvenue(capsys) -> None:
    """Vérifie que le message de confidentialité est affiché."""
    afficher_bienvenue()

    resultat = capsys.readouterr().out

    assert "ComptaPrivée AI" in resultat
    assert "100 % local" in resultat
    assert "aucune donnée envoyée sur Internet" in resultat