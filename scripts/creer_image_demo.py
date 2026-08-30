"""Génère une facture fictive au format PNG pour tester l'OCR."""

from pathlib import Path

import fitz


def creer_image_demo() -> Path:
    """Crée une image de facture ne contenant aucune donnée réelle."""
    chemin_sortie = Path("data/documents/facture_image_demo.png")
    chemin_sortie.parent.mkdir(parents=True, exist_ok=True)

    document = fitz.open()
    page = document.new_page(width=595, height=842)

    contenu = (
        "FACTURE IMAGE FICTIVE\n\n"
        "Numero : IMG-2026-001\n"
        "Date : 2026-08-30\n"
        "Fournisseur : Entreprise Image Exemple Inc.\n"
        "Client : Client Image Fictif Inc.\n\n"
        "Sous-total : 3000.00 CAD\n"
        "TPS : 150.00 CAD\n"
        "TVQ : 299.25 CAD\n"
        "Total : 3449.25 CAD\n"
    )

    page.insert_text(
        (60, 80),
        contenu,
        fontsize=18,
        lineheight=1.5,
    )

    image = page.get_pixmap(dpi=300, alpha=False)
    image.save(chemin_sortie)
    document.close()

    return chemin_sortie


if __name__ == "__main__":
    chemin = creer_image_demo()
    print(f"Facture image fictive créée : {chemin}")