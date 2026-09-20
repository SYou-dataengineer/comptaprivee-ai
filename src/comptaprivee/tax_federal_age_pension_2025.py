"""Crédits fédéraux 2025 - montant en raison de l'âge et revenu de pension."""

from dataclasses import dataclass, replace
from decimal import Decimal

from .tax_federal_2025 import ImpotFederalPreliminaire2025
from .tax_rules_2025 import arrondir_cent


ZERO = Decimal("0")
MONTANT_AGE_FEDERAL_MAX_2025 = Decimal("9028")
SEUIL_REDUCTION_AGE_FEDERAL_2025 = Decimal("45522")
SEUIL_FIN_AGE_FEDERAL_2025 = Decimal("105709")
TAUX_REDUCTION_AGE_FEDERAL_2025 = Decimal("0.15")
MONTANT_PENSION_FEDERAL_MAX_2025 = Decimal("2000")
TAUX_CREDIT_FEDERAL_2025 = Decimal("0.145")
SEUIL_PREMIERE_TRANCHE_FEDERALE_2025 = Decimal("57375")


@dataclass(frozen=True)
class CreditsFederauxAgePension2025:
    reclamer_montant_age: bool = False
    age_65_plus_31_decembre_2025: bool = False
    revenu_net_ligne_23600: Decimal = ZERO
    reclamer_montant_pension: bool = False
    revenu_pension_admissible: Decimal = ZERO
    resident_canada_toute_annee: bool = False
    aucune_regle_deces: bool = False
    aucun_fractionnement_pension: bool = False
    aucun_transfert_conjoint: bool = False
    revenu_pension_admissible_confirme: bool = False
    valide_par_comptable: bool = False
    source_age: str = ""
    source_pension: str = ""


def aucun_credit_age_pension_federal_2025():
    return CreditsFederauxAgePension2025()


def valider_credits_federaux_age_pension_2025(profil):
    if profil.revenu_net_ligne_23600 < ZERO:
        raise ValueError("Le revenu net fédéral de la ligne 23600 ne peut pas être négatif.")
    if profil.revenu_pension_admissible < ZERO:
        raise ValueError("Le revenu de pension admissible ne peut pas être négatif.")
    if not (profil.reclamer_montant_age or profil.reclamer_montant_pension):
        return profil
    if not profil.resident_canada_toute_annee:
        raise ValueError("Cette première version exige une résidence au Canada pendant toute l'année 2025.")
    if profil.reclamer_montant_age and not profil.age_65_plus_31_decembre_2025:
        raise ValueError("Cette première version exige que le contribuable ait 65 ans ou plus au 31 décembre 2025.")
    if not profil.aucune_regle_deces:
        raise ValueError("Les règles spéciales applicables à une personne décédée ne sont pas supportées.")
    if not profil.aucun_fractionnement_pension:
        raise ValueError("Le fractionnement du revenu de pension avec le formulaire T1032 n'est pas supporté.")
    if not profil.aucun_transfert_conjoint:
        raise ValueError("Le transfert de crédits entre conjoints n'est pas supporté.")
    if not profil.valide_par_comptable:
        raise ValueError("Les crédits fédéraux âge/pension doivent être validés par le comptable.")
    if profil.reclamer_montant_age and not profil.source_age.strip():
        raise ValueError("La source confirmant l'âge est obligatoire.")
    if profil.reclamer_montant_pension:
        if profil.revenu_pension_admissible <= ZERO:
            raise ValueError("Un revenu de pension admissible positif est requis pour réclamer la ligne 31400.")
        if not profil.revenu_pension_admissible_confirme:
            raise ValueError("L'admissibilité du revenu de pension doit être confirmée.")
        if not profil.source_pension.strip():
            raise ValueError("La source du revenu de pension admissible est obligatoire.")
    return profil


def montant_age_federal_2025(profil):
    valider_credits_federaux_age_pension_2025(profil)
    if not profil.reclamer_montant_age:
        return ZERO
    revenu = profil.revenu_net_ligne_23600
    if revenu <= SEUIL_REDUCTION_AGE_FEDERAL_2025:
        return MONTANT_AGE_FEDERAL_MAX_2025
    if revenu >= SEUIL_FIN_AGE_FEDERAL_2025:
        return ZERO
    reduction = arrondir_cent(
        (revenu - SEUIL_REDUCTION_AGE_FEDERAL_2025)
        * TAUX_REDUCTION_AGE_FEDERAL_2025
    )
    return max(arrondir_cent(MONTANT_AGE_FEDERAL_MAX_2025 - reduction), ZERO)


def montant_pension_federal_2025(profil):
    valider_credits_federaux_age_pension_2025(profil)
    if not profil.reclamer_montant_pension:
        return ZERO
    return min(
        arrondir_cent(profil.revenu_pension_admissible),
        MONTANT_PENSION_FEDERAL_MAX_2025,
    )


def base_credits_age_pension_federal_2025(profil):
    return arrondir_cent(
        montant_age_federal_2025(profil)
        + montant_pension_federal_2025(profil)
    )


def credit_federal_age_pension_2025(profil):
    return arrondir_cent(
        base_credits_age_pension_federal_2025(profil)
        * TAUX_CREDIT_FEDERAL_2025
    )



def appliquer_credit_federal_age_pension_2025(
    impot: ImpotFederalPreliminaire2025,
    profil: CreditsFederauxAgePension2025,
) -> ImpotFederalPreliminaire2025:
    montant = credit_federal_age_pension_2025(profil)

    if montant == ZERO:
        return impot

    limitations = []
    for texte in impot.limitations:
        if texte == "Aucun montant pour âge, conjoint ou personne à charge.":
            limitations.append(
                "Aucun montant pour conjoint ou personne à charge."
            )
        else:
            limitations.append(texte)

    if profil.reclamer_montant_age:
        limitations.append(
            "Montant fédéral en raison de l'âge ligne 30100 inclus."
        )

    if profil.reclamer_montant_pension:
        limitations.append(
            "Montant fédéral pour revenu de pension ligne 31400 inclus."
        )

    return replace(
        impot,
        impot_federal_de_base=max(
            arrondir_cent(
                impot.impot_federal_de_base - montant
            ),
            ZERO,
        ),
        limitations=tuple(limitations),
    )


def integration_sans_credit_compensatoire_autorisee_2025(revenu_imposable_federal):
    if revenu_imposable_federal < ZERO:
        raise ValueError("Le revenu imposable fédéral ne peut pas être négatif.")
    return revenu_imposable_federal <= SEUIL_PREMIERE_TRANCHE_FEDERALE_2025
