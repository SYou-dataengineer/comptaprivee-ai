"""Tests de la file locale des anomalies OCR."""

import csv

from openpyxl import Workbook

from src.comptaprivee.ocr_review_queue import (
    lister_alertes_ocr_a_verifier,
    synchroniser_export_ocr_a_verifier,
)
from src.comptaprivee.review_queue import (
    NiveauVerification,
)


ENTETE = [
    "Date",
    "Fournisseur",
    "No facture",
    "Sous-total",
    "TPS",
    "TVQ",
    "Total",
    "Validation OCR",
]


def test_synchroniser_csv_ocr_ajoute_une_alerte(tmp_path) -> None:
    source = tmp_path / "scan.pdf"
    source.write_bytes(b"%PDF-test")

    destination = tmp_path / "scan.csv"

    with destination.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as fichier:
        writer = csv.writer(fichier)
        writer.writerow(ENTETE)
        writer.writerow([
            "2026-09-05",
            "Fournisseur F",
            "FAC-N05",
            "1200.00",
            "40.00",
            "119.70",
            "1279.70",
            "À VÉRIFIER",
        ])

    chemin_file = tmp_path / "queue.json"

    nombre = synchroniser_export_ocr_a_verifier(
        source,
        destination,
        "PDF → CSV",
        chemin_file,
    )

    assert nombre == 1

    elements = lister_alertes_ocr_a_verifier(
        chemin_file
    )

    assert len(elements) == 1
    assert elements[0].facture.numero == "FAC-N05"
    assert elements[0].facture.fournisseur == "Fournisseur F"
    assert elements[0].niveau is NiveauVerification.AVERTISSEMENT
    assert any(
        "Total OCR incohérent" in raison
        for raison in elements[0].raisons
    )


def test_synchroniser_excel_ocr_conserve_page_et_tableau(tmp_path) -> None:
    source = tmp_path / "scan.pdf"
    source.write_bytes(b"%PDF-test")

    destination = tmp_path / "scan.xlsx"

    wb = Workbook()
    ws = wb.active
    ws.title = "P2_T3"
    ws.append(ENTETE)
    ws.append([
        "2026-09-05",
        "Fournisseur F",
        "FAC-N05",
        "1200.00",
        "40.00",
        "119.70",
        "1279.70",
        "À VÉRIFIER",
    ])
    wb.save(destination)

    chemin_file = tmp_path / "queue.json"

    nombre = synchroniser_export_ocr_a_verifier(
        source,
        destination,
        "PDF → Excel",
        chemin_file,
    )

    assert nombre == 1

    facture = lister_alertes_ocr_a_verifier(
        chemin_file
    )[0].facture

    assert facture.numero_page == 2
    assert facture.numero_tableau == 3


def test_resynchroniser_export_propre_retire_ancienne_alerte(
    tmp_path,
) -> None:
    source = tmp_path / "scan.pdf"
    source.write_bytes(b"%PDF-test")

    destination = tmp_path / "scan.csv"
    chemin_file = tmp_path / "queue.json"

    with destination.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as fichier:
        writer = csv.writer(fichier)
        writer.writerow(ENTETE)
        writer.writerow([
            "2026-09-05",
            "Fournisseur F",
            "FAC-N05",
            "1200.00",
            "40.00",
            "119.70",
            "1279.70",
            "À VÉRIFIER",
        ])

    synchroniser_export_ocr_a_verifier(
        source,
        destination,
        "PDF → CSV",
        chemin_file,
    )

    with destination.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as fichier:
        writer = csv.writer(fichier)
        writer.writerow(ENTETE)
        writer.writerow([
            "2026-09-05",
            "Fournisseur E",
            "FAC-005",
            "1200.00",
            "60.00",
            "119.70",
            "1379.70",
            "OK",
        ])

    nombre = synchroniser_export_ocr_a_verifier(
        source,
        destination,
        "PDF → CSV",
        chemin_file,
    )

    assert nombre == 0
    assert lister_alertes_ocr_a_verifier(
        chemin_file
    ) == []
