"""Tests du point d'entrée de ComptaPrivée AI."""

import fitz

from src.comptaprivee.main import analyser_pdf, afficher_bienvenue


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

    analyser_pdf(chemin_pdf)

    resultat = capsys.readouterr().out

    assert "facture_integration.pdf" in resultat
    assert "FAC-TEST-001" in resultat
    assert "500.00 CAD" in resultat
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

    analyser_pdf(chemin_pdf, chemin_csv)

    resultat = capsys.readouterr().out

    assert chemin_csv.exists()
    assert "Export CSV créé" in resultat

    contenu_csv = chemin_csv.read_text(encoding="utf-8-sig")

    assert "FAC-EXPORT-001" in contenu_csv
    assert "750.00" in contenu_csv