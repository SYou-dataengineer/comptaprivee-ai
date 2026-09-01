import base64

"""Tests du profil local du cabinet comptable."""

from src.comptaprivee.company_profile import (
    copier_logo_societe,
    ProfilSociete,
    enregistrer_nom_societe,
    enregistrer_profil_societe,
    lignes_coordonnees,
    lire_nom_societe,
    lire_profil_societe,
)


def test_enregistrer_et_lire_nom_societe(tmp_path) -> None:
    chemin = tmp_path / "profil.json"

    enregistrer_nom_societe(
        "Cabinet Exemple CPA Inc.",
        chemin,
    )

    assert lire_nom_societe(
        chemin
    ) == "Cabinet Exemple CPA Inc."


def test_lire_nom_societe_absent(tmp_path) -> None:
    assert lire_nom_societe(
        tmp_path / "absent.json"
    ) == ""


def test_enregistrer_profil_complet(tmp_path) -> None:
    chemin = tmp_path / "profil.json"

    profil = ProfilSociete(
        nom_societe="Cabinet Exemple CPA Inc.",
        adresse="123 rue Exemple",
        ville="Montréal",
        province="QC",
        code_postal="H1H 1H1",
        telephone="514-555-0100",
        courriel="info@exemple.ca",
        site_web="exemple.ca",
        neq="1234567890",
        numero_tps="123456789RT0001",
        numero_tvq="1234567890TQ0001",
    )

    enregistrer_profil_societe(
        profil,
        chemin,
    )

    assert lire_profil_societe(chemin) == profil


def test_lignes_coordonnees() -> None:
    profil = ProfilSociete(
        nom_societe="Cabinet Exemple CPA Inc.",
        adresse="123 rue Exemple",
        ville="Montréal",
        province="QC",
        code_postal="H1H 1H1",
        telephone="514-555-0100",
        courriel="info@exemple.ca",
        neq="1234567890",
    )

    lignes = lignes_coordonnees(profil)

    assert "123 rue Exemple" in lignes
    assert "Montréal, QC, H1H 1H1" in lignes
    assert "514-555-0100 | info@exemple.ca" in lignes
    assert "NEQ 1234567890" in lignes

def test_copier_logo_societe(tmp_path) -> None:
    source = tmp_path / "logo.png"
    source.write_bytes(
        base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB"
            "CAQAAAC1HAwCAAAAC0lEQVR42mP8/x8A"
            "AgMBApY9ZQAAAABJRU5ErkJggg=="
        )
    )

    resultat = copier_logo_societe(
        source,
        tmp_path / "data",
    )

    assert resultat.exists()
    assert resultat.name == "logo_societe.png"


