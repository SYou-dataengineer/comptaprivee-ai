from dataclasses import replace
from decimal import Decimal

import fitz

from src.comptaprivee.tax_contribution_overpayments_2025 import (
    CotisationsExcedentaires2025,
)
from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
)
from src.comptaprivee.tax_report_pdf_2025 import (
    exporter_rapport_fiscal_pdf_2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000


def _dossier_avec_excedents():
    dossier = _dossier_52000()
    remplacements = {
        ("T4", "17"): Decimal("3200.00"),
        ("RL-1", "B.A"): Decimal("3200.00"),
        ("T4", "18"): Decimal("700.00"),
        ("RL-1", "C"): Decimal("700.00"),
        ("T4", "55"): Decimal("300.00"),
        ("RL-1", "H"): Decimal("300.00"),
    }

    donnees = []
    for donnee in dossier.donnees_validees:
        cle = (donnee.type_document, donnee.case)
        if cle in remplacements:
            montant = remplacements[cle]
            donnee = replace(
                donnee,
                valeur_extraite=montant,
                valeur_validee=montant,
            )
        donnees.append(donnee)

    return replace(
        dossier,
        donnees_validees=tuple(donnees),
    )


def _profil():
    return CotisationsExcedentaires2025(
        rrq_ba=Decimal("3200.00"),
        rrq_bb=Decimal("0"),
        gains_admissibles_rrq=Decimal("52000"),
        assurance_emploi=Decimal("700.00"),
        gains_assurables_ae=Decimal("52000"),
        rqap=Decimal("300.00"),
        revenus_assujettis_rqap=Decimal("52000"),
        source="T4 / RL-1 validés",
        valide_par_comptable=True,
        resident_quebec_31_decembre_2025=True,
        emploi_quebec_uniquement=True,
        rrq_uniquement_sans_rpc=True,
        aucun_travail_autonome=True,
        profil_rrq_standard_18_64=True,
        aucun_cas_particulier_ae=True,
        aucun_cas_particulier_rqap=True,
        calcul_standard_confirme=True,
    )


def _texte_pdf(path):
    doc = fitz.open(path)
    try:
        texte = "\n".join(page.get_text() for page in doc)
    finally:
        doc.close()
    texte = texte.replace("\xa0", " ").replace("\u202f", " ")
    return " ".join(texte.split())


def _rapport(tmp_path):
    estimation = calculer_estimation_fiscale_2025(
        _dossier_avec_excedents(),
        cotisations_excedentaires=_profil(),
    )
    return exporter_rapport_fiscal_pdf_2025(
        estimation,
        tmp_path / "cotisations_excedentaires.pdf",
    )


def test_pdf_affiche_section_cotisations_excedentaires(tmp_path):
    texte = _texte_pdf(_rapport(tmp_path))

    assert "COTISATIONS EXCÉDENTAIRES VALIDÉES" in texte
    assert "RRQ" in texte
    assert "ligne Québec 452" in texte
    assert "Assurance-emploi" in texte
    assert "ligne fédérale 45000" in texte
    assert "RQAP" in texte
    assert "ligne Québec 457" in texte


def test_pdf_affiche_remboursements_et_total(tmp_path):
    texte = _texte_pdf(_rapport(tmp_path))

    assert "96,00 $" in texte
    assert "18,80 $" in texte
    assert "43,12 $" in texte
    assert "157,92 $" in texte


def test_pdf_affiche_montants_payes_et_gains(tmp_path):
    texte = _texte_pdf(_rapport(tmp_path))

    assert "3 200,00 $" in texte
    assert "52 000,00 $" in texte
    assert "700,00 $" in texte
    assert "300,00 $" in texte


def test_pdf_affiche_source_et_validations(tmp_path):
    texte = _texte_pdf(_rapport(tmp_path))

    assert "T4 / RL-1 validés" in texte
    assert "Situation validée par le comptable : oui" in texte
    assert "Résident du Québec au 31 décembre 2025 : oui" in texte
    assert "RRQ uniquement, sans RPC : oui" in texte
    assert "Aucun travail autonome : oui" in texte
    assert "Calcul standard RRQ / AE / RQAP confirmé : oui" in texte


def test_pdf_sans_profil_ne_montre_pas_section(tmp_path):
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000()
    )
    path = exporter_rapport_fiscal_pdf_2025(
        estimation,
        tmp_path / "sans_excedents.pdf",
    )
    texte = _texte_pdf(path)

    assert "COTISATIONS EXCÉDENTAIRES VALIDÉES" not in texte
