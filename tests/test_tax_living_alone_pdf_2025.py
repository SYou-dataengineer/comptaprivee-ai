import fitz

from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
)
from src.comptaprivee.tax_report_pdf_2025 import (
    exporter_rapport_fiscal_pdf_2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_living_alone_integration_2025 import _profil_simple


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
        personne_vivant_seule=_profil_simple(),
    )
    return exporter_rapport_fiscal_pdf_2025(
        estimation,
        tmp_path / "personne_vivant_seule.pdf",
    )


def test_pdf_affiche_section_personne_vivant_seule(tmp_path):
    texte = _texte_pdf(_rapport(tmp_path))

    assert "PERSONNE VIVANT SEULE" in texte
    assert "QUÉBEC 2025" in texte
    assert "Annexe B / ligne 361" in texte
    assert "627,06 $" in texte
    assert "87,79 $" in texte


def test_pdf_affiche_regles_de_calcul(tmp_path):
    texte = _texte_pdf(_rapport(tmp_path))

    assert "Montant de base : 2 128,00 $" in texte
    assert "Seuil de réduction : 42 090,00 $" in texte
    assert "Taux de réduction : 18,75 %" in texte
    assert "Taux du crédit Québec : 14 %" in texte


def test_pdf_affiche_source_et_validations(tmp_path):
    texte = _texte_pdf(_rapport(tmp_path))

    assert "Bail et factures validés" in texte
    assert "Sans conjoint au 31 décembre 2025 : oui" in texte
    assert "Résident Québec/Canada toute l'année : oui" in texte
    assert "Habitation maintenue toute l'année : oui" in texte
    assert "Documents justificatifs confirmés : oui" in texte
    assert "Validation comptable : confirmée" in texte


def test_pdf_affiche_option_monoparentale_non_reclamee(tmp_path):
    texte = _texte_pdf(_rapport(tmp_path))

    assert "Additionnel monoparental réclamé : non" in texte


def test_pdf_sans_profil_ne_montre_pas_section(tmp_path):
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000()
    )
    path = exporter_rapport_fiscal_pdf_2025(
        estimation,
        tmp_path / "sans_personne_seule.pdf",
    )
    texte = _texte_pdf(path)

    assert "PERSONNE VIVANT SEULE — QUÉBEC 2025" not in texte
