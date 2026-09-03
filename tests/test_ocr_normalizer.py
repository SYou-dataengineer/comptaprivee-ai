"""Tests de normalisation prudente des montants OCR."""

from src.comptaprivee.ocr_normalizer import normaliser_montants_ocr


def test_corriger_tvq_sans_point_si_coherente() -> None:
    texte = (
        "Sous-total: 250.00 CAD\n"
        "TPS: 12.50 CAD\n"
        "TVQ: 2494CAD\n"
        "Total: 287.44 CAD"
    )

    resultat = normaliser_montants_ocr(texte)

    assert "TVQ: 24.94CAD" in resultat


def test_corriger_tps_sans_point_si_coherente() -> None:
    texte = (
        "Sous-total: 100.00 CAD\n"
        "TPS: 500CAD\n"
        "TVQ: 9.98 CAD\n"
        "Total: 114.98 CAD"
    )

    resultat = normaliser_montants_ocr(texte)

    assert "TPS: 5.00CAD" in resultat


def test_ne_pas_corriger_montant_incoherent() -> None:
    texte = (
        "Sous-total: 250.00 CAD\n"
        "TVQ: 9999CAD\n"
        "Total: 287.44 CAD"
    )

    resultat = normaliser_montants_ocr(texte)

    assert "TVQ: 9999CAD" in resultat


def test_ne_pas_modifier_taxe_deja_correcte() -> None:
    texte = (
        "Sous-total: 250.00 CAD\n"
        "TPS: 12.50 CAD\n"
        "TVQ: 24.94 CAD\n"
        "Total: 287.44 CAD"
    )

    assert normaliser_montants_ocr(texte) == texte


def test_ne_pas_inventer_sans_sous_total() -> None:
    texte = (
        "TVQ: 2494CAD\n"
        "Total: 287.44 CAD"
    )

    assert normaliser_montants_ocr(texte) == texte
