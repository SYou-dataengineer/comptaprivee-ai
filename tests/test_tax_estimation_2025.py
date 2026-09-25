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

from src.comptaprivee.tax_adjustments_2025 import AjustementReer2025


def _reer_5000():
    return AjustementReer2025(
        deduction_reer=Decimal("5000"),
        plafond_reer_confirme=Decimal("8000"),
        source_plafond_reer="Avis de cotisation / T1028 ARC",
        valide_par_comptable=True,
    )


def test_pipeline_sans_reer_reste_identique():
    e = calculer_estimation_fiscale_2025(_dossier_52000())
    assert e.rapprochement.remboursement_estime == Decimal("5611.05")
    assert e.ajustement_reer.deduction_reer == Decimal("0")


def test_pipeline_reer_5000_reduit_revenu_federal():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        ajustement_reer=_reer_5000(),
    )
    assert e.revenu.revenu_imposable_federal == Decimal("46515.00")


def test_pipeline_reer_5000_reduit_revenu_quebec():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        ajustement_reer=_reer_5000(),
    )
    assert e.revenu.revenu_imposable_quebec == Decimal("45095.00")


def test_pipeline_reer_5000_recalcule_impots():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        ajustement_reer=_reer_5000(),
    )
    assert e.federal.impot_federal_de_base == Decimal("3676.90")
    assert e.quebec.impot_quebec_preliminaire == Decimal("3713.36")


def test_pipeline_reer_5000_recalcule_remboursement():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        ajustement_reer=_reer_5000(),
    )
    assert e.rapprochement.impot_total_preliminaire == Decimal("6783.57")
    assert e.rapprochement.remboursement_estime == Decimal("6916.43")


def test_resume_affiche_reer_valide():
    texte = formater_estimation_fiscale_2025(
        calculer_estimation_fiscale_2025(
            _dossier_52000(),
            ajustement_reer=_reer_5000(),
        )
    )
    assert "AJUSTEMENTS VALIDÉS" in texte
    assert "Déduction REER/RPAC/RVER" in texte
    assert "5\u00a0000,00 $" in texte
    assert "Avis de cotisation / T1028 ARC" in texte


def test_trace_reer_ajoute_une_etape():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        ajustement_reer=_reer_5000(),
    )
    trace = construire_trace_calcul_fiscal_2025(e)
    assert len(trace.lignes) == 18
    assert (
        trace.lignes[2].libelle
        == "Déduction REER/RPAC/RVER validée"
    )
    assert trace.lignes[-1].libelle == "Remboursement estimé"


def test_trace_reer_affiche_sources_et_nouveau_resultat():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        ajustement_reer=_reer_5000(),
    )
    texte = formater_trace_calcul_fiscal_2025(
        construire_trace_calcul_fiscal_2025(e)
    )
    assert "ARC ligne 20800" in texte
    assert "Revenu Québec ligne 214" in texte
    assert "6\u00a0916,43 $" in texte

def test_trace_reer_est_placee_avant_revenu_imposable_federal():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        ajustement_reer=_reer_5000(),
    )
    trace = construire_trace_calcul_fiscal_2025(e)

    assert trace.lignes[2].ordre == 3
    assert (
        trace.lignes[2].libelle
        == "Déduction REER/RPAC/RVER validée"
    )
    assert trace.lignes[3].ordre == 4
    assert trace.lignes[3].libelle == "Revenu imposable fédéral"


def test_trace_reer_conserve_une_numerotation_continue():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        ajustement_reer=_reer_5000(),
    )
    trace = construire_trace_calcul_fiscal_2025(e)

    assert [ligne.ordre for ligne in trace.lignes] == list(
        range(1, 19)
    )

# --- Priorité 4A : intégration estimation CELIAPP ---

from src.comptaprivee.tax_fhsa_2025 import DeductionCeliapp2025


def _celiapp_5000():
    return DeductionCeliapp2025(
        deduction=Decimal("5000"),
        cotisations_directes_2025=Decimal("6000"),
        droits_deduction_confirmes=Decimal("8000"),
        source_droits="Annexe 15 / relevé CELIAPP 2025",
        valide_par_comptable=True,
        titulaire_confirme=True,
        residence_canada_quebec_annee_complete=True,
    )


def test_pipeline_sans_celiapp_reste_identique():
    e = calculer_estimation_fiscale_2025(_dossier_52000())
    assert e.deduction_celiapp == DeductionCeliapp2025()
    assert e.rapprochement.remboursement_estime == Decimal("5611.05")


