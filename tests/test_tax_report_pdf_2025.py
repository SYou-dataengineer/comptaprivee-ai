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
