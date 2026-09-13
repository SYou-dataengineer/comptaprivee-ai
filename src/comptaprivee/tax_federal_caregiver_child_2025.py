"""Montant canadien pour aidant naturel — enfant de moins de 18 ans — 2025.

Première version volontairement limitée à un profil simple et vérifié :
- un seul enfant biologique ou adopté du contribuable, ou de son époux/conjoint;
- enfant âgé de moins de 18 ans à la fin de 2025;
- infirmité mentale ou physique confirmée;
- dépendance à autrui prévue pour une longue période continue et
  d'une durée indéterminée;
- besoin de beaucoup plus d'aide pour les besoins et soins personnels
  que les autres enfants du même âge;
- enfant ayant vécu avec ses deux parents durant toute l'année 2025;
- aucune garde partagée;
- aucune pension alimentaire;
- aucun autre réclamant pour la ligne 30500;
- aucun transfert du montant au conjoint dans cette première version;
- preuve médicale ou T2201 approuvé confirmé;
- validation comptable obligatoire.

Cette version simple utilise :
- ligne 30499 : nombre d'enfants admissibles = 1;
- ligne 30500 : montant fixe de 2 687 $ pour 2025;
- taux fédéral de crédit non remboursable 2025 : 14,5 %.

Les situations de garde partagée, de pension alimentaire, de transfert
au conjoint, de plusieurs enfants et les interactions particulières avec
la ligne 30400 seront ajoutées séparément afin d'éviter une réclamation
incorrecte.

Source fiscale :
ARC — ligne 30500, montant canadien pour aidant naturel pour enfants
de moins de 18 ans ayant une infirmité — année d'imposition 2025.
"""

from dataclasses import dataclass, replace
from decimal import Decimal

from .tax_federal_2025 import ImpotFederalPreliminaire2025
from .tax_rules_2025 import (
    FEDERAL_BRACKETS_2025,
    arrondir_cent,
)


ZERO = Decimal("0")
MONTANT_AIDANT_ENFANT_MOINS_18_2025 = Decimal("2687")
TAUX_CREDIT_FEDERAL_2025 = Decimal("0.145")
SEUIL_PREMIERE_TRANCHE_FEDERALE_2025 = FEDERAL_BRACKETS_2025[0][0]


@dataclass(frozen=True)
class AidantNaturelEnfantMoins18Federal2025:
    """Profil simple pour les lignes fédérales 30499 et 30500."""

    reclamer_montant: bool = False

    enfant_biologique_ou_adopte: bool = False
    enfant_moins_18_fin_2025: bool = False

    infirmite_physique_ou_mentale: bool = False
    dependance_longue_continue_duree_indeterminee: bool = False
    besoin_aide_beaucoup_plus_que_meme_age: bool = False

    enfant_avec_deux_parents_toute_annee: bool = False
    aucune_garde_partagee: bool = False
    aucune_pension_alimentaire: bool = False

    aucun_autre_reclamant_30500: bool = False
    aucun_transfert_conjoint_32600: bool = False

    preuve_medicale_ou_t2201_confirmee: bool = False
    valide_par_comptable: bool = False

    source_enfant: str = ""


def aucun_aidant_naturel_enfant_moins18_federal_2025(
) -> AidantNaturelEnfantMoins18Federal2025:
    return AidantNaturelEnfantMoins18Federal2025()


