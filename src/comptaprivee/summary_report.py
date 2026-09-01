"""Résumé comptable imprimable et exportable."""

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import fitz

from .anomalies import detecter_anomalies
from .company_profile import (
    lignes_coordonnees,
    lire_nom_societe,
    lire_profil_societe,
)
from .dashboard import ResumeTableauBord
from .database import FactureEnregistree
from .settings import (
    couleur_hex_vers_pdf,
    formater_date_rapport,
    lire_parametres,
    texte_rapport,
)


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


@dataclass(frozen=True)
class ResumeComptableImprimable:
    """Résumé synthétique prêt à être affiché ou exporté."""

    nombre_factures: int
    sous_total: Decimal
    tps: Decimal
    tvq: Decimal
    total: Decimal
    nombre_anomalies: int
    fournisseur_principal: str
    total_fournisseur_principal: Decimal
    periode: str
    societe_comptable: str


def construire_resume_comptable(
    factures: list[FactureEnregistree],
    resume: ResumeTableauBord,
    *,
    date_debut: str | None = None,
    date_fin: str | None = None,
) -> ResumeComptableImprimable:
    """Construit un résumé comptable à partir des filtres actifs."""
    anomalies = detecter_anomalies(factures)

    if resume.total_par_fournisseur:
        fournisseur_principal, total_principal = (
            resume.total_par_fournisseur[0]
        )
    else:
        fournisseur_principal = "Aucun"
        total_principal = Decimal("0")

    parametres = lire_parametres()
    debut = (
        formater_date_rapport(
            date_debut,
            parametres.format_date,
        )
        if date_debut
        else texte_rapport("toutes", parametres.langue_rapports)
    )
    fin = (
        formater_date_rapport(
            date_fin,
            parametres.format_date,
        )
        if date_fin
        else texte_rapport("toutes", parametres.langue_rapports)
    )

    if date_debut or date_fin:
        liaison = texte_rapport("au", parametres.langue_rapports)
        periode = f"{debut} {liaison} {fin}"
    else:
        periode = texte_rapport(
            "toutes_periodes",
            parametres.langue_rapports,
        )

    return ResumeComptableImprimable(
        nombre_factures=resume.nombre_factures,
        sous_total=resume.sous_total,
        tps=resume.tps,
        tvq=resume.tvq,
        total=resume.total,
        nombre_anomalies=len(anomalies),
        fournisseur_principal=fournisseur_principal,
        total_fournisseur_principal=total_principal,
        periode=periode,
        societe_comptable=(
            lire_nom_societe() or "Société comptable"
        ),
    )


