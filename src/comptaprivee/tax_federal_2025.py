"""Impôt fédéral préliminaire 2025 - profil emploi Québec simple."""

from dataclasses import dataclass, replace
from decimal import Decimal

from .tax_federal_top_up_2025 import CreditsFederauxNonRemboursables2025
from .tax_engine_input_2025 import BaseFiscaleEmploi2025
from .tax_employment_qpp_2025 import calculer_rrq_salarie_2025
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
    # Champs historiques : base du profil salarié et son crédit à 14,5 %.
    # Ils ne deviennent pas silencieusement 33500/33800/35000.
    # credits_federaux_complets expose séparément les agrégats T1, dont 34990.
    # impot_federal_de_base est le solde après 35000 et 40425, avant 40500.
    base_credits_non_remboursables: Decimal
    credits_non_remboursables: Decimal
    impot_federal_de_base: Decimal
    taux_credit: Decimal
    top_up_credit: Decimal
    limitations: tuple[str, ...]
    # impot_federal_de_base conserve la ligne 42900, avant le crédit 40500.
    credit_etranger_ligne_40500: Decimal = ZERO
    credits_federaux_complets: CreditsFederauxNonRemboursables2025 | None = None

    @property
    def impot_federal_apres_credit_etranger(self) -> Decimal:
        return max(arrondir_cent(
            self.impot_federal_de_base - self.credit_etranger_ligne_40500
        ), ZERO)


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
    utiliser_cotisations_attendues: bool = False,
) -> ImpotFederalPreliminaire2025:
    _verifier(base, revenu)
    attendues = calculer_cotisations_attendues_2025(base)

    cotisation_base_rrq = arrondir_cent(
        attendues.rrq_ba - attendues.rrq_premiere_supplementaire
    )
    if base.feuillets_emploi:
        cotisation_base_rrq = calculer_rrq_salarie_2025(
            base.rrq_base_premiere_supplementaire, base.rrq_deuxieme_supplementaire,
            base.gains_admissibles_rrq).ligne_30800

    ae_source = (
        attendues.assurance_emploi
        if utiliser_cotisations_attendues
        else base.assurance_emploi
    )
    rqap_source = (
        attendues.rqap
        if utiliser_cotisations_attendues
        else base.rqap
    )
    if base.feuillets_emploi:
        ae_source = min(base.assurance_emploi, attendues.assurance_emploi)
        rqap_source = min(base.rqap, attendues.rqap)

    ae = (
        ZERO
        if base.gains_assurables_ae <= MIN_INSURABLE_EARNINGS_CREDIT
        else ae_source
    )
    rqap = (
        ZERO
        if base.gains_assurables_rqap < MIN_INSURABLE_EARNINGS_CREDIT
        else rqap_source
    )

    bpa = montant_personnel_base_federal_2025(revenu.revenu_net_federal)
    emploi = montant_canadien_emploi_2025(base.revenu_emploi_federal)

    base_credits = arrondir_cent(
        bpa + cotisation_base_rrq + ae + rqap + emploi
    )

    # Le profil salarié seul reste sous le seuil. L'orchestrateur finalise
    # 34990 une seule fois, une fois toutes les bases admissibles disponibles.
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
            "Employeurs multiples Québec confirmés (7A)." if base.feuillets_emploi else "Profil emploi simple avec un seul T4 et un seul RL-1.",
            "Aucun montant pour âge, conjoint ou personne à charge.",
            "Aucun crédit pour handicap, frais médicaux ou scolarité.",
            "Aucun don ni crédit transféré.",
            "Abattement Québec de 16,5 % non encore appliqué.",
            "Aucun remboursement ou solde final calculé.",
        ),
    )


def finaliser_credits_federaux_2025(
    impot: ImpotFederalPreliminaire2025,
    credits: CreditsFederauxNonRemboursables2025,
) -> ImpotFederalPreliminaire2025:
    """Applique 35000 depuis le brut, une fois, avant 40425 et 40500."""
    if impot.credits_federaux_complets is not None or impot.credit_etranger_ligne_40500:
        raise ValueError("Les crédits fédéraux sont déjà finalisés ou 40500 est déjà appliquée.")
    return replace(
        impot,
        credits_federaux_complets=credits,
        top_up_credit=credits.credit_compensatoire_ligne_34990,
        impot_federal_de_base=max(arrondir_cent(
            impot.impot_brut - credits.total_credits_ligne_35000
        ), ZERO),
    )
