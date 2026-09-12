"""Montant Québec pour personne vivant seule - 2025.

Première brique des crédits familiaux simples de ComptaPrivée.

Références 2025 :
- Annexe B, ligne 20 : montant pour personne vivant seule = 2 128 $;
- Annexe B, ligne 21 : montant additionnel famille monoparentale = 2 627 $;
- réduction : revenu familial net au-delà de 42 090 $ × 18,75 %;
- ligne 361 : montant final de l'annexe B;
- taux du crédit non remboursable Québec : 14 %.

Profil volontairement limité :
- résident Québec/Canada toute l'année;
- aucun conjoint au 31 décembre 2025;
- habitation admissible maintenue pendant toute l'année;
- aucun montant pour âge ou revenus de retraite combiné à la ligne 361;
- documents et situation validés par le comptable.

Le montant additionnel monoparental est supporté uniquement pour le cas
simple d'un enfant majeur aux études admissible. Il est réduit de 218,92 $
par mois d'Allocation famille reçu en 2025 et exige l'absence de droit à
l'Allocation famille en décembre 2025.
"""

from dataclasses import dataclass, replace
from decimal import Decimal

from .tax_quebec_2025 import (
    QUEBEC_BASIC_CREDIT_RATE_2025,
    ImpotQuebecPreliminaire2025,
)
from .tax_rules_2025 import arrondir_cent


ZERO = Decimal("0")
MONTANT_PERSONNE_VIVANT_SEULE_2025 = Decimal("2128")
MONTANT_ADDITIONNEL_MONOPARENTAL_2025 = Decimal("2627")
REDUCTION_MENSUELLE_ALLOCATION_FAMILLE_2025 = Decimal("218.92")
SEUIL_REDUCTION_ANNEXE_B_2025 = Decimal("42090")
TAUX_REDUCTION_ANNEXE_B_2025 = Decimal("0.1875")


@dataclass(frozen=True)
class PersonneVivantSeule2025:
    """Choix et validations pour la ligne 361 - profil simple."""

    reclamer_montant: bool = False
    revenu_familial_net: Decimal = ZERO

    personne_vivant_seule_toute_annee: bool = False
    habitation_maintenue_par_contribuable: bool = False
    seulement_personnes_autorisees_dans_habitation: bool = False
    aucun_conjoint_31_decembre_2025: bool = False
    resident_quebec_canada_toute_annee: bool = False

    reclamer_additionnel_monoparental: bool = False
    enfant_majeur_etudes_admissible: bool = False
    aucun_droit_allocation_famille_decembre: bool = False
    mois_allocation_famille_2025: int = 0

    aucun_montant_age_ou_retraite: bool = False

    documents_justificatifs_confirmes: bool = False
    valide_par_comptable: bool = False
    source: str = ""


def aucun_montant_personne_vivant_seule_2025() -> PersonneVivantSeule2025:
    return PersonneVivantSeule2025()


