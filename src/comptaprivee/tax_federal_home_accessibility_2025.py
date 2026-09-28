"""Ligne fédérale 31285 — dépenses pour l'accessibilité domiciliaire — 2025.

Première version volontairement limitée au profil simple :
- le contribuable réclame pour lui-même;
- il est un particulier déterminé parce qu'il a 65 ans ou plus à la fin
  de 2025, ou qu'il est admissible au crédit d'impôt pour personnes
  handicapées (CIPH) à un moment de l'année;
- le logement admissible est situé au Canada, appartient au contribuable
  et est normalement habité (ou censé l'être) par lui;
- les dépenses ont été effectuées ou engagées en 2025 pour des travaux
  et biens de 2025;
- la rénovation est durable, fait partie intégrante du logement et vise
  l'accessibilité, la mobilité/fonctionnalité ou la réduction du risque
  de blessure;
- partage documenté possible pour un logement unique en 2025 (bloc 5AA);
- aucune ventilation entreprise/location dans cette première version;
- les dépenses non admissibles ont été exclues;
- pièces justificatives conservées et validation comptable.

Le maximum fédéral 2025 est de 20 000 $ de dépenses admissibles.
Dans le profil fiscal fédéral simple de ComptaPrivée, le crédit
non remboursable correspondant est calculé à 14,5 %.

Une dépense qui est également admissible comme frais médical peut être
réclamée aux deux titres pour l'année d'imposition 2025, sous réserve des
règles propres à chaque crédit.

Source :
ARC — ligne 31285, dépenses pour l'accessibilité domiciliaire — 2025.
"""

from dataclasses import dataclass, fields, replace
from decimal import Decimal

from .tax_federal_2025 import ImpotFederalPreliminaire2025
from .tax_rules_2025 import FEDERAL_BRACKETS_2025, arrondir_cent


ZERO = Decimal("0")
MAXIMUM_DEPENSES_ACCESSIBILITE_2025 = Decimal("20000")
TAUX_CREDIT_FEDERAL_2025 = Decimal("0.145")
SEUIL_PREMIERE_TRANCHE_FEDERALE_2025 = FEDERAL_BRACKETS_2025[0][0]


@dataclass(frozen=True)
class DepensesAccessibiliteDomiciliaireFederal2025:
    """Profil simple pour la ligne fédérale 31285."""

    reclamer_montant: bool = False
    depenses_admissibles: Decimal = ZERO

    demande_pour_soi_meme: bool = False
    age_65_plus_fin_annee: bool = False
    admissible_ciph: bool = False

    logement_situe_au_canada: bool = False
    logement_propriete_du_contribuable: bool = False
    logement_normalement_habite_par_contribuable: bool = False

    renovation_durable_et_integrante: bool = False
    accessibilite_ou_reduction_risque_confirmee: bool = False
    travaux_et_biens_2025_uniquement: bool = False

    aucune_part_entreprise_ou_location: bool = False
    aucun_partage_de_la_demande: bool = False
    fournisseurs_lies_admissibles_confirme: bool = False
    depenses_non_admissibles_exclues: bool = False

    pieces_justificatives_conservees: bool = False
    valide_par_comptable: bool = False
    source_renovation: str = ""
    partage_31285_confirme: bool = False
    montant_reclame_autres: Decimal = ZERO
    autres_participants_admissibles_confirmes: bool = False
    logement_unique_2025_confirme: bool = False
    reference_logement: str = ""
    source_partage: str = ""


def aucune_depense_accessibilite_domiciliaire_2025(
) -> DepensesAccessibiliteDomiciliaireFederal2025:
    return DepensesAccessibiliteDomiciliaireFederal2025()


