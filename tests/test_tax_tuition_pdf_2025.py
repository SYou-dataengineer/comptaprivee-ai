from decimal import Decimal

import fitz

from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
)
from src.comptaprivee.tax_report_pdf_2025 import (
    exporter_rapport_fiscal_pdf_2025,
)
from src.comptaprivee.tax_tuition_2025 import FraisScolarite2025
from tests.test_tax_estimation_2025 import _dossier_52000


def _scolarite_3000():
    return FraisScolarite2025(
        montant_admissible_federal=Decimal("3000"),
        montant_admissible_quebec=Decimal("3000"),
        source_federale="T2202 - établissement admissible",
        source_quebec="Reçu officiel - établissement admissible",
        valide_par_comptable=True,
        piece_federale_confirmee=True,
        recu_officiel_quebec_confirme=True,
        seuil_100_confirme=True,
        remboursements_soustraits=True,
        frais_2025_uniquement=True,
        aucun_report_anterieur=True,
        aucun_transfert=True,
        credit_canadien_formation_non_reclame=True,
        profil_resident_quebec_simple=True,
    )


def _texte_pdf(path):
    doc = fitz.open(path)
    try:
        texte = "\n".join(page.get_text() for page in doc)
    finally:
        doc.close()
    return texte.replace("\xa0", " ").replace("\u202f", " ")


def _estimation_scolarite():
    return calculer_estimation_fiscale_2025(
        _dossier_52000(),
        frais_scolarite=_scolarite_3000(),
    )


def test_pdf_scolarite_affiche_section(tmp_path):
    path = exporter_rapport_fiscal_pdf_2025(
        _estimation_scolarite(),
        tmp_path / "scolarite.pdf",
    )
    texte = _texte_pdf(path)
    assert "FRAIS DE SCOLARITÉ / EXAMEN VALIDÉS" in texte
    assert "Montant admissible fédéral" in texte
    assert "Montant admissible Québec" in texte


def test_pdf_scolarite_affiche_credits_et_lignes(tmp_path):
    path = exporter_rapport_fiscal_pdf_2025(
        _estimation_scolarite(),
        tmp_path / "scolarite.pdf",
    )
    texte = _texte_pdf(path)
    assert "435,00 $" in texte
    assert "240,00 $" in texte
    assert "ligne 32300" in texte
    assert "ligne 398" in texte


def test_pdf_scolarite_affiche_sources(tmp_path):
    path = exporter_rapport_fiscal_pdf_2025(
        _estimation_scolarite(),
        tmp_path / "scolarite.pdf",
    )
    texte = _texte_pdf(path)
    assert "T2202 - établissement admissible" in texte
    assert "Reçu officiel - établissement admissible" in texte


def test_pdf_scolarite_affiche_confirmations(tmp_path):
    path = exporter_rapport_fiscal_pdf_2025(
        _estimation_scolarite(),
        tmp_path / "scolarite.pdf",
    )
    texte = _texte_pdf(path)
    assert "Validation comptable : confirmée" in texte
    assert "Pièce fédérale confirmée : oui" in texte
    assert "Reçu officiel Québec confirmé : oui" in texte
    assert "Aucun report antérieur : oui" in texte
    assert "Aucun transfert : oui" in texte


def test_pdf_sans_scolarite_ne_montre_pas_section(tmp_path):
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000()
    )
    path = exporter_rapport_fiscal_pdf_2025(
        estimation,
        tmp_path / "sans_scolarite.pdf",
    )
    texte = _texte_pdf(path)
    assert "FRAIS DE SCOLARITÉ / EXAMEN VALIDÉS" not in texte
