import binascii
import struct
import zlib
import base64

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




def _creer_png_test(chemin) -> None:
    signature = b"\x89PNG\r\n\x1a\n"

    def chunk(type_chunk: bytes, donnees: bytes) -> bytes:
        crc = binascii.crc32(type_chunk + donnees) & 0xFFFFFFFF
        return (
            struct.pack(">I", len(donnees))
            + type_chunk
            + donnees
            + struct.pack(">I", crc)
        )

    ihdr = struct.pack(
        ">IIBBBBB",
        1,
        1,
        8,
        2,
        0,
        0,
        0,
    )

    donnees_image = b"\x00\xff\xff\xff"

    contenu = (
        signature
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(donnees_image))
        + chunk(b"IEND", b"")
    )

    chemin.write_bytes(contenu)

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

    assert "RESUME COMPTABLE" in texte
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

def test_export_pdf_resume_professionnel(tmp_path) -> None:
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

    chemin = tmp_path / "resume_professionnel.pdf"

    exporter_resume_comptable_pdf(
        resume,
        chemin,
    )

    document = fitz.open(chemin)
    try:
        texte = " ".join(
            page.get_text()
            for page in document
        )
    finally:
        document.close()

    assert "RESUME COMPTABLE" in texte
    assert "CONTROLE DES ANOMALIES" in texte
    assert "Aucune anomalie detectee" in texte
    assert "Traitement local" in texte

def test_resume_utilise_nom_societe_local(monkeypatch) -> None:
    from src.comptaprivee import summary_report

    monkeypatch.setattr(
        summary_report,
        "lire_nom_societe",
        lambda: "Cabinet Exemple CPA Inc.",
    )

    resultat = construire_resume_comptable(
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

    assert resultat.societe_comptable == "Cabinet Exemple CPA Inc."

def test_pdf_resume_affiche_coordonnees_societe(
    tmp_path,
    monkeypatch,
) -> None:
    from src.comptaprivee import summary_report
    from src.comptaprivee.company_profile import ProfilSociete

    monkeypatch.setattr(
        summary_report,
        "lire_profil_societe",
        lambda: ProfilSociete(
            nom_societe="Cabinet Exemple CPA Inc.",
            adresse="123 rue Exemple",
            ville="Montréal",
            province="QC",
            code_postal="H1H 1H1",
            telephone="514-555-0100",
            courriel="info@exemple.ca",
        ),
    )

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

    chemin = tmp_path / "resume_coordonnees.pdf"
    exporter_resume_comptable_pdf(
        resume,
        chemin,
    )

    document = fitz.open(chemin)
    try:
        texte = " ".join(
            page.get_text()
            for page in document
        )
    finally:
        document.close()

    assert "123 rue Exemple" in texte
    assert "514-555-0100" in texte
    assert "info@exemple.ca" in texte

def test_pdf_resume_insere_logo_societe(
    tmp_path,
    monkeypatch,
) -> None:
    from src.comptaprivee import summary_report
    from src.comptaprivee.company_profile import ProfilSociete

    logo = tmp_path / "logo.png"
    _creer_png_test(logo)

    monkeypatch.setattr(
        summary_report,
        "lire_profil_societe",
        lambda: ProfilSociete(
            nom_societe="Cabinet Exemple CPA Inc.",
            logo_path=str(logo),
        ),
    )

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

    chemin = tmp_path / "resume_logo.pdf"
    exporter_resume_comptable_pdf(resume, chemin)

    document = fitz.open(chemin)
    try:
        assert any(page.get_images(full=True) for page in document)
    finally:
        document.close()


