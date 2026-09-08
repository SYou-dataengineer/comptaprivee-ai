"""Cotisations syndicales et professionnelles validées - 2025.

Première brique isolée pour le profil emploi Québec simple.

Traitement retenu :
- fédéral : déduction à la ligne 21200;
- Québec : crédit d'impôt non remboursable de 10 % sur la base
  admissible de la ligne 397.1;
- les montants doivent être validés par le comptable;
- les sources doivent être dédoublonnées;
- les droits d'adhésion/initiation sont hors profil;
- pour le Québec, les taxes donnant droit à un remboursement ne
  doivent pas être incluses dans la base admissible.

Ce module ne modifie pas encore le moteur fiscal principal.
"""

from dataclasses import dataclass
from decimal import Decimal

from .tax_rules_2025 import arrondir_cent


ZERO = Decimal("0")
TAUX_CREDIT_COTISATIONS_QUEBEC_2025 = Decimal("0.10")


@dataclass(frozen=True)
class CotisationsSyndicalesProfessionnelles2025:
    montant_federal_admissible: Decimal = ZERO
    montant_quebec_admissible: Decimal = ZERO
    source_federale: str = ""
    source_quebec: str = ""
    valide_par_comptable: bool = False
    sources_dedoublonnees: bool = False
    inclut_droits_adhesion: bool = False
    inclut_taxes_remboursables_quebec: bool = False


def aucune_cotisation_syndicale_2025(
) -> CotisationsSyndicalesProfessionnelles2025:
    return CotisationsSyndicalesProfessionnelles2025()


def valider_cotisations_syndicales_2025(
    cotisations: CotisationsSyndicalesProfessionnelles2025,
) -> CotisationsSyndicalesProfessionnelles2025:
    federal = cotisations.montant_federal_admissible
    quebec = cotisations.montant_quebec_admissible

    if federal < ZERO:
        raise ValueError(
            "Le montant fédéral des cotisations ne peut pas être négatif."
        )

    if quebec < ZERO:
        raise ValueError(
            "Le montant Québec des cotisations ne peut pas être négatif."
        )

    if federal == ZERO and quebec == ZERO:
        return cotisations

    if not cotisations.valide_par_comptable:
        raise ValueError(
            "Les cotisations doivent être validées par le comptable."
        )

    if not cotisations.sources_dedoublonnees:
        raise ValueError(
            "Les sources doivent être vérifiées et dédoublonnées "
            "avant toute réclamation."
        )

    if federal > ZERO and not cotisations.source_federale.strip():
        raise ValueError(
            "La source fédérale des cotisations est obligatoire."
        )

    if quebec > ZERO and not cotisations.source_quebec.strip():
        raise ValueError(
            "La source Québec des cotisations est obligatoire."
        )

    if cotisations.inclut_droits_adhesion:
        raise ValueError(
            "Les droits d'adhésion ou d'initiation ne sont pas "
            "admissibles dans ce profil."
        )

    if (
        quebec > ZERO
        and cotisations.inclut_taxes_remboursables_quebec
    ):
        raise ValueError(
            "La base Québec ne doit pas inclure les taxes donnant "
            "droit à un remboursement."
        )

    return cotisations


def deduction_federale_cotisations_2025(
    cotisations: CotisationsSyndicalesProfessionnelles2025,
) -> Decimal:
    """Montant validé à déduire au fédéral, ligne 21200."""
    valider_cotisations_syndicales_2025(cotisations)
    return arrondir_cent(cotisations.montant_federal_admissible)


def base_credit_quebec_cotisations_2025(
    cotisations: CotisationsSyndicalesProfessionnelles2025,
) -> Decimal:
    """Base validée à inscrire à la ligne 397.1 du Québec."""
    valider_cotisations_syndicales_2025(cotisations)
    return arrondir_cent(cotisations.montant_quebec_admissible)


def credit_quebec_cotisations_2025(
    cotisations: CotisationsSyndicalesProfessionnelles2025,
) -> Decimal:
    """Crédit Québec non remboursable égal à 10 % de la base."""
    base = base_credit_quebec_cotisations_2025(cotisations)
    return arrondir_cent(
        base * TAUX_CREDIT_COTISATIONS_QUEBEC_2025
    )

from dataclasses import replace

from .tax_income_2025 import RevenuNetImposable2025
from .tax_quebec_2025 import ImpotQuebecPreliminaire2025


def appliquer_deduction_federale_cotisations_2025(
    revenu: RevenuNetImposable2025,
    cotisations: CotisationsSyndicalesProfessionnelles2025,
) -> RevenuNetImposable2025:
    """Applique la déduction fédérale ligne 21200 au revenu net fédéral."""
    valider_cotisations_syndicales_2025(cotisations)
    deduction = deduction_federale_cotisations_2025(cotisations)

    if deduction == ZERO:
        return revenu

    limitations = tuple(
        texte
        for texte in revenu.limitations
        if texte != "Aucune autre déduction de revenu net ou imposable."
    ) + (
        "Cotisations syndicales/professionnelles fédérales validées incluses.",
    )

    return replace(
        revenu,
        revenu_net_federal=max(
            arrondir_cent(revenu.revenu_net_federal - deduction),
            ZERO,
        ),
        revenu_imposable_federal=max(
            arrondir_cent(revenu.revenu_imposable_federal - deduction),
            ZERO,
        ),
        profil=revenu.profil + " + cotisations fédérales validées",
        limitations=limitations,
    )


def appliquer_credit_quebec_cotisations_2025(
    impot: ImpotQuebecPreliminaire2025,
    cotisations: CotisationsSyndicalesProfessionnelles2025,
) -> ImpotQuebecPreliminaire2025:
    """Applique le crédit Québec de 10 % après le crédit personnel."""
    valider_cotisations_syndicales_2025(cotisations)
    credit = credit_quebec_cotisations_2025(cotisations)

    if credit == ZERO:
        return impot

    return replace(
        impot,
        impot_quebec_preliminaire=max(
            arrondir_cent(impot.impot_quebec_preliminaire - credit),
            ZERO,
        ),
        limitations=impot.limitations + (
            "Crédit Québec de 10 % pour cotisations admissibles inclus.",
        ),
    )
