"""Ligne fédérale 31270 — montant pour l'achat d'une habitation — 2025.

Extension 5Z : partage documenté entre acquéreurs admissibles, plafond commun
10000 $, part du dossier calculée après les parts convenues ailleurs.

Profil historique conservé :
- acquisition d'une habitation admissible en 2025;
- habitation située au Canada et enregistrée au nom du contribuable
  ou de son époux/conjoint de fait;
- acheteur d'une première habitation;
- intention d'occuper l'habitation comme résidence principale au plus
  tard un an après l'acquisition;
- aucune répartition du montant avec une autre personne;
- aucune utilisation de l'exception liée au crédit d'impôt pour
  personnes handicapées dans cette première version;
- pièces justificatives conservées et validation comptable.

Le montant maximal à la ligne 31270 est de 10 000 $ en 2025.
Dans le profil fiscal fédéral simple de ComptaPrivée, le crédit
non remboursable correspondant est calculé à 14,5 %.

Source :
ARC — ligne 31270, montant pour l'achat d'une habitation — 2025.
"""

from dataclasses import dataclass, replace, fields
from decimal import Decimal

from .tax_federal_2025 import ImpotFederalPreliminaire2025
from .tax_rules_2025 import FEDERAL_BRACKETS_2025, arrondir_cent


ZERO = Decimal("0")
MAXIMUM_LIGNE_31270_2025 = Decimal("10000")
TAUX_CREDIT_FEDERAL_2025 = Decimal("0.145")
SEUIL_PREMIERE_TRANCHE_FEDERALE_2025 = FEDERAL_BRACKETS_2025[0][0]


@dataclass(frozen=True)
class MontantAchatHabitationFederal2025:
    """Profil simple pour la ligne fédérale 31270."""

    reclamer_montant: bool = False
    montant_reclame: Decimal = ZERO

    acquisition_en_2025: bool = False
    habitation_admissible: bool = False
    habitation_situee_au_canada: bool = False
    habitation_enregistree_nom_contribuable_ou_conjoint: bool = False

    premier_acheteur_confirme: bool = False
    aucune_habitation_possedee_habitee_annee_achat_ou_4_precedentes: bool = False

    intention_residence_principale_dans_un_an: bool = False

    aucun_partage_du_montant: bool = False
    aucune_exception_handicap_utilisee: bool = False

    pieces_justificatives_conservees: bool = False
    valide_par_comptable: bool = False
    source_habitation: str = ""
    partage_31270_confirme: bool = False
    montant_attribue_autres_acquereurs: Decimal = ZERO
    autres_acquereurs_admissibles_confirmes: bool = False
    reference_habitation: str = ""
    source_partage: str = ""


def aucun_montant_achat_habitation_2025(
) -> MontantAchatHabitationFederal2025:
    return MontantAchatHabitationFederal2025()


