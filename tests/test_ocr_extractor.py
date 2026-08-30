"""Tests de l'extracteur OCR local."""

import shutil

import fitz
import pytest

from src.comptaprivee.ocr_extractor import extraire_texte_image


@pytest.mark.skipif(
    shutil.which("tesseract") is None,
    reason="Tesseract OCR n'est pas installé.",
)
def test_extraire_texte_image_avec_ocr(tmp_path) -> None:
    """Vérifie l'OCR avec une facture fictive transformée en image."""
    chemin_pdf = tmp_path / "source.pdf"
    chemin_image = tmp_path / "facture_scan.png"

    document = fitz.open()
    page = document.new_page()
    page.insert_text(
        (72, 100),
        (
            "FACTURE FICTIVE\n"
            "Numero : OCR-2026-001\n"
            "Total : 1350.00 CAD"
        ),
        fontsize=24,
    )
    document.save(chemin_pdf)

    image = page.get_pixmap(dpi=300, alpha=False)
    image.save(chemin_image)
    document.close()

    texte = extraire_texte_image(chemin_image)

    assert "FACTURE FICTIVE" in texte
    assert "OCR-2026-001" in texte
    assert "1350.00 CAD" in texte


def test_refuser_un_format_image_invalide(tmp_path) -> None:
    """Vérifie que les formats non pris en charge sont refusés."""
    chemin = tmp_path / "document.txt"
    chemin.touch()

    with pytest.raises(ValueError, match="non pris en charge"):
        extraire_texte_image(chemin)