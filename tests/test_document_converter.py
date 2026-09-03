"""Tests du moteur de conversion locale."""

from pathlib import Path

import pytest

from src.comptaprivee.document_converter import (
    CONVERSIONS_SUPPORTEES,
    convertir_document,
    image_vers_pdf,
)


def test_liste_conversions_supportees() -> None:
    assert "Word → PDF" in CONVERSIONS_SUPPORTEES
    assert "Excel → PDF" in CONVERSIONS_SUPPORTEES
    assert "Excel → CSV" in CONVERSIONS_SUPPORTEES
    assert "Image → PDF" in CONVERSIONS_SUPPORTEES


def test_refuser_conversion_inconnue(tmp_path) -> None:
    source = tmp_path / "test.txt"
    source.write_text("demo", encoding="utf-8")

    with pytest.raises(ValueError):
        convertir_document(
            "TXT → MP3",
            source,
        )


def test_refuser_source_inexistante(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        image_vers_pdf(
            tmp_path / "absente.png",
        )


def test_refuser_mauvaise_extension_image(tmp_path) -> None:
    source = tmp_path / "document.txt"
    source.write_text("demo", encoding="utf-8")

    with pytest.raises(ValueError):
        image_vers_pdf(source)


def test_image_vers_pdf(tmp_path) -> None:
    import fitz

    source = tmp_path / "image.png"
    destination = tmp_path / "image_convertie.pdf"

    document = fitz.open()
    page = document.new_page(width=200, height=120)
    pixmap = page.get_pixmap()
    pixmap.save(source)
    document.close()

    resultat = image_vers_pdf(
        source,
        destination,
    )

    assert resultat.destination == destination
    assert destination.exists()

    pdf = fitz.open(destination)
    try:
        assert pdf.page_count == 1
    finally:
        pdf.close()


def test_destination_pdf_obligatoire(tmp_path) -> None:
    import fitz

    source = tmp_path / "image.png"
    mauvaise_destination = tmp_path / "sortie.txt"

    document = fitz.open()
    page = document.new_page(width=50, height=50)
    page.get_pixmap().save(source)
    document.close()

    with pytest.raises(ValueError):
        image_vers_pdf(
            source,
            mauvaise_destination,
        )

def _creer_pdf_tableau_test(chemin) -> None:
    import fitz
    doc = fitz.open()
    page = doc.new_page(width=400, height=260)
    xs = [40, 150, 280, 360]
    ys = [40, 70, 100, 130]
    for x in xs:
        page.draw_line((x, ys[0]), (x, ys[-1]))
    for y in ys:
        page.draw_line((xs[0], y), (xs[-1], y))
    data = [
        ["Date", "Fournisseur", "Total"],
        ["2026-09-01", "A", "114.98"],
        ["2026-09-02", "B", "287.44"],
    ]
    for r, row in enumerate(data):
        for c, value in enumerate(row):
            page.insert_text((xs[c] + 4, ys[r] + 20), value, fontsize=8)
    doc.save(chemin)
    doc.close()


def test_conversions_avancees_dans_liste() -> None:
    from src.comptaprivee.document_converter import CONVERSIONS_SUPPORTEES
    for nom in ("CSV → Excel", "PDF → CSV", "PDF → Excel", "PDF → Word"):
        assert nom in CONVERSIONS_SUPPORTEES


def test_csv_vers_excel(tmp_path) -> None:
    from openpyxl import load_workbook
    from src.comptaprivee.document_converter import csv_vers_excel
    src = tmp_path / "a.csv"
    dst = tmp_path / "a.xlsx"
    src.write_text("Date,Fournisseur,Total\n2026-09-01,A,114.98\n", encoding="utf-8")
    csv_vers_excel(src, dst)
    wb = load_workbook(dst)
    try:
        ws = wb.active
        assert ws["A1"].value == "Date"
        assert ws["B2"].value == "A"
    finally:
        wb.close()


def test_pdf_vers_csv(tmp_path) -> None:
    from src.comptaprivee.document_converter import pdf_vers_csv
    src = tmp_path / "t.pdf"
    dst = tmp_path / "t.csv"
    _creer_pdf_tableau_test(src)
    pdf_vers_csv(src, dst)
    contenu = dst.read_text(encoding="utf-8-sig")
    assert "Fournisseur" in contenu
    assert "114.98" in contenu


def test_pdf_vers_excel(tmp_path) -> None:
    from openpyxl import load_workbook
    from src.comptaprivee.document_converter import pdf_vers_excel
    src = tmp_path / "t.pdf"
    dst = tmp_path / "t.xlsx"
    _creer_pdf_tableau_test(src)
    pdf_vers_excel(src, dst)
    wb = load_workbook(dst)
    try:
        ws = wb.worksheets[0]
        assert ws["A1"].value == "Date"
        assert ws["C2"].value == "114.98"
    finally:
        wb.close()


def test_pdf_vers_word(tmp_path) -> None:
    import fitz
    from docx import Document
    from src.comptaprivee.document_converter import pdf_vers_word
    src = tmp_path / "t.pdf"
    dst = tmp_path / "t.docx"
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "Facture FAC-001 - Total 114.98 CAD")
    pdf.save(src)
    pdf.close()
    pdf_vers_word(src, dst)
    doc = Document(dst)
    texte = "\n".join(p.text for p in doc.paragraphs)
    assert "FAC-001" in texte

