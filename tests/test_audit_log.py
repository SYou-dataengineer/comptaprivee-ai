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

def test_filtrer_evenements_audit_par_categorie() -> None:
    from src.comptaprivee.audit_log import (
        EvenementAudit,
        filtrer_evenements_audit,
    )

    evenements = [
        EvenementAudit(
            1, "Document converti", "conversion", None,
            "a.xlsx", "2026-09-01 10:00:00",
        ),
        EvenementAudit(
            2, "Alerte OCR résolue", "ocr", None,
            "FAC-N05", "2026-09-03 22:26:22",
        ),
    ]

    resultat = filtrer_evenements_audit(
        evenements,
        categorie="OCR",
    )

    assert len(resultat) == 1
    assert resultat[0].reference == "FAC-N05"


def test_filtrer_evenements_audit_par_periode_inclusive() -> None:
    from src.comptaprivee.audit_log import (
        EvenementAudit,
        filtrer_evenements_audit,
    )

    evenements = [
        EvenementAudit(1, "A", "test", None, None, "2026-09-01 08:00:00"),
        EvenementAudit(2, "B", "test", None, None, "2026-09-03 08:00:00"),
        EvenementAudit(3, "C", "test", None, None, "2026-09-05 08:00:00"),
    ]

    resultat = filtrer_evenements_audit(
        evenements,
        date_debut="2026-09-01",
        date_fin="2026-09-03",
    )

    assert [e.action for e in resultat] == ["A", "B"]


def test_filtrer_evenements_audit_refuse_periode_invalide() -> None:
    from src.comptaprivee.audit_log import (
        EvenementAudit,
        filtrer_evenements_audit,
    )

    evenement = EvenementAudit(
        1, "Test", "test", None, None, "2026-09-03 12:00:00"
    )

    with pytest.raises(ValueError):
        filtrer_evenements_audit(
            [evenement],
            date_debut="2026-09-05",
            date_fin="2026-09-01",
        )


def test_exporter_journal_audit_csv_respecte_categorie_et_periode(
    tmp_path,
) -> None:
    import csv

    from src.comptaprivee.audit_log import (
        exporter_journal_audit_csv,
        lister_evenements,
    )

    chemin_base = tmp_path / "audit.db"
    destination = tmp_path / "filtre.csv"

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

    date_jour = lister_evenements(
        chemin_base,
        limite=1,
    )[0].date_creation[:10]

    exporter_journal_audit_csv(
        destination,
        chemin_base,
        categorie="ocr",
        date_debut=date_jour,
        date_fin=date_jour,
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

def test_periode_rapide_audit_aujourdhui() -> None:
    from datetime import date

    from src.comptaprivee.audit_log import (
        periode_rapide_audit,
    )

    debut, fin = periode_rapide_audit(
        "Aujourd'hui",
        aujourd_hui=date(2026, 9, 3),
    )

    assert debut == "2026-09-03"
    assert fin == "2026-09-03"


def test_periode_rapide_audit_7_jours() -> None:
    from datetime import date

    from src.comptaprivee.audit_log import (
        periode_rapide_audit,
    )

    debut, fin = periode_rapide_audit(
        "7 jours",
        aujourd_hui=date(2026, 9, 3),
    )

    assert debut == "2026-08-28"
    assert fin == "2026-09-03"


def test_periode_rapide_audit_ce_mois() -> None:
    from datetime import date

    from src.comptaprivee.audit_log import (
        periode_rapide_audit,
    )

    debut, fin = periode_rapide_audit(
        "Ce mois",
        aujourd_hui=date(2026, 9, 3),
    )

    assert debut == "2026-09-01"
    assert fin == "2026-09-03"


def test_periode_rapide_audit_refuse_mode_inconnu() -> None:
    from datetime import date

    from src.comptaprivee.audit_log import (
        periode_rapide_audit,
    )

    with pytest.raises(ValueError):
        periode_rapide_audit(
            "Hier seulement",
            aujourd_hui=date(2026, 9, 3),
        )

def test_filtrer_evenements_audit_par_action() -> None:
    from src.comptaprivee.audit_log import (
        EvenementAudit,
        filtrer_evenements_audit,
    )

    evenements = [
        EvenementAudit(
            identifiant=1,
            action="Document converti",
            categorie="conversion",
            details=None,
            reference="document.xlsx",
            date_creation="2026-09-03 10:00:00",
        ),
        EvenementAudit(
            identifiant=2,
            action="Alerte OCR résolue",
            categorie="ocr",
            details=None,
            reference="FAC-N05",
            date_creation="2026-09-03 11:00:00",
        ),
    ]

    resultat = filtrer_evenements_audit(
        evenements,
        action="alerte ocr résolue",
    )

    assert len(resultat) == 1
    assert resultat[0].reference == "FAC-N05"


def test_filtrer_evenements_audit_action_toutes_ne_filtre_pas() -> None:
    from src.comptaprivee.audit_log import (
        EvenementAudit,
        filtrer_evenements_audit,
    )

    evenements = [
        EvenementAudit(
            identifiant=1,
            action="Document converti",
            categorie="conversion",
            details=None,
            reference="a.xlsx",
            date_creation="2026-09-03 10:00:00",
        ),
        EvenementAudit(
            identifiant=2,
            action="Alerte OCR résolue",
            categorie="ocr",
            details=None,
            reference="FAC-N05",
            date_creation="2026-09-03 11:00:00",
        ),
    ]

    resultat = filtrer_evenements_audit(
        evenements,
        action="Toutes",
    )

    assert len(resultat) == 2


def test_filtrer_evenements_audit_combine_action_categorie_periode() -> None:
    from src.comptaprivee.audit_log import (
        EvenementAudit,
        filtrer_evenements_audit,
    )

    evenements = [
        EvenementAudit(
            identifiant=1,
            action="Alerte OCR résolue",
            categorie="ocr",
            details=None,
            reference="FAC-001",
            date_creation="2026-09-01 09:00:00",
        ),
        EvenementAudit(
            identifiant=2,
            action="Alerte OCR résolue",
            categorie="ocr",
            details=None,
            reference="FAC-N05",
            date_creation="2026-09-03 22:26:22",
        ),
        EvenementAudit(
            identifiant=3,
            action="Document converti",
            categorie="conversion",
            details=None,
            reference="document.xlsx",
            date_creation="2026-09-03 22:30:00",
        ),
    ]

    resultat = filtrer_evenements_audit(
        evenements,
        categorie="ocr",
        action="Alerte OCR résolue",
        date_debut="2026-09-03",
        date_fin="2026-09-03",
    )

    assert len(resultat) == 1
    assert resultat[0].reference == "FAC-N05"


def test_exporter_journal_audit_csv_respecte_action(
    tmp_path,
) -> None:
    import csv

    from src.comptaprivee.audit_log import (
        exporter_journal_audit_csv,
    )

    chemin_base = tmp_path / "audit.db"
    destination = tmp_path / "actions.csv"

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
        action="Alerte OCR résolue",
    )

    with destination.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as fichier:
        lignes = list(csv.reader(fichier))

    assert len(lignes) == 2
    assert lignes[1][2] == "Alerte OCR résolue"
    assert lignes[1][3] == "FAC-N05"

