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

def test_filtrer_exports_par_date_debut(tmp_path) -> None:
    from datetime import datetime
    from src.comptaprivee.export_history import filtrer_exports

    ancien = tmp_path / "ancien.pdf"
    recent = tmp_path / "recent.pdf"
    ancien.write_bytes(b"a")
    recent.write_bytes(b"b")

    os.utime(
        ancien,
        (
            datetime(2026, 8, 1, 10, 0).timestamp(),
            datetime(2026, 8, 1, 10, 0).timestamp(),
        ),
    )
    os.utime(
        recent,
        (
            datetime(2026, 9, 1, 10, 0).timestamp(),
            datetime(2026, 9, 1, 10, 0).timestamp(),
        ),
    )

    filtres = filtrer_exports(
        lister_exports(tmp_path),
        date_debut="2026-09-01",
    )

    assert [item.nom for item in filtres] == ["recent.pdf"]


def test_filtrer_exports_par_plage_date(tmp_path) -> None:
    from datetime import datetime
    from src.comptaprivee.export_history import filtrer_exports

    aout = tmp_path / "aout.pdf"
    septembre = tmp_path / "septembre.pdf"
    aout.write_bytes(b"a")
    septembre.write_bytes(b"b")

    os.utime(
        aout,
        (
            datetime(2026, 8, 15, 12, 0).timestamp(),
            datetime(2026, 8, 15, 12, 0).timestamp(),
        ),
    )
    os.utime(
        septembre,
        (
            datetime(2026, 9, 1, 12, 0).timestamp(),
            datetime(2026, 9, 1, 12, 0).timestamp(),
        ),
    )

    filtres = filtrer_exports(
        lister_exports(tmp_path),
        date_debut="2026-08-01",
        date_fin="2026-08-31",
    )

    assert [item.nom for item in filtres] == ["aout.pdf"]


def test_filtrer_exports_date_invalide(tmp_path) -> None:
    import pytest
    from src.comptaprivee.export_history import filtrer_exports

    with pytest.raises(ValueError):
        filtrer_exports(
            lister_exports(tmp_path),
            date_debut="01-09-2026",
        )


def test_filtrer_exports_date_debut_apres_fin(tmp_path) -> None:
    import pytest
    from src.comptaprivee.export_history import filtrer_exports

    with pytest.raises(ValueError):
        filtrer_exports(
            lister_exports(tmp_path),
            date_debut="2026-09-10",
            date_fin="2026-09-01",
        )


def test_filtrer_exports_combine_nom_type_date(tmp_path) -> None:
    from datetime import datetime
    from src.comptaprivee.export_history import filtrer_exports

    pdf = tmp_path / "resume_client.pdf"
    csv = tmp_path / "resume_client.csv"
    pdf.write_bytes(b"a")
    csv.write_bytes(b"b")

    instant = datetime(2026, 9, 1, 9, 0).timestamp()
    os.utime(pdf, (instant, instant))
    os.utime(csv, (instant, instant))

    filtres = filtrer_exports(
        lister_exports(tmp_path),
        recherche="resume",
        type_fichier="PDF",
        date_debut="2026-09-01",
        date_fin="2026-09-01",
    )

    assert [item.nom for item in filtres] == ["resume_client.pdf"]

def test_trier_exports_par_nom(tmp_path) -> None:
    from src.comptaprivee.export_history import trier_exports

    (tmp_path / "zeta.pdf").write_bytes(b"a")
    (tmp_path / "alpha.pdf").write_bytes(b"b")

    tries = trier_exports(
        lister_exports(tmp_path),
        colonne="nom",
        decroissant=False,
    )

    assert [item.nom for item in tries] == [
        "alpha.pdf",
        "zeta.pdf",
    ]


def test_trier_exports_par_taille(tmp_path) -> None:
    from src.comptaprivee.export_history import trier_exports

    (tmp_path / "petit.pdf").write_bytes(b"a")
    (tmp_path / "grand.pdf").write_bytes(b"123456")

    tries = trier_exports(
        lister_exports(tmp_path),
        colonne="taille",
        decroissant=True,
    )

    assert tries[0].nom == "grand.pdf"