def test_pipeline_celiapp_5000_reduit_revenus_net_et_imposable():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        deduction_celiapp=_celiapp_5000(),
    )
    assert e.revenu.revenu_total_federal == Decimal("52000")
    assert e.revenu.revenu_total_quebec == Decimal("52000")
    assert e.revenu.revenu_net_federal == Decimal("46515.00")
    assert e.revenu.revenu_imposable_federal == Decimal("46515.00")
    assert e.revenu.revenu_net_quebec == Decimal("45095.00")
    assert e.revenu.revenu_imposable_quebec == Decimal("45095.00")


def test_pipeline_celiapp_5000_recalcule_impots_comme_deduction_net():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        deduction_celiapp=_celiapp_5000(),
    )
    assert e.federal.impot_federal_de_base == Decimal("3676.90")
    assert e.quebec.impot_quebec_preliminaire == Decimal("3713.36")
    assert e.rapprochement.remboursement_estime == Decimal("6916.43")


def test_resume_affiche_celiapp_4a_20805_215():
    texte = formater_estimation_fiscale_2025(
        calculer_estimation_fiscale_2025(
            _dossier_52000(),
            deduction_celiapp=_celiapp_5000(),
        )
    )
    assert "CELIAPP 2025 VALIDÉ — BLOC 4A" in texte
    assert "ligne 20805" in texte
    assert "ligne 215" in texte
    assert "5000.00 $" in texte
    assert "Annexe 15 / relevé CELIAPP 2025" in texte


def test_pipeline_reer_et_celiapp_sadditionnent_sans_modifier_revenu_total():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        ajustement_reer=_reer_5000(),
        deduction_celiapp=_celiapp_5000(),
    )
    assert e.revenu.revenu_total_federal == Decimal("52000")
    assert e.revenu.revenu_total_quebec == Decimal("52000")
    assert e.revenu.revenu_net_federal == Decimal("41515.00")
    assert e.revenu.revenu_net_quebec == Decimal("40095.00")

# --- Priorité 4A : trace CELIAPP ---

def test_trace_celiapp_4a_ajoute_etape_20805_215():
    from src.comptaprivee.tax_calculation_trace_2025 import (
        construire_trace_calcul_fiscal_2025,
        formater_trace_calcul_fiscal_2025,
    )

    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        deduction_celiapp=_celiapp_5000(),
    )
    trace = construire_trace_calcul_fiscal_2025(e)

    ligne = next(
        x for x in trace.lignes
        if x.libelle == "Déduction CELIAPP 4A validée"
    )
    assert ligne.montant == Decimal("5000")
    assert "20805" in ligne.source
    assert "215" in ligne.source
    assert "Annexe 15 / relevé CELIAPP 2025" in ligne.source

    texte = formater_trace_calcul_fiscal_2025(trace)
    assert "Déduction CELIAPP 4A validée" in texte
    assert "20805" in texte
    assert "215" in texte


def test_trace_celiapp_4a_est_avant_revenu_imposable_federal():
    from src.comptaprivee.tax_calculation_trace_2025 import (
        construire_trace_calcul_fiscal_2025,
    )

    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        deduction_celiapp=_celiapp_5000(),
    )
    trace = construire_trace_calcul_fiscal_2025(e)

    libelles = [x.libelle for x in trace.lignes]
    assert libelles.index("Déduction CELIAPP 4A validée") < libelles.index(
        "Revenu imposable fédéral"
    )

# --- Priorité 4B : intégration estimation frais de garde fédéraux ---

from src.comptaprivee.tax_child_care_2025 import FraisGardeFederaux2025


def _frais_garde_6000():
    return FraisGardeFederaux2025(
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
    )


def test_pipeline_sans_frais_garde_4b_reste_identique():
    e = calculer_estimation_fiscale_2025(_dossier_52000())
    assert e.frais_garde_federaux == FraisGardeFederaux2025()
    assert e.revenu.revenu_net_federal == Decimal("51515.00")
    assert e.revenu.revenu_net_quebec == Decimal("50095.00")
    assert e.rapprochement.remboursement_estime == Decimal("5611.05")


def test_pipeline_frais_garde_6000_reduit_federal_seulement():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        frais_garde_federaux=_frais_garde_6000(),
    )

    assert e.frais_garde_federaux.frais_admissibles_payes == Decimal("6000")
    assert e.revenu.revenu_total_federal == Decimal("52000")
    assert e.revenu.revenu_net_federal == Decimal("45515.00")
    assert e.revenu.revenu_imposable_federal == Decimal("45515.00")

    assert e.revenu.revenu_total_quebec == Decimal("52000")
    assert e.revenu.revenu_net_quebec == Decimal("50095.00")
    assert e.revenu.revenu_imposable_quebec == Decimal("50095.00")


