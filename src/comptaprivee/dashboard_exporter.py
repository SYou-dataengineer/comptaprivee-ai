"""Export local du tableau de bord comptable en CSV et PDF."""

import csv
from pathlib import Path

import fitz

from .company_profile import (
    lignes_coordonnees,
    lire_nom_societe,
    lire_profil_societe,
)
from .dashboard import ResumeTableauBord


def _inserer_logo_pdf(
    page: fitz.Page,
    logo_path: str,
    rectangle: fitz.Rect,
) -> None:
    if not logo_path:
        return

    chemin = Path(logo_path)

    if not chemin.exists() or not chemin.is_file():
        return

    try:
        page.insert_image(
            rectangle,
            filename=str(chemin),
            keep_proportion=True,
            overlay=True,
        )
    except (OSError, RuntimeError, ValueError):
        return


def exporter_tableau_bord_csv(
    resume: ResumeTableauBord,
    chemin_sortie: str | Path,
    *,
    date_debut: str | None = None,
    date_fin: str | None = None,
    fournisseur: str | None = None,
) -> Path:
    """Exporte les indicateurs du tableau de bord dans un CSV local."""
    chemin = Path(chemin_sortie)

    if chemin.suffix.lower() != ".csv":
        raise ValueError(
            "Le fichier de sortie doit etre au format CSV."
        )

    chemin.parent.mkdir(parents=True, exist_ok=True)

    with chemin.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as fichier:
        writer = csv.writer(fichier)

        writer.writerow(
            ["Rapport tableau de bord ComptaPrivee AI"]
        )
        writer.writerow(
            ["Societe comptable", lire_nom_societe() or "Societe comptable"]
        )
        writer.writerow(["Date debut", date_debut or "Toutes"])
        writer.writerow(["Date fin", date_fin or "Toutes"])
        writer.writerow(
            ["Fournisseur", fournisseur or "Tous les fournisseurs"]
        )
        writer.writerow([])

        writer.writerow(["Indicateur", "Valeur"])
        writer.writerow(["Factures", resume.nombre_factures])
        writer.writerow(["Sous-total", f"{resume.sous_total:.2f}"])
        writer.writerow(["TPS", f"{resume.tps:.2f}"])
        writer.writerow(["TVQ", f"{resume.tvq:.2f}"])
        writer.writerow(["Total", f"{resume.total:.2f}"])
        writer.writerow([])

        writer.writerow(["Fournisseur", "Total CAD"])

        for nom, total in resume.total_par_fournisseur:
            writer.writerow([nom, f"{total:.2f}"])

    return chemin


def exporter_tableau_bord_pdf(
    resume: ResumeTableauBord,
    chemin_sortie: str | Path,
    *,
    date_debut: str | None = None,
    date_fin: str | None = None,
    fournisseur: str | None = None,
) -> Path:
    """Exporte un rapport PDF local du tableau de bord."""
    chemin = Path(chemin_sortie)

    if chemin.suffix.lower() != ".pdf":
        raise ValueError(
            "Le fichier de sortie doit etre au format PDF."
        )

    chemin.parent.mkdir(parents=True, exist_ok=True)

    document = fitz.open()

    try:
        page = document.new_page(width=595, height=842)

        page.insert_text(
            (45, 55),
            "ComptaPrivee AI",
            fontsize=20,
            fontname="helv",
        )
        page.insert_text(
            (45, 82),
            "Rapport du tableau de bord comptable",
            fontsize=13,
            fontname="helv",
        )
        profil_societe = lire_profil_societe()

        _inserer_logo_pdf(
            page,
            profil_societe.logo_path,
            fitz.Rect(215, 14, 335, 88),
        )
        nom_societe = (
            lire_nom_societe()
            or profil_societe.nom_societe
            or "Societe comptable"
        )
        page.insert_textbox(
            fitz.Rect(320, 28, 550, 48),
            nom_societe,
            fontsize=10,
            fontname="helv",
            align=fitz.TEXT_ALIGN_RIGHT,
        )
        y_societe = 50
        for ligne_societe in lignes_coordonnees(profil_societe)[:3]:
            page.insert_textbox(
                fitz.Rect(320, y_societe, 550, y_societe + 12),
                ligne_societe,
                fontsize=7,
                fontname="helv",
                align=fitz.TEXT_ALIGN_RIGHT,
            )
            y_societe += 11
        page.draw_line((45, 96), (550, 96), width=0.8)

        filtres = [
            ("Date debut", date_debut or "Toutes"),
            ("Date fin", date_fin or "Toutes"),
            (
                "Fournisseur",
                fournisseur or "Tous les fournisseurs",
            ),
        ]

        y = 125
        for libelle, valeur in filtres:
            page.insert_text(
                (50, y),
                f"{libelle} : {valeur}",
                fontsize=10,
                fontname="helv",
            )
            y += 22

        y += 15
        page.insert_text(
            (50, y),
            "Indicateurs",
            fontsize=13,
            fontname="helv",
        )
        y += 28

        indicateurs = [
            ("Factures", str(resume.nombre_factures)),
            ("Sous-total", f"{resume.sous_total:.2f} CAD"),
            ("TPS", f"{resume.tps:.2f} CAD"),
            ("TVQ", f"{resume.tvq:.2f} CAD"),
            ("Total", f"{resume.total:.2f} CAD"),
        ]

        for libelle, valeur in indicateurs:
            page.insert_text(
                (60, y),
                f"{libelle} : {valeur}",
                fontsize=11,
                fontname="helv",
            )
            y += 25

        y += 15
        page.insert_text(
            (50, y),
            "Totaux par fournisseur",
            fontsize=13,
            fontname="helv",
        )
        y += 28

        if resume.total_par_fournisseur:
            for nom, total in resume.total_par_fournisseur:
                if y > 790:
                    page = document.new_page(
                        width=595,
                        height=842,
                    )
                    y = 55

                page.insert_textbox(
                    fitz.Rect(60, y - 12, 390, y + 14),
                    nom,
                    fontsize=10,
                    fontname="helv",
                )
                page.insert_text(
                    (410, y),
                    f"{total:.2f} CAD",
                    fontsize=10,
                    fontname="helv",
                )
                y += 24
        else:
            page.insert_text(
                (60, y),
                "Aucune facture pour les filtres selectionnes.",
                fontsize=10,
                fontname="helv",
            )

        document.set_metadata(
            {
                "title": "Tableau de bord ComptaPrivee AI",
                "author": "ComptaPrivee AI",
                "subject": "Rapport comptable local",
                "creator": "ComptaPrivee AI",
            }
        )

        document.save(
            chemin,
            garbage=4,
            deflate=True,
        )

    finally:
        document.close()

    return chemin
