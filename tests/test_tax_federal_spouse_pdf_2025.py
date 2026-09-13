import fitz

from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
)
from src.comptaprivee.tax_report_pdf_2025 import (
    exporter_rapport_fiscal_pdf_2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_spouse_integration_2025 import (
    _profil_conjoint,
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
        montant_conjoint_federal=_profil_conjoint(),
    )
    return exporter_rapport_fiscal_pdf_2025(
        estimation,
        tmp_path / "conjoint_federal.pdf",
    )


def test_pdf_affiche_section_conjoint_federal(tmp_path):
    texte = _texte_pdf(_rapport(tmp_path))

    assert "ÉPOUX / CONJOINT DE FAIT - FÉDÉRAL 2025" in texte
    assert "Revenu net du contribuable - ligne 23600 : 51 515,00 $" in texte
    assert "Revenu net du conjoint : 5 000,00 $" in texte
    assert "Montant admissible - ligne 30300 : 11 129,00 $" in texte
    assert "Crédit fédéral - ligne 30300 : 1 613,71 $" in texte
    assert "Taux du crédit fédéral 2025 : 14,5 %" in texte


def test_pdf_affiche_validations_conjoint_federal(tmp_path):
    texte = _texte_pdf(_rapport(tmp_path))

    assert "Contribuable résident du Canada toute l'année : oui" in texte
    assert "Relation époux/conjoint de fait confirmée : oui" in texte
    assert "Conjoint soutenu en 2025 : oui" in texte
    assert "Même conjoint toute l'année 2025 : oui" in texte
    assert "Aucune séparation/réconciliation en 2025 : oui" in texte
    assert "Conjoint résident du Canada toute l'année : oui" in texte
    assert "Aucune pension alimentaire liée à une séparation : oui" in texte
    assert "Aucune déficience du conjoint : oui" in texte
    assert "Un seul conjoint réclame le montant : oui" in texte
    assert "Revenu net du conjoint confirmé : oui" in texte
    assert "Validation comptable : confirmée" in texte


def test_pdf_affiche_source_et_garde_fou(tmp_path):
    texte = _texte_pdf(_rapport(tmp_path))

    assert "Source : État civil et revenu du conjoint validés" in texte
    assert "Ligne 34990 : garde-fou actif" in texte
    assert "première tranche fédérale" in texte


def test_pdf_sans_conjoint_ne_montre_pas_section(tmp_path):
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000()
    )
    path = exporter_rapport_fiscal_pdf_2025(
        estimation,
        tmp_path / "sans_conjoint.pdf",
    )
    texte = _texte_pdf(path)

    assert "ÉPOUX / CONJOINT DE FAIT - FÉDÉRAL 2025" not in texte
