"""Tests du lecteur local de documents Word DOCX."""

from zipfile import ZipFile

import pytest

from src.comptaprivee.word_extractor import extraire_texte_word


def test_extraire_texte_word(tmp_path) -> None:
    """Vérifie l'extraction depuis un document Word fictif."""
    chemin_docx = tmp_path / "facture_fictive.docx"

    contenu_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <w:document
        xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
        <w:body>
            <w:p><w:r><w:t>FACTURE WORD FICTIVE</w:t></w:r></w:p>
            <w:p><w:r><w:t>Numero : WORD-2026-001</w:t></w:r></w:p>
            <w:p><w:r><w:t>Total : 825.00 CAD</w:t></w:r></w:p>
        </w:body>
    </w:document>
    """

    with ZipFile(chemin_docx, "w") as archive:
        archive.writestr("word/document.xml", contenu_xml)

    texte = extraire_texte_word(chemin_docx)

    assert "FACTURE WORD FICTIVE" in texte
    assert "WORD-2026-001" in texte
    assert "825.00 CAD" in texte


def test_refuser_un_fichier_non_docx(tmp_path) -> None:
    """Vérifie que les autres extensions sont refusées."""
    chemin_pdf = tmp_path / "document.pdf"
    chemin_pdf.touch()

    with pytest.raises(ValueError, match="format DOCX"):
        extraire_texte_word(chemin_pdf)


def test_signaler_un_document_word_introuvable(tmp_path) -> None:
    """Vérifie qu'un document absent produit une erreur claire."""
    chemin_docx = tmp_path / "document_absent.docx"

    with pytest.raises(FileNotFoundError, match="Fichier introuvable"):
        extraire_texte_word(chemin_docx)