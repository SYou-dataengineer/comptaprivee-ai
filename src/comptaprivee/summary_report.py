"""Résumé comptable imprimable et exportable."""

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import fitz

from .anomalies import detecter_anomalies
from .dashboard import ResumeTableauBord
from .database import FactureEnregistree


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

    debut = date_debut or "Toutes"
    fin = date_fin or "Toutes"

    if date_debut or date_fin:
        periode = f"{debut} au {fin}"
    else:
        periode = "Toutes les périodes"

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
    )


def exporter_resume_comptable_pdf(
    resume: ResumeComptableImprimable,
    chemin_sortie: str | Path,
) -> Path:
    """Exporte le résumé comptable dans un PDF local."""
    chemin = Path(chemin_sortie)

    if chemin.suffix.lower() != ".pdf":
        raise ValueError(
            "Le fichier de sortie doit être au format PDF."
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
            "Resume comptable",
            fontsize=14,
            fontname="helv",
        )
        page.draw_line((45, 96), (550, 96), width=0.8)

        lignes = [
            ("Periode", resume.periode),
            ("Nombre de factures", str(resume.nombre_factures)),
            ("Sous-total", f"{resume.sous_total:.2f} CAD"),
            ("TPS", f"{resume.tps:.2f} CAD"),
            ("TVQ", f"{resume.tvq:.2f} CAD"),
            ("Total", f"{resume.total:.2f} CAD"),
            ("Nombre d'anomalies", str(resume.nombre_anomalies)),
            ("Fournisseur principal", resume.fournisseur_principal),
            (
                "Total fournisseur principal",
                f"{resume.total_fournisseur_principal:.2f} CAD",
            ),
        ]

        y = 135

        for libelle, valeur in lignes:
            page.insert_text(
                (55, y),
                f"{libelle} :",
                fontsize=11,
                fontname="helv",
            )
            page.insert_textbox(
                fitz.Rect(230, y - 12, 535, y + 18),
                valeur,
                fontsize=11,
                fontname="helv",
            )
            y += 34

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
