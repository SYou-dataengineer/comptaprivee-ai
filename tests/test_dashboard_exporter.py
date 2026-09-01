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
