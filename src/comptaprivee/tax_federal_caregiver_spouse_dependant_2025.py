"""Ligne fédérale 30425 — montant canadien pour aidant naturel — 2025.

Première version volontairement limitée à un profil simple et vérifié.

Le montant vise :
- un époux ou conjoint de fait soutenu par le contribuable; ou
- une personne à charge admissible âgée de 18 ans ou plus,
  admissible à la ligne 30400.

Conditions générales retenues dans cette première version :
- la personne a une infirmité mentale ou physique;
- elle dépend du contribuable en raison de cette infirmité;
- la dépendance existe pour une période considérable;
- le montant de base de 2 687 $ a été inclus dans le calcul
  de la ligne 30300 ou 30400, selon le cas;
- le revenu net 2025 de la personne (ligne 23600) est compris
  entre 8 624 $ et 28 798 $ inclusivement;
- une seule personne réclame la ligne 30425;
- aucune division ou partage de la réclamation;
- preuve médicale admissible ou T2201 approuvé confirmé;
- validation comptable obligatoire.

Calcul de l'annexe 5 — ligne 30425 :
1. 28 798 $ moins le revenu net de la personne;
2. résultat limité à un maximum de 8 601 $;
3. moins le montant réclamé à la ligne 30300 ou 30400,
   s'il y a lieu;
4. minimum zéro.

Le crédit fédéral 2025 est calculé à 14,5 % du montant admissible.

Source :
ARC — Annexe 5, ligne 30425 — année d'imposition 2025.
"""

from dataclasses import dataclass, replace
from decimal import Decimal

from .tax_federal_2025 import ImpotFederalPreliminaire2025

from .tax_rules_2025 import (
    FEDERAL_BRACKETS_2025,
    arrondir_cent,
)


ZERO = Decimal("0")
REVENU_NET_MIN_30425_2025 = Decimal("8624")
BASE_CALCUL_30425_2025 = Decimal("28798")
MAXIMUM_LIGNE_30425_2025 = Decimal("8601")
MONTANT_BASE_AIDANT_30300_30400_2025 = Decimal("2687")
TAUX_CREDIT_FEDERAL_2025 = Decimal("0.145")
SEUIL_PREMIERE_TRANCHE_FEDERALE_2025 = FEDERAL_BRACKETS_2025[0][0]

TYPE_CONJOINT = "conjoint"
TYPE_PERSONNE_CHARGE_ADMISSIBLE = "personne_charge_admissible"
TYPES_PERSONNE_AUTORISES = {
    TYPE_CONJOINT,
    TYPE_PERSONNE_CHARGE_ADMISSIBLE,
}


@dataclass(frozen=True)
class AidantNaturelConjointOuPersonneChargeFederal2025:
    """Profil simple pour la ligne fédérale 30425."""

    reclamer_montant: bool = False

    type_personne: str = ""
    revenu_net_personne_ligne_23600: Decimal = ZERO
    montant_reclame_ligne_30300_ou_30400: Decimal = ZERO

    personne_soutenue_en_2025: bool = False
    personne_charge_18_ans_ou_plus_si_applicable: bool = False

    infirmite_physique_ou_mentale: bool = False
    dependance_due_uniquement_a_infirmite: bool = False
    dependance_periode_considerable: bool = False

    montant_base_2687_inclus: bool = False

    un_seul_reclamant_30425: bool = False
    aucune_reclamation_partagee: bool = False

    preuve_medicale_ou_t2201_confirmee: bool = False
    valide_par_comptable: bool = False

    source_personne: str = ""


def aucun_aidant_naturel_30425_2025(
) -> AidantNaturelConjointOuPersonneChargeFederal2025:
    return AidantNaturelConjointOuPersonneChargeFederal2025()


