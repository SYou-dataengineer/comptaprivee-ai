"""Détection locale des factures potentiellement en double."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .database import (
    CHEMIN_BASE_PAR_DEFAUT,
    FactureEnregistree,
    lister_factures,
)
from .facture_parser import DonneesFacture


class NiveauDoublon(str, Enum):
    """Niveau de confiance d'un doublon détecté."""

    AUCUN = "aucun"
    PROBABLE = "probable"
    CERTAIN = "certain"


@dataclass(frozen=True)
class ResultatDoublon:
    """Résultat d'une vérification de doublon."""

    niveau: NiveauDoublon
    facture_existante: FactureEnregistree | None
    raison: str

    @property
    def est_doublon(self) -> bool:
        return self.niveau is not NiveauDoublon.AUCUN


def _normaliser_texte(valeur: str | None) -> str:
    return " ".join((valeur or "").casefold().split())


def detecter_doublon(
    facture: DonneesFacture,
    chemin_base: str | Path = CHEMIN_BASE_PAR_DEFAUT,
) -> ResultatDoublon:
    """Cherche un doublon certain ou probable dans SQLite local."""
    factures = lister_factures(chemin_base)

    numero = _normaliser_texte(facture.numero)
    fournisseur = _normaliser_texte(facture.fournisseur)

    # Niveau certain : même numéro de facture.
    if numero:
        for existante in factures:
            if _normaliser_texte(existante.numero) == numero:
                return ResultatDoublon(
                    niveau=NiveauDoublon.CERTAIN,
                    facture_existante=existante,
                    raison=(
                        "Une facture avec le même numéro "
                        "est déjà enregistrée."
                    ),
                )

    # Niveau probable : même fournisseur + date + total.
    if fournisseur and facture.date and facture.total is not None:
        for existante in factures:
            if (
                _normaliser_texte(existante.fournisseur)
                == fournisseur
                and existante.date == facture.date
                and existante.total == facture.total
            ):
                return ResultatDoublon(
                    niveau=NiveauDoublon.PROBABLE,
                    facture_existante=existante,
                    raison=(
                        "Même fournisseur, même date et même total "
                        "qu'une facture déjà enregistrée."
                    ),
                )

    return ResultatDoublon(
        niveau=NiveauDoublon.AUCUN,
        facture_existante=None,
        raison="Aucun doublon détecté.",
    )
