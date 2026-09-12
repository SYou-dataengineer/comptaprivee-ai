"""Cotisation au régime d'assurance médicaments du Québec - 2025.

Profil volontairement limité de ComptaPrivée.

Cette première version couvre uniquement :
- une personne sans conjoint au 31 décembre 2025;
- une couverture collective de base pendant toute l'année (cotisation = 0);
- ou une couverture par le régime public pendant toute l'année, sans mois
  d'exemption;
- les cas de revenu assez faible pour l'exemption de la case 449, code 32;
- les cas où la ligne 48 de l'annexe K dépasse 8 181 $, donnant la
  cotisation maximale de 755 $.

Les situations intermédiaires de l'annexe K sont volontairement refusées
tant que leur calcul progressif complet n'est pas implémenté.

Références visées :
- Revenu Québec, ligne 447;
- annexe K;
- case 449, notamment codes 14, 16 et 32.
"""

from dataclasses import dataclass
from decimal import Decimal

from .tax_rules_2025 import arrondir_cent


ZERO = Decimal("0")
COTISATION_MAX_RAMQ_2025 = Decimal("755.00")
SEUIL_REVENU_SANS_CONJOINT_2025 = Decimal("19890")
SEUIL_LIGNE_48_MAX_SANS_CONJOINT_2025 = Decimal("8181")

COUVERTURE_COLLECTIVE = "collectif"
COUVERTURE_PUBLIQUE = "public"
CODES_COLLECTIFS_CASE_449 = {"14", "16"}


@dataclass(frozen=True)
class AssuranceMedicamentsQuebec2025:
    """Données validées pour la ligne 447 / annexe K."""

    type_couverture: str = ""
    couverture_toute_annee: bool = False
    sans_conjoint_31_decembre_2025: bool = False

    revenu_ligne_275: Decimal = ZERO
    revenu_ligne_48_annexe_k: Decimal = ZERO

    aucun_mois_exempt: bool = False
    carte_ramq_valide_2025: bool = False

    situation_validee_par_comptable: bool = False
    aucun_cas_particulier: bool = False
    source: str = ""

    code_case_449: str = ""


def aucune_assurance_medicaments_2025() -> AssuranceMedicamentsQuebec2025:
    """Retourne un profil vide qui ne modifie pas le calcul fiscal."""
    return AssuranceMedicamentsQuebec2025()


def _type_normalise(valeur: str) -> str:
    return valeur.strip().lower()


