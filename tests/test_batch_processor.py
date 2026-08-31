"""Tests du traitement local de plusieurs documents."""

import csv

import fitz
import pytest

from src.comptaprivee.batch_processor import (
    traiter_documents,
    traiter_et_exporter_documents,
)


def creer_pdf_test(
    chemin,
    numero: str,
    total: str,
) -> None:
    """Crée une facture PDF fictive pour les tests."""
    document = fitz.open()
    page = document.new_page()
    page.insert_text(
        (72, 72),
        (
            "FACTURE FICTIVE\n"
            f"Numero : {numero}\n"
            "Date : 2026-08-31\n"
            "Fournisseur : Entreprise Lot Exemple Inc.\n"
            "Client : Client Lot Fictif Inc.\n"
            f"Total : {total} CAD"
        ),
    )
    document.save(chemin)
    document.close()


def creer_pdf_complet_test(
    chemin,
    numero: str,
    total: str,
) -> None:
    """Crée une facture PDF contenant tous les montants."""
    document = fitz.open()
    page = document.new_page()
    page.insert_text(
        (72, 72),
        (
            "FACTURE FICTIVE\n"
            f"Numero : {numero}\n"
            "Date : 2026-08-31\n"
            "Fournisseur : Entreprise Validation Lot Inc.\n"
            "Client : Client Validation Lot Inc.\n"
            "Sous-total : 1000.00 CAD\n"
            "TPS : 50.00 CAD\n"
            "TVQ : 99.75 CAD\n"
            f"Total : {total} CAD"
        ),
    )
    document.save(chemin)
    document.close()


def lire_csv(chemin_csv) -> list[dict[str, str]]:
    """Lit le CSV produit par le traitement par lot."""
    with chemin_csv.open(
        "r",
        newline="",
        encoding="utf-8-sig",
    ) as fichier:
        return list(csv.DictReader(fichier, delimiter=";"))


def test_traiter_et_exporter_plusieurs_documents(tmp_path) -> None:
    """Vérifie le traitement de deux PDF dans un seul CSV."""
    premier_pdf = tmp_path / "facture_001.pdf"
    deuxieme_pdf = tmp_path / "facture_002.pdf"
    chemin_csv = tmp_path / "factures_groupees.csv"

    creer_pdf_test(
        premier_pdf,
        "LOT-TEST-001",
        "500.00",
    )
    creer_pdf_test(
        deuxieme_pdf,
        "LOT-TEST-002",
        "750.00",
    )

    resultat = traiter_et_exporter_documents(
        [premier_pdf, deuxieme_pdf],
        chemin_csv,
    )

    assert resultat.nombre_documents_reussis == 2
    assert resultat.nombre_documents_en_erreur == 0
    assert resultat.nombre_factures_valides == 0
    assert resultat.nombre_factures_a_verifier == 2
    assert chemin_csv.exists()

    lignes = lire_csv(chemin_csv)

    assert len(lignes) == 2
    assert lignes[0]["numero"] == "LOT-TEST-001"
    assert lignes[0]["total"] == "500.00"
    assert lignes[1]["numero"] == "LOT-TEST-002"
    assert lignes[1]["total"] == "750.00"


def test_continuer_apres_un_document_invalide(tmp_path) -> None:
    """Vérifie qu'une erreur n'arrête pas les autres documents."""
    chemin_pdf = tmp_path / "facture_valide.pdf"
    chemin_invalide = tmp_path / "document_invalide.txt"

    creer_pdf_test(
        chemin_pdf,
        "LOT-VALIDE-001",
        "900.00",
    )
    chemin_invalide.write_text(
        "Format non pris en charge",
        encoding="utf-8",
    )

    resultat = traiter_documents(
        [chemin_invalide, chemin_pdf]
    )

    assert resultat.nombre_documents_reussis == 1
    assert resultat.nombre_documents_en_erreur == 1
    assert resultat.factures[0].numero == "LOT-VALIDE-001"
    assert resultat.erreurs[0].chemin == chemin_invalide
    assert "Formats acceptés" in resultat.erreurs[0].message


def test_refuser_export_sans_facture_valide(tmp_path) -> None:
    """Vérifie qu'aucun CSV vide n'est créé."""
    chemin_invalide = tmp_path / "document_invalide.txt"
    chemin_csv = tmp_path / "resultat_vide.csv"

    chemin_invalide.write_text(
        "Document invalide",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Aucune facture valide",
    ):
        traiter_et_exporter_documents(
            [chemin_invalide],
            chemin_csv,
        )

    assert not chemin_csv.exists()


def test_bloquer_facture_incoherente_et_continuer(
    tmp_path,
) -> None:
    """Vérifie qu'une facture erronée ne bloque pas le lot."""
    chemin_valide = tmp_path / "facture_valide.pdf"
    chemin_incoherent = tmp_path / "facture_incoherente.pdf"
    chemin_csv = tmp_path / "factures_validees.csv"

    creer_pdf_complet_test(
        chemin_valide,
        "LOT-VALIDE-002",
        "1149.75",
    )
    creer_pdf_complet_test(
        chemin_incoherent,
        "LOT-ERREUR-001",
        "1300.00",
    )

    resultat = traiter_et_exporter_documents(
        [chemin_valide, chemin_incoherent],
        chemin_csv,
    )

    assert resultat.nombre_documents_reussis == 1
    assert resultat.nombre_documents_en_erreur == 1
    assert resultat.nombre_factures_valides == 1
    assert resultat.nombre_factures_a_verifier == 0

    assert resultat.factures[0].numero == "LOT-VALIDE-002"
    assert resultat.erreurs[0].chemin == chemin_incoherent
    assert (
        "Validation comptable échouée"
        in resultat.erreurs[0].message
    )
    assert "incohérent" in resultat.erreurs[0].message

    lignes = lire_csv(chemin_csv)

    assert len(lignes) == 1
    assert lignes[0]["numero"] == "LOT-VALIDE-002"
    assert lignes[0]["total"] == "1149.75"