"""Tests de la corbeille locale des factures."""

from decimal import Decimal

from src.comptaprivee.database import (
    enregistrer_facture,
    lister_factures,
    lister_factures_corbeille,
    mettre_facture_corbeille,
    restaurer_facture,
    supprimer_facture_corbeille,
)
from src.comptaprivee.facture_parser import DonneesFacture


def creer_facture() -> DonneesFacture:
    return DonneesFacture(
        numero="CORB-TEST-001",
        date="2026-08-31",
        fournisseur="Fournisseur Test",
        client="Client Test",
        sous_total=Decimal("100.00"),
        tps=Decimal("5.00"),
        tvq=Decimal("9.98"),
        total=Decimal("114.98"),
    )


def test_mettre_facture_corbeille(tmp_path) -> None:
    base = tmp_path / "test.db"
    facture = enregistrer_facture(creer_facture(), base)
    assert mettre_facture_corbeille(facture.identifiant, base)
    assert lister_factures(base) == []
    corbeille = lister_factures_corbeille(base)
    assert len(corbeille) == 1
    assert corbeille[0].numero == "CORB-TEST-001"


def test_restaurer_facture(tmp_path) -> None:
    base = tmp_path / "test.db"
    facture = enregistrer_facture(creer_facture(), base)
    assert mettre_facture_corbeille(facture.identifiant, base)
    assert restaurer_facture(facture.identifiant, base)
    actives = lister_factures(base)
    assert len(actives) == 1
    assert actives[0].numero == "CORB-TEST-001"
    assert lister_factures_corbeille(base) == []


def test_supprimer_definitivement_corbeille(tmp_path) -> None:
    base = tmp_path / "test.db"
    facture = enregistrer_facture(creer_facture(), base)
    assert mettre_facture_corbeille(facture.identifiant, base)
    assert supprimer_facture_corbeille(facture.identifiant, base)
    assert lister_factures(base) == []
    assert lister_factures_corbeille(base) == []
