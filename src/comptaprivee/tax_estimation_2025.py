"""Orchestration de l'estimation fiscale locale 2025.

Ce module relie les briques déjà validées :
dossier fiscal verrouillé -> consolidation -> revenu -> fédéral -> Québec
-> rapprochement.

Il ne transmet aucune déclaration et conserve explicitement le statut
d'estimation soumise à validation comptable.
"""

from dataclasses import dataclass, replace
from decimal import Decimal

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
from .tax_contribution_overpayments_2025 import (
    CotisationsExcedentaires2025,
    calculer_remboursements_cotisations_2025,
    valider_cotisations_excedentaires_2025,
)
from .tax_donations_2025 import (
    DonsBienfaisance2025,
    appliquer_credit_federal_dons_2025,
    appliquer_credit_quebec_dons_2025,
    credit_federal_dons_2025,
    credit_quebec_dons_2025,
)
from .tax_disability_2025 import (
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
    appliquer_credit_federal_frais_medicaux_2025,
    appliquer_credit_quebec_frais_medicaux_2025,
    credit_federal_frais_medicaux_2025,
    credit_quebec_frais_medicaux_2025,
)
from .tax_tuition_2025 import (
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
    DepensesAccessibiliteDomiciliaireFederal2025,
    appliquer_credit_federal_ligne_31285_2025,
    credit_federal_ligne_31285_2025,
    integration_31285_sans_credit_compensatoire_autorisee_2025,
    montant_ligne_31285_2025,
    valider_depenses_accessibilite_domiciliaire_2025,
)
from .tax_federal_home_buyers_2025 import (
    MontantAchatHabitationFederal2025,
    appliquer_credit_federal_ligne_31270_2025,
    credit_federal_ligne_31270_2025,
    integration_31270_sans_credit_compensatoire_autorisee_2025,
    montant_ligne_31270_2025,
    valider_montant_achat_habitation_2025,
)
from .tax_federal_caregiver_other_dependant_2025 import (
    AidantNaturelAutrePersonneChargeFederal2025,
    appliquer_credit_federal_ligne_30450_2025,
    credit_federal_ligne_30450_2025,
    integration_30450_sans_credit_compensatoire_autorisee_2025,
    montant_ligne_30450_2025,
    nombre_personnes_charge_ligne_51120_2025,
    valider_aidant_naturel_30450_2025,
)
from .tax_federal_caregiver_spouse_dependant_2025 import (
    TYPE_CONJOINT,
    TYPE_PERSONNE_CHARGE_ADMISSIBLE,
    AidantNaturelConjointOuPersonneChargeFederal2025,
    appliquer_credit_federal_ligne_30425_2025,
    integration_sans_credit_compensatoire_autorisee_2025 as integration_aidant_30425_sans_34990_2025,
    valider_aidant_naturel_30425_2025,
)
from .tax_federal_caregiver_child_2025 import (
    AidantNaturelEnfantMoins18Federal2025,
    appliquer_credit_federal_aidant_enfant_moins18_2025,
    credit_federal_aidant_enfant_moins18_2025,
    integration_sans_credit_compensatoire_autorisee_2025 as integration_aidant_enfant_sans_34990_2025,
    montant_ligne_30500_2025,
    nombre_enfants_ligne_30499_2025,
    valider_aidant_naturel_enfant_moins18_federal_2025,
)
from .tax_federal_eligible_dependant_2025 import (
    MontantPersonneChargeAdmissibleFederal2025,
    appliquer_credit_federal_personne_charge_admissible_2025,
    credit_federal_personne_charge_admissible_2025,
    integration_sans_credit_compensatoire_autorisee_2025 as integration_personne_charge_sans_34990_2025,
    montant_ligne_30400_2025,
    valider_montant_personne_charge_admissible_federal_2025,
)
from .tax_federal_spouse_2025 import (
    MontantConjointFederal2025,
    appliquer_credit_federal_montant_conjoint_2025,
    credit_federal_montant_conjoint_2025,
    integration_sans_credit_compensatoire_autorisee_2025 as integration_montant_conjoint_sans_34990_2025,
    montant_ligne_30300_2025,
    valider_montant_conjoint_federal_2025,
)
from .tax_federal_age_pension_2025 import (
    CreditsFederauxAgePension2025,
    appliquer_credit_federal_age_pension_2025,
    credit_federal_age_pension_2025,
    integration_sans_credit_compensatoire_autorisee_2025,
    montant_age_federal_2025,
    montant_pension_federal_2025,
    valider_credits_federaux_age_pension_2025,
)
from .tax_federal_2025 import (
    ImpotFederalPreliminaire2025,
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


def calculer_estimation_fiscale_2025(
    dossier: DossierFiscalValide,
    ajustement_reer: AjustementReer2025 | None = None,
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
) -> EstimationFiscale2025:
    """Exécute le pipeline fiscal local 2025 sur un dossier verrouillé."""
    if dossier.annee_fiscale != 2025:
        raise ValueError(
            "L'estimation fiscale automatique est disponible "
            "uniquement pour l'année 2025."
        )

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
                parcours_etranger
                or profil_frais_placement != ProfilFraisPlacement2025()
                or profil_reports_pertes != ProfilReportsPertes2025()
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
        # En 3H-B, la FSS finale reste portée une seule fois par le résultat intérêts;
        # la recopier aussi sur les dividendes la compterait deux fois.
        if interets.present and dividendes.present and not capital.present:
            interets = replace(
                interets,
                cotisation_fss=frais_placement.cotisation_fss,
            )
            dividendes = replace(
                dividendes,
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

    if (
        age_retraite_actif
        and personne_vivant_seule_effective.reclamer_montant
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

    if (
        age_pension_federal_actif
        and not integration_sans_credit_compensatoire_autorisee_2025(
            revenu.revenu_imposable_federal
        )
    ):
        raise ValueError(
            "Ce dossier peut nécessiter le crédit compensatoire "
            "fédéral de la ligne 34990. Cette première version "
            "refuse le calcul automatique au-delà de la première "
            "tranche tant que la ligne 34990 n'est pas intégrée."
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

    if (
        montant_conjoint_federal_effectif.reclamer_montant
        and not integration_montant_conjoint_sans_34990_2025(
            revenu.revenu_imposable_federal
        )
    ):
        raise ValueError(
            "Ce dossier peut nécessiter le crédit compensatoire "
            "fédéral de la ligne 34990. Cette première version "
            "refuse le montant conjoint automatique au-delà de la "
            "première tranche tant que la ligne 34990 n'est pas "
            "intégrée complètement."
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

    if (
        personne_charge_admissible_federale_effective.reclamer_montant
        and not integration_personne_charge_sans_34990_2025(
            revenu.revenu_imposable_federal
        )
    ):
        raise ValueError(
            "Ce dossier peut nécessiter le crédit compensatoire "
            "fédéral de la ligne 34990. Cette première version "
            "refuse la ligne 30400 automatique au-delà de la "
            "première tranche tant que la ligne 34990 n'est pas "
            "intégrée complètement."
        )

    aidant_30425_effectif = (
        aidant_conjoint_personne_charge_federal
        if aidant_conjoint_personne_charge_federal is not None
        else AidantNaturelConjointOuPersonneChargeFederal2025()
    )
    valider_aidant_naturel_30425_2025(aidant_30425_effectif)

    if aidant_30425_effectif.reclamer_montant:
        if not integration_aidant_30425_sans_34990_2025(
            revenu.revenu_imposable_federal
        ):
            raise ValueError(
                "Cette première version refuse la ligne 30425 automatique "
                "au-delà de la première tranche tant que la ligne 34990 "
                "n'est pas intégrée complètement."
            )

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

    if (
        accessibilite_domiciliaire_federale_effective.reclamer_montant
        and not integration_31285_sans_credit_compensatoire_autorisee_2025(
            revenu.revenu_imposable_federal
        )
    ):
        raise ValueError(
            "Ce dossier peut nécessiter le crédit compensatoire "
            "fédéral de la ligne 34990. Cette première version "
            "refuse la ligne 31285 automatique au-delà de la "
            "première tranche tant que la ligne 34990 n'est pas "
            "intégrée complètement."
        )

    achat_habitation_federal_effectif = (
        achat_habitation_federal
        if achat_habitation_federal is not None
        else MontantAchatHabitationFederal2025()
    )
    valider_montant_achat_habitation_2025(
        achat_habitation_federal_effectif
    )

    if (
        achat_habitation_federal_effectif.reclamer_montant
        and not integration_31270_sans_credit_compensatoire_autorisee_2025(
            revenu.revenu_imposable_federal
        )
    ):
        raise ValueError(
            "Ce dossier peut nécessiter le crédit compensatoire "
            "fédéral de la ligne 34990. Cette première version "
            "refuse la ligne 31270 automatique au-delà de la "
            "première tranche tant que la ligne 34990 n'est pas "
            "intégrée complètement."
        )

    aidant_30450_effectif = (
        aidant_autre_personne_charge_federal
        if aidant_autre_personne_charge_federal is not None
        else AidantNaturelAutrePersonneChargeFederal2025()
    )
    valider_aidant_naturel_30450_2025(aidant_30450_effectif)

    if (
        aidant_30450_effectif.reclamer_montant
        and not integration_30450_sans_credit_compensatoire_autorisee_2025(
            revenu.revenu_imposable_federal
        )
    ):
        raise ValueError(
            "Ce dossier peut nécessiter le crédit compensatoire fédéral "
            "de la ligne 34990. Cette première version refuse la ligne "
            "30450 automatique au-delà de la première tranche tant que "
            "la ligne 34990 n'est pas intégrée complètement."
        )

    aidant_enfant_federal_effectif = (
        aidant_enfant_federal
        if aidant_enfant_federal is not None
        else AidantNaturelEnfantMoins18Federal2025()
    )
    valider_aidant_naturel_enfant_moins18_federal_2025(
        aidant_enfant_federal_effectif
    )

    if (
        aidant_enfant_federal_effectif.reclamer_montant
        and personne_charge_admissible_federale_effective.reclamer_montant
    ):
        raise ValueError(
            "Cette première version ne combine pas encore la ligne 30400 "
            "avec la ligne 30500. Le profil ligne 30500 intégré ici exige "
            "que l'enfant ait vécu avec ses deux parents pendant toute "
            "l'année 2025; les situations où la ligne 30400 détermine "
            "le réclamant seront traitées séparément."
        )

    if (
        aidant_enfant_federal_effectif.reclamer_montant
        and not integration_aidant_enfant_sans_34990_2025(
            revenu.revenu_imposable_federal
        )
    ):
        raise ValueError(
            "Ce dossier peut nécessiter le crédit compensatoire fédéral "
            "de la ligne 34990. Cette première version refuse la ligne "
            "30500 automatique au-delà de la première tranche tant que "
            "la ligne 34990 n'est pas intégrée complètement."
        )

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
    federal = appliquer_credit_federal_frais_scolarite_2025(
        federal,
        frais_scolarite_effectifs,
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
    quebec = appliquer_credit_quebec_frais_scolarite_2025(
        quebec,
        frais_scolarite_effectifs,
    )
    quebec = appliquer_credit_quebec_deficience_2025(
        quebec,
        credit_deficience_effectif,
    )
    quebec = appliquer_credit_quebec_personne_vivant_seule_2025(
        quebec,
        personne_vivant_seule_effective,
    )
    quebec = appliquer_credit_quebec_age_retraite_2025(
        quebec,
        montants_age_retraite_effectifs,
    )
    federal, quebec = appliquer_credits_dividendes_2025(federal, quebec, dividendes)
    federal, quebec = appliquer_credit_impot_etranger_2025(
        federal, quebec, credit_impot_etranger
    )
    remboursements_cotisations = (
        calculer_remboursements_cotisations_2025(
            cotisations_excedentaires_effectives
        )
    )

    rapprochement = calculer_rapprochement_fiscal_2025(
        base,
        federal,
        quebec,
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
    return EstimationFiscale2025(
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
                estimation.dons_bienfaisance.montant_admissible_federal
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
                f"{formater_montant_estimation(credit_federal_frais_scolarite_2025(estimation.frais_scolarite))}",
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
            if estimation.personne_vivant_seule.reclamer_montant
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
                "Aucun partage de la demande 31285 : oui",
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
                "Aucun partage du montant 31270 : oui",
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
                "Aucun partage de la réclamation 30450 : oui",
                "Preuve médicale ou T2201 : confirmée",
                "Validation comptable : confirmée",
                (
                    "Source : "
                    f"{estimation.aidant_autre_personne_charge_federal.source_personne}"
                ),
            ]
            if (
                estimation.aidant_autre_personne_charge_federal
                .reclamer_montant
            )
            else []
        ),
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
                "Enfant avec ses deux parents toute l'année : oui",
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
            if estimation.aidant_enfant_federal.reclamer_montant
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
                "Aucune déficience de l'enfant : oui",
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
            if (
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
        "FÉDÉRAL",
        f"Impôt fédéral brut : {formater_montant_estimation(federal.impot_brut)}",
        f"Crédits non remboursables inclus : {formater_montant_estimation(federal.credits_non_remboursables)}",
        f"Impôt fédéral de base : {formater_montant_estimation(final.impot_federal_de_base)}",
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
