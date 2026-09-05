"""Paramètres fiscaux officiels versionnés pour l'année 2025.

Ce module contient uniquement des constantes et petits calculs de référence.
Il ne produit pas une déclaration fiscale complète et n'effectue aucune
transmission à l'ARC ou à Revenu Québec.

Sources officielles vérifiées :
- ARC : taux fédéraux 2025, montant personnel de base, montant canadien
  pour emploi, abattement du Québec et plafonds de cotisations.
- Revenu Québec : taux 2025, montant personnel de base, déduction pour
  travailleur et paramètres RRQ 2025.
"""

from decimal import Decimal, ROUND_HALF_UP


ANNEE_FISCALE = 2025
CENT = Decimal("0.01")

# Fédéral 2025
FEDERAL_BRACKETS_2025 = (
    (Decimal("57375"), Decimal("0.145")),
    (Decimal("114750"), Decimal("0.205")),
    (Decimal("177882"), Decimal("0.26")),
    (Decimal("253414"), Decimal("0.29")),
    (None, Decimal("0.33")),
)

FEDERAL_BPA_MAX_2025 = Decimal("16129")
FEDERAL_BPA_MIN_2025 = Decimal("14538")
FEDERAL_BPA_PHASEOUT_START_2025 = Decimal("177882")
FEDERAL_BPA_PHASEOUT_END_2025 = Decimal("253414")
CANADA_EMPLOYMENT_AMOUNT_MAX_2025 = Decimal("1471")
QUEBEC_ABATEMENT_RATE = Decimal("0.165")
EI_MAX_QUEBEC_2025 = Decimal("860.67")

# Québec 2025
QUEBEC_BRACKETS_2025 = (
    (Decimal("53255"), Decimal("0.14")),
    (Decimal("106495"), Decimal("0.19")),
    (Decimal("129590"), Decimal("0.24")),
    (None, Decimal("0.2575")),
)

QUEBEC_BPA_2025 = Decimal("18571")
QUEBEC_WORKER_DEDUCTION_RATE_2025 = Decimal("0.06")
QUEBEC_WORKER_DEDUCTION_MAX_2025 = Decimal("1420")

# RRQ 2025 - portion employé
QPP_BASIC_RATE_EMPLOYEE_2025 = Decimal("0.054")
QPP_FIRST_ADDITIONAL_RATE_EMPLOYEE_2025 = Decimal("0.01")
QPP_BA_TOTAL_RATE_EMPLOYEE_2025 = Decimal("0.064")
QPP_SECOND_ADDITIONAL_RATE_EMPLOYEE_2025 = Decimal("0.04")

QPP_BASIC_EXEMPTION_2025 = Decimal("3500")
QPP_MAX_PENSIONABLE_EARNINGS_2025 = Decimal("71300")
QPP_ADDITIONAL_MAX_PENSIONABLE_EARNINGS_2025 = Decimal("81200")
QPP_BA_MAX_EMPLOYEE_2025 = Decimal("4339.20")
QPP_BASE_MAX_EMPLOYEE_2025 = Decimal("3661.20")
QPP_FIRST_ADDITIONAL_MAX_EMPLOYEE_2025 = Decimal("678.00")
QPP_SECOND_ADDITIONAL_MAX_EMPLOYEE_2025 = Decimal("396.00")


def arrondir_cent(valeur: Decimal) -> Decimal:
    """Arrondit un montant au cent selon ROUND_HALF_UP."""
    return valeur.quantize(CENT, rounding=ROUND_HALF_UP)


def calculer_impot_par_tranches(
    revenu_imposable: Decimal,
    tranches: tuple[tuple[Decimal | None, Decimal], ...],
) -> Decimal:
    """Calcule l'impôt brut progressif pour une table de tranches."""
    if revenu_imposable < 0:
        raise ValueError("Le revenu imposable ne peut pas être négatif.")

    restant = revenu_imposable
    precedent = Decimal("0")
    impot = Decimal("0")

    for plafond, taux in tranches:
        if restant <= 0:
            break

        if plafond is None:
            portion = restant
        else:
            largeur = plafond - precedent
            portion = min(restant, largeur)

        impot += portion * taux
        restant -= portion

        if plafond is not None:
            precedent = plafond

    return arrondir_cent(impot)


