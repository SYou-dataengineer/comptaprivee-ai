"""Conversions locales de documents pour ComptaPrivée AI."""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from pathlib import Path

import fitz


EXTENSIONS_WORD = {".doc", ".docx"}
EXTENSIONS_EXCEL = {".xls", ".xlsx", ".xlsm"}
EXTENSIONS_IMAGES = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}

CONVERSIONS_SUPPORTEES = (
    "Word → PDF",
    "Excel → PDF",
    "Excel → CSV",
    "CSV → Excel",
    "Image → PDF",
    "PDF → CSV",
    "PDF → Excel",
    "PDF → Word",
)


class ErreurConversion(RuntimeError):
    """Erreur contrôlée lors d'une conversion locale."""


@dataclass(frozen=True)
class ResultatConversion:
    """Résultat d'une conversion locale."""

    source: Path
    destination: Path
    type_conversion: str


def _verifier_source(
    source: str | Path,
    extensions: set[str],
) -> Path:
    chemin = Path(source)

    if not chemin.exists():
        raise FileNotFoundError(
            f"Fichier source introuvable : {chemin}"
        )

    if chemin.suffix.lower() not in extensions:
        attendues = ", ".join(sorted(extensions))
        raise ValueError(
            f"Format source non pris en charge. Formats attendus : {attendues}"
        )

    return chemin


def _preparer_destination(
    source: Path,
    destination: str | Path | None,
    extension: str,
) -> Path:
    if destination is None:
        chemin = source.with_suffix(extension)
    else:
        chemin = Path(destination)

    if chemin.suffix.lower() != extension:
        raise ValueError(
            f"Le fichier de destination doit avoir l'extension {extension}."
        )

    chemin.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    return chemin


def word_vers_pdf(
    source: str | Path,
    destination: str | Path | None = None,
) -> ResultatConversion:
    """Convertit Word en PDF via Microsoft Word installé sur Windows."""
    source_path = _verifier_source(
        source,
        EXTENSIONS_WORD,
    )
    destination_path = _preparer_destination(
        source_path,
        destination,
        ".pdf",
    )

    if sys.platform != "win32":
        raise ErreurConversion(
            "Word → PDF nécessite Windows et Microsoft Word installé."
        )

    try:
        import win32com.client  # type: ignore
    except ImportError as erreur:
        raise ErreurConversion(
            "Word → PDF nécessite le module pywin32. "
            "Installez les dépendances du projet."
        ) from erreur

    word = None

    try:
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0

        document = word.Documents.Open(
            str(source_path.resolve()),
            ReadOnly=True,
        )
        try:
            document.ExportAsFixedFormat(
                str(destination_path.resolve()),
                17,
            )
        finally:
            document.Close(False)

    except Exception as erreur:
        raise ErreurConversion(
            f"Impossible de convertir le document Word : {erreur}"
        ) from erreur

    finally:
        if word is not None:
            word.Quit()

    return ResultatConversion(
        source=source_path,
        destination=destination_path,
        type_conversion="Word → PDF",
    )