def valider_depenses_accessibilite_domiciliaire_2025(
    profil: DepensesAccessibiliteDomiciliaireFederal2025,
) -> DepensesAccessibiliteDomiciliaireFederal2025:
    for nom in ("partage_31285_confirme", "autres_participants_admissibles_confirmes", "logement_unique_2025_confirme"):
        if type(getattr(profil, nom)) is not bool:
            raise ValueError("Confirmation de partage 31285 invalide : " + nom)
    autres = profil.montant_reclame_autres
    if (not isinstance(autres, Decimal) or not autres.is_finite()
            or not ZERO <= autres <= MAXIMUM_DEPENSES_ACCESSIBILITE_2025 or autres != arrondir_cent(autres)):
        raise ValueError("Les demandes des autres participants doivent être en cents, entre 0 et 20000 $.")
    if type(profil.reference_logement) is not str or type(profil.source_partage) is not str:
        raise ValueError("Référence et source du partage 31285 invalides.")
    if profil.partage_31285_confirme:
        for champ in fields(profil):
            v, defaut = getattr(profil, champ.name), champ.default
            if isinstance(defaut, (bool, str)) and type(v) is not type(defaut):
                raise ValueError("Type du profil partagé 31285 invalide : " + champ.name)
            if isinstance(defaut, Decimal) and (not isinstance(v, Decimal) or not v.is_finite()
                    or not ZERO <= v <= Decimal("999999999.99") or v != arrondir_cent(v)):
                raise ValueError("Montant du profil partagé 31285 invalide : " + champ.name)
        if not profil.reclamer_montant or profil.aucun_partage_de_la_demande:
            raise ValueError("Partage 31285 contradictoire : activer la demande et désactiver aucun partage.")
        if not profil.autres_participants_admissibles_confirmes or not profil.logement_unique_2025_confirme:
            raise ValueError("Confirmer l'admissibilité de tous les participants habitant le même logement et leur logement admissible unique en 2025.")
        if not profil.reference_logement.strip() or not profil.source_partage.strip():
            raise ValueError("Le partage 31285 exige la référence du logement et l'entente de tous les participants.")
        if autres > min(profil.depenses_admissibles, MAXIMUM_DEPENSES_ACCESSIBILITE_2025):
            raise ValueError("Les demandes des autres participants dépassent les dépenses communes plafonnées.")
    elif (autres != ZERO or profil.autres_participants_admissibles_confirmes or profil.logement_unique_2025_confirme
            or profil.reference_logement or profil.source_partage):
        raise ValueError("Données de partage 31285 sans entente confirmée.")
    if profil.depenses_admissibles < ZERO:
        raise ValueError(
            "Les dépenses admissibles de la ligne 31285 "
            "ne peuvent pas être négatives."
        )

    if profil.depenses_admissibles > MAXIMUM_DEPENSES_ACCESSIBILITE_2025 and not profil.partage_31285_confirme:
        raise ValueError(
            "Les dépenses admissibles de la ligne 31285 "
            "ne peuvent pas dépasser 20 000 $ en 2025."
        )

    if not profil.reclamer_montant:
        if profil.depenses_admissibles != ZERO:
            raise ValueError(
                "Des dépenses ligne 31285 ne peuvent pas être enregistrées "
                "si le crédit n'est pas réclamé."
            )
        return profil

    if profil.depenses_admissibles <= ZERO:
        raise ValueError(
            "Les dépenses admissibles de la ligne 31285 "
            "doivent être supérieures à zéro."
        )

    if not profil.demande_pour_soi_meme:
        raise ValueError(
            "Cette première version de la ligne 31285 est limitée "
            "à une demande faite par le contribuable pour lui-même."
        )

    if not (
        profil.age_65_plus_fin_annee
        or profil.admissible_ciph
    ):
        raise ValueError(
            "Le contribuable doit être âgé de 65 ans ou plus à la fin "
            "de l'année, ou être admissible au CIPH."
        )

    if not profil.logement_situe_au_canada:
        raise ValueError(
            "Le logement admissible de la ligne 31285 "
            "doit être situé au Canada."
        )

    if not profil.logement_propriete_du_contribuable:
        raise ValueError(
            "Cette première version exige que le logement admissible "
            "appartienne au contribuable."
        )

    if not profil.logement_normalement_habite_par_contribuable:
        raise ValueError(
            "Le logement doit être normalement habité, ou censé l'être, "
            "par le contribuable pendant l'année."
        )

    if not profil.renovation_durable_et_integrante:
        raise ValueError(
            "La rénovation admissible doit être durable et faire partie "
            "intégrante du logement."
        )

    if not profil.accessibilite_ou_reduction_risque_confirmee:
        raise ValueError(
            "La rénovation doit améliorer l'accès, la mobilité ou la "
            "fonctionnalité dans le logement, ou réduire le risque "
            "de blessure."
        )

    if not profil.travaux_et_biens_2025_uniquement:
        raise ValueError(
            "Les dépenses réclamées doivent viser les travaux effectués "
            "et les biens acquis au cours de 2025."
        )

    if not profil.aucune_part_entreprise_ou_location:
        raise ValueError(
            "La ventilation entreprise/location est hors du profil simple "
            "de cette première version."
        )

    if not profil.aucun_partage_de_la_demande and not profil.partage_31285_confirme:
        raise ValueError(
            "Le partage de la demande ligne 31285 est hors du profil "
            "simple de cette première version."
        )

    if not profil.fournisseurs_lies_admissibles_confirme:
        raise ValueError(
            "Les règles visant les fournisseurs liés doivent être "
            "confirmées : aucun fournisseur lié non admissible, ou "
            "fournisseur lié inscrit à la TPS/TVH lorsque requis."
        )

    if not profil.depenses_non_admissibles_exclues:
        raise ValueError(
            "Les dépenses non admissibles doivent être exclues "
            "de la ligne 31285."
        )

    if not profil.pieces_justificatives_conservees:
        raise ValueError(
            "Les accords, factures et reçus admissibles doivent être "
            "conservés."
        )

    if not profil.valide_par_comptable:
        raise ValueError(
            "La ligne 31285 doit être validée par le comptable."
        )

    if not profil.source_renovation.strip():
        raise ValueError(
            "Une source confirmant les rénovations et dépenses admissibles "
            "est obligatoire."
        )

    return profil


