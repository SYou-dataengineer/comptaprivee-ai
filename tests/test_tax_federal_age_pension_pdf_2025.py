import fitz

from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
)
from src.comptaprivee.tax_report_pdf_2025 import (
    exporter_rapport_fiscal_pdf_2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_age_pension_integration_2025 import (
    _profil_age_federal,
)


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
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        credits_federaux_age_pension=_profil_age_federal(),
    )
    return exporter_rapport_fiscal_pdf_2025(
        estimation,
        tmp_path / "age_pension_federal.pdf",
    )


def test_pdf_affiche_section_age_pension_federal(tmp_path):
    texte = _texte_pdf(_rapport(tmp_path))

    assert "ÂGE / PENSION - FÉDÉRAL 2025" in texte
    assert "Revenu net fédéral - ligne 23600 : 51 515,00 $" in texte
    assert "Montant en raison de l'âge - ligne 30100 : 8 129,05 $" in texte
    assert "Crédit fédéral âge / pension : 1 178,71 $" in texte
    assert "Taux du crédit fédéral 2025 : 14,5 %" in texte


def test_pdf_affiche_sources_et_validations_age_federal(tmp_path):
    texte = _texte_pdf(_rapport(tmp_path))

    assert "65 ans ou plus au 31 décembre 2025 : oui" in texte
    assert "Résident du Canada toute l'année 2025 : oui" in texte
    assert "Aucune règle spéciale décès : oui" in texte
    assert "Aucun fractionnement de pension T1032 : oui" in texte
    assert "Aucun transfert entre conjoints : oui" in texte
    assert "Validation comptable : confirmée" in texte
    assert "Source âge : Date de naissance validée" in texte


def test_pdf_affiche_ligne_31400_non_reclamee(tmp_path):
    texte = _texte_pdf(_rapport(tmp_path))

    assert "Montant pour revenu de pension - ligne 31400 : 0,00 $" in texte
    assert "Ligne 31400 non réclamée" in texte


def test_pdf_affiche_garde_fou_34990(tmp_path):
    texte = _texte_pdf(_rapport(tmp_path))

    assert "Ligne 34990 : garde-fou actif" in texte
    assert "profil simple actuellement supporté" in texte


def test_pdf_sans_age_pension_federal_ne_montre_pas_section(tmp_path):
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000()
    )
    path = exporter_rapport_fiscal_pdf_2025(
        estimation,
        tmp_path / "sans_age_pension_federal.pdf",
    )
    texte = _texte_pdf(path)

    assert "ÂGE / PENSION - FÉDÉRAL 2025" not in texte
