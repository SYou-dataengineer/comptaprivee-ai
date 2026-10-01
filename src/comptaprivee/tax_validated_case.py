"""Dossier fiscal verrouillé après validation humaine complète.

Ce module construit un instantané immuable des valeurs validées.
Il ne calcule aucun impôt et ne transmet aucune déclaration.
"""

from dataclasses import dataclass, field
from uuid import uuid4
from .tax_minimum_preparation_2025 import ProfilImr2025
from .tax_foreign_property_2025 import InventaireEtranger2025
from .tax_final_return_2025 import Deces2025
from pathlib import Path

from .tax_loss_ledger_2025 import RegistrePertes2025
from .tax_case import DossierFiscal
from .tax_rental_income_2025 import BienLocatif2025
from .tax_self_employment_2025 import Entreprise2025
from .tax_self_employment_contributions_2025 import ProfilCotisationsAutonomes2025
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
    case_id: str = field(default_factory=lambda: str(uuid4()), compare=False, kw_only=True)
    statut: str = STATUT_DOSSIER_VALIDE
    entreprises: tuple[Entreprise2025, ...] = ()
    profil_cotisations_autonomes: ProfilCotisationsAutonomes2025 = ProfilCotisationsAutonomes2025()
    biens_locatifs: tuple[BienLocatif2025, ...] = ()
    registre_pertes: RegistrePertes2025 = RegistrePertes2025()
    deces: Deces2025 | None = None
    imr: ProfilImr2025 | None = None
    biens_etrangers: InventaireEtranger2025 | None = None


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
        case_id=dossier.case_id,
        client=dossier.client,
        annee_fiscale=dossier.annee_fiscale,
        province=dossier.province,
        documents=dossier.documents,
        donnees_validees=tuple(valeurs_validees),
    )
