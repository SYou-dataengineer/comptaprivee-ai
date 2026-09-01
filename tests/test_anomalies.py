"""Tests de la détection d'anomalies comptables."""

from decimal import Decimal

from src.comptaprivee.anomalies import (
    detecter_anomalies,
    detecter_anomalies_facture,
)
from src.comptaprivee.database import FactureEnregistree


def creer_facture(
    *,
    identifiant: int = 1,
    numero: str | None = "FAC-001",
    date: str | None = "2026-09-01",
    fournisseur: str | None = "Fournisseur",
    sous_total: Decimal | None = Decimal("100.00"),
    tps: Decimal | None = Decimal("5.00"),
    tvq: Decimal | None = Decimal("9.98"),
    total: Decimal | None = Decimal("114.98"),
) -> FactureEnregistree:
    return FactureEnregistree(
        identifiant=identifiant,
        numero=numero,
        date=date,
        fournisseur=fournisseur,
        client="Client",
        sous_total=sous_total,
        tps=tps,
        tvq=tvq,
        total=total,
        date_creation="2026-09-01 12:00:00",
    )


def test_aucune_anomalie_sur_facture_valide() -> None:
    assert detecter_anomalies_facture(
        creer_facture()
    ) == []


def test_detecter_champs_et_taxes_manquants() -> None:
    anomalies = detecter_anomalies_facture(
        creer_facture(
            numero=None,
            fournisseur=None,
            tps=None,
            tvq=None,
            total=None,
        )
    )

    messages = {
        anomalie.message
        for anomalie in anomalies
    }

    assert "Numéro de facture manquant." in messages
    assert "Fournisseur manquant." in messages
    assert "TPS manquante." in messages
    assert "TVQ manquante." in messages
    assert "Total manquant." in messages


def test_detecter_total_incoherent() -> None:
    anomalies = detecter_anomalies_facture(
        creer_facture(
            total=Decimal("120.00"),
        )
    )

    assert any(
        anomalie.niveau == "Erreur"
        and "Total incohérent" in anomalie.message
        for anomalie in anomalies
    )


def test_detecter_anomalies_sur_plusieurs_factures() -> None:
    anomalies = detecter_anomalies(
        [
            creer_facture(identifiant=1),
            creer_facture(
                identifiant=2,
                numero="FAC-002",
                tps=Decimal("-1.00"),
            ),
        ]
    )

    assert any(
        anomalie.identifiant == 2
        and "Montant négatif" in anomalie.message
        for anomalie in anomalies
    )
