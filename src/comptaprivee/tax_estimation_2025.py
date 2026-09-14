"""Orchestration de l'estimation fiscale locale 2025.

Ce module relie les briques déjà validées :
dossier fiscal verrouillé -> consolidation -> revenu -> fédéral -> Québec
-> rapprochement.

Il ne transmet aucune déclaration et conserve explicitement le statut
d'estimation soumise à validation comptable.
"""

from dataclasses import dataclass
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
    aidant_enfant_federal: AidantNaturelEnfantMoins18Federal2025


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
    aidant_enfant_federal: (
        AidantNaturelEnfantMoins18Federal2025 | None
    ) = None,
) -> EstimationFiscale2025:
    """Exécute le pipeline fiscal local 2025 sur un dossier verrouillé."""
    if dossier.annee_fiscale != 2025:
        raise ValueError(
            "L'estimation fiscale automatique est disponible "
            "uniquement pour l'année 2025."
        )

    base = consolider_base_fiscale_emploi_2025(dossier)

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

    revenu = calculer_revenu_net_imposable_2025(
        base,
        autoriser_cotisations_excedentaires=(
            cotisations_excedentaires_presentes
        ),
    )

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
        if montants_age_retraite is not None
        else MontantsAgeRetraite2025()
    )
    valider_montants_age_retraite_2025(
        montants_age_retraite_effectifs
    )

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
        if credits_federaux_age_pension is not None
        else CreditsFederauxAgePension2025()
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

    if credits_federaux_age_pension_effectifs.reclamer_montant_pension:
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
    federal = appliquer_credit_federal_aidant_enfant_moins18_2025(
        federal,
        aidant_enfant_federal_effectif,
    )
    quebec = calculer_impot_quebec_preliminaire_2025(revenu)
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
    remboursements_cotisations = (
        calculer_remboursements_cotisations_2025(
            cotisations_excedentaires_effectives
        )
    )

    rapprochement = calculer_rapprochement_fiscal_2025(
        base,
        federal,
        quebec,
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

    return EstimationFiscale2025(
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
        f"Retenue fédérale T4 : {formater_montant_estimation(final.retenue_federale)}",
        f"Retenue Québec RL-1 : {formater_montant_estimation(final.retenue_quebec)}",
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
