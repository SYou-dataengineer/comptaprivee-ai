"""Détection locale de tableaux dans les PDF pour ComptaPrivée AI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz


@dataclass(frozen=True)
class TableauPDF:
    """Tableau détecté sur une page PDF."""

    numero_page: int
    numero_tableau: int
    lignes: list[list[str]]


def _nettoyer_cellule(valeur: object) -> str:
    """Normalise une cellule extraite d'un tableau PDF."""
    if valeur is None:
        return ""

    texte = str(valeur)
    texte = " ".join(texte.replace("\n", " ").split())
    return texte.strip()


def _extraire_tableau_ocr_page_pdf(
    page,
    numero_page: int,
) -> list[list[str]]:
    # Rend une page PDF en image temporaire puis applique Tesseract.
    import tempfile

    from .ocr_table_extractor import extraire_tableau_image_tesseract

    matrice = fitz.Matrix(4.0, 4.0)
    pixmap = page.get_pixmap(
        matrix=matrice,
        alpha=False,
    )

    with tempfile.NamedTemporaryFile(
        suffix=".png",
        delete=False,
    ) as fichier_temp:
        chemin_temp = Path(fichier_temp.name)

    try:
        pixmap.save(chemin_temp)

        return extraire_tableau_image_tesseract(
            str(chemin_temp),
        )

    finally:
        try:
            chemin_temp.unlink(missing_ok=True)
        except Exception:
            pass


def extraire_tableaux_pdf(
    source: str | Path,
    *,
    pages: str = "",
) -> list[TableauPDF]:
    """Détecte les tableaux natifs d'un PDF page par page."""
    from .document_converter import _normaliser_pages_selection

    chemin = Path(source)

    if not chemin.exists():
        raise FileNotFoundError(
            f"Fichier source introuvable : {chemin}"
        )

    if chemin.suffix.lower() != ".pdf":
        raise ValueError(
            "Le fichier source doit être un PDF."
        )

    tableaux: list[TableauPDF] = []

    try:
        with fitz.open(chemin) as document:
            if document.page_count == 0:
                return []

            pages_selectionnees = _normaliser_pages_selection(
                pages,
                document.page_count,
            )

            for index_page in pages_selectionnees:
                page = document[index_page]
                tableaux_page: list[TableauPDF] = []

                try:
                    resultat = page.find_tables()
                except AttributeError as erreur:
                    raise RuntimeError(
                        "Cette version de PyMuPDF ne prend pas en charge "
                        "la détection de tableaux."
                    ) from erreur

                for index_tableau, tableau in enumerate(
                    resultat.tables,
                    start=1,
                ):
                    brut = tableau.extract()

                    if not brut:
                        continue

                    lignes = [
                        [_nettoyer_cellule(cellule) for cellule in ligne]
                        for ligne in brut
                    ]

                    if not any(
                        any(cellule for cellule in ligne)
                        for ligne in lignes
                    ):
                        continue

                    tableaux_page.append(
                        TableauPDF(
                            numero_page=index_page + 1,
                            numero_tableau=index_tableau,
                            lignes=lignes,
                        )
                    )

                # Si aucun tableau natif n'est détecté, tenter une
                # reconstruction OCR de la page scannée.
                if not tableaux_page:
                    texte_natif = page.get_text("text").strip()
                    contient_images = bool(page.get_images(full=True))

                    if len(texte_natif) < 40 or contient_images:
                        lignes_ocr = _extraire_tableau_ocr_page_pdf(
                            page,
                            index_page + 1,
                        )

                        if lignes_ocr:
                            tableaux_page.append(
                                TableauPDF(
                                    numero_page=index_page + 1,
                                    numero_tableau=1,
                                    lignes=lignes_ocr,
                                )
                            )

                tableaux.extend(tableaux_page)

    except (FileNotFoundError, ValueError, RuntimeError):
        raise

    except Exception as erreur:
        raise RuntimeError(
            f"Impossible d'analyser les tableaux du PDF : {erreur}"
        ) from erreur

    return tableaux


def compter_tableaux_pdf(
    source: str | Path,
    *,
    pages: str = "",
) -> int:
    """Retourne le nombre de tableaux détectés."""
    return len(extraire_tableaux_pdf(source, pages=pages))
