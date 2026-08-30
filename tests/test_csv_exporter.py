"""Tests de l'export local des factures en CSV."""

import csv
from decimal import Decimal

import pytest

from src.comptaprivee.csv_exporter import exporter_facture_csv
from src.comptaprivee.facture_parser import DonneesFacture


def creer_facture_test() -> DonneesFacture:
    """Crée des données comptables entièrement fictives."""
    return DonneesFacture(
        numero="FAC-TEST-001",
        date="2026-08-29",
        fournisseur="Entreprise Exemple Inc.",
        client="Client Fictif Inc.",
        sous_total=Decimal("1000.00"),
        tps=Decimal("50.00"),
        tvq=Decimal("99.75"),
        total=Decimal("1149.75"),
    )


def test_exporter_facture_csv(tmp_path) -> None:
    """Vérifie le contenu du fichier CSV exporté."""
    chemin_csv = tmp_path / "facture.csv"

    resultat = exporter_facture_csv(creer_facture_test(), chemin_csv)

    assert resultat == chemin_csv
    assert chemin_csv.exists()

    with chemin_csv.open(
        "r",
        newline="",
        encoding="utf-8-sig",
    ) as fichier:
        lignes = list(csv.DictReader(fichier, delimiter=";"))

    assert len(lignes) == 1
    assert lignes[0]["numero"] == "FAC-TEST-001"
    assert lignes[0]["fournisseur"] == "Entreprise Exemple Inc."
    assert lignes[0]["tps"] == "50.00"
    assert lignes[0]["total"] == "1149.75"


def test_refuser_une_extension_non_csv(tmp_path) -> None:
    """Vérifie que l'export refuse une mauvaise extension."""
    chemin_invalide = tmp_path / "facture.xlsx"

    with pytest.raises(ValueError, match="format CSV"):
        exporter_facture_csv(creer_facture_test(), chemin_invalide)