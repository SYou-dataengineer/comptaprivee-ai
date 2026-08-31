"""Export local des données comptables au format CSV."""

import csv
from collections.abc import Iterable
from decimal import Decimal
from pathlib import Path

from .facture_parser import DonneesFacture


CHAMPS_CSV = [
    "numero",
    "date",
    "fournisseur",
    "client",
    "sous_total",
    "tps",
    "tvq",
    "total",
]


def convertir_montant(montant: Decimal | None) -> str:
    """Convertit un montant en texte pour le fichier CSV."""
    if montant is None:
        return ""

    return f"{montant:.2f}"


def facture_vers_dictionnaire(
    facture: DonneesFacture,
) -> dict[str, str]:
    """Transforme les données d'une facture en ligne CSV."""
    return {
        "numero": facture.numero or "",
        "date": facture.date or "",
        "fournisseur": facture.fournisseur or "",
        "client": facture.client or "",
        "sous_total": convertir_montant(facture.sous_total),
        "tps": convertir_montant(facture.tps),
        "tvq": convertir_montant(facture.tvq),
        "total": convertir_montant(facture.total),
    }


def exporter_factures_csv(
    factures: Iterable[DonneesFacture],
    chemin_sortie: str | Path,
) -> Path:
    """Exporte plusieurs factures dans un seul fichier CSV."""
    chemin = Path(chemin_sortie)

    if chemin.suffix.lower() != ".csv":
        raise ValueError("Le fichier de sortie doit être au format CSV.")

    lignes = [
        facture_vers_dictionnaire(facture)
        for facture in factures
    ]

    if not lignes:
        raise ValueError("Aucune facture à exporter.")

    chemin.parent.mkdir(parents=True, exist_ok=True)

    with chemin.open("w", newline="", encoding="utf-8-sig") as fichier:
        redacteur = csv.DictWriter(
            fichier,
            fieldnames=CHAMPS_CSV,
            delimiter=";",
        )
        redacteur.writeheader()
        redacteur.writerows(lignes)

    return chemin


def exporter_facture_csv(
    facture: DonneesFacture,
    chemin_sortie: str | Path,
) -> Path:
    """Exporte une seule facture dans un fichier CSV."""
    return exporter_factures_csv(
        [facture],
        chemin_sortie,
    )