def excel_vers_pdf(
    source: str | Path,
    destination: str | Path | None = None,
) -> ResultatConversion:
    """Convertit Excel en PDF, une feuille visible = une page PDF."""
    source_path = _verifier_source(
        source,
        EXTENSIONS_EXCEL,
    )
    destination_path = _preparer_destination(
        source_path,
        destination,
        ".pdf",
    )

    if sys.platform != "win32":
        raise ErreurConversion(
            "Excel → PDF nécessite Windows et Microsoft Excel installé."
        )

    try:
        import win32com.client  # type: ignore
    except ImportError as erreur:
        raise ErreurConversion(
            "Excel → PDF nécessite le module pywin32. "
            "Installez les dépendances du projet."
        ) from erreur

    excel = None

    try:
        excel = win32com.client.DispatchEx("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False
        excel.ScreenUpdating = False
        excel.EnableEvents = False

        classeur = excel.Workbooks.Open(
            str(source_path.resolve()),
            ReadOnly=True,
            UpdateLinks=0,
        )

        try:
            feuilles_exportees = 0

            for feuille in classeur.Worksheets:
                # Ignorer les feuilles masquées.
                if feuille.Visible != -1:
                    continue

                # Trouver la vraie zone de contenu.
                # UsedRange peut être artificiellement énorme à cause
                # d'anciens formats, ce qui produit un PDF minuscule.
                premiere_cellule = feuille.Cells.Find(
                    What="*",
                    After=feuille.Cells(1, 1),
                    LookIn=-4163,      # xlFormulas
                    LookAt=2,         # xlPart
                    SearchOrder=1,    # xlByRows
                    SearchDirection=1 # xlNext
                )

                derniere_ligne = feuille.Cells.Find(
                    What="*",
                    After=feuille.Cells(1, 1),
                    LookIn=-4163,
                    LookAt=2,
                    SearchOrder=1,     # xlByRows
                    SearchDirection=2, # xlPrevious
                )

                derniere_colonne = feuille.Cells.Find(
                    What="*",
                    After=feuille.Cells(1, 1),
                    LookIn=-4163,
                    LookAt=2,
                    SearchOrder=2,     # xlByColumns
                    SearchDirection=2, # xlPrevious
                )

                if (
                    premiere_cellule is None
                    or derniere_ligne is None
                    or derniere_colonne is None
                ):
                    continue

                premiere_ligne = premiere_cellule.Row

                premiere_colonne_cellule = feuille.Cells.Find(
                    What="*",
                    After=feuille.Cells(1, 1),
                    LookIn=-4163,
                    LookAt=2,
                    SearchOrder=2,    # xlByColumns
                    SearchDirection=1 # xlNext
                )

                if premiere_colonne_cellule is None:
                    continue

                premiere_colonne = premiere_colonne_cellule.Column
                derniere_ligne_no = derniere_ligne.Row
                derniere_colonne_no = derniere_colonne.Column

                zone = feuille.Range(
                    feuille.Cells(
                        premiere_ligne,
                        premiere_colonne,
                    ),
                    feuille.Cells(
                        derniere_ligne_no,
                        derniere_colonne_no,
                    ),
                )

                try:
                    excel.PrintCommunication = False
                except Exception:
                    pass

                try:
                    feuille.PageSetup.PrintArea = zone.Address

                    # Une feuille Excel visible = exactement une page PDF.
                    feuille.PageSetup.Zoom = False
                    feuille.PageSetup.FitToPagesWide = 1
                    feuille.PageSetup.FitToPagesTall = 1

                    largeur_points = float(zone.Width)
                    hauteur_points = float(zone.Height)

                    # Orientation réellement basée sur les dimensions
                    # visuelles du contenu, pas seulement le nombre de cellules.
                    feuille.PageSetup.Orientation = (
                        2 if largeur_points > hauteur_points else 1
                    )

                    # Papier Letter : format courant au Canada.
                    feuille.PageSetup.PaperSize = 1

                    # Marges compactes mais propres.
                    feuille.PageSetup.LeftMargin = excel.InchesToPoints(0.20)
                    feuille.PageSetup.RightMargin = excel.InchesToPoints(0.20)
                    feuille.PageSetup.TopMargin = excel.InchesToPoints(0.25)
                    feuille.PageSetup.BottomMargin = excel.InchesToPoints(0.25)
                    feuille.PageSetup.HeaderMargin = 0
                    feuille.PageSetup.FooterMargin = 0

                    feuille.PageSetup.CenterHorizontally = True
                    feuille.PageSetup.CenterVertically = True

                    # Évite des pages supplémentaires dues aux titres répétés.
                    feuille.PageSetup.PrintTitleRows = ""
                    feuille.PageSetup.PrintTitleColumns = ""

                    feuilles_exportees += 1

                finally:
                    try:
                        excel.PrintCommunication = True
                    except Exception:
                        pass

            if feuilles_exportees == 0:
                raise ErreurConversion(
                    "Aucune feuille Excel visible contenant des données "
                    "n'a été trouvée."
                )

            # Toutes les feuilles visibles configurées sont exportées :
            # chacune tient sur une page PDF.
            classeur.ExportAsFixedFormat(
                0,
                str(destination_path.resolve()),
                0,
                True,
                False,
            )

        finally:
            classeur.Close(False)

    except ErreurConversion:
        raise

    except Exception as erreur:
        message = str(erreur)

        if (
            "Document not saved" in message
            or "Document non enregistré" in message
        ):
            raise ErreurConversion(
                "Impossible d'enregistrer le PDF. "
                "Fermez le PDF de destination s'il est déjà ouvert, "
                "ou choisissez un autre nom de fichier."
            ) from erreur

        raise ErreurConversion(
            f"Impossible de convertir le classeur Excel : {erreur}"
        ) from erreur

    finally:
        if excel is not None:
            try:
                excel.ScreenUpdating = True
                excel.EnableEvents = True
            except Exception:
                pass
            excel.Quit()

    return ResultatConversion(
        source=source_path,
        destination=destination_path,
        type_conversion="Excel → PDF",
    )


def excel_vers_csv(
    source: str | Path,
    destination: str | Path | None = None,
) -> ResultatConversion:
    """Convertit la feuille active d'un fichier Excel en CSV UTF-8."""
    source_path = _verifier_source(
        source,
        EXTENSIONS_EXCEL,
    )
    destination_path = _preparer_destination(
        source_path,
        destination,
        ".csv",
    )

    try:
        from openpyxl import load_workbook
    except ImportError as erreur:
        raise ErreurConversion(
            "Excel → CSV nécessite openpyxl. "
            "Installez les dépendances du projet."
        ) from erreur

    try:
        classeur = load_workbook(
            source_path,
            data_only=True,
            read_only=False,
        )
        feuille = classeur.active

        # Si la feuille contient un vrai tableau Excel, on exporte
        # uniquement ce tableau. Cela évite les notes ou contenus annexes
        # placés plus bas dans la feuille.
        plage = None

        if feuille.tables:
            premier_tableau = next(iter(feuille.tables.values()))
            plage = premier_tableau.ref

        if plage:
            cellules = feuille[plage]
        else:
            # Sinon, on détecte la zone réellement utilisée en ignorant
            # les lignes et colonnes complètement vides autour des données.
            lignes_non_vides = []
            for ligne in feuille.iter_rows():
                if any(cellule.value is not None for cellule in ligne):
                    lignes_non_vides.append(ligne)

            if not lignes_non_vides:
                raise ErreurConversion(
                    "La feuille Excel ne contient aucune donnée à exporter."
                )

            min_row = min(cellule.row for ligne in lignes_non_vides for cellule in ligne if cellule.value is not None)
            max_row = max(cellule.row for ligne in lignes_non_vides for cellule in ligne if cellule.value is not None)
            min_col = min(cellule.column for ligne in lignes_non_vides for cellule in ligne if cellule.value is not None)
            max_col = max(cellule.column for ligne in lignes_non_vides for cellule in ligne if cellule.value is not None)

            cellules = feuille.iter_rows(
                min_row=min_row,
                max_row=max_row,
                min_col=min_col,
                max_col=max_col,
            )

        with destination_path.open(
            "w",
            encoding="utf-8-sig",
            newline="",
        ) as fichier_csv:
            writer = csv.writer(fichier_csv)

            for ligne in cellules:
                valeurs = []

                for cellule in ligne:
                    valeur = cellule.value

                    if valeur is None:
                        valeurs.append("")
                    elif hasattr(valeur, "strftime"):
                        valeurs.append(
                            valeur.strftime("%Y-%m-%d")
                        )
                    else:
                        valeurs.append(valeur)

                writer.writerow(valeurs)

        classeur.close()

    except Exception as erreur:
        raise ErreurConversion(
            f"Impossible de convertir Excel en CSV : {erreur}"
        ) from erreur

    return ResultatConversion(
        source=source_path,
        destination=destination_path,
        type_conversion="Excel → CSV",
    )


def image_vers_pdf(
    source: str | Path,
    destination: str | Path | None = None,
) -> ResultatConversion:
    """Convertit une image prise en charge en PDF local."""
    source_path = _verifier_source(
        source,
        EXTENSIONS_IMAGES,
    )
    destination_path = _preparer_destination(
        source_path,
        destination,
        ".pdf",
    )

    document = fitz.open()

    try:
        image = fitz.open(source_path)
        try:
            pdf_bytes = image.convert_to_pdf()
        finally:
            image.close()

        pdf_image = fitz.open(
            "pdf",
            pdf_bytes,
        )
        try:
            document.insert_pdf(pdf_image)
        finally:
            pdf_image.close()

        document.save(destination_path)

    except Exception as erreur:
        raise ErreurConversion(
            f"Impossible de convertir l'image en PDF : {erreur}"
        ) from erreur

    finally:
        document.close()

    return ResultatConversion(
        source=source_path,
        destination=destination_path,
        type_conversion="Image → PDF",
    )


def csv_vers_excel(
    source: str | Path,
    destination: str | Path | None = None,
) -> ResultatConversion:
    source_path = _verifier_source(source, {".csv"})
    destination_path = _preparer_destination(
        source_path, destination, ".xlsx"
    )
    from openpyxl import Workbook

    with source_path.open("r", encoding="utf-8-sig", newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        except csv.Error:
            dialect = csv.excel
        rows = list(csv.reader(f, dialect))

    if not rows:
        raise ErreurConversion("Le fichier CSV est vide.")

    wb = Workbook()
    ws = wb.active
    ws.title = "Données"
    for row in rows:
        ws.append(row)
    for cell in ws[1]:
        cell.font = cell.font.copy(bold=True)
    wb.save(destination_path)

    return ResultatConversion(
        source=source_path,
        destination=destination_path,
        type_conversion="CSV → Excel",
    )


def _extraire_tableaux_pdf(source_path: Path):
    """Extrait les tableaux natifs détectables dans un PDF."""
    document = fitz.open(source_path)
    resultats = []

    try:
        for page_no, page in enumerate(document, start=1):
            detection = page.find_tables()

            for table_no, table in enumerate(
                detection.tables,
                start=1,
            ):
                data = table.extract()

                if data and any(
                    any(v not in (None, "") for v in row)
                    for row in data
                ):
                    resultats.append(
                        (page_no, table_no, data)
                    )
    finally:
        document.close()

    return resultats


def _extraire_ocr_pages_pdf(
    source_path: Path,
) -> dict[int, str]:
    """OCR local uniquement des pages PDF qui en ont besoin."""
    from tempfile import TemporaryDirectory

    from .ocr_extractor import extraire_texte_image
    from .ocr_normalizer import normaliser_montants_ocr
    from .pdf_type_detector import analyser_pdf

    analyse = analyser_pdf(source_path)

    if not analyse.necessite_ocr:
        return {}

    pages_ocr = set(analyse.pages_ocr)
    textes: dict[int, str] = {}

    with fitz.open(source_path) as document:
        with TemporaryDirectory(
            prefix="comptaprivee_conversion_ocr_"
        ) as dossier_temporaire:
            dossier = Path(dossier_temporaire)

            for numero_page, page in enumerate(
                document,
                start=1,
            ):
                if numero_page not in pages_ocr:
                    continue

                image_path = dossier / f"page_{numero_page}.png"

                pixmap = page.get_pixmap(
                    dpi=300,
                    alpha=False,
                )
                pixmap.save(image_path)

                texte = normaliser_montants_ocr(
                    extraire_texte_image(
                        image_path
                    ).strip()
                )

                if texte:
                    textes[numero_page] = texte

    return textes


def pdf_vers_csv(
    source: str | Path,
    destination: str | Path | None = None,
) -> ResultatConversion:
    """Convertit les tableaux PDF en CSV avec fallback OCR local."""
    source_path = _verifier_source(
        source,
        {".pdf"},
    )
    destination_path = _preparer_destination(
        source_path,
        destination,
        ".csv",
    )

    tables = _extraire_tableaux_pdf(source_path)
    textes_ocr = _extraire_ocr_pages_pdf(source_path)

    if not tables and not textes_ocr:
        raise ErreurConversion(
            "Aucun tableau structuré ni texte OCR exploitable "
            "n'a été détecté dans ce PDF."
        )

    with destination_path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as fichier:
        writer = csv.writer(fichier)

        for idx, (
            page_no,
            table_no,
            data,
        ) in enumerate(tables):
            if len(tables) > 1 or textes_ocr:
                writer.writerow(
                    [
                        f"Page {page_no} - "
                        f"Tableau {table_no}"
                    ]
                )

            for row in data:
                writer.writerow(
                    [
                        "" if valeur is None else valeur
                        for valeur in row
                    ]
                )

            writer.writerow([])

        # Un scan sans structure de tableau fiable est exporté
        # sous forme Page / Ligne / Texte OCR plutôt que d'inventer
        # des colonnes comptables.
        for page_no in sorted(textes_ocr):
            writer.writerow(
                ["Page", "Ligne", "Texte OCR"]
            )

            lignes = [
                ligne.strip()
                for ligne in textes_ocr[page_no].splitlines()
                if ligne.strip()
            ]

            for numero_ligne, ligne in enumerate(
                lignes,
                start=1,
            ):
                writer.writerow(
                    [
                        page_no,
                        numero_ligne,
                        ligne,
                    ]
                )

            writer.writerow([])

    return ResultatConversion(
        source=source_path,
        destination=destination_path,
        type_conversion="PDF → CSV",
    )


def pdf_vers_excel(
    source: str | Path,
    destination: str | Path | None = None,
) -> ResultatConversion:
    """Convertit tableaux PDF et pages OCR en classeur Excel."""
    source_path = _verifier_source(
        source,
        {".pdf"},
    )
    destination_path = _preparer_destination(
        source_path,
        destination,
        ".xlsx",
    )

    from copy import copy
    from openpyxl import Workbook

    tables = _extraire_tableaux_pdf(source_path)
    textes_ocr = _extraire_ocr_pages_pdf(source_path)

    if not tables and not textes_ocr:
        raise ErreurConversion(
            "Aucun tableau structuré ni texte OCR exploitable "
            "n'a été détecté dans ce PDF."
        )

    wb = Workbook()
    wb.remove(wb.active)

    for page_no, table_no, data in tables:
        ws = wb.create_sheet(
            title=f"P{page_no}_T{table_no}"[:31]
        )

        for row in data:
            ws.append(
                [
                    "" if valeur is None else valeur
                    for valeur in row
                ]
            )

        if ws.max_row:
            for cell in ws[1]:
                nouvelle_police = copy(cell.font)
                nouvelle_police.bold = True
                cell.font = nouvelle_police

        for colonne in ws.columns:
            largeur = max(
                len(str(cell.value or ""))
                for cell in colonne
            )
            lettre = colonne[0].column_letter
            ws.column_dimensions[lettre].width = min(
                max(10, largeur + 2),
                45,
            )

    for page_no in sorted(textes_ocr):
        ws = wb.create_sheet(
            title=f"OCR_Page_{page_no}"[:31]
        )
        ws.append(
            ["Page", "Ligne", "Texte OCR"]
        )

        lignes = [
            ligne.strip()
            for ligne in textes_ocr[page_no].splitlines()
            if ligne.strip()
        ]

        for numero_ligne, ligne in enumerate(
            lignes,
            start=1,
        ):
            ws.append(
                [
                    page_no,
                    numero_ligne,
                    ligne,
                ]
            )

        for cell in ws[1]:
            nouvelle_police = copy(cell.font)
            nouvelle_police.bold = True
            cell.font = nouvelle_police

        ws.column_dimensions["A"].width = 10
        ws.column_dimensions["B"].width = 10
        ws.column_dimensions["C"].width = 80

    wb.save(destination_path)

    return ResultatConversion(
        source=source_path,
        destination=destination_path,
        type_conversion="PDF → Excel",
    )


def pdf_vers_word(
    source: str | Path,
    destination: str | Path | None = None,
) -> ResultatConversion:
    """Convertit PDF natif/mixte/scanné en Word avec OCR local."""
    source_path = _verifier_source(
        source,
        {".pdf"},
    )
    destination_path = _preparer_destination(
        source_path,
        destination,
        ".docx",
    )

    try:
        from docx import Document
        from docx.enum.table import WD_TABLE_ALIGNMENT
        from docx.enum.text import WD_ALIGN_PARAGRAPH
    except ImportError as erreur:
        raise ErreurConversion(
            "PDF → Word nécessite python-docx."
        ) from erreur

    textes_ocr = _extraire_ocr_pages_pdf(
        source_path
    )
    pdf = fitz.open(source_path)

    try:
        document_word = Document()
        contenu_trouve = False

        for index_page, page in enumerate(pdf):
            numero_page = index_page + 1

            if index_page > 0:
                document_word.add_page_break()

            detection = page.find_tables()
            zones_tableaux = []
            tableaux = []

            for tableau in detection.tables:
                donnees = tableau.extract()

                if not donnees:
                    continue

                if not any(
                    any(v not in (None, "") for v in ligne)
                    for ligne in donnees
                ):
                    continue

                zones_tableaux.append(
                    fitz.Rect(tableau.bbox)
                )
                tableaux.append(donnees)

            blocs = page.get_text(
                "blocks",
                sort=True,
            )

            for bloc in blocs:
                rect_bloc = fitz.Rect(
                    bloc[0],
                    bloc[1],
                    bloc[2],
                    bloc[3],
                )

                if any(
                    rect_bloc.intersects(zone)
                    for zone in zones_tableaux
                ):
                    continue

                texte = str(bloc[4]).strip()

                if not texte:
                    continue

                contenu_trouve = True

                for ligne in texte.splitlines():
                    ligne = ligne.strip()

                    if ligne:
                        document_word.add_paragraph(
                            ligne
                        )

            for donnees in tableaux:
                nb_colonnes = max(
                    len(ligne)
                    for ligne in donnees
                )

                tableau_word = document_word.add_table(
                    rows=0,
                    cols=nb_colonnes,
                )
                tableau_word.style = "Table Grid"
                tableau_word.alignment = (
                    WD_TABLE_ALIGNMENT.CENTER
                )

                for numero_ligne, ligne in enumerate(
                    donnees
                ):
                    cellules = tableau_word.add_row().cells

                    for numero_colonne in range(
                        nb_colonnes
                    ):
                        valeur = (
                            ligne[numero_colonne]
                            if numero_colonne < len(ligne)
                            else ""
                        )
                        cellules[
                            numero_colonne
                        ].text = (
                            ""
                            if valeur is None
                            else str(valeur)
                        )

                        for paragraphe in cellules[
                            numero_colonne
                        ].paragraphs:
                            paragraphe.alignment = (
                                WD_ALIGN_PARAGRAPH.LEFT
                            )

                            if numero_ligne == 0:
                                for run in paragraphe.runs:
                                    run.bold = True

                contenu_trouve = True

            # Si la page est un scan, ajouter son texte OCR.
            texte_ocr = textes_ocr.get(
                numero_page,
                "",
            ).strip()

            if texte_ocr:
                document_word.add_paragraph(
                    "Texte reconnu par OCR"
                ).runs[0].bold = True

                for ligne in texte_ocr.splitlines():
                    ligne = ligne.strip()

                    if ligne:
                        document_word.add_paragraph(
                            ligne
                        )

                contenu_trouve = True

        if not contenu_trouve:
            raise ErreurConversion(
                "Aucun texte, tableau ou résultat OCR "
                "n'a été détecté dans ce PDF."
            )

        document_word.save(
            destination_path
        )

    except ErreurConversion:
        raise
    except Exception as erreur:
        raise ErreurConversion(
            f"Impossible de convertir PDF en Word : {erreur}"
        ) from erreur
    finally:
        pdf.close()

    return ResultatConversion(
        source=source_path,
        destination=destination_path,
        type_conversion="PDF → Word",
    )


def convertir_document(
    type_conversion: str,
    source: str | Path,
    destination: str | Path | None = None,
) -> ResultatConversion:
    """Route une conversion vers le moteur correspondant."""
    conversions = {
        "Word → PDF": word_vers_pdf,
        "Excel → PDF": excel_vers_pdf,
        "Excel → CSV": excel_vers_csv,
        "CSV → Excel": csv_vers_excel,
        "Image → PDF": image_vers_pdf,
        "PDF → CSV": pdf_vers_csv,
        "PDF → Excel": pdf_vers_excel,
        "PDF → Word": pdf_vers_word,
    }

    fonction = conversions.get(type_conversion)

    if fonction is None:
        raise ValueError(
            f"Conversion non prise en charge : {type_conversion}"
        )

    return fonction(
        source,
        destination,
    )