def valider_assurance_medicaments_2025(
    assurance: AssuranceMedicamentsQuebec2025,
) -> AssuranceMedicamentsQuebec2025:
    """Valide le profil simple avant tout calcul."""
    if assurance.revenu_ligne_275 < ZERO:
        raise ValueError(
            "Le revenu de la ligne 275 ne peut pas être négatif."
        )

    if assurance.revenu_ligne_48_annexe_k < ZERO:
        raise ValueError(
            "La ligne 48 de l'annexe K ne peut pas être négative."
        )

    type_couverture = _type_normalise(assurance.type_couverture)

    if not type_couverture:
        if (
            assurance.couverture_toute_annee
            or assurance.sans_conjoint_31_decembre_2025
            or assurance.revenu_ligne_275 != ZERO
            or assurance.revenu_ligne_48_annexe_k != ZERO
            or assurance.aucun_mois_exempt
            or assurance.carte_ramq_valide_2025
            or assurance.situation_validee_par_comptable
            or assurance.aucun_cas_particulier
            or assurance.source.strip()
            or assurance.code_case_449.strip()
        ):
            raise ValueError(
                "Le type de couverture médicaments doit être précisé."
            )
        return assurance

    if type_couverture not in {
        COUVERTURE_COLLECTIVE,
        COUVERTURE_PUBLIQUE,
    }:
        raise ValueError(
            "Le type de couverture doit être 'collectif' ou 'public'."
        )

    if not assurance.situation_validee_par_comptable:
        raise ValueError(
            "La situation d'assurance médicaments doit être validée "
            "par le comptable."
        )

    if not assurance.couverture_toute_annee:
        raise ValueError(
            "Cette version accepte uniquement une couverture pendant "
            "toute l'année 2025."
        )

    if not assurance.sans_conjoint_31_decembre_2025:
        raise ValueError(
            "Cette version accepte uniquement une personne sans conjoint "
            "au 31 décembre 2025."
        )

    if not assurance.aucun_cas_particulier:
        raise ValueError(
            "Les cas particuliers de l'annexe K doivent être exclus "
            "ou traités manuellement."
        )

    if not assurance.source.strip():
        raise ValueError(
            "La source justificative de l'assurance médicaments "
            "est obligatoire."
        )

    if type_couverture == COUVERTURE_COLLECTIVE:
        code = assurance.code_case_449.strip()

        if code not in CODES_COLLECTIFS_CASE_449:
            raise ValueError(
                "Pour une couverture collective toute l'année, cette "
                "version accepte uniquement les codes 14 ou 16 "
                "de la case 449."
            )

        if assurance.revenu_ligne_48_annexe_k != ZERO:
            raise ValueError(
                "La ligne 48 de l'annexe K doit rester à zéro pour le "
                "profil collectif de cette version."
            )

        return assurance

    if not assurance.carte_ramq_valide_2025:
        raise ValueError(
            "La carte d'assurance maladie RAMQ 2025 doit être confirmée."
        )

    if not assurance.aucun_mois_exempt:
        raise ValueError(
            "Cette version du régime public accepte uniquement un dossier "
            "sans mois d'exemption à l'annexe K."
        )

    if assurance.code_case_449.strip() not in {"", "32"}:
        raise ValueError(
            "Pour le régime public de ce profil, seule la case 449 "
            "code 32 peut être utilisée lorsque le revenu le permet."
        )

    if assurance.revenu_ligne_275 <= SEUIL_REVENU_SANS_CONJOINT_2025:
        if assurance.revenu_ligne_48_annexe_k != ZERO:
            raise ValueError(
                "Pour un revenu de ligne 275 ne dépassant pas 19 890 $, "
                "la ligne 48 doit rester à zéro dans ce profil."
            )

        if assurance.code_case_449.strip() not in {"", "32"}:
            raise ValueError(
                "Le code attendu à la case 449 est 32."
            )

        return assurance

    if assurance.code_case_449.strip():
        raise ValueError(
            "Le code 32 de la case 449 ne s'applique pas lorsque le "
            "revenu de la ligne 275 dépasse 19 890 $."
        )

    if assurance.revenu_ligne_48_annexe_k <= ZERO:
        raise ValueError(
            "La ligne 48 de l'annexe K est obligatoire lorsque le revenu "
            "de la ligne 275 dépasse 19 890 $."
        )

    if (
        assurance.revenu_ligne_48_annexe_k
        <= SEUIL_LIGNE_48_MAX_SANS_CONJOINT_2025
    ):
        raise ValueError(
            "Le calcul progressif de l'annexe K pour une ligne 48 "
            "entre 0 $ et 8 181 $ n'est pas encore pris en charge."
        )

    return assurance


def cotisation_assurance_medicaments_2025(
    assurance: AssuranceMedicamentsQuebec2025,
) -> Decimal:
    """Calcule la cotisation RAMQ 2025 pour le profil simple supporté."""
    valider_assurance_medicaments_2025(assurance)

    type_couverture = _type_normalise(assurance.type_couverture)

    if not type_couverture:
        return ZERO

    if type_couverture == COUVERTURE_COLLECTIVE:
        return ZERO

    if assurance.revenu_ligne_275 <= SEUIL_REVENU_SANS_CONJOINT_2025:
        return ZERO

    return arrondir_cent(COTISATION_MAX_RAMQ_2025)


def code_exemption_case_449_2025(
    assurance: AssuranceMedicamentsQuebec2025,
) -> str:
    """Retourne le code 449 explicite lorsque le profil en prévoit un."""
    valider_assurance_medicaments_2025(assurance)

    type_couverture = _type_normalise(assurance.type_couverture)

    if not type_couverture:
        return ""

    if type_couverture == COUVERTURE_COLLECTIVE:
        return assurance.code_case_449.strip()

    if assurance.revenu_ligne_275 <= SEUIL_REVENU_SANS_CONJOINT_2025:
        return "32"

    return ""
