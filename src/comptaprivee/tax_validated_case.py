"""Dossier fiscal verrouillé après validation humaine complète.

Ce module construit un instantané immuable des valeurs validées.
Il ne calcule aucun impôt et ne transmet aucune déclaration.
"""

from dataclasses import dataclass
from pathlib import Path

from .tax_case import DossierFiscal
from .tax_field_extractor import DonneeFiscaleExtraite
from .tax_field_validation import (
    DonneeFiscaleValidee,
    cle_donnee_fiscale,
    toutes_donnees_sont_validees,
)


STATUT_DOSSIER_VALIDE = "Validé — prêt pour le moteur fiscal"


@dataclass(frozen=True)
class DossierFiscalValide:
    client: str
    annee_fiscale: int
    province: str
    documents: tuple[Path, ...]
    donnees_validees: tuple[DonneeFiscaleValidee, ...]
    statut: str = STATUT_DOSSIER_VALIDE


def construire_dossier_fiscal_valide(
    dossier: DossierFiscal,
    donnees_extraites: (
        tuple[DonneeFiscaleExtraite, ...]
        | list[DonneeFiscaleExtraite]
    ),
    validations: dict[
        tuple[str, str, str],
        DonneeFiscaleValidee,
    ],
) -> DossierFiscalValide:
    """Construit un dossier fiscal uniquement après validation complète."""
    donnees = tuple(donnees_extraites)

    if not donnees:
        raise ValueError(
            "Aucune donnée fiscale extraite à verrouiller."
        )

    cles = [
        cle_donnee_fiscale(donnee)
        for donnee in donnees
    ]

    if len(set(cles)) != len(cles):
        raise ValueError(
            "Des données fiscales extraites sont dupliquées."
        )

    if not toutes_donnees_sont_validees(
        list(donnees),
        validations,
    ):
        raise ValueError(
            "Toutes les données fiscales doivent être validées "
            "par le comptable avant de préparer le dossier fiscal."
        )

    valeurs_validees: list[DonneeFiscaleValidee] = []

    for donnee, cle in zip(donnees, cles):
        validation = validations[cle]

        if (
            validation.document != donnee.document
            or validation.type_document != donnee.type_document
            or validation.case != donnee.case
        ):
            raise ValueError(
                "Une validation fiscale ne correspond pas "
                "à sa donnée source."
            )

        valeurs_validees.append(validation)

    return DossierFiscalValide(
        client=dossier.client,
        annee_fiscale=dossier.annee_fiscale,
        province=dossier.province,
        documents=dossier.documents,
        donnees_validees=tuple(valeurs_validees),
    )
