"""Tests du tableau de bord comptable."""

from decimal import Decimal

from src.comptaprivee.dashboard import (
    calculer_resume,
    filtrer_factures_fournisseur,
    filtrer_factures_periode,
)
from src.comptaprivee.database import FactureEnregistree


def facture(
    identifiant: int,
    fournisseur: str,
    total: str,
    sous_total: str,
    tps: str,
    tvq: str,
) -> FactureEnregistree:
    return FactureEnregistree(
        identifiant=identifiant,
        numero=f"F-{identifiant}",
        date="2026-09-01",
        fournisseur=fournisseur,
        client="Client",
        sous_total=Decimal(sous_total),
        tps=Decimal(tps),
        tvq=Decimal(tvq),
        total=Decimal(total),
        date_creation="2026-09-01 12:00:00",
    )


def test_calculer_resume() -> None:
    resume = calculer_resume(
        [
            facture(
                1,
                "Alpha",
                "114.98",
                "100.00",
                "5.00",
                "9.98",
            ),
            facture(
                2,
                "Beta",
                "229.96",
                "200.00",
                "10.00",
                "19.96",
            ),
            facture(
                3,
                "Alpha",
                "57.49",
                "50.00",
                "2.50",
                "4.99",
            ),
        ]
    )

    assert resume.nombre_factures == 3
    assert resume.sous_total == Decimal("350.00")
    assert resume.tps == Decimal("17.50")
    assert resume.tvq == Decimal("34.93")
    assert resume.total == Decimal("402.43")
    assert resume.total_par_fournisseur[0] == (
        "Beta",
        Decimal("229.96"),
    )
    assert resume.total_par_fournisseur[1] == (
        "Alpha",
        Decimal("172.47"),
    )


def test_calculer_resume_vide() -> None:
    resume = calculer_resume([])

    assert resume.nombre_factures == 0
    assert resume.total == Decimal("0")
    assert resume.total_par_fournisseur == ()

def test_filtrer_factures_periode() -> None:
    """Les factures hors période sont exclues."""
    factures = [
        facture(
            1,
            "Alpha",
            "114.98",
            "100.00",
            "5.00",
            "9.98",
        ),
        facture(
            2,
            "Beta",
            "229.96",
            "200.00",
            "10.00",
            "19.96",
        ),
    ]

    factures[0] = FactureEnregistree(
        **{
            **factures[0].__dict__,
            "date": "2026-08-15",
        }
    )
    factures[1] = FactureEnregistree(
        **{
            **factures[1].__dict__,
            "date": "2026-09-10",
        }
    )

    resultat = filtrer_factures_periode(
        factures,
        "2026-09-01",
        "2026-09-30",
    )

    assert len(resultat) == 1
    assert resultat[0].identifiant == 2


def test_filtrer_factures_sans_bornes() -> None:
    """Sans dates, toutes les factures datées sont conservées."""
    factures = [
        facture(
            1,
            "Alpha",
            "114.98",
            "100.00",
            "5.00",
            "9.98",
        )
    ]

    assert filtrer_factures_periode(
        factures
    ) == factures


def test_refuser_periode_inversee() -> None:
    """Une période inversée est refusée."""
    import pytest

    with pytest.raises(
        ValueError,
        match="date de début",
    ):
        filtrer_factures_periode(
            [],
            "2026-09-30",
            "2026-09-01",
        )

def test_filtrer_factures_fournisseur() -> None:
    """Seules les factures du fournisseur choisi sont conservées."""
    factures = [
        facture(
            1,
            "Alpha",
            "114.98",
            "100.00",
            "5.00",
            "9.98",
        ),
        facture(
            2,
            "Beta",
            "229.96",
            "200.00",
            "10.00",
            "19.96",
        ),
        facture(
            3,
            "Alpha",
            "57.49",
            "50.00",
            "2.50",
            "4.99",
        ),
    ]

    resultat = filtrer_factures_fournisseur(
        factures,
        "Alpha",
    )

    assert [element.identifiant for element in resultat] == [1, 3]


def test_filtrer_factures_fournisseur_vide() -> None:
    """Sans fournisseur, toutes les factures sont conservées."""
    factures = [
        facture(
            1,
            "Alpha",
            "114.98",
            "100.00",
            "5.00",
            "9.98",
        )
    ]

    assert filtrer_factures_fournisseur(
        factures,
        None,
    ) == factures

