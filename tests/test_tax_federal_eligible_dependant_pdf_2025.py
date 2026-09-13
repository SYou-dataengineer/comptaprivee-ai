import fitz

from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
)
from src.comptaprivee.tax_report_pdf_2025 import (
    exporter_rapport_fiscal_pdf_2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_eligible_dependant_integration_2025 import (
    _profil_personne_charge,
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
        personne_charge_admissible_federale=_profil_personne_charge(),
    )
    return exporter_rapport_fiscal_pdf_2025(
        estimation,
        tmp_path / "personne_charge_admissible.pdf",
    )


def test_pdf_affiche_section_personne_charge_admissible(tmp_path):
    texte = _texte_pdf(_rapport(tmp_path))

    assert "PERSONNE À CHARGE ADMISSIBLE - FÉDÉRAL 2025" in texte
    assert "Revenu net du contribuable - ligne 23600 : 51 515,00 $" in texte
    assert "Revenu net de la personne à charge : 4 000,00 $" in texte
    assert "Montant admissible - ligne 30400 : 12 129,00 $" in texte
    assert "Crédit fédéral - ligne 30400 : 1 758,71 $" in texte
    assert "Taux du crédit fédéral 2025 : 14,5 %" in texte


def test_pdf_affiche_validations_personne_charge(tmp_path):
    texte = _texte_pdf(_rapport(tmp_path))

    assert "Contribuable résident du Canada toute l'année 2025 : oui" in texte
    assert "Aucun époux/conjoint pendant toute l'année 2025 : oui" in texte
    assert "Personne à charge = enfant du contribuable : oui" in texte
    assert "Enfant de moins de 18 ans à la fin de 2025 : oui" in texte
    assert "Aucune déficience de l'enfant : oui" in texte
    assert "Enfant soutenu par le contribuable en 2025 : oui" in texte
    assert "Enfant ayant vécu avec le contribuable : oui" in texte
    assert "Habitation maintenue par le contribuable : oui" in texte
    assert "Enfant résident du Canada toute l'année 2025 : oui" in texte
    assert "Aucune garde partagée : oui" in texte
    assert "Aucune pension alimentaire : oui" in texte
    assert "Un seul montant ligne 30400 par ménage : oui" in texte
    assert "Aucun autre réclamant ligne 30400 : oui" in texte
    assert "Revenu net de la personne à charge confirmé : oui" in texte
    assert "Validation comptable : confirmée" in texte


def test_pdf_affiche_source_et_garde_fou(tmp_path):
    texte = _texte_pdf(_rapport(tmp_path))

    assert (
        "Source : État civil, résidence et revenu de l'enfant validés"
        in texte
    )
    assert "Ligne 34990 : garde-fou actif" in texte
    assert "première tranche fédérale" in texte


def test_pdf_sans_personne_charge_ne_montre_pas_section(tmp_path):
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000()
    )
    path = exporter_rapport_fiscal_pdf_2025(
        estimation,
        tmp_path / "sans_personne_charge.pdf",
    )
    texte = _texte_pdf(path)

    assert "PERSONNE À CHARGE ADMISSIBLE - FÉDÉRAL 2025" not in texte
