"""Tests de l'historique local des exports."""

from datetime import datetime
import os

from src.comptaprivee.export_history import (
    formater_taille,
    lister_exports,
    type_export,
)


def test_type_export() -> None:
    assert type_export("rapport.pdf") == "PDF"
    assert type_export("rapport.csv") == "CSV"


def test_lister_exports_ignore_autres_fichiers(tmp_path) -> None:
    (tmp_path / "rapport.pdf").write_bytes(b"PDF")
    (tmp_path / "rapport.csv").write_text("a,b", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("ignore", encoding="utf-8")

    exports = lister_exports(tmp_path)

    assert {item.nom for item in exports} == {
        "rapport.pdf",
        "rapport.csv",
    }


def test_lister_exports_plus_recent_en_premier(tmp_path) -> None:
    ancien = tmp_path / "ancien.pdf"
    recent = tmp_path / "recent.pdf"

    ancien.write_bytes(b"a")
    recent.write_bytes(b"b")

    os.utime(ancien, (1000, 1000))
    os.utime(recent, (2000, 2000))

    exports = lister_exports(tmp_path)

    assert exports[0].nom == "recent.pdf"
    assert isinstance(exports[0].modifie_le, datetime)


def test_formater_taille() -> None:
    assert formater_taille(512) == "512 o"
    assert formater_taille(2048) == "2.0 Ko"
