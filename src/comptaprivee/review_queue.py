"""Analyse locale des factures nécessitant une vérification humaine."""

from dataclasses import dataclass
from enum import Enum

from .database import FactureEnregistree
from .facture_parser import DonneesFacture
from .invoice_validator import (
    StatutValidation,
    valider_facture,
)
from .tax_validator import appliquer_validation_fiscale


class NiveauVerification(str, Enum):
    """Niveau de priorité d'une facture à vérifier."""

    AVERTISSEMENT = "avertissement"
    ERREUR = "erreur"


@dataclass(frozen=True)
class ElementAVerifier:
    """Une facture enregistrée qui nécessite une intervention humaine."""

    facture: FactureEnregistree
    niveau: NiveauVerification
    raisons: tuple[str, ...]


def _vers_donnees(
    facture: FactureEnregistree,
) -> DonneesFacture:
    return DonneesFacture(
        numero=facture.numero,
        date=facture.date,
        fournisseur=facture.fournisseur,
        client=facture.client,
        sous_total=facture.sous_total,
        tps=facture.tps,
        tvq=facture.tvq,
        total=facture.total,
    )


def _normaliser(valeur: str | None) -> str:
    return " ".join((valeur or "").casefold().split())


def _doublons_probables(
    factures: list[FactureEnregistree],
) -> dict[int, list[str]]:
    """Repère les factures distinctes avec fournisseur/date/total identiques."""
    raisons: dict[int, list[str]] = {}

    for index, facture in enumerate(factures):
        fournisseur = _normaliser(facture.fournisseur)

        if not fournisseur or not facture.date or facture.total is None:
            continue

        for autre in factures[index + 1:]:
            if (
                _normaliser(autre.fournisseur) == fournisseur
                and autre.date == facture.date
                and autre.total == facture.total
                and autre.identifiant != facture.identifiant
            ):
                message = (
                    "Doublon probable : même fournisseur, "
                    "même date et même total."
                )
                raisons.setdefault(
                    facture.identifiant,
                    [],
                ).append(message)
                raisons.setdefault(
                    autre.identifiant,
                    [],
                ).append(message)

    return raisons


def analyser_factures_a_verifier(
    factures: list[FactureEnregistree],
) -> list[ElementAVerifier]:
    """Retourne uniquement les factures qui nécessitent une vérification."""
    doublons = _doublons_probables(factures)
    resultats: list[ElementAVerifier] = []

    for facture in factures:
        donnees = _vers_donnees(facture)
        validation = appliquer_validation_fiscale(
            donnees,
            valider_facture(donnees),
        )

        raisons = [
            *validation.erreurs,
            *validation.avertissements,
            *doublons.get(facture.identifiant, []),
        ]

        # Évite les doublons de messages en conservant l'ordre.
        raisons_uniques = tuple(dict.fromkeys(raisons))

        if not raisons_uniques:
            continue

        niveau = (
            NiveauVerification.ERREUR
            if (
                validation.statut is StatutValidation.ERREUR
                or validation.erreurs
            )
            else NiveauVerification.AVERTISSEMENT
        )

        resultats.append(
            ElementAVerifier(
                facture=facture,
                niveau=niveau,
                raisons=raisons_uniques,
            )
        )

    return resultats
