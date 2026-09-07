from decimal import Decimal
from pathlib import Path

import pytest

from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
    formater_estimation_fiscale_2025,
    formater_montant_estimation,
)
from src.comptaprivee.tax_field_validation import DonneeFiscaleValidee
from src.comptaprivee.tax_validated_case import DossierFiscalValide


def _validee(document, type_document, case, valeur):
    montant = Decimal(valeur)
    return DonneeFiscaleValidee(
        document=Path(document),
        type_document=type_document,
        case=case,
        libelle=f"{type_document} {case}",
        valeur_extraite=montant,
        valeur_validee=montant,
        corrigee=False,
        statut="Validé par le comptable",
    )


def _dossier_52000():
    donnees = (
        _validee("T4.pdf", "T4", "14", "52000"),
        _validee("T4.pdf", "T4", "17", "3104.00"),
        _validee("T4.pdf", "T4", "18", "681.20"),
        _validee("T4.pdf", "T4", "22", "7500"),
        _validee("T4.pdf", "T4", "24", "52000"),
        _validee("T4.pdf", "T4", "26", "52000"),
        _validee("T4.pdf", "T4", "55", "256.88"),
        _validee("T4.pdf", "T4", "56", "52000"),
        _validee("RL1.pdf", "RL-1", "A", "52000"),
        _validee("RL1.pdf", "RL-1", "B.A", "3104.00"),
        _validee("RL1.pdf", "RL-1", "C", "681.20"),
        _validee("RL1.pdf", "RL-1", "E", "6200"),
        _validee("RL1.pdf", "RL-1", "G", "52000"),
        _validee("RL1.pdf", "RL-1", "H", "256.88"),
        _validee("RL1.pdf", "RL-1", "I", "52000"),
    )
    return DossierFiscalValide(
        client="Client Test",
        annee_fiscale=2025,
        province="Québec",
        documents=(Path("T4.pdf"), Path("RL1.pdf")),
        donnees_validees=donnees,
    )


def test_pipeline_complet_52000():
    e = calculer_estimation_fiscale_2025(_dossier_52000())
    assert e.rapprochement.impot_total_preliminaire == Decimal("8088.95")


def test_pipeline_remboursement_52000():
    e = calculer_estimation_fiscale_2025(_dossier_52000())
    assert e.rapprochement.remboursement_estime == Decimal("5611.05")


def test_pipeline_conserve_client():
    e = calculer_estimation_fiscale_2025(_dossier_52000())
    assert e.dossier.client == "Client Test"
    assert e.rapprochement.client == "Client Test"


def test_pipeline_conserve_dossier_verrouille():
    dossier = _dossier_52000()
    e = calculer_estimation_fiscale_2025(dossier)
    assert e.dossier is dossier


def test_pipeline_annee_non_2025_refusee():
    dossier = _dossier_52000()
    dossier = DossierFiscalValide(
        client=dossier.client,
        annee_fiscale=2024,
        province=dossier.province,
        documents=dossier.documents,
        donnees_validees=dossier.donnees_validees,
    )
    with pytest.raises(ValueError):
        calculer_estimation_fiscale_2025(dossier)


def test_format_montant_francais():
    assert formater_montant_estimation(Decimal("5611.05")) == "5\u00a0611,05 $"


def test_resume_contient_resultat():
    texte = formater_estimation_fiscale_2025(
        calculer_estimation_fiscale_2025(_dossier_52000())
    )
    assert "RÉSULTAT : Remboursement estimé" in texte
    assert "5\u00a0611,05 $" in texte


def test_resume_contient_abattement():
    texte = formater_estimation_fiscale_2025(
        calculer_estimation_fiscale_2025(_dossier_52000())
    )
    assert "Abattement Québec (16,5 %)" in texte
    assert "726,31 $" in texte


def test_resume_contient_retenues():
    texte = formater_estimation_fiscale_2025(
        calculer_estimation_fiscale_2025(_dossier_52000())
    )
    assert "7\u00a0500,00 $" in texte
    assert "6\u00a0200,00 $" in texte


def test_resume_affiche_validation_obligatoire():
    texte = formater_estimation_fiscale_2025(
        calculer_estimation_fiscale_2025(_dossier_52000())
    )
    assert "VALIDATION COMPTABLE OBLIGATOIRE" in texte


def test_resume_affiche_aucune_transmission():
    texte = formater_estimation_fiscale_2025(
        calculer_estimation_fiscale_2025(_dossier_52000())
    )
    assert "Aucune déclaration n'a été transmise" in texte


def test_resume_affiche_limitations():
    texte = formater_estimation_fiscale_2025(
        calculer_estimation_fiscale_2025(_dossier_52000())
    )
    assert "LIMITATIONS ACTUELLES" in texte
    assert "profil emploi Québec simple 2025" in texte

from src.comptaprivee.tax_calculation_trace_2025 import (
    construire_trace_calcul_fiscal_2025,
    formater_trace_calcul_fiscal_2025,
)


def test_trace_calcul_contient_17_etapes():
    trace = construire_trace_calcul_fiscal_2025(
        calculer_estimation_fiscale_2025(_dossier_52000())
    )
    assert len(trace.lignes) == 17


def test_trace_calcul_commence_par_t4_case_14():
    trace = construire_trace_calcul_fiscal_2025(
        calculer_estimation_fiscale_2025(_dossier_52000())
    )
    assert trace.lignes[0].source == "T4 case 14 — valeur validée"
    assert trace.lignes[0].montant == Decimal("52000")


def test_trace_calcul_resultat_5611_05():
    trace = construire_trace_calcul_fiscal_2025(
        calculer_estimation_fiscale_2025(_dossier_52000())
    )
    assert trace.resultat == "Remboursement estimé"
    assert trace.montant_resultat == Decimal("5611.05")


def test_trace_calcul_affiche_sources_et_formules():
    texte = formater_trace_calcul_fiscal_2025(
        construire_trace_calcul_fiscal_2025(
            calculer_estimation_fiscale_2025(_dossier_52000())
        )
    )
    assert "Source  : T4 case 14" in texte
    assert "Formule :" in texte
    assert "T4 case 22 + RL-1 case E" in texte


def test_trace_calcul_affiche_resultat():
    texte = formater_trace_calcul_fiscal_2025(
        construire_trace_calcul_fiscal_2025(
            calculer_estimation_fiscale_2025(_dossier_52000())
        )
    )
    assert "Remboursement estimé" in texte
    assert "5\u00a0611,05 $" in texte


def test_trace_calcul_rappelle_validation_et_aucune_transmission():
    texte = formater_trace_calcul_fiscal_2025(
        construire_trace_calcul_fiscal_2025(
            calculer_estimation_fiscale_2025(_dossier_52000())
        )
    )
    assert "VALIDATION COMPTABLE OBLIGATOIRE" in texte
    assert "Elle ne refait pas l'OCR" in texte
    assert "Aucune déclaration n'a été transmise" in texte
