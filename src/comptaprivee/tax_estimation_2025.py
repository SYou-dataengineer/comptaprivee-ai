"""Orchestration de l'estimation fiscale locale 2025.

Ce module relie les briques déjà validées :
dossier fiscal verrouillé -> consolidation -> revenu -> fédéral -> Québec
-> rapprochement.

Il ne transmet aucune déclaration et conserve explicitement le statut
d'estimation soumise à validation comptable.
"""

from .tax_quebec_career_extension_2025 import (ProlongationCarriereQuebec2025, ResultatCarriereQuebec2025,
    calculer_carriere_quebec_2025, appliquer_carriere_quebec_2025, lignes_carriere_quebec_2025)
from .tax_quebec_home_buyers_2025 import (AchatHabitationQuebec2025, ResultatAchatQuebec2025,
    calculer_achat_quebec_2025, appliquer_achat_quebec_2025, lignes_achat_quebec_2025)
from .tax_quebec_student_interest_2025 import (InteretsEtudiantsQuebec2025, ResultatInteretsQuebec2025,
    calculer_interets_quebec_2025, appliquer_interets_quebec_2025, lignes_interets_quebec_2025)
from .tax_medical_expenses_2025 import montant_frais_medicaux_quebec_apres_seuil_2025
from .tax_rules_2025 import arrondir_cent
from .tax_quebec_schedule_b_2025 import calculer_annexe_b_combinee_2025, appliquer_annexe_b_combinee_2025, lignes_annexe_b_combinee_2025
from .tax_federal_caregiver_child_2025 import verifier_combinaison_30400_30500_2025, verifier_attribution_enfants_conjoints_30500_2025
from .tax_family_workers_benefit_2025 import verifier_concordance_act_familial_2025
from .tax_family_medical_2025 import (FraisMedicauxFamilleFederaux2025, ResultatMedicalFamilial2025, calculer_medical_familial_2025, lignes_medical_familial_2025, verifier_combinaison_medicale_famille)
from .tax_disability_transfer_2025 import (TransfertsHandicap2025, ResultatTransfertsHandicap2025, calculer_transferts_handicap_2025)
from .tax_disability_transfer_2025 import lignes_transferts_handicap_2025
from .tax_multigenerational_renovation_2025 import (RenovationsMultigenerationnelles2025, ResultatMultigenerationnel2025, calculer_multigenerationnel_2025, lignes_multigenerationnelles_2025, multigenerationnel_vers_dict, multigenerationnel_depuis_dict)
from .tax_educator_supplies_2025 import (FournituresEducateur2025, ResultatFournituresEducateur2025, calculer_fournitures_educateur_2025, lignes_fournitures_educateur_2025)
from .tax_labour_funds_2025 import (FondsTravailleurs2025, ResultatFondsTravailleurs2025, calculer_fonds_travailleurs_2025, fonds_vers_dict, fonds_depuis_dict, verifier_fonds_conjoint_2025, lignes_fonds_travailleurs_2025)
from .tax_political_contributions_2025 import (ContributionsPolitiques2025, ResultatContributionsPolitiques2025, calculer_contributions_politiques_2025, lignes_contributions_politiques_2025, politiques_depuis_dict, verifier_recus_politiques_conjoint_2025)
from .tax_adoption_2025 import Adoption2025, ResultatAdoption2025, calculer_adoption_2025, lignes_adoption_2025
from .tax_volunteers_2025 import Benevoles2025, ResultatBenevoles2025, calculer_benevoles_2025, lignes_benevoles_2025
from .tax_spouse_transfer_2025 import (TransfertConjointFederal2025, ResultatTransfertConjoint2025, calculer_transfert_conjoint_2025, lignes_transfert_conjoint_2025)
from .tax_tuition_received_2025 import TransfertsScolariteRecus2025, valider_transferts_scolarite_recus_2025, montant_ligne_32400_2025, lignes_transferts_scolarite_recus_2025
from .tax_donation_carryforward_2025 import ResultatReportsDonsFederaux2025, calculer_reports_dons_federaux_2025, lignes_reports_dons_federaux_2025
from .tax_donations_2025 import montant_dons_federaux_reclames_2025
from dataclasses import dataclass, replace
from decimal import Decimal

from .tax_tuition_carryforward_2025 import (
    ResultatReportsScolariteFederaux2025, calculer_reports_scolarite_federaux_2025,
    lignes_reports_scolarite_federaux_2025,
)
from .tax_workers_benefit_2025 import (
    AllocationTravailleurs2025, ResultatAllocationTravailleurs2025,
    valider_allocation_travailleurs_2025, calculer_allocation_travailleurs_2025,
    lignes_allocation_travailleurs_2025,
)
from .tax_medical_supplement_2025 import (ResultatSupplementMedical2025, calculer_supplement_medical_2025, lignes_supplement_medical_2025, verifier_famille_supplement_2025)
from .tax_training_credit_2025 import credit_formation_2025, lignes_formation_2025
from .tax_student_loan_interest_2025 import (
    InteretsPretEtudiant2025, ResultatInteretsPretEtudiant2025,
    valider_interets_pret_etudiant_2025, repartir_interets_pret_etudiant_2025,
    mesurer_incidence_interets_2025, lignes_resume_interets_pret_etudiant_2025,
)
from .tax_age_retirement_2025 import (
    MontantsAgeRetraite2025,
    appliquer_credit_quebec_age_retraite_2025,
    credit_quebec_age_retraite_2025,
    montant_age_2025,
    montant_ligne_361_age_retraite_2025,
    montant_revenus_retraite_2025,
    revenu_retraite_net_admissible_2025,
    valider_montants_age_retraite_2025,
)
from .tax_adjustments_2025 import (
    AjustementReer2025,
    appliquer_ajustement_reer_2025,
)
from .tax_fhsa_2025 import (
    DeductionCeliapp2025,
    appliquer_deduction_celiapp_2025,
    lignes_resume_celiapp_2025,
)
from .tax_child_care_2025 import (
    FraisGardeFederaux2025,
    appliquer_frais_garde_federaux_2025,
    lignes_resume_frais_garde_federaux_2025,
)
from .tax_employment_expenses_2025 import (
    DepensesEmploi2025,
    appliquer_depenses_emploi_2025,
    lignes_resume_depenses_emploi_2025,
)
from .tax_moving_expenses_2025 import (
    FraisDemenagement2025,
    appliquer_frais_demenagement_2025,
    lignes_resume_frais_demenagement_2025,
)
from .tax_support_payments_2025 import (
    PensionAlimentairePayee2025,
    appliquer_pension_alimentaire_payee_2025,
    lignes_resume_pension_alimentaire_payee_2025,
)
from .tax_other_deductions_2025 import (
    AutresDeductions2025,
    appliquer_autres_deductions_2025,
    lignes_resume_autres_deductions_2025,
)
from .tax_contribution_overpayments_2025 import (
    CotisationsExcedentaires2025,
    calculer_remboursements_cotisations_2025,
    valider_cotisations_excedentaires_2025,
)
from .tax_donations_2025 import (
    valider_plafond_dons_monetaire_federal_2025,
    DonsBienfaisance2025,
    appliquer_credit_federal_dons_2025,
    appliquer_credit_quebec_dons_2025,
    credit_federal_dons_2025,
    credit_quebec_dons_2025,
)
from .tax_federal_top_up_2025 import (
    calculer_base_33500_2025,
    calculer_annexe9_ligne22_2025,
    calculer_credits_non_remboursables_2025,
    lignes_resume_credit_compensatoire_2025,
)
from .tax_disability_2025 import (
    montant_federal_handicap_2025,
    lignes_handicap_detaille_2025,
    CreditDeficience2025,
    appliquer_credit_federal_handicap_2025,
    appliquer_credit_quebec_deficience_2025,
    credit_federal_handicap_2025,
    credit_quebec_deficience_2025,
)
from .tax_drug_insurance_2025 import (
    AssuranceMedicamentsQuebec2025,
    code_exemption_case_449_2025,
    cotisation_assurance_medicaments_2025,
    valider_assurance_medicaments_2025,
)
from .tax_living_alone_2025 import (
    PersonneVivantSeule2025,
    appliquer_credit_quebec_personne_vivant_seule_2025,
    credit_quebec_personne_vivant_seule_2025,
    montant_ligne_361_personne_vivant_seule_2025,
    valider_personne_vivant_seule_2025,
)
from .tax_medical_expenses_2025 import (
    FraisMedicaux2025,
    montant_frais_medicaux_federal_apres_seuil_2025,
    appliquer_credit_federal_frais_medicaux_2025,
    appliquer_credit_quebec_frais_medicaux_2025,
    credit_federal_frais_medicaux_2025,
    credit_quebec_frais_medicaux_2025,
)
from .tax_tuition_2025 import (
    valider_frais_scolarite_2025,
    FraisScolarite2025,
    appliquer_credit_federal_frais_scolarite_2025,
    appliquer_credit_quebec_frais_scolarite_2025,
    credit_federal_frais_scolarite_2025,
    credit_quebec_frais_scolarite_2025,
)
from .tax_engine_input_2025 import (
    BaseFiscaleEmploi2025,
    consolider_base_fiscale_emploi_2025,
)
from .tax_federal_home_accessibility_2025 import (
    description_partage_31285_2025,
    DepensesAccessibiliteDomiciliaireFederal2025,
    appliquer_credit_federal_ligne_31285_2025,
    credit_federal_ligne_31285_2025,
    montant_ligne_31285_2025,
    valider_depenses_accessibilite_domiciliaire_2025,
)
from .tax_federal_home_buyers_2025 import (
    description_partage_31270_2025,
    MontantAchatHabitationFederal2025,
    appliquer_credit_federal_ligne_31270_2025,
    credit_federal_ligne_31270_2025,
    montant_ligne_31270_2025,
    valider_montant_achat_habitation_2025,
)
from .tax_federal_caregiver_other_dependant_2025 import (
    description_partage_30450_2025,
    details_personnes_30450_2025,
    AidantNaturelAutrePersonneChargeFederal2025,
    appliquer_credit_federal_ligne_30450_2025,
    credit_federal_ligne_30450_2025,
    montant_ligne_30450_2025,
    nombre_personnes_charge_ligne_51120_2025,
    valider_aidant_naturel_30450_2025,
)
from .tax_federal_caregiver_spouse_dependant_2025 import (
    montant_ligne_30425_2025,
    TYPE_CONJOINT,
    TYPE_PERSONNE_CHARGE_ADMISSIBLE,
    AidantNaturelConjointOuPersonneChargeFederal2025,
    appliquer_credit_federal_ligne_30425_2025,
    valider_aidant_naturel_30425_2025,
)
from .tax_federal_caregiver_child_2025 import (
    details_enfants_30500_2025,
    AidantNaturelEnfantMoins18Federal2025,
    appliquer_credit_federal_aidant_enfant_moins18_2025,
    credit_federal_aidant_enfant_moins18_2025,
    montant_ligne_30500_2025,
    nombre_enfants_ligne_30499_2025,
    valider_aidant_naturel_enfant_moins18_federal_2025,
)
from .tax_federal_eligible_dependant_2025 import (
    MontantPersonneChargeAdmissibleFederal2025,
    appliquer_credit_federal_personne_charge_admissible_2025,
    credit_federal_personne_charge_admissible_2025,
    montant_ligne_30400_2025,
    valider_montant_personne_charge_admissible_federal_2025,
)
from .tax_federal_spouse_2025 import (
    MontantConjointFederal2025,
    appliquer_credit_federal_montant_conjoint_2025,
    credit_federal_montant_conjoint_2025,
    montant_ligne_30300_2025,
    valider_montant_conjoint_federal_2025,
)
from .tax_federal_age_pension_2025 import (
    CreditsFederauxAgePension2025,
    appliquer_credit_federal_age_pension_2025,
    credit_federal_age_pension_2025,
    montant_age_federal_2025,
    montant_pension_federal_2025,
    valider_credits_federaux_age_pension_2025,
)
from .tax_federal_2025 import (
    ImpotFederalPreliminaire2025,
    finaliser_credits_federaux_2025,
    calculer_impot_federal_preliminaire_2025,
)
from .tax_income_2025 import (
    RevenuNetImposable2025,
    calculer_revenu_net_imposable_2025,
)
from .tax_quebec_2025 import (
    ImpotQuebecPreliminaire2025,
    calculer_impot_quebec_preliminaire_2025,
)
from .tax_reconciliation_2025 import (
    RapprochementFiscal2025,
    calculer_rapprochement_fiscal_2025,
)
from .tax_union_dues_2025 import (
    CotisationsSyndicalesProfessionnelles2025,
    appliquer_credit_quebec_cotisations_2025,
    appliquer_deduction_federale_cotisations_2025,
    credit_quebec_cotisations_2025,
)
from .tax_validated_case import DossierFiscalValide
from .tax_capital_loss_carryovers_2025 import (ProfilReportsPertes2025, ReportsPertes2025, verifier_confirmation_reports_pertes_2025, appliquer_reports_pertes_2025, lignes_resume_reports_pertes_2025)
from .tax_investment_expenses_2025 import (ProfilFraisPlacement2025, FraisPlacement2025, verifier_confirmation_frais_2025, calculer_frais_placement_2025, lignes_resume_frais_placement_2025)
from .tax_capital_gains_2025 import (ProfilCapital2025, GainsCapital2025, valider_profil_capital_2025, detecter_capital_2025, consolider_capital_2025, appliquer_capital_2025, lignes_resume_capital_2025)
from .tax_dividend_income_2025 import (ProfilDividendes2025, Dividendes2025, valider_profil_dividendes_2025, detecter_dividendes_2025, consolider_dividendes_2025, appliquer_dividendes_2025, appliquer_credits_dividendes_2025, lignes_resume_dividendes_2025)
from .tax_interest_income_2025 import (ProfilInterets2025, Interets2025, valider_profil_interets_2025, detecter_interets_2025, consolider_interets_2025, appliquer_interets_2025, lignes_resume_interets_2025)
from .tax_investment_combinations_2025 import (
    CombinaisonInteretsDividendes2025,
    CombinaisonPlacementsCanadiens2025,
    detecter_interets_dividendes_2025,
    consolider_interets_dividendes_2025,
    consolider_interets_dividendes_capital_2025,
    lignes_resume_interets_dividendes_2025,
)
from .tax_foreign_investment_2025 import (
    ProfilPlacementEtranger2025,
    PlacementEtranger2025,
    ProfilCreditImpotEtranger2025,
    CreditImpotEtranger2025,
    valider_profil_placement_etranger_2025,
    detecter_placement_etranger_2025,
    consolider_placement_etranger_2025,
    appliquer_placement_etranger_2025,
    consolider_credit_impot_etranger_2025,
    appliquer_credit_impot_etranger_2025,
    lignes_resume_placement_etranger_2025,
    lignes_resume_credit_impot_etranger_2025,
)
from .tax_replacement_benefits_2025 import (ProfilRemplacement2025, PrestationsRemplacement2025, valider_profil_remplacement_2025, detecter_remplacement_2025, consolider_remplacement_2025, appliquer_remplacement_2025, appliquer_redressement_358_2025, lignes_resume_remplacement_2025)
from .tax_rrsp_withdrawals_2025 import (ProfilRetraits2025, Retraits2025, valider_profil_retraits_2025, detecter_retraits_2025, consolider_retraits_2025, appliquer_retraits_2025, lignes_resume_retraits_2025)
from .tax_pension_income_2025 import (ProfilPensions2025, RevenusPensions2025, TYPES_PENSIONS, valider_profil_pensions_2025, consolider_pensions_2025, appliquer_pensions_2025, credit_pension_federal_depuis_feuillets, credit_retraite_quebec_depuis_feuillets, lignes_resume_pensions_2025)
from .tax_old_age_security_2025 import (PrestationsPsv2025, valider_confirmation_psv, consolider_prestations_psv_2025, appliquer_revenu_psv_2025, appliquer_recuperation_psv_2025, lignes_resume_psv_2025)
from .tax_cpp_qpp_benefits_2025 import (
    PrestationsRrqRpc2025, consolider_prestations_rrq_rpc_2025, valider_confirmation_rrq_rpc,
    appliquer_prestations_rrq_rpc_2025, lignes_resume_rrq_rpc_2025,
    base_sans_emploi_rrq_rpc_2025, revenu_sans_emploi_rrq_rpc_2025,
)
from .tax_employment_insurance_2025 import (
    PrestationsAe2025, consolider_prestations_ae_2025, valider_confirmation_ae,
    appliquer_revenu_ae_2025, appliquer_recuperation_ae_2025, lignes_resume_ae_2025,
)

