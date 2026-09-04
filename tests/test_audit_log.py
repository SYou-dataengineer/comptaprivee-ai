"""Tests du journal d'audit local."""

import pytest

from src.comptaprivee.audit_log import (
    enregistrer_evenement,
    initialiser_journal_audit,
    lister_evenements,
    rechercher_evenements,
)


def test_initialiser_journal_audit(tmp_path) -> None:
    chemin = tmp_path / "audit.db"

    resultat = initialiser_journal_audit(chemin)

    assert resultat == chemin
    assert chemin.exists()


def test_enregistrer_et_lister_evenement(tmp_path) -> None:
    chemin = tmp_path / "audit.db"

    evenement = enregistrer_evenement(
        "Facture enregistrée",
        "facture",
        details="Total 1149.75 CAD",
        reference="FAC-001",
        chemin_base=chemin,
    )

    assert evenement.identifiant > 0
    assert evenement.reference == "FAC-001"

    liste = lister_evenements(chemin)

    assert len(liste) == 1
    assert liste[0].action == "Facture enregistrée"


def test_rechercher_evenements(tmp_path) -> None:
    chemin = tmp_path / "audit.db"

    enregistrer_evenement(
        "Facture enregistrée",
        "facture",
        reference="FAC-001",
        chemin_base=chemin,
    )
    enregistrer_evenement(
        "Sauvegarde créée",
        "sauvegarde",
        reference="backup.zip",
        chemin_base=chemin,
    )

    resultat = rechercher_evenements(
        "backup",
        chemin,
    )

    assert len(resultat) == 1
    assert resultat[0].categorie == "sauvegarde"


def test_limiter_nombre_evenements(tmp_path) -> None:
    chemin = tmp_path / "audit.db"

    for index in range(4):
        enregistrer_evenement(
            f"Action {index}",
            "test",
            chemin_base=chemin,
        )

    resultat = lister_evenements(
        chemin,
        limite=2,
    )

    assert len(resultat) == 2
    assert resultat[0].action == "Action 3"


def test_refuser_action_vide(tmp_path) -> None:
    with pytest.raises(ValueError):
        enregistrer_evenement(
            "   ",
            "test",
            chemin_base=tmp_path / "audit.db",
        )

def test_journaliser_sans_bloquer_enregistre(tmp_path) -> None:
    from src.comptaprivee.audit_log import journaliser_sans_bloquer

    chemin = tmp_path / "audit.db"
    journaliser_sans_bloquer(
        "Test",
        "test",
        reference="REF-1",
        chemin_base=chemin,
    )

    evenements = lister_evenements(chemin)
    assert len(evenements) == 1
    assert evenements[0].reference == "REF-1"


def test_journaliser_sans_bloquer_ignore_erreur(tmp_path) -> None:
    from src.comptaprivee.audit_log import journaliser_sans_bloquer

    faux_dossier = tmp_path / "dossier"
    faux_dossier.mkdir()

    journaliser_sans_bloquer(
        "Test",
        "test",
        chemin_base=faux_dossier,
    )


def test_enregistrement_facture_cree_evenement_audit(tmp_path) -> None:
    from decimal import Decimal
    from src.comptaprivee.database import enregistrer_facture
    from src.comptaprivee.facture_parser import DonneesFacture

    chemin = tmp_path / "compta.db"
    enregistrer_facture(
        DonneesFacture(
            numero="AUDIT-FAC-001",
            date="2026-09-02",
            fournisseur="Fournisseur Audit",
            client="Client Audit",
            sous_total=Decimal("100.00"),
            tps=Decimal("5.00"),
            tvq=Decimal("9.98"),
            total=Decimal("114.98"),
        ),
        chemin,
    )

    evenements = lister_evenements(chemin)
    assert any(
        e.action == "Facture enregistrée"
        and e.reference == "AUDIT-FAC-001"
        for e in evenements
    )


def test_corbeille_cree_evenement_audit(tmp_path) -> None:
    from decimal import Decimal
    from src.comptaprivee.database import (
        enregistrer_facture,
        mettre_facture_corbeille,
    )
    from src.comptaprivee.facture_parser import DonneesFacture

    chemin = tmp_path / "compta.db"
    facture = enregistrer_facture(
        DonneesFacture(
            numero="AUDIT-CORB-001",
            date="2026-09-02",
            fournisseur="Fournisseur Audit",
            client="Client Audit",
            sous_total=Decimal("100.00"),
            tps=Decimal("5.00"),
            tvq=Decimal("9.98"),
            total=Decimal("114.98"),
        ),
        chemin,
    )

    assert mettre_facture_corbeille(
        facture.identifiant,
        chemin,
    ) is True

    evenements = lister_evenements(chemin)
    assert any(
        e.action == "Facture mise à la corbeille"
        and e.reference == "AUDIT-CORB-001"
        for e in evenements
    )

