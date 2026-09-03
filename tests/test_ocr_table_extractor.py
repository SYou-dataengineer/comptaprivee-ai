from src.comptaprivee.ocr_table_extractor import (
    MotOCR,
    reconstruire_tableau_depuis_mots,
    extraire_mots_image_tesseract,
)


def _mot(texte, x, y, w=50, h=16):
    return MotOCR(
        texte=texte,
        gauche=x,
        haut=y,
        largeur=w,
        hauteur=h,
        confiance=95.0,
    )


def test_reconstruit_tableau_trois_colonnes() -> None:
    mots = [
        _mot("Date", 10, 10),
        _mot("Fournisseur", 150, 10, 80),
        _mot("Total", 330, 10),
        _mot("2026-09-01", 10, 40, 80),
        _mot("ABC", 150, 40),
        _mot("114.98", 330, 40),
        _mot("2026-09-02", 10, 70, 80),
        _mot("XYZ", 150, 70),
        _mot("287.44", 330, 70),
    ]

    assert reconstruire_tableau_depuis_mots(mots) == [
        ["Date", "Fournisseur", "Total"],
        ["2026-09-01", "ABC", "114.98"],
        ["2026-09-02", "XYZ", "287.44"],
    ]


def test_regroupe_plusieurs_mots_dans_une_cellule() -> None:
    mots = [
        _mot("No", 10, 10, 20),
        _mot("facture", 35, 10, 55),
        _mot("Total", 250, 10),
        _mot("FAC-001", 10, 40, 70),
        _mot("100.00", 250, 40),
    ]

    tableau = reconstruire_tableau_depuis_mots(mots)

    assert tableau[0][0] == "No facture"
    assert tableau[0][1] == "Total"
    assert tableau[1] == ["FAC-001", "100.00"]


def test_retourne_vide_si_pas_de_structure_tabulaire() -> None:
    mots = [
        _mot("Bonjour", 10, 10),
        _mot("comptable", 70, 10),
        _mot("document", 10, 40),
        _mot("simple", 70, 40),
    ]

    assert reconstruire_tableau_depuis_mots(mots) == []


def test_tolerance_verticale_regroupe_mots_proches() -> None:
    mots = [
        _mot("Date", 10, 10),
        _mot("Total", 250, 15),
        _mot("2026-09-01", 10, 45, 80),
        _mot("114.98", 250, 48),
    ]

    assert reconstruire_tableau_depuis_mots(
        mots,
        tolerance_y=10,
    ) == [
        ["Date", "Total"],
        ["2026-09-01", "114.98"],
    ]

from pathlib import Path

import pytest

from src.comptaprivee import ocr_table_extractor as ote


def test_extraire_mots_image_tesseract_parse_tsv(
    tmp_path,
    monkeypatch,
) -> None:
    image = tmp_path / "scan.png"
    image.write_bytes(b"fake")

    tsv = (
        "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\t"
        "left\ttop\twidth\theight\tconf\ttext\n"
        "5\t1\t1\t1\t1\t1\t10\t20\t40\t15\t96.5\tDate\n"
        "5\t1\t1\t1\t1\t2\t200\t20\t50\t15\t94.0\tTotal\n"
    )

    class Resultat:
        returncode = 0
        stdout = tsv
        stderr = ""

    monkeypatch.setattr(ote.shutil if hasattr(ote, "shutil") else __import__("shutil"), "which", lambda _x: "tesseract")

    import subprocess
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: Resultat(),
    )

    mots = ote.extraire_mots_image_tesseract(str(image))

    assert [mot.texte for mot in mots] == ["Date", "Total"]
    assert mots[0].gauche == 10
    assert mots[1].gauche == 200
    assert mots[0].confiance == 96.5


def test_extraire_tableau_image_tesseract_reconstruit_tableau(
    tmp_path,
    monkeypatch,
) -> None:
    image = tmp_path / "scan.png"
    image.write_bytes(b"fake")

    mots = [
        ote.MotOCR("Date", 10, 10, 40, 16, 95),
        ote.MotOCR("Total", 250, 10, 50, 16, 95),
        ote.MotOCR("2026-09-01", 10, 40, 80, 16, 95),
        ote.MotOCR("114.98", 250, 40, 60, 16, 95),
    ]

    monkeypatch.setattr(
        ote,
        "extraire_mots_image_tesseract",
        lambda *args, **kwargs: mots,
    )

    tableau = ote.extraire_tableau_image_tesseract(
        str(image),
    )

    assert tableau == [
        ["Date", "Total"],
        ["2026-09-01", "114.98"],
    ]


