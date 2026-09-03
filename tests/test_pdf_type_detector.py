"""Tests de détection PDF texte / scan / mixte."""

import fitz
import pytest

from src.comptaprivee.pdf_type_detector import analyser_pdf


def _creer_image_png(chemin) -> None:
    doc = fitz.open()
    page = doc.new_page(width=200, height=100)
    page.insert_text((20, 50), "IMAGE TEST")
    pix = page.get_pixmap()
    pix.save(chemin)
    doc.close()


def test_detecter_pdf_texte(tmp_path) -> None:
    chemin = tmp_path / "texte.pdf"

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (72, 72),
        "Facture FAC-001 fournisseur exemple "
        "sous-total 100 TPS 5 TVQ 9.98 total 114.98",
    )
    doc.save(chemin)
    doc.close()

    analyse = analyser_pdf(chemin)

    assert analyse.type_document == "texte"
    assert analyse.necessite_ocr is False
    assert analyse.pages_ocr == ()


def test_detecter_pdf_scan(tmp_path) -> None:
    image = tmp_path / "scan.png"
    _creer_image_png(image)

    chemin = tmp_path / "scan.pdf"
    doc = fitz.open()
    page = doc.new_page(width=200, height=100)
    page.insert_image(page.rect, filename=str(image))
    doc.save(chemin)
    doc.close()

    analyse = analyser_pdf(chemin)

    assert analyse.type_document == "scan"
    assert analyse.necessite_ocr is True
    assert analyse.pages_ocr == (1,)
    assert analyse.pages[0].type_page == "scan"


def test_detecter_pdf_mixte(tmp_path) -> None:
    image = tmp_path / "scan.png"
    _creer_image_png(image)

    chemin = tmp_path / "mixte.pdf"
    doc = fitz.open()

    page1 = doc.new_page()
    page1.insert_text(
        (72, 72),
        "Page texte avec suffisamment de contenu "
        "pour ne pas nécessiter de reconnaissance OCR.",
    )

    page2 = doc.new_page(width=200, height=100)
    page2.insert_image(page2.rect, filename=str(image))

    doc.save(chemin)
    doc.close()

    analyse = analyser_pdf(chemin)

    assert analyse.type_document == "mixte"
    assert analyse.necessite_ocr is True
    assert analyse.pages_ocr == (2,)


def test_refuser_fichier_non_pdf(tmp_path) -> None:
    chemin = tmp_path / "test.txt"
    chemin.write_text("test", encoding="utf-8")

    with pytest.raises(ValueError):
        analyser_pdf(chemin)


def test_refuser_seuil_invalide(tmp_path) -> None:
    chemin = tmp_path / "vide.pdf"

    doc = fitz.open()
    doc.new_page()
    doc.save(chemin)
    doc.close()

    with pytest.raises(ValueError):
        analyser_pdf(
            chemin,
            seuil_texte=0,
        )
