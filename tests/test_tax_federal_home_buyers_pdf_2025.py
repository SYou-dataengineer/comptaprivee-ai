import fitz

from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
)
from src.comptaprivee.tax_report_pdf_2025 import (
    exporter_rapport_fiscal_pdf_2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_home_buyers_2025 import _profil


def _texte_pdf(path):
    doc = fitz.open(path)
    try:
        texte = "\n".join(page.get_text() for page in doc)
    finally:
        doc.close()

    texte = texte.replace("\xa0", " ").replace("\u202f", " ")
    texte = texte.replace("—", "-").replace("–", "-")
    return " ".join(texte.split())


def _rapport(tmp_path):
    profil = _profil()
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        achat_habitation_federal=profil,
    )
    path = exporter_rapport_fiscal_pdf_2025(
        estimation,
        tmp_path / "achat_habitation_31270.pdf",
    )
    return path, profil


def test_pdf_affiche_section_31270(tmp_path):
    path, _ = _rapport(tmp_path)
    texte = _texte_pdf(path)

    assert "ACHAT D'UNE HABITATION - FÉDÉRAL 2025" in texte
    assert "Montant réclamé - ligne 31270 : 10 000,00 $" in texte
    assert "Crédit fédéral calculé - ligne 31270 : 1 450,00 $" in texte
    assert "Maximum ligne 31270 : 10 000 $" in texte
    assert "Taux du crédit fédéral 2025 : 14,5 %" in texte


def test_pdf_affiche_conditions_31270(tmp_path):
    path, _ = _rapport(tmp_path)
    texte = _texte_pdf(path)

    for attendu in (
        "Acquisition en 2025 : oui",
        "Habitation admissible : oui",
        "Habitation située au Canada : oui",
        "Habitation enregistrée au nom du contribuable ou du conjoint : oui",
        "Première habitation : confirmée",
        "Année de l'achat et quatre années précédentes : critère confirmé",
        "Intention de résidence principale dans un an : confirmée",
        "Aucun partage du montant ligne 31270 : oui",
        "Exception handicap non utilisée dans ce profil simple : oui",
        "Pièces justificatives conservées : oui",
        "Validation comptable : confirmée",
    ):
        assert attendu in texte


def test_pdf_affiche_source_et_garde_fou_31270(tmp_path):
    path, profil = _rapport(tmp_path)
    texte = _texte_pdf(path)

    assert profil.source_habitation in texte
    assert "Ligne 34990 : garde-fou actif" in texte
    assert "Profil simple : partage et exception handicap non pris en charge" in texte


def test_pdf_sans_31270_ne_montre_pas_section(tmp_path):
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000()
    )
    path = exporter_rapport_fiscal_pdf_2025(
        estimation,
        tmp_path / "sans_31270.pdf",
    )
    texte = _texte_pdf(path)

    assert "ACHAT D'UNE HABITATION - FÉDÉRAL 2025" not in texte
