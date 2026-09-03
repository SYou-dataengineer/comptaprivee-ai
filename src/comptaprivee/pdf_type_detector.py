"""Détection locale du type de contenu d'un PDF."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz


SEUIL_TEXTE_PAGE = 40


@dataclass(frozen=True)
class AnalysePagePDF:
    """Résultat de détection pour une page PDF."""

    numero_page: int
    nombre_caracteres: int
    nombre_images: int
    type_page: str

    @property
    def necessite_ocr(self) -> bool:
        return self.type_page in {"scan", "mixte_faible"}


@dataclass(frozen=True)
class AnalysePDF:
    """Résumé de la nature d'un document PDF."""

    chemin: Path
    pages: tuple[AnalysePagePDF, ...]
    type_document: str

    @property
    def necessite_ocr(self) -> bool:
        return any(page.necessite_ocr for page in self.pages)

    @property
    def pages_ocr(self) -> tuple[int, ...]:
        return tuple(
            page.numero_page
            for page in self.pages
            if page.necessite_ocr
        )


def analyser_pdf(
    chemin_fichier: str | Path,
    seuil_texte: int = SEUIL_TEXTE_PAGE,
) -> AnalysePDF:
    """Détermine si un PDF est texte, scanné ou mixte."""
    chemin = Path(chemin_fichier)

    if chemin.suffix.lower() != ".pdf":
        raise ValueError("Le fichier doit être au format PDF.")

    if not chemin.exists():
        raise FileNotFoundError(
            f"Fichier introuvable : {chemin}"
        )

    if seuil_texte < 1:
        raise ValueError(
            "Le seuil de texte doit être supérieur à zéro."
        )

    pages: list[AnalysePagePDF] = []

    with fitz.open(chemin) as document:
        for numero_page, page in enumerate(
            document,
            start=1,
        ):
            texte = page.get_text("text").strip()
            nombre_caracteres = len(
                "".join(texte.split())
            )
            nombre_images = len(
                page.get_images(full=True)
            )

            if nombre_caracteres >= seuil_texte:
                type_page = "texte"
            elif nombre_images > 0 and nombre_caracteres == 0:
                type_page = "scan"
            elif nombre_images > 0:
                type_page = "mixte_faible"
            elif nombre_caracteres > 0:
                type_page = "texte_faible"
            else:
                type_page = "vide"

            pages.append(
                AnalysePagePDF(
                    numero_page=numero_page,
                    nombre_caracteres=nombre_caracteres,
                    nombre_images=nombre_images,
                    type_page=type_page,
                )
            )

    types = {page.type_page for page in pages}

    if not pages:
        type_document = "vide"
    elif types <= {"texte", "texte_faible", "vide"}:
        type_document = "texte"
    elif types <= {"scan", "vide"}:
        type_document = "scan"
    else:
        type_document = "mixte"

    return AnalysePDF(
        chemin=chemin,
        pages=tuple(pages),
        type_document=type_document,
    )