def valider_personne_vivant_seule_2025(
    profil: PersonneVivantSeule2025,
) -> PersonneVivantSeule2025:
    if profil.revenu_familial_net < ZERO:
        raise ValueError(
            "Le revenu familial net ne peut pas être négatif."
        )

    if not profil.reclamer_montant:
        return profil

    if not profil.valide_par_comptable:
        raise ValueError(
            "Le montant pour personne vivant seule doit être "
            "validé par le comptable."
        )

    if not profil.resident_quebec_canada_toute_annee:
        raise ValueError(
            "Cette version exige une résidence Québec/Canada "
            "pendant toute l'année 2025."
        )

    if not profil.aucun_conjoint_31_decembre_2025:
        raise ValueError(
            "Cette première version accepte uniquement une personne "
            "sans conjoint au 31 décembre 2025."
        )

    if not profil.personne_vivant_seule_toute_annee:
        raise ValueError(
            "L'admissibilité comme personne vivant seule doit être "
            "confirmée pour toute l'année 2025."
        )

    if not profil.habitation_maintenue_par_contribuable:
        raise ValueError(
            "Le contribuable doit avoir maintenu l'habitation "
            "pendant toute l'année 2025."
        )

    if not profil.seulement_personnes_autorisees_dans_habitation:
        raise ValueError(
            "Le logement doit avoir été occupé uniquement avec des "
            "personnes permises par la règle de la personne vivant seule."
        )

    if not profil.aucun_montant_age_ou_retraite:
        raise ValueError(
            "Cette version ne combine pas encore la ligne 361 avec "
            "les montants pour âge ou revenus de retraite."
        )

    if not profil.documents_justificatifs_confirmes:
        raise ValueError(
            "Les documents justificatifs du logement doivent être "
            "confirmés."
        )

    if not profil.source.strip():
        raise ValueError(
            "La source justificative du montant pour personne vivant "
            "seule est obligatoire."
        )

    if not isinstance(profil.mois_allocation_famille_2025, int):
        raise ValueError(
            "Le nombre de mois d'Allocation famille doit être un entier."
        )

    if not 0 <= profil.mois_allocation_famille_2025 <= 12:
        raise ValueError(
            "Le nombre de mois d'Allocation famille doit être "
            "compris entre 0 et 12."
        )

    if profil.reclamer_additionnel_monoparental:
        if not profil.enfant_majeur_etudes_admissible:
            raise ValueError(
                "L'enfant majeur aux études admissible doit être confirmé "
                "pour le montant additionnel monoparental."
            )

        if not profil.aucun_droit_allocation_famille_decembre:
            raise ValueError(
                "Le montant additionnel exige l'absence de droit à "
                "l'Allocation famille pour décembre 2025."
            )

        if profil.mois_allocation_famille_2025 > 11:
            raise ValueError(
                "Le montant additionnel monoparental n'est pas compatible "
                "avec 12 mois d'Allocation famille en 2025."
            )

    return profil


def montant_additionnel_monoparental_2025(
    profil: PersonneVivantSeule2025,
) -> Decimal:
    valider_personne_vivant_seule_2025(profil)

    if (
        not profil.reclamer_montant
        or not profil.reclamer_additionnel_monoparental
    ):
        return ZERO

    reduction = arrondir_cent(
        REDUCTION_MENSUELLE_ALLOCATION_FAMILLE_2025
        * Decimal(profil.mois_allocation_famille_2025)
    )
    return max(
        arrondir_cent(
            MONTANT_ADDITIONNEL_MONOPARENTAL_2025 - reduction
        ),
        ZERO,
    )


def montant_ligne_361_personne_vivant_seule_2025(
    profil: PersonneVivantSeule2025,
) -> Decimal:
    valider_personne_vivant_seule_2025(profil)

    if not profil.reclamer_montant:
        return ZERO

    montant_brut = (
        MONTANT_PERSONNE_VIVANT_SEULE_2025
        + montant_additionnel_monoparental_2025(profil)
    )

    excedent_revenu = max(
        profil.revenu_familial_net - SEUIL_REDUCTION_ANNEXE_B_2025,
        ZERO,
    )
    reduction = arrondir_cent(
        excedent_revenu * TAUX_REDUCTION_ANNEXE_B_2025
    )

    return max(
        arrondir_cent(montant_brut - reduction),
        ZERO,
    )


def credit_quebec_personne_vivant_seule_2025(
    profil: PersonneVivantSeule2025,
) -> Decimal:
    montant = montant_ligne_361_personne_vivant_seule_2025(profil)
    return arrondir_cent(
        montant * QUEBEC_BASIC_CREDIT_RATE_2025
    )


def appliquer_credit_quebec_personne_vivant_seule_2025(
    impot: ImpotQuebecPreliminaire2025,
    profil: PersonneVivantSeule2025,
) -> ImpotQuebecPreliminaire2025:
    credit = credit_quebec_personne_vivant_seule_2025(profil)

    if credit == ZERO:
        return impot

    limitations = [
        texte
        for texte in impot.limitations
        if texte != "Aucun montant pour conjoint, personne à charge ou âge."
    ]
    limitations.append(
        "Montant Québec pour personne vivant seule inclus à la ligne 361."
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