def valider_aidant_naturel_30425_2025(
    profil: AidantNaturelConjointOuPersonneChargeFederal2025,
) -> AidantNaturelConjointOuPersonneChargeFederal2025:
    if profil.revenu_net_personne_ligne_23600 < ZERO:
        raise ValueError(
            "Le revenu net de la personne — ligne 23600 — "
            "ne peut pas être négatif."
        )

    if profil.montant_reclame_ligne_30300_ou_30400 < ZERO:
        raise ValueError(
            "Le montant réclamé à la ligne 30300 ou 30400 "
            "ne peut pas être négatif."
        )

    if not profil.reclamer_montant:
        return profil

    if profil.type_personne not in TYPES_PERSONNE_AUTORISES:
        raise ValueError(
            "Le type de personne doit être 'conjoint' ou "
            "'personne_charge_admissible'."
        )

    if not profil.personne_soutenue_en_2025:
        raise ValueError(
            "La personne doit avoir été soutenue par le contribuable "
            "en 2025."
        )

    if (
        profil.type_personne == TYPE_PERSONNE_CHARGE_ADMISSIBLE
        and not profil.personne_charge_18_ans_ou_plus_si_applicable
    ):
        raise ValueError(
            "La personne à charge admissible doit avoir 18 ans ou plus "
            "pour la ligne 30425."
        )

    if not profil.infirmite_physique_ou_mentale:
        raise ValueError(
            "Une infirmité physique ou mentale doit être confirmée."
        )

    if not profil.dependance_due_uniquement_a_infirmite:
        raise ValueError(
            "La dépendance doit être due à l'infirmité."
        )

    if not profil.dependance_periode_considerable:
        raise ValueError(
            "La dépendance doit exister pendant une période considérable."
        )

    if not profil.montant_base_2687_inclus:
        raise ValueError(
            "Le montant de base de 2 687 $ doit avoir été inclus "
            "dans le calcul de la ligne 30300 ou 30400."
        )

    revenu = profil.revenu_net_personne_ligne_23600
    if (
        revenu < REVENU_NET_MIN_30425_2025
        or revenu > BASE_CALCUL_30425_2025
    ):
        raise ValueError(
            "Le revenu net 2025 de la personne doit être compris "
            "entre 8 624 $ et 28 798 $ pour cette première version."
        )

    if not profil.un_seul_reclamant_30425:
        raise ValueError(
            "Une seule personne peut réclamer la ligne 30425."
        )

    if not profil.aucune_reclamation_partagee:
        raise ValueError(
            "La ligne 30425 ne peut pas être divisée ou partagée."
        )

    if not profil.preuve_medicale_ou_t2201_confirmee:
        raise ValueError(
            "Une preuve médicale admissible ou un formulaire T2201 "
            "approuvé doit être confirmé."
        )

    if not profil.valide_par_comptable:
        raise ValueError(
            "La ligne 30425 doit être validée par le comptable."
        )

    if not profil.source_personne.strip():
        raise ValueError(
            "Une source confirmant le lien, le revenu et l'infirmité "
            "est obligatoire."
        )

    return profil


def montant_brut_avant_30300_30400_ligne_30425_2025(
    profil: AidantNaturelConjointOuPersonneChargeFederal2025,
) -> Decimal:
    valider_aidant_naturel_30425_2025(profil)

    if not profil.reclamer_montant:
        return ZERO

    brut = max(
        BASE_CALCUL_30425_2025
        - profil.revenu_net_personne_ligne_23600,
        ZERO,
    )
    return min(brut, MAXIMUM_LIGNE_30425_2025)


def montant_ligne_30425_2025(
    profil: AidantNaturelConjointOuPersonneChargeFederal2025,
) -> Decimal:
    valider_aidant_naturel_30425_2025(profil)

    if not profil.reclamer_montant:
        return ZERO

    montant = (
        montant_brut_avant_30300_30400_ligne_30425_2025(profil)
        - profil.montant_reclame_ligne_30300_ou_30400
    )

    return max(arrondir_cent(montant), ZERO)


def credit_federal_ligne_30425_2025(
    profil: AidantNaturelConjointOuPersonneChargeFederal2025,
) -> Decimal:
    return arrondir_cent(
        montant_ligne_30425_2025(profil)
        * TAUX_CREDIT_FEDERAL_2025
    )


def appliquer_credit_federal_ligne_30425_2025(
    impot: ImpotFederalPreliminaire2025,
    profil: AidantNaturelConjointOuPersonneChargeFederal2025,
) -> ImpotFederalPreliminaire2025:
    """Applique le crédit non remboursable de la ligne 30425."""
    valider_aidant_naturel_30425_2025(profil)

    if not profil.reclamer_montant:
        return impot

    credit = credit_federal_ligne_30425_2025(profil)
    limitations = list(impot.limitations)
    limitations.append(
        "Montant canadien pour aidant naturel ligne 30425 inclus."
    )

    return replace(
        impot,
        impot_federal_de_base=max(
            arrondir_cent(impot.impot_federal_de_base - credit),
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
