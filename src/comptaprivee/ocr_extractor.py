"""Extraction locale du texte contenu dans des images."""

import os
import shutil
import subprocess
from pathlib import Path


FORMATS_IMAGES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}


def extraire_texte_image(
    chemin_fichier: str | Path,
    langues: str = "fra+eng",
) -> str:
    """Extrait le texte d'une image avec Tesseract local."""
    chemin = Path(chemin_fichier)

    if chemin.suffix.lower() not in FORMATS_IMAGES:
        raise ValueError("Format d'image non pris en charge.")

    if not chemin.exists():
        raise FileNotFoundError(f"Fichier introuvable : {chemin}")

    executable = shutil.which("tesseract")

    if executable is None:
        raise RuntimeError("Tesseract OCR est introuvable sur cet ordinateur.")

    commande = [
        executable,
        str(chemin),
        "stdout",
        "-l",
        langues,
        "--psm",
        "6",
    ]

    environnement = os.environ.copy()

    resultat = subprocess.run(
        commande,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=environnement,
        check=False,
    )

    if resultat.returncode != 0:
        message = resultat.stderr.strip() or "Erreur OCR inconnue."
        raise RuntimeError(f"Échec de Tesseract OCR : {message}")

    return resultat.stdout.strip()