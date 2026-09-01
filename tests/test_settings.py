"""Tests des paramètres locaux de ComptaPrivée AI."""

import pytest

from src.comptaprivee.settings import (
    ParametresApplication,
    enregistrer_parametres,
    lire_parametres,
    normaliser_couleur_hex,
)


def test_parametres_par_defaut(tmp_path) -> None:
    parametres = lire_parametres(
        tmp_path / "absent.json"
    )

    assert parametres.devise == "CAD"
    assert parametres.langue_rapports == "Français"
    assert parametres.format_date == "AAAA-MM-JJ"


def test_enregistrer_et_lire_parametres(tmp_path) -> None:
    chemin = tmp_path / "parametres.json"
    attendus = ParametresApplication(
        devise="USD",
        langue_rapports="English",
        format_date="MM-JJ-AAAA",
        couleur_pdf="#224488",
    )

    enregistrer_parametres(
        attendus,
        chemin,
    )

    assert lire_parametres(chemin) == attendus


def test_normaliser_couleur_hex() -> None:
    assert normaliser_couleur_hex(
        " #1a408c "
    ) == "#1A408C"


def test_refuser_couleur_invalide() -> None:
    with pytest.raises(ValueError):
        normaliser_couleur_hex("bleu")

def test_couleur_hex_vers_pdf() -> None:
    from src.comptaprivee.settings import couleur_hex_vers_pdf

    assert couleur_hex_vers_pdf("#FF0000") == (1.0, 0.0, 0.0)


def test_formater_date_rapport() -> None:
    from src.comptaprivee.settings import formater_date_rapport

    assert formater_date_rapport(
        "2026-09-01",
        "JJ-MM-AAAA",
    ) == "01-09-2026"


def test_texte_rapport_anglais() -> None:
    from src.comptaprivee.settings import texte_rapport

    assert texte_rapport(
        "resume",
        "English",
    ) == "ACCOUNTING SUMMARY"
