"""Revenu net et revenu imposable 2025 - profil emploi Québec simple."""

from dataclasses import dataclass
from decimal import Decimal

from .tax_engine_input_2025 import BaseFiscaleEmploi2025
from .tax_rules_2025 import (
    EI_MAX_INSURABLE_EARNINGS_QUEBEC_2025,
    EI_RATE_QUEBEC_2025,
    QPIP_MAX_INSURABLE_EARNINGS_2025,
    QPIP_RATE_EMPLOYEE_2025,
    QPP_BA_TOTAL_RATE_EMPLOYEE_2025,
    QPP_BASIC_EXEMPTION_2025,
    QPP_FIRST_ADDITIONAL_RATE_EMPLOYEE_2025,
    QPP_MAX_PENSIONABLE_EARNINGS_2025,
    QPP_ADDITIONAL_MAX_PENSIONABLE_EARNINGS_2025,
    QPP_SECOND_ADDITIONAL_RATE_EMPLOYEE_2025,
    arrondir_cent,
    deduction_travailleur_quebec_2025,
)

ZERO = Decimal("0")
TOLERANCE_COTISATION = Decimal("2.00")


@dataclass(frozen=True)
class CotisationsAttendues2025:
    rrq_ba: Decimal
    rrq_bb: Decimal
    assurance_emploi: Decimal
    rqap: Decimal
    rrq_premiere_supplementaire: Decimal
    rrq_deuxieme_supplementaire: Decimal


@dataclass(frozen=True)
class RevenuNetImposable2025:
    client: str
    annee_fiscale: int
    province: str
    revenu_total_federal: Decimal
    deduction_rrq_amelioree_federale: Decimal
    revenu_net_federal: Decimal
    revenu_imposable_federal: Decimal
    revenu_total_quebec: Decimal
    deduction_travailleur_quebec: Decimal
    deduction_rrq_quebec: Decimal
    revenu_net_quebec: Decimal
    revenu_imposable_quebec: Decimal
    profil: str
    limitations: tuple[str, ...]


def _cotisation_rrq_ba_attendue(gains: Decimal) -> Decimal:
    if gains < ZERO:
        raise ValueError("Les gains admissibles au RRQ ne peuvent pas être négatifs.")
    plafond = min(gains, QPP_MAX_PENSIONABLE_EARNINGS_2025)
    cotisables = max(plafond - QPP_BASIC_EXEMPTION_2025, ZERO)
    return arrondir_cent(cotisables * QPP_BA_TOTAL_RATE_EMPLOYEE_2025)


def _cotisation_rrq_bb_attendue(gains: Decimal) -> Decimal:
    if gains < ZERO:
        raise ValueError("Les gains admissibles au RRQ ne peuvent pas être négatifs.")
    cotisables = max(
        min(gains, QPP_ADDITIONAL_MAX_PENSIONABLE_EARNINGS_2025)
        - QPP_MAX_PENSIONABLE_EARNINGS_2025,
        ZERO,
    )
    return arrondir_cent(cotisables * QPP_SECOND_ADDITIONAL_RATE_EMPLOYEE_2025)


def _cotisation_ae_attendue(gains: Decimal) -> Decimal:
    if gains < ZERO:
        raise ValueError("Les gains assurables AE ne peuvent pas être négatifs.")
    return arrondir_cent(
        min(gains, EI_MAX_INSURABLE_EARNINGS_QUEBEC_2025)
        * EI_RATE_QUEBEC_2025
    )


def _cotisation_rqap_attendue(gains: Decimal) -> Decimal:
    if gains < ZERO:
        raise ValueError("Les gains assurables RQAP ne peuvent pas être négatifs.")
    return arrondir_cent(
        min(gains, QPIP_MAX_INSURABLE_EARNINGS_2025)
        * QPIP_RATE_EMPLOYEE_2025
    )


