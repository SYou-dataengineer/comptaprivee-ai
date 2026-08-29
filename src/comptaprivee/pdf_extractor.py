"""Extraction locale du texte contenu dans les fichiers PDF."""

from pathlib import Path

import fitz


def extraire_texte_pdf(chemin_fichier: str | Path) -> str:
    """Extrait localement le texte de toutes les pages d'un PDF."""
    chemin = Path(chemin_fichier)

    if chemin.suffix.lower() != ".pdf":
        raise ValueError("Le fichier doit être au format PDF.")

    if not chemin.exists():
        raise FileNotFoundError(f"Fichier introuvable : {chemin}")

    textes_pages: list[str] = []

    with fitz.open(chemin) as document:
        for page in document:
            texte = page.get_text("text").strip()

            if texte:
                textes_pages.append(texte)

    return "\n".join(textes_pages)