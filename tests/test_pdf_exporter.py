"""Tests de l'export local des factures au format PDF."""

from decimal import Decimal

import fitz
import pytest

from src.comptaprivee.facture_parser import DonneesFacture
from src.comptaprivee.pdf_exporter import exporter_facture_pdf


def creer_facture() -> DonneesFacture:
    """Construit une facture de test."""
    return DonneesFacture(
        numero="PDF-TEST-001",
        date="2026-09-01",
        fournisseur="Fournisseur PDF",
        client="Client PDF",
        sous_total=Decimal("100.00"),
        tps=Decimal("5.00"),
        tvq=Decimal("9.98"),
        total=Decimal("114.98"),
    )


def test_exporter_facture_pdf(tmp_path) -> None:
    """Le PDF est cree et contient les donnees principales."""
    chemin = tmp_path / "facture.pdf"

    resultat = exporter_facture_pdf(
        creer_facture(),
        chemin,
        identifiant=12,
        date_enregistrement="2026-09-01 10:30:00",
    )

    assert resultat == chemin
    assert chemin.exists()
    assert chemin.stat().st_size > 0

    document = fitz.open(chemin)
    try:
        texte = " ".join(page.get_text() for page in document)
    finally:
        document.close()

    assert "PDF-TEST-001" in texte
    assert "Fournisseur PDF" in texte
    assert "114.98 CAD" in texte
    assert "2026-09-01 10:30:00" in texte


def test_refuser_extension_non_pdf(tmp_path) -> None:
    """Une extension autre que PDF est refusee."""
    with pytest.raises(ValueError, match="format PDF"):
        exporter_facture_pdf(
            creer_facture(),
            tmp_path / "facture.txt",
        )
