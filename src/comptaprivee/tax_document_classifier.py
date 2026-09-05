"""Classification locale des premiers documents fiscaux pris en charge.

Phase 1 : reconnaissance T4 et RL-1 uniquement.
Aucune donnée n'est transmise à un service externe.
"""

from dataclasses import dataclass
from pathlib import Path
import re
import unicodedata


TYPE_T4 = "T4"
TYPE_RL1 = "RL-1"
TYPE_NON_RECONNU = "Non reconnu"
TYPE_A_VERIFIER = "À vérifier"


@dataclass(frozen=True)
class ClassificationDocumentFiscal:
    type_document: str
    confiance: int
    motifs: tuple[str, ...] = ()


def _normaliser(texte: str) -> str:
    valeur = unicodedata.normalize("NFKD", texte)
    valeur = "".join(
        caractere
        for caractere in valeur
        if not unicodedata.combining(caractere)
    )
    return valeur.casefold()


def _score_t4(nom: str, texte: str) -> tuple[int, list[str]]:
    score = 0
    motifs: list[str] = []

    if re.search(r"(^|[^a-z0-9])t4([^a-z0-9]|$)", nom):
        score += 65
        motifs.append("nom de fichier T4")

    regles = (
        ("statement of remuneration paid", 45, "titre officiel T4"),
        ("etat de la remuneration payee", 45, "titre officiel T4"),
        ("employment income", 20, "revenu d'emploi T4"),
        ("income tax deducted", 15, "impôt retenu T4"),
        ("case 14", 12, "case 14"),
        ("box 14", 12, "case 14"),
        ("case 22", 10, "case 22"),
        ("box 22", 10, "case 22"),
    )

    if re.search(r"(^|[^a-z0-9])t4([^a-z0-9]|$)", texte):
        score += 25
        motifs.append("mention T4 dans le document")

    for marqueur, points, motif in regles:
        if marqueur in texte:
            score += points
            motifs.append(motif)

    return min(score, 100), motifs


def _score_rl1(nom: str, texte: str) -> tuple[int, list[str]]:
    score = 0
    motifs: list[str] = []

    if re.search(r"(^|[^a-z0-9])rl[ _-]?1([^a-z0-9]|$)", nom):
        score += 65
        motifs.append("nom de fichier RL-1")

    if "releve 1" in nom:
        score += 65
        motifs.append("nom de fichier Relevé 1")

    regles = (
        ("revenus d'emploi et revenus divers", 45, "titre officiel RL-1"),
        ("revenu quebec", 20, "mention Revenu Québec"),
        ("releve 1", 30, "mention Relevé 1"),
        ("rl-1", 30, "mention RL-1"),
        ("case a", 10, "case A"),
    )

    for marqueur, points, motif in regles:
        if marqueur in texte:
            score += points
            motifs.append(motif)

    return min(score, 100), motifs


def classifier_document_fiscal(
    chemin: str | Path,
    texte: str = "",
) -> ClassificationDocumentFiscal:
    """Classe localement un document comme T4, RL-1 ou non reconnu."""
    chemin = Path(chemin)
    nom = _normaliser(chemin.stem)
    contenu = _normaliser(texte)

    score_t4, motifs_t4 = _score_t4(nom, contenu)
    score_rl1, motifs_rl1 = _score_rl1(nom, contenu)

    meilleur_score = max(score_t4, score_rl1)

    if meilleur_score < 30:
        return ClassificationDocumentFiscal(
            type_document=TYPE_NON_RECONNU,
            confiance=meilleur_score,
            motifs=(),
        )

    if (
        score_t4 >= 30
        and score_rl1 >= 30
        and abs(score_t4 - score_rl1) < 15
    ):
        return ClassificationDocumentFiscal(
            type_document=TYPE_A_VERIFIER,
            confiance=meilleur_score,
            motifs=tuple(motifs_t4 + motifs_rl1),
        )

    if score_t4 > score_rl1:
        return ClassificationDocumentFiscal(
            type_document=TYPE_T4,
            confiance=score_t4,
            motifs=tuple(motifs_t4),
        )

    return ClassificationDocumentFiscal(
        type_document=TYPE_RL1,
        confiance=score_rl1,
        motifs=tuple(motifs_rl1),
    )
