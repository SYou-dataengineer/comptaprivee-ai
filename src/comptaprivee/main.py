"""Point d'entrée de ComptaPrivée AI."""


def afficher_bienvenue() -> None:
    """Affiche les informations principales de l'application."""
    print("=" * 55)
    print("ComptaPrivée AI")
    print("Agent local d'extraction de documents comptables")
    print("=" * 55)
    print("Mode : 100 % local")
    print("Confidentialité : aucune donnée envoyée sur Internet")
    print("État : environnement prêt")


if __name__ == "__main__":
    afficher_bienvenue()