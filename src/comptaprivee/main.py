"""Point d'entrée de ComptaPrivée AI."""

import argparse
from decimal import Decimal
from pathlib import Path

from .csv_exporter import exporter_facture_csv
from .facture_parser import extraire_donnees_facture
from .pdf_extractor import extraire_texte_pdf
from .word_extractor import extraire_texte_word

def afficher_bienvenue() -> None:
    """Affiche les informations principales de l'application."""
    print("=" * 55)
    print("ComptaPrivée AI")
    print("Agent local d'extraction de documents comptables")
    print("=" * 55)
    print("Mode : 100 % local")
    print("Confidentialité : aucune donnée envoyée sur Internet")


def formater_montant(montant: Decimal | None) -> str:
    """Formate un montant comptable pour l'affichage."""
    if montant is None:
        return "Non détecté"

    return f"{montant:.2f} CAD"

def extraire_texte_document(chemin: Path) -> str:
    """Sélectionne le lecteur local selon le format du document."""
    extension = chemin.suffix.lower()

    if extension == ".pdf":
        return extraire_texte_pdf(chemin)

    if extension == ".docx":
        return extraire_texte_word(chemin)

    raise ValueError("Formats acceptés : PDF et DOCX.")

def analyser_document(
    chemin_fichier: str | Path,
    chemin_csv: str | Path | None = None,
) -> None:
    """Extrait, affiche et exporte les données d'un PDF."""
    chemin = Path(chemin_fichier)
    texte = extraire_texte_document(chemin)

    print()
    print(f"Document analysé : {chemin.name}")
    print("-" * 55)

    if not texte:
        print("Aucun texte détecté dans ce document.")
        return

    print(texte)

    facture = extraire_donnees_facture(texte)

    print()
    print("Données structurées")
    print("-" * 55)
    print(f"Numéro de facture : {facture.numero or 'Non détecté'}")
    print(f"Date : {facture.date or 'Non détectée'}")
    print(f"Fournisseur : {facture.fournisseur or 'Non détecté'}")
    print(f"Client : {facture.client or 'Non détecté'}")
    print(f"Sous-total : {formater_montant(facture.sous_total)}")
    print(f"TPS : {formater_montant(facture.tps)}")
    print(f"TVQ : {formater_montant(facture.tvq)}")
    print(f"Total : {formater_montant(facture.total)}")

    if chemin_csv is not None:
        fichier_exporte = exporter_facture_csv(facture, chemin_csv)
        print()
        print(f"Export CSV créé : {fichier_exporte}")


def creer_analyseur_arguments() -> argparse.ArgumentParser:
    """Crée les arguments acceptés par la ligne de commande."""
    analyseur = argparse.ArgumentParser(
        description="Extraction locale de documents comptables PDF et Word DOCX."
    )
    analyseur.add_argument(
        "document",
        nargs="?",
        help="Chemin du document PDF ou DOCX à analyser.",
    )
    analyseur.add_argument(
        "--export-csv",
        dest="chemin_csv",
        help="Chemin du fichier CSV à créer localement.",
    )
    return analyseur


def main() -> None:
    """Lance l'application."""
    arguments = creer_analyseur_arguments().parse_args()

    afficher_bienvenue()

    if arguments.document:
        analyser_document(arguments.document, arguments.chemin_csv)
    else:
        print("État : environnement prêt")
        print("Utilisez --help pour afficher les commandes disponibles.")


if __name__ == "__main__":
    main()