"""Normalisation prudente des montants issus de l'OCR."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation


TAUX_TPS = Decimal("0.05")
TAUX_TVQ = Decimal("0.09975")
TOLERANCE_TAXE = Decimal("0.03")


def _decimal(valeur: str) -> Decimal | None:
    """Convertit une chaîne monétaire OCR en Decimal."""
    nettoyee = (
        valeur.strip()
        .replace(" ", "")
        .replace(",", ".")
    )

    try:
        return Decimal(nettoyee)
    except InvalidOperation:
        return None


def _trouver_montant(
    libelle: str,
    texte: str,
) -> Decimal | None:
    """Trouve un montant déjà correctement séparé."""
    motif = (
        rf"(?im)^\s*{re.escape(libelle)}\s*:\s*"
        r"(\d[\d\s]*(?:[.,]\d{1,2})?)"
        r"\s*(?:CAD|\$)?\s*$"
    )
    resultat = re.search(motif, texte)

    if resultat is None:
        return None

    return _decimal(resultat.group(1))


def _corriger_taxe_sans_separateur(
    texte: str,
    libelle: str,
    sous_total: Decimal | None,
    taux: Decimal,
) -> str:
    """Corrige une taxe OCR sans point seulement si la cohérence est forte."""
    if sous_total is None:
        return texte

    motif = re.compile(
        rf"(?im)^(\s*{re.escape(libelle)}\s*:\s*)"
        r"(\d{3,6})"
        r"(\s*(?:CAD|\$)?\s*)$"
    )

    def remplacer(match: re.Match[str]) -> str:
        brut = match.group(2)

        # Ex. 2494 -> 24.94. On ne corrige jamais automatiquement
        # une valeur déjà dotée d'un séparateur décimal.
        candidat = Decimal(brut) / Decimal("100")
        attendu = (
            sous_total * taux
        ).quantize(Decimal("0.01"))

        if abs(candidat - attendu) > TOLERANCE_TAXE:
            return match.group(0)

        return (
            f"{match.group(1)}"
            f"{candidat:.2f}"
            f"{match.group(3)}"
        )

    return motif.sub(remplacer, texte)


def normaliser_montants_ocr(texte: str) -> str:
    """Corrige seulement les erreurs OCR monétaires vérifiables.

    Exemple sûr :
    Sous-total: 250.00 CAD
    TVQ: 2494CAD
    devient TVQ: 24.94CAD car 24.94 correspond à 9,975 % de 250.

    Une valeur ambiguë qui ne correspond pas au calcul attendu reste intacte.
    """
    if not texte:
        return texte

    sous_total = _trouver_montant(
        "Sous-total",
        texte,
    )

    if sous_total is None:
        return texte

    texte = _corriger_taxe_sans_separateur(
        texte,
        "TPS",
        sous_total,
        TAUX_TPS,
    )
    texte = _corriger_taxe_sans_separateur(
        texte,
        "TVQ",
        sous_total,
        TAUX_TVQ,
    )

    return texte