def test_pipeline_frais_garde_4b_recalcule_impot_federal():
    base = calculer_estimation_fiscale_2025(_dossier_52000())
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        frais_garde_federaux=_frais_garde_6000(),
    )

    assert e.federal.impot_federal_de_base < base.federal.impot_federal_de_base
    assert (
        e.rapprochement.remboursement_estime
        > base.rapprochement.remboursement_estime
    )


def test_resume_affiche_frais_garde_4b_t778_21400():
    texte = formater_estimation_fiscale_2025(
        calculer_estimation_fiscale_2025(
            _dossier_52000(),
            frais_garde_federaux=_frais_garde_6000(),
        )
    )

    assert "FRAIS DE GARDE 2025 VALIDÉS — BLOC 4B" in texte
    assert "T778" in texte
    assert "ligne 21400" in texte
    assert "6000.00 $" in texte
    assert "T778 2025 / reçus de garde" in texte


def test_pipeline_celiapp_et_frais_garde_se_combinent_sans_doubler_quebec():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        deduction_celiapp=_celiapp_5000(),
        frais_garde_federaux=_frais_garde_6000(),
    )

    assert e.revenu.revenu_net_federal == Decimal("40515.00")
    assert e.revenu.revenu_imposable_federal == Decimal("40515.00")

    assert e.revenu.revenu_net_quebec == Decimal("45095.00")
    assert e.revenu.revenu_imposable_quebec == Decimal("45095.00")

# --- Priorité 4B : trace frais de garde fédéraux ---


def test_trace_frais_garde_4b_ajoute_ligne_t778_21400():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        frais_garde_federaux=_frais_garde_6000(),
    )
    trace = construire_trace_calcul_fiscal_2025(e)

    ligne = next(
        x for x in trace.lignes
        if x.libelle
        == "Frais de garde fédéraux 4B — T778 / ligne 21400"
    )

    assert ligne.montant == Decimal("6000")
    assert "T778" in ligne.source
    assert "21400" in ligne.source
    assert "T778 2025 / reçus de garde" in ligne.source
    assert "frais admissibles payés" in ligne.formule
    assert "plafond selon enfants" in ligne.formule
    assert "2/3 du revenu gagné" in ligne.formule


def test_trace_frais_garde_4b_est_avant_revenu_imposable_federal():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        frais_garde_federaux=_frais_garde_6000(),
    )
    trace = construire_trace_calcul_fiscal_2025(e)

    libelles = [x.libelle for x in trace.lignes]
    assert libelles.index(
        "Frais de garde fédéraux 4B — T778 / ligne 21400"
    ) < libelles.index("Revenu imposable fédéral")


def test_trace_frais_garde_4b_ne_cree_aucune_deduction_quebec():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        frais_garde_federaux=_frais_garde_6000(),
    )
    trace = construire_trace_calcul_fiscal_2025(e)

    ligne_federal = next(
        x for x in trace.lignes
        if x.libelle
        == "Frais de garde fédéraux 4B — T778 / ligne 21400"
    )
    assert ligne_federal.section == "REVENU FÉDÉRAL"

    lignes_quebec_garde = [
        x for x in trace.lignes
        if "garde" in x.libelle.lower()
        and x.section == "REVENU QUÉBEC"
    ]
    assert lignes_quebec_garde == []

    revenu_qc = next(
        x for x in trace.lignes
        if x.libelle == "Revenu imposable Québec"
    )
    assert "frais de garde" not in revenu_qc.formule.lower()

# --- Priorité 4C : intégration estimation dépenses d'emploi ---

from src.comptaprivee.tax_employment_expenses_2025 import DepensesEmploi2025


def _depenses_emploi_4c(federal="1200", quebec="1000"):
    return DepensesEmploi2025(
        deduction_federale_t777=Decimal(federal),
        deduction_quebec_tp59=Decimal(quebec),
        source_federale="T2200 + T777 2025",
        source_quebec="TP-64.3 + TP-59 2025",
        valide_par_comptable=True,
        salarie_ordinaire_confirme=True,
        contrat_exige_depenses_confirme=True,
        non_remboursees_confirme=True,
        t2200_confirme=True,
        t777_confirme=True,
        tp_64_3_confirme=True,
        tp_59_confirme=True,
    )


def test_pipeline_sans_depenses_emploi_4c_reste_identique():
    e = calculer_estimation_fiscale_2025(_dossier_52000())
    assert e.depenses_emploi == DepensesEmploi2025()
    assert e.revenu.revenu_net_federal == Decimal("51515.00")
    assert e.revenu.revenu_net_quebec == Decimal("50095.00")
    assert e.rapprochement.remboursement_estime == Decimal("5611.05")


