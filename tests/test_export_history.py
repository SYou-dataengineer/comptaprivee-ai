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

def test_filtrer_exports_par_nom(tmp_path) -> None:
    from src.comptaprivee.export_history import filtrer_exports

    (tmp_path / "resume_client.pdf").write_bytes(b"a")
    (tmp_path / "tableau_bord.csv").write_bytes(b"b")

    exports = lister_exports(tmp_path)
    filtres = filtrer_exports(
        exports,
        recherche="resume",
    )

    assert [item.nom for item in filtres] == [
        "resume_client.pdf"
    ]


def test_filtrer_exports_par_type(tmp_path) -> None:
    from src.comptaprivee.export_history import filtrer_exports

    (tmp_path / "rapport.pdf").write_bytes(b"a")
    (tmp_path / "rapport.csv").write_bytes(b"b")

    exports = lister_exports(tmp_path)
    filtres = filtrer_exports(
        exports,
        type_fichier="PDF",
    )

    assert len(filtres) == 1
    assert filtres[0].type_fichier == "PDF"


def test_filtrer_exports_nom_et_type(tmp_path) -> None:
    from src.comptaprivee.export_history import filtrer_exports

    (tmp_path / "resume.pdf").write_bytes(b"a")
    (tmp_path / "resume.csv").write_bytes(b"b")
    (tmp_path / "tableau.pdf").write_bytes(b"c")

    exports = lister_exports(tmp_path)
    filtres = filtrer_exports(
        exports,
        recherche="resume",
        type_fichier="CSV",
    )

    assert [item.nom for item in filtres] == [
        "resume.csv"
    ]


def test_compter_types(tmp_path) -> None:
    from src.comptaprivee.export_history import compter_types

    (tmp_path / "a.pdf").write_bytes(b"a")
    (tmp_path / "b.pdf").write_bytes(b"b")
    (tmp_path / "c.csv").write_bytes(b"c")

    compte = compter_types(
        lister_exports(tmp_path)
    )

    assert compte == {
        "Tous": 3,
        "PDF": 2,
        "CSV": 1,
    }


def test_recherche_exports_insensible_casse(tmp_path) -> None:
    from src.comptaprivee.export_history import filtrer_exports

    (tmp_path / "Resume_Comptable.PDF").write_bytes(b"a")

    exports = lister_exports(tmp_path)
    filtres = filtrer_exports(
        exports,
        recherche="resume_comptable",
    )

    assert len(filtres) == 1
