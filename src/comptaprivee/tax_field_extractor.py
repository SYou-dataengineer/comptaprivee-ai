"""Extraction locale et traçable des premières cases fiscales.

Extraction T4, RL-1, T4E, RL-6, T4A(P) et RL-2 avec validation humaine.
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
    ("20", "Cotisations à un RPA", (r"\bcase\s*20\b", r"\bbox\s*20\b")),
    ("74", "RPA services avant 1990 (cotisant)", (r"\b(?:case|box|code)\s*74\b",)),
    ("75", "RPA services avant 1990 (non cotisant)", (r"\b(?:case|box|code)\s*75\b",)),
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
    ("D", "Cotisations à un RPA", (r"\bcase\s*d\b(?!\s*[-–]\s*\d)",)),
    ("D-1", "Convention de retraite (hors profil RPA courant)", (r"\b(?:case|code)\s*d\s*[-–]\s*1\b",)),
    ("D-2", "RPA services avant 1990 (cotisant)", (r"\b(?:case|code)\s*d\s*[-–]\s*2\b",)),
    ("D-3", "RPA services avant 1990 (non cotisant)", (r"\b(?:case|code)\s*d\s*[-–]\s*3\b",)),
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

REGLES_T4E = tuple(
    (case, libelle, (rf"\b(?:case|box)\s*{case}\b",))
    for case, libelle in (
        ("7", "Taux de remboursement"), ("14", "Prestations totales"),
        ("15", "Prestations régulières et autres"), ("17", "Soutien à l'emploi"),
        ("18", "Prestations exonérées"), ("20", "Aide imposable aux études"),
        ("21", "Aide non imposable aux études"), ("22", "Impôt fédéral retenu"),
        ("23", "Impôt Québec retenu"), ("24", "Impôt des non-résidents"),
        ("26", "Trop-payé récupéré"), ("27", "Annulation d'impôt retenu"),
        ("30", "Remboursement total"), ("33", "Prestations fonds consolidé"),
        ("36", "Prestations RQAP"), ("37", "AE maternité et parentales"),
    )
)
REGLES_RL6 = tuple(
    (case, libelle, (rf"\bcase\s*{case}\b",))
    for case, libelle in (("A", "Prestations RQAP"), ("D", "Remboursement de prestations"), ("G", "Impôt Québec retenu"))
)

REGLES_PENSIONS = {
    t: tuple((c, label, (rf"\b(?:case|box|code)\s*{('0?' + c[1:]) if t == 'T4A' and c.startswith('0') else c}\b",)) for c, label in cases)
    for t, cases in {
        'T4A': [(c, {'016':'Pension RPA', '022':'Impôt fédéral retenu', '024':'Rente', '133':'Rente ou prestation variable (nature à confirmer)', '194':'RPAC'}.get(c,'Autre case T4A à vérifier')) for c in ('016','018','022','024','028','048','105','106','109','115','119','127','133','135','194')],
        'T4RIF': [(c, 'FERR : '+{'16':'paiement', '22':'autre revenu ou déduction (exclu)', '24':'excédent déjà inclus', '28':'impôt fédéral retenu'}.get(c,'cas particulier exclu')) for c in ('16','18','20','22','24','28','35','36','37')],
        'T3': [(str(c), 'Pension admissible' if c==31 else 'Autre case T3 à vérifier') for c in range(21,53)],
        'T5': [(str(c), 'Rente' if c==19 else 'Autre case T5 à vérifier') for c in range(10,31)],
        'RL-16': [(c, 'Pension admissible' if c=='D' else 'Autre case RL-16 hors périmètre') for c in 'ABCDEFGHIJKLMNOPQRST'],
    }.items()
}

REGLES_T4AOAS = tuple((c, label, (rf"\b(?:case|box)\s*{c}\b",)) for c, label in (("18", "PSV imposable"), ("19", "PSV brute (information)"), ("20", "Trop-payé récupéré (exclu)"), ("21", "Suppléments nets"), ("22", "Impôt fédéral retenu"), ("23", "Impôt Québec retenu")))

REGLES_T4AP = tuple(
    (c, libelle, (rf"\b(?:case|box)\s*{c}\b",))
    for c, libelle in (("14", "Rente de retraite"), ("15", "Rente de survivant"),
        ("16", "Rente d'invalidité"), ("17", "Rente d'enfant"), ("18", "Prestation de décès (exclue)"),
        ("19", "Prestation après-retraite"), ("20", "Total RRQ/RPC imposable"),
        ("21", "Mois d'invalidité"), ("22", "Impôt fédéral retenu"), ("23", "Mois de retraite"))
)
REGLES_RL2 = tuple(
    (c, {"A": "Pension RPA (provenance à confirmer)", "B": "FERR ou rente (provenance à confirmer)", "C": "Prestations RRQ/RPC (provenance à confirmer)", "J": "Impôt Québec retenu"}.get(c, "Autre montant RL-2 hors périmètre"),
     (rf"\b(?:case|box|code)\s*{c}\b(?![-–]\d+\b(?![.,]))",))
    for c in ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "C-1", "C-2", "C-3", "C-4", "C-5", "C-6", "C-7", "C-8", "C-9", "C-10", "A-1", "B-1", "B-2", "B-3", "B-4", "B-5", "B-6", "B-7", "B-8", "B-9", "B-10")
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
        r"\b(?:case|box|code)\s*"
        r"(?:\d{1,3}[a-z]?|[a-z](?:\s*\.\s*[ab])?)\b",
        texte,
        flags=re.IGNORECASE,
    )
    if resultat is None:
        return None
    return resultat.start()


def _chercher_montant_apres(
    texte: str,
    marqueurs: tuple[str, ...],
    conserver_signe: bool = False,
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
        if conserver_signe:
            avant = extrait[:montant.start()].rstrip()
            apres = extrait[montant.end():].lstrip()
            if avant.endswith(("-", "−")) or (avant.endswith("(") and apres.startswith(")")):
                valeur_brute = "-" + valeur_brute
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
    elif type_normalise in REGLES_PENSIONS:
        regles, type_final = REGLES_PENSIONS[type_normalise], type_normalise
    elif type_normalise in {"T4A(OAS)", "T4AOAS"}:
        regles, type_final = REGLES_T4AOAS, "T4A(OAS)"
    elif type_normalise in {"T4A(P)", "T4AP"}:
        regles, type_final = REGLES_T4AP, "T4A(P)"
    elif type_normalise in {"RL-2", "RL2"}:
        regles, type_final = REGLES_RL2, "RL-2"
    elif type_normalise == "T4E":
        regles, type_final = REGLES_T4E, "T4E"
    elif type_normalise in {"RL-6", "RL6"}:
        regles, type_final = REGLES_RL6, "RL-6"
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
            conserver_signe=(
                type_final in REGLES_PENSIONS or type_final in {"T4E", "RL-6", "T4A(P)", "RL-2", "T4A(OAS)"}
                or
                (type_final == "T4" and case in {"20", "74", "75"})
                or (type_final == "RL-1" and case in {"D", "D-1", "D-2", "D-3"})
            ),
        )
        if (type_final == "T4E" and case == "7") or (type_final == "T4A(P)" and case in {"21", "23"}):
            # Taux AE ou nombre de mois RRQ/RPC, souvent entier et précédé d'un libellé.
            # Ne jamais récupérer un montant appartenant à la case suivante.
            resultat = None
            marqueur = re.search(rf"\b(?:case|box)\s*{case}\b", texte, re.IGNORECASE)
            if marqueur:
                extrait = texte[marqueur.end():marqueur.end() + 220]
                limite = _prochaine_case_position(extrait)
                if limite is not None:
                    extrait = extrait[:limite]
                taux = re.search(r"(?<![\w.,])([-−]?\d+(?:[.,]\d+)?)(?![\w.,])\s*%?", extrait)
                if taux:
                    brut = taux.group(1).replace("−", "-")
                    resultat = (Decimal(brut.replace(",", ".")), brut)
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
