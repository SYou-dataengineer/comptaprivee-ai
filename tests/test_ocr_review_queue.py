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

def test_marquer_alerte_ocr_resolue_retire_seulement_la_cible(tmp_path) -> None:
    from src.comptaprivee.ocr_review_queue import marquer_alerte_ocr_resolue

    source_a = tmp_path / "scan_a.pdf"
    source_b = tmp_path / "scan_b.pdf"
    source_a.write_bytes(b"%PDF-a")
    source_b.write_bytes(b"%PDF-b")

    csv_a = tmp_path / "scan_a.csv"
    csv_b = tmp_path / "scan_b.csv"
    chemin_file = tmp_path / "queue.json"

    for destination in (csv_a, csv_b):
        with destination.open("w", encoding="utf-8-sig", newline="") as fichier:
            writer = csv.writer(fichier)
            writer.writerow(ENTETE)
            writer.writerow([
                "2026-09-05", "Fournisseur F", "FAC-N05",
                "1200.00", "40.00", "119.70", "1279.70", "À VÉRIFIER",
            ])

    synchroniser_export_ocr_a_verifier(source_a, csv_a, "PDF → CSV", chemin_file)
    synchroniser_export_ocr_a_verifier(source_b, csv_b, "PDF → CSV", chemin_file)

    elements = lister_alertes_ocr_a_verifier(chemin_file)
    assert len(elements) == 2

    identifiant_cible = elements[0].facture.identifiant
    assert marquer_alerte_ocr_resolue(identifiant_cible, chemin_file) is True

    restants = lister_alertes_ocr_a_verifier(chemin_file)
    assert len(restants) == 1
    assert restants[0].facture.identifiant != identifiant_cible


def test_marquer_alerte_ocr_resolue_identifiant_absent(tmp_path) -> None:
    from src.comptaprivee.ocr_review_queue import marquer_alerte_ocr_resolue

    chemin_file = tmp_path / "queue.json"
    assert marquer_alerte_ocr_resolue(-999, chemin_file) is False


def test_marquer_derniere_alerte_ocr_laisse_file_vide(tmp_path) -> None:
    from src.comptaprivee.ocr_review_queue import marquer_alerte_ocr_resolue

    source = tmp_path / "scan.pdf"
    source.write_bytes(b"%PDF-test")
    destination = tmp_path / "scan.csv"
    chemin_file = tmp_path / "queue.json"

    with destination.open("w", encoding="utf-8-sig", newline="") as fichier:
        writer = csv.writer(fichier)
        writer.writerow(ENTETE)
        writer.writerow([
            "2026-09-05", "Fournisseur F", "FAC-N05",
            "1200.00", "40.00", "119.70", "1279.70", "À VÉRIFIER",
        ])

    synchroniser_export_ocr_a_verifier(source, destination, "PDF → CSV", chemin_file)

    identifiant = lister_alertes_ocr_a_verifier(chemin_file)[0].facture.identifiant
    assert marquer_alerte_ocr_resolue(identifiant, chemin_file) is True
    assert lister_alertes_ocr_a_verifier(chemin_file) == []

def test_resoudre_alerte_ocr_journalise_resolution(tmp_path) -> None:
    from src.comptaprivee.audit_log import lister_evenements
    from src.comptaprivee.ocr_review_queue import (
        resoudre_alerte_ocr_et_journaliser,
    )

    source = tmp_path / "scan_resolution.pdf"
    source.write_bytes(b"%PDF-test")
    destination = tmp_path / "scan_resolution.csv"
    chemin_file = tmp_path / "queue.json"
    chemin_audit = tmp_path / "audit.db"

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

    identifiant = lister_alertes_ocr_a_verifier(
        chemin_file
    )[0].facture.identifiant

    assert resoudre_alerte_ocr_et_journaliser(
        identifiant,
        chemin_file,
        chemin_base_audit=chemin_audit,
    ) is True

    assert lister_alertes_ocr_a_verifier(
        chemin_file
    ) == []

    evenements = lister_evenements(
        chemin_audit
    )

    assert len(evenements) == 1
    assert evenements[0].action == "Alerte OCR résolue"
    assert evenements[0].categorie == "ocr"
    assert evenements[0].reference == "FAC-N05"
    assert "scan_resolution.pdf" in (evenements[0].details or "")
    assert "page=1" in (evenements[0].details or "")
    assert "ligne=2" in (evenements[0].details or "")


def test_resoudre_alerte_ocr_absente_ne_journalise_pas(tmp_path) -> None:
    from src.comptaprivee.audit_log import lister_evenements
    from src.comptaprivee.ocr_review_queue import (
        resoudre_alerte_ocr_et_journaliser,
    )

    chemin_file = tmp_path / "queue.json"
    chemin_audit = tmp_path / "audit.db"

    assert resoudre_alerte_ocr_et_journaliser(
        -999,
        chemin_file,
        chemin_base_audit=chemin_audit,
    ) is False

    assert lister_evenements(
        chemin_audit
    ) == []


def test_resolution_ocr_reste_possible_si_journal_indisponible(
    tmp_path,
) -> None:
    from src.comptaprivee.ocr_review_queue import (
        resoudre_alerte_ocr_et_journaliser,
    )

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

    identifiant = lister_alertes_ocr_a_verifier(
        chemin_file
    )[0].facture.identifiant

    chemin_audit_invalide = tmp_path / "dossier"
    chemin_audit_invalide.mkdir()

    assert resoudre_alerte_ocr_et_journaliser(
        identifiant,
        chemin_file,
        chemin_base_audit=chemin_audit_invalide,
    ) is True

    assert lister_alertes_ocr_a_verifier(
        chemin_file
    ) == []