from .tax_parental_benefits_2025 import (
    PrestationsRqap2025, consolider_prestations_rqap_2025,
    appliquer_prestations_rqap_2025, lignes_resume_rqap_2025, valider_confirmation_rqap,
)

from .tax_rpp_2025 import (
    CotisationsRpa2025, appliquer_cotisations_rpa_2025,
    verifier_rpa_dossier_2025, lignes_resume_rpa_2025,
)


@dataclass(frozen=True)
class EstimationFiscale2025:
    dossier: DossierFiscalValide
    base: BaseFiscaleEmploi2025
    revenu: RevenuNetImposable2025
    federal: ImpotFederalPreliminaire2025
    quebec: ImpotQuebecPreliminaire2025
    rapprochement: RapprochementFiscal2025
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
    aidant_conjoint_personne_charge_federal: AidantNaturelConjointOuPersonneChargeFederal2025
    accessibilite_domiciliaire_federale: DepensesAccessibiliteDomiciliaireFederal2025
    achat_habitation_federal: MontantAchatHabitationFederal2025
    aidant_autre_personne_charge_federal: AidantNaturelAutrePersonneChargeFederal2025
    aidant_enfant_federal: AidantNaturelEnfantMoins18Federal2025
    cotisations_rpa: CotisationsRpa2025 = CotisationsRpa2025()
    rqap_confirme: bool = False
    prestations_rqap: PrestationsRqap2025 = PrestationsRqap2025()
    ae_confirme: bool = False
    prestations_ae: PrestationsAe2025 = PrestationsAe2025()
    profil_reports_pertes: ProfilReportsPertes2025 = ProfilReportsPertes2025()
    reports_pertes: ReportsPertes2025 = ReportsPertes2025()
    profil_frais_placement: ProfilFraisPlacement2025 = ProfilFraisPlacement2025()
    frais_placement: FraisPlacement2025 = FraisPlacement2025()
    profil_capital: ProfilCapital2025 = ProfilCapital2025()
    capital: GainsCapital2025 = GainsCapital2025()
    profil_dividendes: ProfilDividendes2025 = ProfilDividendes2025()
    dividendes: Dividendes2025 = Dividendes2025()
    profil_interets: ProfilInterets2025 = ProfilInterets2025()
    interets: Interets2025 = Interets2025()
    profil_placement_etranger: ProfilPlacementEtranger2025 = ProfilPlacementEtranger2025()
    placement_etranger: PlacementEtranger2025 = PlacementEtranger2025()
    profil_credit_impot_etranger: ProfilCreditImpotEtranger2025 = ProfilCreditImpotEtranger2025()
    credit_impot_etranger: CreditImpotEtranger2025 = CreditImpotEtranger2025()
    profil_remplacement: ProfilRemplacement2025 = ProfilRemplacement2025()
    remplacement: PrestationsRemplacement2025 = PrestationsRemplacement2025()
    profil_retraits: ProfilRetraits2025 = ProfilRetraits2025()
    retraits: Retraits2025 = Retraits2025()
    profil_pensions: ProfilPensions2025 = ProfilPensions2025()
    pensions: RevenusPensions2025 = RevenusPensions2025()
    psv_confirme: bool = False
    prestations_psv: PrestationsPsv2025 = PrestationsPsv2025()
    rrq_rpc_confirme: bool = False
    prestations_rrq_rpc: PrestationsRrqRpc2025 = PrestationsRrqRpc2025()
    allocation_travailleurs: AllocationTravailleurs2025 = AllocationTravailleurs2025()
    resultat_allocation_travailleurs: ResultatAllocationTravailleurs2025 = ResultatAllocationTravailleurs2025()
    prolongation_carriere_quebec: ProlongationCarriereQuebec2025 = ProlongationCarriereQuebec2025()
    resultat_carriere_quebec: ResultatCarriereQuebec2025 = ResultatCarriereQuebec2025()
    achat_habitation_quebec: AchatHabitationQuebec2025 = AchatHabitationQuebec2025()
    resultat_achat_quebec: ResultatAchatQuebec2025 = ResultatAchatQuebec2025()
    interets_etudiants_quebec: InteretsEtudiantsQuebec2025 = InteretsEtudiantsQuebec2025()
    resultat_interets_quebec: ResultatInteretsQuebec2025 = ResultatInteretsQuebec2025()
    interets_pret_etudiant: InteretsPretEtudiant2025 = InteretsPretEtudiant2025()
    resultat_interets_pret_etudiant: ResultatInteretsPretEtudiant2025 = ResultatInteretsPretEtudiant2025()
    resultat_supplement_medical: ResultatSupplementMedical2025 = ResultatSupplementMedical2025()
    resultat_reports_scolarite: ResultatReportsScolariteFederaux2025 = ResultatReportsScolariteFederaux2025()
    resultat_reports_dons: ResultatReportsDonsFederaux2025 = ResultatReportsDonsFederaux2025()
    renovations_multigenerationnelles: RenovationsMultigenerationnelles2025 = RenovationsMultigenerationnelles2025()
    transferts_handicap: TransfertsHandicap2025 = TransfertsHandicap2025()
    frais_medicaux_famille: FraisMedicauxFamilleFederaux2025 = FraisMedicauxFamilleFederaux2025()
    resultat_medical_familial: ResultatMedicalFamilial2025 = ResultatMedicalFamilial2025()
    resultat_transferts_handicap: ResultatTransfertsHandicap2025 = ResultatTransfertsHandicap2025()
    resultat_multigenerationnel: ResultatMultigenerationnel2025 = ResultatMultigenerationnel2025()
    fournitures_educateur: FournituresEducateur2025 = FournituresEducateur2025()
    fonds_travailleurs: FondsTravailleurs2025 = FondsTravailleurs2025()
    contributions_politiques: ContributionsPolitiques2025 = ContributionsPolitiques2025()
    resultat_fournitures_educateur: ResultatFournituresEducateur2025 = ResultatFournituresEducateur2025()
    resultat_fonds_travailleurs: ResultatFondsTravailleurs2025 = ResultatFondsTravailleurs2025()
    resultat_contributions_politiques: ResultatContributionsPolitiques2025 = ResultatContributionsPolitiques2025()
    adoption: Adoption2025 = Adoption2025()
    resultat_adoption: ResultatAdoption2025 = ResultatAdoption2025()
    benevoles: Benevoles2025 = Benevoles2025()
    resultat_benevoles: ResultatBenevoles2025 = ResultatBenevoles2025()
    transfert_conjoint: TransfertConjointFederal2025 = TransfertConjointFederal2025()
    resultat_transfert_conjoint: ResultatTransfertConjoint2025 = ResultatTransfertConjoint2025()
    transferts_scolarite_recus: TransfertsScolariteRecus2025 = TransfertsScolariteRecus2025()


