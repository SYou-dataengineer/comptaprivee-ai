"""Montant canadien pour aidant naturel — enfant de moins de 18 ans — 2025.

Extension 5V : combinaison explicite 30400/30500 du même enfant mineur
avec infirmité, parent sans conjoint, référence concordante et preuve médicale.
Le supplément de 2687 $ est porté uniquement à 30500.
Extension 5Y : plusieurs fiches d’enfants vivant avec leurs deux parents
toute l’année, attribution unique et preuve propre à chaque enfant.

Profil historique conservé :
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
au conjoint et les autres interactions particulières avec
la ligne 30400 restent à étendre séparément afin d'éviter une réclamation
incorrecte.

Source fiscale :
ARC — ligne 30500, montant canadien pour aidant naturel pour enfants
de moins de 18 ans ayant une infirmité — année d'imposition 2025.
"""

from dataclasses import dataclass, replace, fields
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
    enfant_reclame_30400: bool = False
    reference_enfant: str = ""
    enfants_detailles: tuple["EnfantAidant30500", ...] = ()
    identites_distinctes_confirmees: bool = False


@dataclass(frozen=True)
class EnfantAidant30500:
    reference: str = ""
    nom: str = ""
    naissance: str = ""
    profil: AidantNaturelEnfantMoins18Federal2025 = AidantNaturelEnfantMoins18Federal2025()


def aucun_aidant_naturel_enfant_moins18_federal_2025(
) -> AidantNaturelEnfantMoins18Federal2025:
    return AidantNaturelEnfantMoins18Federal2025()


def valider_aidant_naturel_enfant_moins18_federal_2025(
    profil: AidantNaturelEnfantMoins18Federal2025,
) -> AidantNaturelEnfantMoins18Federal2025:
    if type(profil.enfants_detailles) is not tuple or type(profil.identites_distinctes_confirmees) is not bool:
        raise ValueError("Liste d'enfants 30500 ou confirmation d'identité invalide.")
    if profil.enfants_detailles:
        from datetime import date
        for champ in fields(profil):
            if type(getattr(profil, champ.name)) is not type(champ.default):
                raise ValueError("Type invalide dans l'ensemble 30500 : " + champ.name)
        attendu = AidantNaturelEnfantMoins18Federal2025(reclamer_montant=True,
            valide_par_comptable=True, identites_distinctes_confirmees=True, enfants_detailles=profil.enfants_detailles)
        if profil != attendu:
            raise ValueError("L'ensemble 30500 exige validation, identités distinctes et aucun fait individuel concurrent.")
        references, identites = set(), set()
        for enfant in profil.enfants_detailles:
            if type(enfant) is not EnfantAidant30500:
                raise ValueError("Fiche enfant 30500 invalide.")
            for nom in ("reference", "nom", "naissance"):
                if type(getattr(enfant, nom)) is not str or not getattr(enfant, nom).strip():
                    raise ValueError("Référence, nom et naissance de chaque enfant 30500 obligatoires.")
            try:
                naissance = date.fromisoformat(enfant.naissance)
            except ValueError as erreur:
                raise ValueError("Naissance enfant 30500 invalide : AAAA-MM-JJ attendu.") from erreur
            if naissance.isoformat() != enfant.naissance or not date(2008, 1, 1) <= naissance <= date(2025, 12, 31):
                raise ValueError("Chaque enfant doit être né et avoir moins de 18 ans à la fin de 2025.")
            reference = " ".join(enfant.reference.casefold().split())
            identite = (" ".join(enfant.nom.casefold().split()), naissance)
            if reference in references or identite in identites:
                raise ValueError("Enfant 30500 en double : référence ou identité déjà présente.")
            references.add(reference)
            identites.add(identite)
            individuel = enfant.profil
            if type(individuel) is not AidantNaturelEnfantMoins18Federal2025 or individuel.enfants_detailles:
                raise ValueError("Les listes d'enfants 30500 imbriquées sont interdites.")
            for champ in fields(individuel):
                if type(getattr(individuel, champ.name)) is not type(champ.default):
                    raise ValueError("Type invalide dans une fiche enfant 30500 : " + champ.name)
            if not individuel.reclamer_montant or individuel.enfant_reclame_30400:
                raise ValueError("La liste 5Y exige des enfants avec deux parents toute l'année; combinaison 30400 distincte hors de ce mode.")
            valider_aidant_naturel_enfant_moins18_federal_2025(individuel)
        return profil
    if profil.identites_distinctes_confirmees:
        raise ValueError("Confirmation d'identités sans liste d'enfants 30500.")
    if type(profil.enfant_reclame_30400) is not bool or not isinstance(profil.reference_enfant, str):
        raise ValueError("Profil combiné 30400/30500 invalide.")
    if profil.enfant_reclame_30400:
        for champ in fields(profil):
            v = getattr(profil, champ.name)
            if champ.type is bool and type(v) is not bool:
                raise ValueError("Confirmation 30400/30500 non booléenne : " + champ.name)
            if champ.type is str and not isinstance(v, str):
                raise ValueError("Texte 30400/30500 invalide : " + champ.name)
            if champ.type is Decimal:
                from .tax_federal_top_up_2025 import montant_decimal_2025
                if montant_decimal_2025(v, champ.name) != v:
                    raise ValueError("Montant 30400/30500 à exprimer en cents.")
        if not profil.reclamer_montant or not profil.reference_enfant.strip():
            raise ValueError("Profil combiné 30400/30500 : réclamation et référence enfant obligatoires.")
        if profil.enfant_avec_deux_parents_toute_annee:
            raise ValueError("Le profil 30400/30500 exige un parent sans conjoint; résidence avec les deux parents contradictoire.")
    elif profil.reference_enfant:
        raise ValueError("Référence enfant 30500 sans activation du profil combiné.")
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
            profil.enfant_avec_deux_parents_toute_annee or profil.enfant_reclame_30400,
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
    return len(profil.enfants_detailles) if profil.enfants_detailles else int(profil.reclamer_montant)