def montant_ligne_31285_2025(
    profil: DepensesAccessibiliteDomiciliaireFederal2025,
) -> Decimal:
    valider_depenses_accessibilite_domiciliaire_2025(profil)
    if not profil.reclamer_montant:
        return ZERO
    return arrondir_cent(min(profil.depenses_admissibles, MAXIMUM_DEPENSES_ACCESSIBILITE_2025) - profil.montant_reclame_autres)


def description_partage_31285_2025(profil: DepensesAccessibiliteDomiciliaireFederal2025) -> str:
    if not profil.partage_31285_confirme:
        return "Aucun partage de la demande ligne 31285 : oui; aucun partage"
    montant = montant_ligne_31285_2025(profil)
    return (f"Partage 31285 — logement {profil.reference_logement}; logement unique en 2025 pour les participants; "
        f"dépenses communes {profil.depenses_admissibles:.2f} $; plafond 20000 $; "
        f"autres demandes {profil.montant_reclame_autres:.2f} $; solde {montant:.2f} $; "
        f"participants admissibles confirmés; entente : {profil.source_partage}")


def credit_federal_ligne_31285_2025(
    profil: DepensesAccessibiliteDomiciliaireFederal2025,
) -> Decimal:
    return arrondir_cent(
        montant_ligne_31285_2025(profil)
        * TAUX_CREDIT_FEDERAL_2025
    )


def appliquer_credit_federal_ligne_31285_2025(
    impot: ImpotFederalPreliminaire2025,
    profil: DepensesAccessibiliteDomiciliaireFederal2025,
) -> ImpotFederalPreliminaire2025:
    valider_depenses_accessibilite_domiciliaire_2025(profil)

    if not profil.reclamer_montant:
        return impot

    credit = credit_federal_ligne_31285_2025(profil)
    limitations = list(impot.limitations)
    limitations.append(
        "Dépenses pour l'accessibilité domiciliaire ligne 31285 incluses."
    )

    return replace(
        impot,
        impot_federal_de_base=max(
            arrondir_cent(impot.impot_federal_de_base - credit),
            ZERO,
        ),
        limitations=tuple(limitations),
    )


def integration_31285_sans_credit_compensatoire_autorisee_2025(
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