def calculer_estimation_fiscale_2025(
    dossier: DossierFiscalValide,
    ajustement_reer: AjustementReer2025 | None = None,
    deduction_celiapp: DeductionCeliapp2025 | None = None,
    frais_garde_federaux: FraisGardeFederaux2025 | None = None,
    depenses_emploi: DepensesEmploi2025 | None = None,
    frais_demenagement: FraisDemenagement2025 | None = None,
    pension_alimentaire_payee: PensionAlimentairePayee2025 | None = None,
    autres_deductions: AutresDeductions2025 | None = None,
    cotisations_syndicales: (
        CotisationsSyndicalesProfessionnelles2025 | None
    ) = None,
    dons_bienfaisance: DonsBienfaisance2025 | None = None,
    frais_medicaux: FraisMedicaux2025 | None = None,
    frais_scolarite: FraisScolarite2025 | None = None,
    credit_deficience: CreditDeficience2025 | None = None,
    assurance_medicaments: (
        AssuranceMedicamentsQuebec2025 | None
    ) = None,
    cotisations_excedentaires: (
        CotisationsExcedentaires2025 | None
    ) = None,
    personne_vivant_seule: (
        PersonneVivantSeule2025 | None
    ) = None,
    montants_age_retraite: (
        MontantsAgeRetraite2025 | None
    ) = None,
    credits_federaux_age_pension: (
        CreditsFederauxAgePension2025 | None
    ) = None,
    montant_conjoint_federal: (
        MontantConjointFederal2025 | None
    ) = None,
    personne_charge_admissible_federale: (
        MontantPersonneChargeAdmissibleFederal2025 | None
    ) = None,
    aidant_conjoint_personne_charge_federal: (
        AidantNaturelConjointOuPersonneChargeFederal2025 | None
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
    aidant_enfant_federal: (
        AidantNaturelEnfantMoins18Federal2025 | None
    ) = None,
    cotisations_rpa: CotisationsRpa2025 | None = None,
    rqap_confirme: bool = False,
    ae_confirme: bool = False,
    profil_reports_pertes: ProfilReportsPertes2025 = ProfilReportsPertes2025(),
    profil_frais_placement: ProfilFraisPlacement2025 = ProfilFraisPlacement2025(),
    profil_capital: ProfilCapital2025 = ProfilCapital2025(),
    profil_dividendes: ProfilDividendes2025 = ProfilDividendes2025(),
    profil_interets: ProfilInterets2025 = ProfilInterets2025(),
    profil_placement_etranger: ProfilPlacementEtranger2025 = ProfilPlacementEtranger2025(),
    profil_credit_impot_etranger: ProfilCreditImpotEtranger2025 = ProfilCreditImpotEtranger2025(),
    profil_remplacement: ProfilRemplacement2025 = ProfilRemplacement2025(),
    profil_retraits: ProfilRetraits2025 = ProfilRetraits2025(),
    profil_pensions: ProfilPensions2025 = ProfilPensions2025(),
    psv_confirme: bool = False,
    rrq_rpc_confirme: bool = False,
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
    prolongation_carriere_quebec: ProlongationCarriereQuebec2025 | None = None,
    achat_habitation_quebec: AchatHabitationQuebec2025 | None = None,
    interets_etudiants_quebec: InteretsEtudiantsQuebec2025 | None = None,
    interets_pret_etudiant: InteretsPretEtudiant2025 | None = None,
) -> EstimationFiscale2025:
    """Exécute le pipeline fiscal local 2025 sur un dossier verrouillé."""
    if dossier.annee_fiscale != 2025:
        raise ValueError(
            "L'estimation fiscale automatique est disponible "
            "uniquement pour l'année 2025."
        )

    fonds = fonds_travailleurs if fonds_travailleurs is not None else FondsTravailleurs2025()
    resultat_fonds = calculer_fonds_travailleurs_2025(fonds, client=dossier.client, annee=dossier.annee_fiscale)
    politiques = contributions_politiques if contributions_politiques is not None else ContributionsPolitiques2025()
    resultat_politiques = calculer_contributions_politiques_2025(politiques, client=dossier.client, annee=dossier.annee_fiscale)
    adoption_effective = adoption if adoption is not None else Adoption2025()
    resultat_adoption = calculer_adoption_2025(adoption_effective, dossier.annee_fiscale)
    benevoles_effectifs = benevoles if benevoles is not None else Benevoles2025()
    resultat_benevoles = calculer_benevoles_2025(benevoles_effectifs, dossier)
    conjoint = transfert_conjoint if transfert_conjoint is not None else TransfertConjointFederal2025()
    resultat_conjoint = calculer_transfert_conjoint_2025(conjoint, beneficiaire=dossier.client)
    if conjoint.activer and fonds.acquisitions:
        import json
        fonds_conjoint = fonds_depuis_dict(json.loads(conjoint.dossier_conjoint_json).get("fonds_travailleurs"))
        verifier_fonds_conjoint_2025(fonds, fonds_conjoint, resultat_conjoint.nom_conjoint)
    if conjoint.activer and politiques.recus:
        import json
        brut_conjoint = json.loads(conjoint.dossier_conjoint_json)
        politiques_conjoint = politiques_depuis_dict(brut_conjoint.get("contributions_politiques"))
        verifier_recus_politiques_conjoint_2025(politiques, politiques_conjoint, resultat_conjoint.nom_conjoint)
    if conjoint.activer and adoption_effective.enfants:
        import json
        from .tax_adoption_2025 import adoption_depuis_dict, verifier_partage_adoption_2025
        adoption_conjoint = adoption_depuis_dict(json.loads(conjoint.dossier_conjoint_json).get("adoption"))
        verifier_partage_adoption_2025(adoption_effective, adoption_conjoint)
    scolarite_recue = valider_transferts_scolarite_recus_2025(
        transferts_scolarite_recus if transferts_scolarite_recus is not None else TransfertsScolariteRecus2025()
    )
    act = valider_allocation_travailleurs_2025(
        allocation_travailleurs if allocation_travailleurs is not None else AllocationTravailleurs2025()
    )
    pret_etudiant = valider_interets_pret_etudiant_2025(
        interets_pret_etudiant if interets_pret_etudiant is not None else InteretsPretEtudiant2025()
    )
    resultat_pret_etudiant = repartir_interets_pret_etudiant_2025(pret_etudiant)

    parcours_interets_dividendes = (
        detecter_interets_dividendes_2025(dossier)
        and profil_interets != ProfilInterets2025()
        and profil_dividendes != ProfilDividendes2025()
    )
    parcours_3h_c = (
        parcours_interets_dividendes
        and profil_capital != ProfilCapital2025()
    )

    valider_profil_placement_etranger_2025(profil_placement_etranger)
    parcours_etranger = (
        profil_placement_etranger != ProfilPlacementEtranger2025()
        or detecter_placement_etranger_2025(dossier)
    )
    placement_etranger = PlacementEtranger2025()
    credit_impot_etranger = CreditImpotEtranger2025()
    if parcours_etranger:
        if parcours_interets_dividendes:
            raise ValueError(
                "Combinaison intérêts + dividendes avec autre parcours : "
                "hors périmètre 3H-A."
            )
        if (
            profil_capital != ProfilCapital2025()
            or profil_dividendes != ProfilDividendes2025()
            or profil_interets != ProfilInterets2025()
            or profil_frais_placement != ProfilFraisPlacement2025()
            or profil_reports_pertes != ProfilReportsPertes2025()
            or profil_pensions != ProfilPensions2025()
            or profil_retraits != ProfilRetraits2025()
            or profil_remplacement != ProfilRemplacement2025()
            or any((rqap_confirme, ae_confirme, rrq_rpc_confirme, psv_confirme))
        ):
            raise ValueError(
                "Placement étranger avec autre placement, pension ou prestation : "
                "hors périmètre 3G initial."
            )
        placement_etranger = consolider_placement_etranger_2025(
            dossier, profil_placement_etranger
        )
        credit_impot_etranger = consolider_credit_impot_etranger_2025(
            placement_etranger, profil_credit_impot_etranger
        )
    elif profil_credit_impot_etranger != ProfilCreditImpotEtranger2025():
        raise ValueError(
            "Profil de crédit étranger fourni sans parcours de placement étranger."
        )

    combinaison_interets_dividendes = CombinaisonInteretsDividendes2025()
    combinaison_3h_c = CombinaisonPlacementsCanadiens2025()
    if parcours_interets_dividendes:
        if parcours_3h_c:
            if (
                profil_frais_placement != ProfilFraisPlacement2025()
                and not detecter_capital_2025(dossier)
            ):
                raise ValueError(
                    "Combinaison 3H-B avec profil capital sans feuillet capital : "
                    "hors périmètre 3H-D."
                )
            if (
                parcours_etranger
                or profil_pensions != ProfilPensions2025()
                or profil_retraits != ProfilRetraits2025()
                or profil_remplacement != ProfilRemplacement2025()
                or any((rqap_confirme, ae_confirme, rrq_rpc_confirme, psv_confirme))
            ):
                raise ValueError(
                    "Combinaison intérêts + dividendes + capital avec autre parcours : "
                    "hors périmètre 3H-C."
                )
            combinaison_3h_c = consolider_interets_dividendes_capital_2025(
                dossier,
                profil_interets,
                profil_dividendes,
                profil_capital,
            )
            combinaison_interets_dividendes = CombinaisonInteretsDividendes2025(
                interets=combinaison_3h_c.interets,
                dividendes=combinaison_3h_c.dividendes,
                assiette_fss=combinaison_3h_c.assiette_fss,
                cotisation_fss=combinaison_3h_c.cotisation_fss,
                present=True,
            )
        else:
            if (
                parcours_etranger
                or profil_reports_pertes != ProfilReportsPertes2025()
                or profil_pensions != ProfilPensions2025()
                or profil_retraits != ProfilRetraits2025()
                or profil_remplacement != ProfilRemplacement2025()
                or any((rqap_confirme, ae_confirme, rrq_rpc_confirme, psv_confirme))
            ):
                raise ValueError(
                    "Combinaison intérêts + dividendes avec autre parcours : "
                    "hors périmètre 3H-A/3H-B."
                )
            combinaison_interets_dividendes = consolider_interets_dividendes_2025(
                dossier,
                profil_interets,
                profil_dividendes,
            )

    verifier_confirmation_reports_pertes_2025(profil_reports_pertes, dossier, profil_capital, profil_frais_placement)
    verifier_confirmation_frais_2025(profil_frais_placement, dossier, profil_interets, profil_dividendes, profil_capital)
    valider_profil_capital_2025(profil_capital)
    parcours_capital = (
        parcours_3h_c
        or (
            not parcours_interets_dividendes
            and (profil_capital != ProfilCapital2025() or detecter_capital_2025(dossier))
        )
    )
    capital = combinaison_3h_c.capital if parcours_3h_c else GainsCapital2025()
    if parcours_capital and not parcours_3h_c:
        if any((rqap_confirme, ae_confirme, rrq_rpc_confirme, psv_confirme)) or profil_pensions != ProfilPensions2025() or profil_retraits != ProfilRetraits2025() or profil_remplacement != ProfilRemplacement2025() or profil_interets != ProfilInterets2025() or profil_dividendes != ProfilDividendes2025():
            raise ValueError("Capital avec autres placements ou prestations : hors périmètre 3D.")
        capital = consolider_capital_2025(dossier, profil_capital)
    valider_profil_dividendes_2025(profil_dividendes)
    parcours_dividendes = (
        not parcours_interets_dividendes
        and not parcours_capital
        and (profil_dividendes != ProfilDividendes2025() or detecter_dividendes_2025(dossier))
    )
    dividendes = (
        combinaison_interets_dividendes.dividendes
        if parcours_interets_dividendes
        else Dividendes2025()
    )
    if parcours_dividendes:
        if any((rqap_confirme, ae_confirme, rrq_rpc_confirme, psv_confirme)) or profil_pensions != ProfilPensions2025() or profil_retraits != ProfilRetraits2025() or profil_remplacement != ProfilRemplacement2025() or profil_interets != ProfilInterets2025():
            raise ValueError("Dividendes avec autres placements ou prestations : hors périmètre 3C.")
        dividendes = consolider_dividendes_2025(dossier, profil_dividendes)
    valider_profil_interets_2025(profil_interets)
    parcours_interets = (
        not parcours_interets_dividendes
        and not parcours_etranger
        and not parcours_capital
        and not parcours_dividendes
        and (profil_interets != ProfilInterets2025() or detecter_interets_2025(dossier))
    )
    interets = (
        combinaison_interets_dividendes.interets
        if parcours_interets_dividendes
        else Interets2025()
    )
    if parcours_interets:
        if any((rqap_confirme, ae_confirme, rrq_rpc_confirme, psv_confirme)) or profil_pensions != ProfilPensions2025() or profil_retraits != ProfilRetraits2025() or profil_remplacement != ProfilRemplacement2025():
            raise ValueError("Intérêts avec autres prestations : hors périmètre 3A.")
        interets = consolider_interets_2025(dossier, profil_interets)
    valider_profil_remplacement_2025(profil_remplacement)
    parcours_remplacement = profil_remplacement != ProfilRemplacement2025() or detecter_remplacement_2025(dossier)
    remplacement = PrestationsRemplacement2025()
    if parcours_remplacement:
        if any((rqap_confirme, ae_confirme, rrq_rpc_confirme, psv_confirme)) or profil_pensions != ProfilPensions2025() or profil_retraits != ProfilRetraits2025():
            raise ValueError("Remplacement avec autres prestations : hors périmètre.")
        remplacement = consolider_remplacement_2025(dossier, profil_remplacement)
    valider_profil_retraits_2025(profil_retraits)
    parcours_retraits = profil_retraits != ProfilRetraits2025() or detecter_retraits_2025(dossier)
    retraits = Retraits2025()
    if parcours_retraits:
        if any((rqap_confirme, ae_confirme, rrq_rpc_confirme, psv_confirme)) or profil_pensions != ProfilPensions2025():
            raise ValueError("Retraits avec autres prestations ou pensions : hors périmètre.")
        retraits = consolider_retraits_2025(dossier, profil_retraits)
    valider_profil_pensions_2025(profil_pensions)
    parcours_pensions = not parcours_interets_dividendes and not parcours_etranger and not parcours_capital and not parcours_dividendes and not parcours_interets and not parcours_retraits and (profil_pensions != ProfilPensions2025() or any(d.type_document in TYPES_PENSIONS for d in dossier.donnees_validees))
    pensions = RevenusPensions2025()
    if parcours_pensions:
        if rqap_confirme or ae_confirme or rrq_rpc_confirme or psv_confirme:
            raise ValueError("Pensions avec AE/RQAP/RRQ/PSV : profil combiné hors périmètre.")
        pensions = consolider_pensions_2025(dossier, profil_pensions)
    valider_confirmation_psv(psv_confirme)
    parcours_psv = psv_confirme or any(d.type_document == "T4A(OAS)" for d in dossier.donnees_validees)
    prestations_psv = PrestationsPsv2025()
    if parcours_psv:
        if rqap_confirme or ae_confirme or rrq_rpc_confirme:
            raise ValueError("PSV avec AE/RQAP/RRQ : profil combiné hors périmètre.")
        prestations_psv = consolider_prestations_psv_2025(dossier, psv_confirme)
    valider_confirmation_rrq_rpc(rrq_rpc_confirme)
    parcours_rrq_rpc = not parcours_retraits and not parcours_pensions and (rrq_rpc_confirme or any(d.type_document in {"T4A(P)", "RL-2"} for d in dossier.donnees_validees))
    prestations_rrq_rpc = PrestationsRrqRpc2025()
    if parcours_rrq_rpc:
        if ae_confirme or rqap_confirme:
            raise ValueError("RRQ/RPC avec AE/RQAP : profil combiné hors périmètre.")
        prestations_rrq_rpc = consolider_prestations_rrq_rpc_2025(dossier, rrq_rpc_confirme)
    sans_emploi = (parcours_interets_dividendes or parcours_etranger or parcours_capital or parcours_dividendes or parcours_interets or parcours_remplacement or parcours_retraits or parcours_pensions or parcours_psv or parcours_rrq_rpc) and not any(d.type_document in {"T4", "RL-1"} for d in dossier.donnees_validees)
    base = base_sans_emploi_rrq_rpc_2025(dossier) if sans_emploi else consolider_base_fiscale_emploi_2025(dossier)
    if fonds.acquisitions and fonds.contribuable.revenu_emploi_entreprise != base.revenu_emploi_quebec:
        raise ValueError("Fonds : revenus d'emploi déclarés différents du dossier Québec; revenus d'entreprise non encore couverts.")
    if resultat_benevoles.reintegration_10100:
        base = replace(base, revenu_emploi_federal=base.revenu_emploi_federal + resultat_benevoles.reintegration_10100)

    cotisations_excedentaires_effectives = (
        cotisations_excedentaires
        if cotisations_excedentaires is not None
        else CotisationsExcedentaires2025()
    )
    valider_cotisations_excedentaires_2025(
        cotisations_excedentaires_effectives
    )

    cotisations_excedentaires_presentes = (
        cotisations_excedentaires_effectives
        != CotisationsExcedentaires2025()
    )

    if cotisations_excedentaires_presentes:
        controles = (
            (
                "RRQ B.A",
                cotisations_excedentaires_effectives.rrq_ba,
                base.rrq_base_premiere_supplementaire,
            ),
            (
                "RRQ B.B",
                cotisations_excedentaires_effectives.rrq_bb,
                base.rrq_deuxieme_supplementaire,
            ),
            (
                "gains admissibles RRQ",
                cotisations_excedentaires_effectives.gains_admissibles_rrq,
                base.gains_admissibles_rrq,
            ),
            (
                "assurance-emploi",
                cotisations_excedentaires_effectives.assurance_emploi,
                base.assurance_emploi,
            ),
            (
                "gains assurables AE",
                cotisations_excedentaires_effectives.gains_assurables_ae,
                base.gains_assurables_ae,
            ),
            (
                "RQAP",
                cotisations_excedentaires_effectives.rqap,
                base.rqap,
            ),
            (
                "revenus assujettis RQAP",
                cotisations_excedentaires_effectives.revenus_assujettis_rqap,
                base.gains_assurables_rqap,
            ),
        )
        for nom, valeur_profil, valeur_dossier in controles:
            if valeur_profil != valeur_dossier:
                raise ValueError(
                    f"{nom} du profil de cotisations excédentaires "
                    "doit correspondre exactement aux données "
                    "validées du dossier."
                )

    revenu = revenu_sans_emploi_rrq_rpc_2025(dossier) if sans_emploi else calculer_revenu_net_imposable_2025(
        base,
        autoriser_cotisations_excedentaires=(
            cotisations_excedentaires_presentes
        ),
    )

    valider_confirmation_ae(ae_confirme)
    valider_confirmation_rqap(rqap_confirme)
    if ae_confirme and rqap_confirme:
        raise ValueError("AE et RQAP simultanés : profil combiné hors périmètre.")
    # Sans RL-6 et sans confirmation RQAP, le T4E suit le parcours AE.
    parcours_ae = ae_confirme or (
        not rqap_confirme
        and any(d.type_document == "T4E" for d in dossier.donnees_validees)
        and not any(d.type_document == "RL-6" for d in dossier.donnees_validees)
    )
    prestations_ae = PrestationsAe2025()
    prestations_rqap = PrestationsRqap2025()
    if parcours_interets_dividendes:
        revenu = appliquer_interets_2025(revenu, interets)
        revenu = appliquer_dividendes_2025(revenu, dividendes)
        if parcours_3h_c:
            revenu = appliquer_capital_2025(revenu, capital)
    elif parcours_etranger:
        revenu = appliquer_placement_etranger_2025(revenu, placement_etranger)
    elif parcours_capital:
        revenu = appliquer_capital_2025(revenu, capital)
    elif parcours_dividendes:
        revenu = appliquer_dividendes_2025(revenu, dividendes)
    elif parcours_interets:
        revenu = appliquer_interets_2025(revenu, interets)
    elif parcours_remplacement:
        revenu = appliquer_remplacement_2025(revenu, remplacement)
    elif parcours_retraits:
        revenu = appliquer_retraits_2025(revenu, retraits)
    elif parcours_pensions:
        revenu = appliquer_pensions_2025(revenu, pensions)
    elif parcours_psv:
        revenu = appliquer_revenu_psv_2025(revenu, prestations_psv)
    elif parcours_rrq_rpc:
        revenu = appliquer_prestations_rrq_rpc_2025(revenu, prestations_rrq_rpc)
    elif parcours_ae:
        prestations_ae = consolider_prestations_ae_2025(dossier, ae_confirme)
        revenu = appliquer_revenu_ae_2025(revenu, prestations_ae)
    else:
        prestations_rqap = consolider_prestations_rqap_2025(dossier, rqap_confirme)
        revenu = appliquer_prestations_rqap_2025(revenu, prestations_rqap)

    rpa_effectives = cotisations_rpa if cotisations_rpa is not None else CotisationsRpa2025()
    verifier_rpa_dossier_2025(dossier, rpa_effectives)
    revenu = appliquer_cotisations_rpa_2025(revenu, rpa_effectives)

    ajustement_reer_effectif = (
        ajustement_reer
        if ajustement_reer is not None
        else AjustementReer2025()
    )
    revenu = appliquer_ajustement_reer_2025(
        revenu,
        ajustement_reer_effectif,
    )

    deduction_celiapp_effective = (
        deduction_celiapp
        if deduction_celiapp is not None
        else DeductionCeliapp2025()
    )
    revenu = appliquer_deduction_celiapp_2025(
        revenu,
        deduction_celiapp_effective,
    )

    frais_garde_federaux_effectifs = (
        frais_garde_federaux
        if frais_garde_federaux is not None
        else FraisGardeFederaux2025()
    )
    revenu = appliquer_frais_garde_federaux_2025(
        revenu,
        frais_garde_federaux_effectifs,
    )

    depenses_emploi_effectives = (
        depenses_emploi
        if depenses_emploi is not None
        else DepensesEmploi2025()
    )
    revenu = appliquer_depenses_emploi_2025(
        revenu,
        depenses_emploi_effectives,
    )

    educateur = fournitures_educateur if fournitures_educateur is not None else FournituresEducateur2025()
    resultat_educateur = calculer_fournitures_educateur_2025(educateur, annee=dossier.annee_fiscale,
        deduction_t777=arrondir_cent(depenses_emploi_effectives.deduction_federale_t777))

    frais_demenagement_effectifs = (
        frais_demenagement
        if frais_demenagement is not None
        else FraisDemenagement2025()
    )
    revenu = appliquer_frais_demenagement_2025(
        revenu,
        frais_demenagement_effectifs,
    )

    pension_alimentaire_payee_effective = (
        pension_alimentaire_payee
        if pension_alimentaire_payee is not None
        else PensionAlimentairePayee2025()
    )

    if (
        pension_alimentaire_payee_effective.deduction_federale_22000
        > Decimal("0")
        or pension_alimentaire_payee_effective.deduction_quebec_225
        > Decimal("0")
    ):
        profils_credits_lies = (
            montant_conjoint_federal,
            personne_charge_admissible_federale,
            aidant_conjoint_personne_charge_federal,
            aidant_autre_personne_charge_federal,
            aidant_enfant_federal,
        )
        if any(
            profil is not None
            and getattr(profil, "reclamer_montant", False)
            for profil in profils_credits_lies
        ):
            raise ValueError(
                "Bloc 4E simple : une pension alimentaire déductible ne peut "
                "pas être combinée ici avec les lignes fédérales "
                "30300/30400/30425/30450/30500. Une revue avancée est requise."
            )

    revenu = appliquer_pension_alimentaire_payee_2025(
        revenu,
        pension_alimentaire_payee_effective,
    )

    autres_deductions_effectives = (
        autres_deductions
        if autres_deductions is not None
        else AutresDeductions2025()
    )

    if autres_deductions_effectives.deduction_federale_23200 > Decimal("0"):
        conflits_23200 = (
            getattr(prestations_rqap, "remboursement", Decimal("0")),
            getattr(prestations_ae, "remboursement", Decimal("0")),
            getattr(retraits, "ligne_23200", Decimal("0")),
        )
        if any(montant > Decimal("0") for montant in conflits_23200):
            raise ValueError(
                "Bloc 4F simple : la ligne fédérale 23200 est déjà utilisée "
                "par un autre bloc du dossier. Une double déduction est refusée."
            )

    revenu = appliquer_autres_deductions_2025(
        revenu,
        autres_deductions_effectives,
    )

    cotisations_effectives = (
        cotisations_syndicales
        if cotisations_syndicales is not None
        else CotisationsSyndicalesProfessionnelles2025()
    )

    revenu = appliquer_deduction_federale_cotisations_2025(
        revenu,
        cotisations_effectives,
    )

    revenu, frais_placement = calculer_frais_placement_2025(
        profil_frais_placement, revenu, interets, dividendes, capital, profil_interets)
    if frais_placement.present:
        # Une seule cotisation finale, réutilisée partout (résumé, trace, rapprochement).
        # En 3H-B et 3H-D, la FSS finale reste portée une seule fois par le résultat
        # intérêts; dividendes et capital restent à zéro pour éviter tout double comptage.
        if interets.present and dividendes.present:
            interets = replace(
                interets,
                cotisation_fss=frais_placement.cotisation_fss,
            )
            dividendes = replace(
                dividendes,
                cotisation_fss=Decimal("0"),
            )
            if capital.present:
                capital = replace(
                    capital,
                    cotisation_fss=Decimal("0"),
                )
        else:
            if interets.present:
                interets = replace(interets, cotisation_fss=frais_placement.cotisation_fss)
            if dividendes.present:
                dividendes = replace(dividendes, cotisation_fss=frais_placement.cotisation_fss)
            if capital.present:
                capital = replace(capital, cotisation_fss=frais_placement.cotisation_fss)

    revenu, frais_placement, reports_pertes = appliquer_reports_pertes_2025(
        profil_reports_pertes, revenu, capital, frais_placement)

    revenu, prestations_ae = appliquer_recuperation_ae_2025(revenu, prestations_ae)
    revenu, prestations_psv = appliquer_recuperation_psv_2025(revenu, prestations_psv)

    dons_effectifs = (
        dons_bienfaisance
        if dons_bienfaisance is not None
        else DonsBienfaisance2025()
    )
    reports_dons = calculer_reports_dons_federaux_2025(dons_effectifs.reports_federaux,
        dons_2025=dons_effectifs.montant_admissible_federal, revenu_net=revenu.revenu_net_federal)
    valider_plafond_dons_monetaire_federal_2025(dons_effectifs, revenu.revenu_net_federal)

    frais_medicaux_effectifs = (
        frais_medicaux
        if frais_medicaux is not None
        else FraisMedicaux2025()
    )

    frais_scolarite_effectifs = (
        frais_scolarite
        if frais_scolarite is not None
        else FraisScolarite2025()
    )
    valider_frais_scolarite_2025(frais_scolarite_effectifs)

    credit_deficience_effectif = (
        credit_deficience
        if credit_deficience is not None
        else CreditDeficience2025()
    )

    personne_vivant_seule_effective = (
        personne_vivant_seule
        if personne_vivant_seule is not None
        else PersonneVivantSeule2025()
    )
    valider_personne_vivant_seule_2025(
        personne_vivant_seule_effective
    )

    if (
        personne_vivant_seule_effective.reclamer_montant
        and personne_vivant_seule_effective.revenu_familial_net
        != revenu.revenu_net_quebec
    ):
        raise ValueError(
            "Le revenu familial net du profil personne vivant seule "
            "doit correspondre au revenu net Québec calculé pour "
            "ce dossier."
        )

    montants_age_retraite_effectifs = (
        montants_age_retraite
        if montants_age_retraite is not None and (not pensions.present or montants_age_retraite != MontantsAgeRetraite2025())
        else credit_retraite_quebec_depuis_feuillets(pensions, revenu) if pensions.present else MontantsAgeRetraite2025()
    )
    valider_montants_age_retraite_2025(
        montants_age_retraite_effectifs
    )

    if capital.present and montants_age_retraite_effectifs.reclamer_revenus_retraite:
        raise ValueError("Capital : aucun revenu admissible 361.")
    if dividendes.present and montants_age_retraite_effectifs.reclamer_revenus_retraite:
        raise ValueError("Dividendes : aucun revenu admissible 361.")
    if interets.present and montants_age_retraite_effectifs.reclamer_revenus_retraite:
        raise ValueError("Intérêts : aucun revenu admissible 361.")
    if retraits.present and montants_age_retraite_effectifs.reclamer_revenus_retraite:
        raise ValueError("Retraits et forfaits : aucun revenu admissible 361.")
    if pensions.present:
        if montants_age_retraite_effectifs.reclamer_age and profil_pensions.age_31_decembre < 65:
            raise ValueError("Âge du profil pensions incompatible avec le crédit d'âge Québec.")
        if montants_age_retraite_effectifs.reclamer_revenus_retraite and (
            montants_age_retraite_effectifs.revenu_ligne_122 != pensions.admissible_quebec
            or any((montants_age_retraite_effectifs.deduction_ligne_250_point_4, montants_age_retraite_effectifs.deduction_ligne_250_point_6, montants_age_retraite_effectifs.deduction_ligne_293, montants_age_retraite_effectifs.deduction_ligne_297_points_9_12))):
            raise ValueError("Le revenu admissible Québec 361 doit correspondre aux feuillets pensions sans déduction complexe.")
    if prestations_psv.present and montants_age_retraite_effectifs.reclamer_revenus_retraite:
        raise ValueError("La PSV ne donne pas droit au montant pour revenus de retraite (361).")
    if prestations_rrq_rpc.present and montants_age_retraite_effectifs.reclamer_revenus_retraite:
        raise ValueError("Les prestations RRQ/RPC ne donnent pas droit au montant pour revenus de retraite (361).")

    age_retraite_actif = (
        montants_age_retraite_effectifs.reclamer_age
        or montants_age_retraite_effectifs.reclamer_revenus_retraite
    )

    if (
        age_retraite_actif
        and montants_age_retraite_effectifs.revenu_familial_net
        != revenu.revenu_net_quebec
    ):
        raise ValueError(
            "Le revenu familial net du profil âge/retraite "
            "doit correspondre au revenu net Québec calculé pour "
            "ce dossier."
        )

    annexe_b_combinee = calculer_annexe_b_combinee_2025(personne_vivant_seule_effective,
        montants_age_retraite_effectifs, revenu_net=revenu.revenu_net_quebec)
    if (
        age_retraite_actif
        and personne_vivant_seule_effective.reclamer_montant
        and annexe_b_combinee is None
    ):
        raise ValueError(
            "Cette version ne peut pas combiner le montant pour "
            "personne vivant seule avec les montants pour âge ou "
            "revenus de retraite, car ils partagent la réduction "
            "de l\'annexe B."
        )

    credits_federaux_age_pension_effectifs = (
        credits_federaux_age_pension
        if credits_federaux_age_pension is not None and (not pensions.present or credits_federaux_age_pension != CreditsFederauxAgePension2025())
        else credit_pension_federal_depuis_feuillets(pensions, profil_pensions, revenu) if pensions.present else CreditsFederauxAgePension2025()
    )
    valider_credits_federaux_age_pension_2025(
        credits_federaux_age_pension_effectifs
    )

    age_pension_federal_actif = (
        credits_federaux_age_pension_effectifs.reclamer_montant_age
        or credits_federaux_age_pension_effectifs.reclamer_montant_pension
    )

    if (
        age_pension_federal_actif
        and credits_federaux_age_pension_effectifs.revenu_net_ligne_23600
        != revenu.revenu_net_federal
    ):
        raise ValueError(
            "Le revenu net de la ligne 23600 du profil âge/pension "
            "fédéral doit correspondre au revenu net fédéral calculé "
            "pour ce dossier."
        )

    if pensions.present and age_pension_federal_actif:
        if credits_federaux_age_pension_effectifs.age_65_plus_31_decembre_2025 != (profil_pensions.age_31_decembre >= 65):
            raise ValueError("Âge du profil pensions incompatible avec le profil de crédit fédéral.")
        if credits_federaux_age_pension_effectifs.reclamer_montant_pension and credits_federaux_age_pension_effectifs.revenu_pension_admissible != pensions.admissible_federal:
            raise ValueError("Le revenu admissible 31400 doit correspondre aux feuillets pensions.")
    if credits_federaux_age_pension_effectifs.reclamer_montant_pension and not pensions.present:
        raise ValueError(
            "Le montant fédéral pour revenu de pension ligne 31400 "
            "ne peut pas encore être intégré : le revenu de pension "
            "admissible doit d'abord être ajouté au moteur de revenu "
            "(lignes 11500, 11600 ou 12900 selon le cas)."
        )

    montant_conjoint_federal_effectif = (
        montant_conjoint_federal
        if montant_conjoint_federal is not None
        else MontantConjointFederal2025()
    )
    valider_montant_conjoint_federal_2025(
        montant_conjoint_federal_effectif
    )

    if (
        montant_conjoint_federal_effectif.reclamer_montant
        and (
            montant_conjoint_federal_effectif
            .revenu_net_contribuable_ligne_23600
            != revenu.revenu_net_federal
        )
    ):
        raise ValueError(
            "Le revenu net du contribuable à la ligne 23600 du "
            "profil conjoint fédéral doit correspondre au revenu "
            "net fédéral calculé pour ce dossier."
        )

    personne_charge_admissible_federale_effective = (
        personne_charge_admissible_federale
        if personne_charge_admissible_federale is not None
        else MontantPersonneChargeAdmissibleFederal2025()
    )
    valider_montant_personne_charge_admissible_federal_2025(
        personne_charge_admissible_federale_effective
    )

    if (
        personne_charge_admissible_federale_effective.reclamer_montant
        and (
            personne_charge_admissible_federale_effective
            .revenu_net_contribuable_ligne_23600
            != revenu.revenu_net_federal
        )
    ):
        raise ValueError(
            "Le revenu net du contribuable à la ligne 23600 du "
            "profil personne à charge admissible doit correspondre "
            "au revenu net fédéral calculé pour ce dossier."
        )

    if (
        personne_charge_admissible_federale_effective.reclamer_montant
        and montant_conjoint_federal_effectif.reclamer_montant
    ):
        raise ValueError(
            "Cette version ne peut pas combiner les lignes 30300 et "
            "30400 : le profil personne à charge admissible exige "
            "l'absence d'époux ou conjoint de fait."
        )

    aidant_30425_effectif = (
        aidant_conjoint_personne_charge_federal
        if aidant_conjoint_personne_charge_federal is not None
        else AidantNaturelConjointOuPersonneChargeFederal2025()
    )
    valider_aidant_naturel_30425_2025(aidant_30425_effectif)

    if aidant_30425_effectif.reclamer_montant:
        if aidant_30425_effectif.type_personne == TYPE_CONJOINT:
            if not montant_conjoint_federal_effectif.reclamer_montant:
                raise ValueError(
                    "La ligne 30425 pour conjoint exige que la ligne 30300 "
                    "soit réclamée."
                )
            if (
                not montant_conjoint_federal_effectif.conjoint_avec_infirmite
                or not montant_conjoint_federal_effectif
                .aidant_naturel_base_2687_inclus
            ):
                raise ValueError(
                    "La ligne 30425 pour conjoint exige une infirmité "
                    "confirmée et le montant de base de 2 687 $ "
                    "intégré à la ligne 30300."
                )

            revenu_personne_attendu = (
                montant_conjoint_federal_effectif.revenu_net_conjoint_2025
            )
            montant_source_attendu = montant_ligne_30300_2025(
                montant_conjoint_federal_effectif
            )
        elif (
            aidant_30425_effectif.type_personne
            == TYPE_PERSONNE_CHARGE_ADMISSIBLE
        ):
            if not personne_charge_admissible_federale_effective.reclamer_montant:
                raise ValueError(
                    "La ligne 30425 pour personne à charge exige que "
                    "la ligne 30400 soit réclamée."
                )
            if (
                not personne_charge_admissible_federale_effective
                .personne_charge_18_ans_ou_plus
                or not personne_charge_admissible_federale_effective
                .personne_charge_avec_infirmite
                or not personne_charge_admissible_federale_effective
                .aidant_naturel_base_2687_inclus
            ):
                raise ValueError(
                    "La ligne 30425 pour personne à charge exige 18 ans "
                    "ou plus, une infirmité confirmée et le montant "
                    "de base de 2 687 $ à la ligne 30400."
                )

            revenu_personne_attendu = (
                personne_charge_admissible_federale_effective
                .revenu_net_personne_charge_2025
            )
            montant_source_attendu = montant_ligne_30400_2025(
                personne_charge_admissible_federale_effective
            )
        else:
            raise ValueError("Type de personne ligne 30425 non supporté.")

        if (
            aidant_30425_effectif.revenu_net_personne_ligne_23600
            != revenu_personne_attendu
        ):
            raise ValueError(
                "Le revenu net de la personne pour la ligne 30425 doit "
                "correspondre au revenu net validé de la personne."
            )

        if (
            aidant_30425_effectif.montant_reclame_ligne_30300_ou_30400
            != montant_source_attendu
        ):
            raise ValueError(
                "Le montant indiqué pour les lignes 30300/30400 dans "
                "le profil 30425 doit correspondre exactement au montant "
                "calculé par l'estimation."
            )

    accessibilite_domiciliaire_federale_effective = (
        accessibilite_domiciliaire_federale
        if accessibilite_domiciliaire_federale is not None
        else DepensesAccessibiliteDomiciliaireFederal2025()
    )
    valider_depenses_accessibilite_domiciliaire_2025(
        accessibilite_domiciliaire_federale_effective
    )

    achat_habitation_federal_effectif = (
        achat_habitation_federal
        if achat_habitation_federal is not None
        else MontantAchatHabitationFederal2025()
    )
    valider_montant_achat_habitation_2025(
        achat_habitation_federal_effectif
    )

    aidant_30450_effectif = (
        aidant_autre_personne_charge_federal
        if aidant_autre_personne_charge_federal is not None
        else AidantNaturelAutrePersonneChargeFederal2025()
    )
    valider_aidant_naturel_30450_2025(aidant_30450_effectif)

    aidant_enfant_federal_effectif = (
        aidant_enfant_federal
        if aidant_enfant_federal is not None
        else AidantNaturelEnfantMoins18Federal2025()
    )
    valider_aidant_naturel_enfant_moins18_federal_2025(
        aidant_enfant_federal_effectif
    )

    verifier_combinaison_30400_30500_2025(
        personne_charge_admissible_federale_effective, aidant_enfant_federal_effectif)

    assurance_medicaments_effective = (
        assurance_medicaments
        if assurance_medicaments is not None
        else AssuranceMedicamentsQuebec2025()
    )
    if remplacement.present:
        if (credits_federaux_age_pension_effectifs.reclamer_montant_pension
                or montants_age_retraite_effectifs.reclamer_revenus_retraite
                or montant_conjoint_federal_effectif.reclamer_montant):
            raise ValueError("Prestations de remplacement : pensions et conjoint hors périmètre.")
        if assurance_medicaments_effective.type_couverture.strip().lower() == "public":
            raise ValueError("Prestations de remplacement et RAMQ publique : exemptions particulières hors périmètre.")
    if prestations_psv.supplements and assurance_medicaments_effective.type_couverture.strip().lower() == "public":
        raise ValueError("Suppléments PSV avec RAMQ publique : exemptions particulières hors périmètre.")
    valider_assurance_medicaments_2025(
        assurance_medicaments_effective
    )

    if (
        assurance_medicaments_effective.type_couverture.strip()
        and assurance_medicaments_effective.revenu_ligne_275
        != revenu.revenu_net_quebec
    ):
        raise ValueError(
            "Le revenu de la ligne 275 utilisé pour l'assurance "
            "médicaments doit correspondre au revenu net Québec "
            "calculé pour ce dossier."
        )

    federal = calculer_impot_federal_preliminaire_2025(
        base,
        revenu,
        utiliser_cotisations_attendues=(
            cotisations_excedentaires_presentes
        ),
    )
    # T1 Québec : ligne 105 avant scolarité et frais médicaux. Les fonctions
    # existantes conservent leurs validations et limitations; la finalisation
    # ci-dessous reconstruit l'impôt depuis le brut, sans cumuler leurs débits.
    handicap_transfere = transferts_handicap if transferts_handicap is not None else TransfertsHandicap2025()
    resultat_handicap_transfere = calculer_transferts_handicap_2025(
        handicap_transfere, beneficiaire=dossier.client, annee=dossier.annee_fiscale,
        reclame_30400=personne_charge_admissible_federale_effective.reclamer_montant,
        reclame_30450=aidant_30450_effectif.reclamer_montant,
        deduction_22000=pension_alimentaire_payee_effective.deduction_federale_22000,
    )
    montants_avant_scolarite = (
        ("30000", federal.montant_personnel_base),
        ("30800", federal.cotisation_base_rrq),
        ("31200", federal.assurance_emploi_admissible),
        ("31205", federal.rqap_admissible),
        ("31260", federal.montant_canadien_emploi),
        *(((resultat_benevoles.ligne_credit, resultat_benevoles.base_credit),) if resultat_benevoles.ligne_credit else ()),
        ("30100", montant_age_federal_2025(credits_federaux_age_pension_effectifs)),
        ("31400", montant_pension_federal_2025(credits_federaux_age_pension_effectifs)),
        ("30300", montant_ligne_30300_2025(montant_conjoint_federal_effectif)),
        ("30400", montant_ligne_30400_2025(personne_charge_admissible_federale_effective)),
        ("30425", montant_ligne_30425_2025(aidant_30425_effectif)),
        ("30450", montant_ligne_30450_2025(aidant_30450_effectif)),
        ("30500", montant_ligne_30500_2025(aidant_enfant_federal_effectif)),
        ("31270", montant_ligne_31270_2025(achat_habitation_federal_effectif)),
        ("31285", montant_ligne_31285_2025(accessibilite_domiciliaire_federale_effective)),
        ("31300", resultat_adoption.montant_31300),
        ("31600", montant_federal_handicap_2025(credit_deficience_effectif)),
        ("31800", resultat_handicap_transfere.ligne_31800),
    )
    base_ligne105 = calculer_base_33500_2025(montants_avant_scolarite)
    reports_scolarite = calculer_reports_scolarite_federaux_2025(
        frais_scolarite_effectifs.reports_federaux,
        frais_nets_2025=frais_scolarite_effectifs.montant_net_federal,
        revenu_imposable=revenu.revenu_imposable_federal,
        impot_brut=federal.impot_brut, base_ligne105=base_ligne105,
    )
    federal = appliquer_credit_federal_dons_2025(
        federal,
        dons_effectifs,
        revenu.revenu_imposable_federal,
    )
    federal = appliquer_credit_federal_frais_medicaux_2025(
        federal,
        frais_medicaux_effectifs,
        revenu.revenu_net_federal,
    )
    if not frais_scolarite_effectifs.reports_federaux.activer:
        federal = appliquer_credit_federal_frais_scolarite_2025(
            federal,
            frais_scolarite_effectifs,
            base_ligne105=base_ligne105,
        )
    federal = appliquer_credit_federal_handicap_2025(
        federal,
        credit_deficience_effectif,
    )
    federal = appliquer_credit_federal_age_pension_2025(
        federal,
        credits_federaux_age_pension_effectifs,
    )
    federal = appliquer_credit_federal_montant_conjoint_2025(
        federal,
        montant_conjoint_federal_effectif,
    )
    federal = appliquer_credit_federal_personne_charge_admissible_2025(
        federal,
        personne_charge_admissible_federale_effective,
    )
    federal = appliquer_credit_federal_ligne_30425_2025(
        federal,
        aidant_30425_effectif,
    )
    federal = appliquer_credit_federal_ligne_31285_2025(
        federal,
        accessibilite_domiciliaire_federale_effective,
    )
    federal = appliquer_credit_federal_ligne_31270_2025(
        federal,
        achat_habitation_federal_effectif,
    )
    federal = appliquer_credit_federal_ligne_30450_2025(
        federal,
        aidant_30450_effectif,
    )
    federal = appliquer_credit_federal_aidant_enfant_moins18_2025(
        federal,
        aidant_enfant_federal_effectif,
    )
    if conjoint.activer:
        verifier_attribution_enfants_conjoints_30500_2025(aidant_enfant_federal_effectif, resultat_conjoint)
        for valeur in (resultat_conjoint.revenu_beneficiaire_declare_45200, resultat_conjoint.revenu_beneficiaire_declare_act):
            if valeur is not None and valeur != revenu.revenu_net_federal:
                raise ValueError("Le revenu du bénéficiaire déclaré dans les prestations familiales du conjoint diffère du revenu recalculé.")
        if resultat_conjoint.travail_beneficiaire_declare_act is not None and resultat_conjoint.travail_beneficiaire_declare_act != base.revenu_emploi_federal:
            raise ValueError("Le revenu de travail du bénéficiaire déclaré pour l'ACT du conjoint diffère du revenu recalculé.")
        if resultat_conjoint.act_base_beneficiaire_declare is not None and resultat_conjoint.act_base_beneficiaire_declare != act.reclamer_base:
            raise ValueError("Le choix du réclamant de l'ACT de base diverge entre les deux dossiers.")
        if act.famille.activer and act.famille.conjoint_reclame_base != resultat_conjoint.act_base_conjoint_reclamee:
            raise ValueError("La demande ACT de base du conjoint diverge de son dossier recalculé.")
        if resultat_conjoint.revenu_beneficiaire_declare_30300 is not None:
            if resultat_conjoint.revenu_beneficiaire_declare_30300 != revenu.revenu_net_federal:
                raise ValueError("Le revenu du bénéficiaire déclaré à 30300 dans le dossier du conjoint diffère du revenu recalculé.")
            if montant_conjoint_federal_effectif.reclamer_montant:
                raise ValueError("Les deux conjoints ne peuvent réclamer simultanément 30300.")
        if montant_conjoint_federal_effectif.reclamer_montant and montant_conjoint_federal_effectif.revenu_net_conjoint_2025 != resultat_conjoint.revenu_net_conjoint:
            raise ValueError("Le revenu du conjoint pour 30300 diffère du dossier recalculé pour 32600.")
        if (act.present and not act.famille.activer) or (frais_medicaux_effectifs.supplement.reclamer and not frais_medicaux_effectifs.supplement.mode_familial):
            raise ValueError("Le transfert 32600 est incompatible avec les crédits du profil individuel sans conjoint.")
        if any(" ".join(d.nom_etudiant.split()).casefold() == " ".join(resultat_conjoint.nom_conjoint.split()).casefold()
               for d in scolarite_recue.designations):
            raise ValueError("Le même conjoint ne peut être déclaré comme étudiant à 32400 et à 32600.")
    medical_familial = frais_medicaux_famille if frais_medicaux_famille is not None else FraisMedicauxFamilleFederaux2025()
    resultat_medical_familial = calculer_medical_familial_2025(medical_familial,
        demandeur=dossier.client, revenu_net=revenu.revenu_net_federal, annee=dossier.annee_fiscale)
    verifier_combinaison_medicale_famille(medical_familial, frais_medicaux_effectifs, act.present and not act.famille.activer)
    base_medicale = (resultat_medical_familial.ligne_33200 if medical_familial.personnes else
        montant_frais_medicaux_federal_apres_seuil_2025(frais_medicaux_effectifs, revenu.revenu_net_federal))
    credits_complets = calculer_credits_non_remboursables_2025(
        montants_avant_scolarite + (
            (("31900", resultat_pret_etudiant.ligne_31900),)
            if resultat_pret_etudiant.ligne_31900 else ()
        ) + (
            ("32300", reports_scolarite.ligne_32300 if frais_scolarite_effectifs.reports_federaux.activer
             else frais_scolarite_effectifs.montant_net_federal),
            *((("32400", montant_ligne_32400_2025(scolarite_recue)),) if scolarite_recue.designations else ()),
            *((("32600", resultat_conjoint.ligne_32600),) if conjoint.activer else ()),
            ("33200", base_medicale),
        ),
        calculer_annexe9_ligne22_2025(montant_dons_federaux_reclames_2025(dons_effectifs)),
        credit_federal_dons_2025(dons_effectifs, revenu.revenu_imposable_federal),
    )
    federal = finaliser_credits_federaux_2025(federal, credits_complets)
    quebec = calculer_impot_quebec_preliminaire_2025(revenu)
    quebec = appliquer_redressement_358_2025(quebec, remplacement)
    quebec = appliquer_credit_quebec_cotisations_2025(
        quebec,
        cotisations_effectives,
    )
    quebec = appliquer_credit_quebec_dons_2025(
        quebec,
        dons_effectifs,
        revenu.revenu_imposable_quebec,
    )
    quebec = appliquer_credit_quebec_frais_medicaux_2025(
        quebec,
        frais_medicaux_effectifs,
        revenu.revenu_net_quebec,
    )
    pret_quebec = interets_etudiants_quebec if interets_etudiants_quebec is not None else InteretsEtudiantsQuebec2025()
    resultat_pret_quebec = calculer_interets_quebec_2025(pret_quebec,
        base_medicale_381=montant_frais_medicaux_quebec_apres_seuil_2025(frais_medicaux_effectifs, revenu.revenu_net_quebec))
    quebec = appliquer_interets_quebec_2025(quebec, resultat_pret_quebec)
    quebec = appliquer_credit_quebec_frais_scolarite_2025(
        quebec,
        frais_scolarite_effectifs,
    )
    quebec = appliquer_credit_quebec_deficience_2025(
        quebec,
        credit_deficience_effectif,
    )
    if annexe_b_combinee is not None:
        quebec = appliquer_annexe_b_combinee_2025(quebec, annexe_b_combinee)
    else:
        quebec = appliquer_credit_quebec_personne_vivant_seule_2025(
            quebec,
            personne_vivant_seule_effective,
        )
        quebec = appliquer_credit_quebec_age_retraite_2025(
            quebec,
            montants_age_retraite_effectifs,
        )
    achat_quebec = achat_habitation_quebec if achat_habitation_quebec is not None else AchatHabitationQuebec2025()
    ligne_361 = (annexe_b_combinee.ligne_361 if annexe_b_combinee is not None else
        montant_ligne_361_age_retraite_2025(montants_age_retraite_effectifs)
        + montant_ligne_361_personne_vivant_seule_2025(personne_vivant_seule_effective))
    carriere_quebec = prolongation_carriere_quebec if prolongation_carriere_quebec is not None else ProlongationCarriereQuebec2025()
    resultat_carriere_quebec = calculer_carriere_quebec_2025(carriere_quebec,
        salaire=base.revenu_emploi_quebec, revenu_net=revenu.revenu_net_quebec, impot_401=quebec.impot_brut,
        montant_359=quebec.montant_personnel_base - remplacement.ligne_358, montant_361=ligne_361)
    if carriere_quebec.reclamer:
        if any(d.type_document == "RL-1" and d.case == "211" and d.valeur_validee != Decimal(0) for d in dossier.donnees_validees):
            raise ValueError("La case 211 du RL-1 est hors périmètre du profil salarié 391.")
        if pensions.present and profil_pensions.age_31_decembre != 2025 - int(carriere_quebec.naissance[:4]):
            raise ValueError("Naissance 391 incompatible avec l'âge du profil pensions.")
    quebec = appliquer_carriere_quebec_2025(quebec, carriere_quebec, resultat_carriere_quebec)
    resultat_achat_quebec = calculer_achat_quebec_2025(achat_quebec, impot_401=quebec.impot_brut,
        montant_359=quebec.montant_personnel_base - remplacement.ligne_358, montant_361=ligne_361,
        credit_391=resultat_carriere_quebec.credit_ligne_391,
        credit_397=credit_quebec_cotisations_2025(cotisations_effectives))
    quebec = appliquer_achat_quebec_2025(quebec, achat_quebec, resultat_achat_quebec)
    federal, quebec = appliquer_credits_dividendes_2025(federal, quebec, dividendes)
    federal, quebec = appliquer_credit_impot_etranger_2025(
        federal, quebec, credit_impot_etranger
    )
    remboursements_cotisations = (
        calculer_remboursements_cotisations_2025(
            cotisations_excedentaires_effectives
        )
    )

    if frais_medicaux_effectifs.supplement.reclamer and not frais_medicaux_effectifs.supplement.mode_familial and any(p.reclamer_montant for p in (
        montant_conjoint_federal_effectif, personne_charge_admissible_federale_effective,
        aidant_30425_effectif, aidant_30450_effectif, aidant_enfant_federal_effectif,
    )):
        raise ValueError("Supplément médical 5D : combinaison familiale hors du profil individuel pris en charge.")

    if act.present and not act.famille.activer and any(p.reclamer_montant for p in (
        montant_conjoint_federal_effectif, personne_charge_admissible_federale_effective,
        aidant_30425_effectif, aidant_30450_effectif, aidant_enfant_federal_effectif,
    )):
        raise ValueError("ACT 5E : combinaison familiale hors du profil individuel pris en charge.")
    resultat_act = calculer_allocation_travailleurs_2025(
        act, revenu_travail=base.revenu_emploi_federal, revenu_net=revenu.revenu_net_federal,
    )
    if fonds.conjoint.nom and ((act.present and not act.famille.activer) or (frais_medicaux_effectifs.supplement.reclamer and not frais_medicaux_effectifs.supplement.mode_familial)):
        raise ValueError("Fonds avec conjoint : profil familial ACT/supplément médical non encore couvert.")
    if politiques.nom_conjoint and ((act.present and not act.famille.activer) or (frais_medicaux_effectifs.supplement.reclamer and not frais_medicaux_effectifs.supplement.mode_familial)):
        raise ValueError("Les reçus politiques du conjoint exigent un profil familial; ACT et supplément médical individuels ne couvrent pas cette combinaison.")
    verifier_famille_supplement_2025(frais_medicaux_effectifs.supplement,
        demandeur=dossier.client, medical=medical_familial,
        conjoint_30300=montant_conjoint_federal_effectif,
        personne_30400=personne_charge_admissible_federale_effective,
        conjoint_32600=resultat_conjoint if conjoint.activer else None,
        noms_conjoints=(fonds.conjoint.nom, politiques.nom_conjoint), act_individuel=act.present and not act.famille.activer)
    verifier_concordance_act_familial_2025(act, demandeur=dossier.client,
        medical=medical_familial, supplement=frais_medicaux_effectifs.supplement,
        conjoint_30300=montant_conjoint_federal_effectif,
        personne_30400=personne_charge_admissible_federale_effective,
        conjoint_32600=resultat_conjoint if conjoint.activer else None,
        noms_conjoints=(fonds.conjoint.nom, politiques.nom_conjoint))
    supplement_medical = calculer_supplement_medical_2025(
        frais_medicaux_effectifs.supplement, emploi=base.revenu_emploi_federal,
        deduction_20700=rpa_effectives.montant_federal,
        deduction_21200=cotisations_effectives.montant_federal_admissible,
        deduction_22900=depenses_emploi_effectives.deduction_federale_t777,
        revenu_net=revenu.revenu_net_federal,
        ligne_33200=base_medicale,
    )
    multigenerationnel = renovations_multigenerationnelles if renovations_multigenerationnelles is not None else RenovationsMultigenerationnelles2025()
    resultat_multigenerationnel = calculer_multigenerationnel_2025(multigenerationnel, annee=dossier.annee_fiscale,
        autres_frais_reclames=bool(frais_medicaux_effectifs.montant_admissible_federal or medical_familial.depenses or accessibilite_domiciliaire_federale_effective.depenses_admissibles))
    rapprochement = calculer_rapprochement_fiscal_2025(
        base,
        federal,
        quebec,
        credit_formation=credit_formation_2025(frais_scolarite_effectifs.formation),
        supplement_medical=supplement_medical.ligne_45200,
        allocation_travailleurs=resultat_act.ligne_45300,
        avances_act=resultat_act.ligne_41500,
        credit_multigenerationnel=resultat_multigenerationnel.ligne_45355,
        credit_educateur=resultat_educateur.ligne_46900,
        credit_fonds=resultat_fonds.ligne_41400,
        credit_politique=resultat_politiques.ligne_41000,
        prestations_rqap=prestations_rqap,
        prestations_ae=prestations_ae,
        pensions=pensions,
        retraits=retraits,
        remplacement=remplacement,
        interets=interets,
        placement_etranger=placement_etranger,
        dividendes=dividendes,
        capital=capital,
        prestations_psv=prestations_psv,
        prestations_rrq_rpc=prestations_rrq_rpc,
        cotisation_assurance_medicaments=(
            cotisation_assurance_medicaments_2025(
                assurance_medicaments_effective
            )
        ),
        remboursement_rrq_excedentaire=(
            remboursements_cotisations.rrq_ligne_452
        ),
        remboursement_ae_excedentaire=(
            remboursements_cotisations.assurance_emploi_ligne_45000
        ),
        remboursement_rqap_excedentaire=(
            remboursements_cotisations.rqap_ligne_457
        ),
        cotisations_excedentaires_verifiees=(
            cotisations_excedentaires_presentes
        ),
    )

    if reports_pertes.present:
        rapprochement = replace(rapprochement, limitations=tuple(
            texte.replace("aucun report de perte", "reports de pertes validés séparément en 3F")
            for texte in rapprochement.limitations))
    resultat_pret_etudiant = mesurer_incidence_interets_2025(
        resultat_pret_etudiant, credits_complets, federal.impot_brut,
        dividendes.ligne_40425, credit_impot_etranger.ligne_40500,
    )
    return EstimationFiscale2025(
        frais_medicaux_famille=medical_familial, resultat_medical_familial=resultat_medical_familial,
        transferts_handicap=handicap_transfere, resultat_transferts_handicap=resultat_handicap_transfere,
        renovations_multigenerationnelles=multigenerationnel, resultat_multigenerationnel=resultat_multigenerationnel,
        fournitures_educateur=educateur, resultat_fournitures_educateur=resultat_educateur,
        fonds_travailleurs=fonds, resultat_fonds_travailleurs=resultat_fonds,
        contributions_politiques=politiques, resultat_contributions_politiques=resultat_politiques,
        adoption=adoption_effective, resultat_adoption=resultat_adoption,
        benevoles=benevoles_effectifs, resultat_benevoles=resultat_benevoles,
        transfert_conjoint=conjoint, resultat_transfert_conjoint=resultat_conjoint,
        resultat_reports_dons=reports_dons,
        resultat_reports_scolarite=reports_scolarite,
        transferts_scolarite_recus=scolarite_recue,
        allocation_travailleurs=act, resultat_allocation_travailleurs=resultat_act,
        resultat_supplement_medical=supplement_medical,
        prolongation_carriere_quebec=carriere_quebec, resultat_carriere_quebec=resultat_carriere_quebec,
        achat_habitation_quebec=achat_quebec, resultat_achat_quebec=resultat_achat_quebec,
        interets_etudiants_quebec=pret_quebec, resultat_interets_quebec=resultat_pret_quebec,
        interets_pret_etudiant=pret_etudiant,
        resultat_interets_pret_etudiant=resultat_pret_etudiant,
        ae_confirme=ae_confirme,
        profil_pensions=profil_pensions,
        profil_retraits=profil_retraits,
        profil_remplacement=profil_remplacement,
        profil_interets=profil_interets,
        profil_placement_etranger=profil_placement_etranger,
        placement_etranger=placement_etranger,
        profil_credit_impot_etranger=profil_credit_impot_etranger,
        credit_impot_etranger=credit_impot_etranger,
        profil_dividendes=profil_dividendes,
        profil_reports_pertes=profil_reports_pertes,
        reports_pertes=reports_pertes,
        profil_frais_placement=profil_frais_placement,
        frais_placement=frais_placement,
        profil_capital=profil_capital,
        remplacement=remplacement,
        interets=interets,
        dividendes=dividendes,
        capital=capital,
        psv_confirme=psv_confirme,
        rrq_rpc_confirme=rrq_rpc_confirme,
        rqap_confirme=rqap_confirme,
        prestations_rqap=prestations_rqap,
        prestations_ae=prestations_ae,
        pensions=pensions,
        retraits=retraits,
        prestations_psv=prestations_psv,
        prestations_rrq_rpc=prestations_rrq_rpc,
        cotisations_rpa=rpa_effectives,
        dossier=dossier,
        base=base,
        revenu=revenu,
        federal=federal,
        quebec=quebec,
        rapprochement=rapprochement,
        ajustement_reer=ajustement_reer_effectif,
        deduction_celiapp=deduction_celiapp_effective,
        frais_garde_federaux=frais_garde_federaux_effectifs,
        depenses_emploi=depenses_emploi_effectives,
        frais_demenagement=frais_demenagement_effectifs,
        pension_alimentaire_payee=pension_alimentaire_payee_effective,
        autres_deductions=autres_deductions_effectives,
        cotisations_syndicales=cotisations_effectives,
        dons_bienfaisance=dons_effectifs,
        frais_medicaux=frais_medicaux_effectifs,
        frais_scolarite=frais_scolarite_effectifs,
        credit_deficience=credit_deficience_effectif,
        assurance_medicaments=assurance_medicaments_effective,
        cotisations_excedentaires=(
            cotisations_excedentaires_effectives
        ),
        personne_vivant_seule=personne_vivant_seule_effective,
        montants_age_retraite=montants_age_retraite_effectifs,
        credits_federaux_age_pension=(
            credits_federaux_age_pension_effectifs
        ),
        montant_conjoint_federal=(
            montant_conjoint_federal_effectif
        ),
        personne_charge_admissible_federale=(
            personne_charge_admissible_federale_effective
        ),
        aidant_conjoint_personne_charge_federal=(
            aidant_30425_effectif
        ),
        accessibilite_domiciliaire_federale=(
            accessibilite_domiciliaire_federale_effective
        ),
        achat_habitation_federal=(
            achat_habitation_federal_effectif
        ),
        aidant_autre_personne_charge_federal=(
            aidant_30450_effectif
        ),
        aidant_enfant_federal=(
            aidant_enfant_federal_effectif
        ),
    )


def formater_montant_estimation(valeur: Decimal) -> str:
    """Formate un montant en présentation française."""
    texte = f"{valeur:,.2f}"
    texte = texte.replace(",", "\u00a0").replace(".", ",")
    return f"{texte} $"


def formater_estimation_fiscale_2025(
    estimation: EstimationFiscale2025,
) -> str:
    """Construit le résumé lisible destiné à la fenêtre de validation."""
    base = estimation.base
    revenu = estimation.revenu
    federal = estimation.federal
    quebec = estimation.quebec
    final = estimation.rapprochement

    lignes = [
        "ESTIMATION FISCALE 2025 — VALIDATION COMPTABLE OBLIGATOIRE",
        "",
        f"Client : {estimation.dossier.client}",
        f"Année fiscale : {estimation.dossier.annee_fiscale}",
        f"Province : {estimation.dossier.province}",
        "",
        "REVENU",
        f"Revenu d'emploi fédéral : {formater_montant_estimation(base.revenu_emploi_federal)}",
        f"Revenu net fédéral : {formater_montant_estimation(revenu.revenu_net_federal)}",
        f"Revenu imposable fédéral : {formater_montant_estimation(revenu.revenu_imposable_federal)}",
        f"Revenu d'emploi Québec : {formater_montant_estimation(base.revenu_emploi_quebec)}",
        f"Revenu net Québec : {formater_montant_estimation(revenu.revenu_net_quebec)}",
        f"Revenu imposable Québec : {formater_montant_estimation(revenu.revenu_imposable_quebec)}",
        *lignes_resume_rpa_2025(estimation.cotisations_rpa),
        *lignes_resume_rqap_2025(estimation.prestations_rqap),
        *lignes_resume_ae_2025(estimation.prestations_ae),
        *lignes_resume_reports_pertes_2025(estimation.reports_pertes, estimation.profil_reports_pertes),
        *lignes_resume_frais_placement_2025(estimation.frais_placement, estimation.profil_frais_placement, estimation.reports_pertes.present),
        *lignes_resume_capital_2025(estimation.capital, estimation.profil_capital, estimation.reports_pertes.present),
        *lignes_resume_interets_dividendes_2025(CombinaisonInteretsDividendes2025(
            interets=estimation.interets,
            dividendes=estimation.dividendes,
            assiette_fss=(
                estimation.frais_placement.assiette_fss
                if estimation.frais_placement.present
                else estimation.interets.ligne_130
                + estimation.dividendes.ligne_166
                + estimation.dividendes.ligne_167
                + (estimation.capital.ligne_139 if estimation.capital.present else Decimal("0"))
            ),
            cotisation_fss=estimation.interets.cotisation_fss,
            present=estimation.interets.present and estimation.dividendes.present,
            avec_frais=estimation.frais_placement.present,
            avec_capital=estimation.capital.present,
            avec_reports=estimation.reports_pertes.present,
        )),
        *lignes_resume_dividendes_2025(estimation.dividendes, estimation.profil_dividendes),
        *lignes_resume_interets_2025(estimation.interets, estimation.profil_interets),
        *lignes_resume_placement_etranger_2025(
            estimation.placement_etranger, estimation.profil_placement_etranger
        ),
        *lignes_resume_credit_impot_etranger_2025(
            estimation.credit_impot_etranger, estimation.profil_credit_impot_etranger
        ),
        *lignes_resume_remplacement_2025(estimation.remplacement, estimation.profil_remplacement),
        *lignes_resume_retraits_2025(estimation.retraits, estimation.profil_retraits),
        *lignes_resume_pensions_2025(estimation.pensions, estimation.profil_pensions),
        *lignes_resume_psv_2025(estimation.prestations_psv),
        *lignes_resume_rrq_rpc_2025(estimation.prestations_rrq_rpc),
        *([f"Revenu total fédéral : {formater_montant_estimation(revenu.revenu_total_federal)}",
           f"Revenu total Québec : {formater_montant_estimation(revenu.revenu_total_quebec)}"] if estimation.prestations_rqap.present or estimation.prestations_ae.present or estimation.prestations_rrq_rpc.present or estimation.prestations_psv.present or estimation.pensions.present or estimation.retraits.present or estimation.interets.present or estimation.dividendes.present or estimation.capital.present else []),
        *lignes_resume_celiapp_2025(estimation.deduction_celiapp),
        *lignes_resume_frais_garde_federaux_2025(
            estimation.frais_garde_federaux
        ),
        *lignes_resume_depenses_emploi_2025(
            estimation.depenses_emploi
        ),
        *lignes_resume_frais_demenagement_2025(
            estimation.frais_demenagement
        ),
        *lignes_resume_pension_alimentaire_payee_2025(
            estimation.pension_alimentaire_payee
        ),
        *lignes_reports_dons_federaux_2025(estimation.dons_bienfaisance.reports_federaux, estimation.resultat_reports_dons),
        *lignes_reports_scolarite_federaux_2025(estimation.frais_scolarite.reports_federaux, estimation.resultat_reports_scolarite),
        *lignes_handicap_detaille_2025(estimation.credit_deficience),
        *([f"COMBINAISON 30400 / 30500 — enfant : {estimation.aidant_enfant_federal.reference_enfant}; attribution au même parent validée; 2687 $ uniquement à 30500."]
          if estimation.aidant_enfant_federal.enfant_reclame_30400 else []),
        *lignes_medical_familial_2025(estimation.frais_medicaux_famille, estimation.resultat_medical_familial),
        *lignes_transferts_handicap_2025(estimation.transferts_handicap, estimation.resultat_transferts_handicap),
        *lignes_multigenerationnelles_2025(estimation.renovations_multigenerationnelles, estimation.resultat_multigenerationnel),
        *lignes_fournitures_educateur_2025(estimation.fournitures_educateur, estimation.resultat_fournitures_educateur),
        *lignes_fonds_travailleurs_2025(estimation.fonds_travailleurs, estimation.resultat_fonds_travailleurs, estimation.rapprochement),
        *lignes_contributions_politiques_2025(estimation.contributions_politiques, estimation.resultat_contributions_politiques, estimation.rapprochement),
        *lignes_adoption_2025(estimation.adoption, estimation.resultat_adoption),
        *lignes_benevoles_2025(estimation.benevoles, estimation.resultat_benevoles),
        *lignes_annexe_b_combinee_2025(estimation.personne_vivant_seule, estimation.montants_age_retraite),
        *lignes_transfert_conjoint_2025(estimation.transfert_conjoint, estimation.resultat_transfert_conjoint),
        *lignes_transferts_scolarite_recus_2025(estimation.transferts_scolarite_recus),
        *lignes_allocation_travailleurs_2025(estimation.allocation_travailleurs, estimation.resultat_allocation_travailleurs),
        *lignes_supplement_medical_2025(estimation.frais_medicaux.supplement, estimation.resultat_supplement_medical),
        *lignes_formation_2025(estimation.frais_scolarite.formation),
        *lignes_carriere_quebec_2025(estimation.prolongation_carriere_quebec, estimation.resultat_carriere_quebec),
        *lignes_achat_quebec_2025(estimation.achat_habitation_quebec, estimation.resultat_achat_quebec),
        *lignes_interets_quebec_2025(estimation.interets_etudiants_quebec, estimation.resultat_interets_quebec),
        *lignes_resume_interets_pret_etudiant_2025(
            estimation.interets_pret_etudiant, estimation.resultat_interets_pret_etudiant
        ),
        *lignes_resume_autres_deductions_2025(
            estimation.autres_deductions
        ),
        *(
            [
                "",
                "AJUSTEMENTS VALIDÉS",
                "Déduction REER/RPAC/RVER : "
                f"{formater_montant_estimation(estimation.ajustement_reer.deduction_reer)}",
                "Plafond individuel confirmé : "
                f"{formater_montant_estimation(estimation.ajustement_reer.plafond_reer_confirme)}",
                "Source du plafond : "
                f"{estimation.ajustement_reer.source_plafond_reer}",
            ]
            if estimation.ajustement_reer.deduction_reer
            > Decimal("0")
            else []
        ),
        *(
            [
                "",
                "COTISATIONS SYNDICALES / PROFESSIONNELLES VALIDÉES",
                "Cotisations fédérales — ligne 21200 : "
                f"{formater_montant_estimation(estimation.cotisations_syndicales.montant_federal_admissible)}",
                "Source fédérale : "
                f"{estimation.cotisations_syndicales.source_federale}",
                "Base Québec — ligne 397.1 : "
                f"{formater_montant_estimation(estimation.cotisations_syndicales.montant_quebec_admissible)}",
                "Crédit Québec (10 %) : "
                f"{formater_montant_estimation(credit_quebec_cotisations_2025(estimation.cotisations_syndicales))}",
                "Source Québec : "
                f"{estimation.cotisations_syndicales.source_quebec}",
            ]
            if (
                estimation.cotisations_syndicales.montant_federal_admissible
                > Decimal("0")
                or estimation.cotisations_syndicales.montant_quebec_admissible
                > Decimal("0")
            )
            else []
        ),
        *(
            [
                "",
                "DONS DE BIENFAISANCE VALIDÉS",
                "Montant admissible fédéral : "
                f"{formater_montant_estimation(estimation.dons_bienfaisance.montant_admissible_federal)}",
                "Crédit fédéral — ligne 34900 : "
                f"{formater_montant_estimation(credit_federal_dons_2025(estimation.dons_bienfaisance, revenu.revenu_imposable_federal))}",
                "Source fédérale : "
                f"{estimation.dons_bienfaisance.source_federale}",
                "Montant admissible Québec : "
                f"{formater_montant_estimation(estimation.dons_bienfaisance.montant_admissible_quebec)}",
                "Crédit Québec — ligne 395 : "
                f"{formater_montant_estimation(credit_quebec_dons_2025(estimation.dons_bienfaisance, revenu.revenu_imposable_quebec))}",
                "Source Québec : "
                f"{estimation.dons_bienfaisance.source_quebec}",
            ]
            if (
                estimation.dons_bienfaisance.reports_federaux.activer
                or estimation.dons_bienfaisance.montant_admissible_federal
                > Decimal("0")
                or estimation.dons_bienfaisance.montant_admissible_quebec
                > Decimal("0")
            )
            else []
        ),
        *(
            [
                "",
                "FRAIS MÉDICAUX VALIDÉS",
                "Montant admissible fédéral : "
                f"{formater_montant_estimation(estimation.frais_medicaux.montant_admissible_federal)}",
                "Crédit fédéral — lignes 33099 / 33200 : "
                f"{formater_montant_estimation(credit_federal_frais_medicaux_2025(estimation.frais_medicaux, revenu.revenu_net_federal))}",
                "Source fédérale : "
                f"{estimation.frais_medicaux.source_federale}",
                "Montant admissible Québec : "
                f"{formater_montant_estimation(estimation.frais_medicaux.montant_admissible_quebec)}",
                "Crédit Québec — ligne 381 : "
                f"{formater_montant_estimation(credit_quebec_frais_medicaux_2025(estimation.frais_medicaux, revenu.revenu_net_quebec))}",
                "Source Québec : "
                f"{estimation.frais_medicaux.source_quebec}",
            ]
            if (
                estimation.frais_medicaux.montant_admissible_federal
                > Decimal("0")
                or estimation.frais_medicaux.montant_admissible_quebec
                > Decimal("0")
            )
            else []
        ),
        *(
            [
                "",
                "FRAIS DE SCOLARITÉ / EXAMEN VALIDÉS",
                "Montant admissible fédéral : "
                f"{formater_montant_estimation(estimation.frais_scolarite.montant_admissible_federal)}",
                "Crédit fédéral — ligne 32300 : "
                f"{formater_montant_estimation(credit_federal_frais_scolarite_2025(estimation.frais_scolarite, resultat_reports=estimation.resultat_reports_scolarite))}",
                "Source fédérale : "
                f"{estimation.frais_scolarite.source_federale}",
                "Montant admissible Québec : "
                f"{formater_montant_estimation(estimation.frais_scolarite.montant_admissible_quebec)}",
                "Crédit Québec — ligne 398 : "
                f"{formater_montant_estimation(credit_quebec_frais_scolarite_2025(estimation.frais_scolarite))}",
                "Source Québec : "
                f"{estimation.frais_scolarite.source_quebec}",
            ]
            if (
                estimation.frais_scolarite.montant_admissible_federal
                > Decimal("0")
                or estimation.frais_scolarite.montant_admissible_quebec
                > Decimal("0")
            )
            else []
        ),
        *(
            [
                "",
                "HANDICAP / DÉFICIENCE VALIDÉ(E)",
                *(
                    [
                        "Montant fédéral — ligne 31600 : "
                        "10 138,00 $",
                        "Crédit fédéral — ligne 31600 : "
                        f"{formater_montant_estimation(credit_federal_handicap_2025(estimation.credit_deficience))}",
                        "Source fédérale : "
                        f"{estimation.credit_deficience.source_federale}",
                    ]
                    if estimation.credit_deficience.reclamer_federal
                    else []
                ),
                *(
                    [
                        "Montant Québec — ligne 376 : "
                        "4 123,00 $",
                        "Crédit Québec — ligne 376 : "
                        f"{formater_montant_estimation(credit_quebec_deficience_2025(estimation.credit_deficience))}",
                        "Source Québec : "
                        f"{estimation.credit_deficience.source_quebec}",
                    ]
                    if estimation.credit_deficience.reclamer_quebec
                    else []
                ),
            ]
            if (
                estimation.credit_deficience.reclamer_federal
                or estimation.credit_deficience.reclamer_quebec
            )
            else []
        ),
        *(
            [
                "",
                "ASSURANCE MÉDICAMENTS QUÉBEC VALIDÉE",
                (
                    "Type de couverture : "
                    + (
                        "Régime public"
                        if (
                            estimation.assurance_medicaments
                            .type_couverture.strip().lower()
                            == "public"
                        )
                        else "Couverture collective"
                    )
                ),
                "Revenu net Québec / ligne 275 : "
                f"{formater_montant_estimation(estimation.assurance_medicaments.revenu_ligne_275)}",
                "Ligne 48 — annexe K : "
                f"{formater_montant_estimation(estimation.assurance_medicaments.revenu_ligne_48_annexe_k)}",
                "Cotisation Québec — ligne 447 : "
                f"{formater_montant_estimation(estimation.rapprochement.cotisation_assurance_medicaments)}",
                *(
                    [
                        "Code d'exemption — case 449 : "
                        f"{code_exemption_case_449_2025(estimation.assurance_medicaments)}",
                    ]
                    if code_exemption_case_449_2025(
                        estimation.assurance_medicaments
                    )
                    else []
                ),
                "Source : "
                f"{estimation.assurance_medicaments.source}",
            ]
            if estimation.assurance_medicaments.type_couverture.strip()
            else []
        ),
        *(
            [
                "",
                "PERSONNE VIVANT SEULE — QUÉBEC 2025",
                "Revenu familial net : "
                f"{formater_montant_estimation(estimation.personne_vivant_seule.revenu_familial_net)}",
                "Montant annexe B / ligne 361 : "
                f"{formater_montant_estimation(montant_ligne_361_personne_vivant_seule_2025(estimation.personne_vivant_seule))}",
                "Crédit Québec : "
                f"{formater_montant_estimation(credit_quebec_personne_vivant_seule_2025(estimation.personne_vivant_seule))}",
                "Source : "
                f"{estimation.personne_vivant_seule.source}",
            ]
            if estimation.personne_vivant_seule.reclamer_montant and not estimation.personne_vivant_seule.combinaison_annexe_b_confirmee
            else []
        ),
        *(
            [
                "",
                "ACCESSIBILITÉ DOMICILIAIRE — FÉDÉRAL 2025",
                (
                    "Dépenses admissibles — ligne 31285 : "
                    f"{formater_montant_estimation(
                        montant_ligne_31285_2025(
                            estimation.accessibilite_domiciliaire_federale
                        )
                    )}"
                ),
                (
                    "Crédit fédéral calculé : "
                    f"{formater_montant_estimation(
                        credit_federal_ligne_31285_2025(
                            estimation.accessibilite_domiciliaire_federale
                        )
                    )}"
                ),
                "Taux du crédit fédéral 2025 : 14,5 %",
                "Maximum ligne 31285 : 20 000 $",
                "Particulier déterminé : 65 ans ou plus / CIPH",
                "Demande pour soi-même : oui",
                "Logement admissible situé au Canada : oui",
                "Logement appartenant au contribuable : oui",
                "Logement normalement habité par le contribuable : oui",
                "Rénovation durable et intégrante : oui",
                "Accessibilité / mobilité / réduction du risque : confirmée",
                "Travaux et biens de 2025 uniquement : oui",
                "Aucune part entreprise/location : oui",
                description_partage_31285_2025(estimation.accessibilite_domiciliaire_federale),
                "Fournisseurs liés : règles confirmées",
                "Dépenses non admissibles exclues : oui",
                "Pièces justificatives conservées : oui",
                "Validation comptable : confirmée",
                (
                    "Source : "
                    f"{estimation.accessibilite_domiciliaire_federale.source_renovation}"
                ),
            ]
            if estimation.accessibilite_domiciliaire_federale.reclamer_montant
            else []
        ),
        *(
            [
                "",
                "ACHAT D'UNE HABITATION — FÉDÉRAL 2025",
                (
                    "Montant réclamé — ligne 31270 : "
                    f"{formater_montant_estimation(
                        montant_ligne_31270_2025(
                            estimation.achat_habitation_federal
                        )
                    )}"
                ),
                (
                    "Crédit fédéral calculé : "
                    f"{formater_montant_estimation(
                        credit_federal_ligne_31270_2025(
                            estimation.achat_habitation_federal
                        )
                    )}"
                ),
                "Taux du crédit fédéral 2025 : 14,5 %",
                "Maximum ligne 31270 : 10 000 $",
                "Acquisition en 2025 : oui",
                "Habitation admissible située au Canada : oui",
                "Habitation enregistrée au nom du contribuable ou du conjoint : oui",
                "Première habitation : confirmée",
                "Aucune habitation possédée et habitée pendant l'année de l'achat ou les quatre années précédentes : oui",
                "Intention de résidence principale dans un an : oui",
                description_partage_31270_2025(estimation.achat_habitation_federal),
                "Exception handicap non utilisée dans ce profil simple : oui",
                "Pièces justificatives conservées : oui",
                "Validation comptable : confirmée",
                (
                    "Source : "
                    f"{estimation.achat_habitation_federal.source_habitation}"
                ),
            ]
            if estimation.achat_habitation_federal.reclamer_montant
            else []
        ),
        *(["", "AIDANTS — PERSONNES À CHARGE 30450", *details_personnes_30450_2025(estimation.aidant_autre_personne_charge_federal),
            f"Total ligne 30450 : {montant_ligne_30450_2025(estimation.aidant_autre_personne_charge_federal):.2f} $; "
            f"nombre ligne 51120 : {nombre_personnes_charge_ligne_51120_2025(estimation.aidant_autre_personne_charge_federal)}; "
            "crédit calculé à 14,5 % de la somme des parts, arrondi une fois."]
          if estimation.aidant_autre_personne_charge_federal.personnes_detaillees else []),
        *(
            [
                "",
                "AIDANT NATUREL — AUTRE PERSONNE À CHARGE 18+ — FÉDÉRAL 2025",
                (
                    "Nombre de personnes à charge — ligne 51120 : "
                    f"{nombre_personnes_charge_ligne_51120_2025(estimation.aidant_autre_personne_charge_federal)}"
                ),
                (
                    "Lien familial : "
                    f"{estimation.aidant_autre_personne_charge_federal.lien_personne}"
                ),
                (
                    "Revenu net de la personne — ligne 23600 : "
                    f"{formater_montant_estimation(estimation.aidant_autre_personne_charge_federal.revenu_net_personne_ligne_23600)}"
                ),
                (
                    "Montant canadien pour aidant naturel — ligne 30450 : "
                    f"{formater_montant_estimation(montant_ligne_30450_2025(estimation.aidant_autre_personne_charge_federal))}"
                ),
                (
                    "Crédit fédéral calculé : "
                    f"{formater_montant_estimation(credit_federal_ligne_30450_2025(estimation.aidant_autre_personne_charge_federal))}"
                ),
                "Taux du crédit fédéral 2025 : 14,5 %",
                "Personne à charge de 18 ans ou plus : oui",
                "Infirmité physique ou mentale confirmée : oui",
                "Dépendance due à l'infirmité : oui",
                "Dépendance pendant une période considérable : oui",
                "Aucune ligne 30300/30400 pour cette même personne : oui",
                "Aucune pension alimentaire pour cette personne : oui",
                description_partage_30450_2025(estimation.aidant_autre_personne_charge_federal),
                "Preuve médicale ou T2201 : confirmée",
                "Validation comptable : confirmée",
                (
                    "Source : "
                    f"{estimation.aidant_autre_personne_charge_federal.source_personne}"
                ),
            ]
            if (
                estimation.aidant_autre_personne_charge_federal
                .reclamer_montant and not estimation.aidant_autre_personne_charge_federal.personnes_detaillees
            )
            else []
        ),
        *(["", "AIDANTS — ENFANTS 30500", *details_enfants_30500_2025(estimation.aidant_enfant_federal),
            f"Nombre ligne 30499 : {len(estimation.aidant_enfant_federal.enfants_detailles)}; "
            f"total ligne 30500 : {montant_ligne_30500_2025(estimation.aidant_enfant_federal):.2f} $; "
            "crédit à 14,5 % du total arrondi une fois."] if estimation.aidant_enfant_federal.enfants_detailles else []),
        *(
            [
                "",
                "AIDANT NATUREL — ENFANT DE MOINS DE 18 ANS — FÉDÉRAL 2025",
                "Nombre d'enfants — ligne 30499 : 1",
                (
                    "Montant canadien pour aidant naturel — ligne 30500 : "
                    f"{formater_montant_estimation(
                        montant_ligne_30500_2025(
                            estimation.aidant_enfant_federal
                        )
                    )}"
                ),
                (
                    "Crédit fédéral calculé : "
                    f"{formater_montant_estimation(
                        credit_federal_aidant_enfant_moins18_2025(
                            estimation.aidant_enfant_federal
                        )
                    )}"
                ),
                "Taux du crédit fédéral 2025 : 14,5 %",
                "Enfant de moins de 18 ans : oui",
                "Infirmité physique ou mentale confirmée : oui",
                "Besoin de beaucoup plus d'aide que les enfants du même âge : oui",
                ("Même enfant réclamé à 30400/30500 : " + estimation.aidant_enfant_federal.reference_enfant if estimation.aidant_enfant_federal.enfant_reclame_30400 else "Enfant avec ses deux parents toute l'année : oui"),
                "Aucune garde partagée : oui",
                "Aucune pension alimentaire : oui",
                "Aucun autre réclamant ligne 30500 : oui",
                "Aucun transfert au conjoint ligne 32600 : oui",
                "Preuve médicale ou T2201 : confirmée",
                "Validation comptable : confirmée",
                (
                    "Source : "
                    f"{estimation.aidant_enfant_federal.source_enfant}"
                ),
            ]
            if estimation.aidant_enfant_federal.reclamer_montant and not estimation.aidant_enfant_federal.enfants_detailles
            else []
        ),
        *(
            [
                "",
                "PERSONNE À CHARGE ADMISSIBLE — FÉDÉRAL 2025",
                (
                    "Revenu net du contribuable — ligne 23600 : "
                    f"{formater_montant_estimation(
                        estimation.personne_charge_admissible_federale
                        .revenu_net_contribuable_ligne_23600
                    )}"
                ),
                (
                    "Revenu net de la personne à charge : "
                    f"{formater_montant_estimation(
                        estimation.personne_charge_admissible_federale
                        .revenu_net_personne_charge_2025
                    )}"
                ),
                (
                    "Ligne 30400 : "
                    f"{formater_montant_estimation(
                        montant_ligne_30400_2025(
                            estimation.personne_charge_admissible_federale
                        )
                    )}"
                ),
                (
                    "Crédit fédéral calculé : "
                    f"{formater_montant_estimation(
                        credit_federal_personne_charge_admissible_2025(
                            estimation.personne_charge_admissible_federale
                        )
                    )}"
                ),
                "Taux du crédit fédéral 2025 : 14,5 %",
                "Personne à charge : enfant de moins de 18 ans",
                "Aucune garde partagée : oui",
                "Aucune pension alimentaire : oui",
                ("Infirmité de l'enfant : confirmée; supplément distinct à 30500" if estimation.personne_charge_admissible_federale.enfant_infirmite_ligne30500 else "Aucune déficience de l'enfant : oui"),
                "Validation comptable : confirmée",
                (
                    "Source : "
                    f"{estimation.personne_charge_admissible_federale.source_personne_charge}"
                ),
            ]
            if estimation.personne_charge_admissible_federale.reclamer_montant
            else []
        ),
        *(
            [
                "",
                "ÉPOUX / CONJOINT DE FAIT — FÉDÉRAL 2025",
                (
                    "Revenu net du contribuable — ligne 23600 : "
                    f"{formater_montant_estimation(
                        estimation.montant_conjoint_federal
                        .revenu_net_contribuable_ligne_23600
                    )}"
                ),
                (
                    "Revenu net du conjoint : "
                    f"{formater_montant_estimation(
                        estimation.montant_conjoint_federal
                        .revenu_net_conjoint_2025
                    )}"
                ),
                (
                    "Ligne 30300 : "
                    f"{formater_montant_estimation(
                        montant_ligne_30300_2025(
                            estimation.montant_conjoint_federal
                        )
                    )}"
                ),
                (
                    "Crédit fédéral calculé : "
                    f"{formater_montant_estimation(
                        credit_federal_montant_conjoint_2025(
                            estimation.montant_conjoint_federal
                        )
                    )}"
                ),
                "Taux du crédit fédéral 2025 : 14,5 %",
                "Même conjoint toute l'année 2025 : oui",
                "Aucune séparation/réconciliation : oui",
                "Conjoint résident du Canada toute l'année : oui",
                "Un seul conjoint réclame le montant : oui",
                "Validation comptable : confirmée",
                (
                    "Source : "
                    f"{estimation.montant_conjoint_federal.source_conjoint}"
                ),
            ]
            if estimation.montant_conjoint_federal.reclamer_montant
            else []
        ),
        *(
            [
                "",
                "ÂGE / PENSION — FÉDÉRAL 2025",
                (
                    "Revenu net fédéral — ligne 23600 : "
                    f"{formater_montant_estimation(
                        estimation.credits_federaux_age_pension
                        .revenu_net_ligne_23600
                    )}"
                ),
                (
                    "Montant en raison de l'âge — ligne 30100 : "
                    f"{formater_montant_estimation(
                        montant_age_federal_2025(
                            estimation.credits_federaux_age_pension
                        )
                    )}"
                ),
                (
                    "Montant pour revenu de pension — ligne 31400 : "
                    f"{formater_montant_estimation(
                        montant_pension_federal_2025(
                            estimation.credits_federaux_age_pension
                        )
                    )}"
                ),
                (
                    "Crédit fédéral calculé : "
                    f"{formater_montant_estimation(
                        credit_federal_age_pension_2025(
                            estimation.credits_federaux_age_pension
                        )
                    )}"
                ),
                *(
                    [
                        "Source âge : "
                        f"{estimation.credits_federaux_age_pension.source_age}"
                    ]
                    if estimation.credits_federaux_age_pension.reclamer_montant_age
                    else []
                ),
                *(
                    [
                        "Source pension : "
                        f"{estimation.credits_federaux_age_pension.source_pension}"
                    ]
                    if estimation.credits_federaux_age_pension.reclamer_montant_pension
                    else ["Ligne 31400 non réclamée"]
                ),
                "Fractionnement T1032 : non",
                "Transfert entre conjoints : non",
                "Validation comptable : confirmée",
            ]
            if (
                estimation.credits_federaux_age_pension.reclamer_montant_age
                or estimation.credits_federaux_age_pension.reclamer_montant_pension
            )
            else []
        ),
        *(
            [
                "",
                "ÂGE / REVENUS DE RETRAITE — QUÉBEC 2025",
                "Revenu familial net : "
                f"{formater_montant_estimation(estimation.montants_age_retraite.revenu_familial_net)}",
                *(
                    [
                        "Montant âge — annexe B ligne 22 : "
                        f"{formater_montant_estimation(montant_age_2025(estimation.montants_age_retraite))}",
                        "Source âge : "
                        f"{estimation.montants_age_retraite.source_age}",
                    ]
                    if estimation.montants_age_retraite.reclamer_age
                    else []
                ),
                *(
                    [
                        "Revenu retraite net admissible : "
                        f"{formater_montant_estimation(revenu_retraite_net_admissible_2025(estimation.montants_age_retraite))}",
                        "Montant revenus de retraite : "
                        f"{formater_montant_estimation(montant_revenus_retraite_2025(estimation.montants_age_retraite))}",
                        "Source retraite : "
                        f"{estimation.montants_age_retraite.source_retraite}",
                    ]
                    if (
                        estimation.montants_age_retraite
                        .reclamer_revenus_retraite
                    )
                    else []
                ),
                "Montant annexe B / ligne 361 : "
                f"{formater_montant_estimation(montant_ligne_361_age_retraite_2025(estimation.montants_age_retraite))}",
                "Crédit Québec : "
                f"{formater_montant_estimation(credit_quebec_age_retraite_2025(estimation.montants_age_retraite))}",
            ]
            if not estimation.montants_age_retraite.combinaison_annexe_b_confirmee and (
                estimation.montants_age_retraite.reclamer_age
                or (
                    estimation.montants_age_retraite
                    .reclamer_revenus_retraite
                )
            )
            else []
        ),
        *(
            [
                "",
                "COTISATIONS EXCÉDENTAIRES VALIDÉES",
                "RRQ — ligne Québec 452 : "
                f"{formater_montant_estimation(final.remboursement_rrq_excedentaire)}",
                "Assurance-emploi — ligne fédérale 45000 : "
                f"{formater_montant_estimation(final.remboursement_ae_excedentaire)}",
                "RQAP — ligne Québec 457 : "
                f"{formater_montant_estimation(final.remboursement_rqap_excedentaire)}",
                "Total remboursable : "
                f"{formater_montant_estimation(final.remboursements_cotisations_totaux)}",
                "Source : "
                f"{estimation.cotisations_excedentaires.source}",
            ]
            if (
                estimation.cotisations_excedentaires
                != CotisationsExcedentaires2025()
            )
            else []
        ),
        "",
        *lignes_resume_credit_compensatoire_2025(federal.credits_federaux_complets),
        "FÉDÉRAL",
        f"Impôt fédéral brut : {formater_montant_estimation(federal.impot_brut)}",
        f"Crédits non remboursables de base emploi : {formater_montant_estimation(federal.credits_non_remboursables)}",
        f"Impôt fédéral de base : {formater_montant_estimation(final.impot_federal_de_base)}",
        *([
            f"Ligne 42900 avant crédit étranger : {formater_montant_estimation(final.impot_federal_de_base)}",
            f"Crédit étranger utilisable 40500 : {formater_montant_estimation(final.credit_etranger_ligne_40500)}",
            f"Impôt fédéral après ligne 40500 : {formater_montant_estimation(final.impot_federal_apres_credit_etranger)}",
        ] if estimation.credit_impot_etranger.present else []),
        f"Abattement Québec (16,5 %) : -{formater_montant_estimation(final.abattement_quebec)}",
        f"Impôt fédéral après abattement : {formater_montant_estimation(final.impot_federal_apres_abattement)}",
        "",
        "QUÉBEC",
        f"Impôt Québec brut : {formater_montant_estimation(quebec.impot_brut)}",
        f"Crédit personnel de base : -{formater_montant_estimation(quebec.credit_personnel_base)}",
        f"Impôt Québec préliminaire : {formater_montant_estimation(final.impot_quebec_preliminaire)}",
        "",
        "RAPPROCHEMENT",
        f"Impôt total préliminaire : {formater_montant_estimation(final.impot_total_preliminaire)}",
        ("Retenue fédérale T4 + T4E : " if estimation.prestations_rqap.present or estimation.prestations_ae.present else ("Retenue fédérale T4 + T4A(P) : " if estimation.base.nombre_t4 else "Retenue fédérale T4A(P) : ") if estimation.prestations_rrq_rpc.present else ("Retenue fédérale " + ("T4 + " if estimation.base.nombre_t4 else "") + "T4A(OAS) : ") if estimation.prestations_psv.present else "Retenues fédérales emploi et pensions : " if estimation.pensions.present else "Retenues fédérales emploi et retraits : " if estimation.retraits.present else "Retenue fédérale T4 : ") + formater_montant_estimation(final.retenue_federale),
        ("Retenue Québec RL-1 + RL-6 : " if estimation.prestations_rqap.present else "Retenue Québec RL-1 + T4E : " if estimation.prestations_ae.present else ("Retenue Québec " + ("RL-1 + " if estimation.base.nombre_rl1 else "") + ("RL-2 : " if estimation.prestations_rrq_rpc.releve_2_present else "(aucun RL-2 reçu) : ")) if estimation.prestations_rrq_rpc.present else ("Retenue Québec " + ("RL-1 + " if estimation.base.nombre_rl1 else "") + "T4A(OAS) : ") if estimation.prestations_psv.present else "Retenues Québec emploi et pensions : " if estimation.pensions.present else "Retenues Québec emploi et retraits : " if estimation.retraits.present else "Retenue Québec RL-1 : ") + formater_montant_estimation(final.retenue_quebec),
        f"Retenues totales : {formater_montant_estimation(final.retenues_totales)}",
        "",
        f"RÉSULTAT : {final.resultat}",
    ]

    if final.remboursement_estime > Decimal("0"):
        lignes.append(
            "Montant : "
            f"{formater_montant_estimation(final.remboursement_estime)}"
        )
    elif final.solde_estime > Decimal("0"):
        lignes.append(
            "Montant : "
            f"{formater_montant_estimation(final.solde_estime)}"
        )
    else:
        lignes.append("Montant : 0,00 $")

    lignes.extend(
        [
            "",
            f"Statut : {final.statut}",
            "",
            "LIMITATIONS ACTUELLES",
        ]
    )

    for limitation in final.limitations:
        lignes.append(f"• {limitation}")

    lignes.extend(
        [
            "",
            "Aucune donnée n'a quitté l'ordinateur.",
            "Aucune déclaration n'a été transmise à l'ARC "
            "ou à Revenu Québec.",
        ]
    )

    return "\n".join(lignes)
