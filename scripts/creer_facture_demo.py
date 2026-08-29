"""Génère une facture PDF fictive pour la démonstration locale."""

from pathlib import Path

import fitz


def creer_facture_demo() -> Path:
    """Crée une facture fictive ne contenant aucune donnée réelle."""
    chemin_sortie = Path("data/documents/facture_demo.pdf")
    chemin_sortie.parent.mkdir(parents=True, exist_ok=True)

    document = fitz.open()
    page = document.new_page()

    contenu = (
        "FACTURE FICTIVE - DEMONSTRATION\n\n"
        "Numero : FAC-2026-001\n"
        "Date : 2026-08-29\n"
        "Fournisseur : Entreprise Exemple Quebec Inc.\n"
        "Client : Client Fictif Inc.\n\n"
        "Description : Services professionnels\n"
        "Sous-total : 1000.00 CAD\n"
        "TPS : 50.00 CAD\n"
        "TVQ : 99.75 CAD\n"
        "Total : 1149.75 CAD\n"
    )

    page.insert_text((72, 72), contenu, fontsize=12)
    document.save(chemin_sortie)
    document.close()

    return chemin_sortie


if __name__ == "__main__":
    chemin = creer_facture_demo()
    print(f"Facture fictive créée : {chemin}")