"""Tests de sauvegarde et restauration locales."""

import json
import zipfile
from pathlib import Path

import pytest

from src.comptaprivee.backup_manager import (
    creer_sauvegarde,
    restaurer_sauvegarde,
)


def test_creer_sauvegarde_zip(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    data = Path("data")
    data.mkdir()
    (data / "comptaprivee.db").write_bytes(b"sqlite-demo")
    (data / "parametres.json").write_text(
        '{"devise": "CAD"}',
        encoding="utf-8",
    )
    (data / "profil_comptable.json").write_text(
        '{"nom": "Cabinet Test"}',
        encoding="utf-8",
    )

    destination = Path("sauvegarde.zip")
    resultat = creer_sauvegarde(destination)

    assert resultat == destination
    assert destination.exists()

    with zipfile.ZipFile(destination) as archive:
        noms = set(archive.namelist())

    assert "manifest.json" in noms
    assert "data/comptaprivee.db" in noms
    assert "data/parametres.json" in noms
    assert "data/profil_comptable.json" in noms


def test_refuser_extension_non_zip(tmp_path) -> None:
    with pytest.raises(ValueError):
        creer_sauvegarde(tmp_path / "sauvegarde.txt")


def test_restaurer_sauvegarde(tmp_path) -> None:
    archive = tmp_path / "backup.zip"

    with zipfile.ZipFile(archive, "w") as fichier:
        fichier.writestr(
            "manifest.json",
            json.dumps({"application": "ComptaPrivée AI"}),
        )
        fichier.writestr(
            "data/parametres.json",
            '{"langue": "fr"}',
        )

    cible = tmp_path / "restaure"
    fichiers = restaurer_sauvegarde(
        archive,
        racine=cible,
    )

    attendu = cible / "data" / "parametres.json"
    assert attendu in fichiers
    assert attendu.read_text(encoding="utf-8") == '{"langue": "fr"}'


def test_restaurer_refuse_manifest_absent(tmp_path) -> None:
    archive = tmp_path / "backup.zip"

    with zipfile.ZipFile(archive, "w") as fichier:
        fichier.writestr(
            "data/comptaprivee.db",
            "demo",
        )

    with pytest.raises(ValueError):
        restaurer_sauvegarde(archive, racine=tmp_path / "cible")


def test_restaurer_refuse_chemin_dangereux(tmp_path) -> None:
    archive = tmp_path / "backup.zip"

    with zipfile.ZipFile(archive, "w") as fichier:
        fichier.writestr(
            "manifest.json",
            "{}",
        )
        fichier.writestr(
            "../hors_dossier.txt",
            "danger",
        )

    with pytest.raises(ValueError):
        restaurer_sauvegarde(archive, racine=tmp_path / "cible")
