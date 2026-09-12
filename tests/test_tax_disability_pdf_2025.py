import fitz

from src.comptaprivee.tax_disability_2025 import CreditDeficience2025
from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
)
from src.comptaprivee.tax_report_pdf_2025 import (
    exporter_rapport_fiscal_pdf_2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000


def _deficience_complete():
    return CreditDeficience2025(
        reclamer_federal=True,
        reclamer_quebec=True,
        source_federale="T2201 / approbation ARC",
        source_quebec="Attestation professionnelle Québec",
        valide_par_comptable=True,
        age_18_plus_au_1_janvier_2025=True,
        deficience_12_mois_confirmee=True,
        profil_soi_meme_resident_quebec=True,
        ciph_approuve_arc=True,
        attestation_quebec_confirmee=True,
        aucun_conflit_soins_prepose_etablissement=True,
        aucun_transfert_federal=True,
    )


def _texte_pdf(path):
    doc = fitz.open(path)
    try:
        texte = "\n".join(page.get_text() for page in doc)
    finally:
        doc.close()
    return texte.replace("\xa0", " ").replace("\u202f", " ")


def _estimation_deficience():
    return calculer_estimation_fiscale_2025(
        _dossier_52000(),
        credit_deficience=_deficience_complete(),
    )


def test_pdf_deficience_affiche_section(tmp_path):
    path = exporter_rapport_fiscal_pdf_2025(
        _estimation_deficience(),
        tmp_path / "deficience.pdf",
    )
    texte = _texte_pdf(path)

    assert "HANDICAP / DÉFICIENCE VALIDÉ(E)" in texte
    assert "ligne 31600" in texte
    assert "ligne 376" in texte


def test_pdf_deficience_affiche_montants_et_credits(tmp_path):
    path = exporter_rapport_fiscal_pdf_2025(
        _estimation_deficience(),
        tmp_path / "deficience.pdf",
    )
    texte = _texte_pdf(path)

    assert "10 138,00 $" in texte
    assert "1 470,01 $" in texte
    assert "4 123,00 $" in texte
    assert "577,22 $" in texte


def test_pdf_deficience_affiche_sources(tmp_path):
    path = exporter_rapport_fiscal_pdf_2025(
        _estimation_deficience(),
        tmp_path / "deficience.pdf",
    )
    texte = _texte_pdf(path)

    assert "T2201 / approbation ARC" in texte
    assert "Attestation professionnelle Québec" in texte


def test_pdf_deficience_affiche_confirmations(tmp_path):
    path = exporter_rapport_fiscal_pdf_2025(
        _estimation_deficience(),
        tmp_path / "deficience.pdf",
    )
    texte = _texte_pdf(path)

    assert "Validation comptable : confirmée" in texte
    assert "18 ans ou plus au 1er janvier 2025 : oui" in texte
    assert "Déficience d'au moins 12 mois : confirmée" in texte
    assert "CIPH / T2201 approuvé par l'ARC : oui" in texte
    assert "Attestation professionnelle Québec : confirmée" in texte
    assert "Aucun transfert fédéral : oui" in texte


def test_pdf_sans_deficience_ne_montre_pas_section(tmp_path):
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000()
    )
    path = exporter_rapport_fiscal_pdf_2025(
        estimation,
        tmp_path / "sans_deficience.pdf",
    )
    texte = _texte_pdf(path)

    assert "HANDICAP / DÉFICIENCE VALIDÉ(E)" not in texte
