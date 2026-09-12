"""Montants Québec en raison de l'âge et pour revenus de retraite - 2025.

Références 2025 (annexe B, ligne 361) :
- ligne 22 : montant en raison de l'âge = 3 906 $;
- grille revenus de retraite : revenu admissible net × 1,25,
  maximum 3 470 $;
- seuil de réduction : revenu familial net au-delà de 42 090 $;
- taux de réduction : 18,75 %;
- taux du crédit non remboursable Québec : 14 %.

Première version volontairement limitée au contribuable lui-même :
- aucun conjoint au 31 décembre 2025;
- résidence Québec/Canada toute l'année;
- aucune combinaison avec le montant pour personne vivant seule;
- aucun transfert de revenus de retraite entre conjoints;
- revenus de retraite admissibles seulement;
- situation validée par le comptable.

La combinaison avec le montant pour personne vivant seule devra être
traitée dans une étape ultérieure avec un calcul unique de la réduction
de l'annexe B, afin d'éviter toute double réduction.
"""

from dataclasses import dataclass, replace
from decimal import Decimal

from .tax_quebec_2025 import (
    QUEBEC_BASIC_CREDIT_RATE_2025,
    ImpotQuebecPreliminaire2025,
)
from .tax_rules_2025 import arrondir_cent


ZERO = Decimal("0")

MONTANT_AGE_2025 = Decimal("3906")
MONTANT_REVENUS_RETRAITE_MAX_2025 = Decimal("3470")
COEFFICIENT_REVENUS_RETRAITE_2025 = Decimal("1.25")

SEUIL_REDUCTION_ANNEXE_B_2025 = Decimal("42090")
TAUX_REDUCTION_ANNEXE_B_2025 = Decimal("0.1875")
SEUIL_EXCEDENT_SANS_CONJOINT_2025 = Decimal("64699")


@dataclass(frozen=True)
class MontantsAgeRetraite2025:
    """Profil simple pour les lignes 22 et 27 de l'annexe B 2025."""

    reclamer_age: bool = False
    ne_avant_1_janvier_1961: bool = False

    reclamer_revenus_retraite: bool = False
    revenu_ligne_122: Decimal = ZERO
    revenu_ligne_123: Decimal = ZERO

    deduction_ligne_250_point_4: Decimal = ZERO
    deduction_ligne_250_point_6: Decimal = ZERO
    deduction_ligne_293: Decimal = ZERO
    deduction_ligne_297_points_9_12: Decimal = ZERO
    transfert_revenus_retraite_ligne_245: Decimal = ZERO

    revenu_familial_net: Decimal = ZERO

    aucun_conjoint_31_decembre_2025: bool = False
    resident_quebec_canada_toute_annee: bool = False
    aucun_montant_personne_vivant_seule: bool = False

    revenus_retraite_admissibles_confirmes: bool = False
    revenus_non_admissibles_exclus: bool = False

    valide_par_comptable: bool = False
    source_age: str = ""
    source_retraite: str = ""


def aucun_montant_age_retraite_2025() -> MontantsAgeRetraite2025:
    return MontantsAgeRetraite2025()


def _montants_retraite(profil: MontantsAgeRetraite2025) -> tuple[Decimal, ...]:
    return (
        profil.revenu_ligne_122,
        profil.revenu_ligne_123,
        profil.deduction_ligne_250_point_4,
        profil.deduction_ligne_250_point_6,
        profil.deduction_ligne_293,
        profil.deduction_ligne_297_points_9_12,
        profil.transfert_revenus_retraite_ligne_245,
    )


def valider_montants_age_retraite_2025(
    profil: MontantsAgeRetraite2025,
) -> MontantsAgeRetraite2025:
    if profil.revenu_familial_net < ZERO:
        raise ValueError(
            "Le revenu familial net ne peut pas être négatif."
        )

    for valeur in _montants_retraite(profil):
        if valeur < ZERO:
            raise ValueError(
                "Les montants de revenus et déductions de retraite "
                "ne peuvent pas être négatifs."
            )

    if not (profil.reclamer_age or profil.reclamer_revenus_retraite):
        return profil

    if not profil.valide_par_comptable:
        raise ValueError(
            "Les montants pour âge ou revenus de retraite doivent être "
            "validés par le comptable."
        )

    if not profil.resident_quebec_canada_toute_annee:
        raise ValueError(
            "Cette première version exige une résidence Québec/Canada "
            "pendant toute l'année 2025."
        )

    if not profil.aucun_conjoint_31_decembre_2025:
        raise ValueError(
            "Cette première version accepte uniquement une personne "
            "sans conjoint au 31 décembre 2025."
        )

    if not profil.aucun_montant_personne_vivant_seule:
        raise ValueError(
            "Cette première version ne combine pas encore les montants "
            "pour âge ou retraite avec le montant pour personne vivant "
            "seule de l'annexe B."
        )

    if profil.reclamer_age:
        if not profil.ne_avant_1_janvier_1961:
            raise ValueError(
                "Le montant en raison de l'âge exige une naissance "
                "avant le 1er janvier 1961."
            )

        if not profil.source_age.strip():
            raise ValueError(
                "La source confirmant l'âge est obligatoire."
            )

    if profil.reclamer_revenus_retraite:
        total_revenus = (
            profil.revenu_ligne_122 + profil.revenu_ligne_123
        )

        if total_revenus <= ZERO:
            raise ValueError(
                "Un montant positif à la ligne 122 ou 123 est requis "
                "pour réclamer le montant pour revenus de retraite."
            )

        if profil.revenu_ligne_123 != ZERO:
            raise ValueError(
                "La ligne 123 n'est pas supportée dans ce profil simple "
                "sans conjoint."
            )

        if profil.transfert_revenus_retraite_ligne_245 != ZERO:
            raise ValueError(
                "Le transfert de revenus de retraite entre conjoints "
                "n'est pas supporté dans ce profil simple."
            )

        if not profil.revenus_retraite_admissibles_confirmes:
            raise ValueError(
                "L'admissibilité des revenus de retraite doit être "
                "confirmée."
            )

        if not profil.revenus_non_admissibles_exclus:
            raise ValueError(
                "Les revenus non admissibles, notamment PSV, RRQ et RPC, "
                "doivent être exclus du calcul."
            )

        if not profil.source_retraite.strip():
            raise ValueError(
                "La source des revenus de retraite est obligatoire."
            )

        deductions = (
            profil.deduction_ligne_250_point_4
            + profil.deduction_ligne_250_point_6
            + profil.deduction_ligne_293
            + profil.deduction_ligne_297_points_9_12
            + profil.transfert_revenus_retraite_ligne_245
        )
        if deductions > total_revenus:
            raise ValueError(
                "Les déductions liées aux revenus de retraite ne peuvent "
                "pas dépasser les revenus des lignes 122 et 123."
            )

    return profil


