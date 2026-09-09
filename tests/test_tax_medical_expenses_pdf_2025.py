from decimal import Decimal

import fitz

from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
)
from src.comptaprivee.tax_medical_expenses_2025 import (
    FraisMedicaux2025,
)
from src.comptaprivee.tax_report_pdf_2025 import (
    exporter_rapport_fiscal_pdf_2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000


def _frais_3000():
    return FraisMedicaux2025(
        montant_admissible_federal=Decimal("3000"),
        montant_admissible_quebec=Decimal("3000"),
        source_federale="Reçus médicaux vérifiés - ARC",
        source_quebec="Reçus médicaux vérifiés - Revenu Québec",
        valide_par_comptable=True,
        recus_confirmes=True,
        remboursements_soustraits=True,
        periode_12_mois_fin_2025_confirmee=True,
        aucune_periode_deja_reclamee=True,
        profil_individuel_sans_conjoint_dependant=True,
    )


def _texte_pdf(path):
    doc = fitz.open(path)
    try:
        texte = "\n".join(page.get_text() for page in doc)
    finally:
        doc.close()

    return (
        texte.replace("\xa0", " ")
        .replace("\u202f", " ")
    )


def _estimation_medicale():
    return calculer_estimation_fiscale_2025(
        _dossier_52000(),
        frais_medicaux=_frais_3000(),
    )


def test_pdf_medical_affiche_section(tmp_path):
    path = exporter_rapport_fiscal_pdf_2025(
        _estimation_medicale(),
        tmp_path / "medical.pdf",
    )
    texte = _texte_pdf(path)

    assert "FRAIS MÉDICAUX VALIDÉS" in texte
    assert "Montant admissible fédéral" in texte
    assert "Montant admissible Québec" in texte


def test_pdf_medical_affiche_credits(tmp_path):
    path = exporter_rapport_fiscal_pdf_2025(
        _estimation_medicale(),
        tmp_path / "medical.pdf",
    )
    texte = _texte_pdf(path)

    assert "210,91 $" in texte
    assert "299,43 $" in texte
    assert "33099 / 33200" in texte
    assert "ligne 381" in texte


def test_pdf_medical_affiche_sources(tmp_path):
    path = exporter_rapport_fiscal_pdf_2025(
        _estimation_medicale(),
        tmp_path / "medical.pdf",
    )
    texte = _texte_pdf(path)

    assert "Reçus médicaux vérifiés - ARC" in texte
    assert "Reçus médicaux vérifiés - Revenu Québec" in texte


def test_pdf_medical_affiche_confirmations(tmp_path):
    path = exporter_rapport_fiscal_pdf_2025(
        _estimation_medicale(),
        tmp_path / "medical.pdf",
    )
    texte = _texte_pdf(path)

    assert "Validation comptable : confirmée" in texte
    assert "Reçus confirmés : oui" in texte
    assert "Remboursements soustraits : oui" in texte


def test_pdf_sans_medical_ne_montre_pas_section(tmp_path):
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000()
    )
    path = exporter_rapport_fiscal_pdf_2025(
        estimation,
        tmp_path / "sans_medical.pdf",
    )
    texte = _texte_pdf(path)

    assert "FRAIS MÉDICAUX VALIDÉS" not in texte
