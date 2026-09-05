"""Validation humaine des données fiscales extraites.

Cette couche sépare explicitement l'extraction automatique de la validation
comptable. Aucune donnée non validée ne doit alimenter un futur calcul fiscal.
"""

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from .tax_field_extractor import (
    DonneeFiscaleExtraite,
    convertir_montant_fiscal,
)


STATUT_VALIDE = "Validé par le comptable"
STATUT_CORRIGE_VALIDE = "Corrigé et validé par le comptable"


@dataclass(frozen=True)
class DonneeFiscaleValidee:
    document: Path
    type_document: str
    case: str
    libelle: str
    valeur_extraite: Decimal
    valeur_validee: Decimal
    corrigee: bool
    statut: str


def cle_donnee_fiscale(
    donnee: DonneeFiscaleExtraite,
) -> tuple[str, str, str]:
    """Construit une clé locale stable pour une donnée fiscale."""
    return (
        str(donnee.document),
        donnee.type_document,
        donnee.case,
    )


def valider_donnee_fiscale(
    donnee: DonneeFiscaleExtraite,
) -> DonneeFiscaleValidee:
    """Valide la valeur extraite sans modification."""
    return DonneeFiscaleValidee(
        document=donnee.document,
        type_document=donnee.type_document,
        case=donnee.case,
        libelle=donnee.libelle,
        valeur_extraite=donnee.valeur,
        valeur_validee=donnee.valeur,
        corrigee=False,
        statut=STATUT_VALIDE,
    )


def corriger_et_valider_donnee_fiscale(
    donnee: DonneeFiscaleExtraite,
    nouvelle_valeur: str | Decimal,
) -> DonneeFiscaleValidee:
    """Corrige une valeur puis la marque comme validée par le comptable."""
    if isinstance(nouvelle_valeur, Decimal):
        valeur = nouvelle_valeur
    else:
        valeur = convertir_montant_fiscal(nouvelle_valeur)

    if valeur < Decimal("0"):
        raise ValueError(
            "Une valeur fiscale validée ne peut pas être négative "
            "dans cette première phase."
        )

    corrigee = valeur != donnee.valeur

    return DonneeFiscaleValidee(
        document=donnee.document,
        type_document=donnee.type_document,
        case=donnee.case,
        libelle=donnee.libelle,
        valeur_extraite=donnee.valeur,
        valeur_validee=valeur,
        corrigee=corrigee,
        statut=(
            STATUT_CORRIGE_VALIDE
            if corrigee
            else STATUT_VALIDE
        ),
    )


def toutes_donnees_sont_validees(
    donnees: tuple[DonneeFiscaleExtraite, ...] | list[DonneeFiscaleExtraite],
    validations: dict[
        tuple[str, str, str],
        DonneeFiscaleValidee,
    ],
) -> bool:
    """Retourne True seulement si chaque donnée extraite est validée."""
    if not donnees:
        return False

    return all(
        cle_donnee_fiscale(donnee) in validations
        for donnee in donnees
    )
