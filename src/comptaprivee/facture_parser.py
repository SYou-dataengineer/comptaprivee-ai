"""Extraction structurée des champs d'une facture."""

import re
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class DonneesFacture:
    """Données structurées extraites d'une facture."""

    numero: str | None
    date: str | None
    fournisseur: str | None
    client: str | None
    sous_total: Decimal | None
    tps: Decimal | None
    tvq: Decimal | None
    total: Decimal | None


def extraire_texte_ligne(libelle: str, texte: str) -> str | None:
    """Extrait la valeur textuelle située après un libellé."""
    motif = rf"^\s*{re.escape(libelle)}\s*:\s*(.+?)\s*$"
    resultat = re.search(motif, texte, flags=re.IGNORECASE | re.MULTILINE)

    if resultat is None:
        return None

    return resultat.group(1).strip()


def extraire_montant(libelle: str, texte: str) -> Decimal | None:
    """Extrait un montant et le convertit en nombre décimal."""
    motif = (
    rf"^\s*{re.escape(libelle)}\s*:\s*"
    r"([\d\s]+(?:[.,]\d{1,2})?)"
    r"(?:\s*CAD)?\s*$"
)
    resultat = re.search(motif, texte, flags=re.IGNORECASE | re.MULTILINE)

    if resultat is None:
        return None

    valeur = resultat.group(1).replace(" ", "").replace(",", ".")
    return Decimal(valeur)


def extraire_donnees_facture(texte: str) -> DonneesFacture:
    """Extrait les principaux champs comptables d'une facture."""
    return DonneesFacture(
        numero=extraire_texte_ligne("Numero", texte),
        date=extraire_texte_ligne("Date", texte),
        fournisseur=extraire_texte_ligne("Fournisseur", texte),
        client=extraire_texte_ligne("Client", texte),
        sous_total=extraire_montant("Sous-total", texte),
        tps=extraire_montant("TPS", texte),
        tvq=extraire_montant("TVQ", texte),
        total=extraire_montant("Total", texte),
    )