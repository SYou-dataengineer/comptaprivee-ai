"""Tests de l'extracteur PDF local."""

import fitz
import pytest

from src.comptaprivee.pdf_extractor import extraire_texte_pdf


def test_extraire_texte_pdf(tmp_path) -> None:
    """Vérifie l'extraction depuis un faux document comptable."""
    chemin_pdf = tmp_path / "facture_fictive.pdf"

    document = fitz.open()
    page = document.new_page()
    page.insert_text(
        (72, 72),
        "FACTURE FICTIVE\nNumero : FAC-2026-001\nTotal : 1250,00 CAD",
    )
    document.save(chemin_pdf)
    document.close()

    texte = extraire_texte_pdf(chemin_pdf)

    assert "FACTURE FICTIVE" in texte
    assert "FAC-2026-001" in texte
    assert "1250,00 CAD" in texte


def test_refuser_un_fichier_non_pdf(tmp_path) -> None:
    """Vérifie que les autres formats sont refusés."""
    chemin_word = tmp_path / "document.docx"
    chemin_word.touch()

    with pytest.raises(ValueError, match="format PDF"):
        extraire_texte_pdf(chemin_word)


def test_signaler_un_pdf_introuvable(tmp_path) -> None:
    """Vérifie qu'un PDF absent produit une erreur claire."""
    chemin_pdf = tmp_path / "document_absent.pdf"

    with pytest.raises(FileNotFoundError, match="Fichier introuvable"):
        extraire_texte_pdf(chemin_pdf)