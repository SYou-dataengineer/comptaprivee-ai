from pathlib import Path

from src.comptaprivee.tax_document_classifier import (
    TYPE_A_VERIFIER,
    TYPE_NON_RECONNU,
    TYPE_RL1,
    TYPE_T4,
    classifier_document_fiscal,
)


def test_t4_reconnu_par_nom_fichier() -> None:
    resultat = classifier_document_fiscal(Path("T4_Client_Test.pdf"))
    assert resultat.type_document == TYPE_T4
    assert resultat.confiance >= 65


def test_t4_reconnu_par_texte_francais() -> None:
    resultat = classifier_document_fiscal(
        "document.pdf",
        "T4 État de la rémunération payée Case 14 Case 22",
    )
    assert resultat.type_document == TYPE_T4
    assert resultat.confiance >= 70


def test_t4_reconnu_par_texte_anglais() -> None:
    resultat = classifier_document_fiscal(
        "document.pdf",
        "T4 Statement of Remuneration Paid Employment income Box 14",
    )
    assert resultat.type_document == TYPE_T4


def test_rl1_reconnu_par_nom_fichier() -> None:
    resultat = classifier_document_fiscal(Path("RL-1_Client_Test.pdf"))
    assert resultat.type_document == TYPE_RL1
    assert resultat.confiance >= 65


def test_rl1_reconnu_par_releve_1_dans_nom() -> None:
    resultat = classifier_document_fiscal(Path("Releve 1 Client.pdf"))
    assert resultat.type_document == TYPE_RL1


def test_rl1_reconnu_par_texte() -> None:
    resultat = classifier_document_fiscal(
        "document.pdf",
        (
            "Relevé 1 Revenus d'emploi et revenus divers "
            "Revenu Québec Case A"
        ),
    )
    assert resultat.type_document == TYPE_RL1
    assert resultat.confiance >= 80


def test_document_generique_reste_non_reconnu() -> None:
    resultat = classifier_document_fiscal(
        "facture_demo.pdf",
        "Facture fournisseur total TPS TVQ",
    )
    assert resultat.type_document == TYPE_NON_RECONNU


def test_document_ambigu_est_a_verifier() -> None:
    resultat = classifier_document_fiscal(
        "document.pdf",
        (
            "T4 Relevé 1 Statement of Remuneration Paid "
            "Revenus d'emploi et revenus divers"
        ),
    )
    assert resultat.type_document == TYPE_A_VERIFIER