def test_pdf_vers_word_recree_tableau(tmp_path) -> None:
    import fitz
    from docx import Document
    from src.comptaprivee.document_converter import pdf_vers_word

    source = tmp_path / "tableau_word.pdf"
    destination = tmp_path / "tableau_word.docx"

    pdf = fitz.open()
    page = pdf.new_page(width=400, height=260)

    xs = [40, 150, 280, 360]
    ys = [40, 70, 100, 130]

    for x in xs:
        page.draw_line((x, ys[0]), (x, ys[-1]))
    for y in ys:
        page.draw_line((xs[0], y), (xs[-1], y))

    data = [
        ["Date", "Fournisseur", "Total"],
        ["2026-09-01", "A", "114.98"],
        ["2026-09-02", "B", "287.44"],
    ]

    for r, row in enumerate(data):
        for c, value in enumerate(row):
            page.insert_text(
                (xs[c] + 4, ys[r] + 20),
                value,
                fontsize=8,
            )

    pdf.save(source)
    pdf.close()

    pdf_vers_word(source, destination)

    doc = Document(destination)

    assert len(doc.tables) == 1
    assert doc.tables[0].cell(0, 0).text == "Date"
    assert doc.tables[0].cell(1, 1).text == "A"
    assert doc.tables[0].cell(2, 2).text == "287.44"


def test_pdf_vers_word_evite_dupliquer_texte_tableau(tmp_path) -> None:
    import fitz
    from docx import Document
    from src.comptaprivee.document_converter import pdf_vers_word

    source = tmp_path / "mixte.pdf"
    destination = tmp_path / "mixte.docx"

    pdf = fitz.open()
    page = pdf.new_page(width=400, height=300)
    page.insert_text((40, 30), "Rapport comptable")

    xs = [40, 180, 320]
    ys = [70, 100, 130]

    for x in xs:
        page.draw_line((x, ys[0]), (x, ys[-1]))
    for y in ys:
        page.draw_line((xs[0], y), (xs[-1], y))

    page.insert_text((45, 90), "Facture", fontsize=8)
    page.insert_text((185, 90), "Total", fontsize=8)
    page.insert_text((45, 120), "FAC-001", fontsize=8)
    page.insert_text((185, 120), "114.98", fontsize=8)

    pdf.save(source)
    pdf.close()

    pdf_vers_word(source, destination)

    doc = Document(destination)
    texte_paragraphes = "\n".join(
        p.text for p in doc.paragraphs
    )

    assert "Rapport comptable" in texte_paragraphes
    assert len(doc.tables) == 1
    assert "FAC-001" not in texte_paragraphes

def test_pdf_vers_word_fallback_ocr(
    tmp_path,
    monkeypatch,
) -> None:
    import fitz
    from docx import Document
    import src.comptaprivee.document_converter as dc

    source = tmp_path / "scan.pdf"
    destination = tmp_path / "scan.docx"

    doc = fitz.open()
    doc.new_page()
    doc.save(source)
    doc.close()

    monkeypatch.setattr(
        dc,
        "_extraire_ocr_pages_pdf",
        lambda _source: {
            1: "Facture FAC-OCR-001\nTotal 114.98 CAD"
        },
    )

    dc.pdf_vers_word(
        source,
        destination,
    )

    word = Document(destination)
    texte = "\n".join(
        p.text for p in word.paragraphs
    )

    assert "FAC-OCR-001" in texte
    assert "114.98" in texte


def test_pdf_vers_csv_fallback_ocr(
    tmp_path,
    monkeypatch,
) -> None:
    import fitz
    import src.comptaprivee.document_converter as dc

    source = tmp_path / "scan.pdf"
    destination = tmp_path / "scan.csv"

    doc = fitz.open()
    doc.new_page()
    doc.save(source)
    doc.close()

    monkeypatch.setattr(
        dc,
        "_extraire_ocr_pages_pdf",
        lambda _source: {
            1: "Facture FAC-OCR-001\nTotal 114.98 CAD"
        },
    )

    dc.pdf_vers_csv(
        source,
        destination,
    )

    contenu = destination.read_text(
        encoding="utf-8-sig"
    )

    assert "Texte OCR" in contenu
    assert "FAC-OCR-001" in contenu
    assert "114.98" in contenu


def test_pdf_vers_excel_fallback_ocr(
    tmp_path,
    monkeypatch,
) -> None:
    import fitz
    from openpyxl import load_workbook
    import src.comptaprivee.document_converter as dc

    source = tmp_path / "scan.pdf"
    destination = tmp_path / "scan.xlsx"

    doc = fitz.open()
    doc.new_page()
    doc.save(source)
    doc.close()

    monkeypatch.setattr(
        dc,
        "_extraire_ocr_pages_pdf",
        lambda _source: {
            1: "Facture FAC-OCR-001\nTotal 114.98 CAD"
        },
    )

    dc.pdf_vers_excel(
        source,
        destination,
    )

    wb = load_workbook(destination)
    try:
        assert "OCR_Page_1" in wb.sheetnames
        ws = wb["OCR_Page_1"]
        valeurs = [
            str(ws.cell(row=i, column=3).value or "")
            for i in range(1, ws.max_row + 1)
        ]
        texte = "\n".join(valeurs)
        assert "FAC-OCR-001" in texte
        assert "114.98" in texte
    finally:
        wb.close()
