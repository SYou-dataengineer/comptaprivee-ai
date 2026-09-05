"""Impôt Québec préliminaire 2025 - profil emploi Québec simple.

Cette étape calcule uniquement :
- l'impôt brut du Québec sur le revenu imposable;
- le montant personnel de base 2025;
- le crédit non remboursable correspondant au taux de 14 %;
- l'impôt Québec préliminaire après ce crédit de base.

Important :
Le montant personnel de base du Québec tient déjà compte des cotisations
au RRQ, au RQAP et à l'assurance-emploi. Ces cotisations ne sont donc pas
ajoutées une deuxième fois comme crédits provinciaux dans ce profil.

Ne sont pas encore inclus : conjoint, personnes à charge, âge, retraite,
handicap, frais médicaux, scolarité, dons, carrière prolongée, crédits
remboursables, assurance médicaments, Fonds des services de santé,
ajustements CNESST/SAAQ ou autres situations particulières.
"""

from dataclasses import dataclass
from decimal import Decimal

from .tax_income_2025 import RevenuNetImposable2025
from .tax_rules_2025 import (
    QUEBEC_BPA_2025,
    arrondir_cent,
    impot_quebec_brut_2025,
)


ZERO = Decimal("0")
QUEBEC_BASIC_CREDIT_RATE_2025 = Decimal("0.14")


@dataclass(frozen=True)
class ImpotQuebecPreliminaire2025:
    client: str
    annee_fiscale: int
    province: str

    revenu_imposable: Decimal
    impot_brut: Decimal

    montant_personnel_base: Decimal
    taux_credit_personnel: Decimal
    credit_personnel_base: Decimal

    impot_quebec_preliminaire: Decimal
    limitations: tuple[str, ...]


def _verifier_revenu(
    revenu: RevenuNetImposable2025,
) -> None:
    if revenu.annee_fiscale != 2025:
        raise ValueError(
            "Cette version de l'impôt Québec accepte uniquement 2025."
        )

    if revenu.province.strip().lower() not in {
        "québec",
        "quebec",
    }:
        raise ValueError(
            "Cette version de l'impôt Québec accepte uniquement "
            "les dossiers du Québec."
        )

    if revenu.revenu_imposable_quebec < ZERO:
        raise ValueError(
            "Le revenu imposable Québec ne peut pas être négatif."
        )


def calculer_impot_quebec_preliminaire_2025(
    revenu: RevenuNetImposable2025,
) -> ImpotQuebecPreliminaire2025:
    """Calcule l'impôt Québec simple avant crédits/situations avancés."""
    _verifier_revenu(revenu)

    impot_brut = impot_quebec_brut_2025(
        revenu.revenu_imposable_quebec
    )

    credit_personnel = arrondir_cent(
        QUEBEC_BPA_2025
        * QUEBEC_BASIC_CREDIT_RATE_2025
    )

    impot_preliminaire = max(
        arrondir_cent(
            impot_brut - credit_personnel
        ),
        ZERO,
    )

    return ImpotQuebecPreliminaire2025(
        client=revenu.client,
        annee_fiscale=revenu.annee_fiscale,
        province=revenu.province,
        revenu_imposable=revenu.revenu_imposable_quebec,
        impot_brut=impot_brut,
        montant_personnel_base=QUEBEC_BPA_2025,
        taux_credit_personnel=QUEBEC_BASIC_CREDIT_RATE_2025,
        credit_personnel_base=credit_personnel,
        impot_quebec_preliminaire=impot_preliminaire,
        limitations=(
            "Résident du Québec et du Canada pour toute l'année.",
            "Profil emploi simple avec un seul T4 et un seul RL-1.",
            "Le montant personnel de base inclut déjà RRQ, RQAP et AE.",
            "Aucun montant pour conjoint, personne à charge ou âge.",
            "Aucun crédit handicap, médical, scolarité ou don.",
            "Aucun ajustement CNESST/SAAQ ni indemnité de remplacement.",
            "Aucun crédit remboursable ni prime d'assurance médicaments.",
            "Aucun remboursement ou solde final calculé.",
        ),
    )