def impot_federal_brut_2025(revenu_imposable: Decimal) -> Decimal:
    """Impôt fédéral brut par tranches 2025, avant crédits."""
    return calculer_impot_par_tranches(
        revenu_imposable,
        FEDERAL_BRACKETS_2025,
    )


def impot_quebec_brut_2025(revenu_imposable: Decimal) -> Decimal:
    """Impôt Québec brut par tranches 2025, avant crédits."""
    return calculer_impot_par_tranches(
        revenu_imposable,
        QUEBEC_BRACKETS_2025,
    )


def montant_personnel_base_federal_2025(
    revenu_net: Decimal,
) -> Decimal:
    """Calcule le montant personnel de base fédéral 2025."""
    if revenu_net < 0:
        raise ValueError("Le revenu net ne peut pas être négatif.")

    if revenu_net <= FEDERAL_BPA_PHASEOUT_START_2025:
        return FEDERAL_BPA_MAX_2025

    if revenu_net >= FEDERAL_BPA_PHASEOUT_END_2025:
        return FEDERAL_BPA_MIN_2025

    reduction = (
        revenu_net - FEDERAL_BPA_PHASEOUT_START_2025
    ) * (
        (FEDERAL_BPA_MAX_2025 - FEDERAL_BPA_MIN_2025)
        / (
            FEDERAL_BPA_PHASEOUT_END_2025
            - FEDERAL_BPA_PHASEOUT_START_2025
        )
    )

    return arrondir_cent(
        FEDERAL_BPA_MAX_2025 - reduction
    )


def montant_canadien_emploi_2025(
    revenu_emploi: Decimal,
) -> Decimal:
    """Retourne le montant canadien pour emploi admissible."""
    if revenu_emploi < 0:
        raise ValueError("Le revenu d'emploi ne peut pas être négatif.")

    return min(
        revenu_emploi,
        CANADA_EMPLOYMENT_AMOUNT_MAX_2025,
    )


def deduction_travailleur_quebec_2025(
    revenu_travail_admissible: Decimal,
) -> Decimal:
    """Déduction québécoise pour travailleur : 6 %, maximum 1 420 $."""
    if revenu_travail_admissible < 0:
        raise ValueError(
            "Le revenu de travail admissible ne peut pas être négatif."
        )

    return arrondir_cent(
        min(
            revenu_travail_admissible
            * QUEBEC_WORKER_DEDUCTION_RATE_2025,
            QUEBEC_WORKER_DEDUCTION_MAX_2025,
        )
    )


def decomposer_rrq_ba_2025(
    cotisation_ba: Decimal,
) -> tuple[Decimal, Decimal]:
    """Sépare B.A en cotisation de base et première supplémentaire.

    En 2025, B.A regroupe 5,4 % de cotisation de base et 1 % de
    première cotisation supplémentaire, soit 6,4 % au total.
    """
    if cotisation_ba < 0:
        raise ValueError("La cotisation B.A ne peut pas être négative.")

    if cotisation_ba > QPP_BA_MAX_EMPLOYEE_2025:
        raise ValueError(
            "La cotisation B.A dépasse le maximum employé 2025."
        )

    premiere_supplementaire = arrondir_cent(
        cotisation_ba
        * (
            QPP_FIRST_ADDITIONAL_RATE_EMPLOYEE_2025
            / QPP_BA_TOTAL_RATE_EMPLOYEE_2025
        )
    )

    base = arrondir_cent(
        cotisation_ba - premiere_supplementaire
    )

    return base, premiere_supplementaire


def valider_rrq_bb_2025(cotisation_bb: Decimal) -> Decimal:
    """Valide la deuxième cotisation supplémentaire RRQ 2025."""
    if cotisation_bb < 0:
        raise ValueError("La cotisation B.B ne peut pas être négative.")

    if cotisation_bb > QPP_SECOND_ADDITIONAL_MAX_EMPLOYEE_2025:
        raise ValueError(
            "La cotisation B.B dépasse le maximum employé 2025."
        )

    return arrondir_cent(cotisation_bb)
