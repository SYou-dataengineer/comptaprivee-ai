"""Tests de l'extraction structurée des factures."""

from decimal import Decimal

from src.comptaprivee.facture_parser import extraire_donnees_facture


def test_extraire_tous_les_champs_facture() -> None:
    """Vérifie l'extraction des champs d'une facture complète."""
    texte = """
    FACTURE FICTIVE
    Numero : FAC-2026-001
    Date : 2026-08-29
    Fournisseur : Entreprise Exemple Quebec Inc.
    Client : Client Fictif Inc.
    Sous-total : 1000.00 CAD
    TPS : 50.00 CAD
    TVQ : 99.75 CAD
    Total : 1149.75 CAD
    """

    facture = extraire_donnees_facture(texte)

    assert facture.numero == "FAC-2026-001"
    assert facture.date == "2026-08-29"
    assert facture.fournisseur == "Entreprise Exemple Quebec Inc."
    assert facture.client == "Client Fictif Inc."
    assert facture.sous_total == Decimal("1000.00")
    assert facture.tps == Decimal("50.00")
    assert facture.tvq == Decimal("99.75")
    assert facture.total == Decimal("1149.75")


def test_accepter_les_montants_avec_virgule() -> None:
    """Vérifie les montants utilisant la notation française."""
    texte = """
    Numero : FAC-002
    Total : 1 149,75 CAD
    """

    facture = extraire_donnees_facture(texte)

    assert facture.numero == "FAC-002"
    assert facture.total == Decimal("1149.75")
    assert facture.tps is None

def test_facture_multi_page_ne_melange_pas_les_pages() -> None:
    from src.comptaprivee.facture_parser import extraire_donnees_facture

    texte = (
        "Fournisseur : Page Un Inc.\n"
        "Total : 344.93 CAD"
        "\n\n--- Page suivante ---\n\n"
        "Facture : FAC-SCAN-001\n"
        "Fournisseur : Fournisseur Scan Inc.\n"
        "Date : 2026-09-02\n"
        "Sous-total : 250.00 CAD\n"
        "TPS : 12.50 CAD\n"
        "TVQ : 24.94 CAD\n"
        "Total : 287.44 CAD"
    )

    facture = extraire_donnees_facture(texte)

    assert facture.numero == "FAC-SCAN-001"
    assert facture.fournisseur == "Fournisseur Scan Inc."
    assert str(facture.sous_total) == "250.00"
    assert str(facture.tvq) == "24.94"
    assert str(facture.total) == "287.44"


def test_facture_alias_facture_devient_numero() -> None:
    from src.comptaprivee.facture_parser import extraire_donnees_facture

    facture = extraire_donnees_facture(
        "Facture : FAC-777\n"
        "Total : 10.00 CAD"
    )

    assert facture.numero == "FAC-777"


def test_facture_page_coherente_est_preferee() -> None:
    from src.comptaprivee.facture_parser import extraire_donnees_facture

    texte = (
        "Facture : MAUVAISE\n"
        "Sous-total : 250.00 CAD\n"
        "TPS : 12.50 CAD\n"
        "TVQ : 24.94 CAD\n"
        "Total : 344.93 CAD"
        "\n\n--- Page suivante ---\n\n"
        "Facture : BONNE\n"
        "Sous-total : 250.00 CAD\n"
        "TPS : 12.50 CAD\n"
        "TVQ : 24.94 CAD\n"
        "Total : 287.44 CAD"
    )

    facture = extraire_donnees_facture(texte)

    assert facture.numero == "BONNE"
    assert str(facture.total) == "287.44"