def test_extraire_mots_image_tesseract_refuse_image_absente() -> None:
    with pytest.raises(FileNotFoundError):
        ote.extraire_mots_image_tesseract("introuvable.png")

def test_tesseract_utilise_psm_11(
    tmp_path,
    monkeypatch,
) -> None:
    image = tmp_path / "scan.png"
    image.write_bytes(b"fake")

    commandes = []

    class Resultat:
        returncode = 0
        stdout = (
            "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\t"
            "left\ttop\twidth\theight\tconf\ttext\n"
        )
        stderr = ""

    import shutil
    import subprocess

    monkeypatch.setattr(
        shutil,
        "which",
        lambda _x: "tesseract",
    )

    def faux_run(commande, **kwargs):
        commandes.append(commande)
        return Resultat()

    monkeypatch.setattr(
        subprocess,
        "run",
        faux_run,
    )

    extraire_mots_image_tesseract(str(image))

    assert commandes
    assert "--psm" in commandes[0]
    assert "11" in commandes[0]
    assert "preserve_interword_spaces=1" in commandes[0]
    assert "tessedit_create_tsv=1" in commandes[0]

def test_pretraitement_tableau_supprime_lignes(
    tmp_path,
) -> None:
    from PIL import Image, ImageDraw

    from src.comptaprivee.ocr_table_extractor import _pretraiter_image_tableau

    source = tmp_path / "grille.png"

    image = Image.new("L", (500, 300), 255)
    dessin = ImageDraw.Draw(image)

    dessin.line((20, 80, 480, 80), fill=0, width=4)
    dessin.line((150, 20, 150, 280), fill=0, width=4)
    dessin.text((30, 40), "Date", fill=0)

    image.save(source)

    destination = Path(
        _pretraiter_image_tableau(str(source))
    )

    try:
        resultat = Image.open(destination).convert("L")

        assert resultat.getpixel((300, 80)) > 240
        assert resultat.getpixel((150, 200)) > 240

    finally:
        destination.unlink(missing_ok=True)


def test_tableau_image_utilise_pretraitement(
    tmp_path,
    monkeypatch,
) -> None:
    from src.comptaprivee import ocr_table_extractor as ote

    image = tmp_path / "scan.png"
    image.write_bytes(b"fake")

    image_nettoyee = tmp_path / "nettoyee.png"
    image_nettoyee.write_bytes(b"fake2")

    monkeypatch.setattr(
        ote,
        "_pretraiter_image_tableau",
        lambda _source: str(image_nettoyee),
    )

    appels = []

    monkeypatch.setattr(
        ote,
        "extraire_mots_image_tesseract",
        lambda chemin, **kwargs: (
            appels.append(chemin)
            or [
                ote.MotOCR("Date", 10, 10, 40, 16, 95),
                ote.MotOCR("Total", 250, 10, 50, 16, 95),
                ote.MotOCR("2026-09-01", 10, 40, 80, 16, 95),
                ote.MotOCR("114.98", 250, 40, 60, 16, 95),
            ]
        ),
    )

    resultat = ote.extraire_tableau_image_tesseract(
        str(image),
    )

    assert appels == [str(image_nettoyee)]
    assert resultat == [
        ["Date", "Total"],
        ["2026-09-01", "114.98"],
    ]

def test_reconstruction_ignore_titre_et_note() -> None:
    mots = [
        _mot("Titre", 10, 0, 80),
        _mot("Date", 10, 40),
        _mot("Fournisseur", 180, 40, 100),
        _mot("Total", 500, 40),
        _mot("2026-09-01", 10, 80, 100),
        _mot("ABC", 180, 80),
        _mot("114.98", 500, 80),
        _mot("2026-09-02", 10, 120, 100),
        _mot("XYZ", 180, 120),
        _mot("287.44", 500, 120),
        _mot("Attendu", 10, 180, 90),
        _mot("fin", 110, 180, 30),
    ]

    tableau = reconstruire_tableau_depuis_mots(
        mots,
        ecart_minimum=55,
    )

    assert tableau == [
        ["Date", "Fournisseur", "Total"],
        ["2026-09-01", "ABC", "114.98"],
        ["2026-09-02", "XYZ", "287.44"],
    ]


