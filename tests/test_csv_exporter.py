"""Tests de l'export local des factures en CSV."""

import csv
from decimal import Decimal

import pytest

from src.comptaprivee.csv_exporter import (
    exporter_facture_csv,
    exporter_factures_csv,
)
from src.comptaprivee.facture_parser import DonneesFacture


def creer_facture_test() -> DonneesFacture:
    """Crée une première facture entièrement fictive."""
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


def creer_deuxieme_facture_test() -> DonneesFacture:
    """Crée une deuxième facture entièrement fictive."""
    return DonneesFacture(
        numero="FAC-TEST-002",
        date="2026-08-30",
        fournisseur="Deuxième Entreprise Exemple Inc.",
        client="Deuxième Client Fictif Inc.",
        sous_total=Decimal("2000.00"),
        tps=Decimal("100.00"),
        tvq=Decimal("199.50"),
        total=Decimal("2299.50"),
    )


def lire_lignes_csv(chemin_csv) -> list[dict[str, str]]:
    """Lit les lignes d'un fichier CSV de test."""
    with chemin_csv.open(
        "r",
        newline="",
        encoding="utf-8-sig",
    ) as fichier:
        return list(csv.DictReader(fichier, delimiter=";"))


def test_exporter_facture_csv(tmp_path) -> None:
    """Vérifie le contenu d'un CSV contenant une seule facture."""
    chemin_csv = tmp_path / "facture.csv"

    resultat = exporter_facture_csv(
        creer_facture_test(),
        chemin_csv,
    )

    assert resultat == chemin_csv
    assert chemin_csv.exists()

    lignes = lire_lignes_csv(chemin_csv)

    assert len(lignes) == 1
    assert lignes[0]["numero"] == "FAC-TEST-001"
    assert lignes[0]["fournisseur"] == "Entreprise Exemple Inc."
    assert lignes[0]["tps"] == "50.00"
    assert lignes[0]["total"] == "1149.75"


def test_exporter_plusieurs_factures_csv(tmp_path) -> None:
    """Vérifie l'export de plusieurs factures dans un seul CSV."""
    chemin_csv = tmp_path / "factures_groupees.csv"
    factures = [
        creer_facture_test(),
        creer_deuxieme_facture_test(),
    ]

    resultat = exporter_factures_csv(
        factures,
        chemin_csv,
    )

    assert resultat == chemin_csv
    assert chemin_csv.exists()

    lignes = lire_lignes_csv(chemin_csv)

    assert len(lignes) == 2

    assert lignes[0]["numero"] == "FAC-TEST-001"
    assert lignes[0]["total"] == "1149.75"

    assert lignes[1]["numero"] == "FAC-TEST-002"
    assert lignes[1]["fournisseur"] == (
        "Deuxième Entreprise Exemple Inc."
    )
    assert lignes[1]["total"] == "2299.50"


def test_refuser_une_liste_de_factures_vide(tmp_path) -> None:
    """Vérifie qu'un export vide est refusé."""
    chemin_csv = tmp_path / "factures_vides.csv"

    with pytest.raises(ValueError, match="Aucune facture"):
        exporter_factures_csv([], chemin_csv)

    assert not chemin_csv.exists()


def test_refuser_une_extension_non_csv(tmp_path) -> None:
    """Vérifie que l'export refuse une mauvaise extension."""
    chemin_invalide = tmp_path / "facture.xlsx"

    with pytest.raises(ValueError, match="format CSV"):
        exporter_facture_csv(
            creer_facture_test(),
            chemin_invalide,
        )