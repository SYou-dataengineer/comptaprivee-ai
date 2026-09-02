"""Tests de validation fiscale avancée."""

from decimal import Decimal

from src.comptaprivee.facture_parser import DonneesFacture
from src.comptaprivee.tax_validator import valider_fiscalite


def facture_base(**remplacements) -> DonneesFacture:
    donnees = dict(
        numero="FAC-TAX-001",
        date="2026-09-01",
        fournisseur="Fournisseur Exemple",
        client="Client Exemple",
        sous_total=Decimal("1000.00"),
        tps=Decimal("50.00"),
        tvq=Decimal("99.75"),
        total=Decimal("1149.75"),
    )
    donnees.update(remplacements)
    return DonneesFacture(**donnees)


def test_fiscalite_valide() -> None:
    resultat = valider_fiscalite(facture_base())

    assert resultat.valide is True
    assert resultat.erreurs == ()


def test_detecter_tps_incorrecte() -> None:
    resultat = valider_fiscalite(
        facture_base(tps=Decimal("40.00"))
    )

    assert resultat.valide is False
    assert any("TPS incohérente" in e for e in resultat.erreurs)


def test_detecter_tvq_incorrecte() -> None:
    resultat = valider_fiscalite(
        facture_base(tvq=Decimal("90.00"))
    )

    assert resultat.valide is False
    assert any("TVQ incohérente" in e for e in resultat.erreurs)


def test_detecter_total_incorrect() -> None:
    resultat = valider_fiscalite(
        facture_base(total=Decimal("1200.00"))
    )

    assert resultat.valide is False
    assert any("Total incohérent" in e for e in resultat.erreurs)


def test_signaler_taxes_manquantes() -> None:
    resultat = valider_fiscalite(
        facture_base(tps=None, tvq=None)
    )

    assert resultat.valide is True
    assert len(resultat.avertissements) == 2

def test_fusion_validation_fiscale_valide() -> None:
    from src.comptaprivee.invoice_validator import valider_facture
    from src.comptaprivee.tax_validator import appliquer_validation_fiscale

    facture = facture_base()
    validation = appliquer_validation_fiscale(
        facture,
        valider_facture(facture),
    )

    assert validation.est_valide is True


def test_fusion_validation_fiscale_bloque_tps_incorrecte() -> None:
    from src.comptaprivee.invoice_validator import (
        StatutValidation,
        valider_facture,
    )
    from src.comptaprivee.tax_validator import appliquer_validation_fiscale

    facture = facture_base(tps=Decimal("40.00"), total=Decimal("1139.75"))
    validation = appliquer_validation_fiscale(
        facture,
        valider_facture(facture),
    )

    assert validation.statut is StatutValidation.ERREUR
    assert any(
        "TPS incohérente" in message
        for message in validation.erreurs
    )


def test_fusion_validation_fiscale_taxe_manquante_a_verifier() -> None:
    from src.comptaprivee.invoice_validator import (
        StatutValidation,
        valider_facture,
    )
    from src.comptaprivee.tax_validator import appliquer_validation_fiscale

    facture = facture_base(tps=None, tvq=None)
    validation = appliquer_validation_fiscale(
        facture,
        valider_facture(facture),
    )

    assert validation.statut is StatutValidation.A_VERIFIER
    assert any(
        "TPS manquante" in message
        for message in validation.avertissements
    )