def test_pipeline_depenses_emploi_4c_reduit_chaque_juridiction_separement():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        depenses_emploi=_depenses_emploi_4c(),
    )
    assert e.depenses_emploi.deduction_federale_t777 == Decimal("1200")
    assert e.depenses_emploi.deduction_quebec_tp59 == Decimal("1000")
    assert e.revenu.revenu_total_federal == Decimal("52000")
    assert e.revenu.revenu_net_federal == Decimal("50315.00")
    assert e.revenu.revenu_imposable_federal == Decimal("50315.00")
    assert e.revenu.revenu_total_quebec == Decimal("52000")
    assert e.revenu.revenu_net_quebec == Decimal("49095.00")
    assert e.revenu.revenu_imposable_quebec == Decimal("49095.00")


def test_pipeline_depenses_emploi_4c_recalcule_les_impots():
    base = calculer_estimation_fiscale_2025(_dossier_52000())
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        depenses_emploi=_depenses_emploi_4c(),
    )
    assert e.federal.impot_federal_de_base < base.federal.impot_federal_de_base
    assert e.quebec.impot_quebec_preliminaire < base.quebec.impot_quebec_preliminaire
    assert e.rapprochement.remboursement_estime > base.rapprochement.remboursement_estime


def test_resume_affiche_depenses_emploi_4c():
    texte = formater_estimation_fiscale_2025(
        calculer_estimation_fiscale_2025(
            _dossier_52000(),
            depenses_emploi=_depenses_emploi_4c(),
        )
    )
    assert "DÉPENSES D'EMPLOI 2025 VALIDÉES — BLOC 4C" in texte
    assert "T777" in texte
    assert "ligne 22900" in texte
    assert "TP-59" in texte
    assert "ligne 207, code 07" in texte
    assert "1200.00 $" in texte
    assert "1000.00 $" in texte


def test_pipeline_4a_4b_4c_se_combinent_sans_modifier_revenu_total():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        deduction_celiapp=_celiapp_5000(),
        frais_garde_federaux=_frais_garde_6000(),
        depenses_emploi=_depenses_emploi_4c(),
    )
    assert e.revenu.revenu_total_federal == Decimal("52000")
    assert e.revenu.revenu_total_quebec == Decimal("52000")
    assert e.revenu.revenu_net_federal == Decimal("39315.00")
    assert e.revenu.revenu_imposable_federal == Decimal("39315.00")
    assert e.revenu.revenu_net_quebec == Decimal("44095.00")
    assert e.revenu.revenu_imposable_quebec == Decimal("44095.00")

# --- Priorité 4C : trace dépenses d'emploi ---


def test_trace_depenses_emploi_4c_ajoute_lignes_federal_et_quebec():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        depenses_emploi=_depenses_emploi_4c(),
    )
    trace = construire_trace_calcul_fiscal_2025(e)

    federal = next(
        x for x in trace.lignes
        if x.libelle == "Dépenses d'emploi 4C — T777 / ligne 22900"
    )
    quebec = next(
        x for x in trace.lignes
        if x.libelle
        == "Dépenses d'emploi 4C — TP-59 / ligne 207 code 07"
    )

    assert federal.section == "REVENU FÉDÉRAL"
    assert federal.montant == Decimal("1200")
    assert "T2200" in federal.source
    assert "T777" in federal.source
    assert "22900" in federal.source
    assert "T2200 + T777 2025" in federal.source

    assert quebec.section == "REVENU QUÉBEC"
    assert quebec.montant == Decimal("1000")
    assert "TP-64.3" in quebec.source
    assert "TP-59" in quebec.source
    assert "207 code 07" in quebec.source
    assert "TP-64.3 + TP-59 2025" in quebec.source


def test_trace_depenses_emploi_4c_est_avant_revenus_imposables():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        depenses_emploi=_depenses_emploi_4c(),
    )
    trace = construire_trace_calcul_fiscal_2025(e)
    libelles = [x.libelle for x in trace.lignes]

    assert libelles.index(
        "Dépenses d'emploi 4C — T777 / ligne 22900"
    ) < libelles.index("Revenu imposable fédéral")

    assert libelles.index(
        "Dépenses d'emploi 4C — TP-59 / ligne 207 code 07"
    ) < libelles.index("Revenu imposable Québec")


def test_trace_depenses_emploi_4c_formules_revenus_identifient_les_lignes():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        depenses_emploi=_depenses_emploi_4c(),
    )
    trace = construire_trace_calcul_fiscal_2025(e)

    revenu_federal = next(
        x for x in trace.lignes if x.libelle == "Revenu imposable fédéral"
    )
    revenu_quebec = next(
        x for x in trace.lignes if x.libelle == "Revenu imposable Québec"
    )

    assert "T777 / ligne 22900" in revenu_federal.formule
    assert "TP-59 / ligne 207 code 07" in revenu_quebec.formule
