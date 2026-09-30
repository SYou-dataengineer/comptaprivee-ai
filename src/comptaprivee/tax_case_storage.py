"""Persistance locale des dossiers fiscaux validés."""

from __future__ import annotations
from .tax_family_medical_2025 import (FraisMedicauxFamilleFederaux2025, calculer_medical_familial_2025, medical_familial_vers_dict, medical_familial_depuis_dict, verifier_combinaison_medicale_famille)
from .tax_family_workers_benefit_2025 import famille_act_vers_dict, famille_act_depuis_dict, verifier_concordance_act_familial_2025
from .tax_disability_transfer_2025 import (TransfertsHandicap2025, calculer_transferts_handicap_2025, transferts_handicap_vers_dict, transferts_handicap_depuis_dict)

from .tax_multigenerational_renovation_2025 import (RenovationsMultigenerationnelles2025, calculer_multigenerationnel_2025, multigenerationnel_vers_dict, multigenerationnel_depuis_dict)
from .tax_educator_supplies_2025 import (FournituresEducateur2025, calculer_fournitures_educateur_2025, educateur_vers_dict, educateur_depuis_dict)
from .tax_labour_funds_2025 import (FondsTravailleurs2025, ResultatFondsTravailleurs2025, calculer_fonds_travailleurs_2025, fonds_vers_dict, fonds_depuis_dict, verifier_fonds_conjoint_2025, lignes_fonds_travailleurs_2025)
from .tax_political_contributions_2025 import ContributionsPolitiques2025, calculer_contributions_politiques_2025, politiques_vers_dict, politiques_depuis_dict
from .tax_adoption_2025 import Adoption2025, calculer_adoption_2025, adoption_vers_dict, adoption_depuis_dict
from .tax_volunteers_2025 import Benevoles2025, ActiviteBenevole2025, calculer_benevoles_2025
from .tax_spouse_transfer_2025 import TransfertConjointFederal2025, valider_transfert_conjoint_2025, calculer_transfert_conjoint_2025
from .tax_tuition_received_2025 import TransfertsScolariteRecus2025, valider_transferts_scolarite_recus_2025
from .tax_tuition_received_2025 import DesignationScolariteRecue2025
from .tax_donation_carryforward_2025 import ReportsDonsFederaux2025, ReportDonFederal2025, valider_reports_dons_federaux_2025
from dataclasses import dataclass, asdict, fields
from datetime import datetime
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
from typing import Any

from .tax_tuition_transfer_2025 import TransfertScolariteSortant2025, valider_transfert_scolarite_sortant_2025
from .tax_tuition_carryforward_2025 import ReportsScolariteFederaux2025, valider_reports_scolarite_federaux_2025
from .tax_workers_benefit_2025 import AllocationTravailleurs2025, valider_allocation_travailleurs_2025
from .tax_medical_supplement_2025 import SupplementMedical2025, valider_supplement_medical_2025, verifier_famille_supplement_2025
from .tax_training_credit_2025 import Formation2025, valider_formation_2025
from .tax_quebec_senior_support_2025 import (SoutienAinesQuebec2025, valider_soutien_aines_quebec_2025, soutien_aines_vers_dict, soutien_aines_depuis_dict)
from .tax_quebec_volunteers_2025 import (VolontairesQuebec2025, valider_volontaires_quebec_2025, volontaires_vers_dict, volontaires_depuis_dict)
from .tax_quebec_home_support_2025 import (MaintienDomicileQuebec2025, valider_maintien_domicile_quebec_2025, maintien_domicile_vers_dict, maintien_domicile_depuis_dict)
from .tax_quebec_work_premium_2025 import (PrimeTravailQuebec2025, valider_prime_travail_quebec_2025, prime_travail_vers_dict, prime_travail_depuis_dict)
from .tax_quebec_solidarity_2025 import (SolidariteQuebec2025, valider_solidarite_quebec_2025, solidarite_quebec_vers_dict, solidarite_quebec_depuis_dict)
from .tax_quebec_caregiver_2025 import (PersonneAidanteQuebec2025, valider_aidante_quebec_2025, aidante_quebec_vers_dict, aidante_quebec_depuis_dict)
from .tax_quebec_childcare_2025 import (FraisGardeQuebec2025, valider_garde_quebec_2025,
    garde_quebec_vers_dict, garde_quebec_depuis_dict)
from .tax_quebec_refundable_medical_2025 import (MedicalRemboursableQuebec2025, valider_medical_remboursable_quebec_2025,
    medical_remboursable_quebec_vers_dict, medical_remboursable_quebec_depuis_dict)
from .tax_quebec_career_extension_2025 import (ProlongationCarriereQuebec2025, valider_carriere_quebec_2025,
    carriere_quebec_vers_dict, carriere_quebec_depuis_dict)
from .tax_quebec_home_buyers_2025 import (AchatHabitationQuebec2025, valider_achat_quebec_2025,
    achat_quebec_vers_dict, achat_quebec_depuis_dict)
from .tax_quebec_student_interest_2025 import (InteretsEtudiantsQuebec2025, valider_interets_quebec_2025,
    interets_quebec_vers_dict, interets_quebec_depuis_dict)
from .tax_student_loan_interest_2025 import (
    InteretsPretEtudiant2025, valider_interets_pret_etudiant_2025,
)
from .tax_adjustments_2025 import (
    AjustementReer2025,
    valider_ajustement_reer_2025,
)
from .tax_fhsa_2025 import (
    DeductionCeliapp2025,
    valider_deduction_celiapp_2025,
)
from .tax_child_care_2025 import (
    FraisGardeFederaux2025,
    valider_frais_garde_federaux_2025,
)
from .tax_employment_expenses_2025 import (
    DepensesEmploi2025,
    valider_depenses_emploi_2025,
)
from .tax_moving_expenses_2025 import (
    FraisDemenagement2025,
    valider_frais_demenagement_2025,
)
from .tax_support_payments_2025 import (
    PensionAlimentairePayee2025,
    valider_pension_alimentaire_payee_2025,
)
from .tax_other_deductions_2025 import (
    AutresDeductions2025,
    valider_autres_deductions_2025,
)
from .tax_union_dues_2025 import (
    CotisationsSyndicalesProfessionnelles2025,
    valider_cotisations_syndicales_2025,
)
from .tax_donations_2025 import (
    DonsBienfaisance2025,
    valider_dons_bienfaisance_2025,
)
from .tax_disability_2025 import (
    CreditDeficience2025,
    valider_credit_deficience_2025,
)
from .tax_drug_insurance_2025 import (
    AssuranceMedicamentsQuebec2025,
    valider_assurance_medicaments_2025,
)
from .tax_contribution_overpayments_2025 import (
    CotisationsExcedentaires2025,
    valider_cotisations_excedentaires_2025,
)
from .tax_age_retirement_2025 import (
    MontantsAgeRetraite2025,
    valider_montants_age_retraite_2025,
)
from .tax_federal_age_pension_2025 import (
    CreditsFederauxAgePension2025,
    valider_credits_federaux_age_pension_2025,
)
from .tax_federal_spouse_2025 import (
    MontantConjointFederal2025,
    valider_montant_conjoint_federal_2025,
)
from .tax_federal_home_accessibility_2025 import (
    DepensesAccessibiliteDomiciliaireFederal2025,
    valider_depenses_accessibilite_domiciliaire_2025,
)
from .tax_federal_home_buyers_2025 import (
    MontantAchatHabitationFederal2025,
    valider_montant_achat_habitation_2025,
)
from .tax_federal_caregiver_other_dependant_2025 import (
    PersonneAidant30450,
    AidantNaturelAutrePersonneChargeFederal2025,
    valider_aidant_naturel_30450_2025,
)
from .tax_federal_caregiver_spouse_dependant_2025 import (
    AidantNaturelConjointOuPersonneChargeFederal2025,
    valider_aidant_naturel_30425_2025,
)
from .tax_federal_caregiver_child_2025 import (
    EnfantAidant30500,
    verifier_combinaison_30400_30500_2025,
    AidantNaturelEnfantMoins18Federal2025,
    valider_aidant_naturel_enfant_moins18_federal_2025,
)
from .tax_federal_eligible_dependant_2025 import (
    MontantPersonneChargeAdmissibleFederal2025,
    valider_montant_personne_charge_admissible_federal_2025,
)
from .tax_living_alone_2025 import (
    PersonneVivantSeule2025,
    valider_personne_vivant_seule_2025,
)
from .tax_medical_expenses_2025 import (
    FraisMedicaux2025,
    valider_frais_medicaux_2025,
)
from .tax_tuition_2025 import (
    FraisScolarite2025,
    valider_frais_scolarite_2025,
)
from .tax_estimation_2025 import EstimationFiscale2025
from .tax_field_validation import (
    DonneeFiscaleValidee,
    STATUT_CORRIGE_VALIDE,
    STATUT_VALIDE,
)
from .tax_validated_case import DossierFiscalValide
from .tax_capital_loss_carryovers_2025 import ProfilReportsPertes2025, verifier_confirmation_reports_pertes_2025
from .tax_investment_expenses_2025 import ProfilFraisPlacement2025, valider_profil_frais_placement_2025, verifier_confirmation_frais_2025
from .tax_capital_gains_2025 import ProfilCapital2025, valider_profil_capital_2025, consolider_capital_2025
from .tax_dividend_income_2025 import ProfilDividendes2025, valider_profil_dividendes_2025, consolider_dividendes_2025
from .tax_interest_income_2025 import ProfilInterets2025, valider_profil_interets_2025, consolider_interets_2025
from .tax_investment_combinations_2025 import (
    consolider_interets_dividendes_2025,
    consolider_interets_dividendes_capital_2025,
)
from .tax_foreign_investment_2025 import (
    ProfilPlacementEtranger2025,
    ProfilCreditImpotEtranger2025,
    valider_profil_placement_etranger_2025,
    consolider_placement_etranger_2025,
    valider_profil_credit_impot_etranger_2025,
)
from .tax_replacement_benefits_2025 import (ProfilRemplacement2025, PrestationsRemplacement2025, valider_profil_remplacement_2025, detecter_remplacement_2025, consolider_remplacement_2025, appliquer_remplacement_2025, appliquer_redressement_358_2025, lignes_resume_remplacement_2025)
from .tax_rrsp_withdrawals_2025 import (ProfilRetraits2025, Retraits2025, valider_profil_retraits_2025, detecter_retraits_2025, consolider_retraits_2025, appliquer_retraits_2025, lignes_resume_retraits_2025)
from .tax_pension_income_2025 import ProfilPensions2025, valider_profil_pensions_2025, consolider_pensions_2025
from .tax_old_age_security_2025 import consolider_prestations_psv_2025, valider_confirmation_psv
from .tax_cpp_qpp_benefits_2025 import consolider_prestations_rrq_rpc_2025, valider_confirmation_rrq_rpc
from .tax_employment_insurance_2025 import consolider_prestations_ae_2025, valider_confirmation_ae
from .tax_parental_benefits_2025 import consolider_prestations_rqap_2025, valider_confirmation_rqap

from .tax_rpp_2025 import (
    CotisationsRpa2025, valider_cotisations_rpa_2025, verifier_rpa_dossier_2025,
)

SCHEMA_VERSION = 1

# Racine stable du projet, indépendante du dossier courant.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOSSIERS_FISCAUX_DIR = (
    PROJECT_ROOT / "data" / "dossiers_fiscaux"
)
STATUTS_VALIDATION_AUTORISES = {STATUT_VALIDE, STATUT_CORRIGE_VALIDE}


@dataclass(frozen=True)
class ResumeEstimationSauvegardee:
    resultat: str
    montant: Decimal
    impot_total_preliminaire: Decimal
    retenues_totales: Decimal


@dataclass(frozen=True)
class DossierFiscalEnregistre:
    chemin: Path
    dossier: DossierFiscalValide
    sauvegarde_le: str
    estimation: ResumeEstimationSauvegardee | None
    rapport_pdf: Path | None
    documents_manquants: tuple[Path, ...]
    ajustement_reer: AjustementReer2025
    deduction_celiapp: DeductionCeliapp2025
    frais_garde_federaux: FraisGardeFederaux2025
    depenses_emploi: DepensesEmploi2025
    frais_demenagement: FraisDemenagement2025
    pension_alimentaire_payee: PensionAlimentairePayee2025
    autres_deductions: AutresDeductions2025
    cotisations_syndicales: CotisationsSyndicalesProfessionnelles2025
    dons_bienfaisance: DonsBienfaisance2025
    frais_medicaux: FraisMedicaux2025
    frais_scolarite: FraisScolarite2025
    credit_deficience: CreditDeficience2025
    assurance_medicaments: AssuranceMedicamentsQuebec2025
    cotisations_excedentaires: CotisationsExcedentaires2025
    personne_vivant_seule: PersonneVivantSeule2025
    montants_age_retraite: MontantsAgeRetraite2025
    credits_federaux_age_pension: CreditsFederauxAgePension2025
    montant_conjoint_federal: MontantConjointFederal2025
    personne_charge_admissible_federale: MontantPersonneChargeAdmissibleFederal2025
    accessibilite_domiciliaire_federale: DepensesAccessibiliteDomiciliaireFederal2025
    achat_habitation_federal: MontantAchatHabitationFederal2025
    aidant_autre_personne_charge_federal: AidantNaturelAutrePersonneChargeFederal2025
    aidant_conjoint_personne_charge_federal: AidantNaturelConjointOuPersonneChargeFederal2025
    aidant_enfant_federal: AidantNaturelEnfantMoins18Federal2025
    cotisations_rpa: CotisationsRpa2025 = CotisationsRpa2025()
    rqap_confirme: bool = False
    ae_confirme: bool = False
    profil_reports_pertes: ProfilReportsPertes2025 = ProfilReportsPertes2025()
    profil_frais_placement: ProfilFraisPlacement2025 = ProfilFraisPlacement2025()
    profil_capital: ProfilCapital2025 = ProfilCapital2025()
    profil_dividendes: ProfilDividendes2025 = ProfilDividendes2025()
    profil_interets: ProfilInterets2025 = ProfilInterets2025()
    profil_placement_etranger: ProfilPlacementEtranger2025 = ProfilPlacementEtranger2025()
    profil_credit_impot_etranger: ProfilCreditImpotEtranger2025 = ProfilCreditImpotEtranger2025()
    profil_remplacement: ProfilRemplacement2025 = ProfilRemplacement2025()
    profil_retraits: ProfilRetraits2025 = ProfilRetraits2025()
    profil_pensions: ProfilPensions2025 = ProfilPensions2025()
    psv_confirme: bool = False
    rrq_rpc_confirme: bool = False
    renovations_multigenerationnelles: RenovationsMultigenerationnelles2025 = RenovationsMultigenerationnelles2025()
    transferts_handicap: TransfertsHandicap2025 = TransfertsHandicap2025()
    frais_medicaux_famille: FraisMedicauxFamilleFederaux2025 = FraisMedicauxFamilleFederaux2025()
    fournitures_educateur: FournituresEducateur2025 = FournituresEducateur2025()
    fonds_travailleurs: FondsTravailleurs2025 = FondsTravailleurs2025()
    contributions_politiques: ContributionsPolitiques2025 = ContributionsPolitiques2025()
    adoption: Adoption2025 = Adoption2025()
    benevoles: Benevoles2025 = Benevoles2025()
    transfert_conjoint: TransfertConjointFederal2025 = TransfertConjointFederal2025()
    transferts_scolarite_recus: TransfertsScolariteRecus2025 = TransfertsScolariteRecus2025()
    allocation_travailleurs: AllocationTravailleurs2025 = AllocationTravailleurs2025()
    frais_garde_quebec: FraisGardeQuebec2025 = FraisGardeQuebec2025()
    soutien_aines_quebec: SoutienAinesQuebec2025 = SoutienAinesQuebec2025()
    volontaires_quebec: VolontairesQuebec2025 = VolontairesQuebec2025()
    maintien_domicile_quebec: MaintienDomicileQuebec2025 = MaintienDomicileQuebec2025()
    prime_travail_quebec: PrimeTravailQuebec2025 = PrimeTravailQuebec2025()
    solidarite_quebec: SolidariteQuebec2025 = SolidariteQuebec2025()
    personne_aidante_quebec: PersonneAidanteQuebec2025 = PersonneAidanteQuebec2025()
    medical_remboursable_quebec: MedicalRemboursableQuebec2025 = MedicalRemboursableQuebec2025()
    prolongation_carriere_quebec: ProlongationCarriereQuebec2025 = ProlongationCarriereQuebec2025()
    achat_habitation_quebec: AchatHabitationQuebec2025 = AchatHabitationQuebec2025()
    interets_etudiants_quebec: InteretsEtudiantsQuebec2025 = InteretsEtudiantsQuebec2025()
    interets_pret_etudiant: InteretsPretEtudiant2025 = InteretsPretEtudiant2025()


def _nom_securise(valeur: str) -> str:
    texte = re.sub(r"[^\w-]+", "_", valeur.strip(), flags=re.UNICODE)
    texte = re.sub(r"_+", "_", texte).strip("_")
    return texte or "client"


def nom_fichier_dossier_fiscal(dossier: DossierFiscalValide) -> str:
    return f"Dossier_Fiscal_{dossier.annee_fiscale}_{_nom_securise(dossier.client)}.json"


def _chemin_vers_stockage(chemin: Path) -> str:
    valeur = Path(chemin)

    if valeur.is_absolute():
        absolu = valeur
    else:
        absolu = PROJECT_ROOT / valeur

    try:
        absolu_resolu = absolu.resolve()
        racine = PROJECT_ROOT.resolve()
        return str(absolu_resolu.relative_to(racine))
    except (OSError, ValueError):
        return str(absolu)


def _chemin_depuis_stockage(valeur: str) -> Path:
    chemin = Path(valeur)

    if chemin.is_absolute():
        return chemin

    return PROJECT_ROOT / chemin


def _decimal_texte(valeur: Decimal) -> str:
    return format(valeur, "f")


def _estimation_vers_dict(estimation: EstimationFiscale2025 | None):
    if estimation is None:
        return None
    r = estimation.rapprochement
    montant = r.remboursement_estime if r.remboursement_estime > 0 else r.solde_estime
    return {
        "resultat": r.resultat,
        "montant": _decimal_texte(montant),
        "impot_total_preliminaire": _decimal_texte(r.impot_total_preliminaire),
        "retenues_totales": _decimal_texte(r.retenues_totales),
    }



def _ajustement_reer_vers_dict(
    ajustement: AjustementReer2025 | None,
):
    if ajustement is None:
        ajustement = AjustementReer2025()

    valider_ajustement_reer_2025(ajustement)

    return {
        "deduction_reer": _decimal_texte(ajustement.deduction_reer),
        "plafond_reer_confirme": _decimal_texte(
            ajustement.plafond_reer_confirme
        ),
        "source_plafond_reer": ajustement.source_plafond_reer,
        "valide_par_comptable": bool(ajustement.valide_par_comptable),
        "inclut_transfert_reer": bool(ajustement.inclut_transfert_reer),
        "inclut_remboursement_rap_reep": bool(
            ajustement.inclut_remboursement_rap_reep
        ),
    }


def _ajustement_reer_depuis_dict(valeur: Any) -> AjustementReer2025:
    if valeur is None:
        return AjustementReer2025()

    if not isinstance(valeur, dict):
        raise ValueError("L'ajustement REER enregistré est invalide.")

    ajustement = AjustementReer2025(
        deduction_reer=_decimal_depuis_json(
            valeur.get("deduction_reer", "0"),
            "ajustement_reer.deduction_reer",
        ),
        plafond_reer_confirme=_decimal_depuis_json(
            valeur.get("plafond_reer_confirme", "0"),
            "ajustement_reer.plafond_reer_confirme",
        ),
        source_plafond_reer=str(valeur.get("source_plafond_reer", "")),
        valide_par_comptable=bool(
            valeur.get("valide_par_comptable", False)
        ),
        inclut_transfert_reer=bool(
            valeur.get("inclut_transfert_reer", False)
        ),
        inclut_remboursement_rap_reep=bool(
            valeur.get("inclut_remboursement_rap_reep", False)
        ),
    )
    return valider_ajustement_reer_2025(ajustement)


def _deduction_celiapp_vers_dict(
    profil: DeductionCeliapp2025 | None,
):
    if profil is None:
        profil = DeductionCeliapp2025()

    profil = valider_deduction_celiapp_2025(profil)
    return {
        "deduction": _decimal_texte(profil.deduction),
        "cotisations_directes_2025": _decimal_texte(
            profil.cotisations_directes_2025
        ),
        "droits_deduction_confirmes": _decimal_texte(
            profil.droits_deduction_confirmes
        ),
        "source_droits": profil.source_droits,
        "valide_par_comptable": bool(profil.valide_par_comptable),
        "titulaire_confirme": bool(profil.titulaire_confirme),
        "residence_canada_quebec_annee_complete": bool(
            profil.residence_canada_quebec_annee_complete
        ),
        "inclut_cotisations_inutilisees_anterieures": bool(
            profil.inclut_cotisations_inutilisees_anterieures
        ),
        "inclut_transfert_reer": bool(profil.inclut_transfert_reer),
        "retrait_2025": bool(profil.retrait_2025),
        "excedent_2025": bool(profil.excedent_2025),
    }


def _deduction_celiapp_depuis_dict(
    valeur: Any,
) -> DeductionCeliapp2025:
    if valeur is None:
        return DeductionCeliapp2025()
    if not isinstance(valeur, dict):
        raise ValueError("La déduction CELIAPP enregistrée est invalide.")

    profil = DeductionCeliapp2025(
        deduction=_decimal_depuis_json(
            valeur.get("deduction", "0"),
            "deduction_celiapp.deduction",
        ),
        cotisations_directes_2025=_decimal_depuis_json(
            valeur.get("cotisations_directes_2025", "0"),
            "deduction_celiapp.cotisations_directes_2025",
        ),
        droits_deduction_confirmes=_decimal_depuis_json(
            valeur.get("droits_deduction_confirmes", "0"),
            "deduction_celiapp.droits_deduction_confirmes",
        ),
        source_droits=str(valeur.get("source_droits", "")),
        valide_par_comptable=bool(
            valeur.get("valide_par_comptable", False)
        ),
        titulaire_confirme=bool(
            valeur.get("titulaire_confirme", False)
        ),
        residence_canada_quebec_annee_complete=bool(
            valeur.get(
                "residence_canada_quebec_annee_complete",
                False,
            )
        ),
        inclut_cotisations_inutilisees_anterieures=bool(
            valeur.get(
                "inclut_cotisations_inutilisees_anterieures",
                False,
            )
        ),
        inclut_transfert_reer=bool(
            valeur.get("inclut_transfert_reer", False)
        ),
        retrait_2025=bool(valeur.get("retrait_2025", False)),
        excedent_2025=bool(valeur.get("excedent_2025", False)),
    )
    return valider_deduction_celiapp_2025(profil)


def _frais_garde_federaux_vers_dict(
    profil: FraisGardeFederaux2025 | None,
):
    if profil is None:
        profil = FraisGardeFederaux2025()
    profil = valider_frais_garde_federaux_2025(profil)
    return {
        "frais_admissibles_payes": _decimal_texte(profil.frais_admissibles_payes),
        "revenu_gagne_t778": _decimal_texte(profil.revenu_gagne_t778),
        "nombre_enfants_moins_7_sans_dtc": int(profil.nombre_enfants_moins_7_sans_dtc),
        "nombre_enfants_7_a_16_ou_infirmes_sans_dtc": int(profil.nombre_enfants_7_a_16_ou_infirmes_sans_dtc),
        "nombre_enfants_dtc": int(profil.nombre_enfants_dtc),
        "source": profil.source,
        "valide_par_comptable": bool(profil.valide_par_comptable),
        "services_fournis_en_2025_confirmes": bool(profil.services_fournis_en_2025_confirmes),
        "frais_pour_gagner_revenu_confirmes": bool(profil.frais_pour_gagner_revenu_confirmes),
        "recus_confirmes": bool(profil.recus_confirmes),
        "demandeur_seul_ou_revenu_inferieur_confirme": bool(profil.demandeur_seul_ou_revenu_inferieur_confirme),
        "partie_c_requise": bool(profil.partie_c_requise),
        "partie_d_requise": bool(profil.partie_d_requise),
        "camp_avec_hebergement": bool(profil.camp_avec_hebergement),
        "garde_partagee": bool(profil.garde_partagee),
        "repartition_entre_contribuables": bool(profil.repartition_entre_contribuables),
        "demandeur_revenu_superieur": bool(profil.demandeur_revenu_superieur),
    }


