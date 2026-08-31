"""Tests du stockage local des factures avec SQLite."""

import sqlite3
from decimal import Decimal

import pytest

from src.comptaprivee.database import (
    enregistrer_facture,
    initialiser_base,
    lister_factures,
    rechercher_factures,
    supprimer_facture,
)
from src.comptaprivee.facture_parser import DonneesFacture


def creer_facture_test(
    numero: str = "FAC-DB-001",
    fournisseur: str = "Entreprise SQLite Inc.",
    client: str = "Client Base Locale Inc.",
) -> DonneesFacture:
    """Crée une facture fictive pour les tests."""
    return DonneesFacture(
        numero=numero,
        date="2026-08-31",
        fournisseur=fournisseur,
        client=client,
        sous_total=Decimal("1000.00"),
        tps=Decimal("50.00"),
        tvq=Decimal("99.75"),
        total=Decimal("1149.75"),
    )


def test_initialiser_base_cree_la_table(tmp_path) -> None:
    """Vérifie que la base et la table sont créées."""
    chemin_base = tmp_path / "test.db"

    resultat = initialiser_base(chemin_base)

    assert resultat == chemin_base
    assert chemin_base.exists()

    with sqlite3.connect(chemin_base) as connexion:
        table = connexion.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'factures'
            """
        ).fetchone()

    assert table is not None
    assert table[0] == "factures"


def test_enregistrer_et_lister_une_facture(tmp_path) -> None:
    """Vérifie l’enregistrement et la lecture d’une facture."""
    chemin_base = tmp_path / "test.db"
    facture = creer_facture_test()

    facture_enregistree = enregistrer_facture(
        facture,
        chemin_base,
    )
    factures = lister_factures(chemin_base)

    assert facture_enregistree.identifiant > 0
    assert facture_enregistree.numero == "FAC-DB-001"
    assert facture_enregistree.total == Decimal("1149.75")

    assert len(factures) == 1
    assert factures[0].numero == "FAC-DB-001"
    assert factures[0].fournisseur == "Entreprise SQLite Inc."
    assert factures[0].client == "Client Base Locale Inc."
    assert factures[0].sous_total == Decimal("1000.00")
    assert factures[0].tps == Decimal("50.00")
    assert factures[0].tvq == Decimal("99.75")
    assert factures[0].total == Decimal("1149.75")


def test_refuser_un_numero_de_facture_en_double(tmp_path) -> None:
    """Vérifie qu’un même numéro ne peut pas être enregistré deux fois."""
    chemin_base = tmp_path / "test.db"
    facture = creer_facture_test()

    enregistrer_facture(facture, chemin_base)

    with pytest.raises(ValueError, match="existe déjà"):
        enregistrer_facture(facture, chemin_base)

    assert len(lister_factures(chemin_base)) == 1


def test_rechercher_des_factures(tmp_path) -> None:
    """Vérifie la recherche par numéro, fournisseur et client."""
    chemin_base = tmp_path / "test.db"

    enregistrer_facture(
        creer_facture_test(
            numero="FAC-DB-001",
            fournisseur="Entreprise Alpha Inc.",
            client="Client Montréal Inc.",
        ),
        chemin_base,
    )

    enregistrer_facture(
        creer_facture_test(
            numero="FAC-DB-002",
            fournisseur="Entreprise Beta Inc.",
            client="Client Québec Inc.",
        ),
        chemin_base,
    )

    resultat_numero = rechercher_factures(
        "FAC-DB-002",
        chemin_base,
    )
    resultat_fournisseur = rechercher_factures(
        "alpha",
        chemin_base,
    )
    resultat_client = rechercher_factures(
        "Montréal",
        chemin_base,
    )

    assert len(resultat_numero) == 1
    assert resultat_numero[0].numero == "FAC-DB-002"

    assert len(resultat_fournisseur) == 1
    assert resultat_fournisseur[0].fournisseur == "Entreprise Alpha Inc."

    assert len(resultat_client) == 1
    assert resultat_client[0].client == "Client Montréal Inc."


def test_supprimer_une_facture(tmp_path) -> None:
    """Vérifie la suppression d’une facture."""
    chemin_base = tmp_path / "test.db"
    facture = enregistrer_facture(
        creer_facture_test(),
        chemin_base,
    )

    facture_supprimee = supprimer_facture(
        facture.identifiant,
        chemin_base,
    )
    seconde_suppression = supprimer_facture(
        facture.identifiant,
        chemin_base,
    )

    assert facture_supprimee is True
    assert seconde_suppression is False
    assert lister_factures(chemin_base) == []