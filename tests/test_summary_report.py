"""Tests du résumé comptable imprimable."""

from decimal import Decimal

import fitz
import pytest

from src.comptaprivee.dashboard import ResumeTableauBord
from src.comptaprivee.database import FactureEnregistree
from src.comptaprivee.summary_report import (
    construire_resume_comptable,
    exporter_resume_comptable_pdf,
)


def creer_facture(
    identifiant: int = 1,
    fournisseur: str = "Alpha",
) -> FactureEnregistree:
    return FactureEnregistree(
        identifiant=identifiant,
        numero=f"FAC-{identifiant:03d}",
        date="2026-09-01",
        fournisseur=fournisseur,
        client="Client",
        sous_total=Decimal("100.00"),
        tps=Decimal("5.00"),
        tvq=Decimal("9.98"),
        total=Decimal("114.98"),
        date_creation="2026-09-01 12:00:00",
    )


def creer_resume() -> ResumeTableauBord:
    return ResumeTableauBord(
        nombre_factures=2,
        sous_total=Decimal("300.00"),
        tps=Decimal("15.00"),
        tvq=Decimal("29.93"),
        total=Decimal("344.93"),
        total_par_fournisseur=(
            ("Alpha", Decimal("229.95")),
            ("Beta", Decimal("114.98")),
        ),
    )


def test_construire_resume_comptable() -> None:
    resultat = construire_resume_comptable(
        [
            creer_facture(1, "Alpha"),
            creer_facture(2, "Beta"),
        ],
        creer_resume(),
        date_debut="2026-09-01",
        date_fin="2026-09-30",
    )

    assert resultat.nombre_factures == 2
    assert resultat.nombre_anomalies == 0
    assert resultat.fournisseur_principal == "Alpha"
    assert resultat.total_fournisseur_principal == Decimal("229.95")
    assert resultat.periode == "2026-09-01 au 2026-09-30"


def test_resume_comptable_sans_fournisseur() -> None:
    resume = ResumeTableauBord(
        nombre_factures=0,
        sous_total=Decimal("0"),
        tps=Decimal("0"),
        tvq=Decimal("0"),
        total=Decimal("0"),
        total_par_fournisseur=(),
    )

    resultat = construire_resume_comptable(
        [],
        resume,
    )

    assert resultat.fournisseur_principal == "Aucun"
    assert resultat.total_fournisseur_principal == Decimal("0")
    assert resultat.periode == "Toutes les périodes"


def test_exporter_resume_comptable_pdf(tmp_path) -> None:
    resume = construire_resume_comptable(
        [creer_facture()],
        ResumeTableauBord(
            nombre_factures=1,
            sous_total=Decimal("100.00"),
            tps=Decimal("5.00"),
            tvq=Decimal("9.98"),
            total=Decimal("114.98"),
            total_par_fournisseur=(
                ("Alpha", Decimal("114.98")),
            ),
        ),
    )

    chemin = tmp_path / "resume_comptable.pdf"

    resultat = exporter_resume_comptable_pdf(
        resume,
        chemin,
    )

    assert resultat == chemin
    assert chemin.exists()
    assert chemin.stat().st_size > 0

    document = fitz.open(chemin)
    try:
        texte = " ".join(
            page.get_text()
            for page in document
        )
    finally:
        document.close()

    assert "Resume comptable" in texte
    assert "114.98 CAD" in texte
    assert "Alpha" in texte


def test_refuser_extension_resume_pdf_invalide(tmp_path) -> None:
    resume = construire_resume_comptable(
        [],
        ResumeTableauBord(
            nombre_factures=0,
            sous_total=Decimal("0"),
            tps=Decimal("0"),
            tvq=Decimal("0"),
            total=Decimal("0"),
            total_par_fournisseur=(),
        ),
    )

    with pytest.raises(ValueError, match="format PDF"):
        exporter_resume_comptable_pdf(
            resume,
            tmp_path / "resume.txt",
        )
