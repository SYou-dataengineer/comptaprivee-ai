"""Export local des données comptables au format CSV."""

import csv
from decimal import Decimal
from pathlib import Path

from .facture_parser import DonneesFacture


def convertir_montant(montant: Decimal | None) -> str:
    """Convertit un montant en texte pour le fichier CSV."""
    if montant is None:
        return ""

    return f"{montant:.2f}"


def exporter_facture_csv(
    facture: DonneesFacture,
    chemin_sortie: str | Path,
) -> Path:
    """Exporte localement les données d'une facture dans un CSV."""
    chemin = Path(chemin_sortie)

    if chemin.suffix.lower() != ".csv":
        raise ValueError("Le fichier de sortie doit être au format CSV.")

    chemin.parent.mkdir(parents=True, exist_ok=True)

    donnees = {
        "numero": facture.numero or "",
        "date": facture.date or "",
        "fournisseur": facture.fournisseur or "",
        "client": facture.client or "",
        "sous_total": convertir_montant(facture.sous_total),
        "tps": convertir_montant(facture.tps),
        "tvq": convertir_montant(facture.tvq),
        "total": convertir_montant(facture.total),
    }

    with chemin.open("w", newline="", encoding="utf-8-sig") as fichier:
        redacteur = csv.DictWriter(
            fichier,
            fieldnames=list(donnees.keys()),
            delimiter=";",
        )
        redacteur.writeheader()
        redacteur.writerow(donnees)

    return chemin