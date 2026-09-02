"""Sauvegarde et restauration locales de ComptaPrivée AI."""

from __future__ import annotations

import json
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

from .database import CHEMIN_BASE_PAR_DEFAUT


DOSSIER_DATA = Path("data")
FICHIER_PARAMETRES = DOSSIER_DATA / "parametres.json"
FICHIER_PROFIL = DOSSIER_DATA / "profil_comptable.json"


def _fichiers_a_sauvegarder() -> list[Path]:
    """Retourne les fichiers locaux importants à inclure."""
    candidats = [
        CHEMIN_BASE_PAR_DEFAUT,
        FICHIER_PARAMETRES,
        FICHIER_PROFIL,
    ]
    return [
        Path(chemin)
        for chemin in candidats
        if Path(chemin).exists()
    ]


def creer_sauvegarde(
    destination: str | Path,
) -> Path:
    """Crée une archive ZIP locale contenant les données essentielles."""
    destination = Path(destination)

    if destination.suffix.lower() != ".zip":
        raise ValueError(
            "Le fichier de sauvegarde doit avoir l'extension .zip."
        )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fichiers = _fichiers_a_sauvegarder()

    manifeste = {
        "application": "ComptaPrivée AI",
        "cree_le": datetime.now().isoformat(timespec="seconds"),
        "fichiers": [
            str(fichier.as_posix())
            for fichier in fichiers
        ],
    }

    with zipfile.ZipFile(
        destination,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        archive.writestr(
            "manifest.json",
            json.dumps(
                manifeste,
                ensure_ascii=False,
                indent=2,
            ),
        )

        for fichier in fichiers:
            archive.write(
                fichier,
                arcname=fichier.as_posix(),
            )

    from .audit_log import journaliser_sans_bloquer

    journaliser_sans_bloquer(
        "Sauvegarde créée",
        "sauvegarde",
        reference=destination.name,
    )

    return destination


def _chemin_est_sur(
    membre: zipfile.ZipInfo,
) -> bool:
    """Refuse les chemins absolus ou qui sortent du dossier cible."""
    chemin = Path(membre.filename)

    if chemin.is_absolute():
        return False

    return ".." not in chemin.parts


def restaurer_sauvegarde(
    source: str | Path,
    *,
    racine: str | Path = ".",
) -> list[Path]:
    """Restaure une sauvegarde ZIP après validation de son contenu."""
    source = Path(source)
    racine = Path(racine)

    if not source.exists():
        raise FileNotFoundError(
            f"Sauvegarde introuvable : {source}"
        )

    if source.suffix.lower() != ".zip":
        raise ValueError(
            "La sauvegarde doit être un fichier .zip."
        )

    fichiers_restaures: list[Path] = []

    with zipfile.ZipFile(source, "r") as archive:
        noms = set(archive.namelist())

        if "manifest.json" not in noms:
            raise ValueError(
                "Archive invalide : manifest.json manquant."
            )

        membres = [
            membre
            for membre in archive.infolist()
            if membre.filename != "manifest.json"
        ]

        if not all(_chemin_est_sur(membre) for membre in membres):
            raise ValueError(
                "Archive invalide : chemin non sécurisé détecté."
            )

        with tempfile.TemporaryDirectory() as dossier_temporaire:
            temp = Path(dossier_temporaire)

            for membre in membres:
                archive.extract(
                    membre,
                    path=temp,
                )

            for membre in membres:
                source_extraite = temp / membre.filename
                destination = racine / membre.filename

                destination.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                shutil.copy2(
                    source_extraite,
                    destination,
                )
                fichiers_restaures.append(destination)

    from .audit_log import journaliser_sans_bloquer

    journaliser_sans_bloquer(
        "Sauvegarde restaurée",
        "sauvegarde",
        details=f"{len(fichiers_restaures)} fichier(s) restauré(s)",
        reference=source.name,
        chemin_base=racine / CHEMIN_BASE_PAR_DEFAUT,
    )

    return fichiers_restaures
