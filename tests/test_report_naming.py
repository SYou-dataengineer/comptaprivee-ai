"""Tests du nommage automatique des rapports."""

from datetime import date

from src.comptaprivee.report_naming import (
    nettoyer_nom_fichier,
    nom_fichier_rapport,
)


def test_nettoyer_nom_fichier() -> None:
    assert nettoyer_nom_fichier("Safouani CPA Inc.") == "Safouani_CPA_Inc"


def test_nom_rapport_avec_periode() -> None:
    assert nom_fichier_rapport(
        "Safouani CPA Inc.",
        "Resume comptable",
        "pdf",
        date_debut="2026-08-01",
        date_fin="2026-08-31",
    ) == (
        "Safouani_CPA_Inc_Resume_comptable_"
        "2026-08-01_au_2026-08-31.pdf"
    )


def test_nom_rapport_sans_periode() -> None:
    assert nom_fichier_rapport(
        "Cabinet Exemple",
        "Tableau de bord",
        ".csv",
        date_reference=date(2026, 9, 1),
    ) == "Cabinet_Exemple_Tableau_de_bord_2026-09-01.csv"


def test_nom_rapport_accepte_accent() -> None:
    assert nettoyer_nom_fichier(
        "Société Comptabilité Québec"
    ) == "Societe_Comptabilite_Quebec"