def test_reconstruction_garde_cellule_multi_mots_haute_resolution() -> None:
    mots = [
        _mot("Date", 200, 40, 80),
        _mot("Fournisseur", 550, 40, 170),
        _mot("Total", 1700, 40, 90),
        _mot("2026-09-01", 200, 90, 180),
        _mot("Fournisseur", 550, 90, 170),
        _mot("A", 735, 90, 20),
        _mot("114.98", 1700, 90, 100),
        _mot("2026-09-02", 200, 140, 180),
        _mot("Fournisseur", 550, 140, 170),
        _mot("B", 735, 140, 20),
        _mot("287.44", 1700, 140, 100),
    ]

    tableau = reconstruire_tableau_depuis_mots(
        mots,
        ecart_minimum=55,
    )

    assert tableau[1][1] == "Fournisseur A"
    assert tableau[2][1] == "Fournisseur B"

def test_reconstruction_recupere_entete_separe_en_plusieurs_mots() -> None:
    mots = [
        _mot("Titre", 10, 0, 80),
        _mot("Date", 100, 50, 70),
        _mot("Fournisseur", 400, 50, 150),
        _mot("No", 800, 50, 35),
        _mot("facture", 850, 50, 90),
        _mot("Sous-total", 1100, 50, 120),
        _mot("TPS", 1400, 50, 60),
        _mot("TVQ", 1600, 50, 60),
        _mot("Total", 1800, 50, 80),

        _mot("2026-09-01", 100, 120, 170),
        _mot("Fournisseur", 400, 120, 150),
        _mot("A", 570, 120, 25),
        _mot("FAC-001", 800, 120, 120),
        _mot("100.00", 1100, 120, 100),
        _mot("5.00", 1400, 120, 70),
        _mot("9.98", 1600, 120, 70),
        _mot("114.98", 1800, 120, 100),

        _mot("2026-09-02", 100, 190, 170),
        _mot("Fournisseur", 400, 190, 150),
        _mot("B", 570, 190, 25),
        _mot("FAC-002", 800, 190, 120),
        _mot("250.00", 1100, 190, 100),
        _mot("12.50", 1400, 190, 80),
        _mot("24.94", 1600, 190, 80),
        _mot("287.44", 1800, 190, 100),
    ]

    tableau = reconstruire_tableau_depuis_mots(
        mots,
        ecart_minimum=55,
    )

    assert tableau[0] == [
        "Date",
        "Fournisseur",
        "No facture",
        "Sous-total",
        "TPS",
        "TVQ",
        "Total",
    ]
    assert tableau[1][2] == "FAC-001"
    assert tableau[2][6] == "287.44"


def test_reconstruction_ignore_note_apres_tableau() -> None:
    mots = [
        _mot("Date", 100, 50),
        _mot("Total", 800, 50),
        _mot("2026-09-01", 100, 120, 120),
        _mot("114.98", 800, 120, 90),
        _mot("2026-09-02", 100, 190, 120),
        _mot("287.44", 800, 190, 90),
        _mot("Attendu", 100, 400, 100),
        _mot("fin", 220, 400, 40),
    ]

    tableau = reconstruire_tableau_depuis_mots(
        mots,
        ecart_minimum=55,
    )

    assert tableau == [
        ["Date", "Total"],
        ["2026-09-01", "114.98"],
        ["2026-09-02", "287.44"],
    ]

def test_ajoute_entete_comptable_si_ocr_rate_entete() -> None:
    from src.comptaprivee.ocr_table_extractor import (
        _ajouter_entetes_comptables_si_manquants,
    )

    tableau = [
        [
            "2026-09-01",
            "Fournisseur A",
            "FAC-001",
            "100.00",
            "5.00",
            "9.98",
            "114.98",
        ],
        [
            "2026-09-02",
            "Fournisseur B",
            "FAC-002",
            "250.00",
            "12.50",
            "24.94",
            "287.44",
        ],
    ]

    resultat = _ajouter_entetes_comptables_si_manquants(
        tableau,
    )

    assert resultat[0] == [
        "Date",
        "Fournisseur",
        "No facture",
        "Sous-total",
        "TPS",
        "TVQ",
        "Total",
    ]
    assert resultat[1] == tableau[0]


def test_ne_duplique_pas_entete_deja_present() -> None:
    from src.comptaprivee.ocr_table_extractor import (
        _ajouter_entetes_comptables_si_manquants,
    )

    tableau = [
        [
            "Date",
            "Fournisseur",
            "No facture",
            "Sous-total",
            "TPS",
            "TVQ",
            "Total",
        ],
        [
            "2026-09-01",
            "Fournisseur A",
            "FAC-001",
            "100.00",
            "5.00",
            "9.98",
            "114.98",
        ],
    ]

    resultat = _ajouter_entetes_comptables_si_manquants(
        tableau,
    )

    assert resultat == tableau
