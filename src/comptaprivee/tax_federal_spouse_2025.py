"""Montant fédéral pour époux ou conjoint de fait — ligne 30300 — 2025.

Première version volontairement limitée à un profil simple et vérifié :
- contribuable résident du Canada toute l'année 2025;
- même époux/conjoint de fait pendant toute l'année;
- aucune séparation ni réconciliation en 2025;
- conjoint résident du Canada toute l'année;
- aucun paiement de pension alimentaire lié à une séparation;
- aucune déficience physique ou mentale du conjoint (le montant canadien
  pour aidant naturel est traité séparément);
- un seul conjoint réclame le montant;
- revenu net du conjoint confirmé;
- validation comptable obligatoire.

La ligne 30300 est calculée comme le montant personnel de base fédéral du
contribuable moins le revenu net du conjoint, sans descendre sous zéro.

Le taux fédéral des crédits non remboursables utilisé ici est 14,5 % pour
2025. Un garde-fou provisoire empêche l'intégration automatique des dossiers
au-delà de la première tranche fédérale tant que la ligne 34990 n'est pas
gérée complètement par le moteur.
"""

from dataclasses import dataclass, replace
from decimal import Decimal

from .tax_federal_2025 import ImpotFederalPreliminaire2025
from .tax_rules_2025 import (
    FEDERAL_BRACKETS_2025,
    arrondir_cent,
    montant_personnel_base_federal_2025,
)


ZERO = Decimal("0")
TAUX_CREDIT_FEDERAL_2025 = Decimal("0.145")
SEUIL_PREMIERE_TRANCHE_FEDERALE_2025 = FEDERAL_BRACKETS_2025[0][0]


@dataclass(frozen=True)
class MontantConjointFederal2025:
    """Profil simple pour le montant ligne 30300."""

    reclamer_montant: bool = False

    revenu_net_contribuable_ligne_23600: Decimal = ZERO
    revenu_net_conjoint_2025: Decimal = ZERO

    contribuable_resident_canada_toute_annee: bool = False
    relation_conjoint_confirmee: bool = False
    conjoint_soutenu_2025: bool = False
    meme_conjoint_toute_annee_2025: bool = False
    aucune_separation_2025: bool = False
    conjoint_resident_canada_toute_annee: bool = False
    aucun_paiement_pension_alimentaire: bool = False
    aucune_infirmite_conjoint: bool = False
    un_seul_conjoint_reclame_montant: bool = False
    revenu_conjoint_confirme: bool = False

    valide_par_comptable: bool = False
    source_conjoint: str = ""


def aucun_montant_conjoint_federal_2025() -> MontantConjointFederal2025:
    return MontantConjointFederal2025()


def valider_montant_conjoint_federal_2025(
    profil: MontantConjointFederal2025,
) -> MontantConjointFederal2025:
    if profil.revenu_net_contribuable_ligne_23600 < ZERO:
        raise ValueError(
            "Le revenu net du contribuable à la ligne 23600 "
            "ne peut pas être négatif."
        )

    if profil.revenu_net_conjoint_2025 < ZERO:
        raise ValueError(
            "Le revenu net du conjoint ne peut pas être négatif."
        )

    if not profil.reclamer_montant:
        return profil

    controles = (
        (
            profil.contribuable_resident_canada_toute_annee,
            "Cette première version exige que le contribuable soit "
            "résident du Canada toute l'année 2025.",
        ),
        (
            profil.relation_conjoint_confirmee,
            "La relation d'époux ou conjoint de fait doit être confirmée.",
        ),
        (
            profil.conjoint_soutenu_2025,
            "Le contribuable doit avoir subvenu aux besoins du conjoint "
            "en 2025 pour réclamer la ligne 30300.",
        ),
        (
            profil.meme_conjoint_toute_annee_2025,
            "Les changements de conjoint en cours d'année ne sont pas "
            "supportés dans ce profil simple.",
        ),
        (
            profil.aucune_separation_2025,
            "Les séparations ou réconciliations en 2025 ne sont pas "
            "supportées dans ce profil simple.",
        ),
        (
            profil.conjoint_resident_canada_toute_annee,
            "Le conjoint non-résident n'est pas supporté dans ce "
            "profil simple.",
        ),
        (
            profil.aucun_paiement_pension_alimentaire,
            "Les situations avec pension alimentaire liée à une "
            "séparation ne sont pas supportées dans ce profil simple.",
        ),
        (
            profil.aucune_infirmite_conjoint,
            "Le conjoint avec déficience doit être traité avec les "
            "règles du montant canadien pour aidant naturel.",
        ),
        (
            profil.un_seul_conjoint_reclame_montant,
            "Un seul époux ou conjoint de fait peut réclamer le "
            "montant pour l'année.",
        ),
        (
            profil.revenu_conjoint_confirme,
            "Le revenu net 2025 du conjoint doit être confirmé.",
        ),
        (
            profil.valide_par_comptable,
            "Le montant fédéral pour conjoint doit être validé "
            "par le comptable.",
        ),
    )

    for condition, message in controles:
        if not condition:
            raise ValueError(message)

    if not profil.source_conjoint.strip():
        raise ValueError(
            "Une source confirmant la situation et le revenu du conjoint "
            "est obligatoire."
        )

    return profil


def montant_ligne_30300_2025(
    profil: MontantConjointFederal2025,
) -> Decimal:
    valider_montant_conjoint_federal_2025(profil)

    if not profil.reclamer_montant:
        return ZERO

    montant_personnel = montant_personnel_base_federal_2025(
        profil.revenu_net_contribuable_ligne_23600
    )

    return max(
        arrondir_cent(
            montant_personnel - profil.revenu_net_conjoint_2025
        ),
        ZERO,
    )


def credit_federal_montant_conjoint_2025(
    profil: MontantConjointFederal2025,
) -> Decimal:
    return arrondir_cent(
        montant_ligne_30300_2025(profil)
        * TAUX_CREDIT_FEDERAL_2025
    )



def appliquer_credit_federal_montant_conjoint_2025(
    impot: ImpotFederalPreliminaire2025,
    profil: MontantConjointFederal2025,
) -> ImpotFederalPreliminaire2025:
    """Applique le crédit ligne 30300 au calcul fédéral préliminaire."""
    valider_montant_conjoint_federal_2025(profil)

    if not profil.reclamer_montant:
        return impot

    credit = credit_federal_montant_conjoint_2025(profil)

    limitations = []
    for texte in impot.limitations:
        if texte == "Aucun montant pour âge, conjoint ou personne à charge.":
            limitations.append(
                "Aucun montant pour âge ou personne à charge."
            )
        elif texte == "Aucun montant pour conjoint ou personne à charge.":
            limitations.append(
                "Aucun montant pour personne à charge."
            )
        else:
            limitations.append(texte)

    limitations.append(
        "Montant fédéral pour époux ou conjoint de fait "
        "ligne 30300 inclus."
    )

    return replace(
        impot,
        impot_federal_de_base=max(
            arrondir_cent(
                impot.impot_federal_de_base - credit
            ),
            ZERO,
        ),
        limitations=tuple(limitations),
    )

def integration_sans_credit_compensatoire_autorisee_2025(
    revenu_imposable_federal: Decimal,
) -> bool:
    """Garde-fou provisoire avant intégration complète de la ligne 34990."""
    if revenu_imposable_federal < ZERO:
        raise ValueError(
            "Le revenu imposable fédéral ne peut pas être négatif."
        )

    return (
        revenu_imposable_federal
        <= SEUIL_PREMIERE_TRANCHE_FEDERALE_2025
    )