def test_trier_evenements_audit_date_ascendante() -> None:
    from src.comptaprivee.audit_log import (
        EvenementAudit,
        trier_evenements_audit,
    )

    evenements = [
        EvenementAudit(
            identifiant=1,
            action="A",
            categorie="test",
            details=None,
            reference="B",
            date_creation="2026-09-03 12:00:00",
        ),
        EvenementAudit(
            identifiant=2,
            action="B",
            categorie="test",
            details=None,
            reference="A",
            date_creation="2026-09-01 08:00:00",
        ),
    ]

    resultat = trier_evenements_audit(
        evenements,
        "date",
    )

    assert [e.identifiant for e in resultat] == [2, 1]


def test_trier_evenements_audit_action_sans_casse() -> None:
    from src.comptaprivee.audit_log import (
        EvenementAudit,
        trier_evenements_audit,
    )

    evenements = [
        EvenementAudit(
            identifiant=1,
            action="Sauvegarde créée",
            categorie="systeme",
            details=None,
            reference=None,
            date_creation="2026-09-03 12:00:00",
        ),
        EvenementAudit(
            identifiant=2,
            action="alerte OCR résolue",
            categorie="ocr",
            details=None,
            reference="FAC-N05",
            date_creation="2026-09-03 13:00:00",
        ),
        EvenementAudit(
            identifiant=3,
            action="Document converti",
            categorie="conversion",
            details=None,
            reference="a.xlsx",
            date_creation="2026-09-03 14:00:00",
        ),
    ]

    resultat = trier_evenements_audit(
        evenements,
        "action",
    )

    assert [e.identifiant for e in resultat] == [2, 3, 1]