def _frais_garde_federaux_depuis_dict(valeur: Any) -> FraisGardeFederaux2025:
    if valeur is None:
        return FraisGardeFederaux2025()
    if not isinstance(valeur, dict):
        raise ValueError("Les frais de garde fédéraux enregistrés sont invalides.")

    autorises = set(FraisGardeFederaux2025.__dataclass_fields__)
    inconnus = set(valeur) - autorises
    if inconnus:
        raise ValueError("Champs frais de garde fédéraux inconnus : " + ", ".join(sorted(inconnus)))

    try:
        moins_7 = int(valeur.get("nombre_enfants_moins_7_sans_dtc", 0))
        sept_16 = int(valeur.get("nombre_enfants_7_a_16_ou_infirmes_sans_dtc", 0))
        dtc = int(valeur.get("nombre_enfants_dtc", 0))
    except (TypeError, ValueError) as erreur:
        raise ValueError("Le nombre d'enfants des frais de garde est invalide.") from erreur

    profil = FraisGardeFederaux2025(
        frais_admissibles_payes=_decimal_depuis_json(
            valeur.get("frais_admissibles_payes", "0"),
            "frais_garde_federaux.frais_admissibles_payes",
        ),
        revenu_gagne_t778=_decimal_depuis_json(
            valeur.get("revenu_gagne_t778", "0"),
            "frais_garde_federaux.revenu_gagne_t778",
        ),
        nombre_enfants_moins_7_sans_dtc=moins_7,
        nombre_enfants_7_a_16_ou_infirmes_sans_dtc=sept_16,
        nombre_enfants_dtc=dtc,
        source=str(valeur.get("source", "")),
        valide_par_comptable=bool(valeur.get("valide_par_comptable", False)),
        services_fournis_en_2025_confirmes=bool(valeur.get("services_fournis_en_2025_confirmes", False)),
        frais_pour_gagner_revenu_confirmes=bool(valeur.get("frais_pour_gagner_revenu_confirmes", False)),
        recus_confirmes=bool(valeur.get("recus_confirmes", False)),
        demandeur_seul_ou_revenu_inferieur_confirme=bool(valeur.get("demandeur_seul_ou_revenu_inferieur_confirme", False)),
        partie_c_requise=bool(valeur.get("partie_c_requise", False)),
        partie_d_requise=bool(valeur.get("partie_d_requise", False)),
        camp_avec_hebergement=bool(valeur.get("camp_avec_hebergement", False)),
        garde_partagee=bool(valeur.get("garde_partagee", False)),
        repartition_entre_contribuables=bool(valeur.get("repartition_entre_contribuables", False)),
        demandeur_revenu_superieur=bool(valeur.get("demandeur_revenu_superieur", False)),
    )
    return valider_frais_garde_federaux_2025(profil)


def _depenses_emploi_vers_dict(
    profil: DepensesEmploi2025 | None,
):
    if profil is None:
        profil = DepensesEmploi2025()

    profil = valider_depenses_emploi_2025(profil)
    return {
        "deduction_federale_t777": _decimal_texte(
            profil.deduction_federale_t777
        ),
        "deduction_quebec_tp59": _decimal_texte(
            profil.deduction_quebec_tp59
        ),
        "source_federale": profil.source_federale,
        "source_quebec": profil.source_quebec,
        "valide_par_comptable": bool(profil.valide_par_comptable),
        "salarie_ordinaire_confirme": bool(
            profil.salarie_ordinaire_confirme
        ),
        "contrat_exige_depenses_confirme": bool(
            profil.contrat_exige_depenses_confirme
        ),
        "non_remboursees_confirme": bool(
            profil.non_remboursees_confirme
        ),
        "t2200_confirme": bool(profil.t2200_confirme),
        "t777_confirme": bool(profil.t777_confirme),
        "tp_64_3_confirme": bool(profil.tp_64_3_confirme),
        "tp_59_confirme": bool(profil.tp_59_confirme),
        "employe_a_commission": bool(profil.employe_a_commission),
        "vehicule_ou_cca": bool(profil.vehicule_ou_cca),
        "voyage_repas_logement": bool(profil.voyage_repas_logement),
        "bureau_a_domicile": bool(profil.bureau_a_domicile),
        "outils_ou_profil_specialise": bool(
            profil.outils_ou_profil_specialise
        ),
    }


def _depenses_emploi_depuis_dict(valeur: Any) -> DepensesEmploi2025:
    if valeur is None:
        return DepensesEmploi2025()
    if not isinstance(valeur, dict):
        raise ValueError("Les dépenses d'emploi enregistrées sont invalides.")

    autorises = set(DepensesEmploi2025.__dataclass_fields__)
    inconnus = set(valeur) - autorises
    if inconnus:
        raise ValueError(
            "Champs dépenses d'emploi inconnus : "
            + ", ".join(sorted(inconnus))
        )

    profil = DepensesEmploi2025(
        deduction_federale_t777=_decimal_depuis_json(
            valeur.get("deduction_federale_t777", "0"),
            "depenses_emploi.deduction_federale_t777",
        ),
        deduction_quebec_tp59=_decimal_depuis_json(
            valeur.get("deduction_quebec_tp59", "0"),
            "depenses_emploi.deduction_quebec_tp59",
        ),
        source_federale=str(valeur.get("source_federale", "")),
        source_quebec=str(valeur.get("source_quebec", "")),
        valide_par_comptable=bool(
            valeur.get("valide_par_comptable", False)
        ),
        salarie_ordinaire_confirme=bool(
            valeur.get("salarie_ordinaire_confirme", False)
        ),
        contrat_exige_depenses_confirme=bool(
            valeur.get("contrat_exige_depenses_confirme", False)
        ),
        non_remboursees_confirme=bool(
            valeur.get("non_remboursees_confirme", False)
        ),
        t2200_confirme=bool(valeur.get("t2200_confirme", False)),
        t777_confirme=bool(valeur.get("t777_confirme", False)),
        tp_64_3_confirme=bool(valeur.get("tp_64_3_confirme", False)),
        tp_59_confirme=bool(valeur.get("tp_59_confirme", False)),
        employe_a_commission=bool(
            valeur.get("employe_a_commission", False)
        ),
        vehicule_ou_cca=bool(valeur.get("vehicule_ou_cca", False)),
        voyage_repas_logement=bool(
            valeur.get("voyage_repas_logement", False)
        ),
        bureau_a_domicile=bool(
            valeur.get("bureau_a_domicile", False)
        ),
        outils_ou_profil_specialise=bool(
            valeur.get("outils_ou_profil_specialise", False)
        ),
    )
    return valider_depenses_emploi_2025(profil)


def _frais_demenagement_vers_dict(
    profil: FraisDemenagement2025 | None,
):
    if profil is None:
        profil = FraisDemenagement2025()

    profil = valider_frais_demenagement_2025(profil)
    return {
        "deduction_federale_t1m": _decimal_texte(
            profil.deduction_federale_t1m
        ),
        "deduction_quebec_tp348": _decimal_texte(
            profil.deduction_quebec_tp348
        ),
        "source_federale": profil.source_federale,
        "source_quebec": profil.source_quebec,
        "valide_par_comptable": bool(profil.valide_par_comptable),
        "salarie_ordinaire_confirme": bool(
            profil.salarie_ordinaire_confirme
        ),
        "demenagement_pour_emploi_confirme": bool(
            profil.demenagement_pour_emploi_confirme
        ),
        "rapprochement_40km_confirme": bool(
            profil.rapprochement_40km_confirme
        ),
        "demenagement_interieur_canada_confirme": bool(
            profil.demenagement_interieur_canada_confirme
        ),
        "remboursements_employeur_pris_en_compte_confirme": bool(
            profil.remboursements_employeur_pris_en_compte_confirme
        ),
        "t1m_confirme": bool(profil.t1m_confirme),
        "tp348_confirme": bool(profil.tp348_confirme),
        "travailleur_autonome": bool(profil.travailleur_autonome),
        "etudiant_temps_plein": bool(profil.etudiant_temps_plein),
        "demenagement_international": bool(
            profil.demenagement_international
        ),
        "report_annees_anterieures": bool(
            profil.report_annees_anterieures
        ),
        "plusieurs_demenagements_admissibles": bool(
            profil.plusieurs_demenagements_admissibles
        ),
    }


def _frais_demenagement_depuis_dict(
    valeur: Any,
) -> FraisDemenagement2025:
    if valeur is None:
        return FraisDemenagement2025()
    if not isinstance(valeur, dict):
        raise ValueError(
            "Les frais de déménagement enregistrés sont invalides."
        )

    autorises = set(FraisDemenagement2025.__dataclass_fields__)
    inconnus = set(valeur) - autorises
    if inconnus:
        raise ValueError(
            "Champs frais de déménagement inconnus : "
            + ", ".join(sorted(inconnus))
        )

    profil = FraisDemenagement2025(
        deduction_federale_t1m=_decimal_depuis_json(
            valeur.get("deduction_federale_t1m", "0"),
            "frais_demenagement.deduction_federale_t1m",
        ),
        deduction_quebec_tp348=_decimal_depuis_json(
            valeur.get("deduction_quebec_tp348", "0"),
            "frais_demenagement.deduction_quebec_tp348",
        ),
        source_federale=str(valeur.get("source_federale", "")),
        source_quebec=str(valeur.get("source_quebec", "")),
        valide_par_comptable=bool(
            valeur.get("valide_par_comptable", False)
        ),
        salarie_ordinaire_confirme=bool(
            valeur.get("salarie_ordinaire_confirme", False)
        ),
        demenagement_pour_emploi_confirme=bool(
            valeur.get("demenagement_pour_emploi_confirme", False)
        ),
        rapprochement_40km_confirme=bool(
            valeur.get("rapprochement_40km_confirme", False)
        ),
        demenagement_interieur_canada_confirme=bool(
            valeur.get("demenagement_interieur_canada_confirme", False)
        ),
        remboursements_employeur_pris_en_compte_confirme=bool(
            valeur.get(
                "remboursements_employeur_pris_en_compte_confirme",
                False,
            )
        ),
        t1m_confirme=bool(valeur.get("t1m_confirme", False)),
        tp348_confirme=bool(valeur.get("tp348_confirme", False)),
        travailleur_autonome=bool(
            valeur.get("travailleur_autonome", False)
        ),
        etudiant_temps_plein=bool(
            valeur.get("etudiant_temps_plein", False)
        ),
        demenagement_international=bool(
            valeur.get("demenagement_international", False)
        ),
        report_annees_anterieures=bool(
            valeur.get("report_annees_anterieures", False)
        ),
        plusieurs_demenagements_admissibles=bool(
            valeur.get("plusieurs_demenagements_admissibles", False)
        ),
    )
    return valider_frais_demenagement_2025(profil)



def _pension_alimentaire_payee_vers_dict(
    profil: PensionAlimentairePayee2025 | None,
):
    if profil is None:
        profil = PensionAlimentairePayee2025()

    profil = valider_pension_alimentaire_payee_2025(profil)
    return {
        "total_paye_federal_21999": _decimal_texte(
            profil.total_paye_federal_21999
        ),
        "deduction_federale_22000": _decimal_texte(
            profil.deduction_federale_22000
        ),
        "deduction_quebec_225": _decimal_texte(
            profil.deduction_quebec_225
        ),
        "source_federale": profil.source_federale,
        "source_quebec": profil.source_quebec,
        "valide_par_comptable": bool(profil.valide_par_comptable),
        "ordonnance_ou_entente_ecrite_confirmee": bool(
            profil.ordonnance_ou_entente_ecrite_confirmee
        ),
        "paiement_periodique_conjoint_ex_conjoint_confirme": bool(
            profil.paiement_periodique_conjoint_ex_conjoint_confirme
        ),
        "vie_separee_au_moment_paiement_confirmee": bool(
            profil.vie_separee_au_moment_paiement_confirmee
        ),
        "enregistrement_arc_confirme": bool(
            profil.enregistrement_arc_confirme
        ),
        "montant_federal_confirme": bool(
            profil.montant_federal_confirme
        ),
        "montant_quebec_confirme": bool(
            profil.montant_quebec_confirme
        ),
        "aucun_credit_personnel_lie_confirme": bool(
            profil.aucun_credit_personnel_lie_confirme
        ),
        "pension_enfant": bool(profil.pension_enfant),
        "regime_avant_mai_1997_ou_t1157": bool(
            profil.regime_avant_mai_1997_ou_t1157
        ),
        "arrerages_ou_retroactif": bool(
            profil.arrerages_ou_retroactif
        ),
        "paiement_forfaitaire": bool(profil.paiement_forfaitaire),
        "remboursement_pension": bool(profil.remboursement_pension),
        "frais_juridiques_ou_comptables": bool(
            profil.frais_juridiques_ou_comptables
        ),
        "plusieurs_beneficiaires": bool(
            profil.plusieurs_beneficiaires
        ),
        "annee_changement_etat_civil_avec_choix_credit": bool(
            profil.annee_changement_etat_civil_avec_choix_credit
        ),
    }


def _pension_alimentaire_payee_depuis_dict(
    valeur: Any,
) -> PensionAlimentairePayee2025:
    if valeur is None:
        return PensionAlimentairePayee2025()

    if not isinstance(valeur, dict):
        raise ValueError(
            "La pension alimentaire enregistrée est invalide."
        )

    autorises = set(PensionAlimentairePayee2025.__dataclass_fields__)
    inconnus = set(valeur) - autorises
    if inconnus:
        raise ValueError(
            "Champs pension alimentaire inconnus : "
            + ", ".join(sorted(inconnus))
        )

    profil = PensionAlimentairePayee2025(
        total_paye_federal_21999=_decimal_depuis_json(
            valeur.get("total_paye_federal_21999", "0"),
            "pension_alimentaire_payee.total_paye_federal_21999",
        ),
        deduction_federale_22000=_decimal_depuis_json(
            valeur.get("deduction_federale_22000", "0"),
            "pension_alimentaire_payee.deduction_federale_22000",
        ),
        deduction_quebec_225=_decimal_depuis_json(
            valeur.get("deduction_quebec_225", "0"),
            "pension_alimentaire_payee.deduction_quebec_225",
        ),
        source_federale=str(valeur.get("source_federale", "")),
        source_quebec=str(valeur.get("source_quebec", "")),
        valide_par_comptable=bool(
            valeur.get("valide_par_comptable", False)
        ),
        ordonnance_ou_entente_ecrite_confirmee=bool(
            valeur.get("ordonnance_ou_entente_ecrite_confirmee", False)
        ),
        paiement_periodique_conjoint_ex_conjoint_confirme=bool(
            valeur.get(
                "paiement_periodique_conjoint_ex_conjoint_confirme",
                False,
            )
        ),
        vie_separee_au_moment_paiement_confirmee=bool(
            valeur.get(
                "vie_separee_au_moment_paiement_confirmee",
                False,
            )
        ),
        enregistrement_arc_confirme=bool(
            valeur.get("enregistrement_arc_confirme", False)
        ),
        montant_federal_confirme=bool(
            valeur.get("montant_federal_confirme", False)
        ),
        montant_quebec_confirme=bool(
            valeur.get("montant_quebec_confirme", False)
        ),
        aucun_credit_personnel_lie_confirme=bool(
            valeur.get("aucun_credit_personnel_lie_confirme", False)
        ),
        pension_enfant=bool(valeur.get("pension_enfant", False)),
        regime_avant_mai_1997_ou_t1157=bool(
            valeur.get("regime_avant_mai_1997_ou_t1157", False)
        ),
        arrerages_ou_retroactif=bool(
            valeur.get("arrerages_ou_retroactif", False)
        ),
        paiement_forfaitaire=bool(
            valeur.get("paiement_forfaitaire", False)
        ),
        remboursement_pension=bool(
            valeur.get("remboursement_pension", False)
        ),
        frais_juridiques_ou_comptables=bool(
            valeur.get("frais_juridiques_ou_comptables", False)
        ),
        plusieurs_beneficiaires=bool(
            valeur.get("plusieurs_beneficiaires", False)
        ),
        annee_changement_etat_civil_avec_choix_credit=bool(
            valeur.get(
                "annee_changement_etat_civil_avec_choix_credit",
                False,
            )
        ),
    )
    return valider_pension_alimentaire_payee_2025(profil)



def _autres_deductions_vers_dict(
    profil: AutresDeductions2025 | None,
):
    if profil is None:
        profil = AutresDeductions2025()

    profil = valider_autres_deductions_2025(profil)
    return {
        "deduction_federale_23200": _decimal_texte(
            profil.deduction_federale_23200
        ),
        "deduction_quebec_250_code17": _decimal_texte(
            profil.deduction_quebec_250_code17
        ),
        "nature_federale": profil.nature_federale,
        "nature_quebec": profil.nature_quebec,
        "source_federale": profil.source_federale,
        "source_quebec": profil.source_quebec,
        "valide_par_comptable": bool(profil.valide_par_comptable),
        "montant_federal_deja_etabli_confirme": bool(
            profil.montant_federal_deja_etabli_confirme
        ),
        "montant_quebec_deja_etabli_confirme": bool(
            profil.montant_quebec_deja_etabli_confirme
        ),
        "aucune_autre_ligne_ou_bloc_applicable_confirme": bool(
            profil.aucune_autre_ligne_ou_bloc_applicable_confirme
        ),
        "remboursement_ae_ou_rqap": bool(
            profil.remboursement_ae_ou_rqap
        ),
        "recuperation_prestations_sociales_23500": bool(
            profil.recuperation_prestations_sociales_23500
        ),
        "retrait_reer_ou_t3012a": bool(
            profil.retrait_reer_ou_t3012a
        ),
        "frais_juridiques": bool(profil.frais_juridiques),
        "remboursement_pension_alimentaire": bool(
            profil.remboursement_pension_alimentaire
        ),
        "transfert_ou_cotisations_inutilisees_regime": bool(
            profil.transfert_ou_cotisations_inutilisees_regime
        ),
        "soutien_personne_handicapee": bool(
            profil.soutien_personne_handicapee
        ),
        "celiapp_montant_deja_inclus": bool(
            profil.celiapp_montant_deja_inclus
        ),
        "abri_fiscal_ou_revenu_fractionne": bool(
            profil.abri_fiscal_ou_revenu_fractionne
        ),
        "autre_traitement_specialise": bool(
            profil.autre_traitement_specialise
        ),
    }


def _autres_deductions_depuis_dict(
    valeur: Any,
) -> AutresDeductions2025:
    if valeur is None:
        return AutresDeductions2025()

    if not isinstance(valeur, dict):
        raise ValueError(
            "Les autres déductions enregistrées sont invalides."
        )

    autorises = set(AutresDeductions2025.__dataclass_fields__)
    inconnus = set(valeur) - autorises
    if inconnus:
        raise ValueError(
            "Champs autres déductions inconnus : "
            + ", ".join(sorted(inconnus))
        )

    profil = AutresDeductions2025(
        deduction_federale_23200=_decimal_depuis_json(
            valeur.get("deduction_federale_23200", "0"),
            "autres_deductions.deduction_federale_23200",
        ),
        deduction_quebec_250_code17=_decimal_depuis_json(
            valeur.get("deduction_quebec_250_code17", "0"),
            "autres_deductions.deduction_quebec_250_code17",
        ),
        nature_federale=str(valeur.get("nature_federale", "")),
        nature_quebec=str(valeur.get("nature_quebec", "")),
        source_federale=str(valeur.get("source_federale", "")),
        source_quebec=str(valeur.get("source_quebec", "")),
        valide_par_comptable=bool(
            valeur.get("valide_par_comptable", False)
        ),
        montant_federal_deja_etabli_confirme=bool(
            valeur.get(
                "montant_federal_deja_etabli_confirme",
                False,
            )
        ),
        montant_quebec_deja_etabli_confirme=bool(
            valeur.get(
                "montant_quebec_deja_etabli_confirme",
                False,
            )
        ),
        aucune_autre_ligne_ou_bloc_applicable_confirme=bool(
            valeur.get(
                "aucune_autre_ligne_ou_bloc_applicable_confirme",
                False,
            )
        ),
        remboursement_ae_ou_rqap=bool(
            valeur.get("remboursement_ae_ou_rqap", False)
        ),
        recuperation_prestations_sociales_23500=bool(
            valeur.get(
                "recuperation_prestations_sociales_23500",
                False,
            )
        ),
        retrait_reer_ou_t3012a=bool(
            valeur.get("retrait_reer_ou_t3012a", False)
        ),
        frais_juridiques=bool(
            valeur.get("frais_juridiques", False)
        ),
        remboursement_pension_alimentaire=bool(
            valeur.get("remboursement_pension_alimentaire", False)
        ),
        transfert_ou_cotisations_inutilisees_regime=bool(
            valeur.get(
                "transfert_ou_cotisations_inutilisees_regime",
                False,
            )
        ),
        soutien_personne_handicapee=bool(
            valeur.get("soutien_personne_handicapee", False)
        ),
        celiapp_montant_deja_inclus=bool(
            valeur.get("celiapp_montant_deja_inclus", False)
        ),
        abri_fiscal_ou_revenu_fractionne=bool(
            valeur.get("abri_fiscal_ou_revenu_fractionne", False)
        ),
        autre_traitement_specialise=bool(
            valeur.get("autre_traitement_specialise", False)
        ),
    )
    return valider_autres_deductions_2025(profil)


def _cotisations_syndicales_vers_dict(
    cotisations: CotisationsSyndicalesProfessionnelles2025 | None,
):
    if cotisations is None:
        cotisations = CotisationsSyndicalesProfessionnelles2025()

    valider_cotisations_syndicales_2025(cotisations)

    return {
        "montant_federal_admissible": _decimal_texte(
            cotisations.montant_federal_admissible
        ),
        "montant_quebec_admissible": _decimal_texte(
            cotisations.montant_quebec_admissible
        ),
        "source_federale": cotisations.source_federale,
        "source_quebec": cotisations.source_quebec,
        "valide_par_comptable": bool(
            cotisations.valide_par_comptable
        ),
        "sources_dedoublonnees": bool(
            cotisations.sources_dedoublonnees
        ),
    }


def _cotisations_syndicales_depuis_dict(
    valeur: Any,
) -> CotisationsSyndicalesProfessionnelles2025:
    if valeur is None:
        return CotisationsSyndicalesProfessionnelles2025()

    if not isinstance(valeur, dict):
        raise ValueError(
            "Les cotisations syndicales enregistrées sont invalides."
        )

    cotisations = CotisationsSyndicalesProfessionnelles2025(
        montant_federal_admissible=_decimal_depuis_json(
            valeur.get("montant_federal_admissible", "0"),
            "cotisations_syndicales.montant_federal_admissible",
        ),
        montant_quebec_admissible=_decimal_depuis_json(
            valeur.get("montant_quebec_admissible", "0"),
            "cotisations_syndicales.montant_quebec_admissible",
        ),
        source_federale=str(valeur.get("source_federale", "")),
        source_quebec=str(valeur.get("source_quebec", "")),
        valide_par_comptable=bool(
            valeur.get("valide_par_comptable", False)
        ),
        sources_dedoublonnees=bool(
            valeur.get("sources_dedoublonnees", False)
        ),
    )
    return valider_cotisations_syndicales_2025(cotisations)



def _reports_dons_vers_dict(p):
    valider_reports_dons_federaux_2025(p)
    v = asdict(p)
    v["montant_reclame"] = format(p.montant_reclame, ".2f")
    v["reports"] = [dict(annee=r.annee, montant=format(r.montant, ".2f"), source=r.source) for r in p.reports]
    return v


def _reports_dons_depuis_dict(valeur):
    if valeur is None:
        return ReportsDonsFederaux2025()
    if not isinstance(valeur, dict) or set(valeur) - set(ReportsDonsFederaux2025.__dataclass_fields__):
        raise ValueError("Profil reports dons ou clés inconnues invalides.")
    v = dict(valeur)
    v["montant_reclame"] = _decimal_depuis_json(v.get("montant_reclame", "0"), "Dons réclamés")
    reports = v.get("reports", [])
    if not isinstance(reports, list):
        raise ValueError("Liste reports dons invalide.")
    resultat = []
    for r in reports:
        if not isinstance(r, dict) or set(r) != {"annee", "montant", "source"}:
            raise ValueError("Report dons ou clés invalides.")
        resultat.append(ReportDonFederal2025(r["annee"], _decimal_depuis_json(r["montant"], "Solde dons"), r["source"]))
    v["reports"] = tuple(resultat)
    return valider_reports_dons_federaux_2025(ReportsDonsFederaux2025(**v))


def _dons_bienfaisance_vers_dict(
    dons: DonsBienfaisance2025 | None,
):
    if dons is None:
        dons = DonsBienfaisance2025()

    valider_dons_bienfaisance_2025(dons)

    return {
        "reports_federaux": _reports_dons_vers_dict(dons.reports_federaux),
        "montant_admissible_federal": _decimal_texte(
            dons.montant_admissible_federal
        ),
        "montant_admissible_quebec": _decimal_texte(
            dons.montant_admissible_quebec
        ),
        "source_federale": dons.source_federale,
        "source_quebec": dons.source_quebec,
        "valide_par_comptable": bool(dons.valide_par_comptable),
        "donataire_reconnu_confirme": bool(
            dons.donataire_reconnu_confirme
        ),
        "dons_monetaires_2025_uniquement": bool(
            dons.dons_monetaires_2025_uniquement
        ),
        "aucun_report_anterieur": bool(
            dons.aucun_report_anterieur
        ),
        "inclut_dons_jan_fev_2025": bool(
            dons.inclut_dons_jan_fev_2025
        ),
        "dons_jan_fev_deja_reclames_2024": bool(
            dons.dons_jan_fev_deja_reclames_2024
        ),
    }


