"""Tests de détection des tableaux PDF."""

from __future__ import annotations

import fitz


def _creer_pdf_avec_tableau(chemin) -> None:
    doc = fitz.open()
    page = doc.new_page(width=500, height=300)

    xs = [40, 160, 280, 380, 460]
    ys = [40, 80, 120, 160]

    for x in xs:
        page.draw_line((x, ys[0]), (x, ys[-1]))

    for y in ys:
        page.draw_line((xs[0], y), (xs[-1], y))

    donnees = [
        ["Date", "Fournisseur", "TPS", "Total"],
        ["2026-09-01", "ABC Inc.", "5.00", "114.98"],
        ["2026-09-02", "XYZ Inc.", "12.50", "287.44"],
    ]

    for row_idx, ligne in enumerate(donnees):
        for col_idx, valeur in enumerate(ligne):
            page.insert_text(
                (
                    xs[col_idx] + 5,
                    ys[row_idx] + 25,
                ),
                valeur,
                fontsize=9,
            )

    doc.save(chemin)
    doc.close()


def test_extraire_tableau_pdf_structure(tmp_path) -> None:
    from src.comptaprivee.pdf_table_extractor import extraire_tableaux_pdf

    source = tmp_path / "tableau.pdf"
    _creer_pdf_avec_tableau(source)

    tableaux = extraire_tableaux_pdf(source)

    assert len(tableaux) >= 1
    premier = tableaux[0]
    assert premier.numero_page == 1
    assert premier.numero_tableau == 1
    assert premier.lignes[0][:4] == [
        "Date",
        "Fournisseur",
        "TPS",
        "Total",
    ]
    assert premier.lignes[1][1] == "ABC Inc."
    assert premier.lignes[2][3] == "287.44"


def test_compter_tableaux_pdf(tmp_path) -> None:
    from src.comptaprivee.pdf_table_extractor import compter_tableaux_pdf

    source = tmp_path / "tableau.pdf"
    _creer_pdf_avec_tableau(source)

    assert compter_tableaux_pdf(source) >= 1


def test_pdf_sans_tableau_retourne_liste_vide(tmp_path) -> None:
    from src.comptaprivee.pdf_table_extractor import extraire_tableaux_pdf

    source = tmp_path / "texte.pdf"

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (72, 72),
        "Document comptable sans tableau trace.",
    )
    doc.save(source)
    doc.close()

    assert extraire_tableaux_pdf(source) == []


def test_selection_pages_tableaux_pdf(tmp_path) -> None:
    from src.comptaprivee.pdf_table_extractor import extraire_tableaux_pdf

    source = tmp_path / "multi.pdf"

    doc = fitz.open()
    page1 = doc.new_page()
    page1.insert_text((72, 72), "Page 1 sans tableau")

    page2 = doc.new_page(width=500, height=300)
    xs = [40, 160, 280]
    ys = [40, 80, 120]

    for x in xs:
        page2.draw_line((x, ys[0]), (x, ys[-1]))
    for y in ys:
        page2.draw_line((xs[0], y), (xs[-1], y))

    page2.insert_text((45, 65), "A")
    page2.insert_text((165, 65), "B")
    page2.insert_text((45, 105), "1")
    page2.insert_text((165, 105), "2")

    doc.save(source)
    doc.close()

    tableaux = extraire_tableaux_pdf(
        source,
        pages="2",
    )

    assert len(tableaux) >= 1
    assert all(t.numero_page == 2 for t in tableaux)


def test_refuse_fichier_non_pdf(tmp_path) -> None:
    import pytest

    from src.comptaprivee.pdf_table_extractor import extraire_tableaux_pdf

    source = tmp_path / "notes.txt"
    source.write_text("test", encoding="utf-8")

    with pytest.raises(ValueError):
        extraire_tableaux_pdf(source)

def test_tableau_pdf_scane_utilise_fallback_ocr(
    tmp_path,
    monkeypatch,
) -> None:
    import fitz

    from src.comptaprivee import pdf_table_extractor as pte

    source = tmp_path / "scan.pdf"

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (72, 72),
        "scan",
    )
    doc.save(source)
    doc.close()

    monkeypatch.setattr(
        pte,
        "_extraire_tableau_ocr_page_pdf",
        lambda page, numero_page: [
            ["Date", "Total"],
            ["2026-09-01", "114.98"],
        ],
    )

    tableaux = pte.extraire_tableaux_pdf(source)

    assert len(tableaux) == 1
    assert tableaux[0].numero_page == 1
    assert tableaux[0].lignes[0] == ["Date", "Total"]


def test_tableau_pdf_natif_reste_prioritaire(
    tmp_path,
    monkeypatch,
) -> None:
    from src.comptaprivee import pdf_table_extractor as pte

    source = tmp_path / "tableau.pdf"
    _creer_pdf_avec_tableau(source)

    appele = {"ocr": False}

    def faux_ocr(page, numero_page):
        appele["ocr"] = True
        return [["OCR"]]

    monkeypatch.setattr(
        pte,
        "_extraire_tableau_ocr_page_pdf",
        faux_ocr,
    )

    tableaux = pte.extraire_tableaux_pdf(source)

    assert len(tableaux) >= 1
    assert appele["ocr"] is False


def test_fallback_ocr_vide_ne_cree_pas_tableau(
    tmp_path,
    monkeypatch,
) -> None:
    import fitz

    from src.comptaprivee import pdf_table_extractor as pte

    source = tmp_path / "vide.pdf"

    doc = fitz.open()
    doc.new_page()
    doc.save(source)
    doc.close()

    monkeypatch.setattr(
        pte,
        "_extraire_tableau_ocr_page_pdf",
        lambda page, numero_page: [],
    )

    assert pte.extraire_tableaux_pdf(source) == []