def test_trier_evenements_audit_reference_descendante() -> None:
    from src.comptaprivee.audit_log import (
        EvenementAudit,
        trier_evenements_audit,
    )

    evenements = [
        EvenementAudit(
            identifiant=1,
            action="A",
            categorie="test",
            details=None,
            reference=None,
            date_creation="2026-09-03 12:00:00",
        ),
        EvenementAudit(
            identifiant=2,
            action="B",
            categorie="test",
            details=None,
            reference="FAC-001",
            date_creation="2026-09-03 13:00:00",
        ),
        EvenementAudit(
            identifiant=3,
            action="C",
            categorie="test",
            details=None,
            reference="Zeta",
            date_creation="2026-09-03 14:00:00",
        ),
    ]

    resultat = trier_evenements_audit(
        evenements,
        "reference",
        descendant=True,
    )

    assert [e.identifiant for e in resultat] == [3, 2, 1]


def test_trier_evenements_audit_refuse_colonne_inconnue() -> None:
    from src.comptaprivee.audit_log import (
        EvenementAudit,
        trier_evenements_audit,
    )

    evenement = EvenementAudit(
        identifiant=1,
        action="Test",
        categorie="test",
        details=None,
        reference=None,
        date_creation="2026-09-03 12:00:00",
    )

    with pytest.raises(ValueError):
        trier_evenements_audit(
            [evenement],
            "details",
        )

def test_exporter_evenements_audit_csv_conserve_ordre_affiche(
    tmp_path,
) -> None:
    import csv

    from src.comptaprivee.audit_log import (
        EvenementAudit,
        exporter_evenements_audit_csv,
    )

    evenements = [
        EvenementAudit(
            identifiant=2,
            action="Document converti",
            categorie="conversion",
            details="deuxieme",
            reference="B.xlsx",
            date_creation="2026-09-03 12:00:00",
        ),
        EvenementAudit(
            identifiant=1,
            action="Alerte OCR résolue",
            categorie="ocr",
            details="premier",
            reference="FAC-N05",
            date_creation="2026-09-03 11:00:00",
        ),
    ]

    destination = tmp_path / "vue.csv"

    exporter_evenements_audit_csv(
        destination,
        evenements,
    )

    with destination.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as fichier:
        lignes = list(csv.reader(fichier))

    assert lignes[1][3] == "B.xlsx"
    assert lignes[2][3] == "FAC-N05"