def revenu_retraite_net_admissible_2025(
    profil: MontantsAgeRetraite2025,
) -> Decimal:
    valider_montants_age_retraite_2025(profil)

    if not profil.reclamer_revenus_retraite:
        return ZERO

    total_revenus = (
        profil.revenu_ligne_122 + profil.revenu_ligne_123
    )
    deductions = (
        profil.deduction_ligne_250_point_4
        + profil.deduction_ligne_250_point_6
        + profil.deduction_ligne_293
        + profil.deduction_ligne_297_points_9_12
        + profil.transfert_revenus_retraite_ligne_245
    )

    return max(
        arrondir_cent(total_revenus - deductions),
        ZERO,
    )


def montant_revenus_retraite_2025(
    profil: MontantsAgeRetraite2025,
) -> Decimal:
    net = revenu_retraite_net_admissible_2025(profil)

    if net == ZERO:
        return ZERO

    montant = arrondir_cent(
        net * COEFFICIENT_REVENUS_RETRAITE_2025
    )
    return min(
        montant,
        MONTANT_REVENUS_RETRAITE_MAX_2025,
    )


def montant_age_2025(
    profil: MontantsAgeRetraite2025,
) -> Decimal:
    valider_montants_age_retraite_2025(profil)

    if not profil.reclamer_age:
        return ZERO

    return MONTANT_AGE_2025


def montant_brut_age_retraite_2025(
    profil: MontantsAgeRetraite2025,
) -> Decimal:
    return arrondir_cent(
        montant_age_2025(profil)
        + montant_revenus_retraite_2025(profil)
    )


def reduction_annexe_b_age_retraite_2025(
    profil: MontantsAgeRetraite2025,
) -> Decimal:
    valider_montants_age_retraite_2025(profil)

    if not (profil.reclamer_age or profil.reclamer_revenus_retraite):
        return ZERO

    excedent = max(
        profil.revenu_familial_net
        - SEUIL_REDUCTION_ANNEXE_B_2025,
        ZERO,
    )

    if excedent > SEUIL_EXCEDENT_SANS_CONJOINT_2025:
        return montant_brut_age_retraite_2025(profil)

    return arrondir_cent(
        excedent * TAUX_REDUCTION_ANNEXE_B_2025
    )


def montant_ligne_361_age_retraite_2025(
    profil: MontantsAgeRetraite2025,
) -> Decimal:
    valider_montants_age_retraite_2025(profil)

    if not (profil.reclamer_age or profil.reclamer_revenus_retraite):
        return ZERO

    brut = montant_brut_age_retraite_2025(profil)
    reduction = reduction_annexe_b_age_retraite_2025(profil)

    return max(
        arrondir_cent(brut - reduction),
        ZERO,
    )


def credit_quebec_age_retraite_2025(
    profil: MontantsAgeRetraite2025,
) -> Decimal:
    montant = montant_ligne_361_age_retraite_2025(profil)
    return arrondir_cent(
        montant * QUEBEC_BASIC_CREDIT_RATE_2025
    )


def appliquer_credit_quebec_age_retraite_2025(
    impot: ImpotQuebecPreliminaire2025,
    profil: MontantsAgeRetraite2025,
) -> ImpotQuebecPreliminaire2025:
    credit = credit_quebec_age_retraite_2025(profil)

    if credit == ZERO:
        return impot

    limitations = [
        texte
        for texte in impot.limitations
        if texte != "Aucun montant pour conjoint, personne à charge ou âge."
    ]
    limitations.append(
        "Montants Québec en raison de l'âge ou pour revenus de retraite "
        "inclus à la ligne 361."
    )

    return replace(
        impot,
        impot_quebec_preliminaire=max(
            arrondir_cent(
                impot.impot_quebec_preliminaire - credit
            ),
            ZERO,
        ),
        limitations=tuple(limitations),
    )