def valider_montant_achat_habitation_2025(
    profil: MontantAchatHabitationFederal2025,
) -> MontantAchatHabitationFederal2025:
    if type(profil.partage_31270_confirme) is not bool or type(profil.autres_acquereurs_admissibles_confirmes) is not bool:
        raise ValueError("Les confirmations de partage 31270 doivent être booléennes.")
    autres = profil.montant_attribue_autres_acquereurs
    if (not isinstance(autres, Decimal) or not autres.is_finite() or not ZERO <= autres <= MAXIMUM_LIGNE_31270_2025
            or autres != arrondir_cent(autres)):
        raise ValueError("Les parts des autres acquéreurs doivent être en cents, entre 0 et 10000 $.")
    if type(profil.reference_habitation) is not str or type(profil.source_partage) is not str:
        raise ValueError("Référence et source du partage 31270 invalides.")
    if profil.partage_31270_confirme:
        for champ in fields(profil):
            v, defaut = getattr(profil, champ.name), champ.default
            if isinstance(defaut, (bool, str)) and type(v) is not type(defaut):
                raise ValueError("Type du profil partagé 31270 invalide : " + champ.name)
            if isinstance(defaut, Decimal) and (not isinstance(v, Decimal) or not v.is_finite()
                    or not ZERO <= v <= MAXIMUM_LIGNE_31270_2025 or v != arrondir_cent(v)):
                raise ValueError("Montant du profil partagé 31270 invalide : " + champ.name)
        if not profil.reclamer_montant or profil.aucun_partage_du_montant or profil.montant_reclame != ZERO:
            raise ValueError("Partage 31270 contradictoire : activer la demande, désactiver aucun partage et laisser le montant manuel à zéro.")
        if not profil.autres_acquereurs_admissibles_confirmes:
            raise ValueError("Tous les autres acquéreurs participant au partage doivent être admissibles à 31270 pour la même habitation.")
        if not profil.reference_habitation.strip() or not profil.source_partage.strip():
            raise ValueError("Le partage 31270 exige une référence d'habitation et la source de l'entente entre tous les acquéreurs.")
    elif autres != ZERO or profil.autres_acquereurs_admissibles_confirmes or profil.reference_habitation or profil.source_partage:
        raise ValueError("Données de partage 31270 sans entente confirmée.")
    if profil.montant_reclame < ZERO:
        raise ValueError(
            "Le montant réclamé à la ligne 31270 ne peut pas être négatif."
        )

    if profil.montant_reclame > MAXIMUM_LIGNE_31270_2025:
        raise ValueError(
            "Le montant réclamé à la ligne 31270 ne peut pas dépasser "
            "10 000 $ en 2025."
        )

    if not profil.reclamer_montant:
        if profil.montant_reclame != ZERO:
            raise ValueError(
                "Un montant ligne 31270 ne peut pas être enregistré "
                "si le crédit n'est pas réclamé."
            )
        return profil

    if profil.montant_reclame <= ZERO and not profil.partage_31270_confirme:
        raise ValueError(
            "Le montant réclamé à la ligne 31270 doit être supérieur à zéro."
        )

    if not profil.acquisition_en_2025:
        raise ValueError(
            "L'habitation doit avoir été acquise en 2025."
        )

    if not profil.habitation_admissible:
        raise ValueError(
            "L'habitation doit être admissible au montant pour l'achat "
            "d'une habitation."
        )

    if not profil.habitation_situee_au_canada:
        raise ValueError(
            "L'habitation admissible doit être située au Canada."
        )

    if not profil.habitation_enregistree_nom_contribuable_ou_conjoint:
        raise ValueError(
            "L'habitation doit être enregistrée au nom du contribuable "
            "ou de son époux/conjoint de fait."
        )

    if not profil.premier_acheteur_confirme:
        raise ValueError(
            "Cette première version exige le profil acheteur d'une "
            "première habitation."
        )

    if (
        not profil
        .aucune_habitation_possedee_habitee_annee_achat_ou_4_precedentes
    ):
        raise ValueError(
            "Le contribuable ne doit pas avoir habité une autre habitation "
            "qu'il possédait, ou que son époux/conjoint possédait, pendant "
            "l'année de l'achat ou l'une des quatre années précédentes."
        )

    if not profil.intention_residence_principale_dans_un_an:
        raise ValueError(
            "Le contribuable doit avoir l'intention d'occuper l'habitation "
            "comme résidence principale au plus tard un an après "
            "l'acquisition."
        )

    if not profil.aucun_partage_du_montant and not profil.partage_31270_confirme:
        raise ValueError(
            "Le partage du montant de la ligne 31270 est hors du profil "
            "simple de cette première version."
        )

    if not profil.aucune_exception_handicap_utilisee:
        raise ValueError(
            "L'exception liée au crédit d'impôt pour personnes handicapées "
            "est hors du profil simple de cette première version."
        )

    if not profil.pieces_justificatives_conservees:
        raise ValueError(
            "Les pièces justificatives de l'acquisition doivent être "
            "conservées."
        )

    if not profil.valide_par_comptable:
        raise ValueError(
            "La ligne 31270 doit être validée par le comptable."
        )

    if not profil.source_habitation.strip():
        raise ValueError(
            "Une source confirmant l'acquisition et l'admissibilité de "
            "l'habitation est obligatoire."
        )

    return profil


def montant_ligne_31270_2025(
    profil: MontantAchatHabitationFederal2025,
) -> Decimal:
    valider_montant_achat_habitation_2025(profil)
    if not profil.reclamer_montant:
        return ZERO
    if profil.partage_31270_confirme:
        return arrondir_cent(MAXIMUM_LIGNE_31270_2025 - profil.montant_attribue_autres_acquereurs)
    return arrondir_cent(profil.montant_reclame)


def credit_federal_ligne_31270_2025(
    profil: MontantAchatHabitationFederal2025,
) -> Decimal:
    return arrondir_cent(
        montant_ligne_31270_2025(profil)
        * TAUX_CREDIT_FEDERAL_2025
    )


def appliquer_credit_federal_ligne_31270_2025(
    impot: ImpotFederalPreliminaire2025,
    profil: MontantAchatHabitationFederal2025,
) -> ImpotFederalPreliminaire2025:
    valider_montant_achat_habitation_2025(profil)

    if not profil.reclamer_montant:
        return impot

    credit = credit_federal_ligne_31270_2025(profil)
    limitations = list(impot.limitations)
    limitations.append(
        "Montant pour l'achat d'une habitation ligne 31270 inclus."
    )

    return replace(
        impot,
        impot_federal_de_base=max(
            arrondir_cent(impot.impot_federal_de_base - credit),
            ZERO,
        ),
        limitations=tuple(limitations),
    )


def integration_31270_sans_credit_compensatoire_autorisee_2025(
    revenu_imposable_federal: Decimal,
) -> bool:
    """Garde-fou provisoire lié à la ligne fédérale 34990."""
    if revenu_imposable_federal < ZERO:
        raise ValueError(
            "Le revenu imposable fédéral ne peut pas être négatif."
        )

    return (
        revenu_imposable_federal
        <= SEUIL_PREMIERE_TRANCHE_FEDERALE_2025
    )


def description_partage_31270_2025(profil):
    valider_montant_achat_habitation_2025(profil)
    if not profil.partage_31270_confirme:
        return "Aucun partage du montant 31270 : oui"
    return (f"Partage 31270 — habitation {profil.reference_habitation} : plafond commun 10000,00 $ "
            f"moins parts des autres acquéreurs {profil.montant_attribue_autres_acquereurs:.2f} $ "
            f"= part du dossier {montant_ligne_31270_2025(profil):.2f} $. "
            f"Admissibilité de tous les participants confirmée; entente : {profil.source_partage}")