def _dons_bienfaisance_depuis_dict(
    valeur: Any,
) -> DonsBienfaisance2025:
    if valeur is None:
        return DonsBienfaisance2025()

    if not isinstance(valeur, dict):
        raise ValueError(
            "Les dons de bienfaisance enregistrés sont invalides."
        )

    dons = DonsBienfaisance2025(
        reports_federaux=_reports_dons_depuis_dict(valeur.get("reports_federaux")),
        montant_admissible_federal=_decimal_depuis_json(
            valeur.get("montant_admissible_federal", "0"),
            "dons_bienfaisance.montant_admissible_federal",
        ),
        montant_admissible_quebec=_decimal_depuis_json(
            valeur.get("montant_admissible_quebec", "0"),
            "dons_bienfaisance.montant_admissible_quebec",
        ),
        source_federale=str(valeur.get("source_federale", "")),
        source_quebec=str(valeur.get("source_quebec", "")),
        valide_par_comptable=bool(
            valeur.get("valide_par_comptable", False)
        ),
        donataire_reconnu_confirme=bool(
            valeur.get("donataire_reconnu_confirme", False)
        ),
        dons_monetaires_2025_uniquement=bool(
            valeur.get("dons_monetaires_2025_uniquement", False)
        ),
        aucun_report_anterieur=bool(
            valeur.get("aucun_report_anterieur", False)
        ),
        inclut_dons_jan_fev_2025=bool(
            valeur.get("inclut_dons_jan_fev_2025", False)
        ),
        dons_jan_fev_deja_reclames_2024=bool(
            valeur.get("dons_jan_fev_deja_reclames_2024", False)
        ),
    )
    return valider_dons_bienfaisance_2025(dons)


def _verifier_prestations_familiales_stockees(contenu, dossier, medical):
    p = _frais_medicaux_depuis_dict(contenu.get("frais_medicaux")).supplement
    act = _allocation_travailleurs_depuis_dict(contenu.get("allocation_travailleurs"))
    if not (p.reclamer and p.mode_familial) and not act.famille.activer:
        return
    conjoint = _transfert_conjoint_depuis_dict(contenu.get("transfert_conjoint"), dossier.client)
    resultat = calculer_transfert_conjoint_2025(conjoint, beneficiaire=dossier.client) if conjoint.activer else None
    fonds = fonds_depuis_dict(contenu.get("fonds_travailleurs"), client=dossier.client, annee=dossier.annee_fiscale)
    politiques = politiques_depuis_dict(contenu.get("contributions_politiques"), client=dossier.client, annee=dossier.annee_fiscale)
    verifier_famille_supplement_2025(p, demandeur=dossier.client, medical=medical,
        conjoint_30300=_montant_conjoint_federal_depuis_dict(contenu.get("montant_conjoint_federal")),
        personne_30400=_personne_charge_admissible_federale_depuis_dict(contenu.get("personne_charge_admissible_federale")),
        conjoint_32600=resultat, noms_conjoints=(fonds.conjoint.nom, politiques.nom_conjoint),
        act_individuel=act.present and not act.famille.activer)
    verifier_concordance_act_familial_2025(act, demandeur=dossier.client, medical=medical, supplement=p,
        conjoint_30300=_montant_conjoint_federal_depuis_dict(contenu.get("montant_conjoint_federal")),
        personne_30400=_personne_charge_admissible_federale_depuis_dict(contenu.get("personne_charge_admissible_federale")),
        conjoint_32600=resultat, noms_conjoints=(fonds.conjoint.nom, politiques.nom_conjoint))


def _supplement_medical_depuis_dict(valeur):
    if valeur is None:
        return SupplementMedical2025()
    if not isinstance(valeur, dict) or set(valeur) - set(SupplementMedical2025.__dataclass_fields__):
        raise ValueError("Profil supplément médical ou clés inconnues invalides.")
    valeur = dict(valeur)
    revenu = valeur.get("revenu_net_conjoint", "0")
    if isinstance(revenu, bool) or not isinstance(revenu, (str, int)):
        raise ValueError("Revenu net du conjoint du supplément médical invalide.")
    try:
        valeur["revenu_net_conjoint"] = Decimal(revenu)
    except InvalidOperation as exc:
        raise ValueError("Revenu net du conjoint du supplément médical invalide.") from exc
    return valider_supplement_medical_2025(SupplementMedical2025(**valeur))


def _frais_medicaux_vers_dict(
    frais: FraisMedicaux2025 | None,
):
    if frais is None:
        frais = FraisMedicaux2025()

    valider_frais_medicaux_2025(frais)

    return {
        "supplement": {**asdict(frais.supplement),
                       "revenu_net_conjoint": format(frais.supplement.revenu_net_conjoint, ".2f")},
        "montant_admissible_federal": _decimal_texte(
            frais.montant_admissible_federal
        ),
        "montant_admissible_quebec": _decimal_texte(
            frais.montant_admissible_quebec
        ),
        "source_federale": frais.source_federale,
        "source_quebec": frais.source_quebec,
        "valide_par_comptable": bool(frais.valide_par_comptable),
        "recus_confirmes": bool(frais.recus_confirmes),
        "remboursements_soustraits": bool(
            frais.remboursements_soustraits
        ),
        "periode_12_mois_fin_2025_confirmee": bool(
            frais.periode_12_mois_fin_2025_confirmee
        ),
        "aucune_periode_deja_reclamee": bool(
            frais.aucune_periode_deja_reclamee
        ),
        "profil_individuel_sans_conjoint_dependant": bool(
            frais.profil_individuel_sans_conjoint_dependant
        ),
    }


def _frais_medicaux_depuis_dict(
    valeur: Any,
) -> FraisMedicaux2025:
    if valeur is None:
        return FraisMedicaux2025()

    if not isinstance(valeur, dict):
        raise ValueError(
            "Les frais médicaux enregistrés sont invalides."
        )

    frais = FraisMedicaux2025(
        supplement=_supplement_medical_depuis_dict(valeur.get("supplement")),
        montant_admissible_federal=_decimal_depuis_json(
            valeur.get("montant_admissible_federal", "0"),
            "frais_medicaux.montant_admissible_federal",
        ),
        montant_admissible_quebec=_decimal_depuis_json(
            valeur.get("montant_admissible_quebec", "0"),
            "frais_medicaux.montant_admissible_quebec",
        ),
        source_federale=str(valeur.get("source_federale", "")),
        source_quebec=str(valeur.get("source_quebec", "")),
        valide_par_comptable=bool(
            valeur.get("valide_par_comptable", False)
        ),
        recus_confirmes=bool(
            valeur.get("recus_confirmes", False)
        ),
        remboursements_soustraits=bool(
            valeur.get("remboursements_soustraits", False)
        ),
        periode_12_mois_fin_2025_confirmee=bool(
            valeur.get(
                "periode_12_mois_fin_2025_confirmee",
                False,
            )
        ),
        aucune_periode_deja_reclamee=bool(
            valeur.get("aucune_periode_deja_reclamee", False)
        ),
        profil_individuel_sans_conjoint_dependant=bool(
            valeur.get(
                "profil_individuel_sans_conjoint_dependant",
                False,
            )
        ),
    )
    return valider_frais_medicaux_2025(frais)


def _transfert_scolarite_sortant_depuis_dict(valeur):
    if valeur is None:
        return TransfertScolariteSortant2025()
    if not isinstance(valeur, dict) or set(valeur) - set(TransfertScolariteSortant2025.__dataclass_fields__):
        raise ValueError("Profil transfert sortant ou clés inconnues invalides.")
    valeurs = dict(valeur)
    valeurs["montant_designe"] = _decimal_depuis_json(valeurs.get("montant_designe", "0"), "Transfert désigné")
    return valider_transfert_scolarite_sortant_2025(TransfertScolariteSortant2025(**valeurs))


def _reports_scolarite_federaux_vers_dict(profil):
    valeurs = asdict(valider_reports_scolarite_federaux_2025(profil))
    valeurs["report_avis_2024"] = format(profil.report_avis_2024, ".2f")
    valeurs["transfert_sortant"]["montant_designe"] = format(profil.transfert_sortant.montant_designe, ".2f")
    return valeurs


def _reports_scolarite_federaux_depuis_dict(valeur):
    if valeur is None:
        return ReportsScolariteFederaux2025()
    if not isinstance(valeur, dict) or set(valeur) - set(ReportsScolariteFederaux2025.__dataclass_fields__):
        raise ValueError("Profil reports scolarité ou clés inconnues invalides.")
    valeurs = dict(valeur)
    valeurs["report_avis_2024"] = _decimal_depuis_json(valeurs.get("report_avis_2024", "0"), "Report scolarité")
    valeurs["transfert_sortant"] = _transfert_scolarite_sortant_depuis_dict(valeurs.get("transfert_sortant"))
    return valider_reports_scolarite_federaux_2025(ReportsScolariteFederaux2025(**valeurs))


def _formation_vers_dict(profil):
    valider_formation_2025(profil)
    valeurs = asdict(profil)
    for nom in ("frais_canadiens", "plafond_avis_2025"):
        valeurs[nom] = format(valeurs[nom], ".2f")
    return valeurs


def _formation_depuis_dict(valeur):
    if valeur is None:
        return Formation2025()
    if not isinstance(valeur, dict) or set(valeur) - set(Formation2025.__dataclass_fields__):
        raise ValueError("Profil formation ou clés inconnues invalides.")
    valeurs = dict(valeur)
    for nom in ("frais_canadiens", "plafond_avis_2025"):
        valeurs[nom] = _decimal_depuis_json(valeurs.get(nom, "0"), "formation." + nom)
    return valider_formation_2025(Formation2025(**valeurs))


def _frais_scolarite_vers_dict(
    frais: FraisScolarite2025 | None,
):
    if frais is None:
        frais = FraisScolarite2025()

    valider_frais_scolarite_2025(frais)

    return {
        "reports_federaux": _reports_scolarite_federaux_vers_dict(frais.reports_federaux),
        "formation": _formation_vers_dict(frais.formation),
        "montant_admissible_federal": _decimal_texte(
            frais.montant_admissible_federal
        ),
        "montant_admissible_quebec": _decimal_texte(
            frais.montant_admissible_quebec
        ),
        "source_federale": frais.source_federale,
        "source_quebec": frais.source_quebec,
        "valide_par_comptable": bool(frais.valide_par_comptable),
        "piece_federale_confirmee": bool(frais.piece_federale_confirmee),
        "recu_officiel_quebec_confirme": bool(
            frais.recu_officiel_quebec_confirme
        ),
        "seuil_100_confirme": bool(frais.seuil_100_confirme),
        "remboursements_soustraits": bool(
            frais.remboursements_soustraits
        ),
        "frais_2025_uniquement": bool(frais.frais_2025_uniquement),
        "aucun_report_anterieur": bool(frais.aucun_report_anterieur),
        "aucun_transfert": bool(frais.aucun_transfert),
        "credit_canadien_formation_non_reclame": bool(
            frais.credit_canadien_formation_non_reclame
        ),
        "profil_resident_quebec_simple": bool(
            frais.profil_resident_quebec_simple
        ),
    }


def _frais_scolarite_depuis_dict(
    valeur: Any,
) -> FraisScolarite2025:
    if valeur is None:
        return FraisScolarite2025()

    if not isinstance(valeur, dict):
        raise ValueError(
            "Les frais de scolarité enregistrés sont invalides."
        )

    frais = FraisScolarite2025(
        reports_federaux=_reports_scolarite_federaux_depuis_dict(valeur.get("reports_federaux")),
        formation=_formation_depuis_dict(valeur.get("formation")),
        montant_admissible_federal=_decimal_depuis_json(
            valeur.get("montant_admissible_federal", "0"),
            "frais_scolarite.montant_admissible_federal",
        ),
        montant_admissible_quebec=_decimal_depuis_json(
            valeur.get("montant_admissible_quebec", "0"),
            "frais_scolarite.montant_admissible_quebec",
        ),
        source_federale=str(valeur.get("source_federale", "")),
        source_quebec=str(valeur.get("source_quebec", "")),
        valide_par_comptable=bool(
            valeur.get("valide_par_comptable", False)
        ),
        piece_federale_confirmee=bool(
            valeur.get("piece_federale_confirmee", False)
        ),
        recu_officiel_quebec_confirme=bool(
            valeur.get("recu_officiel_quebec_confirme", False)
        ),
        seuil_100_confirme=bool(
            valeur.get("seuil_100_confirme", False)
        ),
        remboursements_soustraits=bool(
            valeur.get("remboursements_soustraits", False)
        ),
        frais_2025_uniquement=bool(
            valeur.get("frais_2025_uniquement", False)
        ),
        aucun_report_anterieur=bool(
            valeur.get("aucun_report_anterieur", False)
        ),
        aucun_transfert=bool(
            valeur.get("aucun_transfert", False)
        ),
        credit_canadien_formation_non_reclame=bool(
            valeur.get("credit_canadien_formation_non_reclame", False)
        ),
        profil_resident_quebec_simple=bool(
            valeur.get("profil_resident_quebec_simple", False)
        ),
    )
    return valider_frais_scolarite_2025(frais)


def _credit_deficience_vers_dict(
    credit: CreditDeficience2025 | None,
):
    if credit is None:
        credit = CreditDeficience2025()

    valider_credit_deficience_2025(credit)

    return {
        "naissance_federale": credit.naissance_federale,
        "soins_reclames_federaux": format(credit.soins_reclames_federaux, ".2f"),
        "source_soins_federaux": credit.source_soins_federaux,
        "soins_federaux_valides": credit.soins_federaux_valides,
        "reclamer_federal": bool(credit.reclamer_federal),
        "reclamer_quebec": bool(credit.reclamer_quebec),
        "source_federale": credit.source_federale,
        "source_quebec": credit.source_quebec,
        "valide_par_comptable": bool(credit.valide_par_comptable),
        "age_18_plus_au_1_janvier_2025": bool(
            credit.age_18_plus_au_1_janvier_2025
        ),
        "deficience_12_mois_confirmee": bool(
            credit.deficience_12_mois_confirmee
        ),
        "profil_soi_meme_resident_quebec": bool(
            credit.profil_soi_meme_resident_quebec
        ),
        "ciph_approuve_arc": bool(credit.ciph_approuve_arc),
        "attestation_quebec_confirmee": bool(
            credit.attestation_quebec_confirmee
        ),
        "aucun_conflit_soins_prepose_etablissement": bool(
            credit.aucun_conflit_soins_prepose_etablissement
        ),
        "aucun_transfert_federal": bool(
            credit.aucun_transfert_federal
        ),
    }


def _credit_deficience_depuis_dict(
    valeur: Any,
) -> CreditDeficience2025:
    if valeur is None:
        return CreditDeficience2025()

    if not isinstance(valeur, dict):
        raise ValueError(
            "Le crédit handicap/déficience enregistré est invalide."
        )

    from dataclasses import fields
    if set(valeur) - {f.name for f in fields(CreditDeficience2025)}:
        raise ValueError("Clé inconnue du profil handicap/déficience.")
    soins = valeur.get("soins_reclames_federaux", "0")
    if not isinstance(soins, (str, int)) or isinstance(soins, bool):
        raise ValueError("Type invalide des frais de soins fédéraux.")

    credit = CreditDeficience2025(
        naissance_federale=valeur.get("naissance_federale", ""),
        soins_reclames_federaux=_decimal_depuis_json(soins, "soins_reclames_federaux"),
        source_soins_federaux=valeur.get("source_soins_federaux", ""),
        soins_federaux_valides=valeur.get("soins_federaux_valides", False),
        reclamer_federal=bool(
            valeur.get("reclamer_federal", False)
        ),
        reclamer_quebec=bool(
            valeur.get("reclamer_quebec", False)
        ),
        source_federale=str(
            valeur.get("source_federale", "")
        ),
        source_quebec=str(
            valeur.get("source_quebec", "")
        ),
        valide_par_comptable=bool(
            valeur.get("valide_par_comptable", False)
        ),
        age_18_plus_au_1_janvier_2025=bool(
            valeur.get("age_18_plus_au_1_janvier_2025", False)
        ),
        deficience_12_mois_confirmee=bool(
            valeur.get("deficience_12_mois_confirmee", False)
        ),
        profil_soi_meme_resident_quebec=bool(
            valeur.get("profil_soi_meme_resident_quebec", False)
        ),
        ciph_approuve_arc=bool(
            valeur.get("ciph_approuve_arc", False)
        ),
        attestation_quebec_confirmee=bool(
            valeur.get("attestation_quebec_confirmee", False)
        ),
        aucun_conflit_soins_prepose_etablissement=bool(
            valeur.get(
                "aucun_conflit_soins_prepose_etablissement",
                False,
            )
        ),
        aucun_transfert_federal=bool(
            valeur.get("aucun_transfert_federal", False)
        ),
    )
    return valider_credit_deficience_2025(credit)


def _assurance_medicaments_vers_dict(
    assurance: AssuranceMedicamentsQuebec2025 | None,
):
    if assurance is None:
        assurance = AssuranceMedicamentsQuebec2025()

    valider_assurance_medicaments_2025(assurance)

    return {
        "type_couverture": assurance.type_couverture,
        "couverture_toute_annee": bool(
            assurance.couverture_toute_annee
        ),
        "sans_conjoint_31_decembre_2025": bool(
            assurance.sans_conjoint_31_decembre_2025
        ),
        "revenu_ligne_275": _decimal_texte(
            assurance.revenu_ligne_275
        ),
        "revenu_ligne_48_annexe_k": _decimal_texte(
            assurance.revenu_ligne_48_annexe_k
        ),
        "aucun_mois_exempt": bool(assurance.aucun_mois_exempt),
        "carte_ramq_valide_2025": bool(
            assurance.carte_ramq_valide_2025
        ),
        "situation_validee_par_comptable": bool(
            assurance.situation_validee_par_comptable
        ),
        "aucun_cas_particulier": bool(
            assurance.aucun_cas_particulier
        ),
        "source": assurance.source,
        "code_case_449": assurance.code_case_449,
    }


def _assurance_medicaments_depuis_dict(
    valeur: Any,
) -> AssuranceMedicamentsQuebec2025:
    if valeur is None:
        return AssuranceMedicamentsQuebec2025()

    if not isinstance(valeur, dict):
        raise ValueError(
            "L'assurance médicaments enregistrée est invalide."
        )

    assurance = AssuranceMedicamentsQuebec2025(
        type_couverture=str(
            valeur.get("type_couverture", "")
        ),
        couverture_toute_annee=bool(
            valeur.get("couverture_toute_annee", False)
        ),
        sans_conjoint_31_decembre_2025=bool(
            valeur.get(
                "sans_conjoint_31_decembre_2025",
                False,
            )
        ),
        revenu_ligne_275=_decimal_depuis_json(
            valeur.get("revenu_ligne_275", "0"),
            "assurance_medicaments.revenu_ligne_275",
        ),
        revenu_ligne_48_annexe_k=_decimal_depuis_json(
            valeur.get("revenu_ligne_48_annexe_k", "0"),
            "assurance_medicaments.revenu_ligne_48_annexe_k",
        ),
        aucun_mois_exempt=bool(
            valeur.get("aucun_mois_exempt", False)
        ),
        carte_ramq_valide_2025=bool(
            valeur.get("carte_ramq_valide_2025", False)
        ),
        situation_validee_par_comptable=bool(
            valeur.get(
                "situation_validee_par_comptable",
                False,
            )
        ),
        aucun_cas_particulier=bool(
            valeur.get("aucun_cas_particulier", False)
        ),
        source=str(valeur.get("source", "")),
        code_case_449=str(
            valeur.get("code_case_449", "")
        ),
    )
    return valider_assurance_medicaments_2025(assurance)


def _cotisations_excedentaires_vers_dict(
    cotisations: CotisationsExcedentaires2025 | None,
):
    if cotisations is None:
        cotisations = CotisationsExcedentaires2025()

    valider_cotisations_excedentaires_2025(cotisations)

    return {
        "rrq_ba": _decimal_texte(cotisations.rrq_ba),
        "rrq_bb": _decimal_texte(cotisations.rrq_bb),
        "gains_admissibles_rrq": _decimal_texte(
            cotisations.gains_admissibles_rrq
        ),
        "assurance_emploi": _decimal_texte(
            cotisations.assurance_emploi
        ),
        "gains_assurables_ae": _decimal_texte(
            cotisations.gains_assurables_ae
        ),
        "rqap": _decimal_texte(cotisations.rqap),
        "revenus_assujettis_rqap": _decimal_texte(
            cotisations.revenus_assujettis_rqap
        ),
        "source": cotisations.source,
        "valide_par_comptable": bool(
            cotisations.valide_par_comptable
        ),
        "resident_quebec_31_decembre_2025": bool(
            cotisations.resident_quebec_31_decembre_2025
        ),
        "emploi_quebec_uniquement": bool(
            cotisations.emploi_quebec_uniquement
        ),
        "rrq_uniquement_sans_rpc": bool(
            cotisations.rrq_uniquement_sans_rpc
        ),
        "aucun_travail_autonome": bool(
            cotisations.aucun_travail_autonome
        ),
        "profil_rrq_standard_18_64": bool(
            cotisations.profil_rrq_standard_18_64
        ),
        "aucun_cas_particulier_ae": bool(
            cotisations.aucun_cas_particulier_ae
        ),
        "aucun_cas_particulier_rqap": bool(
            cotisations.aucun_cas_particulier_rqap
        ),
        "calcul_standard_confirme": bool(
            cotisations.calcul_standard_confirme
        ),
        "multi_employeurs_confirme": cotisations.multi_employeurs_confirme,
    }


def _cotisations_excedentaires_depuis_dict(
    valeur: Any,
) -> CotisationsExcedentaires2025:
    if valeur is None:
        return CotisationsExcedentaires2025()

    if not isinstance(valeur, dict):
        raise ValueError(
            "Les cotisations excédentaires enregistrées sont invalides."
        )

    cotisations = CotisationsExcedentaires2025(
        rrq_ba=_decimal_depuis_json(
            valeur.get("rrq_ba", "0"),
            "cotisations_excedentaires.rrq_ba",
        ),
        rrq_bb=_decimal_depuis_json(
            valeur.get("rrq_bb", "0"),
            "cotisations_excedentaires.rrq_bb",
        ),
        gains_admissibles_rrq=_decimal_depuis_json(
            valeur.get("gains_admissibles_rrq", "0"),
            "cotisations_excedentaires.gains_admissibles_rrq",
        ),
        assurance_emploi=_decimal_depuis_json(
            valeur.get("assurance_emploi", "0"),
            "cotisations_excedentaires.assurance_emploi",
        ),
        gains_assurables_ae=_decimal_depuis_json(
            valeur.get("gains_assurables_ae", "0"),
            "cotisations_excedentaires.gains_assurables_ae",
        ),
        rqap=_decimal_depuis_json(
            valeur.get("rqap", "0"),
            "cotisations_excedentaires.rqap",
        ),
        revenus_assujettis_rqap=_decimal_depuis_json(
            valeur.get("revenus_assujettis_rqap", "0"),
            "cotisations_excedentaires.revenus_assujettis_rqap",
        ),
        source=str(valeur.get("source", "")),
        valide_par_comptable=bool(
            valeur.get("valide_par_comptable", False)
        ),
        resident_quebec_31_decembre_2025=bool(
            valeur.get(
                "resident_quebec_31_decembre_2025",
                False,
            )
        ),
        emploi_quebec_uniquement=bool(
            valeur.get("emploi_quebec_uniquement", False)
        ),
        rrq_uniquement_sans_rpc=bool(
            valeur.get("rrq_uniquement_sans_rpc", False)
        ),
        aucun_travail_autonome=bool(
            valeur.get("aucun_travail_autonome", False)
        ),
        profil_rrq_standard_18_64=bool(
            valeur.get("profil_rrq_standard_18_64", False)
        ),
        aucun_cas_particulier_ae=bool(
            valeur.get("aucun_cas_particulier_ae", False)
        ),
        aucun_cas_particulier_rqap=bool(
            valeur.get("aucun_cas_particulier_rqap", False)
        ),
        calcul_standard_confirme=bool(
            valeur.get("calcul_standard_confirme", False)
        ),
        multi_employeurs_confirme=valeur.get("multi_employeurs_confirme", False),
    )
    return valider_cotisations_excedentaires_2025(cotisations)


def _personne_vivant_seule_vers_dict(
    profil: PersonneVivantSeule2025 | None,
):
    if profil is None:
        profil = PersonneVivantSeule2025()

    valider_personne_vivant_seule_2025(profil)

    return {
        "combinaison_annexe_b_confirmee": profil.combinaison_annexe_b_confirmee,
        "reclamer_montant": bool(profil.reclamer_montant),
        "revenu_familial_net": _decimal_texte(
            profil.revenu_familial_net
        ),
        "personne_vivant_seule_toute_annee": bool(
            profil.personne_vivant_seule_toute_annee
        ),
        "habitation_maintenue_par_contribuable": bool(
            profil.habitation_maintenue_par_contribuable
        ),
        "seulement_personnes_autorisees_dans_habitation": bool(
            profil.seulement_personnes_autorisees_dans_habitation
        ),
        "aucun_conjoint_31_decembre_2025": bool(
            profil.aucun_conjoint_31_decembre_2025
        ),
        "resident_quebec_canada_toute_annee": bool(
            profil.resident_quebec_canada_toute_annee
        ),
        "reclamer_additionnel_monoparental": bool(
            profil.reclamer_additionnel_monoparental
        ),
        "enfant_majeur_etudes_admissible": bool(
            profil.enfant_majeur_etudes_admissible
        ),
        "aucun_droit_allocation_famille_decembre": bool(
            profil.aucun_droit_allocation_famille_decembre
        ),
        "mois_allocation_famille_2025": int(
            profil.mois_allocation_famille_2025
        ),
        "aucun_montant_age_ou_retraite": bool(
            profil.aucun_montant_age_ou_retraite
        ),
        "documents_justificatifs_confirmes": bool(
            profil.documents_justificatifs_confirmes
        ),
        "valide_par_comptable": bool(
            profil.valide_par_comptable
        ),
        "source": profil.source,
    }


