from decimal import Decimal

import fitz

from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
)
from src.comptaprivee.tax_federal_caregiver_spouse_dependant_2025 import (
    credit_federal_ligne_30425_2025,
    montant_ligne_30425_2025,
)
from src.comptaprivee.tax_report_pdf_2025 import (
    exporter_rapport_fiscal_pdf_2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_caregiver_spouse_dependant_integration_2025 import (
    _30425_conjoint,
    _30425_personne_charge,
)
from tests.test_tax_federal_eligible_dependant_caregiver_base_2025 import (
    _profil_18_plus_infirmite,
)
from tests.test_tax_federal_spouse_caregiver_base_2025 import (
    _profil_infirmite,
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


def _rapport(tmp_path, profil, nom):
    kwargs = {
        "aidant_conjoint_personne_charge_federal": profil,
    }

    if profil.type_personne == "conjoint":
        kwargs["montant_conjoint_federal"] = _profil_infirmite(
            revenu_net_contribuable_ligne_23600=Decimal("51515.00")
        )
    else:
        kwargs["personne_charge_admissible_federale"] = (
            _profil_18_plus_infirmite(
                revenu_net_contribuable_ligne_23600=Decimal("51515.00")
            )
        )

    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        **kwargs,
    )
    return exporter_rapport_fiscal_pdf_2025(
        estimation,
        tmp_path / nom,
    )


def test_pdf_30425_conjoint_affiche_montants(tmp_path):
    profil = _30425_conjoint()
    texte = _texte_pdf(
        _rapport(tmp_path, profil, "30425_conjoint.pdf")
    )

    montant = montant_ligne_30425_2025(profil)
    credit = credit_federal_ligne_30425_2025(profil)

    assert (
        "AIDANT NATUREL - CONJOINT / PERSONNE À CHARGE - FÉDÉRAL 2025"
        in texte
    )
    assert "Type de personne : conjoint" in texte
    assert "Revenu net de la personne - ligne 23600 :" in texte
    assert "Montant source - ligne 30300 :" in texte
    assert "Montant canadien pour aidant naturel - ligne 30425 :" in texte
    assert (
        f"{montant:,.2f}".replace(",", " ").replace(".", ",")
        in texte
    )
    assert (
        f"{credit:,.2f}".replace(",", " ").replace(".", ",")
        in texte
    )
    assert "Taux du crédit fédéral 2025 : 14,5 %" in texte


def test_pdf_30425_personne_charge_affiche_chemin_30400(tmp_path):
    profil = _30425_personne_charge()
    texte = _texte_pdf(
        _rapport(tmp_path, profil, "30425_personne_charge.pdf")
    )

    assert "Type de personne : personne à charge admissible" in texte
    assert "Montant source - ligne 30400 :" in texte
    assert (
        "Personne à charge 18 ans ou plus si applicable : oui"
        in texte
    )


def test_pdf_30425_affiche_validations(tmp_path):
    texte = _texte_pdf(
        _rapport(tmp_path, _30425_conjoint(), "30425_validations.pdf")
    )

    for attendu in (
        "Personne soutenue en 2025 : oui",
        "Infirmité physique ou mentale : confirmée",
        "Dépendance due uniquement à l'infirmité : oui",
        "Dépendance pendant une période considérable : oui",
        "Base aidant naturel de 2 687 $ incluse dans 30300/30400 : oui",
        "Un seul réclamant ligne 30425 : oui",
        "Aucune réclamation partagée : oui",
        "Preuve médicale admissible ou T2201 approuvé : confirmée",
        "Validation comptable : confirmée",
        "Ligne 34990 : garde-fou actif",
    ):
        assert attendu in texte


def test_pdf_30425_affiche_source(tmp_path):
    profil = _30425_conjoint()
    texte = _texte_pdf(
        _rapport(tmp_path, profil, "30425_source.pdf")
    )

    assert "Source : " in texte
    assert profil.source_personne in texte


def test_pdf_sans_30425_ne_montre_pas_section(tmp_path):
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000()
    )
    path = exporter_rapport_fiscal_pdf_2025(
        estimation,
        tmp_path / "sans_30425.pdf",
    )
    texte = _texte_pdf(path)

    assert (
        "AIDANT NATUREL - CONJOINT / PERSONNE À CHARGE - FÉDÉRAL 2025"
        not in texte
    )
