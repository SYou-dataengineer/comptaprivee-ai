"""Calculs locaux pour le tableau de bord comptable."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from .database import FactureEnregistree


@dataclass(frozen=True)
class ResumeTableauBord:
    """Indicateurs synthétiques calculés à partir des factures."""

    nombre_factures: int
    sous_total: Decimal
    tps: Decimal
    tvq: Decimal
    total: Decimal
    total_par_fournisseur: tuple[tuple[str, Decimal], ...]


def filtrer_factures_periode(
    factures: list[FactureEnregistree],
    date_debut: str | None = None,
    date_fin: str | None = None,
) -> list[FactureEnregistree]:
    """Filtre les factures selon une période ISO AAAA-MM-JJ."""
    debut = (
        date.fromisoformat(date_debut)
        if date_debut
        else None
    )
    fin = (
        date.fromisoformat(date_fin)
        if date_fin
        else None
    )

    if debut and fin and debut > fin:
        raise ValueError(
            "La date de début doit être antérieure "
            "ou égale à la date de fin."
        )

    resultat = []

    for facture in factures:
        if not facture.date:
            continue

        try:
            date_facture = date.fromisoformat(
                facture.date
            )
        except ValueError:
            continue

        if debut and date_facture < debut:
            continue

        if fin and date_facture > fin:
            continue

        resultat.append(facture)

    return resultat


def calculer_resume(
    factures: list[FactureEnregistree],
) -> ResumeTableauBord:
    """Calcule les indicateurs du tableau de bord."""
    sous_total = Decimal("0")
    tps = Decimal("0")
    tvq = Decimal("0")
    total = Decimal("0")
    fournisseurs: dict[str, Decimal] = defaultdict(
        lambda: Decimal("0")
    )

    for facture in factures:
        sous_total += facture.sous_total or Decimal("0")
        tps += facture.tps or Decimal("0")
        tvq += facture.tvq or Decimal("0")
        total += facture.total or Decimal("0")

        fournisseur = (
            facture.fournisseur
            or "Fournisseur non renseigné"
        )
        fournisseurs[fournisseur] += (
            facture.total or Decimal("0")
        )

    classement = tuple(
        sorted(
            fournisseurs.items(),
            key=lambda element: element[1],
            reverse=True,
        )
    )

    return ResumeTableauBord(
        nombre_factures=len(factures),
        sous_total=sous_total,
        tps=tps,
        tvq=tvq,
        total=total,
        total_par_fournisseur=classement,
    )

def filtrer_factures_fournisseur(
    factures: list[FactureEnregistree],
    fournisseur: str | None = None,
) -> list[FactureEnregistree]:
    """Filtre les factures selon le fournisseur choisi."""
    if not fournisseur:
        return list(factures)

    recherche = fournisseur.strip().casefold()

    if not recherche:
        return list(factures)

    return [
        facture
        for facture in factures
        if (facture.fournisseur or "").strip().casefold()
        == recherche
    ]

def preparer_totaux_fournisseurs_graphique(
    resume: ResumeTableauBord,
    limite: int = 8,
) -> tuple[tuple[str, Decimal], ...]:
    """Prépare les principaux fournisseurs pour un graphique."""
    if limite <= 0:
        raise ValueError(
            "La limite du graphique doit être supérieure à zéro."
        )

    return resume.total_par_fournisseur[:limite]

def calculer_totaux_mensuels(
    factures: list[FactureEnregistree],
) -> tuple[tuple[str, Decimal], ...]:
    """Regroupe les totaux de factures par mois AAAA-MM."""
    totaux: dict[str, Decimal] = defaultdict(
        lambda: Decimal("0")
    )

    for facture in factures:
        if not facture.date:
            continue

        try:
            date_facture = date.fromisoformat(
                facture.date
            )
        except ValueError:
            continue

        cle_mois = date_facture.strftime("%Y-%m")
        totaux[cle_mois] += (
            facture.total or Decimal("0")
        )

    return tuple(
        sorted(
            totaux.items(),
            key=lambda element: element[0],
        )
    )

def calculer_taxes_mensuelles(
    factures: list[FactureEnregistree],
) -> tuple[tuple[str, Decimal, Decimal], ...]:
    """Regroupe la TPS et la TVQ par mois AAAA-MM."""
    taxes: dict[str, list[Decimal]] = defaultdict(
        lambda: [Decimal("0"), Decimal("0")]
    )

    for facture in factures:
        if not facture.date:
            continue

        try:
            date_facture = date.fromisoformat(
                facture.date
            )
        except ValueError:
            continue

        cle_mois = date_facture.strftime("%Y-%m")
        taxes[cle_mois][0] += facture.tps or Decimal("0")
        taxes[cle_mois][1] += facture.tvq or Decimal("0")

    return tuple(
        (
            mois,
            montants[0],
            montants[1],
        )
        for mois, montants in sorted(
            taxes.items(),
            key=lambda element: element[0],
        )
    )

