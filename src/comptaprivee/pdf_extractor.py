"""Extraction locale du texte contenu dans les fichiers PDF."""

from pathlib import Path
from tempfile import TemporaryDirectory

import fitz

from .ocr_extractor import extraire_texte_image
from .ocr_normalizer import normaliser_montants_ocr
from .pdf_type_detector import analyser_pdf


def extraire_texte_pdf(chemin_fichier: str | Path) -> str:
    """Extrait le texte d'un PDF et applique l'OCR page par page si nécessaire."""
    chemin = Path(chemin_fichier)

    if chemin.suffix.lower() != ".pdf":
        raise ValueError("Le fichier doit être au format PDF.")

    if not chemin.exists():
        raise FileNotFoundError(
            f"Fichier introuvable : {chemin}"
        )

    analyse = analyser_pdf(chemin)
    pages_ocr = set(analyse.pages_ocr)
    textes_pages: list[str] = []

    with fitz.open(chemin) as document:
        with TemporaryDirectory(
            prefix="comptaprivee_ocr_"
        ) as dossier_temporaire:
            for numero_page, page in enumerate(
                document,
                start=1,
            ):
                texte = page.get_text("text").strip()

                if numero_page not in pages_ocr:
                    if texte:
                        textes_pages.append(texte)
                    continue

                chemin_image = (
                    Path(dossier_temporaire)
                    / f"page_{numero_page}.png"
                )

                image = page.get_pixmap(
                    dpi=300,
                    alpha=False,
                )
                image.save(chemin_image)

                texte_ocr = normaliser_montants_ocr(
                    extraire_texte_image(
                        chemin_image
                    ).strip()
                )

                # Sur une page mixte, conserver aussi le texte PDF déjà présent
                # si l'OCR produit du contenu complémentaire.
                if texte and texte_ocr:
                    textes_pages.append(
                        texte + "\n" + texte_ocr
                    )
                elif texte_ocr:
                    textes_pages.append(texte_ocr)
                elif texte:
                    textes_pages.append(texte)

    separateur_pages = "\n\n--- Page suivante ---\n\n"
    return separateur_pages.join(textes_pages)
