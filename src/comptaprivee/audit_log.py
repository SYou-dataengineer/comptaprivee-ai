"""Journal d'audit local de ComptaPrivée AI."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
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
