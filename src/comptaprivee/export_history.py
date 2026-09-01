"""Historique local des fichiers exportés par ComptaPrivée AI."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

EXTENSIONS_EXPORT = {".pdf", ".csv"}


@dataclass(frozen=True)
class ExportEnregistre:
    nom: str
    chemin: Path
    type_fichier: str
    taille_octets: int
    modifie_le: datetime


def type_export(chemin: str | Path) -> str:
    extension = Path(chemin).suffix.lower()
    if extension == ".pdf":
        return "PDF"
    if extension == ".csv":
        return "CSV"
    return extension.lstrip(".").upper() or "Fichier"


def lister_exports(
    dossier: str | Path = Path("data") / "exports",
) -> list[ExportEnregistre]:
    repertoire = Path(dossier)
    if not repertoire.exists():
        return []

    resultats = []

    for chemin in repertoire.iterdir():
        if (
            not chemin.is_file()
            or chemin.suffix.lower() not in EXTENSIONS_EXPORT
        ):
            continue

        stat = chemin.stat()
        resultats.append(
            ExportEnregistre(
                nom=chemin.name,
                chemin=chemin,
                type_fichier=type_export(chemin),
                taille_octets=stat.st_size,
                modifie_le=datetime.fromtimestamp(stat.st_mtime),
            )
        )

    return sorted(
        resultats,
        key=lambda item: item.modifie_le,
        reverse=True,
    )


def formater_taille(taille_octets: int) -> str:
    if taille_octets < 1024:
        return f"{taille_octets} o"

    if taille_octets < 1024 * 1024:
        return f"{taille_octets / 1024:.1f} Ko"

    return f"{taille_octets / (1024 * 1024):.1f} Mo"

def filtrer_exports(
    exports: list[ExportEnregistre],
    *,
    recherche: str = "",
    type_fichier: str = "Tous",
    date_debut: str = "",
    date_fin: str = "",
) -> list[ExportEnregistre]:
    """Filtre les exports par nom, type et date de modification."""
    terme = recherche.strip().casefold()
    type_demande = type_fichier.strip().upper()

    debut = _lire_date_filtre(date_debut)
    fin = _lire_date_filtre(date_fin)

    if debut and fin and debut > fin:
        raise ValueError(
            "La date de début doit être antérieure ou égale à la date de fin."
        )

    resultats = []

    for export in exports:
        if terme and terme not in export.nom.casefold():
            continue

        if (
            type_demande not in {"", "TOUS"}
            and export.type_fichier.upper() != type_demande
        ):
            continue

        jour_export = export.modifie_le.date()

        if debut and jour_export < debut:
            continue

        if fin and jour_export > fin:
            continue

        resultats.append(export)

    return resultats


def _lire_date_filtre(valeur: str):
    """Lit une date AAAA-MM-JJ vide ou valide."""
    from datetime import date

    texte = valeur.strip()

    if not texte:
        return None

    try:
        return date.fromisoformat(texte)
    except ValueError as erreur:
        raise ValueError(
            "Les dates doivent être au format AAAA-MM-JJ."
        ) from erreur

def compter_types(
    exports: list[ExportEnregistre],
) -> dict[str, int]:
    """Compte rapidement le nombre de PDF et CSV."""
    compte = {
        "Tous": len(exports),
        "PDF": 0,
        "CSV": 0,
    }

    for export in exports:
        type_fichier = export.type_fichier.upper()

        if type_fichier in compte:
            compte[type_fichier] += 1

    return compte

def trier_exports(
    exports: list[ExportEnregistre],
    colonne: str = "date",
    decroissant: bool = True,
) -> list[ExportEnregistre]:
    """Trie les exports selon une colonne de l'historique."""
    cles = {
        "nom": lambda item: item.nom.casefold(),
        "type": lambda item: item.type_fichier.casefold(),
        "date": lambda item: item.modifie_le,
        "taille": lambda item: item.taille_octets,
    }

    if colonne not in cles:
        raise ValueError(f"Colonne de tri inconnue : {colonne}")

    return sorted(
        exports,
        key=cles[colonne],
        reverse=decroissant,
    )

def exporter_historique_csv(
    exports: list[ExportEnregistre],
    chemin: str | Path,
) -> Path:
    # Exporte une liste d'exports vers un fichier CSV UTF-8.
    import csv

    destination = Path(chemin)

    if destination.suffix.lower() != ".csv":
        raise ValueError(
            "Le fichier d'historique doit avoir l'extension .csv."
        )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with destination.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as fichier:
        writer = csv.writer(fichier)
        writer.writerow(
            [
                "Fichier",
                "Type",
                "Cree_modifie",
                "Taille_octets",
            ]
        )

        for export in exports:
            writer.writerow(
                [
                    export.nom,
                    export.type_fichier,
                    export.modifie_le.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    export.taille_octets,
                ]
            )

    return destination
