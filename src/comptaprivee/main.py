"""Point d'entrée de ComptaPrivée AI."""

import argparse
from pathlib import Path

from .pdf_extractor import extraire_texte_pdf


def afficher_bienvenue() -> None:
    """Affiche les informations principales de l'application."""
    print("=" * 55)
    print("ComptaPrivée AI")
    print("Agent local d'extraction de documents comptables")
    print("=" * 55)
    print("Mode : 100 % local")
    print("Confidentialité : aucune donnée envoyée sur Internet")


def analyser_pdf(chemin_fichier: str | Path) -> None:
    """Extrait et affiche le texte d'un PDF local."""
    chemin = Path(chemin_fichier)
    texte = extraire_texte_pdf(chemin)

    print()
    print(f"Document analysé : {chemin.name}")
    print("-" * 55)

    if texte:
        print(texte)
    else:
        print("Aucun texte détecté dans ce document.")


def creer_analyseur_arguments() -> argparse.ArgumentParser:
    """Crée les arguments acceptés par la ligne de commande."""
    analyseur = argparse.ArgumentParser(
        description="Extraction locale de documents comptables PDF."
    )
    analyseur.add_argument(
        "pdf",
        nargs="?",
        help="Chemin du fichier PDF à analyser.",
    )
    return analyseur


def main() -> None:
    """Lance l'application."""
    arguments = creer_analyseur_arguments().parse_args()

    afficher_bienvenue()

    if arguments.pdf:
        analyser_pdf(arguments.pdf)
    else:
        print("État : environnement prêt")
        print("Utilisez --help pour afficher les commandes disponibles.")


if __name__ == "__main__":
    main()