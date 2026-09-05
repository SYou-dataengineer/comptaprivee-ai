"""Verrous de conformité pour le futur Agent fiscal.

Cette première version ne transmet aucune déclaration.
Les fonctions de transmission restent désactivées par défaut.
"""

from dataclasses import dataclass


MODE_LOCAL_PAR_DEFAUT = True
VALIDATION_HUMAINE_OBLIGATOIRE = True
TRANSMISSION_ARC_ACTIVE = False
TRANSMISSION_REVENU_QUEBEC_ACTIVE = False
IA_EXTERNE_AUTORISEE = False


@dataclass(frozen=True)
class EtatConformiteFiscale:
    mode_local: bool = MODE_LOCAL_PAR_DEFAUT
    validation_humaine_obligatoire: bool = VALIDATION_HUMAINE_OBLIGATOIRE
    transmission_arc_active: bool = TRANSMISSION_ARC_ACTIVE
    transmission_revenu_quebec_active: bool = (
        TRANSMISSION_REVENU_QUEBEC_ACTIVE
    )
    ia_externe_autorisee: bool = IA_EXTERNE_AUTORISEE


def etat_conformite_initial() -> EtatConformiteFiscale:
    """Retourne l'état de conformité sécurisé par défaut."""
    return EtatConformiteFiscale()


def transmission_autorisee(
    destination: str,
    *,
    validation_humaine_effectuee: bool = False,
) -> tuple[bool, str]:
    """Indique si une transmission fiscale est autorisée.

    Phase 0 : aucune transmission n'est activée.
    La validation humaine reste obligatoire dans tous les cas.
    """
    cible = destination.strip().casefold()

    if cible not in {"arc", "revenu québec", "revenu quebec", "rq"}:
        raise ValueError(
            "Destination fiscale inconnue. Utilisez ARC ou Revenu Québec."
        )

    if not validation_humaine_effectuee:
        return (
            False,
            "Validation humaine obligatoire avant toute transmission.",
        )

    if cible == "arc":
        if not TRANSMISSION_ARC_ACTIVE:
            return (
                False,
                "Transmission ARC désactivée tant que les exigences "
                "EFILE/certification ne sont pas satisfaites.",
            )

    if not TRANSMISSION_REVENU_QUEBEC_ACTIVE:
        return (
            False,
            "Transmission Revenu Québec désactivée tant que les exigences "
            "d'autorisation/certification ne sont pas satisfaites.",
        )

    return True, "Transmission autorisée."


def traitement_ia_externe_autorise() -> bool:
    """Phase 0 : les données fiscales ne sont pas envoyées à une IA externe."""
    return IA_EXTERNE_AUTORISEE
