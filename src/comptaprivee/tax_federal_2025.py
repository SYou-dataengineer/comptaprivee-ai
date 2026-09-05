"""Impôt fédéral préliminaire 2025 - profil emploi Québec simple."""

from dataclasses import dataclass
from decimal import Decimal

from .tax_engine_input_2025 import BaseFiscaleEmploi2025
from .tax_income_2025 import RevenuNetImposable2025, calculer_cotisations_attendues_2025
from .tax_rules_2025 import (
    arrondir_cent,
    impot_federal_brut_2025,
    montant_canadien_emploi_2025,
    montant_personnel_base_federal_2025,
)

ZERO = Decimal("0")
FEDERAL_CREDIT_RATE_2025 = Decimal("0.145")
MIN_INSURABLE_EARNINGS_CREDIT = Decimal("2000")


@dataclass(frozen=True)
class ImpotFederalPreliminaire2025:
    client: str
    annee_fiscale: int
    revenu_imposable: Decimal
    impot_brut: Decimal
    montant_personnel_base: Decimal
    cotisation_base_rrq: Decimal
    assurance_emploi_admissible: Decimal
    rqap_admissible: Decimal
    montant_canadien_emploi: Decimal
    base_credits_non_remboursables: Decimal
    credits_non_remboursables: Decimal
    impot_federal_de_base: Decimal
    taux_credit: Decimal
    top_up_credit: Decimal
    limitations: tuple[str, ...]


def _verifier(base: BaseFiscaleEmploi2025, revenu: RevenuNetImposable2025) -> None:
    if base.client != revenu.client:
        raise ValueError("Client incohérent entre la base et le calcul de revenu.")
    if base.annee_fiscale != revenu.annee_fiscale:
        raise ValueError("Année fiscale incohérente entre la base et le revenu.")
    if revenu.annee_fiscale != 2025:
        raise ValueError("Cette version accepte uniquement l'année 2025.")
    if revenu.province.strip().lower() not in {"québec", "quebec"}:
        raise ValueError("Cette version est limitée au profil Québec.")


def calculer_impot_federal_preliminaire_2025(
    base: BaseFiscaleEmploi2025,
    revenu: RevenuNetImposable2025,
) -> ImpotFederalPreliminaire2025:
    _verifier(base, revenu)
    attendues = calculer_cotisations_attendues_2025(base)

    cotisation_base_rrq = arrondir_cent(
        attendues.rrq_ba - attendues.rrq_premiere_supplementaire
    )

    ae = (
        ZERO
        if base.gains_assurables_ae <= MIN_INSURABLE_EARNINGS_CREDIT
        else base.assurance_emploi
    )
    rqap = (
        ZERO
        if base.gains_assurables_rqap < MIN_INSURABLE_EARNINGS_CREDIT
        else base.rqap
    )

    bpa = montant_personnel_base_federal_2025(revenu.revenu_net_federal)
    emploi = montant_canadien_emploi_2025(base.revenu_emploi_federal)

    base_credits = arrondir_cent(
        bpa + cotisation_base_rrq + ae + rqap + emploi
    )

    # Le profil simple ne contient pas assez de montants admissibles pour que
    # le crédit compensatoire 2025 soit requis.
    top_up = ZERO

    credits = arrondir_cent(
        base_credits * FEDERAL_CREDIT_RATE_2025 + top_up
    )
    impot_brut = impot_federal_brut_2025(revenu.revenu_imposable_federal)
    impot_de_base = max(arrondir_cent(impot_brut - credits), ZERO)

    return ImpotFederalPreliminaire2025(
        client=revenu.client,
        annee_fiscale=revenu.annee_fiscale,
        revenu_imposable=revenu.revenu_imposable_federal,
        impot_brut=impot_brut,
        montant_personnel_base=bpa,
        cotisation_base_rrq=cotisation_base_rrq,
        assurance_emploi_admissible=ae,
        rqap_admissible=rqap,
        montant_canadien_emploi=emploi,
        base_credits_non_remboursables=base_credits,
        credits_non_remboursables=credits,
        impot_federal_de_base=impot_de_base,
        taux_credit=FEDERAL_CREDIT_RATE_2025,
        top_up_credit=top_up,
        limitations=(
            "Résident du Canada et du Québec pour toute l'année.",
            "Profil emploi simple avec un seul T4 et un seul RL-1.",
            "Aucun montant pour âge, conjoint ou personne à charge.",
            "Aucun crédit pour handicap, frais médicaux ou scolarité.",
            "Aucun don ni crédit transféré.",
            "Abattement Québec de 16,5 % non encore appliqué.",
            "Aucun remboursement ou solde final calculé.",
        ),
    )