def calculer_cotisations_attendues_2025(
    base: BaseFiscaleEmploi2025,
) -> CotisationsAttendues2025:
    rrq_ba = _cotisation_rrq_ba_attendue(base.gains_admissibles_rrq)
    rrq_bb = _cotisation_rrq_bb_attendue(base.gains_admissibles_rrq)
    ae = _cotisation_ae_attendue(base.gains_assurables_ae)
    rqap = _cotisation_rqap_attendue(base.gains_assurables_rqap)

    plafond = min(
        base.gains_admissibles_rrq,
        QPP_MAX_PENSIONABLE_EARNINGS_2025,
    )
    cotisables = max(plafond - QPP_BASIC_EXEMPTION_2025, ZERO)
    premiere = arrondir_cent(
        cotisables * QPP_FIRST_ADDITIONAL_RATE_EMPLOYEE_2025
    )

    return CotisationsAttendues2025(
        rrq_ba=rrq_ba,
        rrq_bb=rrq_bb,
        assurance_emploi=ae,
        rqap=rqap,
        rrq_premiere_supplementaire=premiere,
        rrq_deuxieme_supplementaire=rrq_bb,
    )


def _verifier_proche(nom: str, valeur: Decimal, attendue: Decimal) -> None:
    if abs(valeur - attendue) > TOLERANCE_COTISATION:
        raise ValueError(
            f"{nom} incohérente pour le profil automatique 2025 : "
            f"valeur validée={valeur}, valeur attendue≈{attendue}. "
            "Le dossier doit être vérifié par le comptable ou traité "
            "par un module avancé."
        )


def verifier_profil_emploi_simple_2025(
    base: BaseFiscaleEmploi2025,
) -> CotisationsAttendues2025:
    if base.annee_fiscale != 2025:
        raise ValueError("Cette version du calcul accepte uniquement l'année 2025.")

    if base.province.strip().lower() not in {"québec", "quebec"}:
        raise ValueError("Cette version du calcul accepte uniquement le Québec.")

    if base.nombre_t4 != 1 or base.nombre_rl1 != 1:
        raise ValueError(
            "Le calcul automatique de cette première version exige "
            "exactement un T4 et un RL-1."
        )

    attendues = calculer_cotisations_attendues_2025(base)

    _verifier_proche(
        "Cotisation RRQ B.A / T4 case 17",
        base.rrq_base_premiere_supplementaire,
        attendues.rrq_ba,
    )
    _verifier_proche(
        "Deuxième cotisation RRQ B.B / T4 case 17A",
        base.rrq_deuxieme_supplementaire,
        attendues.rrq_bb,
    )
    _verifier_proche(
        "Cotisation d'assurance-emploi",
        base.assurance_emploi,
        attendues.assurance_emploi,
    )
    _verifier_proche(
        "Cotisation RQAP",
        base.rqap,
        attendues.rqap,
    )

    return attendues


def calculer_revenu_net_imposable_2025(
    base: BaseFiscaleEmploi2025,
) -> RevenuNetImposable2025:
    attendues = verifier_profil_emploi_simple_2025(base)

    deduction_rrq = arrondir_cent(
        attendues.rrq_premiere_supplementaire
        + attendues.rrq_deuxieme_supplementaire
    )

    revenu_net_federal = max(
        arrondir_cent(base.revenu_emploi_federal - deduction_rrq),
        ZERO,
    )
    revenu_imposable_federal = revenu_net_federal

    deduction_travailleur = deduction_travailleur_quebec_2025(
        base.revenu_emploi_quebec
    )

    revenu_net_quebec = max(
        arrondir_cent(
            base.revenu_emploi_quebec
            - deduction_travailleur
            - deduction_rrq
        ),
        ZERO,
    )
    revenu_imposable_quebec = revenu_net_quebec

    return RevenuNetImposable2025(
        client=base.client,
        annee_fiscale=base.annee_fiscale,
        province=base.province,
        revenu_total_federal=base.revenu_emploi_federal,
        deduction_rrq_amelioree_federale=deduction_rrq,
        revenu_net_federal=revenu_net_federal,
        revenu_imposable_federal=revenu_imposable_federal,
        revenu_total_quebec=base.revenu_emploi_quebec,
        deduction_travailleur_quebec=deduction_travailleur,
        deduction_rrq_quebec=deduction_rrq,
        revenu_net_quebec=revenu_net_quebec,
        revenu_imposable_quebec=revenu_imposable_quebec,
        profil="Emploi Québec simple 2025",
        limitations=(
            "Un seul T4 et un seul RL-1.",
            "Aucun revenu de travail autonome.",
            "Aucune cotisation CPP ou situation interprovinciale.",
            "Aucune proratisation ou élection spéciale du RRQ.",
            "Aucune autre déduction de revenu net ou imposable.",
            "Aucun calcul d'impôt ou de remboursement à cette étape.",
        ),
    )
