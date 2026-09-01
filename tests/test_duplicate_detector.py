"""Tests de détection locale des factures en double."""

from decimal import Decimal

from src.comptaprivee.database import enregistrer_facture
from src.comptaprivee.duplicate_detector import (
    NiveauDoublon,
    detecter_doublon,
)
from src.comptaprivee.facture_parser import DonneesFacture


def facture(
    *,
    numero: str | None = "FAC-001",
    date: str | None = "2026-09-01",
    fournisseur: str | None = "Fournisseur Exemple Inc.",
    total: Decimal | None = Decimal("1149.75"),
) -> DonneesFacture:
    return DonneesFacture(
        numero=numero,
        date=date,
        fournisseur=fournisseur,
        client="Client Exemple",
        sous_total=Decimal("1000.00"),
        tps=Decimal("50.00"),
        tvq=Decimal("99.75"),
        total=total,
    )


def test_detecter_doublon_par_numero(tmp_path) -> None:
    chemin = tmp_path / "test.db"
    enregistrer_facture(facture(), chemin)

    resultat = detecter_doublon(
        facture(
            fournisseur="Autre fournisseur",
            total=Decimal("999.00"),
        ),
        chemin,
    )

    assert resultat.niveau is NiveauDoublon.CERTAIN
    assert resultat.facture_existante is not None
    assert resultat.facture_existante.numero == "FAC-001"


def test_detecter_doublon_numero_insensible_casse(tmp_path) -> None:
    chemin = tmp_path / "test.db"
    enregistrer_facture(facture(numero="FAC-ABC-01"), chemin)

    resultat = detecter_doublon(
        facture(numero=" fac-abc-01 "),
        chemin,
    )

    assert resultat.niveau is NiveauDoublon.CERTAIN


def test_detecter_doublon_probable_sans_numero(tmp_path) -> None:
    chemin = tmp_path / "test.db"
    enregistrer_facture(
        facture(numero="FAC-ORIGINALE"),
        chemin,
    )

    resultat = detecter_doublon(
        facture(numero=None),
        chemin,
    )

    assert resultat.niveau is NiveauDoublon.PROBABLE
    assert "Même fournisseur" in resultat.raison


def test_ne_pas_signaler_si_total_different(tmp_path) -> None:
    chemin = tmp_path / "test.db"
    enregistrer_facture(facture(), chemin)

    resultat = detecter_doublon(
        facture(
            numero="FAC-002",
            total=Decimal("1200.00"),
        ),
        chemin,
    )

    assert resultat.niveau is NiveauDoublon.AUCUN
    assert resultat.est_doublon is False


def test_ne_pas_signaler_base_vide(tmp_path) -> None:
    resultat = detecter_doublon(
        facture(),
        tmp_path / "vide.db",
    )

    assert resultat.niveau is NiveauDoublon.AUCUN
    assert resultat.facture_existante is None
