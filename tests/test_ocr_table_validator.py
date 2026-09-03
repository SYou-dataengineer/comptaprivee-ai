from decimal import Decimal

from src.comptaprivee.ocr_table_validator import (
    detecter_anomalies_comptables,
    normaliser_montant_ocr,
    normaliser_tableau_comptable,
)


def test_normaliser_point_decimal_perdu_en_espace() -> None:
    assert normaliser_montant_ocr("1200 00") == "1200.00"
    assert normaliser_montant_ocr("119 70") == "119.70"


def test_normaliser_virgule_decimal() -> None:
    assert normaliser_montant_ocr("24,94") == "24.94"


def test_ne_corrige_pas_valeur_ambigue() -> None:
    assert normaliser_montant_ocr("FAC-N05") == "FAC-N05"
    assert normaliser_montant_ocr("1O0.00") == "1O0.00"


def test_normaliser_tableau_comptable() -> None:
    tableau = [
        ["Date", "Fournisseur", "No facture", "Sous-total", "TPS", "TVQ", "Total"],
        ["2026-09-05", "Fournisseur F", "FAC-N05", "1200 00", "40 00", "119 70", "1279 70"],
    ]

    resultat = normaliser_tableau_comptable(tableau)

    assert resultat[1][3:] == [
        "1200.00",
        "40.00",
        "119.70",
        "1279.70",
    ]


def test_detecter_total_incoherent() -> None:
    tableau = [
        ["Date", "Fournisseur", "No facture", "Sous-total", "TPS", "TVQ", "Total"],
        ["2026-09-05", "Fournisseur F", "FAC-N05", "1200.00", "40.00", "119.70", "1279.70"],
    ]

    anomalies = detecter_anomalies_comptables(tableau)

    assert len(anomalies) == 1
    assert anomalies[0].type_anomalie == "total_incoherent"
    assert anomalies[0].numero_ligne == 2


def test_ligne_comptable_valide_ne_declenche_pas_anomalie() -> None:
    tableau = [
        ["Date", "Fournisseur", "No facture", "Sous-total", "TPS", "TVQ", "Total"],
        ["2026-09-01", "Fournisseur A", "FAC-001", "100.00", "5.00", "9.98", "114.98"],
    ]

    assert detecter_anomalies_comptables(
        tableau,
        tolerance=Decimal("0.03"),
    ) == []