def _personne_vivant_seule_depuis_dict(
    valeur: Any,
) -> PersonneVivantSeule2025:
    if valeur is None:
        return PersonneVivantSeule2025()

    if not isinstance(valeur, dict):
        raise ValueError(
            "Le profil personne vivant seule enregistré est invalide."
        )

    try:
        mois_allocation = int(
            valeur.get("mois_allocation_famille_2025", 0)
        )
    except (TypeError, ValueError) as erreur:
        raise ValueError(
            "Le nombre de mois d'Allocation famille enregistré "
            "est invalide."
        ) from erreur

    _verifier_types_annexe_b_6a(valeur, PersonneVivantSeule2025())
    profil = PersonneVivantSeule2025(
        combinaison_annexe_b_confirmee=valeur.get("combinaison_annexe_b_confirmee", False),
        reclamer_montant=bool(
            valeur.get("reclamer_montant", False)
        ),
        revenu_familial_net=_decimal_depuis_json(
            valeur.get("revenu_familial_net", "0"),
            "personne_vivant_seule.revenu_familial_net",
        ),
        personne_vivant_seule_toute_annee=bool(
            valeur.get(
                "personne_vivant_seule_toute_annee",
                False,
            )
        ),
        habitation_maintenue_par_contribuable=bool(
            valeur.get(
                "habitation_maintenue_par_contribuable",
                False,
            )
        ),
        seulement_personnes_autorisees_dans_habitation=bool(
            valeur.get(
                "seulement_personnes_autorisees_dans_habitation",
                False,
            )
        ),
        aucun_conjoint_31_decembre_2025=bool(
            valeur.get(
                "aucun_conjoint_31_decembre_2025",
                False,
            )
        ),
        resident_quebec_canada_toute_annee=bool(
            valeur.get(
                "resident_quebec_canada_toute_annee",
                False,
            )
        ),
        reclamer_additionnel_monoparental=bool(
            valeur.get(
                "reclamer_additionnel_monoparental",
                False,
            )
        ),
        enfant_majeur_etudes_admissible=bool(
            valeur.get(
                "enfant_majeur_etudes_admissible",
                False,
            )
        ),
        aucun_droit_allocation_famille_decembre=bool(
            valeur.get(
                "aucun_droit_allocation_famille_decembre",
                False,
            )
        ),
        mois_allocation_famille_2025=mois_allocation,
        aucun_montant_age_ou_retraite=bool(
            valeur.get(
                "aucun_montant_age_ou_retraite",
                False,
            )
        ),
        documents_justificatifs_confirmes=bool(
            valeur.get(
                "documents_justificatifs_confirmes",
                False,
            )
        ),
        valide_par_comptable=bool(
            valeur.get("valide_par_comptable", False)
        ),
        source=str(valeur.get("source", "")),
    )
    return valider_personne_vivant_seule_2025(profil)


def _credits_federaux_age_pension_vers_dict(
    profil: CreditsFederauxAgePension2025 | None,
):
    if profil is None:
        profil = CreditsFederauxAgePension2025()

    valider_credits_federaux_age_pension_2025(profil)

    return {
        "reclamer_montant_age": bool(
            profil.reclamer_montant_age
        ),
        "age_65_plus_31_decembre_2025": bool(
            profil.age_65_plus_31_decembre_2025
        ),
        "revenu_net_ligne_23600": _decimal_texte(
            profil.revenu_net_ligne_23600
        ),
        "reclamer_montant_pension": bool(
            profil.reclamer_montant_pension
        ),
        "revenu_pension_admissible": _decimal_texte(
            profil.revenu_pension_admissible
        ),
        "resident_canada_toute_annee": bool(
            profil.resident_canada_toute_annee
        ),
        "aucune_regle_deces": bool(
            profil.aucune_regle_deces
        ),
        "aucun_fractionnement_pension": bool(
            profil.aucun_fractionnement_pension
        ),
        "aucun_transfert_conjoint": bool(
            profil.aucun_transfert_conjoint
        ),
        "revenu_pension_admissible_confirme": bool(
            profil.revenu_pension_admissible_confirme
        ),
        "valide_par_comptable": bool(
            profil.valide_par_comptable
        ),
        "source_age": profil.source_age,
        "source_pension": profil.source_pension,
    }


def _credits_federaux_age_pension_depuis_dict(
    valeur: Any,
) -> CreditsFederauxAgePension2025:
    if valeur is None:
        return CreditsFederauxAgePension2025()

    if not isinstance(valeur, dict):
        raise ValueError(
            "Le profil âge/pension fédéral enregistré est invalide."
        )

    profil = CreditsFederauxAgePension2025(
        reclamer_montant_age=bool(
            valeur.get("reclamer_montant_age", False)
        ),
        age_65_plus_31_decembre_2025=bool(
            valeur.get(
                "age_65_plus_31_decembre_2025",
                False,
            )
        ),
        revenu_net_ligne_23600=_decimal_depuis_json(
            valeur.get("revenu_net_ligne_23600", "0"),
            (
                "credits_federaux_age_pension."
                "revenu_net_ligne_23600"
            ),
        ),
        reclamer_montant_pension=bool(
            valeur.get("reclamer_montant_pension", False)
        ),
        revenu_pension_admissible=_decimal_depuis_json(
            valeur.get("revenu_pension_admissible", "0"),
            (
                "credits_federaux_age_pension."
                "revenu_pension_admissible"
            ),
        ),
        resident_canada_toute_annee=bool(
            valeur.get(
                "resident_canada_toute_annee",
                False,
            )
        ),
        aucune_regle_deces=bool(
            valeur.get("aucune_regle_deces", False)
        ),
        aucun_fractionnement_pension=bool(
            valeur.get(
                "aucun_fractionnement_pension",
                False,
            )
        ),
        aucun_transfert_conjoint=bool(
            valeur.get("aucun_transfert_conjoint", False)
        ),
        revenu_pension_admissible_confirme=bool(
            valeur.get(
                "revenu_pension_admissible_confirme",
                False,
            )
        ),
        valide_par_comptable=bool(
            valeur.get("valide_par_comptable", False)
        ),
        source_age=str(
            valeur.get("source_age", "")
        ),
        source_pension=str(
            valeur.get("source_pension", "")
        ),
    )
    return valider_credits_federaux_age_pension_2025(profil)


def _montant_conjoint_federal_vers_dict(
    profil: MontantConjointFederal2025 | None,
):
    if profil is None:
        profil = MontantConjointFederal2025()

    valider_montant_conjoint_federal_2025(profil)

    return {
        "reclamer_montant": bool(profil.reclamer_montant),
        "revenu_net_contribuable_ligne_23600": _decimal_texte(
            profil.revenu_net_contribuable_ligne_23600
        ),
        "revenu_net_conjoint_2025": _decimal_texte(
            profil.revenu_net_conjoint_2025
        ),
        "contribuable_resident_canada_toute_annee": bool(
            profil.contribuable_resident_canada_toute_annee
        ),
        "relation_conjoint_confirmee": bool(
            profil.relation_conjoint_confirmee
        ),
        "conjoint_soutenu_2025": bool(
            profil.conjoint_soutenu_2025
        ),
        "meme_conjoint_toute_annee_2025": bool(
            profil.meme_conjoint_toute_annee_2025
        ),
        "aucune_separation_2025": bool(
            profil.aucune_separation_2025
        ),
        "conjoint_resident_canada_toute_annee": bool(
            profil.conjoint_resident_canada_toute_annee
        ),
        "aucun_paiement_pension_alimentaire": bool(
            profil.aucun_paiement_pension_alimentaire
        ),
        "aucune_infirmite_conjoint": bool(
            profil.aucune_infirmite_conjoint
        ),
        "conjoint_avec_infirmite": bool(
            profil.conjoint_avec_infirmite
        ),
        "dependance_due_uniquement_a_infirmite": bool(
            profil.dependance_due_uniquement_a_infirmite
        ),
        "dependance_periode_considerable": bool(
            profil.dependance_periode_considerable
        ),
        "aidant_naturel_base_2687_inclus": bool(
            profil.aidant_naturel_base_2687_inclus
        ),
        "preuve_medicale_ou_t2201_confirmee": bool(
            profil.preuve_medicale_ou_t2201_confirmee
        ),
        "un_seul_conjoint_reclame_montant": bool(
            profil.un_seul_conjoint_reclame_montant
        ),
        "revenu_conjoint_confirme": bool(
            profil.revenu_conjoint_confirme
        ),
        "valide_par_comptable": bool(
            profil.valide_par_comptable
        ),
        "source_conjoint": profil.source_conjoint,
    }


def _montant_conjoint_federal_depuis_dict(
    valeur: Any,
) -> MontantConjointFederal2025:
    if valeur is None:
        return MontantConjointFederal2025()

    if not isinstance(valeur, dict):
        raise ValueError(
            "Le montant fédéral pour conjoint enregistré est invalide."
        )

    profil = MontantConjointFederal2025(
        reclamer_montant=bool(
            valeur.get("reclamer_montant", False)
        ),
        revenu_net_contribuable_ligne_23600=_decimal_depuis_json(
            valeur.get(
                "revenu_net_contribuable_ligne_23600",
                "0",
            ),
            (
                "montant_conjoint_federal."
                "revenu_net_contribuable_ligne_23600"
            ),
        ),
        revenu_net_conjoint_2025=_decimal_depuis_json(
            valeur.get("revenu_net_conjoint_2025", "0"),
            "montant_conjoint_federal.revenu_net_conjoint_2025",
        ),
        contribuable_resident_canada_toute_annee=bool(
            valeur.get(
                "contribuable_resident_canada_toute_annee",
                False,
            )
        ),
        relation_conjoint_confirmee=bool(
            valeur.get("relation_conjoint_confirmee", False)
        ),
        conjoint_soutenu_2025=bool(
            valeur.get("conjoint_soutenu_2025", False)
        ),
        meme_conjoint_toute_annee_2025=bool(
            valeur.get("meme_conjoint_toute_annee_2025", False)
        ),
        aucune_separation_2025=bool(
            valeur.get("aucune_separation_2025", False)
        ),
        conjoint_resident_canada_toute_annee=bool(
            valeur.get(
                "conjoint_resident_canada_toute_annee",
                False,
            )
        ),
        aucun_paiement_pension_alimentaire=bool(
            valeur.get(
                "aucun_paiement_pension_alimentaire",
                False,
            )
        ),
        aucune_infirmite_conjoint=bool(
            valeur.get("aucune_infirmite_conjoint", False)
        ),
        conjoint_avec_infirmite=bool(
            valeur.get("conjoint_avec_infirmite", False)
        ),
        dependance_due_uniquement_a_infirmite=bool(
            valeur.get(
                "dependance_due_uniquement_a_infirmite",
                False,
            )
        ),
        dependance_periode_considerable=bool(
            valeur.get(
                "dependance_periode_considerable",
                False,
            )
        ),
        aidant_naturel_base_2687_inclus=bool(
            valeur.get("aidant_naturel_base_2687_inclus", False)
        ),
        preuve_medicale_ou_t2201_confirmee=bool(
            valeur.get(
                "preuve_medicale_ou_t2201_confirmee",
                False,
            )
        ),
        un_seul_conjoint_reclame_montant=bool(
            valeur.get(
                "un_seul_conjoint_reclame_montant",
                False,
            )
        ),
        revenu_conjoint_confirme=bool(
            valeur.get("revenu_conjoint_confirme", False)
        ),
        valide_par_comptable=bool(
            valeur.get("valide_par_comptable", False)
        ),
        source_conjoint=str(
            valeur.get("source_conjoint", "")
        ),
    )

    return valider_montant_conjoint_federal_2025(profil)



def _personne_charge_admissible_federale_vers_dict(
    profil: MontantPersonneChargeAdmissibleFederal2025 | None,
):
    if profil is None:
        profil = MontantPersonneChargeAdmissibleFederal2025()

    valider_montant_personne_charge_admissible_federal_2025(
        profil
    )

    return {
        "enfant_infirmite_ligne30500": profil.enfant_infirmite_ligne30500,
        "reference_enfant": profil.reference_enfant,
        "reclamer_montant": bool(profil.reclamer_montant),
        "revenu_net_contribuable_ligne_23600": _decimal_texte(
            profil.revenu_net_contribuable_ligne_23600
        ),
        "revenu_net_personne_charge_2025": _decimal_texte(
            profil.revenu_net_personne_charge_2025
        ),
        "contribuable_resident_canada_toute_annee": bool(
            profil.contribuable_resident_canada_toute_annee
        ),
        "aucun_epoux_conjoint_2025": bool(
            profil.aucun_epoux_conjoint_2025
        ),
        "personne_charge_est_enfant": bool(
            profil.personne_charge_est_enfant
        ),
        "enfant_moins_18_fin_2025": bool(
            profil.enfant_moins_18_fin_2025
        ),
        "aucune_infirmite_enfant": bool(
            profil.aucune_infirmite_enfant
        ),
        "personne_charge_18_ans_ou_plus": bool(
            profil.personne_charge_18_ans_ou_plus
        ),
        "personne_charge_avec_infirmite": bool(
            profil.personne_charge_avec_infirmite
        ),
        "dependance_due_uniquement_a_infirmite": bool(
            profil.dependance_due_uniquement_a_infirmite
        ),
        "dependance_periode_considerable": bool(
            profil.dependance_periode_considerable
        ),
        "aidant_naturel_base_2687_inclus": bool(
            profil.aidant_naturel_base_2687_inclus
        ),
        "preuve_medicale_ou_t2201_confirmee": bool(
            profil.preuve_medicale_ou_t2201_confirmee
        ),
        "enfant_soutenu_2025": bool(
            profil.enfant_soutenu_2025
        ),
        "enfant_a_vecu_avec_contribuable": bool(
            profil.enfant_a_vecu_avec_contribuable
        ),
        "habitation_maintenue_par_contribuable": bool(
            profil.habitation_maintenue_par_contribuable
        ),
        "enfant_resident_canada_toute_annee": bool(
            profil.enfant_resident_canada_toute_annee
        ),
        "aucune_garde_partagee": bool(
            profil.aucune_garde_partagee
        ),
        "aucun_paiement_pension_alimentaire": bool(
            profil.aucun_paiement_pension_alimentaire
        ),
        "un_seul_montant_30400_par_menage": bool(
            profil.un_seul_montant_30400_par_menage
        ),
        "aucun_autre_reclamant_30400": bool(
            profil.aucun_autre_reclamant_30400
        ),
        "revenu_personne_charge_confirme": bool(
            profil.revenu_personne_charge_confirme
        ),
        "valide_par_comptable": bool(
            profil.valide_par_comptable
        ),
        "source_personne_charge": profil.source_personne_charge,
    }


def _personne_charge_admissible_federale_depuis_dict(
    valeur: Any,
) -> MontantPersonneChargeAdmissibleFederal2025:
    if valeur is None:
        return MontantPersonneChargeAdmissibleFederal2025()

    if not isinstance(valeur, dict):
        raise ValueError(
            "Le montant fédéral pour personne à charge "
            "admissible enregistré est invalide."
        )

    if type(valeur.get("enfant_infirmite_ligne30500", False)) is not bool:
        raise ValueError("Activation du profil 30400/30500 non booléenne.")
    if valeur.get("enfant_infirmite_ligne30500", False):
        if set(valeur) - {f.name for f in fields(MontantPersonneChargeAdmissibleFederal2025)}:
            raise ValueError("Clés du profil 30400/30500 inconnues.")
        for champ in fields(MontantPersonneChargeAdmissibleFederal2025):
            if champ.type is bool and champ.name in valeur and type(valeur[champ.name]) is not bool:
                raise ValueError("Confirmation JSON 30400/30500 non booléenne.")
            if champ.type is str and champ.name in valeur and not isinstance(valeur[champ.name], str):
                raise ValueError("Texte JSON 30400/30500 invalide.")
            if champ.type is Decimal and champ.name in valeur and (isinstance(valeur[champ.name], bool) or not isinstance(valeur[champ.name], (str, int))):
                raise ValueError("Montant JSON 30400/30500 invalide.")


    profil = MontantPersonneChargeAdmissibleFederal2025(
        enfant_infirmite_ligne30500=valeur.get("enfant_infirmite_ligne30500", False),
        reference_enfant=valeur.get("reference_enfant", ""),
        reclamer_montant=bool(
            valeur.get("reclamer_montant", False)
        ),
        revenu_net_contribuable_ligne_23600=_decimal_depuis_json(
            valeur.get(
                "revenu_net_contribuable_ligne_23600",
                "0",
            ),
            (
                "personne_charge_admissible_federale."
                "revenu_net_contribuable_ligne_23600"
            ),
        ),
        revenu_net_personne_charge_2025=_decimal_depuis_json(
            valeur.get(
                "revenu_net_personne_charge_2025",
                "0",
            ),
            (
                "personne_charge_admissible_federale."
                "revenu_net_personne_charge_2025"
            ),
        ),
        contribuable_resident_canada_toute_annee=bool(
            valeur.get(
                "contribuable_resident_canada_toute_annee",
                False,
            )
        ),
        aucun_epoux_conjoint_2025=bool(
            valeur.get("aucun_epoux_conjoint_2025", False)
        ),
        personne_charge_est_enfant=bool(
            valeur.get("personne_charge_est_enfant", False)
        ),
        enfant_moins_18_fin_2025=bool(
            valeur.get("enfant_moins_18_fin_2025", False)
        ),
        aucune_infirmite_enfant=bool(
            valeur.get("aucune_infirmite_enfant", False)
        ),
        personne_charge_18_ans_ou_plus=bool(
            valeur.get("personne_charge_18_ans_ou_plus", False)
        ),
        personne_charge_avec_infirmite=bool(
            valeur.get("personne_charge_avec_infirmite", False)
        ),
        dependance_due_uniquement_a_infirmite=bool(
            valeur.get(
                "dependance_due_uniquement_a_infirmite",
                False,
            )
        ),
        dependance_periode_considerable=bool(
            valeur.get(
                "dependance_periode_considerable",
                False,
            )
        ),
        aidant_naturel_base_2687_inclus=bool(
            valeur.get("aidant_naturel_base_2687_inclus", False)
        ),
        preuve_medicale_ou_t2201_confirmee=bool(
            valeur.get(
                "preuve_medicale_ou_t2201_confirmee",
                False,
            )
        ),
        enfant_soutenu_2025=bool(
            valeur.get("enfant_soutenu_2025", False)
        ),
        enfant_a_vecu_avec_contribuable=bool(
            valeur.get(
                "enfant_a_vecu_avec_contribuable",
                False,
            )
        ),
        habitation_maintenue_par_contribuable=bool(
            valeur.get(
                "habitation_maintenue_par_contribuable",
                False,
            )
        ),
        enfant_resident_canada_toute_annee=bool(
            valeur.get(
                "enfant_resident_canada_toute_annee",
                False,
            )
        ),
        aucune_garde_partagee=bool(
            valeur.get("aucune_garde_partagee", False)
        ),
        aucun_paiement_pension_alimentaire=bool(
            valeur.get(
                "aucun_paiement_pension_alimentaire",
                False,
            )
        ),
        un_seul_montant_30400_par_menage=bool(
            valeur.get(
                "un_seul_montant_30400_par_menage",
                False,
            )
        ),
        aucun_autre_reclamant_30400=bool(
            valeur.get(
                "aucun_autre_reclamant_30400",
                False,
            )
        ),
        revenu_personne_charge_confirme=bool(
            valeur.get(
                "revenu_personne_charge_confirme",
                False,
            )
        ),
        valide_par_comptable=bool(
            valeur.get("valide_par_comptable", False)
        ),
        source_personne_charge=str(
            valeur.get("source_personne_charge", "")
        ),
    )

    return valider_montant_personne_charge_admissible_federal_2025(
        profil
    )



def _accessibilite_domiciliaire_federale_vers_dict(
    profil: DepensesAccessibiliteDomiciliaireFederal2025 | None,
):
    if profil is None:
        profil = DepensesAccessibiliteDomiciliaireFederal2025()

    valider_depenses_accessibilite_domiciliaire_2025(profil)

    return {
        "reclamer_montant": bool(profil.reclamer_montant),
        "depenses_admissibles": _decimal_texte(profil.depenses_admissibles),
        "demande_pour_soi_meme": bool(profil.demande_pour_soi_meme),
        "age_65_plus_fin_annee": bool(profil.age_65_plus_fin_annee),
        "admissible_ciph": bool(profil.admissible_ciph),
        "logement_situe_au_canada": bool(profil.logement_situe_au_canada),
        "logement_propriete_du_contribuable": bool(
            profil.logement_propriete_du_contribuable
        ),
        "logement_normalement_habite_par_contribuable": bool(
            profil.logement_normalement_habite_par_contribuable
        ),
        "renovation_durable_et_integrante": bool(
            profil.renovation_durable_et_integrante
        ),
        "accessibilite_ou_reduction_risque_confirmee": bool(
            profil.accessibilite_ou_reduction_risque_confirmee
        ),
        "travaux_et_biens_2025_uniquement": bool(
            profil.travaux_et_biens_2025_uniquement
        ),
        "aucune_part_entreprise_ou_location": bool(
            profil.aucune_part_entreprise_ou_location
        ),
        "aucun_partage_de_la_demande": bool(
            profil.aucun_partage_de_la_demande
        ),
        "fournisseurs_lies_admissibles_confirme": bool(
            profil.fournisseurs_lies_admissibles_confirme
        ),
        "depenses_non_admissibles_exclues": bool(
            profil.depenses_non_admissibles_exclues
        ),
        "pieces_justificatives_conservees": bool(
            profil.pieces_justificatives_conservees
        ),
        "valide_par_comptable": bool(profil.valide_par_comptable),
        "source_renovation": profil.source_renovation,
        "partage_31285_confirme": profil.partage_31285_confirme,
        "montant_reclame_autres": _decimal_texte(profil.montant_reclame_autres),
        "autres_participants_admissibles_confirmes": profil.autres_participants_admissibles_confirmes,
        "logement_unique_2025_confirme": profil.logement_unique_2025_confirme,
        "reference_logement": profil.reference_logement,
        "source_partage": profil.source_partage,
    }


def _accessibilite_domiciliaire_federale_depuis_dict(
    valeur: Any,
) -> DepensesAccessibiliteDomiciliaireFederal2025:
    if valeur is None:
        return DepensesAccessibiliteDomiciliaireFederal2025()

    if not isinstance(valeur, dict):
        raise ValueError(
            "Les dépenses fédérales pour l'accessibilité domiciliaire "
            "ligne 31285 enregistrées sont invalides."
        )

    nouveaux = {"partage_31285_confirme", "montant_reclame_autres", "autres_participants_admissibles_confirmes", "logement_unique_2025_confirme", "reference_logement", "source_partage"}
    if nouveaux.intersection(valeur):
        defaults = DepensesAccessibiliteDomiciliaireFederal2025()
        if set(valeur) - {f.name for f in fields(defaults)}:
            raise ValueError("Clé inconnue dans le profil 31285.")
        for nom, v in valeur.items():
            defaut = getattr(defaults, nom)
            if isinstance(defaut, (bool, str)) and type(v) is not type(defaut):
                raise ValueError("Type JSON 31285 invalide : " + nom)
            if isinstance(defaut, Decimal) and type(v) not in (str, int):
                raise ValueError("Montant JSON 31285 invalide : " + nom)

    profil = DepensesAccessibiliteDomiciliaireFederal2025(
        partage_31285_confirme=valeur.get("partage_31285_confirme", False),
        montant_reclame_autres=_decimal_depuis_json(valeur.get("montant_reclame_autres", "0"), "Autres demandes 31285"),
        autres_participants_admissibles_confirmes=valeur.get("autres_participants_admissibles_confirmes", False),
        logement_unique_2025_confirme=valeur.get("logement_unique_2025_confirme", False),
        reference_logement=valeur.get("reference_logement", ""), source_partage=valeur.get("source_partage", ""),
        reclamer_montant=bool(valeur.get("reclamer_montant", False)),
        depenses_admissibles=_decimal_depuis_json(
            valeur.get("depenses_admissibles", "0"),
            "accessibilite_domiciliaire_federale.depenses_admissibles",
        ),
        demande_pour_soi_meme=bool(
            valeur.get("demande_pour_soi_meme", False)
        ),
        age_65_plus_fin_annee=bool(
            valeur.get("age_65_plus_fin_annee", False)
        ),
        admissible_ciph=bool(valeur.get("admissible_ciph", False)),
        logement_situe_au_canada=bool(
            valeur.get("logement_situe_au_canada", False)
        ),
        logement_propriete_du_contribuable=bool(
            valeur.get("logement_propriete_du_contribuable", False)
        ),
        logement_normalement_habite_par_contribuable=bool(
            valeur.get(
                "logement_normalement_habite_par_contribuable",
                False,
            )
        ),
        renovation_durable_et_integrante=bool(
            valeur.get("renovation_durable_et_integrante", False)
        ),
        accessibilite_ou_reduction_risque_confirmee=bool(
            valeur.get(
                "accessibilite_ou_reduction_risque_confirmee",
                False,
            )
        ),
        travaux_et_biens_2025_uniquement=bool(
            valeur.get("travaux_et_biens_2025_uniquement", False)
        ),
        aucune_part_entreprise_ou_location=bool(
            valeur.get("aucune_part_entreprise_ou_location", False)
        ),
        aucun_partage_de_la_demande=bool(
            valeur.get("aucun_partage_de_la_demande", False)
        ),
        fournisseurs_lies_admissibles_confirme=bool(
            valeur.get("fournisseurs_lies_admissibles_confirme", False)
        ),
        depenses_non_admissibles_exclues=bool(
            valeur.get("depenses_non_admissibles_exclues", False)
        ),
        pieces_justificatives_conservees=bool(
            valeur.get("pieces_justificatives_conservees", False)
        ),
        valide_par_comptable=bool(
            valeur.get("valide_par_comptable", False)
        ),
        source_renovation=str(valeur.get("source_renovation", "")),
    )

    return valider_depenses_accessibilite_domiciliaire_2025(profil)


