"""Ligne fédérale 30450 — aidant naturel pour autre personne à charge — 2025.

Première version volontairement limitée à un profil simple et vérifié
pour une seule personne à charge.

La ligne 30450 vise une personne à charge de 18 ans ou plus qui :
- dépend du contribuable en raison d'une infirmité mentale ou physique;
- est un enfant, petit-enfant, parent, grand-parent, frère, sœur,
  tante, oncle, nièce ou neveu du contribuable ou de son conjoint;
- a un revenu net 2025 (ligne 23600) inférieur à 28 798 $;
- n'est pas la même personne pour laquelle un montant est demandé
  à la ligne 30300 ou 30400.

Pour les liens autres qu'enfant ou petit-enfant, cette première version
exige que la personne ait résidé au Canada à un moment de 2025.

Le bloc 5W autorise le partage documenté entre soutiens pour cette personne.
Les pensions alimentaires et plusieurs personnes restent hors de ce profil.

Calcul de l'annexe 5 — ligne 30450 :
1. 28 798 $ moins le revenu net de la personne;
2. résultat limité à un maximum de 8 601 $;
3. minimum zéro.

Le crédit fédéral non remboursable 2025 est calculé à 14,5 % du montant
admissible dans le profil simple actuellement pris en charge.

Source :
ARC — Annexe 5, ligne 30450 — année d'imposition 2025.
"""

from dataclasses import dataclass, fields, replace
from decimal import Decimal

from .tax_federal_2025 import ImpotFederalPreliminaire2025
from .tax_rules_2025 import FEDERAL_BRACKETS_2025, arrondir_cent


ZERO = Decimal("0")
BASE_CALCUL_30450_2025 = Decimal("28798")
MAXIMUM_LIGNE_30450_2025 = Decimal("8601")
TAUX_CREDIT_FEDERAL_2025 = Decimal("0.145")
SEUIL_PREMIERE_TRANCHE_FEDERALE_2025 = FEDERAL_BRACKETS_2025[0][0]

LIEN_ENFANT = "enfant"
LIEN_PETIT_ENFANT = "petit_enfant"
LIEN_PARENT = "parent"
LIEN_GRAND_PARENT = "grand_parent"
LIEN_FRERE_SOEUR = "frere_soeur"
LIEN_TANTE_ONCLE = "tante_oncle"
LIEN_NIECE_NEVEU = "niece_neveu"

LIENS_AUTORISES = {
    LIEN_ENFANT,
    LIEN_PETIT_ENFANT,
    LIEN_PARENT,
    LIEN_GRAND_PARENT,
    LIEN_FRERE_SOEUR,
    LIEN_TANTE_ONCLE,
    LIEN_NIECE_NEVEU,
}

LIENS_EXCEPTION_RESIDENCE = {
    LIEN_ENFANT,
    LIEN_PETIT_ENFANT,
}


@dataclass(frozen=True)
class AidantNaturelAutrePersonneChargeFederal2025:
    """Profil simple pour la ligne fédérale 30450."""

    reclamer_montant: bool = False

    lien_personne: str = ""
    revenu_net_personne_ligne_23600: Decimal = ZERO

    age_18_ans_ou_plus: bool = False
    personne_soutenue_en_2025: bool = False

    infirmite_physique_ou_mentale: bool = False
    dependance_due_uniquement_a_infirmite: bool = False
    dependance_periode_considerable: bool = False

    resident_canada_au_moins_un_moment_2025: bool = False

    aucune_reclamation_ligne_30300_30400_pour_personne: bool = False
    aucun_paiement_pension_alimentaire_pour_personne: bool = False

    aucun_partage_reclamation_30450: bool = False

    preuve_medicale_ou_t2201_confirmee: bool = False
    valide_par_comptable: bool = False

    source_personne: str = ""

    partage_30450_confirme: bool = False
    montant_attribue_autres_soutiens: Decimal = ZERO
    reference_personne: str = ""
    source_partage: str = ""


