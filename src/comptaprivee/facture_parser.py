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


def _extraire_premier_libelle(libelles: tuple[str, ...], texte: str) -> str | None:
    for libelle in libelles:
        valeur = extraire_texte_ligne(libelle, texte)
        if valeur:
            return valeur
    return None


def _parser_bloc_facture(texte: str) -> DonneesFacture:
    return DonneesFacture(
        numero=_extraire_premier_libelle(
            ("Numero", "Numéro", "N° facture", "No facture", "Facture"),
            texte,
        ),
        date=extraire_texte_ligne("Date", texte),
        fournisseur=extraire_texte_ligne("Fournisseur", texte),
        client=extraire_texte_ligne("Client", texte),
        sous_total=extraire_montant("Sous-total", texte),
        tps=extraire_montant("TPS", texte),
        tvq=extraire_montant("TVQ", texte),
        total=extraire_montant("Total", texte),
    )


def _score_facture(facture: DonneesFacture) -> int:
    valeurs = (
        facture.numero,
        facture.date,
        facture.fournisseur,
        facture.client,
        facture.sous_total,
        facture.tps,
        facture.tvq,
        facture.total,
    )
    score = sum(v is not None for v in valeurs)

    if (
        facture.sous_total is not None
        and facture.tps is not None
        and facture.tvq is not None
        and facture.total is not None
    ):
        calcule = facture.sous_total + facture.tps + facture.tvq
        if abs(calcule - facture.total) <= Decimal("0.02"):
            score += 5

    return score


def extraire_donnees_facture(texte: str) -> DonneesFacture:
    blocs = [
        bloc.strip()
        for bloc in texte.split("\n\n--- Page suivante ---\n\n")
        if bloc.strip()
    ]

    if not blocs:
        return _parser_bloc_facture("")

    if len(blocs) == 1:
        return _parser_bloc_facture(blocs[0])

    factures = [_parser_bloc_facture(bloc) for bloc in blocs]
    return max(factures, key=_score_facture)
