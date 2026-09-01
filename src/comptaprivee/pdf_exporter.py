"""Export local du détail d'une facture au format PDF."""

from pathlib import Path

import fitz

from .facture_parser import DonneesFacture


def _texte(valeur: str | None) -> str:
    """Retourne une valeur lisible pour le PDF."""
    return valeur or "Non renseigne"


def _montant(valeur) -> str:
    """Formate un montant comptable en CAD."""
    if valeur is None:
        return "Non renseigne"
    return f"{valeur:.2f} CAD"


def exporter_facture_pdf(
    facture: DonneesFacture,
    chemin_sortie: str | Path,
    *,
    identifiant: int | None = None,
    date_enregistrement: str | None = None,
) -> Path:
    """Cree localement un PDF contenant le detail d'une facture."""
    chemin = Path(chemin_sortie)

    if chemin.suffix.lower() != ".pdf":
        raise ValueError("Le fichier de sortie doit etre au format PDF.")

    chemin.parent.mkdir(parents=True, exist_ok=True)

    document = fitz.open()
    try:
        page = document.new_page(width=595, height=842)
        page.insert_text((50, 60), "ComptaPrivee AI", fontsize=20, fontname="helv")
        page.insert_text((50, 84), "Detail de facture - export local", fontsize=11, fontname="helv")
        page.draw_line((50, 100), (545, 100), width=0.8)

        informations = [
            ("Identifiant", "Non renseigne" if identifiant is None else str(identifiant)),
            ("Numero de facture", _texte(facture.numero)),
            ("Date", _texte(facture.date)),
            ("Fournisseur", _texte(facture.fournisseur)),
            ("Client", _texte(facture.client)),
            ("Sous-total", _montant(facture.sous_total)),
            ("TPS", _montant(facture.tps)),
            ("TVQ", _montant(facture.tvq)),
            ("Total", _montant(facture.total)),
            ("Enregistree le", _texte(date_enregistrement)),
        ]

        y = 135
        for libelle, valeur in informations:
            page.insert_text((55, y), f"{libelle} :", fontsize=10, fontname="helv")
            rectangle = fitz.Rect(200, y - 12, 535, y + 18)
            page.insert_textbox(rectangle, valeur, fontsize=10, fontname="helv")
            y += 45

        page.draw_line((50, y + 5), (545, y + 5), width=0.8)
        page.insert_text(
            (50, y + 35),
            "Document genere localement. Aucune donnee envoyee sur Internet.",
            fontsize=9,
            fontname="helv",
        )

        document.set_metadata(
            {
                "title": f"Facture {facture.numero or 'sans numero'}",
                "author": "ComptaPrivee AI",
                "subject": "Detail de facture comptable",
                "creator": "ComptaPrivee AI",
            }
        )

        document.save(chemin, garbage=4, deflate=True)
    finally:
        document.close()

    return chemin
