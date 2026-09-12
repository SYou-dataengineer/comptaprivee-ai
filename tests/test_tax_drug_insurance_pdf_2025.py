from decimal import Decimal

import fitz

from src.comptaprivee.tax_drug_insurance_2025 import (
    AssuranceMedicamentsQuebec2025,
)
from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
)
from src.comptaprivee.tax_report_pdf_2025 import (
    exporter_rapport_fiscal_pdf_2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000


def _public_max():
    return AssuranceMedicamentsQuebec2025(
        type_couverture="public",
        couverture_toute_annee=True,
        sans_conjoint_31_decembre_2025=True,
        revenu_ligne_275=Decimal("50095.00"),
        revenu_ligne_48_annexe_k=Decimal("10000"),
        aucun_mois_exempt=True,
        carte_ramq_valide_2025=True,
        situation_validee_par_comptable=True,
        aucun_cas_particulier=True,
        source="Annexe K / ligne 447 validée",
        code_case_449="",
    )


def _collectif():
    return AssuranceMedicamentsQuebec2025(
        type_couverture="collectif",
        couverture_toute_annee=True,
        sans_conjoint_31_decembre_2025=True,
        revenu_ligne_275=Decimal("50095.00"),
        revenu_ligne_48_annexe_k=Decimal("0"),
        aucun_mois_exempt=False,
        carte_ramq_valide_2025=False,
        situation_validee_par_comptable=True,
        aucun_cas_particulier=True,
        source="Assurance collective employeur",
        code_case_449="14",
    )


def _texte_pdf(path):
    doc = fitz.open(path)
    try:
        texte = "\n".join(page.get_text() for page in doc)
    finally:
        doc.close()
    return texte.replace("\xa0", " ").replace("\u202f", " ")


def test_pdf_public_affiche_section_ligne_447(tmp_path):
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        assurance_medicaments=_public_max(),
    )
    path = exporter_rapport_fiscal_pdf_2025(
        estimation,
        tmp_path / "ramq_public.pdf",
    )
    texte = _texte_pdf(path)

    assert "ASSURANCE MÉDICAMENTS QUÉBEC VALIDÉE" in texte
    assert "Régime public" in texte
    assert "ligne 447" in texte
    assert "annexe k" in texte.lower()


def test_pdf_public_affiche_montants(tmp_path):
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        assurance_medicaments=_public_max(),
    )
    path = exporter_rapport_fiscal_pdf_2025(
        estimation,
        tmp_path / "ramq_public.pdf",
    )
    texte = _texte_pdf(path)

    assert "50 095,00 $" in texte
    assert "10 000,00 $" in texte
    assert "755,00 $" in texte
    assert "Annexe K / ligne 447 validée" in texte


def test_pdf_public_affiche_confirmations(tmp_path):
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        assurance_medicaments=_public_max(),
    )
    path = exporter_rapport_fiscal_pdf_2025(
        estimation,
        tmp_path / "ramq_public.pdf",
    )
    texte = _texte_pdf(path)

    assert "Couverture toute l'année 2025 : oui" in texte
    assert "Sans conjoint au 31 décembre 2025 : oui" in texte
    assert "Carte RAMQ 2025 confirmée : oui" in texte
    assert "Situation validée par le comptable : oui" in texte
    assert "Aucun cas particulier de l'annexe K : oui" in texte


def test_pdf_collectif_affiche_code_14_et_zero(tmp_path):
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        assurance_medicaments=_collectif(),
    )
    path = exporter_rapport_fiscal_pdf_2025(
        estimation,
        tmp_path / "ramq_collectif.pdf",
    )
    texte = _texte_pdf(path)

    assert "Couverture collective" in texte
    assert "Case 449" in texte
    assert "code : 14" in texte
    assert "Cotisation Québec" in texte
    assert "ligne 447" in texte
    assert "0,00 $" in texte
    assert "Assurance collective employeur" in texte


def test_pdf_sans_assurance_ne_montre_pas_section(tmp_path):
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000()
    )
    path = exporter_rapport_fiscal_pdf_2025(
        estimation,
        tmp_path / "sans_ramq.pdf",
    )
    texte = _texte_pdf(path)

    assert "ASSURANCE MÉDICAMENTS QUÉBEC VALIDÉE" not in texte
