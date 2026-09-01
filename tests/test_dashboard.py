"""Tests du tableau de bord comptable."""

from decimal import Decimal

from src.comptaprivee.dashboard import (
    calculer_taxes_mensuelles,
    calculer_totaux_mensuels,
    ResumeTableauBord,
    calculer_resume,
    filtrer_factures_fournisseur,
    filtrer_factures_periode,
    preparer_totaux_fournisseurs_graphique,
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

def test_preparer_totaux_fournisseurs_graphique() -> None:
    """Le graphique conserve les principaux fournisseurs."""
    resume = ResumeTableauBord(
        nombre_factures=3,
        sous_total=Decimal("300.00"),
        tps=Decimal("15.00"),
        tvq=Decimal("29.93"),
        total=Decimal("344.93"),
        total_par_fournisseur=(
            ("Alpha", Decimal("200.00")),
            ("Beta", Decimal("100.00")),
            ("Gamma", Decimal("44.93")),
        ),
    )

    resultat = preparer_totaux_fournisseurs_graphique(
        resume,
        limite=2,
    )

    assert resultat == (
        ("Alpha", Decimal("200.00")),
        ("Beta", Decimal("100.00")),
    )


def test_refuser_limite_graphique_invalide() -> None:
    """Une limite de graphique invalide est refusée."""
    import pytest

    resume = ResumeTableauBord(
        nombre_factures=0,
        sous_total=Decimal("0"),
        tps=Decimal("0"),
        tvq=Decimal("0"),
        total=Decimal("0"),
        total_par_fournisseur=(),
    )

    with pytest.raises(
        ValueError,
        match="supérieure à zéro",
    ):
        preparer_totaux_fournisseurs_graphique(
            resume,
            limite=0,
        )

def test_calculer_totaux_mensuels() -> None:
    """Les factures sont regroupées par mois dans l'ordre."""
    facture_a = facture(
        1,
        "Alpha",
        "114.98",
        "100.00",
        "5.00",
        "9.98",
    )
    facture_b = facture(
        2,
        "Beta",
        "229.96",
        "200.00",
        "10.00",
        "19.96",
    )
    facture_c = facture(
        3,
        "Gamma",
        "57.49",
        "50.00",
        "2.50",
        "4.99",
    )

    facture_a = FactureEnregistree(
        **{
            **facture_a.__dict__,
            "date": "2026-08-05",
        }
    )
    facture_b = FactureEnregistree(
        **{
            **facture_b.__dict__,
            "date": "2026-08-20",
        }
    )
    facture_c = FactureEnregistree(
        **{
            **facture_c.__dict__,
            "date": "2026-09-01",
        }
    )

    resultat = calculer_totaux_mensuels(
        [facture_c, facture_b, facture_a]
    )

    assert resultat == (
        ("2026-08", Decimal("344.94")),
        ("2026-09", Decimal("57.49")),
    )


def test_calculer_totaux_mensuels_ignore_dates_invalides() -> None:
    """Les factures sans date exploitable sont ignorées."""
    facture_invalide = facture(
        1,
        "Alpha",
        "114.98",
        "100.00",
        "5.00",
        "9.98",
    )

    facture_invalide = FactureEnregistree(
        **{
            **facture_invalide.__dict__,
            "date": "date-invalide",
        }
    )

    assert calculer_totaux_mensuels(
        [facture_invalide]
    ) == ()

def test_calculer_taxes_mensuelles() -> None:
    """La TPS et la TVQ sont regroupées par mois."""
    facture_a = facture(
        1,
        "Alpha",
        "114.98",
        "100.00",
        "5.00",
        "9.98",
    )
    facture_b = facture(
        2,
        "Beta",
        "229.96",
        "200.00",
        "10.00",
        "19.96",
    )
    facture_c = facture(
        3,
        "Gamma",
        "57.49",
        "50.00",
        "2.50",
        "4.99",
    )

    facture_a = FactureEnregistree(
        **{
            **facture_a.__dict__,
            "date": "2026-08-05",
        }
    )
    facture_b = FactureEnregistree(
        **{
            **facture_b.__dict__,
            "date": "2026-08-20",
        }
    )
    facture_c = FactureEnregistree(
        **{
            **facture_c.__dict__,
            "date": "2026-09-01",
        }
    )

    resultat = calculer_taxes_mensuelles(
        [facture_c, facture_b, facture_a]
    )

    assert resultat == (
        (
            "2026-08",
            Decimal("15.00"),
            Decimal("29.94"),
        ),
        (
            "2026-09",
            Decimal("2.50"),
            Decimal("4.99"),
        ),
    )


def test_calculer_taxes_mensuelles_ignore_dates_invalides() -> None:
    """Les dates invalides sont ignorées dans les taxes mensuelles."""
    facture_invalide = facture(
        1,
        "Alpha",
        "114.98",
        "100.00",
        "5.00",
        "9.98",
    )

    facture_invalide = FactureEnregistree(
        **{
            **facture_invalide.__dict__,
            "date": "invalide",
        }
    )

    assert calculer_taxes_mensuelles(
        [facture_invalide]
    ) == ()

