"""Journal d'audit local de ComptaPrivée AI."""

from __future__ import annotations

import csv
import sqlite3
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from .database import (
    CHEMIN_BASE_PAR_DEFAUT,
    ouvrir_connexion,
)


@dataclass(frozen=True)
class EvenementAudit:
    """Une action enregistrée dans le journal d'audit local."""

    identifiant: int
    action: str
    categorie: str
    details: str | None
    reference: str | None
    date_creation: str


def initialiser_journal_audit(
    chemin_base: str | Path = CHEMIN_BASE_PAR_DEFAUT,
) -> Path:
    """Crée la table du journal d'audit si nécessaire."""
    chemin = Path(chemin_base)
    chemin.parent.mkdir(parents=True, exist_ok=True)

    with ouvrir_connexion(chemin) as connexion:
        connexion.execute(
            """
            CREATE TABLE IF NOT EXISTS journal_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                categorie TEXT NOT NULL,
                details TEXT,
                reference TEXT,
                date_creation TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

    return chemin


def enregistrer_evenement(
    action: str,
    categorie: str,
    *,
    details: str | None = None,
    reference: str | None = None,
    chemin_base: str | Path = CHEMIN_BASE_PAR_DEFAUT,
) -> EvenementAudit:
    """Ajoute une entrée dans le journal d'audit local."""
    action = action.strip()
    categorie = categorie.strip()

    if not action:
        raise ValueError("L'action du journal d'audit est obligatoire.")

    if not categorie:
        raise ValueError("La catégorie du journal d'audit est obligatoire.")

    initialiser_journal_audit(chemin_base)

    with ouvrir_connexion(chemin_base) as connexion:
        curseur = connexion.execute(
            """
            INSERT INTO journal_audit (
                action,
                categorie,
                details,
                reference
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                action,
                categorie,
                details,
                reference,
            ),
        )

        identifiant = curseur.lastrowid

        ligne = connexion.execute(
            """
            SELECT *
            FROM journal_audit
            WHERE id = ?
            """,
            (identifiant,),
        ).fetchone()

    if ligne is None:
        raise RuntimeError(
            "L'événement d'audit a été enregistré mais reste introuvable."
        )

    return _ligne_vers_evenement(ligne)


def _ligne_vers_evenement(
    ligne: sqlite3.Row,
) -> EvenementAudit:
    return EvenementAudit(
        identifiant=ligne["id"],
        action=ligne["action"],
        categorie=ligne["categorie"],
        details=ligne["details"],
        reference=ligne["reference"],
        date_creation=ligne["date_creation"],
    )


def lister_evenements(
    chemin_base: str | Path = CHEMIN_BASE_PAR_DEFAUT,
    *,
    limite: int | None = None,
) -> list[EvenementAudit]:
    """Retourne les événements du plus récent au plus ancien."""
    initialiser_journal_audit(chemin_base)

    requete = """
        SELECT *
        FROM journal_audit
        ORDER BY id DESC
    """
    parametres: tuple[int, ...] = ()

    if limite is not None:
        if limite <= 0:
            raise ValueError("La limite doit être supérieure à zéro.")

        requete += " LIMIT ?"
        parametres = (limite,)

    with ouvrir_connexion(chemin_base) as connexion:
        lignes = connexion.execute(
            requete,
            parametres,
        ).fetchall()

    return [
        _ligne_vers_evenement(ligne)
        for ligne in lignes
    ]


def rechercher_evenements(
    recherche: str,
    chemin_base: str | Path = CHEMIN_BASE_PAR_DEFAUT,
) -> list[EvenementAudit]:
    """Recherche dans action, catégorie, détails et référence."""
    initialiser_journal_audit(chemin_base)

    terme = f"%{recherche.strip()}%"

    with ouvrir_connexion(chemin_base) as connexion:
        lignes = connexion.execute(
            """
            SELECT *
            FROM journal_audit
            WHERE action LIKE ? COLLATE NOCASE
               OR categorie LIKE ? COLLATE NOCASE
               OR details LIKE ? COLLATE NOCASE
               OR reference LIKE ? COLLATE NOCASE
            ORDER BY id DESC
            """,
            (
                terme,
                terme,
                terme,
                terme,
            ),
        ).fetchall()

    return [
        _ligne_vers_evenement(ligne)
        for ligne in lignes
    ]

def journaliser_sans_bloquer(
    action: str,
    categorie: str,
    *,
    details: str | None = None,
    reference: str | None = None,
    chemin_base: str | Path = CHEMIN_BASE_PAR_DEFAUT,
) -> None:
    """Journalise une action sans bloquer l'opération principale."""
    try:
        enregistrer_evenement(
            action,
            categorie,
            details=details,
            reference=reference,
            chemin_base=chemin_base,
        )
    except Exception:
        return

def filtrer_evenements_audit(
    evenements: list[EvenementAudit],
    *,
    categorie: str | None = None,
    action: str | None = None,
    date_debut: str | None = None,
    date_fin: str | None = None,
) -> list[EvenementAudit]:
    """Filtre des événements par catégorie et période inclusive."""
    categorie_normalisee = (categorie or "").strip().casefold()
    if categorie_normalisee in {"", "toutes", "tous"}:
        categorie_normalisee = ""

    action_normalisee = (action or "").strip().casefold()
    if action_normalisee in {"", "toutes", "tous"}:
        action_normalisee = ""

    debut: date | None = None
    fin: date | None = None

    if (date_debut or "").strip():
        try:
            debut = date.fromisoformat(str(date_debut).strip())
        except ValueError as erreur:
            raise ValueError(
                "La date de début doit être au format AAAA-MM-JJ."
            ) from erreur

    if (date_fin or "").strip():
        try:
            fin = date.fromisoformat(str(date_fin).strip())
        except ValueError as erreur:
            raise ValueError(
                "La date de fin doit être au format AAAA-MM-JJ."
            ) from erreur

    if debut is not None and fin is not None and debut > fin:
        raise ValueError(
            "La date de début ne peut pas être après la date de fin."
        )

    resultat: list[EvenementAudit] = []

    for evenement in evenements:
        if categorie_normalisee:
            categorie_evenement = (
                evenement.categorie.strip().casefold()
            )

            if categorie_normalisee == "autres":
                if categorie_evenement in {
                    "conversion",
                    "ocr",
                }:
                    continue
            elif categorie_evenement != categorie_normalisee:
                continue

        if (
            action_normalisee
            and evenement.action.strip().casefold()
            != action_normalisee
        ):
            continue

        try:
            date_evenement = date.fromisoformat(
                evenement.date_creation[:10]
            )
        except (TypeError, ValueError) as erreur:
            raise ValueError(
                "Une date du journal d'audit est invalide."
            ) from erreur

        if debut is not None and date_evenement < debut:
            continue
        if fin is not None and date_evenement > fin:
            continue

        resultat.append(evenement)

    return resultat

def resumer_evenements_audit(
    evenements: list[EvenementAudit],
) -> dict[str, int]:
    """Retourne un résumé simple de la vue courante du journal d'audit."""
    total = len(evenements)
    conversions = 0
    ocr = 0

    for evenement in evenements:
        categorie = evenement.categorie.strip().casefold()

        if categorie == "conversion":
            conversions += 1
        elif categorie == "ocr":
            ocr += 1

    return {
        "total": total,
        "conversions": conversions,
        "ocr": ocr,
        "autres": total - conversions - ocr,
    }

def trier_evenements_audit(
    evenements: list[EvenementAudit],
    colonne: str,
    *,
    descendant: bool = False,
) -> list[EvenementAudit]:
    """Trie une copie des événements selon une colonne visible du journal."""
    cles = {
        "date": lambda evenement: evenement.date_creation,
        "categorie": lambda evenement: evenement.categorie.casefold(),
        "action": lambda evenement: evenement.action.casefold(),
        "reference": lambda evenement: (
            evenement.reference or ""
        ).casefold(),
    }

    cle = cles.get(colonne)

    if cle is None:
        raise ValueError(
            "Colonne de tri inconnue. "
            "Utilisez date, categorie, action ou reference."
        )

    return sorted(
        evenements,
        key=cle,
        reverse=descendant,
    )

def periode_rapide_audit(
    mode: str,
    *,
    aujourd_hui: date | None = None,
) -> tuple[str, str]:
    """Retourne une période inclusive prête à utiliser dans les filtres."""
    jour = aujourd_hui or date.today()
    mode_normalise = mode.strip().casefold()

    if mode_normalise in {
        "aujourd'hui",
        "aujourdhui",
        "today",
    }:
        debut = jour
        fin = jour
    elif mode_normalise in {
        "7 jours",
        "7 derniers jours",
        "semaine",
    }:
        debut = jour - timedelta(days=6)
        fin = jour
    elif mode_normalise in {
        "ce mois",
        "mois",
        "this month",
    }:
        debut = jour.replace(day=1)
        fin = jour
    else:
        raise ValueError(
            "Période rapide inconnue. "
            "Utilisez Aujourd'hui, 7 jours ou Ce mois."
        )

    return debut.isoformat(), fin.isoformat()

def exporter_evenements_audit_csv(
    destination: str | Path,
    evenements: list[EvenementAudit],
) -> Path:
    """Exporte exactement les événements fournis, dans l'ordre reçu."""
    chemin_destination = Path(destination)

    if chemin_destination.suffix.lower() != ".csv":
        raise ValueError(
            "Le journal d'audit doit être exporté dans un fichier .csv."
        )

    chemin_destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with chemin_destination.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as fichier:
        writer = csv.writer(fichier)
        writer.writerow(
            [
                "Date / heure",
                "Catégorie",
                "Action",
                "Référence",
                "Détails",
            ]
        )

        for evenement in evenements:
            writer.writerow(
                [
                    evenement.date_creation,
                    evenement.categorie,
                    evenement.action,
                    evenement.reference or "",
                    evenement.details or "",
                ]
            )

    return chemin_destination

def exporter_journal_audit_csv(
    destination: str | Path,
    chemin_base: str | Path = CHEMIN_BASE_PAR_DEFAUT,
    *,
    recherche: str | None = None,
    categorie: str | None = None,
    action: str | None = None,
    date_debut: str | None = None,
    date_fin: str | None = None,
    limite: int | None = 500,
) -> Path:
    """Exporte localement le journal d'audit dans un CSV compatible Excel."""
    chemin_destination = Path(destination)

    if chemin_destination.suffix.lower() != ".csv":
        raise ValueError(
            "Le journal d'audit doit être exporté dans un fichier .csv."
        )

    terme = (recherche or "").strip()

    if terme:
        evenements = rechercher_evenements(
            terme,
            chemin_base,
        )
    else:
        evenements = lister_evenements(
            chemin_base,
            limite=limite,
        )

    evenements = filtrer_evenements_audit(
        evenements,
        categorie=categorie,
        action=action,
        date_debut=date_debut,
        date_fin=date_fin,
    )

    return exporter_evenements_audit_csv(
        chemin_destination,
        evenements,
    )

def formater_evenement_audit_details(
    evenement: EvenementAudit,
) -> str:
    """Prépare une vue lisible d'un événement pour l'interface."""
    return "\n".join(
        [
            f"Date / heure : {evenement.date_creation}",
            f"Catégorie : {evenement.categorie}",
            f"Action : {evenement.action}",
            f"Référence : {evenement.reference or '-'}",
            "",
            "Détails :",
            evenement.details or "-",
        ]
    )
