"""Validation prudente des tableaux comptables issus de l'OCR.

Ce module ne devine jamais une valeur. Il normalise uniquement les
transformations sûres (ex. ``1200 00`` -> ``1200.00``) et signale les lignes
dont les montants sont incohérents.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import re


@dataclass(frozen=True)
class AnomalieOCR:
    numero_ligne: int
    type_anomalie: str
    message: str


def normaliser_montant_ocr(valeur: str) -> str:
    """Normalise uniquement les séparateurs monétaires évidents.

    Exemples sûrs :
    - ``1200 00`` -> ``1200.00``
    - ``119,70`` -> ``119.70``
    - ``1 200.00`` -> ``1200.00``

    Les caractères ambigus (lettres/chiffres mal reconnus) ne sont jamais
    corrigés automatiquement.
    """
    texte = (valeur or "").strip()

    if not texte:
        return texte

    # Espace de milliers suivi d'un séparateur décimal explicite.
    if re.fullmatch(r"\d{1,3}(?: \d{3})+[.,]\d{2}", texte):
        return texte.replace(" ", "").replace(",", ".")

    # Cas OCR fréquent : le point décimal devient un espace.
    match = re.fullmatch(r"([+-]?\d+)\s+(\d{2})", texte)
    if match:
        return f"{match.group(1)}.{match.group(2)}"

    # Virgule décimale -> point.
    if re.fullmatch(r"[+-]?\d+,\d{2}", texte):
        return texte.replace(",", ".")

    return texte


def _decimal(valeur: str) -> Decimal | None:
    texte = normaliser_montant_ocr(valeur)

    try:
        return Decimal(texte)
    except (InvalidOperation, ValueError):
        return None


def normaliser_tableau_comptable(
    tableau: list[list[str]],
) -> list[list[str]]:
    """Normalise les colonnes monétaires d'un tableau comptable reconnu."""
    if not tableau:
        return tableau

    entete = [cellule.strip().lower() for cellule in tableau[0]]

    index_monetaires = []
    for nom in ("sous-total", "subtotal", "tps", "tvq", "total"):
        if nom in entete:
            index_monetaires.append(entete.index(nom))

    if not index_monetaires:
        return [list(ligne) for ligne in tableau]

    resultat = [list(tableau[0])]

    for ligne in tableau[1:]:
        copie = list(ligne)

        for index in index_monetaires:
            if index < len(copie):
                copie[index] = normaliser_montant_ocr(copie[index])

        resultat.append(copie)

    return resultat


def detecter_anomalies_comptables(
    tableau: list[list[str]],
    *,
    tolerance: Decimal = Decimal("0.03"),
) -> list[AnomalieOCR]:
    """Signale les lignes dont sous-total + TPS + TVQ != total.

    Aucune correction n'est appliquée : l'objectif est de demander une
    validation humaine plutôt que d'inventer un montant.
    """
    if len(tableau) < 2:
        return []

    entete = [cellule.strip().lower() for cellule in tableau[0]]

    noms = {
        "sous_total": ("sous-total", "subtotal"),
        "tps": ("tps",),
        "tvq": ("tvq",),
        "total": ("total",),
    }

    index: dict[str, int] = {}

    for cle, variantes in noms.items():
        for variante in variantes:
            if variante in entete:
                index[cle] = entete.index(variante)
                break

    if set(index) != {"sous_total", "tps", "tvq", "total"}:
        return []

    anomalies: list[AnomalieOCR] = []

    for numero_ligne, ligne in enumerate(tableau[1:], start=2):
        try:
            sous_total = _decimal(ligne[index["sous_total"]])
            tps = _decimal(ligne[index["tps"]])
            tvq = _decimal(ligne[index["tvq"]])
            total = _decimal(ligne[index["total"]])
        except IndexError:
            anomalies.append(
                AnomalieOCR(
                    numero_ligne=numero_ligne,
                    type_anomalie="colonnes_manquantes",
                    message="La ligne OCR ne contient pas toutes les colonnes attendues.",
                )
            )
            continue

        if None in (sous_total, tps, tvq, total):
            anomalies.append(
                AnomalieOCR(
                    numero_ligne=numero_ligne,
                    type_anomalie="montant_illisible",
                    message="Au moins un montant OCR n'est pas interprétable de façon sûre.",
                )
            )
            continue

        calcule = sous_total + tps + tvq
        ecart = abs(calcule - total)

        if ecart > tolerance:
            anomalies.append(
                AnomalieOCR(
                    numero_ligne=numero_ligne,
                    type_anomalie="total_incoherent",
                    message=(
                        f"Total OCR incohérent : {sous_total} + {tps} + "
                        f"{tvq} = {calcule}, mais le total lu est {total}."
                    ),
                )
            )

    return anomalies
