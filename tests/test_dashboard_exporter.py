"""Tests de l'export du tableau de bord."""

from decimal import Decimal

import fitz
import pytest

from src.comptaprivee.dashboard import ResumeTableauBord
from src.comptaprivee.dashboard_exporter import (
    exporter_tableau_bord_csv,
    exporter_tableau_bord_pdf,
)


def creer_resume() -> ResumeTableauBord:
    return ResumeTableauBord(
        nombre_factures=2,
        sous_total=Decimal("300.00"),
        tps=Decimal("15.00"),
        tvq=Decimal("29.93"),
        total=Decimal("344.93"),
        total_par_fournisseur=(
            ("Alpha", Decimal("229.95")),
            ("Beta", Decimal("114.98")),
        ),
    )


def test_exporter_tableau_bord_csv(tmp_path) -> None:
    chemin = tmp_path / "rapport.csv"

    resultat = exporter_tableau_bord_csv(
        creer_resume(),
        chemin,
        date_debut="2026-08-01",
        date_fin="2026-08-31",
        fournisseur="Alpha",
    )

    assert resultat == chemin
    contenu = chemin.read_text(encoding="utf-8-sig")
    assert "Factures,2" in contenu
    assert "Total,344.93" in contenu
    assert "Alpha,229.95" in contenu


def test_exporter_tableau_bord_pdf(tmp_path) -> None:
    chemin = tmp_path / "rapport.pdf"

    resultat = exporter_tableau_bord_pdf(
        creer_resume(),
        chemin,
        date_debut="2026-08-01",
        date_fin="2026-08-31",
        fournisseur="Alpha",
    )

    assert resultat == chemin
    assert chemin.exists()
    assert chemin.stat().st_size > 0

    document = fitz.open(chemin)
    try:
        texte = " ".join(
            page.get_text()
            for page in document
        )
    finally:
        document.close()

    assert "Rapport du tableau de bord comptable" in texte
    assert "344.93 CAD" in texte
    assert "Alpha" in texte


def test_refuser_extension_csv_invalide(tmp_path) -> None:
    with pytest.raises(ValueError, match="format CSV"):
        exporter_tableau_bord_csv(
            creer_resume(),
            tmp_path / "rapport.txt",
        )


def test_refuser_extension_pdf_invalide(tmp_path) -> None:
    with pytest.raises(ValueError, match="format PDF"):
        exporter_tableau_bord_pdf(
            creer_resume(),
            tmp_path / "rapport.txt",
        )


def test_export_dashboard_pdf_affiche_societe(
    tmp_path,
    monkeypatch,
) -> None:
    from src.comptaprivee import dashboard_exporter

    monkeypatch.setattr(
        dashboard_exporter,
        "lire_nom_societe",
        lambda: "Cabinet Exemple CPA Inc.",
    )

    chemin = tmp_path / "rapport_societe.pdf"

    exporter_tableau_bord_pdf(
        creer_resume(),
        chemin,
    )

    document = fitz.open(chemin)
    try:
        texte = " ".join(
            page.get_text()
            for page in document
        )
    finally:
        document.close()

    assert "Cabinet Exemple CPA Inc." in texte


def test_export_dashboard_csv_affiche_societe(
    tmp_path,
    monkeypatch,
) -> None:
    from src.comptaprivee import dashboard_exporter

    monkeypatch.setattr(
        dashboard_exporter,
        "lire_nom_societe",
        lambda: "Cabinet Exemple CPA Inc.",
    )

    chemin = tmp_path / "rapport_societe.csv"

    exporter_tableau_bord_csv(
        creer_resume(),
        chemin,
    )

    contenu = chemin.read_text(encoding="utf-8-sig")
    assert "Societe comptable,Cabinet Exemple CPA Inc." in contenu

def test_export_dashboard_pdf_affiche_coordonnees(
    tmp_path,
    monkeypatch,
) -> None:
    from src.comptaprivee import dashboard_exporter
    from src.comptaprivee.company_profile import ProfilSociete

    monkeypatch.setattr(
        dashboard_exporter,
        "lire_profil_societe",
        lambda: ProfilSociete(
            nom_societe="Cabinet Exemple CPA Inc.",
            adresse="123 rue Exemple",
            ville="Montréal",
            province="QC",
            telephone="514-555-0100",
        ),
    )

    chemin = tmp_path / "rapport_coordonnees.pdf"

    exporter_tableau_bord_pdf(
        creer_resume(),
        chemin,
    )

    document = fitz.open(chemin)
    try:
        texte = " ".join(
            page.get_text()
            for page in document
        )
    finally:
        document.close()

    assert "123 rue Exemple" in texte
    assert "514-555-0100" in texte