def _achat_habitation_federal_vers_dict(
    profil: MontantAchatHabitationFederal2025 | None,
):
    if profil is None:
        profil = MontantAchatHabitationFederal2025()

    valider_montant_achat_habitation_2025(profil)

    return {
        "reclamer_montant": bool(profil.reclamer_montant),
        "montant_reclame": _decimal_texte(
            profil.montant_reclame
        ),
        "acquisition_en_2025": bool(
            profil.acquisition_en_2025
        ),
        "habitation_admissible": bool(
            profil.habitation_admissible
        ),
        "habitation_situee_au_canada": bool(
            profil.habitation_situee_au_canada
        ),
        "habitation_enregistree_nom_contribuable_ou_conjoint": bool(
            profil.habitation_enregistree_nom_contribuable_ou_conjoint
        ),
        "premier_acheteur_confirme": bool(
            profil.premier_acheteur_confirme
        ),
        "aucune_habitation_possedee_habitee_annee_achat_ou_4_precedentes": bool(
            profil
            .aucune_habitation_possedee_habitee_annee_achat_ou_4_precedentes
        ),
        "intention_residence_principale_dans_un_an": bool(
            profil.intention_residence_principale_dans_un_an
        ),
        "aucun_partage_du_montant": bool(
            profil.aucun_partage_du_montant
        ),
        "aucune_exception_handicap_utilisee": bool(
            profil.aucune_exception_handicap_utilisee
        ),
        "pieces_justificatives_conservees": bool(
            profil.pieces_justificatives_conservees
        ),
        "valide_par_comptable": bool(
            profil.valide_par_comptable
        ),
        "source_habitation": profil.source_habitation,
        "partage_31270_confirme": profil.partage_31270_confirme,
        "montant_attribue_autres_acquereurs": _decimal_texte(profil.montant_attribue_autres_acquereurs),
        "autres_acquereurs_admissibles_confirmes": profil.autres_acquereurs_admissibles_confirmes,
        "reference_habitation": profil.reference_habitation,
        "source_partage": profil.source_partage,
    }


def _achat_habitation_federal_depuis_dict(
    valeur: Any,
) -> MontantAchatHabitationFederal2025:
    if valeur is None:
        return MontantAchatHabitationFederal2025()

    if not isinstance(valeur, dict):
        raise ValueError(
            "Le montant fédéral pour l'achat d'une habitation "
            "ligne 31270 enregistré est invalide."
        )

    nouveaux = {"partage_31270_confirme", "montant_attribue_autres_acquereurs", "autres_acquereurs_admissibles_confirmes", "reference_habitation", "source_partage"}
    if nouveaux.intersection(valeur):
        defaults = MontantAchatHabitationFederal2025()
        if set(valeur) - {f.name for f in fields(defaults)}:
            raise ValueError("Clé inconnue dans le profil 31270.")
        for nom, v in valeur.items():
            defaut = getattr(defaults, nom)
            if isinstance(defaut, (bool, str)) and type(v) is not type(defaut):
                raise ValueError("Type JSON 31270 invalide : " + nom)
            if isinstance(defaut, Decimal) and type(v) not in (str, int):
                raise ValueError("Montant JSON 31270 invalide : " + nom)

    profil = MontantAchatHabitationFederal2025(
        partage_31270_confirme=valeur.get("partage_31270_confirme", False),
        montant_attribue_autres_acquereurs=_decimal_depuis_json(valeur.get("montant_attribue_autres_acquereurs", "0"), "Parts autres acquéreurs 31270"),
        autres_acquereurs_admissibles_confirmes=valeur.get("autres_acquereurs_admissibles_confirmes", False),
        reference_habitation=valeur.get("reference_habitation", ""), source_partage=valeur.get("source_partage", ""),
        reclamer_montant=bool(
            valeur.get("reclamer_montant", False)
        ),
        montant_reclame=_decimal_depuis_json(
            valeur.get("montant_reclame", "0"),
            "achat_habitation_federal.montant_reclame",
        ),
        acquisition_en_2025=bool(
            valeur.get("acquisition_en_2025", False)
        ),
        habitation_admissible=bool(
            valeur.get("habitation_admissible", False)
        ),
        habitation_situee_au_canada=bool(
            valeur.get("habitation_situee_au_canada", False)
        ),
        habitation_enregistree_nom_contribuable_ou_conjoint=bool(
            valeur.get(
                "habitation_enregistree_nom_contribuable_ou_conjoint",
                False,
            )
        ),
        premier_acheteur_confirme=bool(
            valeur.get("premier_acheteur_confirme", False)
        ),
        aucune_habitation_possedee_habitee_annee_achat_ou_4_precedentes=bool(
            valeur.get(
                "aucune_habitation_possedee_habitee_annee_achat_ou_4_precedentes",
                False,
            )
        ),
        intention_residence_principale_dans_un_an=bool(
            valeur.get(
                "intention_residence_principale_dans_un_an",
                False,
            )
        ),
        aucun_partage_du_montant=bool(
            valeur.get("aucun_partage_du_montant", False)
        ),
        aucune_exception_handicap_utilisee=bool(
            valeur.get(
                "aucune_exception_handicap_utilisee",
                False,
            )
        ),
        pieces_justificatives_conservees=bool(
            valeur.get(
                "pieces_justificatives_conservees",
                False,
            )
        ),
        valide_par_comptable=bool(
            valeur.get("valide_par_comptable", False)
        ),
        source_habitation=str(
            valeur.get("source_habitation", "")
        ),
    )

    return valider_montant_achat_habitation_2025(profil)


def _aidant_autre_personne_charge_federal_vers_dict(
    profil: AidantNaturelAutrePersonneChargeFederal2025 | None,
):
    if profil is None:
        profil = AidantNaturelAutrePersonneChargeFederal2025()

    valider_aidant_naturel_30450_2025(profil)

    return {
        "reclamer_montant": bool(profil.reclamer_montant),
        "lien_personne": profil.lien_personne,
        "revenu_net_personne_ligne_23600": _decimal_texte(
            profil.revenu_net_personne_ligne_23600
        ),
        "age_18_ans_ou_plus": bool(
            profil.age_18_ans_ou_plus
        ),
        "personne_soutenue_en_2025": bool(
            profil.personne_soutenue_en_2025
        ),
        "infirmite_physique_ou_mentale": bool(
            profil.infirmite_physique_ou_mentale
        ),
        "dependance_due_uniquement_a_infirmite": bool(
            profil.dependance_due_uniquement_a_infirmite
        ),
        "dependance_periode_considerable": bool(
            profil.dependance_periode_considerable
        ),
        "resident_canada_au_moins_un_moment_2025": bool(
            profil.resident_canada_au_moins_un_moment_2025
        ),
        "aucune_reclamation_ligne_30300_30400_pour_personne": bool(
            profil.aucune_reclamation_ligne_30300_30400_pour_personne
        ),
        "aucun_paiement_pension_alimentaire_pour_personne": bool(
            profil.aucun_paiement_pension_alimentaire_pour_personne
        ),
        "aucun_partage_reclamation_30450": bool(
            profil.aucun_partage_reclamation_30450
        ),
        "preuve_medicale_ou_t2201_confirmee": bool(
            profil.preuve_medicale_ou_t2201_confirmee
        ),
        "valide_par_comptable": bool(
            profil.valide_par_comptable
        ),
        "source_personne": profil.source_personne,
        "partage_30450_confirme": profil.partage_30450_confirme,
        "montant_attribue_autres_soutiens": _decimal_texte(profil.montant_attribue_autres_soutiens),
        "reference_personne": profil.reference_personne,
        "source_partage": profil.source_partage,
        "identites_distinctes_confirmees": profil.identites_distinctes_confirmees,
        "personnes_detaillees": [{"reference": p.reference, "nom": p.nom, "naissance": p.naissance,
            "profil": _aidant_autre_personne_charge_federal_vers_dict(p.profil)} for p in profil.personnes_detaillees],
    }


def _aidant_autre_personne_charge_federal_depuis_dict(
    valeur: Any, *, individuel: bool = False,
) -> AidantNaturelAutrePersonneChargeFederal2025:
    if valeur is None:
        return AidantNaturelAutrePersonneChargeFederal2025()

    if not isinstance(valeur, dict):
        raise ValueError(
            "Le montant fédéral pour aidant naturel ligne 30450 "
            "enregistré est invalide."
        )

    nouveaux = {"partage_30450_confirme", "montant_attribue_autres_soutiens", "reference_personne", "source_partage", "personnes_detaillees", "identites_distinctes_confirmees"}
    if individuel or nouveaux.intersection(valeur):
        defaults = AidantNaturelAutrePersonneChargeFederal2025()
        connus = {c.name for c in fields(defaults)}
        if set(valeur) - connus:
            raise ValueError("Clé inconnue dans le profil 30450.")
        for nom, v in valeur.items():
            defaut = getattr(defaults, nom)
            if isinstance(defaut, bool) and type(v) is not bool:
                raise ValueError(f"Confirmation 30450 invalide : {nom}.")
            if isinstance(defaut, str) and type(v) is not str:
                raise ValueError(f"Texte 30450 invalide : {nom}.")
            if isinstance(defaut, Decimal) and type(v) not in (str, int):
                raise ValueError(f"Montant 30450 invalide : {nom}.")

    liste = valeur.get("personnes_detaillees", [])
    if type(liste) is not list or (individuel and liste):
        raise ValueError("Liste détaillée 30450 invalide ou imbriquée.")
    personnes = []
    for personne in liste:
        if (type(personne) is not dict or set(personne) != {"reference", "nom", "naissance", "profil"}
                or type(personne["profil"]) is not dict):
            raise ValueError("Fiche de personne 30450 invalide.")
        personnes.append(PersonneAidant30450(
            reference=personne["reference"], nom=personne["nom"], naissance=personne["naissance"],
            profil=_aidant_autre_personne_charge_federal_depuis_dict(personne["profil"], individuel=True)))

    profil = AidantNaturelAutrePersonneChargeFederal2025(
        personnes_detaillees=tuple(personnes),
        identites_distinctes_confirmees=valeur.get("identites_distinctes_confirmees", False),
        partage_30450_confirme=valeur.get("partage_30450_confirme", False),
        montant_attribue_autres_soutiens=_decimal_depuis_json(
            valeur.get("montant_attribue_autres_soutiens", "0"), "partage 30450"),
        reference_personne=valeur.get("reference_personne", ""),
        source_partage=valeur.get("source_partage", ""),
        reclamer_montant=bool(
            valeur.get("reclamer_montant", False)
        ),
        lien_personne=str(
            valeur.get("lien_personne", "")
        ),
        revenu_net_personne_ligne_23600=_decimal_depuis_json(
            valeur.get("revenu_net_personne_ligne_23600", "0"),
            (
                "aidant_autre_personne_charge_federal."
                "revenu_net_personne_ligne_23600"
            ),
        ),
        age_18_ans_ou_plus=bool(
            valeur.get("age_18_ans_ou_plus", False)
        ),
        personne_soutenue_en_2025=bool(
            valeur.get("personne_soutenue_en_2025", False)
        ),
        infirmite_physique_ou_mentale=bool(
            valeur.get("infirmite_physique_ou_mentale", False)
        ),
        dependance_due_uniquement_a_infirmite=bool(
            valeur.get(
                "dependance_due_uniquement_a_infirmite",
                False,
            )
        ),
        dependance_periode_considerable=bool(
            valeur.get(
                "dependance_periode_considerable",
                False,
            )
        ),
        resident_canada_au_moins_un_moment_2025=bool(
            valeur.get(
                "resident_canada_au_moins_un_moment_2025",
                False,
            )
        ),
        aucune_reclamation_ligne_30300_30400_pour_personne=bool(
            valeur.get(
                "aucune_reclamation_ligne_30300_30400_pour_personne",
                False,
            )
        ),
        aucun_paiement_pension_alimentaire_pour_personne=bool(
            valeur.get(
                "aucun_paiement_pension_alimentaire_pour_personne",
                False,
            )
        ),
        aucun_partage_reclamation_30450=bool(
            valeur.get(
                "aucun_partage_reclamation_30450",
                False,
            )
        ),
        preuve_medicale_ou_t2201_confirmee=bool(
            valeur.get(
                "preuve_medicale_ou_t2201_confirmee",
                False,
            )
        ),
        valide_par_comptable=bool(
            valeur.get("valide_par_comptable", False)
        ),
        source_personne=str(
            valeur.get("source_personne", "")
        ),
    )

    return valider_aidant_naturel_30450_2025(profil)


def _aidant_conjoint_personne_charge_federal_vers_dict(
    profil: AidantNaturelConjointOuPersonneChargeFederal2025 | None,
):
    if profil is None:
        profil = AidantNaturelConjointOuPersonneChargeFederal2025()

    valider_aidant_naturel_30425_2025(profil)

    return {
        "reclamer_montant": bool(profil.reclamer_montant),
        "type_personne": profil.type_personne,
        "revenu_net_personne_ligne_23600": _decimal_texte(
            profil.revenu_net_personne_ligne_23600
        ),
        "montant_reclame_ligne_30300_ou_30400": _decimal_texte(
            profil.montant_reclame_ligne_30300_ou_30400
        ),
        "personne_soutenue_en_2025": bool(
            profil.personne_soutenue_en_2025
        ),
        "personne_charge_18_ans_ou_plus_si_applicable": bool(
            profil.personne_charge_18_ans_ou_plus_si_applicable
        ),
        "infirmite_physique_ou_mentale": bool(
            profil.infirmite_physique_ou_mentale
        ),
        "dependance_due_uniquement_a_infirmite": bool(
            profil.dependance_due_uniquement_a_infirmite
        ),
        "dependance_periode_considerable": bool(
            profil.dependance_periode_considerable
        ),
        "montant_base_2687_inclus": bool(
            profil.montant_base_2687_inclus
        ),
        "un_seul_reclamant_30425": bool(
            profil.un_seul_reclamant_30425
        ),
        "aucune_reclamation_partagee": bool(
            profil.aucune_reclamation_partagee
        ),
        "preuve_medicale_ou_t2201_confirmee": bool(
            profil.preuve_medicale_ou_t2201_confirmee
        ),
        "valide_par_comptable": bool(
            profil.valide_par_comptable
        ),
        "source_personne": profil.source_personne,
    }


def _aidant_conjoint_personne_charge_federal_depuis_dict(
    valeur: Any,
) -> AidantNaturelConjointOuPersonneChargeFederal2025:
    if valeur is None:
        return AidantNaturelConjointOuPersonneChargeFederal2025()

    if not isinstance(valeur, dict):
        raise ValueError(
            "Le montant fédéral pour aidant naturel ligne 30425 "
            "enregistré est invalide."
        )

    profil = AidantNaturelConjointOuPersonneChargeFederal2025(
        reclamer_montant=bool(
            valeur.get("reclamer_montant", False)
        ),
        type_personne=str(
            valeur.get("type_personne", "")
        ),
        revenu_net_personne_ligne_23600=_decimal_depuis_json(
            valeur.get("revenu_net_personne_ligne_23600", "0"),
            (
                "aidant_conjoint_personne_charge_federal."
                "revenu_net_personne_ligne_23600"
            ),
        ),
        montant_reclame_ligne_30300_ou_30400=_decimal_depuis_json(
            valeur.get(
                "montant_reclame_ligne_30300_ou_30400",
                "0",
            ),
            (
                "aidant_conjoint_personne_charge_federal."
                "montant_reclame_ligne_30300_ou_30400"
            ),
        ),
        personne_soutenue_en_2025=bool(
            valeur.get("personne_soutenue_en_2025", False)
        ),
        personne_charge_18_ans_ou_plus_si_applicable=bool(
            valeur.get(
                "personne_charge_18_ans_ou_plus_si_applicable",
                False,
            )
        ),
        infirmite_physique_ou_mentale=bool(
            valeur.get("infirmite_physique_ou_mentale", False)
        ),
        dependance_due_uniquement_a_infirmite=bool(
            valeur.get(
                "dependance_due_uniquement_a_infirmite",
                False,
            )
        ),
        dependance_periode_considerable=bool(
            valeur.get(
                "dependance_periode_considerable",
                False,
            )
        ),
        montant_base_2687_inclus=bool(
            valeur.get("montant_base_2687_inclus", False)
        ),
        un_seul_reclamant_30425=bool(
            valeur.get("un_seul_reclamant_30425", False)
        ),
        aucune_reclamation_partagee=bool(
            valeur.get("aucune_reclamation_partagee", False)
        ),
        preuve_medicale_ou_t2201_confirmee=bool(
            valeur.get(
                "preuve_medicale_ou_t2201_confirmee",
                False,
            )
        ),
        valide_par_comptable=bool(
            valeur.get("valide_par_comptable", False)
        ),
        source_personne=str(
            valeur.get("source_personne", "")
        ),
    )

    return valider_aidant_naturel_30425_2025(profil)


def _aidant_enfant_federal_vers_dict(
    profil: AidantNaturelEnfantMoins18Federal2025 | None,
):
    if profil is None:
        profil = AidantNaturelEnfantMoins18Federal2025()

    valider_aidant_naturel_enfant_moins18_federal_2025(profil)

    return {
        "enfant_reclame_30400": profil.enfant_reclame_30400,
        "reference_enfant": profil.reference_enfant,
        "identites_distinctes_confirmees": profil.identites_distinctes_confirmees,
        "enfants_detailles": [{"reference": e.reference, "nom": e.nom, "naissance": e.naissance,
            "profil": _aidant_enfant_federal_vers_dict(e.profil)} for e in profil.enfants_detailles],
        "reclamer_montant": bool(profil.reclamer_montant),
        "enfant_biologique_ou_adopte": bool(
            profil.enfant_biologique_ou_adopte
        ),
        "enfant_moins_18_fin_2025": bool(
            profil.enfant_moins_18_fin_2025
        ),
        "infirmite_physique_ou_mentale": bool(
            profil.infirmite_physique_ou_mentale
        ),
        "dependance_longue_continue_duree_indeterminee": bool(
            profil.dependance_longue_continue_duree_indeterminee
        ),
        "besoin_aide_beaucoup_plus_que_meme_age": bool(
            profil.besoin_aide_beaucoup_plus_que_meme_age
        ),
        "enfant_avec_deux_parents_toute_annee": bool(
            profil.enfant_avec_deux_parents_toute_annee
        ),
        "aucune_garde_partagee": bool(
            profil.aucune_garde_partagee
        ),
        "aucune_pension_alimentaire": bool(
            profil.aucune_pension_alimentaire
        ),
        "aucun_autre_reclamant_30500": bool(
            profil.aucun_autre_reclamant_30500
        ),
        "aucun_transfert_conjoint_32600": bool(
            profil.aucun_transfert_conjoint_32600
        ),
        "preuve_medicale_ou_t2201_confirmee": bool(
            profil.preuve_medicale_ou_t2201_confirmee
        ),
        "valide_par_comptable": bool(
            profil.valide_par_comptable
        ),
        "source_enfant": profil.source_enfant,
    }


def _aidant_enfant_federal_depuis_dict(
    valeur: Any, *, individuel: bool = False,
) -> AidantNaturelEnfantMoins18Federal2025:
    if valeur is None:
        return AidantNaturelEnfantMoins18Federal2025()

    if not isinstance(valeur, dict):
        raise ValueError(
            "Le montant fédéral pour aidant naturel enfant "
            "enregistré est invalide."
        )

    if type(valeur.get("enfant_reclame_30400", False)) is not bool:
        raise ValueError("Activation du profil 30400/30500 non booléenne.")
    if individuel or "enfants_detailles" in valeur or "identites_distinctes_confirmees" in valeur or valeur.get("enfant_reclame_30400", False):
        if set(valeur) - {f.name for f in fields(AidantNaturelEnfantMoins18Federal2025)}:
            raise ValueError("Clés du profil 30400/30500 inconnues.")
        for champ in fields(AidantNaturelEnfantMoins18Federal2025):
            if champ.type is bool and champ.name in valeur and type(valeur[champ.name]) is not bool:
                raise ValueError("Confirmation JSON 30400/30500 non booléenne.")
            if champ.type is str and champ.name in valeur and not isinstance(valeur[champ.name], str):
                raise ValueError("Texte JSON 30400/30500 invalide.")
            if champ.type is Decimal and champ.name in valeur and (isinstance(valeur[champ.name], bool) or not isinstance(valeur[champ.name], (str, int))):
                raise ValueError("Montant JSON 30400/30500 invalide.")


    liste = valeur.get("enfants_detailles", [])
    if type(liste) is not list or (individuel and liste):
        raise ValueError("Liste détaillée 30500 invalide ou imbriquée.")
    enfants = []
    for enfant in liste:
        if (type(enfant) is not dict or set(enfant) != {"reference", "nom", "naissance", "profil"}
                or type(enfant["profil"]) is not dict):
            raise ValueError("Fiche enfant 30500 invalide.")
        enfants.append(EnfantAidant30500(reference=enfant["reference"], nom=enfant["nom"], naissance=enfant["naissance"],
            profil=_aidant_enfant_federal_depuis_dict(enfant["profil"], individuel=True)))

    profil = AidantNaturelEnfantMoins18Federal2025(
        enfants_detailles=tuple(enfants),
        identites_distinctes_confirmees=valeur.get("identites_distinctes_confirmees", False),
        enfant_reclame_30400=valeur.get("enfant_reclame_30400", False),
        reference_enfant=valeur.get("reference_enfant", ""),
        reclamer_montant=bool(
            valeur.get("reclamer_montant", False)
        ),
        enfant_biologique_ou_adopte=bool(
            valeur.get("enfant_biologique_ou_adopte", False)
        ),
        enfant_moins_18_fin_2025=bool(
            valeur.get("enfant_moins_18_fin_2025", False)
        ),
        infirmite_physique_ou_mentale=bool(
            valeur.get("infirmite_physique_ou_mentale", False)
        ),
        dependance_longue_continue_duree_indeterminee=bool(
            valeur.get(
                "dependance_longue_continue_duree_indeterminee",
                False,
            )
        ),
        besoin_aide_beaucoup_plus_que_meme_age=bool(
            valeur.get(
                "besoin_aide_beaucoup_plus_que_meme_age",
                False,
            )
        ),
        enfant_avec_deux_parents_toute_annee=bool(
            valeur.get(
                "enfant_avec_deux_parents_toute_annee",
                False,
            )
        ),
        aucune_garde_partagee=bool(
            valeur.get("aucune_garde_partagee", False)
        ),
        aucune_pension_alimentaire=bool(
            valeur.get("aucune_pension_alimentaire", False)
        ),
        aucun_autre_reclamant_30500=bool(
            valeur.get("aucun_autre_reclamant_30500", False)
        ),
        aucun_transfert_conjoint_32600=bool(
            valeur.get("aucun_transfert_conjoint_32600", False)
        ),
        preuve_medicale_ou_t2201_confirmee=bool(
            valeur.get(
                "preuve_medicale_ou_t2201_confirmee",
                False,
            )
        ),
        valide_par_comptable=bool(
            valeur.get("valide_par_comptable", False)
        ),
        source_enfant=str(
            valeur.get("source_enfant", "")
        ),
    )

    return valider_aidant_naturel_enfant_moins18_federal_2025(
        profil
    )

def _montants_age_retraite_vers_dict(
    profil: MontantsAgeRetraite2025 | None,
):
    if profil is None:
        profil = MontantsAgeRetraite2025()

    valider_montants_age_retraite_2025(profil)

    return {
        "combinaison_annexe_b_confirmee": profil.combinaison_annexe_b_confirmee,
        "reclamer_age": bool(profil.reclamer_age),
        "ne_avant_1_janvier_1961": bool(
            profil.ne_avant_1_janvier_1961
        ),
        "reclamer_revenus_retraite": bool(
            profil.reclamer_revenus_retraite
        ),
        "revenu_ligne_122": _decimal_texte(
            profil.revenu_ligne_122
        ),
        "revenu_ligne_123": _decimal_texte(
            profil.revenu_ligne_123
        ),
        "deduction_ligne_250_point_4": _decimal_texte(
            profil.deduction_ligne_250_point_4
        ),
        "deduction_ligne_250_point_6": _decimal_texte(
            profil.deduction_ligne_250_point_6
        ),
        "deduction_ligne_293": _decimal_texte(
            profil.deduction_ligne_293
        ),
        "deduction_ligne_297_points_9_12": _decimal_texte(
            profil.deduction_ligne_297_points_9_12
        ),
        "transfert_revenus_retraite_ligne_245": _decimal_texte(
            profil.transfert_revenus_retraite_ligne_245
        ),
        "revenu_familial_net": _decimal_texte(
            profil.revenu_familial_net
        ),
        "aucun_conjoint_31_decembre_2025": bool(
            profil.aucun_conjoint_31_decembre_2025
        ),
        "resident_quebec_canada_toute_annee": bool(
            profil.resident_quebec_canada_toute_annee
        ),
        "aucun_montant_personne_vivant_seule": bool(
            profil.aucun_montant_personne_vivant_seule
        ),
        "revenus_retraite_admissibles_confirmes": bool(
            profil.revenus_retraite_admissibles_confirmes
        ),
        "revenus_non_admissibles_exclus": bool(
            profil.revenus_non_admissibles_exclus
        ),
        "valide_par_comptable": bool(
            profil.valide_par_comptable
        ),
        "source_age": profil.source_age,
        "source_retraite": profil.source_retraite,
    }