def test_exporter_evenements_audit_csv_exporte_seulement_vue(
    tmp_path,
) -> None:
    import csv

    from src.comptaprivee.audit_log import (
        EvenementAudit,
        exporter_evenements_audit_csv,
    )

    evenement_visible = EvenementAudit(
        identifiant=7,
        action="Alerte OCR résolue",
        categorie="ocr",
        details=None,
        reference="FAC-N05",
        date_creation="2026-09-03 22:26:22",
    )

    destination = tmp_path / "vue_filtree.csv"

    exporter_evenements_audit_csv(
        destination,
        [evenement_visible],
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


def test_exporter_evenements_audit_csv_vue_vide_garde_entete(
    tmp_path,
) -> None:
    import csv

    from src.comptaprivee.audit_log import (
        exporter_evenements_audit_csv,
    )

    destination = tmp_path / "vue_vide.csv"

    exporter_evenements_audit_csv(
        destination,
        [],
    )

    with destination.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as fichier:
        lignes = list(csv.reader(fichier))

    assert lignes == [
        [
            "Date / heure",
            "Catégorie",
            "Action",
            "Référence",
            "Détails",
        ]
    ]


def test_exporter_evenements_audit_csv_refuse_extension_non_csv(
    tmp_path,
) -> None:
    from src.comptaprivee.audit_log import (
        exporter_evenements_audit_csv,
    )

    with pytest.raises(ValueError):
        exporter_evenements_audit_csv(
            tmp_path / "vue.xlsx",
            [],
        )

def test_resumer_evenements_audit_compte_categories() -> None:
    from src.comptaprivee.audit_log import (
        EvenementAudit,
        resumer_evenements_audit,
    )

    evenements = [
        EvenementAudit(
            1, "Document converti", "conversion", None,
            "a.xlsx", "2026-09-03 10:00:00",
        ),
        EvenementAudit(
            2, "Document converti", "conversion", None,
            "b.xlsx", "2026-09-03 11:00:00",
        ),
        EvenementAudit(
            3, "Alerte OCR résolue", "ocr", None,
            "FAC-N05", "2026-09-03 12:00:00",
        ),
        EvenementAudit(
            4, "Sauvegarde créée", "sauvegarde", None,
            "backup.zip", "2026-09-03 13:00:00",
        ),
    ]

    resume = resumer_evenements_audit(evenements)

    assert resume == {
        "total": 4,
        "conversions": 2,
        "ocr": 1,
        "autres": 1,
    }


def test_resumer_evenements_audit_est_insensible_a_la_casse() -> None:
    from src.comptaprivee.audit_log import (
        EvenementAudit,
        resumer_evenements_audit,
    )

    evenements = [
        EvenementAudit(
            1, "A", " Conversion ", None,
            None, "2026-09-03 10:00:00",
        ),
        EvenementAudit(
            2, "B", "OCR", None,
            None, "2026-09-03 11:00:00",
        ),
    ]

    resume = resumer_evenements_audit(evenements)

    assert resume["conversions"] == 1
    assert resume["ocr"] == 1
    assert resume["autres"] == 0


def test_resumer_evenements_audit_vue_vide() -> None:
    from src.comptaprivee.audit_log import (
        resumer_evenements_audit,
    )

    resume = resumer_evenements_audit([])

    assert resume == {
        "total": 0,
        "conversions": 0,
        "ocr": 0,
        "autres": 0,
    }


def test_resumer_evenements_audit_classe_categories_inconnues_autres() -> None:
    from src.comptaprivee.audit_log import (
        EvenementAudit,
        resumer_evenements_audit,
    )

    evenements = [
        EvenementAudit(
            1, "Facture enregistrée", "facture", None,
            "FAC-001", "2026-09-03 10:00:00",
        ),
        EvenementAudit(
            2, "Sauvegarde créée", "sauvegarde", None,
            "backup.zip", "2026-09-03 11:00:00",
        ),
    ]

    resume = resumer_evenements_audit(evenements)

    assert resume["total"] == 2
    assert resume["autres"] == 2

def test_filtrer_evenements_audit_categorie_autres() -> None:
    from src.comptaprivee.audit_log import (
        EvenementAudit,
        filtrer_evenements_audit,
    )

    evenements = [
        EvenementAudit(
            1, "Document converti", "conversion", None,
            "a.xlsx", "2026-09-03 10:00:00",
        ),
        EvenementAudit(
            2, "Alerte OCR résolue", "ocr", None,
            "FAC-N05", "2026-09-03 11:00:00",
        ),
        EvenementAudit(
            3, "Sauvegarde créée", "sauvegarde", None,
            "backup.zip", "2026-09-03 12:00:00",
        ),
        EvenementAudit(
            4, "Facture enregistrée", "facture", None,
            "FAC-001", "2026-09-03 13:00:00",
        ),
    ]

    resultat = filtrer_evenements_audit(
        evenements,
        categorie="Autres",
    )

    assert [e.identifiant for e in resultat] == [3, 4]


def test_filtrer_evenements_audit_autres_insensible_a_la_casse() -> None:
    from src.comptaprivee.audit_log import (
        EvenementAudit,
        filtrer_evenements_audit,
    )

    evenements = [
        EvenementAudit(
            1, "A", "OCR", None,
            None, "2026-09-03 10:00:00",
        ),
        EvenementAudit(
            2, "B", " Sauvegarde ", None,
            None, "2026-09-03 11:00:00",
        ),
    ]

    resultat = filtrer_evenements_audit(
        evenements,
        categorie=" autres ",
    )

    assert len(resultat) == 1
    assert resultat[0].identifiant == 2


def test_exporter_journal_audit_csv_categorie_autres(
    tmp_path,
) -> None:
    import csv

    from src.comptaprivee.audit_log import (
        exporter_journal_audit_csv,
    )

    chemin_base = tmp_path / "audit.db"
    destination = tmp_path / "autres.csv"

    enregistrer_evenement(
        "Document converti",
        "conversion",
        reference="document.xlsx",
        chemin_base=chemin_base,
    )
    enregistrer_evenement(
        "Sauvegarde créée",
        "sauvegarde",
        reference="backup.zip",
        chemin_base=chemin_base,
    )

    exporter_journal_audit_csv(
        destination,
        chemin_base,
        categorie="Autres",
    )

    with destination.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as fichier:
        lignes = list(csv.reader(fichier))

    assert len(lignes) == 2
    assert lignes[1][1] == "sauvegarde"
    assert lignes[1][3] == "backup.zip"


def test_resume_apres_filtre_autres_est_coherent() -> None:
    from src.comptaprivee.audit_log import (
        EvenementAudit,
        filtrer_evenements_audit,
        resumer_evenements_audit,
    )

    evenements = [
        EvenementAudit(
            1, "A", "conversion", None,
            None, "2026-09-03 10:00:00",
        ),
        EvenementAudit(
            2, "B", "ocr", None,
            None, "2026-09-03 11:00:00",
        ),
        EvenementAudit(
            3, "C", "facture", None,
            None, "2026-09-03 12:00:00",
        ),
    ]

    vue = filtrer_evenements_audit(
        evenements,
        categorie="Autres",
    )
    resume = resumer_evenements_audit(vue)

    assert resume == {
        "total": 1,
        "conversions": 0,
        "ocr": 0,
        "autres": 1,
    }
