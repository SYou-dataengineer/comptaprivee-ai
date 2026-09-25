from decimal import Decimal
from pathlib import Path
import fitz

from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
from src.comptaprivee.tax_field_validation import DonneeFiscaleValidee
from src.comptaprivee.tax_report_pdf_2025 import (
    exporter_rapport_fiscal_pdf_2025,
    nom_rapport_fiscal_pdf_2025,
)
from src.comptaprivee.tax_validated_case import DossierFiscalValide


def _v(doc, typ, case, valeur):
    m = Decimal(valeur)
    return DonneeFiscaleValidee(
        document=Path(doc), type_document=typ, case=case,
        libelle=f"{typ} {case}", valeur_extraite=m,
        valeur_validee=m, corrigee=False,
        statut="Validé par le comptable",
    )


def _estimation():
    donnees = (
        _v("T4.pdf","T4","14","52000"), _v("T4.pdf","T4","17","3104.00"),
        _v("T4.pdf","T4","18","681.20"), _v("T4.pdf","T4","22","7500"),
        _v("T4.pdf","T4","24","52000"), _v("T4.pdf","T4","26","52000"),
        _v("T4.pdf","T4","55","256.88"), _v("T4.pdf","T4","56","52000"),
        _v("RL1.pdf","RL-1","A","52000"), _v("RL1.pdf","RL-1","B.A","3104.00"),
        _v("RL1.pdf","RL-1","C","681.20"), _v("RL1.pdf","RL-1","E","6200"),
        _v("RL1.pdf","RL-1","G","52000"), _v("RL1.pdf","RL-1","H","256.88"),
        _v("RL1.pdf","RL-1","I","52000"),
    )
    dossier = DossierFiscalValide(
        client="Client Test", annee_fiscale=2025, province="Québec",
        documents=(Path("T4.pdf"), Path("RL1.pdf")),
        donnees_validees=donnees,
    )
    return calculer_estimation_fiscale_2025(dossier)


def _texte(path):
    doc = fitz.open(path)
    try:
        return "\n".join(page.get_text() for page in doc)
    finally:
        doc.close()


def test_nom_pdf():
    assert nom_rapport_fiscal_pdf_2025(_estimation()) == "Estimation_Fiscale_2025_Client_Test.pdf"


def test_export_cree_pdf(tmp_path):
    path = exporter_rapport_fiscal_pdf_2025(_estimation(), tmp_path / "rapport")
    assert path.exists()
    assert path.suffix == ".pdf"


def test_pdf_contient_client_et_resultat(tmp_path):
    path = exporter_rapport_fiscal_pdf_2025(_estimation(), tmp_path / "rapport.pdf")
    texte = _texte(path)
    assert "Client Test" in texte
    assert "Remboursement estimé" in texte


def test_pdf_contient_montant(tmp_path):
    path = exporter_rapport_fiscal_pdf_2025(_estimation(), tmp_path / "rapport.pdf")
    texte = _texte(path).replace("\xa0", " ")
    assert "5 611,05 $" in texte


def test_pdf_contient_validation_et_transmission(tmp_path):
    path = exporter_rapport_fiscal_pdf_2025(_estimation(), tmp_path / "rapport.pdf")
    texte = _texte(path)
    assert "VALIDATION COMPTABLE OBLIGATOIRE" in texte
    assert "Aucune déclaration" in texte
    assert "ARC" in texte
    assert "Revenu Québec" in texte


def test_pdf_metadonnees(tmp_path):
    path = exporter_rapport_fiscal_pdf_2025(_estimation(), tmp_path / "rapport.pdf")
    doc = fitz.open(path)
    try:
        assert doc.metadata["author"] == "ComptaPrivée AI"
    finally:
        doc.close()

# --- Priorité 4A : PDF CELIAPP ---

from src.comptaprivee.tax_fhsa_2025 import DeductionCeliapp2025


def _estimation_celiapp():
    base = _estimation()
    return calculer_estimation_fiscale_2025(
        base.dossier,
        deduction_celiapp=DeductionCeliapp2025(
            deduction=Decimal("5000"),
            cotisations_directes_2025=Decimal("6000"),
            droits_deduction_confirmes=Decimal("8000"),
            source_droits="Annexe 15 / relevé CELIAPP 2025",
            valide_par_comptable=True,
            titulaire_confirme=True,
            residence_canada_quebec_annee_complete=True,
        ),
    )


def test_pdf_celiapp_4a_contient_deduction_et_lignes(tmp_path):
    path = exporter_rapport_fiscal_pdf_2025(
        _estimation_celiapp(),
        tmp_path / "rapport_celiapp.pdf",
    )
    texte = _texte(path).replace("\xa0", " ")

    assert "CELIAPP 2025 VALIDÉ" in texte
    assert "BLOC 4A" in texte
    assert "20805" in texte
    assert "215" in texte
    assert "5000.00 $" in texte
    assert "Annexe 15 / relevé CELIAPP 2025" in texte

# --- Priorité 4B : PDF frais de garde fédéraux ---

from src.comptaprivee.tax_child_care_2025 import FraisGardeFederaux2025


def _estimation_frais_garde_4b():
    base = _estimation()
    return calculer_estimation_fiscale_2025(
        base.dossier,
        frais_garde_federaux=FraisGardeFederaux2025(
            frais_admissibles_payes=Decimal("6000"),
            revenu_gagne_t778=Decimal("52000"),
            nombre_enfants_moins_7_sans_dtc=1,
            nombre_enfants_7_a_16_ou_infirmes_sans_dtc=0,
            nombre_enfants_dtc=0,
            source="T778 2025 / reçus de garde",
            valide_par_comptable=True,
            services_fournis_en_2025_confirmes=True,
            frais_pour_gagner_revenu_confirmes=True,
            recus_confirmes=True,
            demandeur_seul_ou_revenu_inferieur_confirme=True,
        ),
    )


def test_pdf_frais_garde_4b_contient_t778_ligne_21400(tmp_path):
    path = exporter_rapport_fiscal_pdf_2025(
        _estimation_frais_garde_4b(),
        tmp_path / "rapport_frais_garde_4b.pdf",
    )
    texte = _texte(path).replace("\xa0", " ")

    assert "FRAIS DE GARDE 2025 VALIDÉS" in texte
    assert "BLOC 4B" in texte
    assert "T778" in texte
    assert "21400" in texte
    assert "6000.00 $" in texte
    assert "T778 2025 / reçus de garde" in texte


def test_pdf_frais_garde_4b_reste_federal_seulement(tmp_path):
    estimation = _estimation_frais_garde_4b()

    assert estimation.revenu.revenu_net_federal == Decimal("45515.00")
    assert estimation.revenu.revenu_net_quebec == Decimal("50095.00")

    path = exporter_rapport_fiscal_pdf_2025(
        estimation,
        tmp_path / "rapport_frais_garde_4b_federal.pdf",
    )
    texte = _texte(path).replace("\xa0", " ")

    assert "Revenu net fédéral" in texte
    assert "45 515,00 $" in texte
    assert "Revenu net Québec" in texte
    assert "50 095,00 $" in texte
