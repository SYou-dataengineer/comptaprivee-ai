import fitz

from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
)
from src.comptaprivee.tax_report_pdf_2025 import (
    exporter_rapport_fiscal_pdf_2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_home_accessibility_2025 import _profil


def _texte_pdf(path):
    document = fitz.open(path)
    try:
        texte = "\n".join(page.get_text() for page in document)
    finally:
        document.close()

    texte = texte.replace("\xa0", " ").replace("\u202f", " ")
    texte = texte.replace("—", "-").replace("–", "-")
    return " ".join(texte.split())


def _rapport(tmp_path):
    profil = _profil()
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        accessibilite_domiciliaire_federale=profil,
    )
    path = exporter_rapport_fiscal_pdf_2025(
        estimation,
        tmp_path / "accessibilite_31285.pdf",
    )
    return path, profil


def test_pdf_affiche_section_31285(tmp_path):
    path, _ = _rapport(tmp_path)
    texte = _texte_pdf(path)

    assert "ACCESSIBILITÉ DOMICILIAIRE - FÉDÉRAL 2025" in texte
    assert "Dépenses admissibles - ligne 31285 : 20 000,00 $" in texte
    assert "Crédit fédéral calculé - ligne 31285 : 2 900,00 $" in texte
    assert "Maximum ligne 31285 : 20 000 $" in texte
    assert "Taux du crédit fédéral 2025 : 14,5 %" in texte


def test_pdf_affiche_admissibilite_31285(tmp_path):
    path, _ = _rapport(tmp_path)
    texte = _texte_pdf(path)

    for attendu in (
        "Demande pour soi-même : oui",
        "65 ans ou plus à la fin de 2025 : oui",
        "Admissible au CIPH en 2025 : non",
        "Logement situé au Canada : oui",
        "Logement appartenant au contribuable : oui",
        "Logement normalement habité par le contribuable : oui",
        "Rénovation durable et intégrante : oui",
        "Accessibilité / mobilité / réduction du risque : confirmée",
        "Travaux et biens de 2025 uniquement : oui",
        "Aucune part entreprise/location : oui",
        "Aucun partage de la demande ligne 31285 : oui",
        "Fournisseurs liés : règles confirmées",
        "Dépenses non admissibles exclues : oui",
        "Pièces justificatives conservées : oui",
        "Validation comptable : confirmée",
    ):
        assert attendu in texte


def test_pdf_affiche_source_et_garde_fou_31285(tmp_path):
    path, profil = _rapport(tmp_path)
    texte = _texte_pdf(path)

    assert profil.source_renovation in texte
    assert "Ligne 34990 : garde-fou actif" in texte
    assert "Profil simple : demande pour soi-même" in texte
    assert "partage" in texte
    assert "entreprise/location" in texte


def test_pdf_sans_31285_ne_montre_pas_section(tmp_path):
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000()
    )
    path = exporter_rapport_fiscal_pdf_2025(
        estimation,
        tmp_path / "sans_31285.pdf",
    )
    texte = _texte_pdf(path)

    assert "ACCESSIBILITÉ DOMICILIAIRE - FÉDÉRAL 2025" not in texte