def aucun_aidant_naturel_30450_2025(
) -> AidantNaturelAutrePersonneChargeFederal2025:
    return AidantNaturelAutrePersonneChargeFederal2025()


def valider_aidant_naturel_30450_2025(
    profil: AidantNaturelAutrePersonneChargeFederal2025,
) -> AidantNaturelAutrePersonneChargeFederal2025:
    if type(profil.partage_30450_confirme) is not bool:
        raise ValueError("La confirmation de partage 30450 doit être booléenne.")
    autres = profil.montant_attribue_autres_soutiens
    if (not isinstance(autres, Decimal) or not autres.is_finite()
            or autres < ZERO or autres != arrondir_cent(autres)):
        raise ValueError("La somme attribuée aux autres soutiens doit être un montant positif ou nul, en cents.")
    if type(profil.reference_personne) is not str or type(profil.source_partage) is not str:
        raise ValueError("La référence et la source du partage 30450 doivent être textuelles.")
    if profil.partage_30450_confirme:
        for champ in fields(profil):
            valeur, defaut = getattr(profil, champ.name), champ.default
            if isinstance(defaut, bool) and type(valeur) is not bool:
                raise ValueError(f"Confirmation 30450 invalide : {champ.name}.")
            if isinstance(defaut, str) and type(valeur) is not str:
                raise ValueError(f"Texte 30450 invalide : {champ.name}.")
        revenu = profil.revenu_net_personne_ligne_23600
        if (not isinstance(revenu, Decimal) or not revenu.is_finite()
                or revenu < ZERO or revenu != arrondir_cent(revenu)):
            raise ValueError("Revenu 23600 du partage 30450 invalide.")
        if not profil.reclamer_montant or profil.aucun_partage_reclamation_30450:
            raise ValueError("Le partage 30450 contredit les confirmations du profil.")
        if not profil.reference_personne.strip() or not profil.source_partage.strip():
            raise ValueError("Le partage 30450 exige la référence de la personne et la source de l'entente entre tous les soutiens.")
    elif autres != ZERO or profil.reference_personne or profil.source_partage:
        raise ValueError("Les données de partage 30450 exigent une entente confirmée.")
    if profil.revenu_net_personne_ligne_23600 < ZERO:
        raise ValueError(
            "Le revenu net de la personne — ligne 23600 — "
            "ne peut pas être négatif."
        )

    if not profil.reclamer_montant:
        return profil

    if profil.lien_personne not in LIENS_AUTORISES:
        raise ValueError(
            "Le lien avec la personne à charge n'est pas admissible "
            "à la ligne 30450."
        )

    if not profil.age_18_ans_ou_plus:
        raise ValueError(
            "La personne à charge doit avoir 18 ans ou plus "
            "pour la ligne 30450."
        )

    if not profil.personne_soutenue_en_2025:
        raise ValueError(
            "La personne doit avoir été soutenue par le contribuable "
            "en 2025."
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

    if (
        profil.lien_personne not in LIENS_EXCEPTION_RESIDENCE
        and not profil.resident_canada_au_moins_un_moment_2025
    ):
        raise ValueError(
            "Pour ce lien familial, la personne à charge doit avoir "
            "résidé au Canada à un moment de 2025."
        )

    if profil.revenu_net_personne_ligne_23600 >= BASE_CALCUL_30450_2025:
        raise ValueError(
            "Le revenu net 2025 de la personne doit être inférieur "
            "à 28 798 $ pour la ligne 30450."
        )

    if not profil.aucune_reclamation_ligne_30300_30400_pour_personne:
        raise ValueError(
            "Aucun montant ne doit être réclamé à la ligne 30300 "
            "ou 30400 pour cette même personne."
        )

    if not profil.aucun_paiement_pension_alimentaire_pour_personne:
        raise ValueError(
            "Les situations de pension alimentaire sont hors du "
            "profil simple de la ligne 30450."
        )

    if not profil.aucun_partage_reclamation_30450 and not profil.partage_30450_confirme:
        raise ValueError(
            "Le partage de la réclamation 30450 entre plusieurs "
            "personnes est hors du profil simple actuel."
        )

    if not profil.preuve_medicale_ou_t2201_confirmee:
        raise ValueError(
            "Une preuve médicale admissible ou un formulaire T2201 "
            "approuvé doit être confirmé."
        )

    if not profil.valide_par_comptable:
        raise ValueError(
            "La ligne 30450 doit être validée par le comptable."
        )

    if not profil.source_personne.strip():
        raise ValueError(
            "Une source confirmant le lien, le revenu, l'infirmité "
            "et la résidence lorsque requise est obligatoire."
        )

    if profil.partage_30450_confirme:
        plafond = min(MAXIMUM_LIGNE_30450_2025,
            max(BASE_CALCUL_30450_2025 - profil.revenu_net_personne_ligne_23600, ZERO))
        if autres > plafond:
            raise ValueError("Les parts attribuées aux autres soutiens dépassent le plafond 30450 après réduction du revenu.")
    return profil


def montant_ligne_30450_2025(
    profil: AidantNaturelAutrePersonneChargeFederal2025,
) -> Decimal:
    valider_aidant_naturel_30450_2025(profil)

    if not profil.reclamer_montant:
        return ZERO

    montant = max(
        BASE_CALCUL_30450_2025
        - profil.revenu_net_personne_ligne_23600,
        ZERO,
    )

    plafond = arrondir_cent(min(montant, MAXIMUM_LIGNE_30450_2025))
    return arrondir_cent(plafond - profil.montant_attribue_autres_soutiens)


def credit_federal_ligne_30450_2025(
    profil: AidantNaturelAutrePersonneChargeFederal2025,
) -> Decimal:
    return arrondir_cent(
        montant_ligne_30450_2025(profil)
        * TAUX_CREDIT_FEDERAL_2025
    )


def nombre_personnes_charge_ligne_51120_2025(
    profil: AidantNaturelAutrePersonneChargeFederal2025,
) -> int:
    valider_aidant_naturel_30450_2025(profil)
    return int(montant_ligne_30450_2025(profil) > ZERO)


def description_partage_30450_2025(profil: AidantNaturelAutrePersonneChargeFederal2025) -> str:
    """Ventilation du plafond, des parts convenues ailleurs et du solde du dossier."""
    valider_aidant_naturel_30450_2025(profil)
    if not profil.partage_30450_confirme:
        return "Aucun partage de la réclamation 30450 : oui"
    plafond = arrondir_cent(min(MAXIMUM_LIGNE_30450_2025,
        max(BASE_CALCUL_30450_2025 - profil.revenu_net_personne_ligne_23600, ZERO)))
    part = montant_ligne_30450_2025(profil)
    return (f"Partage 30450 — {profil.reference_personne} : plafond {plafond:.2f} $; "
            f"moins parts attribuées aux autres soutiens {plafond - part:.2f} $ "
            f"= part du dossier {part:.2f} $; "
            f"entente validée : {profil.source_partage}")


def appliquer_credit_federal_ligne_30450_2025(
    impot: ImpotFederalPreliminaire2025,
    profil: AidantNaturelAutrePersonneChargeFederal2025,
) -> ImpotFederalPreliminaire2025:
    """Applique le crédit non remboursable de la ligne 30450."""
    valider_aidant_naturel_30450_2025(profil)

    if not profil.reclamer_montant:
        return impot

    credit = credit_federal_ligne_30450_2025(profil)
    limitations = list(impot.limitations)
    limitations.append(
        "Montant canadien pour aidant naturel ligne 30450 inclus."
    )

    return replace(
        impot,
        impot_federal_de_base=max(
            arrondir_cent(impot.impot_federal_de_base - credit),
            ZERO,
        ),
        limitations=tuple(limitations),
    )


def integration_30450_sans_credit_compensatoire_autorisee_2025(
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
