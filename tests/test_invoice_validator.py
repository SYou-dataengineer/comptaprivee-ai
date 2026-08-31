"""Tests de la validation locale des factures."""

from decimal import Decimal

from src.comptaprivee.facture_parser import DonneesFacture
from src.comptaprivee.invoice_validator import (
    StatutValidation,
    valider_facture,
)


def creer_facture_valide() -> DonneesFacture:
    """Crée une facture dont les données sont cohérentes."""
    return DonneesFacture(
        numero="VALIDATION-001",
        date="2026-08-31",
        fournisseur="Entreprise Validation Exemple Inc.",
        client="Client Validation Fictif Inc.",
        sous_total=Decimal("1000.00"),
        tps=Decimal("50.00"),
        tvq=Decimal("99.75"),
        total=Decimal("1149.75"),
    )


def test_accepter_une_facture_valide() -> None:
    """Vérifie qu'une facture cohérente est déclarée valide."""
    facture = creer_facture_valide()

    resultat = valider_facture(facture)

    assert resultat.statut == StatutValidation.VALIDE
    assert resultat.est_valide
    assert resultat.autorise_export
    assert resultat.erreurs == ()
    assert resultat.avertissements == ()


def test_signaler_un_champ_obligatoire_manquant() -> None:
    """Vérifie qu'un champ absent demande une vérification."""
    facture = DonneesFacture(
        numero="VALIDATION-002",
        date=None,
        fournisseur="Entreprise Validation Exemple Inc.",
        client="Client Validation Fictif Inc.",
        sous_total=Decimal("1000.00"),
        tps=Decimal("50.00"),
        tvq=Decimal("99.75"),
        total=Decimal("1149.75"),
    )

    resultat = valider_facture(facture)

    assert resultat.statut == StatutValidation.A_VERIFIER
    assert not resultat.est_valide
    assert resultat.autorise_export
    assert not resultat.erreurs
    assert any(
        "date" in avertissement.lower()
        for avertissement in resultat.avertissements
    )


def test_refuser_un_total_incoherent() -> None:
    """Vérifie qu'une erreur de calcul bloque l'export."""
    facture = DonneesFacture(
        numero="VALIDATION-003",
        date="2026-08-31",
        fournisseur="Entreprise Validation Exemple Inc.",
        client="Client Validation Fictif Inc.",
        sous_total=Decimal("1000.00"),
        tps=Decimal("50.00"),
        tvq=Decimal("99.75"),
        total=Decimal("1200.00"),
    )

    resultat = valider_facture(facture)

    assert resultat.statut == StatutValidation.ERREUR
    assert not resultat.est_valide
    assert not resultat.autorise_export
    assert any(
        "incohérent" in erreur
        for erreur in resultat.erreurs
    )


def test_refuser_un_montant_negatif() -> None:
    """Vérifie qu'un montant négatif bloque l'export."""
    facture = DonneesFacture(
        numero="VALIDATION-004",
        date="2026-08-31",
        fournisseur="Entreprise Validation Exemple Inc.",
        client="Client Validation Fictif Inc.",
        sous_total=Decimal("1000.00"),
        tps=Decimal("-5.00"),
        tvq=Decimal("99.75"),
        total=Decimal("1094.75"),
    )

    resultat = valider_facture(facture)

    assert resultat.statut == StatutValidation.ERREUR
    assert not resultat.autorise_export
    assert any(
        "négatif" in erreur
        for erreur in resultat.erreurs
    )