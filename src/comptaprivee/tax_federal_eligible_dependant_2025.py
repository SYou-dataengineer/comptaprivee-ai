"""Montant fédéral pour personne à charge admissible — ligne 30400 — 2025.

Première version volontairement limitée à un profil simple et vérifié :
- contribuable résident du Canada toute l'année 2025;
- aucun époux ou conjoint de fait pendant toute l'année 2025;
- une seule personne à charge réclamée;
- personne à charge = enfant du contribuable, âgé de moins de 18 ans
  à la fin de 2025;
- aucune déficience physique ou mentale de l'enfant dans cette version;
- l'enfant a été soutenu par le contribuable et a vécu avec lui dans
  une habitation maintenue par le contribuable;
- aucune garde partagée ni paiement de pension alimentaire;
- aucun autre membre du ménage ni autre contribuable ne réclame la
  ligne 30400 pour cette personne;
- revenu net de la personne à charge confirmé;
- validation comptable obligatoire.

La ligne 30400 est calculée comme le montant personnel de base fédéral
applicable au contribuable, moins le revenu net de la personne à charge,
sans descendre sous zéro.

Le taux fédéral des crédits non remboursables utilisé ici est 14,5 % pour
2025. Un garde-fou provisoire protège la ligne 34990 pour les dossiers
au-delà de la première tranche fédérale.

Source fiscale : ARC, ligne 30400 et annexe 5, année d'imposition 2025.
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
MONTANT_AIDANT_PERSONNE_CHARGE_2025 = Decimal("2687")
TAUX_CREDIT_FEDERAL_2025 = Decimal("0.145")
SEUIL_PREMIERE_TRANCHE_FEDERALE_2025 = FEDERAL_BRACKETS_2025[0][0]


@dataclass(frozen=True)
class MontantPersonneChargeAdmissibleFederal2025:
    """Profil simple pour la ligne fédérale 30400."""

    reclamer_montant: bool = False

    revenu_net_contribuable_ligne_23600: Decimal = ZERO
    revenu_net_personne_charge_2025: Decimal = ZERO

    contribuable_resident_canada_toute_annee: bool = False
    aucun_epoux_conjoint_2025: bool = False

    personne_charge_est_enfant: bool = False
    enfant_moins_18_fin_2025: bool = False
    aucune_infirmite_enfant: bool = False
    personne_charge_18_ans_ou_plus: bool = False
    personne_charge_avec_infirmite: bool = False
    dependance_due_uniquement_a_infirmite: bool = False
    dependance_periode_considerable: bool = False
    aidant_naturel_base_2687_inclus: bool = False
    preuve_medicale_ou_t2201_confirmee: bool = False
    enfant_soutenu_2025: bool = False
    enfant_a_vecu_avec_contribuable: bool = False
    habitation_maintenue_par_contribuable: bool = False
    enfant_resident_canada_toute_annee: bool = False

    aucune_garde_partagee: bool = False
    aucun_paiement_pension_alimentaire: bool = False
    un_seul_montant_30400_par_menage: bool = False
    aucun_autre_reclamant_30400: bool = False
    revenu_personne_charge_confirme: bool = False

    valide_par_comptable: bool = False
    source_personne_charge: str = ""


def aucun_montant_personne_charge_admissible_federal_2025(
) -> MontantPersonneChargeAdmissibleFederal2025:
    return MontantPersonneChargeAdmissibleFederal2025()


def valider_montant_personne_charge_admissible_federal_2025(
    profil: MontantPersonneChargeAdmissibleFederal2025,
) -> MontantPersonneChargeAdmissibleFederal2025:
    if profil.revenu_net_contribuable_ligne_23600 < ZERO:
        raise ValueError(
            "Le revenu net du contribuable à la ligne 23600 "
            "ne peut pas être négatif."
        )

    if profil.revenu_net_personne_charge_2025 < ZERO:
        raise ValueError(
            "Le revenu net de la personne à charge "
            "ne peut pas être négatif."
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
            profil.aucun_epoux_conjoint_2025,
            "Cette première version de la ligne 30400 est limitée au "
            "contribuable sans époux ni conjoint de fait pendant toute "
            "l'année 2025.",
        ),
        (
            profil.personne_charge_est_enfant,
            "Cette première version de la ligne 30400 est limitée à "
            "l'enfant du contribuable.",
        ),
        (
            profil.enfant_soutenu_2025,
            "Le contribuable doit avoir subvenu aux besoins de l'enfant "
            "en 2025.",
        ),
        (
            profil.enfant_a_vecu_avec_contribuable,
            "L'enfant doit avoir vécu avec le contribuable dans ce "
            "profil simple.",
        ),
        (
            profil.habitation_maintenue_par_contribuable,
            "Le contribuable doit avoir maintenu l'habitation où il "
            "vivait avec l'enfant.",
        ),
        (
            profil.enfant_resident_canada_toute_annee,
            "Cette première version exige que l'enfant soit résident "
            "du Canada toute l'année 2025.",
        ),
        (
            profil.aucune_garde_partagee,
            "Les situations de garde partagée ne sont pas supportées "
            "dans cette première version.",
        ),
        (
            profil.aucun_paiement_pension_alimentaire,
            "Les situations avec paiement de pension alimentaire pour "
            "l'enfant ne sont pas supportées dans ce profil simple.",
        ),
        (
            profil.un_seul_montant_30400_par_menage,
            "Un seul montant de la ligne 30400 peut être réclamé par "
            "ménage dans ce profil.",
        ),
        (
            profil.aucun_autre_reclamant_30400,
            "Aucun autre contribuable ne doit réclamer la ligne 30400 "
            "pour cette personne à charge.",
        ),
        (
            profil.revenu_personne_charge_confirme,
            "Le revenu net 2025 de la personne à charge doit être "
            "confirmé.",
        ),
        (
            profil.valide_par_comptable,
            "Le montant fédéral pour personne à charge admissible doit "
            "être validé par le comptable.",
        ),
    )

    for condition, message in controles:
        if not condition:
            raise ValueError(message)

    if profil.personne_charge_18_ans_ou_plus:
        if profil.enfant_moins_18_fin_2025:
            raise ValueError(
                "Le profil est contradictoire : moins de 18 ans "
                "et 18 ans ou plus ne peuvent pas être vrais ensemble."
            )
        if (
            profil.aucune_infirmite_enfant
            or not profil.personne_charge_avec_infirmite
        ):
            raise ValueError(
                "Une infirmité physique ou mentale doit être confirmée "
                "pour la personne à charge de 18 ans ou plus."
            )
        if not profil.dependance_due_uniquement_a_infirmite:
            raise ValueError(
                "La dépendance de la personne à charge doit être "
                "due à l'infirmité."
            )
        if not profil.dependance_periode_considerable:
            raise ValueError(
                "La dépendance de la personne à charge doit exister "
                "pendant une période considérable."
            )
        if not profil.aidant_naturel_base_2687_inclus:
            raise ValueError(
                "Le montant de base de 2 687 $ pour aidant naturel "
                "doit être inclus dans le calcul de la ligne 30400."
            )
        if not profil.preuve_medicale_ou_t2201_confirmee:
            raise ValueError(
                "Une preuve médicale admissible ou un formulaire T2201 "
                "approuvé doit être confirmé."
            )
    else:
        if not profil.enfant_moins_18_fin_2025:
            raise ValueError(
                "L'enfant doit avoir moins de 18 ans à la fin de 2025 "
                "dans ce profil simple."
            )
        if not profil.aucune_infirmite_enfant:
            raise ValueError(
                "L'enfant avec déficience doit être traité séparément "
                "avec les règles du montant canadien pour aidant naturel."
            )
        if (
            profil.personne_charge_avec_infirmite
            or profil.dependance_due_uniquement_a_infirmite
            or profil.dependance_periode_considerable
            or profil.aidant_naturel_base_2687_inclus
            or profil.preuve_medicale_ou_t2201_confirmee
        ):
            raise ValueError(
                "Les indicateurs d'aidant naturel pour une personne "
                "de 18 ans ou plus ne peuvent pas être activés ici."
            )

    if not profil.source_personne_charge.strip():
        raise ValueError(
            "Une source confirmant la situation et le revenu de la "
            "personne à charge est obligatoire."
        )

    return profil


def montant_base_aidant_personne_charge_30400_2025(
    profil: MontantPersonneChargeAdmissibleFederal2025,
) -> Decimal:
    valider_montant_personne_charge_admissible_federal_2025(profil)

    if not profil.reclamer_montant:
        return ZERO

    if (
        profil.personne_charge_18_ans_ou_plus
        and profil.personne_charge_avec_infirmite
        and profil.aidant_naturel_base_2687_inclus
    ):
        return MONTANT_AIDANT_PERSONNE_CHARGE_2025

    return ZERO


def montant_ligne_30400_2025(
    profil: MontantPersonneChargeAdmissibleFederal2025,
) -> Decimal:
    valider_montant_personne_charge_admissible_federal_2025(profil)

    if not profil.reclamer_montant:
        return ZERO

    montant_personnel = montant_personnel_base_federal_2025(
        profil.revenu_net_contribuable_ligne_23600
    )

    montant_aidant = (
        MONTANT_AIDANT_PERSONNE_CHARGE_2025
        if (
            profil.personne_charge_18_ans_ou_plus
            and profil.personne_charge_avec_infirmite
            and profil.aidant_naturel_base_2687_inclus
        )
        else ZERO
    )

    return max(
        arrondir_cent(
            montant_personnel
            + montant_aidant
            - profil.revenu_net_personne_charge_2025
        ),
        ZERO,
    )


def credit_federal_personne_charge_admissible_2025(
    profil: MontantPersonneChargeAdmissibleFederal2025,
) -> Decimal:
    return arrondir_cent(
        montant_ligne_30400_2025(profil)
        * TAUX_CREDIT_FEDERAL_2025
    )



def appliquer_credit_federal_personne_charge_admissible_2025(
    impot: ImpotFederalPreliminaire2025,
    profil: MontantPersonneChargeAdmissibleFederal2025,
) -> ImpotFederalPreliminaire2025:
    """Applique le crédit de la ligne fédérale 30400."""
    valider_montant_personne_charge_admissible_federal_2025(profil)

    if not profil.reclamer_montant:
        return impot

    credit = credit_federal_personne_charge_admissible_2025(profil)

    limitations = []
    for texte in impot.limitations:
        if texte == "Aucun montant pour âge, conjoint ou personne à charge.":
            limitations.append("Aucun montant pour âge ou conjoint.")
        elif texte == "Aucun montant pour âge ou personne à charge.":
            limitations.append("Aucun montant pour âge.")
        else:
            limitations.append(texte)

    limitations.append(
        "Montant fédéral pour personne à charge admissible "
        "ligne 30400 inclus."
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
