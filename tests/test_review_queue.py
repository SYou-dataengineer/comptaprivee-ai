"""Tests du tableau des factures à vérifier."""

from decimal import Decimal

from src.comptaprivee.database import FactureEnregistree
from src.comptaprivee.review_queue import (
    NiveauVerification,
    analyser_factures_a_verifier,
)


def facture(
    identifiant: int,
    *,
    numero: str | None = "FAC-001",
    date: str | None = "2026-09-01",
    fournisseur: str | None = "Fournisseur Exemple Inc.",
    sous_total: Decimal | None = Decimal("1000.00"),
    tps: Decimal | None = Decimal("50.00"),
    tvq: Decimal | None = Decimal("99.75"),
    total: Decimal | None = Decimal("1149.75"),
) -> FactureEnregistree:
    return FactureEnregistree(
        identifiant=identifiant,
        numero=numero,
        date=date,
        fournisseur=fournisseur,
        client="Client Exemple",
        sous_total=sous_total,
        tps=tps,
        tvq=tvq,
        total=total,
        date_creation="2026-09-01 12:00:00",
    )


def test_facture_valide_absente_de_la_file() -> None:
    resultat = analyser_factures_a_verifier(
        [facture(1)]
    )

    assert resultat == []


def test_facture_tps_incorrecte_est_erreur() -> None:
    resultat = analyser_factures_a_verifier(
        [
            facture(
                1,
                tps=Decimal("40.00"),
                total=Decimal("1139.75"),
            )
        ]
    )

    assert len(resultat) == 1
    assert resultat[0].niveau is NiveauVerification.ERREUR
    assert any(
        "TPS incohérente" in raison
        for raison in resultat[0].raisons
    )


def test_facture_numero_manquant_est_avertissement() -> None:
    resultat = analyser_factures_a_verifier(
        [facture(1, numero=None)]
    )

    assert len(resultat) == 1
    assert resultat[0].niveau is NiveauVerification.AVERTISSEMENT
    assert any(
        "numéro de facture" in raison
        for raison in resultat[0].raisons
    )


def test_detecter_deux_doublons_probables() -> None:
    resultat = analyser_factures_a_verifier(
        [
            facture(1, numero="FAC-A"),
            facture(2, numero="FAC-B"),
        ]
    )

    assert len(resultat) == 2
    assert all(
        any(
            "Doublon probable" in raison
            for raison in element.raisons
        )
        for element in resultat
    )


def test_pas_doublon_si_total_different() -> None:
    resultat = analyser_factures_a_verifier(
        [
            facture(1, numero="FAC-A"),
            facture(
                2,
                numero="FAC-B",
                total=Decimal("1200.00"),
            ),
        ]
    )

    assert len(resultat) == 1
    assert all(
        "Doublon probable" not in raison
        for raison in resultat[0].raisons
    )
