"""Frais de garde fédéraux simples 2025 — Bloc 4B.

Périmètre initial :
- formulaire T778, parties A et B seulement;
- ligne fédérale 21400;
- frais pour services de garde fournis en 2025;
- demandeur seul à soutenir l'enfant ou personne au revenu net le moins élevé;
- aucune situation spéciale des parties C ou D;
- aucun crédit Québec calculé dans ce module.

Les plafonds annuels du T778 utilisés dans ce bloc sont :
- 8 000 $ par enfant de moins de 7 ans sans DTC;
- 5 000 $ par enfant de 7 à 16 ans, ou enfant plus âgé admissible
  pour déficience sans DTC;
- 11 000 $ par enfant pour lequel le DTC peut être demandé.
"""

from dataclasses import dataclass, replace
from decimal import Decimal

from .tax_income_2025 import RevenuNetImposable2025
from .tax_rules_2025 import arrondir_cent


ZERO = Decimal("0")
PLAFOND_MOINS_7_2025 = Decimal("8000")
PLAFOND_7_A_16_OU_INFIRME_2025 = Decimal("5000")
PLAFOND_DTC_2025 = Decimal("11000")
DEUX_TIERS = Decimal("2") / Decimal("3")


@dataclass(frozen=True)
class FraisGardeFederaux2025:
    frais_admissibles_payes: Decimal = ZERO
    revenu_gagne_t778: Decimal = ZERO
    nombre_enfants_moins_7_sans_dtc: int = 0
    nombre_enfants_7_a_16_ou_infirmes_sans_dtc: int = 0
    nombre_enfants_dtc: int = 0
    source: str = ""
    valide_par_comptable: bool = False
    services_fournis_en_2025_confirmes: bool = False
    frais_pour_gagner_revenu_confirmes: bool = False
    recus_confirmes: bool = False
    demandeur_seul_ou_revenu_inferieur_confirme: bool = False
    partie_c_requise: bool = False
    partie_d_requise: bool = False
    camp_avec_hebergement: bool = False
    garde_partagee: bool = False
    repartition_entre_contribuables: bool = False
    demandeur_revenu_superieur: bool = False


def _montant_fini_non_negatif(valeur: Decimal, libelle: str) -> Decimal:
    if not valeur.is_finite():
        raise ValueError(f"{libelle} doit être un nombre fini.")
    if valeur < ZERO:
        raise ValueError(f"{libelle} ne peut pas être négatif.")
    return arrondir_cent(valeur)


def _entier_non_negatif(valeur: int, libelle: str) -> int:
    if isinstance(valeur, bool) or not isinstance(valeur, int):
        raise ValueError(f"{libelle} doit être un entier.")
    if valeur < 0:
        raise ValueError(f"{libelle} ne peut pas être négatif.")
    return valeur


def valider_frais_garde_federaux_2025(
    profil: FraisGardeFederaux2025,
) -> FraisGardeFederaux2025:
    frais = _montant_fini_non_negatif(
        profil.frais_admissibles_payes,
        "Les frais de garde admissibles payés",
    )
    revenu_gagne = _montant_fini_non_negatif(
        profil.revenu_gagne_t778,
        "Le revenu gagné T778",
    )
    moins_7 = _entier_non_negatif(
        profil.nombre_enfants_moins_7_sans_dtc,
        "Le nombre d'enfants de moins de 7 ans sans DTC",
    )
    sept_16 = _entier_non_negatif(
        profil.nombre_enfants_7_a_16_ou_infirmes_sans_dtc,
        "Le nombre d'enfants de 7 à 16 ans ou infirmes sans DTC",
    )
    dtc = _entier_non_negatif(
        profil.nombre_enfants_dtc,
        "Le nombre d'enfants admissibles au DTC",
    )

    profil = replace(
        profil,
        frais_admissibles_payes=frais,
        revenu_gagne_t778=revenu_gagne,
        nombre_enfants_moins_7_sans_dtc=moins_7,
        nombre_enfants_7_a_16_ou_infirmes_sans_dtc=sept_16,
        nombre_enfants_dtc=dtc,
        source=profil.source.strip(),
    )

    if frais == ZERO:
        return profil

    if not profil.valide_par_comptable:
        raise ValueError(
            "Les frais de garde doivent être validés par le comptable."
        )
    if not profil.services_fournis_en_2025_confirmes:
        raise ValueError(
            "Le Bloc 4B exige des services de garde fournis en 2025."
        )
    if not profil.frais_pour_gagner_revenu_confirmes:
        raise ValueError(
            "Le Bloc 4B simple exige des frais engagés pour permettre au "
            "demandeur de gagner un revenu."
        )
    if not profil.recus_confirmes:
        raise ValueError(
            "Les reçus de frais de garde doivent être confirmés."
        )
    if not profil.demandeur_seul_ou_revenu_inferieur_confirme:
        raise ValueError(
            "Le demandeur doit être seul à soutenir l'enfant ou être la "
            "personne au revenu net le moins élevé dans le Bloc 4B."
        )
    if not profil.source:
        raise ValueError(
            "La source des frais de garde et du calcul T778 est obligatoire."
        )
    if revenu_gagne == ZERO:
        raise ValueError(
            "Le revenu gagné T778 doit être supérieur à zéro dans le Bloc 4B."
        )
    if moins_7 + sept_16 + dtc == 0:
        raise ValueError(
            "Au moins un enfant admissible doit être indiqué pour le Bloc 4B."
        )

    cas_avances = (
        profil.partie_c_requise,
        profil.partie_d_requise,
        profil.camp_avec_hebergement,
        profil.garde_partagee,
        profil.repartition_entre_contribuables,
        profil.demandeur_revenu_superieur,
    )
    if any(cas_avances):
        raise ValueError(
            "La situation indiquée est hors périmètre 4B et nécessite "
            "un traitement T778 avancé."
        )

    return profil