def _montants_age_retraite_depuis_dict(
    valeur: Any,
) -> MontantsAgeRetraite2025:
    if valeur is None:
        return MontantsAgeRetraite2025()

    if not isinstance(valeur, dict):
        raise ValueError(
            "Le profil âge/retraite enregistré est invalide."
        )

    _verifier_types_annexe_b_6a(valeur, MontantsAgeRetraite2025())
    profil = MontantsAgeRetraite2025(
        combinaison_annexe_b_confirmee=valeur.get("combinaison_annexe_b_confirmee", False),
        reclamer_age=bool(
            valeur.get("reclamer_age", False)
        ),
        ne_avant_1_janvier_1961=bool(
            valeur.get("ne_avant_1_janvier_1961", False)
        ),
        reclamer_revenus_retraite=bool(
            valeur.get("reclamer_revenus_retraite", False)
        ),
        revenu_ligne_122=_decimal_depuis_json(
            valeur.get("revenu_ligne_122", "0"),
            "montants_age_retraite.revenu_ligne_122",
        ),
        revenu_ligne_123=_decimal_depuis_json(
            valeur.get("revenu_ligne_123", "0"),
            "montants_age_retraite.revenu_ligne_123",
        ),
        deduction_ligne_250_point_4=_decimal_depuis_json(
            valeur.get("deduction_ligne_250_point_4", "0"),
            "montants_age_retraite.deduction_ligne_250_point_4",
        ),
        deduction_ligne_250_point_6=_decimal_depuis_json(
            valeur.get("deduction_ligne_250_point_6", "0"),
            "montants_age_retraite.deduction_ligne_250_point_6",
        ),
        deduction_ligne_293=_decimal_depuis_json(
            valeur.get("deduction_ligne_293", "0"),
            "montants_age_retraite.deduction_ligne_293",
        ),
        deduction_ligne_297_points_9_12=_decimal_depuis_json(
            valeur.get("deduction_ligne_297_points_9_12", "0"),
            "montants_age_retraite.deduction_ligne_297_points_9_12",
        ),
        transfert_revenus_retraite_ligne_245=_decimal_depuis_json(
            valeur.get(
                "transfert_revenus_retraite_ligne_245",
                "0",
            ),
            (
                "montants_age_retraite."
                "transfert_revenus_retraite_ligne_245"
            ),
        ),
        revenu_familial_net=_decimal_depuis_json(
            valeur.get("revenu_familial_net", "0"),
            "montants_age_retraite.revenu_familial_net",
        ),
        aucun_conjoint_31_decembre_2025=bool(
            valeur.get(
                "aucun_conjoint_31_decembre_2025",
                False,
            )
        ),
        resident_quebec_canada_toute_annee=bool(
            valeur.get(
                "resident_quebec_canada_toute_annee",
                False,
            )
        ),
        aucun_montant_personne_vivant_seule=bool(
            valeur.get(
                "aucun_montant_personne_vivant_seule",
                False,
            )
        ),
        revenus_retraite_admissibles_confirmes=bool(
            valeur.get(
                "revenus_retraite_admissibles_confirmes",
                False,
            )
        ),
        revenus_non_admissibles_exclus=bool(
            valeur.get(
                "revenus_non_admissibles_exclus",
                False,
            )
        ),
        valide_par_comptable=bool(
            valeur.get("valide_par_comptable", False)
        ),
        source_age=str(
            valeur.get("source_age", "")
        ),
        source_retraite=str(
            valeur.get("source_retraite", "")
        ),
    )
    return valider_montants_age_retraite_2025(profil)


def _rpa_depuis_dict(valeur):
    if not isinstance(valeur, dict):
        raise ValueError("Cotisations RPA enregistrées invalides.")
    champs = CotisationsRpa2025.__dataclass_fields__
    if set(valeur) != set(champs):
        raise ValueError("Champs RPA enregistrés incomplets ou inconnus.")
    valeurs = dict(valeur)
    for nom in ("montant_federal", "montant_quebec"):
        valeurs[nom] = _decimal_depuis_json(valeurs[nom], "cotisations_rpa." + nom)
    return valider_cotisations_rpa_2025(CotisationsRpa2025(**valeurs))


def _scolarite_recue_vers_dict(profil):
    valider_transferts_scolarite_recus_2025(profil)
    return {"designations": [dict(asdict(d), montant_certificat=format(d.montant_certificat, ".2f"))
                             for d in profil.designations]}


def _scolarite_recue_depuis_dict(valeur):
    if valeur is None:
        return TransfertsScolariteRecus2025()
    if not isinstance(valeur, dict) or set(valeur) - {"designations"}:
        raise ValueError("Profil scolarité reçue ou clés inconnues invalides.")
    liste = valeur.get("designations", [])
    if not isinstance(liste, list):
        raise ValueError("Liste des désignations invalide.")
    designations = []
    for entree in liste:
        if not isinstance(entree, dict) or set(entree) - set(DesignationScolariteRecue2025.__dataclass_fields__):
            raise ValueError("Désignation ou clés inconnues invalides.")
        v = dict(entree)
        v["montant_certificat"] = _decimal_depuis_json(v.get("montant_certificat", "0"), "Désignation reçue")
        designations.append(DesignationScolariteRecue2025(**v))
    return valider_transferts_scolarite_recus_2025(TransfertsScolariteRecus2025(tuple(designations)))


def _allocation_travailleurs_vers_dict(profil):
    valeurs = asdict(valider_allocation_travailleurs_2025(profil))
    for nom in ("avances_rc210_case10", "avances_rc210_case11"):
        valeurs[nom] = format(valeurs[nom], ".2f")
    valeurs["famille"] = famille_act_vers_dict(profil.famille)
    return valeurs


def _allocation_travailleurs_depuis_dict(valeur):
    if valeur is None:
        return AllocationTravailleurs2025()
    if not isinstance(valeur, dict) or set(valeur) - set(AllocationTravailleurs2025.__dataclass_fields__):
        raise ValueError("Profil ACT ou clés inconnues invalides.")
    valeurs = dict(valeur)
    valeurs["famille"] = famille_act_depuis_dict(valeurs.get("famille"))
    for nom in ("avances_rc210_case10", "avances_rc210_case11"):
        valeurs[nom] = _decimal_depuis_json(valeurs.get(nom, "0"), "allocation_travailleurs." + nom)
    return valider_allocation_travailleurs_2025(AllocationTravailleurs2025(**valeurs))


def _interets_pret_etudiant_vers_dict(profil):
    profil = valider_interets_pret_etudiant_2025(profil)
    valeurs = asdict(profil)
    for nom in ("interets_payes_2025", "montant_reclame_31900"):
        valeurs[nom] = _decimal_texte(valeurs[nom])
    valeurs["reports"] = [{"annee": a, "montant": _decimal_texte(m)} for a, m in profil.reports]
    return valeurs


def _interets_pret_etudiant_depuis_dict(valeur):
    if valeur is None:
        return InteretsPretEtudiant2025()
    if not isinstance(valeur, dict) or set(valeur) - set(InteretsPretEtudiant2025.__dataclass_fields__):
        raise ValueError("Champs inconnus ou profil intérêts étudiants invalide.")
    valeurs = dict(valeur)
    for nom in ("interets_payes_2025", "montant_reclame_31900"):
        valeurs[nom] = _decimal_depuis_json(valeurs.get(nom, "0"), "interets_pret_etudiant." + nom)
    reports = valeurs.get("reports", [])
    if not isinstance(reports, list):
        raise ValueError("Les reports étudiants doivent être une liste annuelle.")
    lignes = []
    for report in reports:
        if not isinstance(report, dict) or set(report) != {"annee", "montant"}:
            raise ValueError("Champs de report étudiant invalides.")
        lignes.append((report["annee"], _decimal_depuis_json(report["montant"], "report étudiant")))
    valeurs["reports"] = tuple(lignes)
    return valider_interets_pret_etudiant_2025(InteretsPretEtudiant2025(**valeurs))


def _benevoles_vers_dict(p):
    from dataclasses import asdict
    brut = asdict(p)
    brut["activites"] = [dict(asdict(a), heures=format(a.heures, ".2f")) for a in p.activites]
    return brut


def _benevoles_depuis_dict(valeur, dossier):
    from dataclasses import fields
    if valeur is None:
        p = Benevoles2025()
    else:
        if not isinstance(valeur, dict) or set(valeur) - {f.name for f in fields(Benevoles2025)}:
            raise ValueError("Champs du profil bénévoles invalides.")
        brut = dict(valeur)
        activites = brut.get("activites", [])
        if not isinstance(activites, list):
            raise ValueError("Les activités bénévoles doivent être une liste.")
        lignes = []
        for a in activites:
            if not isinstance(a, dict) or set(a) - {f.name for f in fields(ActiviteBenevole2025)}:
                raise ValueError("Champs de l'activité bénévole invalides.")
            v = dict(a)
            v["heures"] = _decimal_depuis_json(v.get("heures", "0"), "heures bénévoles")
            lignes.append(ActiviteBenevole2025(**v))
        brut["activites"] = tuple(lignes)
        p = Benevoles2025(**brut)
    calculer_benevoles_2025(p, dossier)
    return p


def _transfert_conjoint_depuis_dict(valeur, beneficiaire):
    from dataclasses import fields
    if valeur is None:
        return TransfertConjointFederal2025()
    if not isinstance(valeur, dict) or set(valeur) - {f.name for f in fields(TransfertConjointFederal2025)}:
        raise ValueError("Champs du transfert du conjoint invalides.")
    p = valider_transfert_conjoint_2025(TransfertConjointFederal2025(**valeur))
    calculer_transfert_conjoint_2025(p, beneficiaire=beneficiaire)
    return p


