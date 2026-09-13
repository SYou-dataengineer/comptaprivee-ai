import fitz

from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
)
from src.comptaprivee.tax_report_pdf_2025 import (
    exporter_rapport_fiscal_pdf_2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_caregiver_child_integration_2025 import (
    _profil_aidant_enfant,
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
        aidant_enfant_federal=_profil_aidant_enfant(),
    )
    return exporter_rapport_fiscal_pdf_2025(
        estimation,
        tmp_path / "aidant_enfant_federal.pdf",
    )


def test_pdf_affiche_section_aidant_enfant(tmp_path):
    texte = _texte_pdf(_rapport(tmp_path))

    assert (
        "AIDANT NATUREL - ENFANT DE MOINS DE 18 ANS - FÉDÉRAL 2025"
        in texte
    )
    assert "Nombre d'enfants - ligne 30499 : 1" in texte
    assert "Montant admissible - ligne 30500 : 2 687,00 $" in texte
    assert "Crédit fédéral - ligne 30500 : 389,62 $" in texte
    assert "Taux du crédit fédéral 2025 : 14,5 %" in texte


def test_pdf_affiche_validations_aidant_enfant(tmp_path):
    texte = _texte_pdf(_rapport(tmp_path))

    for attendu in (
        "Enfant biologique ou adopté : oui",
        "Enfant de moins de 18 ans à la fin de 2025 : oui",
        "Infirmité physique ou mentale confirmée : oui",
        "Dépendance longue, continue et de durée indéterminée : oui",
        "Besoin de beaucoup plus d'aide que les enfants du même âge : oui",
        "Enfant avec ses deux parents toute l'année 2025 : oui",
        "Aucune garde partagée : oui",
        "Aucune pension alimentaire : oui",
        "Aucun autre réclamant ligne 30500 : oui",
        "Aucun transfert au conjoint - ligne 32600 : oui",
        "Preuve médicale admissible ou T2201 approuvé : confirmée",
        "Validation comptable : confirmée",
    ):
        assert attendu in texte


def test_pdf_affiche_source_et_garde_fous_aidant_enfant(tmp_path):
    texte = _texte_pdf(_rapport(tmp_path))

    assert (
        "Source : Lien familial, résidence et preuve médicale validés"
        in texte
    )
    assert "Ligne 34990 : garde-fou actif" in texte
    assert (
        "Combinaison ligne 30400 + ligne 30500 : non supportée"
        in texte
    )


def test_pdf_sans_aidant_enfant_ne_montre_pas_section(tmp_path):
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000()
    )
    path = exporter_rapport_fiscal_pdf_2025(
        estimation,
        tmp_path / "sans_aidant_enfant.pdf",
    )
    texte = _texte_pdf(path)

    assert (
        "AIDANT NATUREL - ENFANT DE MOINS DE 18 ANS - FÉDÉRAL 2025"
        not in texte
    )
