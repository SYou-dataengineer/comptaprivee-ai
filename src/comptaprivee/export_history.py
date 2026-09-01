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
) -> list[ExportEnregistre]:
    """Filtre une liste d'exports par nom et par type."""
    terme = recherche.strip().casefold()
    type_demande = type_fichier.strip().upper()

    resultats = []

    for export in exports:
        if terme and terme not in export.nom.casefold():
            continue

        if (
            type_demande not in {"", "TOUS"}
            and export.type_fichier.upper() != type_demande
        ):
            continue

        resultats.append(export)

    return resultats


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