def exporter_resume_comptable_pdf(
    resume: ResumeComptableImprimable,
    chemin_sortie: str | Path,
) -> Path:
    """Exporte un résumé comptable professionnel dans un PDF local."""
    chemin = Path(chemin_sortie)

    if chemin.suffix.lower() != ".pdf":
        raise ValueError(
            "Le fichier de sortie doit être au format PDF."
        )

    chemin.parent.mkdir(parents=True, exist_ok=True)

    document = fitz.open()

    try:
        page = document.new_page(width=595, height=842)

        parametres = lire_parametres()
        langue = parametres.langue_rapports
        devise = parametres.devise

        bleu = couleur_hex_vers_pdf(parametres.couleur_pdf)
        bleu_clair = (0.93, 0.96, 1.00)
        vert = (0.08, 0.45, 0.22)
        orange = (0.78, 0.36, 0.06)
        gris = (0.30, 0.34, 0.40)
        gris_clair = (0.95, 0.96, 0.97)
        blanc = (1.00, 1.00, 1.00)

        # Bandeau principal.
        page.draw_rect(
            fitz.Rect(0, 0, 595, 105),
            color=bleu,
            fill=bleu,
        )

        page.insert_text(
            (42, 48),
            "ComptaPrivee AI",
            fontsize=22,
            fontname="helv",
            color=blanc,
        )
        page.insert_text(
            (42, 76),
            texte_rapport("resume", langue),
            fontsize=13,
            fontname="helv",
            color=blanc,
        )
        profil_societe = lire_profil_societe()

        _inserer_logo_pdf(
            page,
            profil_societe.logo_path,
            fitz.Rect(215, 12, 335, 90),
        )
        nom_societe = (
            profil_societe.nom_societe
            or resume.societe_comptable
        )

        largeur_nom = fitz.get_text_length(
            nom_societe,
            fontname="helv",
            fontsize=10.5,
        )
        page.insert_text(
            (553 - largeur_nom, 31),
            nom_societe,
            fontsize=10.5,
            fontname="helv",
            color=blanc,
        )

        y_societe = 48
        for ligne_societe in lignes_coordonnees(profil_societe)[:4]:
            largeur_ligne = fitz.get_text_length(
                ligne_societe,
                fontname="helv",
                fontsize=6.8,
            )
            page.insert_text(
                (553 - largeur_ligne, y_societe),
                ligne_societe,
                fontsize=6.8,
                fontname="helv",
                color=blanc,
            )
            y_societe += 11
        page.insert_text(
            (42, 94),
            texte_rapport("traitement_local", langue),
            fontsize=7.5,
            fontname="helv",
            color=blanc,
        )

        # Période.
        page.draw_rect(
            fitz.Rect(42, 125, 553, 166),
            color=bleu_clair,
            fill=bleu_clair,
        )
        page.insert_text(
            (56, 143),
            texte_rapport("periode", langue),
            fontsize=9,
            fontname="helv",
            color=gris,
        )
        page.insert_text(
            (56, 158),
            resume.periode,
            fontsize=12,
            fontname="helv",
            color=bleu,
        )

        # Cartes des indicateurs.
        cartes = [
            (
                texte_rapport("factures", langue),
                str(resume.nombre_factures),
            ),
            (
                texte_rapport("sous_total", langue),
                f"{resume.sous_total:.2f} {devise}",
            ),
            (
                "TPS",
                f"{resume.tps:.2f} {devise}",
            ),
            (
                "TVQ",
                f"{resume.tvq:.2f} {devise}",
            ),
            (
                texte_rapport("total", langue),
                f"{resume.total:.2f} {devise}",
            ),
        ]

        x_positions = [42, 147, 252, 357, 462]
        largeurs = [95, 95, 95, 95, 91]

        for index, (titre, valeur) in enumerate(cartes):
            x = x_positions[index]
            largeur = largeurs[index]

            page.draw_rect(
                fitz.Rect(x, 190, x + largeur, 262),
                color=(0.82, 0.85, 0.89),
                fill=gris_clair,
            )
            page.insert_text(
                (x + 10, 210),
                titre,
                fontsize=8,
                fontname="helv",
                color=gris,
            )
            page.insert_textbox(
                fitz.Rect(
                    x + 8,
                    222,
                    x + largeur - 8,
                    252,
                ),
                valeur,
                fontsize=11,
                fontname="helv",
                color=bleu,
                align=fitz.TEXT_ALIGN_CENTER,
            )

        # Bloc fournisseur principal.
        page.insert_text(
            (42, 305),
            texte_rapport("fournisseur_principal", langue),
            fontsize=10,
            fontname="helv",
            color=gris,
        )

        page.draw_rect(
            fitz.Rect(42, 320, 553, 385),
            color=(0.84, 0.87, 0.91),
            fill=blanc,
        )

        page.insert_textbox(
            fitz.Rect(58, 338, 390, 368),
            resume.fournisseur_principal,
            fontsize=12,
            fontname="helv",
            color=bleu,
        )
        page.insert_textbox(
            fitz.Rect(395, 338, 535, 368),
            f"{resume.total_fournisseur_principal:.2f} {devise}",
            fontsize=12,
            fontname="helv",
            color=bleu,
            align=fitz.TEXT_ALIGN_RIGHT,
        )

        # Bloc contrôle / anomalies.
        page.insert_text(
            (42, 425),
            texte_rapport("controle_anomalies", langue),
            fontsize=10,
            fontname="helv",
            color=gris,
        )

        if resume.nombre_anomalies == 0:
            statut = texte_rapport("aucune_anomalie", langue)
            couleur_statut = vert
            fond_statut = (0.92, 0.98, 0.94)
        else:
            statut = (
                f"{resume.nombre_anomalies} anomalie(s) detectee(s)"
            )
            couleur_statut = orange
            fond_statut = (1.00, 0.95, 0.90)

        page.draw_rect(
            fitz.Rect(42, 440, 553, 500),
            color=fond_statut,
            fill=fond_statut,
        )

        page.insert_text(
            (58, 466),
            statut,
            fontsize=13,
            fontname="helv",
            color=couleur_statut,
        )

        # Note de confidentialité.
        page.draw_line(
            (42, 735),
            (553, 735),
            color=(0.80, 0.82, 0.85),
            width=0.7,
        )
        page.insert_text(
            (42, 756),
            "Document genere localement par ComptaPrivee AI.",
            fontsize=8,
            fontname="helv",
            color=gris,
        )
        page.insert_text(
            (42, 771),
            "Aucune donnee comptable n'est envoyee sur Internet.",
            fontsize=8,
            fontname="helv",
            color=gris,
        )
        page.insert_text(
            (42, 800),
            "Validation humaine recommandee avant utilisation officielle.",
            fontsize=8,
            fontname="helv",
            color=gris,
        )

        document.set_metadata(
            {
                "title": "Resume comptable ComptaPrivee AI",
                "author": "ComptaPrivee AI",
                "subject": "Resume comptable local",
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

