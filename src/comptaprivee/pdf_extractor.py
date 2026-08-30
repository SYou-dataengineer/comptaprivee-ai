"""Extraction locale du texte contenu dans les fichiers PDF."""

from pathlib import Path
from tempfile import TemporaryDirectory

import fitz

from .ocr_extractor import extraire_texte_image


def extraire_texte_pdf(chemin_fichier: str | Path) -> str:
    """Extrait le texte d'un PDF et utilise l'OCR si nécessaire."""
    chemin = Path(chemin_fichier)

    if chemin.suffix.lower() != ".pdf":
        raise ValueError("Le fichier doit être au format PDF.")

    if not chemin.exists():
        raise FileNotFoundError(f"Fichier introuvable : {chemin}")

    textes_pages: list[str] = []

    with fitz.open(chemin) as document:
        with TemporaryDirectory(prefix="comptaprivee_ocr_") as dossier_temporaire:
            for numero_page, page in enumerate(document, start=1):
                texte = page.get_text("text").strip()

                if texte:
                    textes_pages.append(texte)
                    continue

                chemin_image = (
                    Path(dossier_temporaire)
                    / f"page_{numero_page}.png"
                )

                image = page.get_pixmap(dpi=300, alpha=False)
                image.save(chemin_image)

                texte_ocr = extraire_texte_image(chemin_image).strip()

                if texte_ocr:
                    textes_pages.append(texte_ocr)

    return "\n".join(textes_pages)