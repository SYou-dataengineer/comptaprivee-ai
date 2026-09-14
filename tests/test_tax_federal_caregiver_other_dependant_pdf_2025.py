import fitz

from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
)
from src.comptaprivee.tax_report_pdf_2025 import (
    exporter_rapport_fiscal_pdf_2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_caregiver_other_dependant_2025 import _profil


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
        aidant_autre_personne_charge_federal=profil,
    )
    return (
        exporter_rapport_fiscal_pdf_2025(
            estimation,
            tmp_path / "aidant_30450.pdf",
        ),
        profil,
    )


def test_pdf_affiche_section_30450(tmp_path):
    path, _profil_30450 = _rapport(tmp_path)
    texte = _texte_pdf(path)

    assert (
        "AIDANT NATUREL - AUTRE PERSONNE À CHARGE 18+ - FÉDÉRAL 2025"
        in texte
    )
    assert "Lien avec la personne : parent" in texte
    assert "Revenu net de la personne - ligne 23600 : 25 000,00 $" in texte
    assert "Nombre de personnes à charge - ligne 51120 : 1" in texte
    assert (
        "Montant canadien pour aidant naturel - ligne 30450 : "
        "3 798,00 $"
        in texte
    )
    assert (
        "Crédit fédéral calculé - ligne 30450 : 550,71 $"
        in texte
    )
    assert "Base de calcul 2025 : 28 798 $" in texte
    assert "Maximum ligne 30450 : 8 601 $" in texte
    assert "Taux du crédit fédéral 2025 : 14,5 %" in texte


def test_pdf_affiche_validations_30450(tmp_path):
    path, _profil_30450 = _rapport(tmp_path)
    texte = _texte_pdf(path)

    for attendu in (
        "Personne à charge âgée de 18 ans ou plus : oui",
        "Personne soutenue par le contribuable en 2025 : oui",
        "Infirmité physique ou mentale confirmée : oui",
        "Dépendance due à l'infirmité : oui",
        "Dépendance pendant une période considérable : oui",
        "Résidence au Canada confirmée lorsque requise : oui",
        "Aucun montant ligne 30300/30400 pour cette personne : oui",
        "Aucune pension alimentaire pour cette personne : oui",
        "Aucun partage de la réclamation 30450 : oui",
        "Preuve médicale admissible ou T2201 approuvé : confirmée",
        "Validation comptable : confirmée",
    ):
        assert attendu in texte


def test_pdf_affiche_source_et_garde_fous_30450(tmp_path):
    path, profil = _rapport(tmp_path)
    texte = _texte_pdf(path)

    assert profil.source_personne in texte
    assert "Ligne 34990 : garde-fou actif" in texte
    assert (
        "Profil simple : une seule autre personne à charge"
        in texte
    )


def test_pdf_sans_30450_ne_montre_pas_section(tmp_path):
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000()
    )
    path = exporter_rapport_fiscal_pdf_2025(
        estimation,
        tmp_path / "sans_30450.pdf",
    )
    texte = _texte_pdf(path)

    assert (
        "AIDANT NATUREL - AUTRE PERSONNE À CHARGE 18+ - FÉDÉRAL 2025"
        not in texte
    )
