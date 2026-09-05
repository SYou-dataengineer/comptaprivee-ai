"""Extraction locale et traçable des premières cases fiscales.

Phase 1 : extraction de champs T4 et RL-1 seulement.
Aucun calcul d'impôt et aucune transmission gouvernementale.
"""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re


STATUT_A_VALIDER = "À valider par le comptable"


@dataclass(frozen=True)
class DonneeFiscaleExtraite:
    document: Path
    type_document: str
    case: str
    libelle: str
    valeur: Decimal
    valeur_brute: str
    statut: str = STATUT_A_VALIDER


REGLES_T4 = (
    ("14", "Revenu d'emploi", (r"\bcase\s*14\b", r"\bbox\s*14\b")),
    ("16", "Cotisations RPC", (r"\bcase\s*16\b", r"\bbox\s*16\b")),
    ("17", "Cotisations RRQ", (r"\bcase\s*17\b", r"\bbox\s*17\b")),
    (
        "17A",
        "Deuxième cotisation supplémentaire au RRQ",
        (r"\bcase\s*17a\b", r"\bbox\s*17a\b"),
    ),
    (
        "18",
        "Cotisations assurance-emploi",
        (r"\bcase\s*18\b", r"\bbox\s*18\b"),
    ),
    (
        "22",
        "Impôt sur le revenu retenu",
        (r"\bcase\s*22\b", r"\bbox\s*22\b"),
    ),
    (
        "24",
        "Gains assurables assurance-emploi",
        (r"\bcase\s*24\b", r"\bbox\s*24\b"),
    ),
    (
        "26",
        "Gains admissibles RPC/RRQ",
        (r"\bcase\s*26\b", r"\bbox\s*26\b"),
    ),
    (
        "55",
        "Cotisations au RQAP",
        (r"\bcase\s*55\b", r"\bbox\s*55\b"),
    ),
    (
        "56",
        "Gains assurables au RQAP",
        (r"\bcase\s*56\b", r"\bbox\s*56\b"),
    ),
)

REGLES_RL1 = (
    (
        "B.A",
        "Cotisation RRQ (base + première supplémentaire)",
        (r"\bcase\s*b\s*\.\s*a\b",),
    ),
    (
        "B.B",
        "Cotisation supplémentaire au RRQ",
        (r"\bcase\s*b\s*\.\s*b\b",),
    ),
    (
        "A",
        "Revenus d'emploi",
        (r"\bcase\s*a\b",),
    ),
    (
        "B",
        "Cotisation RRQ",
        (r"\bcase\s*b\b(?!\s*\.)",),
    ),
    (
        "C",
        "Cotisation à l'assurance-emploi",
        (r"\bcase\s*c\b",),
    ),
    (
        "E",
        "Impôt du Québec retenu",
        (r"\bcase\s*e\b",),
    ),
    (
        "G",
        "Salaire admissible au RRQ",
        (r"\bcase\s*g\b",),
    ),
    (
        "H",
        "Cotisation au RQAP",
        (r"\bcase\s*h\b",),
    ),
    (
        "I",
        "Salaire admissible au RQAP",
        (r"\bcase\s*i\b",),
    ),
)

MONTANT_RE = re.compile(
    r"(?<![\w.])("
    r"(?:\d{1,3}(?:[ \u00a0]\d{3})+(?:[,.]\d{2})?)"
    r"|(?:\d{1,3}(?:,\d{3})+(?:\.\d{2})?)"
    r"|(?:\d{1,3}(?:\.\d{3})+(?:,\d{2})?)"
    r"|(?:\d+\.\d{2})"
    r"|(?:\d+,\d{2})"
    r")\s*\$?"
)


def convertir_montant_fiscal(valeur: str) -> Decimal:
    """Convertit un montant canadien courant en Decimal."""
    texte = valeur.strip().replace("$", "").replace("\u00a0", " ")
    texte = texte.replace(" ", "")

    if "," in texte and "." in texte:
        if texte.rfind(",") > texte.rfind("."):
            texte = texte.replace(".", "").replace(",", ".")
        else:
            texte = texte.replace(",", "")
    elif "," in texte:
        parties = texte.split(",")
        if len(parties[-1]) == 2:
            texte = "".join(parties[:-1]) + "." + parties[-1]
        else:
            texte = texte.replace(",", "")
    elif texte.count(".") > 1:
        parties = texte.split(".")
        if len(parties[-1]) == 2:
            texte = "".join(parties[:-1]) + "." + parties[-1]
        else:
            texte = texte.replace(".", "")

    try:
        return Decimal(texte)
    except InvalidOperation as erreur:
        raise ValueError(
            f"Montant fiscal invalide : {valeur}"
        ) from erreur


def formater_montant_fiscal(valeur: Decimal) -> str:
    """Formate un montant en notation canadienne-française."""
    texte = f"{valeur:,.2f}"
    texte = texte.replace(",", "X").replace(".", ",").replace("X", " ")
    return f"{texte} $"


def _prochaine_case_position(texte: str) -> int | None:
    resultat = re.search(
        r"\b(?:case|box)\s*"
        r"(?:\d{1,2}[a-z]?|[a-z](?:\s*\.\s*[ab])?)\b",
        texte,
        flags=re.IGNORECASE,
    )
    if resultat is None:
        return None
    return resultat.start()


def _chercher_montant_apres(
    texte: str,
    marqueurs: tuple[str, ...],
) -> tuple[Decimal, str] | None:
    for marqueur in marqueurs:
        resultat = re.search(
            marqueur,
            texte,
            flags=re.IGNORECASE,
        )
        if resultat is None:
            continue

        extrait = texte[resultat.end():resultat.end() + 220]
        prochaine_case = _prochaine_case_position(extrait)

        if prochaine_case is not None and prochaine_case > 0:
            extrait = extrait[:prochaine_case]

        montant = MONTANT_RE.search(extrait)
        if montant is None:
            continue

        valeur_brute = montant.group(1)
        return convertir_montant_fiscal(valeur_brute), valeur_brute

    return None


def extraire_cases_fiscales(
    type_document: str,
    texte: str,
    source_document: str | Path,
) -> tuple[DonneeFiscaleExtraite, ...]:
    """Extrait les cases connues et conserve la source de chaque valeur."""
    type_normalise = type_document.strip().upper()

    if type_normalise == "T4":
        regles = REGLES_T4
        type_final = "T4"
    elif type_normalise in {"RL-1", "RL1"}:
        regles = REGLES_RL1
        type_final = "RL-1"
    else:
        raise ValueError(
            "Type fiscal non pris en charge pour l'extraction."
        )

    document = Path(source_document)
    donnees: list[DonneeFiscaleExtraite] = []

    for case, libelle, marqueurs in regles:
        resultat = _chercher_montant_apres(
            texte,
            marqueurs,
        )
        if resultat is None:
            continue

        valeur, valeur_brute = resultat
        donnees.append(
            DonneeFiscaleExtraite(
                document=document,
                type_document=type_final,
                case=case,
                libelle=libelle,
                valeur=valeur,
                valeur_brute=valeur_brute,
            )
        )

    return tuple(donnees)