def test_trier_exports_par_date(tmp_path) -> None:
    from datetime import datetime
    from src.comptaprivee.export_history import trier_exports

    ancien = tmp_path / "ancien.pdf"
    recent = tmp_path / "recent.pdf"
    ancien.write_bytes(b"a")
    recent.write_bytes(b"b")

    instant_ancien = datetime(2026, 8, 1, 9, 0).timestamp()
    instant_recent = datetime(2026, 9, 1, 9, 0).timestamp()
    os.utime(ancien, (instant_ancien, instant_ancien))
    os.utime(recent, (instant_recent, instant_recent))

    tries = trier_exports(
        lister_exports(tmp_path),
        colonne="date",
        decroissant=False,
    )

    assert [item.nom for item in tries] == [
        "ancien.pdf",
        "recent.pdf",
    ]


def test_trier_exports_colonne_invalide(tmp_path) -> None:
    import pytest
    from src.comptaprivee.export_history import trier_exports

    with pytest.raises(ValueError):
        trier_exports(
            lister_exports(tmp_path),
            colonne="inconnue",
        )

def test_exporter_historique_csv(tmp_path) -> None:
    from src.comptaprivee.export_history import exporter_historique_csv

    (tmp_path / "a.pdf").write_bytes(b"a")
    (tmp_path / "b.csv").write_bytes(b"bb")

    exports = lister_exports(tmp_path)
    chemin = tmp_path / "historique.csv"

    resultat = exporter_historique_csv(exports, chemin)

    assert resultat == chemin
    contenu = chemin.read_text(encoding="utf-8-sig")
    assert "Fichier,Type,Cree_modifie,Taille_octets" in contenu
    assert "a.pdf,PDF" in contenu
    assert "b.csv,CSV" in contenu


def test_exporter_historique_csv_refuse_extension(tmp_path) -> None:
    import pytest
    from src.comptaprivee.export_history import exporter_historique_csv

    with pytest.raises(ValueError):
        exporter_historique_csv(
            [],
            tmp_path / "historique.txt",
        )


def test_exporter_historique_csv_liste_vide(tmp_path) -> None:
    from src.comptaprivee.export_history import exporter_historique_csv

    chemin = tmp_path / "vide.csv"
    exporter_historique_csv([], chemin)

    contenu = chemin.read_text(encoding="utf-8-sig")
    assert contenu.strip() == (
        "Fichier,Type,Cree_modifie,Taille_octets"
    )

def test_periode_rapide_exports_aujourdhui() -> None:
    from datetime import date
    from src.comptaprivee.export_history import periode_rapide_exports

    debut, fin = periode_rapide_exports(
        "Aujourd'hui",
        aujourd_hui=date(2026, 9, 4),
    )

    assert debut == "2026-09-04"
    assert fin == "2026-09-04"


def test_periode_rapide_exports_7_jours() -> None:
    from datetime import date
    from src.comptaprivee.export_history import periode_rapide_exports

    debut, fin = periode_rapide_exports(
        "7 jours",
        aujourd_hui=date(2026, 9, 4),
    )

    assert debut == "2026-08-29"
    assert fin == "2026-09-04"


def test_periode_rapide_exports_ce_mois() -> None:
    from datetime import date
    from src.comptaprivee.export_history import periode_rapide_exports

    debut, fin = periode_rapide_exports(
        "Ce mois",
        aujourd_hui=date(2026, 9, 4),
    )

    assert debut == "2026-09-01"
    assert fin == "2026-09-04"


def test_periode_rapide_exports_refuse_mode_inconnu() -> None:
    import pytest
    from datetime import date
    from src.comptaprivee.export_history import periode_rapide_exports

    with pytest.raises(ValueError):
        periode_rapide_exports(
            "30 jours",
            aujourd_hui=date(2026, 9, 4),
        )
