"""Tests du point d'entrée de ComptaPrivée AI."""

from zipfile import ZipFile

import fitz

from src.comptaprivee.main import analyser_document, afficher_bienvenue


def test_afficher_bienvenue(capsys) -> None:
    """Vérifie que le message de confidentialité est affiché."""
    afficher_bienvenue()

    resultat = capsys.readouterr().out

    assert "ComptaPrivée AI" in resultat
    assert "100 % local" in resultat
    assert "aucune donnée envoyée sur Internet" in resultat


def test_analyser_pdf_affiche_le_document(tmp_path, capsys) -> None:
    """Vérifie l'analyse complète d'un PDF fictif."""
    chemin_pdf = tmp_path / "facture_integration.pdf"

    document = fitz.open()
    page = document.new_page()
    page.insert_text(
        (72, 72),
        "FACTURE FICTIVE\nNumero : FAC-TEST-001\nTotal : 500.00 CAD",
    )
    document.save(chemin_pdf)
    document.close()

    analyser_document(chemin_pdf)

    resultat = capsys.readouterr().out

    assert "facture_integration.pdf" in resultat
    assert "FAC-TEST-001" in resultat
    assert "Données structurées" in resultat
    assert "Numéro de facture : FAC-TEST-001" in resultat
    assert "Total : 500.00 CAD" in resultat


def test_analyser_pdf_exporte_un_csv(tmp_path, capsys) -> None:
    """Vérifie le pipeline complet du PDF jusqu'au CSV."""
    chemin_pdf = tmp_path / "facture_export.pdf"
    chemin_csv = tmp_path / "facture_export.csv"

    document = fitz.open()
    page = document.new_page()
    page.insert_text(
        (72, 72),
        (
            "FACTURE FICTIVE\n"
            "Numero : FAC-EXPORT-001\n"
            "Date : 2026-08-30\n"
            "Total : 750.00 CAD"
        ),
    )
    document.save(chemin_pdf)
    document.close()

    analyser_document(chemin_pdf, chemin_csv)

    resultat = capsys.readouterr().out
    contenu_csv = chemin_csv.read_text(encoding="utf-8-sig")

    assert chemin_csv.exists()
    assert "Export CSV créé" in resultat
    assert "FAC-EXPORT-001" in contenu_csv
    assert "750.00" in contenu_csv


def test_analyser_word_exporte_un_csv(tmp_path, capsys) -> None:
    """Vérifie le pipeline complet du document Word jusqu'au CSV."""
    chemin_docx = tmp_path / "facture_word.docx"
    chemin_csv = tmp_path / "facture_word.csv"

    contenu_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <w:document
        xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
        <w:body>
            <w:p><w:r><w:t>FACTURE WORD FICTIVE</w:t></w:r></w:p>
            <w:p><w:r><w:t>Numero : WORD-TEST-001</w:t></w:r></w:p>
            <w:p><w:r><w:t>Date : 2026-08-30</w:t></w:r></w:p>
            <w:p><w:r><w:t>Total : 925.00 CAD</w:t></w:r></w:p>
        </w:body>
    </w:document>
    """

    with ZipFile(chemin_docx, "w") as archive:
        archive.writestr("word/document.xml", contenu_xml)

    analyser_document(chemin_docx, chemin_csv)

    resultat = capsys.readouterr().out
    contenu_csv = chemin_csv.read_text(encoding="utf-8-sig")

    assert chemin_csv.exists()
    assert "WORD-TEST-001" in resultat
    assert "Total : 925.00 CAD" in resultat
    assert "Export CSV créé" in resultat
    assert "WORD-TEST-001" in contenu_csv
    assert "925.00" in contenu_csv


def test_analyser_image_exporte_un_csv(tmp_path, capsys) -> None:
    """Vérifie le pipeline complet de l'image jusqu'au CSV."""
    chemin_image = tmp_path / "facture_image.png"
    chemin_csv = tmp_path / "facture_image.csv"

    document = fitz.open()
    page = document.new_page()
    page.insert_text(
        (72, 100),
        (
            "FACTURE IMAGE FICTIVE\n"
            "Numero : IMAGE-TEST-001\n"
            "Date : 2026-08-30\n"
            "Total : 650.00 CAD"
        ),
        fontsize=24,
    )

    image = page.get_pixmap(dpi=300, alpha=False)
    image.save(chemin_image)
    document.close()

    analyser_document(chemin_image, chemin_csv)

    resultat = capsys.readouterr().out
    contenu_csv = chemin_csv.read_text(encoding="utf-8-sig")

    assert chemin_csv.exists()
    assert "IMAGE-TEST-001" in resultat
    assert "Total : 650.00 CAD" in resultat
    assert "Export CSV créé" in resultat
    assert "IMAGE-TEST-001" in contenu_csv
    assert "650.00" in contenu_csv