def test_exporter_journal_audit_csv(tmp_path) -> None:
    import csv

    from src.comptaprivee.audit_log import (
        exporter_journal_audit_csv,
    )

    chemin_base = tmp_path / "audit.db"
    destination = tmp_path / "journal.csv"

    enregistrer_evenement(
        "Alerte OCR résolue",
        "ocr",
        reference="FAC-N05",
        details="page=1; ligne=6",
        chemin_base=chemin_base,
    )

    resultat = exporter_journal_audit_csv(
        destination,
        chemin_base,
    )

    assert resultat == destination
    assert destination.exists()

    with destination.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as fichier:
        lignes = list(csv.reader(fichier))

    assert lignes[0] == [
        "Date / heure",
        "Catégorie",
        "Action",
        "Référence",
        "Détails",
    ]
    assert lignes[1][1] == "ocr"
    assert lignes[1][2] == "Alerte OCR résolue"
    assert lignes[1][3] == "FAC-N05"


def test_exporter_journal_audit_csv_respecte_recherche(
    tmp_path,
) -> None:
    import csv

    from src.comptaprivee.audit_log import (
        exporter_journal_audit_csv,
    )

    chemin_base = tmp_path / "audit.db"
    destination = tmp_path / "ocr.csv"

    enregistrer_evenement(
        "Document converti",
        "conversion",
        reference="document.xlsx",
        chemin_base=chemin_base,
    )
    enregistrer_evenement(
        "Alerte OCR résolue",
        "ocr",
        reference="FAC-N05",
        chemin_base=chemin_base,
    )

    exporter_journal_audit_csv(
        destination,
        chemin_base,
        recherche="Alerte OCR résolue",
    )

    with destination.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as fichier:
        lignes = list(csv.reader(fichier))

    assert len(lignes) == 2
    assert lignes[1][1] == "ocr"
    assert lignes[1][3] == "FAC-N05"


def test_exporter_journal_audit_refuse_extension_non_csv(
    tmp_path,
) -> None:
    from src.comptaprivee.audit_log import (
        exporter_journal_audit_csv,
    )

    with pytest.raises(ValueError):
        exporter_journal_audit_csv(
            tmp_path / "journal.xlsx",
            tmp_path / "audit.db",
        )

def test_formater_evenement_audit_details_complet() -> None:
    from src.comptaprivee.audit_log import (
        EvenementAudit,
        formater_evenement_audit_details,
    )

    evenement = EvenementAudit(
        identifiant=1,
        action="Alerte OCR résolue",
        categorie="ocr",
        details="source=scan.pdf; page=1; ligne=6",
        reference="FAC-N05",
        date_creation="2026-09-03 22:26:22",
    )

    texte = formater_evenement_audit_details(
        evenement
    )

    assert "Date / heure : 2026-09-03 22:26:22" in texte
    assert "Catégorie : ocr" in texte
    assert "Action : Alerte OCR résolue" in texte
    assert "Référence : FAC-N05" in texte
    assert "source=scan.pdf; page=1; ligne=6" in texte


def test_formater_evenement_audit_details_valeurs_absentes() -> None:
    from src.comptaprivee.audit_log import (
        EvenementAudit,
        formater_evenement_audit_details,
    )

    evenement = EvenementAudit(
        identifiant=2,
        action="Test",
        categorie="test",
        details=None,
        reference=None,
        date_creation="2026-09-03 12:00:00",
    )

    texte = formater_evenement_audit_details(
        evenement
    )

    assert "Référence : -" in texte
    assert texte.endswith("Détails :\n-")


def test_formater_evenement_audit_details_conserve_multiligne() -> None:
    from src.comptaprivee.audit_log import (
        EvenementAudit,
        formater_evenement_audit_details,
    )

    evenement = EvenementAudit(
        identifiant=3,
        action="Document converti",
        categorie="conversion",
        details="source=a.pdf\nexport=a.xlsx",
        reference="a.xlsx",
        date_creation="2026-09-03 12:10:00",
    )

    texte = formater_evenement_audit_details(
        evenement
    )

    assert "source=a.pdf\nexport=a.xlsx" in texte