def valider_aidant_naturel_enfant_moins18_federal_2025(
    profil: AidantNaturelEnfantMoins18Federal2025,
) -> AidantNaturelEnfantMoins18Federal2025:
    if not profil.reclamer_montant:
        return profil

    controles = (
        (
            profil.enfant_biologique_ou_adopte,
            "Cette première version est limitée à un enfant biologique "
            "ou adopté du contribuable ou de son époux/conjoint.",
        ),
        (
            profil.enfant_moins_18_fin_2025,
            "L'enfant doit être âgé de moins de 18 ans à la fin de 2025.",
        ),
        (
            profil.infirmite_physique_ou_mentale,
            "Une infirmité physique ou mentale de l'enfant doit être "
            "confirmée.",
        ),
        (
            profil.dependance_longue_continue_duree_indeterminee,
            "L'infirmité doit rendre l'enfant dépendant d'autrui pendant "
            "une longue période continue et d'une durée indéterminée.",
        ),
        (
            profil.besoin_aide_beaucoup_plus_que_meme_age,
            "L'enfant doit avoir besoin de beaucoup plus d'aide pour ses "
            "besoins et soins personnels que les autres enfants du même âge.",
        ),
        (
            profil.enfant_avec_deux_parents_toute_annee,
            "Cette première version est limitée au cas où l'enfant a vécu "
            "avec ses deux parents pendant toute l'année 2025.",
        ),
        (
            profil.aucune_garde_partagee,
            "Les situations de garde partagée ne sont pas supportées "
            "dans cette première version.",
        ),
        (
            profil.aucune_pension_alimentaire,
            "Les situations avec pension alimentaire ne sont pas supportées "
            "dans cette première version.",
        ),
        (
            profil.aucun_autre_reclamant_30500,
            "Le montant de la ligne 30500 ne doit pas être réclamé par "
            "une autre personne pour cet enfant.",
        ),
        (
            profil.aucun_transfert_conjoint_32600,
            "Les transferts du montant au conjoint ne sont pas supportés "
            "dans cette première version.",
        ),
        (
            profil.preuve_medicale_ou_t2201_confirmee,
            "Une preuve médicale admissible ou un formulaire T2201 approuvé "
            "doit être confirmé.",
        ),
        (
            profil.valide_par_comptable,
            "Le montant canadien pour aidant naturel doit être validé "
            "par le comptable.",
        ),
    )

    for condition, message in controles:
        if not condition:
            raise ValueError(message)

    if not profil.source_enfant.strip():
        raise ValueError(
            "Une source confirmant l'enfant, l'infirmité et les conditions "
            "de garde est obligatoire."
        )

    return profil


def nombre_enfants_ligne_30499_2025(
    profil: AidantNaturelEnfantMoins18Federal2025,
) -> int:
    valider_aidant_naturel_enfant_moins18_federal_2025(profil)
    return 1 if profil.reclamer_montant else 0


def montant_ligne_30500_2025(
    profil: AidantNaturelEnfantMoins18Federal2025,
) -> Decimal:
    valider_aidant_naturel_enfant_moins18_federal_2025(profil)

    if not profil.reclamer_montant:
        return ZERO

    return MONTANT_AIDANT_ENFANT_MOINS_18_2025


def credit_federal_aidant_enfant_moins18_2025(
    profil: AidantNaturelEnfantMoins18Federal2025,
) -> Decimal:
    return arrondir_cent(
        montant_ligne_30500_2025(profil)
        * TAUX_CREDIT_FEDERAL_2025
    )



def appliquer_credit_federal_aidant_enfant_moins18_2025(
    impot: ImpotFederalPreliminaire2025,
    profil: AidantNaturelEnfantMoins18Federal2025,
) -> ImpotFederalPreliminaire2025:
    """Applique le crédit fédéral des lignes 30499 / 30500."""
    valider_aidant_naturel_enfant_moins18_federal_2025(profil)

    if not profil.reclamer_montant:
        return impot

    credit = credit_federal_aidant_enfant_moins18_2025(profil)

    limitations = []
    for texte in impot.limitations:
        if texte == "Aucun montant pour âge, conjoint ou personne à charge.":
            limitations.append(
                "Aucun montant pour âge, conjoint ou personne à charge "
                "admissible ligne 30400."
            )
        elif texte == "Aucun montant pour conjoint ou personne à charge.":
            limitations.append(
                "Aucun montant pour conjoint ou personne à charge "
                "admissible ligne 30400."
            )
        elif texte == "Aucun montant pour âge ou personne à charge.":
            limitations.append(
                "Aucun montant pour âge ou personne à charge "
                "admissible ligne 30400."
            )
        elif texte == "Aucun montant pour personne à charge.":
            limitations.append(
                "Aucun montant pour personne à charge admissible "
                "ligne 30400."
            )
        else:
            limitations.append(texte)

    limitations.append(
        "Montant canadien pour aidant naturel enfant de moins de 18 ans "
        "ligne 30500 inclus."
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
