"""Tests de l'extracteur PDF local."""

import shutil

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


@pytest.mark.skipif(
    shutil.which("tesseract") is None,
    reason="Tesseract OCR n'est pas installé.",
)
def test_extraire_texte_pdf_numerise_avec_ocr(tmp_path) -> None:
    """Vérifie l'OCR automatique d'un PDF sans texte sélectionnable."""
    chemin_source = tmp_path / "source.pdf"
    chemin_scan = tmp_path / "facture_numerisee.pdf"

    source = fitz.open()
    page_source = source.new_page(width=595, height=842)
    page_source.insert_text(
        (72, 100),
        (
            "FACTURE NUMERISEE\n"
            "Numero : SCAN-2026-001\n"
            "Total : 1450.00 CAD"
        ),
        fontsize=24,
    )
    source.save(chemin_source)

    image = page_source.get_pixmap(dpi=300, alpha=False)
    source.close()

    scan = fitz.open()
    page_scan = scan.new_page(width=595, height=842)
    page_scan.insert_image(
        page_scan.rect,
        pixmap=image,
    )
    scan.save(chemin_scan)
    scan.close()

    texte = extraire_texte_pdf(chemin_scan)

    assert "FACTURE NUMERISEE" in texte
    assert "SCAN-2026-001" in texte
    assert "1450.00 CAD" in texte

def test_pdf_multi_pages_affiche_separateur_sans_perdre_limite_logique(
    tmp_path,
) -> None:
    import fitz

    from src.comptaprivee.pdf_extractor import extraire_texte_pdf

    chemin = tmp_path / "deux_pages.pdf"

    doc = fitz.open()
    page1 = doc.new_page()
    page1.insert_text(
        (72, 72),
        "Facture : PAGE-1 avec suffisamment de texte pour extraction native.",
    )
    page2 = doc.new_page()
    page2.insert_text(
        (72, 72),
        "Facture : PAGE-2 avec suffisamment de texte pour extraction native.",
    )
    doc.save(chemin)
    doc.close()

    texte = extraire_texte_pdf(chemin)

    assert "PAGE-1" in texte
    assert "PAGE-2" in texte
    assert "--- Page suivante ---" in texte
    assert "\f" not in texte

    blocs = texte.split("\n\n--- Page suivante ---\n\n")
    assert len(blocs) == 2
    assert "PAGE-1" in blocs[0]
    assert "PAGE-2" in blocs[1]

