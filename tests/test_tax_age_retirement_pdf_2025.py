import fitz

from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
)
from src.comptaprivee.tax_report_pdf_2025 import (
    exporter_rapport_fiscal_pdf_2025,
)
from tests.test_tax_age_retirement_integration_2025 import (
    _profil_age_retraite,
)
from tests.test_tax_estimation_2025 import _dossier_52000


def _texte_pdf(path):
    document = fitz.open(path)
    try:
        texte = "\n".join(page.get_text() for page in document)
    finally:
        document.close()

    return " ".join(
        texte.replace("\xa0", " ")
        .replace("\u202f", " ")
        .replace("—", "-")
        .replace("–", "-")
        .split()
    )


def _rapport(tmp_path):
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        montants_age_retraite=_profil_age_retraite(),
    )
    return exporter_rapport_fiscal_pdf_2025(
        estimation,
        tmp_path / "age_retraite_2025.pdf",
    )


def test_pdf_affiche_section_age_retraite(tmp_path):
    texte = _texte_pdf(_rapport(tmp_path))

    assert "ÂGE / REVENUS DE RETRAITE - QUÉBEC 2025" in texte
    assert "Annexe B / ligne 361 : 5 875,06 $" in texte
    assert "Crédit Québec : 822,51 $" in texte


def test_pdf_affiche_montants_et_regles(tmp_path):
    texte = _texte_pdf(_rapport(tmp_path))

    assert "Montant en raison de l'âge : 3 906,00 $" in texte
    assert "Revenu retraite net admissible : 3 000,00 $" in texte
    assert "Montant pour revenus de retraite : 3 470,00 $" in texte
    assert "Coefficient revenus de retraite : 1,25" in texte
    assert "Maximum revenus de retraite : 3 470,00 $" in texte
    assert "Seuil de réduction : 42 090,00 $" in texte
    assert "Taux de réduction : 18,75 %" in texte
    assert "Taux du crédit Québec : 14 %" in texte


def test_pdf_affiche_sources_age_retraite(tmp_path):
    texte = _texte_pdf(_rapport(tmp_path))

    assert "Source âge : Date de naissance validée" in texte
    assert (
        "Source retraite : RL-2 / feuillet retraite validé"
        in texte
    )


def test_pdf_affiche_validations_age_retraite(tmp_path):
    texte = _texte_pdf(_rapport(tmp_path))

    assert "Sans conjoint au 31 décembre 2025 : oui" in texte
    assert "Résident Québec/Canada toute l'année : oui" in texte
    assert "Aucun montant personne vivant seule combiné : oui" in texte
    assert "Revenus de retraite admissibles confirmés : oui" in texte
    assert "PSV, RRQ et RPC exclus : oui" in texte
    assert "Validation comptable : confirmée" in texte


def test_pdf_affiche_lignes_retraite_sources(tmp_path):
    texte = _texte_pdf(_rapport(tmp_path))

    assert "Revenu ligne 122 : 3 000,00 $" in texte
    assert "Revenu ligne 123 : 0,00 $" in texte
    assert "Transfert ligne 245 : 0,00 $" in texte


def test_pdf_sans_age_retraite_ne_montre_pas_section(tmp_path):
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000()
    )
    path = exporter_rapport_fiscal_pdf_2025(
        estimation,
        tmp_path / "sans_age_retraite.pdf",
    )
    texte = _texte_pdf(path)

    assert "ÂGE / REVENUS DE RETRAITE - QUÉBEC 2025" not in texte