def plafond_enfants_frais_garde_2025(
    profil: FraisGardeFederaux2025,
) -> Decimal:
    profil = valider_frais_garde_federaux_2025(profil)
    montant = (
        Decimal(profil.nombre_enfants_moins_7_sans_dtc)
        * PLAFOND_MOINS_7_2025
        + Decimal(
            profil.nombre_enfants_7_a_16_ou_infirmes_sans_dtc
        )
        * PLAFOND_7_A_16_OU_INFIRME_2025
        + Decimal(profil.nombre_enfants_dtc)
        * PLAFOND_DTC_2025
    )
    return arrondir_cent(montant)


def limite_deux_tiers_revenu_gagne_2025(
    profil: FraisGardeFederaux2025,
) -> Decimal:
    profil = valider_frais_garde_federaux_2025(profil)
    return arrondir_cent(profil.revenu_gagne_t778 * DEUX_TIERS)


def deduction_frais_garde_federale_2025(
    profil: FraisGardeFederaux2025,
) -> Decimal:
    profil = valider_frais_garde_federaux_2025(profil)
    if profil.frais_admissibles_payes == ZERO:
        return ZERO
    return min(
        profil.frais_admissibles_payes,
        plafond_enfants_frais_garde_2025(profil),
        limite_deux_tiers_revenu_gagne_2025(profil),
    )


def appliquer_frais_garde_federaux_2025(
    revenu: RevenuNetImposable2025,
    profil: FraisGardeFederaux2025,
) -> RevenuNetImposable2025:
    if revenu.annee_fiscale != 2025:
        raise ValueError(
            "Les frais de garde actuels acceptent uniquement l'année 2025."
        )

    deduction = deduction_frais_garde_federale_2025(profil)
    if deduction == ZERO:
        return revenu

    limitations = tuple(
        texte
        for texte in revenu.limitations
        if texte != "Aucune autre déduction de revenu net ou imposable."
    ) + (
        "Frais de garde fédéraux T778 / ligne 21400 inclus.",
        "Parties C/D et situations avancées T778 hors périmètre 4B.",
        "Aucun crédit Québec pour frais de garde n'est calculé dans le Bloc 4B.",
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
        profil=revenu.profil + " + frais de garde 4B",
        limitations=limitations,
    )


def lignes_resume_frais_garde_federaux_2025(
    profil: FraisGardeFederaux2025,
) -> list[str]:
    profil = valider_frais_garde_federaux_2025(profil)
    if profil.frais_admissibles_payes == ZERO:
        return []

    deduction = deduction_frais_garde_federale_2025(profil)
    return [
        "",
        "FRAIS DE GARDE 2025 VALIDÉS — BLOC 4B",
        f"Déduction fédérale T778 — ligne 21400 : {deduction:.2f} $",
        (
            "Frais admissibles payés : "
            f"{profil.frais_admissibles_payes:.2f} $"
        ),
        (
            "Plafond annuel selon les enfants : "
            f"{plafond_enfants_frais_garde_2025(profil):.2f} $"
        ),
        (
            "Limite des 2/3 du revenu gagné : "
            f"{limite_deux_tiers_revenu_gagne_2025(profil):.2f} $"
        ),
        f"Source : {profil.source}",
    ]