def sauvegarder_dossier_fiscal(
    dossier: DossierFiscalValide,
    *,
    estimation: EstimationFiscale2025 | None = None,
    ajustement_reer: AjustementReer2025 | None = None,
    deduction_celiapp: DeductionCeliapp2025 | None = None,
    frais_garde_federaux: FraisGardeFederaux2025 | None = None,
    depenses_emploi: DepensesEmploi2025 | None = None,
    frais_demenagement: FraisDemenagement2025 | None = None,
    pension_alimentaire_payee: PensionAlimentairePayee2025 | None = None,
    autres_deductions: AutresDeductions2025 | None = None,
    renovations_multigenerationnelles: RenovationsMultigenerationnelles2025 | None = None,
    transferts_handicap: TransfertsHandicap2025 | None = None,
    frais_medicaux_famille: FraisMedicauxFamilleFederaux2025 | None = None,
    fournitures_educateur: FournituresEducateur2025 | None = None,
    fonds_travailleurs: FondsTravailleurs2025 | None = None,
    contributions_politiques: ContributionsPolitiques2025 | None = None,
    adoption: Adoption2025 | None = None,
    benevoles: Benevoles2025 | None = None,
    transfert_conjoint: TransfertConjointFederal2025 | None = None,
    transferts_scolarite_recus: TransfertsScolariteRecus2025 | None = None,
    allocation_travailleurs: AllocationTravailleurs2025 | None = None,
    frais_garde_quebec: FraisGardeQuebec2025 | None = None,
    soutien_aines_quebec: SoutienAinesQuebec2025 | None = None,
    volontaires_quebec: VolontairesQuebec2025 | None = None,
    maintien_domicile_quebec: MaintienDomicileQuebec2025 | None = None,
    prime_travail_quebec: PrimeTravailQuebec2025 | None = None,
    solidarite_quebec: SolidariteQuebec2025 | None = None,
    personne_aidante_quebec: PersonneAidanteQuebec2025 | None = None,
    medical_remboursable_quebec: MedicalRemboursableQuebec2025 | None = None,
    prolongation_carriere_quebec: ProlongationCarriereQuebec2025 | None = None,
    achat_habitation_quebec: AchatHabitationQuebec2025 | None = None,
    interets_etudiants_quebec: InteretsEtudiantsQuebec2025 | None = None,
    interets_pret_etudiant: InteretsPretEtudiant2025 | None = None,
    cotisations_syndicales: (
        CotisationsSyndicalesProfessionnelles2025 | None
    ) = None,
    dons_bienfaisance: DonsBienfaisance2025 | None = None,
    frais_medicaux: FraisMedicaux2025 | None = None,
    frais_scolarite: FraisScolarite2025 | None = None,
    credit_deficience: CreditDeficience2025 | None = None,
    assurance_medicaments: AssuranceMedicamentsQuebec2025 | None = None,
    cotisations_excedentaires: CotisationsExcedentaires2025 | None = None,
    personne_vivant_seule: PersonneVivantSeule2025 | None = None,
    montants_age_retraite: MontantsAgeRetraite2025 | None = None,
    credits_federaux_age_pension: CreditsFederauxAgePension2025 | None = None,
    montant_conjoint_federal: MontantConjointFederal2025 | None = None,
    personne_charge_admissible_federale: (
        MontantPersonneChargeAdmissibleFederal2025 | None
    ) = None,
    accessibilite_domiciliaire_federale: (
        DepensesAccessibiliteDomiciliaireFederal2025 | None
    ) = None,
    achat_habitation_federal: (
        MontantAchatHabitationFederal2025 | None
    ) = None,
    aidant_autre_personne_charge_federal: (
        AidantNaturelAutrePersonneChargeFederal2025 | None
    ) = None,
    aidant_conjoint_personne_charge_federal: (
        AidantNaturelConjointOuPersonneChargeFederal2025 | None
    ) = None,
    aidant_enfant_federal: (
        AidantNaturelEnfantMoins18Federal2025 | None
    ) = None,
    rapport_pdf: Path | str | None = None,
    destination: Path | str | None = None,
    cotisations_rpa: CotisationsRpa2025 | None = None,
    rqap_confirme: bool | None = None,
    ae_confirme: bool | None = None,
    profil_reports_pertes: ProfilReportsPertes2025 | None = None,
    profil_frais_placement: ProfilFraisPlacement2025 | None = None,
    profil_capital: ProfilCapital2025 | None = None,
    profil_dividendes: ProfilDividendes2025 | None = None,
    profil_interets: ProfilInterets2025 | None = None,
    profil_placement_etranger: ProfilPlacementEtranger2025 | None = None,
    profil_credit_impot_etranger: ProfilCreditImpotEtranger2025 | None = None,
    profil_remplacement: ProfilRemplacement2025 | None = None,
    profil_retraits: ProfilRetraits2025 | None = None,
    profil_pensions: ProfilPensions2025 | None = None,
    psv_confirme: bool | None = None,
    rrq_rpc_confirme: bool | None = None,
) -> Path:
    if estimation is not None:
        estime_30450 = estimation.aidant_autre_personne_charge_federal
        if estime_30450.partage_30450_confirme or estime_30450.personnes_detaillees or (
            aidant_autre_personne_charge_federal is not None
            and (aidant_autre_personne_charge_federal.partage_30450_confirme or aidant_autre_personne_charge_federal.personnes_detaillees)
        ):
            if aidant_autre_personne_charge_federal is None:
                aidant_autre_personne_charge_federal = estime_30450
            elif aidant_autre_personne_charge_federal != estime_30450:
                raise ValueError("Profil de partage 30450 divergent de l'estimation.")

    if estimation is not None and (estimation.aidant_enfant_federal.enfants_detailles or (
        aidant_enfant_federal is not None and aidant_enfant_federal.enfants_detailles
    )):
        if aidant_enfant_federal is None:
            aidant_enfant_federal = estimation.aidant_enfant_federal
        elif aidant_enfant_federal != estimation.aidant_enfant_federal:
            raise ValueError("Profil des enfants 30500 divergent de l'estimation.")

    if estimation is not None and (estimation.achat_habitation_federal.partage_31270_confirme or (
        achat_habitation_federal is not None and achat_habitation_federal.partage_31270_confirme
    )):
        if achat_habitation_federal is None:
            achat_habitation_federal = estimation.achat_habitation_federal
        elif achat_habitation_federal != estimation.achat_habitation_federal:
            raise ValueError("Profil partagé 31270 divergent de l'estimation.")

    if estimation is not None and (estimation.accessibilite_domiciliaire_federale.partage_31285_confirme or (
        accessibilite_domiciliaire_federale is not None and accessibilite_domiciliaire_federale.partage_31285_confirme
    )):
        if accessibilite_domiciliaire_federale is None:
            accessibilite_domiciliaire_federale = estimation.accessibilite_domiciliaire_federale
        elif accessibilite_domiciliaire_federale != estimation.accessibilite_domiciliaire_federale:
            raise ValueError("Profil partagé 31285 divergent de l'estimation.")

    if estimation is not None and any(p is not None and p.combinaison_annexe_b_confirmee for p in (
        personne_vivant_seule, montants_age_retraite, estimation.personne_vivant_seule, estimation.montants_age_retraite)):
        if personne_vivant_seule is None:
            personne_vivant_seule = estimation.personne_vivant_seule
        elif personne_vivant_seule != estimation.personne_vivant_seule:
            raise ValueError("Profil personne seule de l'annexe B divergent de l'estimation.")
        if montants_age_retraite is None:
            montants_age_retraite = estimation.montants_age_retraite
        elif montants_age_retraite != estimation.montants_age_retraite:
            raise ValueError("Profil âge/retraite de l'annexe B divergent de l'estimation.")

    celiapp_effectif = (
        deduction_celiapp
        if deduction_celiapp is not None
        else (
            estimation.deduction_celiapp
            if estimation is not None
            else DeductionCeliapp2025()
        )
    )
    celiapp_effectif = valider_deduction_celiapp_2025(celiapp_effectif)
    if (
        estimation is not None
        and celiapp_effectif != estimation.deduction_celiapp
    ):
        raise ValueError(
            "La déduction CELIAPP diffère de l'estimation."
        )

    frais_garde_effectifs = (
        frais_garde_federaux
        if frais_garde_federaux is not None
        else (
            estimation.frais_garde_federaux
            if estimation is not None
            else FraisGardeFederaux2025()
        )
    )
    frais_garde_effectifs = valider_frais_garde_federaux_2025(
        frais_garde_effectifs
    )
    if (
        estimation is not None
        and frais_garde_effectifs != estimation.frais_garde_federaux
    ):
        raise ValueError(
            "Les frais de garde fédéraux diffèrent de l'estimation."
        )

    depenses_emploi_effectives = (
        depenses_emploi
        if depenses_emploi is not None
        else (
            estimation.depenses_emploi
            if estimation is not None
            else DepensesEmploi2025()
        )
    )
    depenses_emploi_effectives = valider_depenses_emploi_2025(
        depenses_emploi_effectives
    )
    if (
        estimation is not None
        and depenses_emploi_effectives != estimation.depenses_emploi
    ):
        raise ValueError(
            "Les dépenses d'emploi diffèrent de l'estimation."
        )

    frais_demenagement_effectifs = (
        frais_demenagement
        if frais_demenagement is not None
        else (
            estimation.frais_demenagement
            if estimation is not None
            else FraisDemenagement2025()
        )
    )
    frais_demenagement_effectifs = valider_frais_demenagement_2025(
        frais_demenagement_effectifs
    )
    if (
        estimation is not None
        and frais_demenagement_effectifs != estimation.frais_demenagement
    ):
        raise ValueError(
            "Les frais de déménagement diffèrent de l'estimation."
        )

    pension_alimentaire_effective = (
        pension_alimentaire_payee
        if pension_alimentaire_payee is not None
        else (
            estimation.pension_alimentaire_payee
            if estimation is not None
            else PensionAlimentairePayee2025()
        )
    )
    pension_alimentaire_effective = (
        valider_pension_alimentaire_payee_2025(
            pension_alimentaire_effective
        )
    )
    if (
        estimation is not None
        and pension_alimentaire_effective
        != estimation.pension_alimentaire_payee
    ):
        raise ValueError(
            "La pension alimentaire diffère de l'estimation."
        )

    if estimation is not None:
        if credit_deficience is None and estimation.credit_deficience.naissance_federale:
            credit_deficience = estimation.credit_deficience
        elif credit_deficience is not None and (credit_deficience.naissance_federale or estimation.credit_deficience.naissance_federale):
            if credit_deficience != estimation.credit_deficience:
                raise ValueError("Profil handicap détaillé divergent de l'estimation.")

    if estimation is not None:
        if frais_medicaux is None:
            frais_medicaux = estimation.frais_medicaux
        elif (frais_medicaux.supplement != SupplementMedical2025()
              or estimation.frais_medicaux.supplement != SupplementMedical2025()):
            if frais_medicaux != estimation.frais_medicaux:
                raise ValueError("Le profil médical/supplément diffère de l'estimation.")

    if estimation is not None:
        if frais_scolarite is None:
            frais_scolarite = estimation.frais_scolarite
        elif (frais_scolarite.formation != Formation2025()
              or estimation.frais_scolarite.formation != Formation2025()
              or frais_scolarite.reports_federaux != ReportsScolariteFederaux2025()
              or estimation.frais_scolarite.reports_federaux != ReportsScolariteFederaux2025()):
            if frais_scolarite != estimation.frais_scolarite:
                raise ValueError("Le profil scolarité/formation diffère de l'estimation.")

    if estimation is not None:
        if dons_bienfaisance is None:
            dons_bienfaisance = estimation.dons_bienfaisance
        elif (dons_bienfaisance.reports_federaux.activer or estimation.dons_bienfaisance.reports_federaux.activer) and dons_bienfaisance != estimation.dons_bienfaisance:
            raise ValueError("Le profil dons/reports diffère de l'estimation.")

    if estimation is not None and (
        estimation.personne_charge_admissible_federale.enfant_infirmite_ligne30500
        or estimation.aidant_enfant_federal.enfant_reclame_30400
        or (personne_charge_admissible_federale is not None and personne_charge_admissible_federale.enfant_infirmite_ligne30500)
        or (aidant_enfant_federal is not None and aidant_enfant_federal.enfant_reclame_30400)
    ):
        if personne_charge_admissible_federale is None:
            personne_charge_admissible_federale = estimation.personne_charge_admissible_federale
        if aidant_enfant_federal is None:
            aidant_enfant_federal = estimation.aidant_enfant_federal
        if (personne_charge_admissible_federale != estimation.personne_charge_admissible_federale
                or aidant_enfant_federal != estimation.aidant_enfant_federal):
            raise ValueError("Profils 30400/30500 divergents de l'estimation.")

    medical_familial = frais_medicaux_famille if frais_medicaux_famille is not None else (estimation.frais_medicaux_famille if estimation else FraisMedicauxFamilleFederaux2025())
    if estimation is not None and medical_familial != estimation.frais_medicaux_famille:
        raise ValueError("Profil médical familial divergent de l'estimation.")
    calculer_medical_familial_2025(medical_familial, demandeur=dossier.client,
        revenu_net=estimation.revenu.revenu_net_federal if estimation else Decimal(0), annee=dossier.annee_fiscale)
    multigenerationnel = renovations_multigenerationnelles if renovations_multigenerationnelles is not None else (estimation.renovations_multigenerationnelles if estimation else RenovationsMultigenerationnelles2025())
    acces_5q = accessibilite_domiciliaire_federale if accessibilite_domiciliaire_federale is not None else (estimation.accessibilite_domiciliaire_federale if estimation else None)
    calculer_multigenerationnel_2025(multigenerationnel, annee=dossier.annee_fiscale,
        autres_frais_reclames=bool(medical_familial.depenses or (frais_medicaux and frais_medicaux.montant_admissible_federal) or (acces_5q and acces_5q.depenses_admissibles)))
    if estimation is not None and multigenerationnel != estimation.renovations_multigenerationnelles:
        raise ValueError("Profil multigénérationnel divergent de l'estimation.")
    educateur = fournitures_educateur if fournitures_educateur is not None else (estimation.fournitures_educateur if estimation else FournituresEducateur2025())
    calculer_fournitures_educateur_2025(educateur, annee=dossier.annee_fiscale, deduction_t777=depenses_emploi_effectives.deduction_federale_t777)
    if estimation is not None and educateur != estimation.fournitures_educateur:
        raise ValueError("Profil éducateur divergent de l'estimation.")
    fonds = fonds_travailleurs if fonds_travailleurs is not None else (estimation.fonds_travailleurs if estimation else FondsTravailleurs2025())
    calculer_fonds_travailleurs_2025(fonds, client=dossier.client, annee=dossier.annee_fiscale)
    if estimation is not None and fonds != estimation.fonds_travailleurs:
        raise ValueError("Profil fonds divergent de l'estimation.")
    politiques = contributions_politiques if contributions_politiques is not None else (estimation.contributions_politiques if estimation else ContributionsPolitiques2025())
    calculer_contributions_politiques_2025(politiques, client=dossier.client, annee=dossier.annee_fiscale)
    if estimation is not None and politiques != estimation.contributions_politiques:
        raise ValueError("Profil politique divergent de l'estimation.")
    adoption_effective = adoption if adoption is not None else (estimation.adoption if estimation else Adoption2025())
    calculer_adoption_2025(adoption_effective, dossier.annee_fiscale)
    if estimation is not None and adoption_effective != estimation.adoption:
        raise ValueError("Le profil adoption diffère de celui de l'estimation.")
    benevoles_effectifs = benevoles if benevoles is not None else (estimation.benevoles if estimation else Benevoles2025())
    calculer_benevoles_2025(benevoles_effectifs, dossier)
    if estimation is not None and benevoles_effectifs != estimation.benevoles:
        raise ValueError("Le profil bénévoles diffère de l'estimation.")
    handicap_transfere = transferts_handicap if transferts_handicap is not None else (estimation.transferts_handicap if estimation else TransfertsHandicap2025())
    if estimation is not None and handicap_transfere != estimation.transferts_handicap:
        raise ValueError("Profil des transferts handicap divergent de l'estimation.")
    conjoint = valider_transfert_conjoint_2025(
        transfert_conjoint if transfert_conjoint is not None
        else (estimation.transfert_conjoint if estimation else TransfertConjointFederal2025())
    )
    if estimation is not None and conjoint != estimation.transfert_conjoint:
        raise ValueError("Le profil transfert du conjoint diffère de l'estimation.")
    calculer_transfert_conjoint_2025(conjoint, beneficiaire=dossier.client)
    scolarite_recue = valider_transferts_scolarite_recus_2025(
        transferts_scolarite_recus if transferts_scolarite_recus is not None
        else (estimation.transferts_scolarite_recus if estimation else TransfertsScolariteRecus2025())
    )
    if estimation is not None and scolarite_recue != estimation.transferts_scolarite_recus:
        raise ValueError("Le profil scolarité reçue diffère de l’estimation.")
    act = valider_allocation_travailleurs_2025(
        allocation_travailleurs if allocation_travailleurs is not None
        else (estimation.allocation_travailleurs if estimation else AllocationTravailleurs2025())
    )
    if estimation is not None and act != estimation.allocation_travailleurs:
        raise ValueError("Le profil ACT diffère de l'estimation.")
    frais_garde_quebec = valider_garde_quebec_2025(frais_garde_quebec if frais_garde_quebec is not None
        else estimation.frais_garde_quebec if estimation is not None else FraisGardeQuebec2025())
    if estimation is not None and frais_garde_quebec != estimation.frais_garde_quebec:
        raise ValueError("Profil de garde Québec divergent de l'estimation.")
    medical_remboursable_quebec = valider_medical_remboursable_quebec_2025(medical_remboursable_quebec if medical_remboursable_quebec is not None
        else estimation.medical_remboursable_quebec if estimation is not None else MedicalRemboursableQuebec2025())
    if estimation is not None and medical_remboursable_quebec != estimation.medical_remboursable_quebec:
        raise ValueError("Profil médical remboursable Québec divergent de l'estimation.")
    carriere_quebec = valider_carriere_quebec_2025(prolongation_carriere_quebec if prolongation_carriere_quebec is not None
        else estimation.prolongation_carriere_quebec if estimation is not None else ProlongationCarriereQuebec2025())
    if estimation is not None and carriere_quebec != estimation.prolongation_carriere_quebec:
        raise ValueError("Profil prolongation de carrière Québec divergent de l'estimation.")
    achat_quebec = valider_achat_quebec_2025(achat_habitation_quebec if achat_habitation_quebec is not None
        else estimation.achat_habitation_quebec if estimation is not None else AchatHabitationQuebec2025())
    if estimation is not None and achat_quebec != estimation.achat_habitation_quebec:
        raise ValueError("Profil achat habitation Québec divergent de l'estimation.")
    pret_quebec = valider_interets_quebec_2025(interets_etudiants_quebec if interets_etudiants_quebec is not None
        else estimation.interets_etudiants_quebec if estimation is not None else InteretsEtudiantsQuebec2025())
    if estimation is not None and pret_quebec != estimation.interets_etudiants_quebec:
        raise ValueError("Profil intérêts étudiants Québec divergent de l'estimation.")
    pret_etudiant = valider_interets_pret_etudiant_2025(
        interets_pret_etudiant if interets_pret_etudiant is not None
        else (estimation.interets_pret_etudiant if estimation else InteretsPretEtudiant2025())
    )
    if estimation is not None and pret_etudiant != estimation.interets_pret_etudiant:
        raise ValueError("Le profil intérêts étudiants diffère de l'estimation.")
    soutien_aines_quebec = valider_soutien_aines_quebec_2025(soutien_aines_quebec if soutien_aines_quebec is not None
        else estimation.soutien_aines_quebec if estimation is not None else SoutienAinesQuebec2025())
    if estimation is not None and soutien_aines_quebec != estimation.soutien_aines_quebec:
        raise ValueError("Profil soutien aux aînés divergent de l'estimation.")
    volontaires_quebec = valider_volontaires_quebec_2025(volontaires_quebec if volontaires_quebec is not None
        else estimation.volontaires_quebec if estimation is not None else VolontairesQuebec2025())
    if estimation is not None and volontaires_quebec != estimation.volontaires_quebec:
        raise ValueError("Profil volontaires Québec divergent de l'estimation.")
    maintien_domicile_quebec = valider_maintien_domicile_quebec_2025(maintien_domicile_quebec if maintien_domicile_quebec is not None
        else estimation.maintien_domicile_quebec if estimation is not None else MaintienDomicileQuebec2025())
    if estimation is not None and maintien_domicile_quebec != estimation.maintien_domicile_quebec:
        raise ValueError("Profil maintien à domicile divergent de l'estimation.")
    prime_travail_quebec = valider_prime_travail_quebec_2025(prime_travail_quebec if prime_travail_quebec is not None
        else estimation.prime_travail_quebec if estimation is not None else PrimeTravailQuebec2025())
    if estimation is not None and prime_travail_quebec != estimation.prime_travail_quebec:
        raise ValueError("Profil prime au travail divergent de l'estimation.")
    solidarite_quebec = valider_solidarite_quebec_2025(solidarite_quebec if solidarite_quebec is not None
        else estimation.solidarite_quebec if estimation is not None else SolidariteQuebec2025())
    if estimation is not None and solidarite_quebec != estimation.solidarite_quebec:
        raise ValueError("Profil solidarité Québec divergent de l'estimation.")
    personne_aidante_quebec = valider_aidante_quebec_2025(personne_aidante_quebec if personne_aidante_quebec is not None
        else estimation.personne_aidante_quebec if estimation is not None else PersonneAidanteQuebec2025())
    if estimation is not None and personne_aidante_quebec != estimation.personne_aidante_quebec:
        raise ValueError("Profil de personne aidante Québec divergent de l'estimation.")

    autres_deductions_effectives = (
        autres_deductions
        if autres_deductions is not None
        else (
            estimation.autres_deductions
            if estimation is not None
            else AutresDeductions2025()
        )
    )
    autres_deductions_effectives = valider_autres_deductions_2025(
        autres_deductions_effectives
    )
    if (
        estimation is not None
        and autres_deductions_effectives != estimation.autres_deductions
    ):
        raise ValueError(
            "Les autres déductions diffèrent de l'estimation."
        )

    pertes_effectif = profil_reports_pertes if profil_reports_pertes is not None else (estimation.profil_reports_pertes if estimation else ProfilReportsPertes2025())
    if estimation and pertes_effectif != estimation.profil_reports_pertes:
        raise ValueError("Le profil reports de pertes diffère de l'estimation.")
    frais_effectif = profil_frais_placement if profil_frais_placement is not None else (estimation.profil_frais_placement if estimation else ProfilFraisPlacement2025())
    valider_profil_frais_placement_2025(frais_effectif)
    if estimation and frais_effectif != estimation.profil_frais_placement:
        raise ValueError("Le profil frais de placement diffère de l'estimation.")
    capital_effectif = profil_capital if profil_capital is not None else (estimation.profil_capital if estimation else ProfilCapital2025())
    valider_profil_capital_2025(capital_effectif)
    if estimation and capital_effectif != estimation.profil_capital:
        raise ValueError("Le profil capital diffère de l’estimation.")
    # Validation standalone ou combinée différée jusqu'à connaître
    # les profils intérêts/dividendes effectifs.
    dividendes_effectif = profil_dividendes if profil_dividendes is not None else (estimation.profil_dividendes if estimation else ProfilDividendes2025())
    valider_profil_dividendes_2025(dividendes_effectif)
    if estimation and dividendes_effectif != estimation.profil_dividendes:
        raise ValueError("Le profil dividendes diffère de l’estimation.")
    interets_effectif_preliminaire = (
        profil_interets
        if profil_interets is not None
        else (
            estimation.profil_interets
            if estimation is not None
            else ProfilInterets2025()
        )
    )
    combinaison_3h_a = (
        dividendes_effectif.confirme
        and interets_effectif_preliminaire.confirme
    )
    if dividendes_effectif.confirme and not combinaison_3h_a:
        if any((rqap_confirme, ae_confirme, rrq_rpc_confirme, psv_confirme)) or any(p and p != type(p)() for p in (profil_pensions, profil_retraits, profil_remplacement, profil_interets)):
            raise ValueError("Dividendes avec autres placements/prestations : hors périmètre 3C.")
        consolider_dividendes_2025(dossier, dividendes_effectif)
    placement_etranger_effectif = (
        profil_placement_etranger
        if profil_placement_etranger is not None
        else (
            estimation.profil_placement_etranger
            if estimation is not None
            else ProfilPlacementEtranger2025()
        )
    )
    valider_profil_placement_etranger_2025(placement_etranger_effectif)
    if (
        estimation is not None
        and placement_etranger_effectif != estimation.profil_placement_etranger
    ):
        raise ValueError("Le profil placement étranger diffère de l'estimation.")

    credit_etranger_effectif = (
        profil_credit_impot_etranger
        if profil_credit_impot_etranger is not None
        else (
            estimation.profil_credit_impot_etranger
            if estimation is not None
            else ProfilCreditImpotEtranger2025()
        )
    )
    if (
        estimation is not None
        and credit_etranger_effectif != estimation.profil_credit_impot_etranger
    ):
        raise ValueError("Le profil de crédit étranger diffère de l'estimation.")

    if placement_etranger_effectif != ProfilPlacementEtranger2025():
        placement_etranger_resultat = consolider_placement_etranger_2025(
            dossier, placement_etranger_effectif
        )
        valider_profil_credit_impot_etranger_2025(
            credit_etranger_effectif, placement_etranger_resultat
        )
    elif credit_etranger_effectif != ProfilCreditImpotEtranger2025():
        raise ValueError(
            "Un profil de crédit étranger ne peut pas être sauvegardé "
            "sans profil de placement étranger."
        )

    interets_effectif = interets_effectif_preliminaire
    valider_profil_interets_2025(interets_effectif)
    if estimation and interets_effectif != estimation.profil_interets:
        raise ValueError("Le profil intérêts diffère de l’estimation.")
    if combinaison_3h_a:
        if any((rqap_confirme, ae_confirme, rrq_rpc_confirme, psv_confirme)):
            raise ValueError("Combinaison intérêts + dividendes avec autre parcours : hors périmètre 3H.")
        if any(
            p is not None and p != type(p)()
            for p in (
                profil_pensions,
                profil_retraits,
                profil_remplacement,
                profil_placement_etranger,
            )
        ):
            raise ValueError("Combinaison intérêts + dividendes avec autre parcours : hors périmètre 3H.")
        if pertes_effectif != ProfilReportsPertes2025():
            if not capital_effectif.confirme:
                raise ValueError(
                    "Combinaison intérêts + dividendes + reports sans capital : "
                    "hors périmètre 3H-E."
                )
        if capital_effectif.confirme:
            consolider_interets_dividendes_capital_2025(
                dossier,
                interets_effectif,
                dividendes_effectif,
                capital_effectif,
            )
        else:
            consolider_interets_dividendes_2025(
                dossier,
                interets_effectif,
                dividendes_effectif,
            )
    elif capital_effectif.confirme:
        if any((rqap_confirme, ae_confirme, rrq_rpc_confirme, psv_confirme)) or any(
            p is not None and p != type(p)()
            for p in (
                profil_pensions,
                profil_retraits,
                profil_remplacement,
            )
        ) or interets_effectif != ProfilInterets2025() or dividendes_effectif != ProfilDividendes2025():
            raise ValueError("Capital avec autres placements/prestations : hors périmètre 3D.")
        consolider_capital_2025(dossier, capital_effectif)
    elif interets_effectif.confirme:
        if any((rqap_confirme, ae_confirme, rrq_rpc_confirme, psv_confirme)) or any(p and p.confirme for p in (profil_pensions, profil_retraits, profil_remplacement)):
            raise ValueError("Intérêts avec autres prestations : hors périmètre 3A.")
        consolider_interets_2025(dossier, interets_effectif)
    remplacement_effectif = profil_remplacement if profil_remplacement is not None else (estimation.profil_remplacement if estimation else ProfilRemplacement2025())
    valider_profil_remplacement_2025(remplacement_effectif)
    if estimation and remplacement_effectif != estimation.profil_remplacement:
        raise ValueError("Le profil remplacement diffère de l’estimation.")
    if remplacement_effectif.confirme:
        if any((rqap_confirme, ae_confirme, rrq_rpc_confirme, psv_confirme)) or (profil_pensions and profil_pensions.confirme) or (profil_retraits and profil_retraits.confirme):
            raise ValueError("Remplacement avec autres prestations : hors périmètre.")
        consolider_remplacement_2025(dossier, remplacement_effectif)
    retraits_effectif = profil_retraits if profil_retraits is not None else (estimation.profil_retraits if estimation else ProfilRetraits2025())
    valider_profil_retraits_2025(retraits_effectif)
    if estimation and retraits_effectif != estimation.profil_retraits:
        raise ValueError("Le profil retraits diffère de l'estimation.")
    if retraits_effectif.confirme:
        if any((rqap_confirme, ae_confirme, rrq_rpc_confirme, psv_confirme)) or (profil_pensions and profil_pensions.confirme):
            raise ValueError("Retraits avec autres prestations : hors périmètre.")
        consolider_retraits_2025(dossier, retraits_effectif)
    pensions_effectif = profil_pensions if profil_pensions is not None else (estimation.profil_pensions if estimation else ProfilPensions2025())
    valider_profil_pensions_2025(pensions_effectif)
    if estimation and pensions_effectif != estimation.profil_pensions:
        raise ValueError("Le profil pensions diffère de l'estimation.")
    if pensions_effectif.confirme:
        if any((psv_confirme, rqap_confirme, ae_confirme, rrq_rpc_confirme)) or (estimation and any((estimation.psv_confirme, estimation.ae_confirme, estimation.rqap_confirme, estimation.rrq_rpc_confirme))):
            raise ValueError("Pensions avec d'autres prestations hors périmètre.")
        consolider_pensions_2025(dossier, pensions_effectif)
    confirme_psv = psv_confirme if psv_confirme is not None else (estimation.psv_confirme if estimation else False)
    valider_confirmation_psv(confirme_psv)
    if estimation is not None and confirme_psv != estimation.psv_confirme:
        raise ValueError("La confirmation PSV diffère de l'estimation.")
    if confirme_psv:
        if rqap_confirme or ae_confirme or rrq_rpc_confirme or (estimation and (estimation.rqap_confirme or estimation.ae_confirme or estimation.rrq_rpc_confirme)):
            raise ValueError("PSV avec AE/RQAP/RRQ : hors périmètre.")
        consolider_prestations_psv_2025(dossier, True)
    confirme_rrq_rpc = rrq_rpc_confirme if rrq_rpc_confirme is not None else (estimation.rrq_rpc_confirme if estimation else False)
    valider_confirmation_rrq_rpc(confirme_rrq_rpc)
    if estimation is not None and confirme_rrq_rpc != estimation.rrq_rpc_confirme:
        raise ValueError("La confirmation RRQ/RPC diffère de l'estimation.")
    if confirme_rrq_rpc:
        consolider_prestations_rrq_rpc_2025(dossier, True)
        if rqap_confirme or ae_confirme or (estimation and (estimation.rqap_confirme or estimation.ae_confirme)):
            raise ValueError("RRQ/RPC avec AE/RQAP : hors périmètre.")
    confirme = rqap_confirme if rqap_confirme is not None else (estimation.rqap_confirme if estimation else False)
    valider_confirmation_rqap(confirme)
    confirme_ae = ae_confirme if ae_confirme is not None else (estimation.ae_confirme if estimation else False)
    valider_confirmation_ae(confirme_ae)
    if confirme and confirme_ae:
        raise ValueError("AE et RQAP simultanés : hors périmètre.")
    if estimation is not None and confirme_ae != estimation.ae_confirme:
        raise ValueError("La confirmation AE diffère de l'estimation.")
    if confirme_ae:
        consolider_prestations_ae_2025(dossier, True)
    if estimation is not None and (confirme != estimation.rqap_confirme or dossier != estimation.dossier):
        raise ValueError("Le dossier ou la confirmation RQAP diffère de l'estimation.")
    if confirme:
        consolider_prestations_rqap_2025(dossier, confirme)
    rpa = cotisations_rpa if cotisations_rpa is not None else (
        estimation.cotisations_rpa if estimation is not None else CotisationsRpa2025()
    )
    valider_cotisations_rpa_2025(rpa)
    if estimation is not None and rpa != estimation.cotisations_rpa:
        raise ValueError("Le profil RPA ne correspond pas à l'estimation à sauvegarder.")
    # Un dossier peut être sauvegardé avant le paramétrage RPA; le calcul
    # impose ensuite la cohérence avec les cases validées.
    if rpa.montant_federal:
        verifier_rpa_dossier_2025(dossier, rpa)
    verifier_confirmation_reports_pertes_2025(pertes_effectif, dossier, capital_effectif, frais_effectif)
    verifier_confirmation_frais_2025(frais_effectif, dossier, interets_effectif, dividendes_effectif, capital_effectif)
    if destination is None:
        DOSSIERS_FISCAUX_DIR.mkdir(parents=True, exist_ok=True)
        chemin = DOSSIERS_FISCAUX_DIR / nom_fichier_dossier_fiscal(dossier)
    else:
        chemin = Path(destination)
        if chemin.suffix.lower() != ".json":
            chemin = chemin.with_suffix(".json")
        chemin.parent.mkdir(parents=True, exist_ok=True)

    contenu = {
        "schema_version": SCHEMA_VERSION,
        "rqap_confirme": confirme,
        "ae_confirme": confirme_ae,
        "profil_pensions": asdict(pensions_effectif),
        "profil_retraits": asdict(retraits_effectif),
        "profil_remplacement": asdict(remplacement_effectif),
        "profil_interets": asdict(interets_effectif),
        "profil_placement_etranger": asdict(placement_etranger_effectif),
        "profil_credit_impot_etranger": {
            "credit_federal_40500": _decimal_texte(
                credit_etranger_effectif.credit_federal_40500
            ),
            "credit_quebec_409": _decimal_texte(
                credit_etranger_effectif.credit_quebec_409
            ),
            "source_t2209": credit_etranger_effectif.source_t2209,
            "source_tp772": credit_etranger_effectif.source_tp772,
            "confirme": credit_etranger_effectif.confirme,
        },
        "profil_dividendes": asdict(dividendes_effectif),
        "profil_reports_pertes": asdict(pertes_effectif),
        "profil_frais_placement": asdict(frais_effectif),
        "profil_capital": asdict(capital_effectif),
        "psv_confirme": confirme_psv,
        "rrq_rpc_confirme": confirme_rrq_rpc,
        "cotisations_rpa": {
            nom: _decimal_texte(valeur) if isinstance(valeur, Decimal) else valeur
            for nom, valeur in vars(rpa).items()
        },
        "sauvegarde_le": datetime.now().astimezone().isoformat(timespec="seconds"),
        "client": dossier.client,
        "annee_fiscale": dossier.annee_fiscale,
        "province": dossier.province,
        "documents": [_chemin_vers_stockage(x) for x in dossier.documents],
        "donnees_validees": [
            {
                "document": _chemin_vers_stockage(d.document),
                "type_document": d.type_document,
                "case": d.case,
                "libelle": d.libelle,
                "valeur_extraite": _decimal_texte(d.valeur_extraite),
                "valeur_validee": _decimal_texte(d.valeur_validee),
                "corrigee": bool(d.corrigee),
                "statut": d.statut,
            }
            for d in dossier.donnees_validees
        ],
        "derniere_estimation": _estimation_vers_dict(estimation),
        "ajustement_reer": _ajustement_reer_vers_dict(
            ajustement_reer
        ),
        "deduction_celiapp": _deduction_celiapp_vers_dict(
            celiapp_effectif
        ),
        "frais_garde_federaux": _frais_garde_federaux_vers_dict(
            frais_garde_effectifs
        ),
        "depenses_emploi": _depenses_emploi_vers_dict(
            depenses_emploi_effectives
        ),
        "frais_demenagement": _frais_demenagement_vers_dict(
            frais_demenagement_effectifs
        ),
        "pension_alimentaire_payee": _pension_alimentaire_payee_vers_dict(
            pension_alimentaire_effective
        ),
        "renovations_multigenerationnelles": multigenerationnel_vers_dict(multigenerationnel),
        "transferts_handicap": transferts_handicap_vers_dict(handicap_transfere),
        "frais_medicaux_famille": medical_familial_vers_dict(medical_familial),
        "fournitures_educateur": educateur_vers_dict(educateur),
        "fonds_travailleurs": fonds_vers_dict(fonds),
        "contributions_politiques": politiques_vers_dict(politiques),
        "adoption": adoption_vers_dict(adoption_effective),
        "benevoles": _benevoles_vers_dict(benevoles_effectifs),
        "transfert_conjoint": {nom: getattr(conjoint, nom) for nom in conjoint.__dataclass_fields__},
        "transferts_scolarite_recus": _scolarite_recue_vers_dict(scolarite_recue),
        "allocation_travailleurs": _allocation_travailleurs_vers_dict(act),
        "frais_garde_quebec": garde_quebec_vers_dict(frais_garde_quebec),
        "soutien_aines_quebec": soutien_aines_vers_dict(soutien_aines_quebec),
        "volontaires_quebec": volontaires_vers_dict(volontaires_quebec),
        "maintien_domicile_quebec": maintien_domicile_vers_dict(maintien_domicile_quebec),
        "prime_travail_quebec": prime_travail_vers_dict(prime_travail_quebec),
        "solidarite_quebec": solidarite_quebec_vers_dict(solidarite_quebec),
        "personne_aidante_quebec": aidante_quebec_vers_dict(personne_aidante_quebec),
        "medical_remboursable_quebec": medical_remboursable_quebec_vers_dict(medical_remboursable_quebec),
        "prolongation_carriere_quebec": carriere_quebec_vers_dict(carriere_quebec),
        "achat_habitation_quebec": achat_quebec_vers_dict(achat_quebec),
        "interets_etudiants_quebec": interets_quebec_vers_dict(pret_quebec),
        "interets_pret_etudiant": _interets_pret_etudiant_vers_dict(pret_etudiant),
        "autres_deductions": _autres_deductions_vers_dict(
            autres_deductions_effectives
        ),
        "cotisations_syndicales": _cotisations_syndicales_vers_dict(
            cotisations_syndicales
        ),
        "dons_bienfaisance": _dons_bienfaisance_vers_dict(
            dons_bienfaisance
        ),
        "frais_medicaux": _frais_medicaux_vers_dict(
            frais_medicaux
        ),
        "frais_scolarite": _frais_scolarite_vers_dict(
            frais_scolarite
        ),
        "credit_deficience": _credit_deficience_vers_dict(
            credit_deficience
        ),
        "assurance_medicaments": _assurance_medicaments_vers_dict(
            assurance_medicaments
        ),
        "cotisations_excedentaires": _cotisations_excedentaires_vers_dict(
            cotisations_excedentaires
        ),
        "personne_vivant_seule": _personne_vivant_seule_vers_dict(
            personne_vivant_seule
        ),
        "montants_age_retraite": _montants_age_retraite_vers_dict(
            montants_age_retraite
        ),
        "credits_federaux_age_pension": _credits_federaux_age_pension_vers_dict(
            credits_federaux_age_pension
        ),
        "montant_conjoint_federal": _montant_conjoint_federal_vers_dict(
            montant_conjoint_federal
        ),
        "personne_charge_admissible_federale": (
            _personne_charge_admissible_federale_vers_dict(
                personne_charge_admissible_federale
            )
        ),
        "accessibilite_domiciliaire_federale": (
            _accessibilite_domiciliaire_federale_vers_dict(
                accessibilite_domiciliaire_federale
            )
        ),
        "achat_habitation_federal": (
            _achat_habitation_federal_vers_dict(
                achat_habitation_federal
            )
        ),
        "aidant_autre_personne_charge_federal": (
            _aidant_autre_personne_charge_federal_vers_dict(
                aidant_autre_personne_charge_federal
            )
        ),
        "aidant_conjoint_personne_charge_federal": (
            _aidant_conjoint_personne_charge_federal_vers_dict(
                aidant_conjoint_personne_charge_federal
            )
        ),
        "aidant_enfant_federal": (
            _aidant_enfant_federal_vers_dict(
                aidant_enfant_federal
            )
        ),
        "rapport_pdf": _chemin_vers_stockage(Path(rapport_pdf)) if rapport_pdf else None,
    }

    calculer_transferts_handicap_2025(handicap_transfere,
        beneficiaire=dossier.client, annee=dossier.annee_fiscale,
        reclame_30400=contenu["personne_charge_admissible_federale"]["reclamer_montant"],
        reclame_30450=contenu["aidant_autre_personne_charge_federal"]["reclamer_montant"],
        deduction_22000=pension_alimentaire_effective.deduction_federale_22000)
    verifier_combinaison_medicale_famille(medical_familial,
        _frais_medicaux_depuis_dict(contenu["frais_medicaux"]), act.present and not act.famille.activer)
    _verifier_prestations_familiales_stockees(contenu, dossier, medical_familial)
    _verifier_enfant_5v_stocke(contenu)
    _verifier_annexe_b_6a_stockee(contenu)
    _verifier_enfants_conjoints_5ab_stockes(contenu, dossier)
    temporaire = chemin.with_suffix(chemin.suffix + ".tmp")
    try:
        temporaire.write_text(json.dumps(contenu, ensure_ascii=False, indent=2), encoding="utf-8")
        temporaire.replace(chemin)
    finally:
        try:
            temporaire.unlink()
        except OSError:
            pass
    return chemin


