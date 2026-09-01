"""Calculs locaux pour le tableau de bord comptable."""

from collections import defaultdict
from dataclasses import dataclass
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