def montant_ligne_30500_2025(
    profil: AidantNaturelEnfantMoins18Federal2025,
) -> Decimal:
    valider_aidant_naturel_enfant_moins18_federal_2025(profil)

    if not profil.reclamer_montant:
        return ZERO

    return MONTANT_AIDANT_ENFANT_MOINS_18_2025 * nombre_enfants_ligne_30499_2025(profil)


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


def verifier_combinaison_30400_30500_2025(personne, aidant):
    """Même enfant; 2687 à 30500 uniquement, ARC 30500 et annexe 5."""
    valider_aidant_naturel_enfant_moins18_federal_2025(aidant)
    from .tax_federal_eligible_dependant_2025 import valider_montant_personne_charge_admissible_federal_2025
    valider_montant_personne_charge_admissible_federal_2025(personne)
    if personne.enfant_infirmite_ligne30500 or aidant.enfant_reclame_30400:
        if not (personne.enfant_infirmite_ligne30500 and aidant.enfant_reclame_30400):
            raise ValueError("Les deux profils 30400/30500 du même enfant doivent être présents.")
        normaliser = lambda s: " ".join(s.split()).casefold()
        if normaliser(personne.reference_enfant) != normaliser(aidant.reference_enfant):
            raise ValueError("Références de l'enfant divergentes entre 30400 et 30500.")
    elif personne.reclamer_montant and aidant.reclamer_montant:
        raise ValueError("Combinaison 30400/30500 : utiliser le profil explicite du même enfant.")


def details_enfants_30500_2025(profil):
    valider_aidant_naturel_enfant_moins18_federal_2025(profil)
    return tuple(f"{e.reference} — {e.nom}, naissance {e.naissance} : 2687,00 $. "
        f"Source : {e.profil.source_enfant}. Deux parents toute l'année; attribution unique, "
        "infirmité, aide accrue, preuve médicale et validation comptable confirmées."
        for e in profil.enfants_detailles)


def verifier_attribution_enfants_conjoints_30500_2025(profil, resultat_conjoint):
    """5AB : deux demandes 30500 doivent viser des enfants identifiés distincts."""
    valider_aidant_naturel_enfant_moins18_federal_2025(profil)
    if not profil.reclamer_montant or not resultat_conjoint.enfant_30500:
        return
    if not profil.enfants_detailles or not resultat_conjoint.enfants_30500:
        raise ValueError("Deux montants 30500 : utiliser les fiches identifiées des enfants dans les deux dossiers.")
    normaliser = lambda s: " ".join(s.casefold().split())
    references = {normaliser(ref) for ref, nom, naissance in resultat_conjoint.enfants_30500}
    identites = {(normaliser(nom), naissance) for ref, nom, naissance in resultat_conjoint.enfants_30500}
    for enfant in profil.enfants_detailles:
        if normaliser(enfant.reference) in references or (normaliser(enfant.nom), enfant.naissance) in identites:
            raise ValueError("Même enfant 30500 réclamé dans les deux dossiers du couple : attribution unique obligatoire.")