def _decimal_depuis_json(valeur: Any, nom: str) -> Decimal:
    try:
        resultat = Decimal(str(valeur))
    except (InvalidOperation, ValueError, TypeError) as erreur:
        raise ValueError(f"Valeur décimale invalide pour {nom}.") from erreur
    if not resultat.is_finite():
        raise ValueError(f"Valeur décimale non finie pour {nom}.")
    return resultat


def charger_dossier_fiscal(source: Path | str) -> DossierFiscalEnregistre:
    chemin = Path(source)
    try:
        contenu = json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as erreur:
        raise ValueError(f"Dossier fiscal illisible : {chemin.name}") from erreur
    return dossier_fiscal_depuis_contenu(contenu, chemin=chemin)


def dossier_fiscal_depuis_contenu(contenu, *, chemin=Path("."), verifier_documents=True):
    """Même validation que le chargement fichier; mode sans accès aux pièces sources."""
    if not isinstance(contenu, dict) or contenu.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Version de dossier fiscal non prise en charge.")

    try:
        client = " ".join(str(contenu["client"]).split())
        annee = int(contenu["annee_fiscale"])
        province = str(contenu["province"])
        sauvegarde_le = str(contenu["sauvegarde_le"])
        documents_json = contenu["documents"]
        donnees_json = contenu["donnees_validees"]
    except (KeyError, TypeError, ValueError) as erreur:
        raise ValueError("Le dossier fiscal enregistré est incomplet.") from erreur

    if not client or annee < 2000 or annee > 2100:
        raise ValueError("Identité du dossier fiscal enregistrée invalide.")
    if province.strip().casefold() not in {"québec", "quebec"}:
        raise ValueError("Cette version accepte uniquement les dossiers Québec.")
    if not isinstance(documents_json, list) or not isinstance(donnees_json, list) or not donnees_json:
        raise ValueError("Le dossier fiscal enregistré ne contient pas de données valides.")

    documents = tuple(Path(str(v)) for v in documents_json)
    donnees = []
    for index, brut in enumerate(donnees_json):
        if not isinstance(brut, dict):
            raise ValueError("Une donnée fiscale enregistrée est invalide.")
        try:
            statut = str(brut["statut"])
            type_document = str(brut["type_document"])
            document = Path(str(brut["document"]))
            case = str(brut["case"])
            libelle = str(brut["libelle"])
            corrigee = bool(brut["corrigee"])
        except KeyError as erreur:
            raise ValueError("Une donnée fiscale enregistrée est incomplète.") from erreur
        if statut not in STATUTS_VALIDATION_AUTORISES:
            raise ValueError("Statut de validation fiscale enregistré invalide.")
        if type_document not in {"T4", "RL-1", "T4E", "RL-6", "T4A(P)", "RL-2", "T4A(OAS)", "T4A", "T4RIF", "T3", "T5", "RL-16", "T4RSP", "T5007", "RL-5", "RL-3", "INTERETS", "T5008", "RL-18"}:
            raise ValueError("Type de document fiscal enregistré non pris en charge.")
        ve = _decimal_depuis_json(brut.get("valeur_extraite"), f"valeur_extraite[{index}]")
        vv = _decimal_depuis_json(brut.get("valeur_validee"), f"valeur_validee[{index}]")
        if ve < 0 or vv < 0:
            raise ValueError("Une valeur fiscale enregistrée ne peut pas être négative.")
        donnees.append(DonneeFiscaleValidee(
            document=document,
            type_document=type_document,
            case=case,
            libelle=libelle,
            valeur_extraite=ve,
            valeur_validee=vv,
            corrigee=corrigee,
            statut=statut,
        ))

    dossier = DossierFiscalValide(
        client=client,
        annee_fiscale=annee,
        province="Québec",
        documents=documents,
        donnees_validees=tuple(donnees),
    )

    estimation = None
    e = contenu.get("derniere_estimation")
    if e is not None:
        if not isinstance(e, dict):
            raise ValueError("Le résumé d'estimation enregistré est invalide.")
        estimation = ResumeEstimationSauvegardee(
            resultat=str(e.get("resultat", "")),
            montant=_decimal_depuis_json(e.get("montant"), "estimation.montant"),
            impot_total_preliminaire=_decimal_depuis_json(e.get("impot_total_preliminaire"), "estimation.impot_total_preliminaire"),
            retenues_totales=_decimal_depuis_json(e.get("retenues_totales"), "estimation.retenues_totales"),
        )

    ajustement_reer = _ajustement_reer_depuis_dict(
        contenu.get("ajustement_reer")
    )
    deduction_celiapp = _deduction_celiapp_depuis_dict(
        contenu.get("deduction_celiapp")
    )
    frais_garde_federaux = _frais_garde_federaux_depuis_dict(
        contenu.get("frais_garde_federaux")
    )
    depenses_emploi = _depenses_emploi_depuis_dict(
        contenu.get("depenses_emploi")
    )
    frais_demenagement = _frais_demenagement_depuis_dict(
        contenu.get("frais_demenagement")
    )
    pension_alimentaire_payee = _pension_alimentaire_payee_depuis_dict(
        contenu.get("pension_alimentaire_payee")
    )
    autres_deductions = _autres_deductions_depuis_dict(
        contenu.get("autres_deductions")
    )
    cotisations_syndicales = _cotisations_syndicales_depuis_dict(
        contenu.get("cotisations_syndicales")
    )
    dons_bienfaisance = _dons_bienfaisance_depuis_dict(
        contenu.get("dons_bienfaisance")
    )
    frais_medicaux = _frais_medicaux_depuis_dict(
        contenu.get("frais_medicaux")
    )
    frais_scolarite = _frais_scolarite_depuis_dict(
        contenu.get("frais_scolarite")
    )
    credit_deficience = _credit_deficience_depuis_dict(
        contenu.get("credit_deficience")
    )
    assurance_medicaments = _assurance_medicaments_depuis_dict(
        contenu.get("assurance_medicaments")
    )
    cotisations_excedentaires = _cotisations_excedentaires_depuis_dict(
        contenu.get("cotisations_excedentaires")
    )
    personne_vivant_seule = _personne_vivant_seule_depuis_dict(
        contenu.get("personne_vivant_seule")
    )
    montants_age_retraite = _montants_age_retraite_depuis_dict(
        contenu.get("montants_age_retraite")
    )
    credits_federaux_age_pension = _credits_federaux_age_pension_depuis_dict(
        contenu.get("credits_federaux_age_pension")
    )
    montant_conjoint_federal = _montant_conjoint_federal_depuis_dict(
        contenu.get("montant_conjoint_federal")
    )
    personne_charge_admissible_federale = (
        _personne_charge_admissible_federale_depuis_dict(
            contenu.get("personne_charge_admissible_federale")
        )
    )
    accessibilite_domiciliaire_federale = (
        _accessibilite_domiciliaire_federale_depuis_dict(
            contenu.get("accessibilite_domiciliaire_federale")
        )
    )
    achat_habitation_federal = (
        _achat_habitation_federal_depuis_dict(
            contenu.get("achat_habitation_federal")
        )
    )
    aidant_autre_personne_charge_federal = (
        _aidant_autre_personne_charge_federal_depuis_dict(
            contenu.get("aidant_autre_personne_charge_federal")
        )
    )
    aidant_conjoint_personne_charge_federal = (
        _aidant_conjoint_personne_charge_federal_depuis_dict(
            contenu.get("aidant_conjoint_personne_charge_federal")
        )
    )
    aidant_enfant_federal = (
        _aidant_enfant_federal_depuis_dict(
            contenu.get("aidant_enfant_federal")
        )
    )
    rapport = Path(str(contenu["rapport_pdf"])) if contenu.get("rapport_pdf") else None
    manquants = tuple(x for x in documents if not x.exists()) if verifier_documents else ()
    rpa = _rpa_depuis_dict(contenu["cotisations_rpa"]) if "cotisations_rpa" in contenu else CotisationsRpa2025()
    if rpa.montant_federal:
        verifier_rpa_dossier_2025(dossier, rpa)
    confirme = valider_confirmation_rqap(contenu.get("rqap_confirme", False))
    if confirme:
        consolider_prestations_rqap_2025(dossier, confirme)
    confirme_ae = valider_confirmation_ae(contenu.get("ae_confirme", False))
    if confirme_ae and confirme:
        raise ValueError("AE et RQAP simultanés : hors périmètre.")
    if confirme_ae:
        consolider_prestations_ae_2025(dossier, True)
    confirme_rrq_rpc = valider_confirmation_rrq_rpc(contenu.get("rrq_rpc_confirme", False))
    if confirme_rrq_rpc:
        if confirme or confirme_ae:
            raise ValueError("RRQ/RPC avec AE/RQAP : hors périmètre.")
        consolider_prestations_rrq_rpc_2025(dossier, True)
    confirme_psv = valider_confirmation_psv(contenu.get("psv_confirme", False))
    if confirme_psv:
        if confirme or confirme_ae or confirme_rrq_rpc:
            raise ValueError("PSV avec AE/RQAP/RRQ : hors périmètre.")
        consolider_prestations_psv_2025(dossier, True)
    try:
        placement_etranger_profil = ProfilPlacementEtranger2025(
            **contenu.get("profil_placement_etranger", {})
        )
    except (TypeError, ValueError) as erreur:
        raise ValueError("Profil placement étranger enregistré invalide.") from erreur
    valider_profil_placement_etranger_2025(placement_etranger_profil)

    credit_brut = contenu.get("profil_credit_impot_etranger", {})
    if not isinstance(credit_brut, dict):
        raise ValueError("Profil crédit étranger enregistré invalide.")
    try:
        credit_etranger_profil = ProfilCreditImpotEtranger2025(
            credit_federal_40500=_decimal_depuis_json(
                credit_brut.get("credit_federal_40500", "0"),
                "profil_credit_impot_etranger.credit_federal_40500",
            ),
            credit_quebec_409=_decimal_depuis_json(
                credit_brut.get("credit_quebec_409", "0"),
                "profil_credit_impot_etranger.credit_quebec_409",
            ),
            source_t2209=str(credit_brut.get("source_t2209", "")),
            source_tp772=str(credit_brut.get("source_tp772", "")),
            confirme=credit_brut.get("confirme", False),
        )
    except (TypeError, ValueError) as erreur:
        raise ValueError("Profil crédit étranger enregistré invalide.") from erreur

    if placement_etranger_profil != ProfilPlacementEtranger2025():
        placement_etranger_resultat = consolider_placement_etranger_2025(
            dossier, placement_etranger_profil
        )
        valider_profil_credit_impot_etranger_2025(
            credit_etranger_profil, placement_etranger_resultat
        )
    elif credit_etranger_profil != ProfilCreditImpotEtranger2025():
        raise ValueError("Profil crédit étranger présent sans placement étranger.")

    try:
        pensions_profil = ProfilPensions2025(**contenu.get("profil_pensions", {}))
    except (TypeError, ValueError) as erreur:
        raise ValueError("Profil pensions enregistré invalide.") from erreur
    valider_profil_pensions_2025(pensions_profil)
    if pensions_profil.confirme:
        if any((confirme_psv, confirme, confirme_ae, confirme_rrq_rpc)):
            raise ValueError("Pensions avec d'autres prestations hors périmètre.")
        consolider_pensions_2025(dossier, pensions_profil)
    try:
        retraits_profil = ProfilRetraits2025(**contenu.get("profil_retraits", {}))
    except (TypeError, ValueError) as erreur:
        raise ValueError("Profil retraits enregistré invalide.") from erreur
    valider_profil_retraits_2025(retraits_profil)
    if retraits_profil.confirme:
        if any((confirme_psv, confirme, confirme_ae, confirme_rrq_rpc, pensions_profil.confirme)):
            raise ValueError("Retraits avec autres prestations : hors périmètre.")
        consolider_retraits_2025(dossier, retraits_profil)
    try:
        remplacement_profil = ProfilRemplacement2025(**contenu.get("profil_remplacement", {}))
    except (TypeError, ValueError) as erreur:
        raise ValueError("Profil remplacement enregistré invalide.") from erreur
    valider_profil_remplacement_2025(remplacement_profil)
    if remplacement_profil.confirme:
        if any((confirme_psv, confirme, confirme_ae, confirme_rrq_rpc, pensions_profil.confirme, retraits_profil.confirme)):
            raise ValueError("Remplacement avec autres prestations : hors périmètre.")
        consolider_remplacement_2025(dossier, remplacement_profil)
    try:
        interets_profil = ProfilInterets2025(**contenu.get("profil_interets", {}))
    except (TypeError, ValueError) as erreur:
        raise ValueError("Profil intérêts enregistré invalide.") from erreur
    valider_profil_interets_2025(interets_profil)
    combinaison_3h_a_chargee = interets_profil.confirme
    try:
        dividendes_profil = ProfilDividendes2025(**contenu.get("profil_dividendes", {}))
    except (TypeError, ValueError) as erreur:
        raise ValueError("Profil dividendes enregistré invalide.") from erreur
    valider_profil_dividendes_2025(dividendes_profil)
    combinaison_3h_a_chargee = (
        combinaison_3h_a_chargee and dividendes_profil.confirme
    )
    if combinaison_3h_a_chargee:
        if any((confirme_psv, confirme, confirme_ae, confirme_rrq_rpc, pensions_profil.confirme, retraits_profil.confirme, remplacement_profil.confirme)):
            raise ValueError("Combinaison intérêts + dividendes avec autre parcours : hors périmètre 3H.")
        # Consolidation différée après lecture du profil capital afin de
        # distinguer 3H-A/3H-B de 3H-C.
    else:
        if interets_profil.confirme:
            if any((confirme_psv, confirme, confirme_ae, confirme_rrq_rpc, pensions_profil.confirme, retraits_profil.confirme, remplacement_profil.confirme)):
                raise ValueError("Intérêts avec autres prestations : hors périmètre 3A.")
            consolider_interets_2025(dossier, interets_profil)
        if dividendes_profil.confirme:
            if any((confirme_psv, confirme, confirme_ae, confirme_rrq_rpc)) or any(p != type(p)() for p in (pensions_profil, retraits_profil, remplacement_profil, interets_profil)):
                raise ValueError("Dividendes avec autres placements/prestations : hors périmètre 3C.")
            consolider_dividendes_2025(dossier, dividendes_profil)
    try:
        capital_profil = ProfilCapital2025(**contenu.get("profil_capital", {}))
    except (TypeError, ValueError) as erreur:
        raise ValueError("Profil capital enregistré invalide.") from erreur
    valider_profil_capital_2025(capital_profil)
    if combinaison_3h_a_chargee:
        if capital_profil.confirme:
            consolider_interets_dividendes_capital_2025(
                dossier,
                interets_profil,
                dividendes_profil,
                capital_profil,
            )
        else:
            consolider_interets_dividendes_2025(
                dossier,
                interets_profil,
                dividendes_profil,
            )
    elif capital_profil.confirme:
        if any((confirme_psv, confirme, confirme_ae, confirme_rrq_rpc)) or any(p != type(p)() for p in (pensions_profil, retraits_profil, remplacement_profil, interets_profil, dividendes_profil)):
            raise ValueError("Capital avec autres placements/prestations : hors périmètre 3D.")
        consolider_capital_2025(dossier, capital_profil)
    try:
        frais_profil = ProfilFraisPlacement2025(**contenu.get("profil_frais_placement", {}))
    except (TypeError, ValueError) as erreur:
        raise ValueError("Profil frais de placement enregistré invalide.") from erreur
    verifier_confirmation_frais_2025(
        frais_profil,
        dossier,
        interets_profil,
        dividendes_profil,
        capital_profil,
    )
    try:
        pertes_profil = ProfilReportsPertes2025(**contenu.get("profil_reports_pertes", {}))
    except (TypeError, ValueError) as erreur:
        raise ValueError("Profil reports de pertes enregistré invalide.") from erreur
    verifier_confirmation_reports_pertes_2025(pertes_profil, dossier, capital_profil, frais_profil)
    medical_familial = medical_familial_depuis_dict(contenu.get("frais_medicaux_famille"))
    calculer_medical_familial_2025(medical_familial, demandeur=dossier.client, revenu_net=Decimal(0), annee=dossier.annee_fiscale)
    act = _allocation_travailleurs_depuis_dict(contenu.get("allocation_travailleurs"))
    verifier_combinaison_medicale_famille(medical_familial, frais_medicaux, act.present and not act.famille.activer)
    _verifier_prestations_familiales_stockees(contenu, dossier, medical_familial)
    _verifier_enfant_5v_stocke(contenu)
    _verifier_annexe_b_6a_stockee(contenu)
    _verifier_enfants_conjoints_5ab_stockes(contenu, dossier)
    handicap_transfere = transferts_handicap_depuis_dict(contenu.get("transferts_handicap"))
    calculer_transferts_handicap_2025(handicap_transfere,
        beneficiaire=dossier.client, annee=dossier.annee_fiscale,
        reclame_30400=personne_charge_admissible_federale.reclamer_montant,
        reclame_30450=aidant_autre_personne_charge_federal.reclamer_montant,
        deduction_22000=pension_alimentaire_payee.deduction_federale_22000)
    return DossierFiscalEnregistre(
        frais_medicaux_famille=medical_familial,
        transferts_handicap=handicap_transfere,
        profil_reports_pertes=pertes_profil,
        profil_frais_placement=frais_profil,
        profil_capital=capital_profil,
        profil_dividendes=dividendes_profil,
        profil_interets=interets_profil,
        profil_placement_etranger=placement_etranger_profil,
        profil_credit_impot_etranger=credit_etranger_profil,
        profil_remplacement=remplacement_profil,
        profil_retraits=retraits_profil,
        profil_pensions=pensions_profil,
        psv_confirme=confirme_psv,
        rrq_rpc_confirme=confirme_rrq_rpc,
        ae_confirme=confirme_ae,
        rqap_confirme=confirme,
        cotisations_rpa=rpa,
        chemin=chemin,
        dossier=dossier,
        sauvegarde_le=sauvegarde_le,
        estimation=estimation,
        rapport_pdf=rapport,
        documents_manquants=manquants,
        ajustement_reer=ajustement_reer,
        deduction_celiapp=deduction_celiapp,
        frais_garde_federaux=frais_garde_federaux,
        depenses_emploi=depenses_emploi,
        frais_demenagement=frais_demenagement,
        pension_alimentaire_payee=pension_alimentaire_payee,
        renovations_multigenerationnelles=multigenerationnel_depuis_dict(contenu.get("renovations_multigenerationnelles"), annee=dossier.annee_fiscale,
            autres_frais_reclames=bool(medical_familial.depenses or frais_medicaux.montant_admissible_federal or accessibilite_domiciliaire_federale.depenses_admissibles)),
        fournitures_educateur=educateur_depuis_dict(contenu.get("fournitures_educateur"), annee=dossier.annee_fiscale, deduction_t777=depenses_emploi.deduction_federale_t777),
        fonds_travailleurs=fonds_depuis_dict(contenu.get("fonds_travailleurs"), client=dossier.client, annee=dossier.annee_fiscale),
        contributions_politiques=politiques_depuis_dict(contenu.get("contributions_politiques"), client=dossier.client, annee=dossier.annee_fiscale),
        adoption=adoption_depuis_dict(contenu.get("adoption"), dossier.annee_fiscale),
        benevoles=_benevoles_depuis_dict(contenu.get("benevoles"), dossier),
        transfert_conjoint=_transfert_conjoint_depuis_dict(contenu.get("transfert_conjoint"), dossier.client),
        transferts_scolarite_recus=_scolarite_recue_depuis_dict(contenu.get("transferts_scolarite_recus")),
        allocation_travailleurs=_allocation_travailleurs_depuis_dict(contenu.get("allocation_travailleurs")),
        frais_garde_quebec=garde_quebec_depuis_dict(contenu.get("frais_garde_quebec")),
        soutien_aines_quebec=soutien_aines_depuis_dict(contenu.get("soutien_aines_quebec")),
        volontaires_quebec=volontaires_depuis_dict(contenu.get("volontaires_quebec")),
        maintien_domicile_quebec=maintien_domicile_depuis_dict(contenu.get("maintien_domicile_quebec")),
        prime_travail_quebec=prime_travail_depuis_dict(contenu.get("prime_travail_quebec")),
        solidarite_quebec=solidarite_quebec_depuis_dict(contenu.get("solidarite_quebec")),
        personne_aidante_quebec=aidante_quebec_depuis_dict(contenu.get("personne_aidante_quebec")),
        medical_remboursable_quebec=medical_remboursable_quebec_depuis_dict(contenu.get("medical_remboursable_quebec")),
        prolongation_carriere_quebec=carriere_quebec_depuis_dict(contenu.get("prolongation_carriere_quebec")),
        achat_habitation_quebec=achat_quebec_depuis_dict(contenu.get("achat_habitation_quebec")),
        interets_etudiants_quebec=interets_quebec_depuis_dict(contenu.get("interets_etudiants_quebec")),
        interets_pret_etudiant=_interets_pret_etudiant_depuis_dict(contenu.get("interets_pret_etudiant")),
        autres_deductions=autres_deductions,
        cotisations_syndicales=cotisations_syndicales,
        dons_bienfaisance=dons_bienfaisance,
        frais_medicaux=frais_medicaux,
        frais_scolarite=frais_scolarite,
        credit_deficience=credit_deficience,
        assurance_medicaments=assurance_medicaments,
        cotisations_excedentaires=cotisations_excedentaires,
        personne_vivant_seule=personne_vivant_seule,
        montants_age_retraite=montants_age_retraite,
        credits_federaux_age_pension=(
            credits_federaux_age_pension
        ),
        montant_conjoint_federal=(
            montant_conjoint_federal
        ),
        personne_charge_admissible_federale=(
            personne_charge_admissible_federale
        ),
        accessibilite_domiciliaire_federale=(
            accessibilite_domiciliaire_federale
        ),
        achat_habitation_federal=(
            achat_habitation_federal
        ),
        aidant_autre_personne_charge_federal=(
            aidant_autre_personne_charge_federal
        ),
        aidant_conjoint_personne_charge_federal=(
            aidant_conjoint_personne_charge_federal
        ),
        aidant_enfant_federal=(
            aidant_enfant_federal
        ),
    )


def lister_dossiers_fiscaux(dossier: Path | str = DOSSIERS_FISCAUX_DIR):
    racine = Path(dossier)
    if not racine.exists():
        return ()
    resultats = []
    for chemin in racine.glob("*.json"):
        try:
            resultats.append(charger_dossier_fiscal(chemin))
        except ValueError:
            continue
    return tuple(sorted(resultats, key=lambda x: (x.sauvegarde_le, x.chemin.name), reverse=True))


def _verifier_enfant_5v_stocke(contenu):
    personne = _personne_charge_admissible_federale_depuis_dict(contenu.get("personne_charge_admissible_federale"))
    aidant = _aidant_enfant_federal_depuis_dict(contenu.get("aidant_enfant_federal"))
    if personne.enfant_infirmite_ligne30500 or aidant.enfant_reclame_30400 or aidant.enfants_detailles:
        verifier_combinaison_30400_30500_2025(personne, aidant)


def _verifier_enfants_conjoints_5ab_stockes(contenu, dossier):
    from .tax_federal_caregiver_child_2025 import verifier_attribution_enfants_conjoints_30500_2025
    aidant = _aidant_enfant_federal_depuis_dict(contenu.get("aidant_enfant_federal"))
    if not aidant.reclamer_montant or not contenu.get("transfert_conjoint", {}).get("activer", False):
        return
    conjoint = _transfert_conjoint_depuis_dict(contenu.get("transfert_conjoint"), dossier.client)
    resultat = calculer_transfert_conjoint_2025(conjoint, beneficiaire=dossier.client)
    verifier_attribution_enfants_conjoints_30500_2025(aidant, resultat)


def _verifier_types_annexe_b_6a(valeur, defaults):
    if "combinaison_annexe_b_confirmee" not in valeur:
        return
    if set(valeur) - {f.name for f in fields(defaults)}:
        raise ValueError("Clé inconnue dans l'annexe B.")
    for nom, v in valeur.items():
        defaut = getattr(defaults, nom)
        if isinstance(defaut, (bool, str, int)) and type(v) is not type(defaut):
            raise ValueError("Type JSON annexe B invalide : " + nom)
        if isinstance(defaut, Decimal) and type(v) not in (str, int):
            raise ValueError("Montant JSON annexe B invalide : " + nom)


def _verifier_annexe_b_6a_stockee(contenu):
    from .tax_quebec_schedule_b_2025 import calculer_annexe_b_combinee_2025
    seule = _personne_vivant_seule_depuis_dict(contenu.get("personne_vivant_seule"))
    age = _montants_age_retraite_depuis_dict(contenu.get("montants_age_retraite"))
    calculer_annexe_b_combinee_2025(seule, age)
