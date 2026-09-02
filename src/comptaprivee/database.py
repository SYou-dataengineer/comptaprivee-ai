"""Stockage local des factures dans une base de données SQLite."""

import sqlite3
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from .facture_parser import DonneesFacture


CHEMIN_BASE_PAR_DEFAUT = Path("data") / "comptaprivee.db"


@dataclass(frozen=True)
class FactureEnregistree:
    """Représente une facture enregistrée dans la base de données."""

    identifiant: int
    numero: str | None
    date: str | None
    fournisseur: str | None
    client: str | None
    sous_total: Decimal | None
    tps: Decimal | None
    tvq: Decimal | None
    total: Decimal | None
    date_creation: str


@dataclass(frozen=True)
class FactureCorbeille:
    """Représente une facture placée dans la corbeille locale."""

    identifiant: int
    numero: str | None
    date: str | None
    fournisseur: str | None
    client: str | None
    sous_total: Decimal | None
    tps: Decimal | None
    tvq: Decimal | None
    total: Decimal | None
    date_creation: str
    date_suppression: str


def ouvrir_connexion(
    chemin_base: str | Path = CHEMIN_BASE_PAR_DEFAUT,
) -> sqlite3.Connection:
    """Ouvre une connexion vers la base SQLite locale."""
    chemin = Path(chemin_base)
    chemin.parent.mkdir(parents=True, exist_ok=True)

    connexion = sqlite3.connect(chemin)
    connexion.row_factory = sqlite3.Row

    return connexion


def initialiser_base(
    chemin_base: str | Path = CHEMIN_BASE_PAR_DEFAUT,
) -> Path:
    """Crée la base et la table des factures si nécessaire."""
    chemin = Path(chemin_base)

    with ouvrir_connexion(chemin) as connexion:
        connexion.execute(
            """
            CREATE TABLE IF NOT EXISTS factures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero TEXT,
                date_facture TEXT,
                fournisseur TEXT,
                client TEXT,
                sous_total TEXT,
                tps TEXT,
                tvq TEXT,
                total TEXT,
                date_creation TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        connexion.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            index_factures_numero_unique
            ON factures(numero)
            WHERE numero IS NOT NULL AND numero != ''
            """
        )

    return chemin


def decimal_vers_texte(valeur: Decimal | None) -> str | None:
    """Convertit un montant décimal en texte pour SQLite."""
    if valeur is None:
        return None

    return format(valeur, ".2f")


def texte_vers_decimal(valeur: str | None) -> Decimal | None:
    """Convertit un montant SQLite en nombre décimal."""
    if valeur is None:
        return None

    return Decimal(valeur)


def ligne_vers_facture(ligne: sqlite3.Row) -> FactureEnregistree:
    """Transforme une ligne SQLite en facture enregistrée."""
    return FactureEnregistree(
        identifiant=ligne["id"],
        numero=ligne["numero"],
        date=ligne["date_facture"],
        fournisseur=ligne["fournisseur"],
        client=ligne["client"],
        sous_total=texte_vers_decimal(ligne["sous_total"]),
        tps=texte_vers_decimal(ligne["tps"]),
        tvq=texte_vers_decimal(ligne["tvq"]),
        total=texte_vers_decimal(ligne["total"]),
        date_creation=ligne["date_creation"],
    )


def enregistrer_facture(
    facture: DonneesFacture,
    chemin_base: str | Path = CHEMIN_BASE_PAR_DEFAUT,
) -> FactureEnregistree:
    """Enregistre une facture et retourne les données sauvegardées."""
    initialiser_base(chemin_base)

    try:
        with ouvrir_connexion(chemin_base) as connexion:
            curseur = connexion.execute(
                """
                INSERT INTO factures (
                    numero,
                    date_facture,
                    fournisseur,
                    client,
                    sous_total,
                    tps,
                    tvq,
                    total
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    facture.numero,
                    facture.date,
                    facture.fournisseur,
                    facture.client,
                    decimal_vers_texte(facture.sous_total),
                    decimal_vers_texte(facture.tps),
                    decimal_vers_texte(facture.tvq),
                    decimal_vers_texte(facture.total),
                ),
            )

            identifiant = curseur.lastrowid

            ligne = connexion.execute(
                """
                SELECT *
                FROM factures
                WHERE id = ?
                """,
                (identifiant,),
            ).fetchone()

    except sqlite3.IntegrityError as erreur:
        raise ValueError(
            f"La facture numéro {facture.numero!r} existe déjà."
        ) from erreur

    if ligne is None:
        raise RuntimeError(
            "La facture a été enregistrée, mais elle est introuvable."
        )

    resultat = ligne_vers_facture(ligne)

    from .audit_log import journaliser_sans_bloquer

    journaliser_sans_bloquer(
        "Facture enregistrée",
        "facture",
        details=(
            f"Fournisseur : {resultat.fournisseur or '-'}; "
            f"Total : {resultat.total if resultat.total is not None else '-'}"
        ),
        reference=resultat.numero,
        chemin_base=chemin_base,
    )

    return resultat


def lister_factures(
    chemin_base: str | Path = CHEMIN_BASE_PAR_DEFAUT,
) -> list[FactureEnregistree]:
    """Retourne toutes les factures, de la plus récente à l’ancienne."""
    initialiser_base(chemin_base)

    with ouvrir_connexion(chemin_base) as connexion:
        lignes = connexion.execute(
            """
            SELECT *
            FROM factures
            ORDER BY id DESC
            """
        ).fetchall()

    return [ligne_vers_facture(ligne) for ligne in lignes]


def rechercher_factures(
    recherche: str,
    chemin_base: str | Path = CHEMIN_BASE_PAR_DEFAUT,
) -> list[FactureEnregistree]:
    """Recherche des factures dans les principaux champs textuels."""
    initialiser_base(chemin_base)

    valeur_recherchee = f"%{recherche.strip()}%"

    with ouvrir_connexion(chemin_base) as connexion:
        lignes = connexion.execute(
            """
            SELECT *
            FROM factures
            WHERE numero LIKE ? COLLATE NOCASE
               OR date_facture LIKE ? COLLATE NOCASE
               OR fournisseur LIKE ? COLLATE NOCASE
               OR client LIKE ? COLLATE NOCASE
            ORDER BY id DESC
            """,
            (
                valeur_recherchee,
                valeur_recherchee,
                valeur_recherchee,
                valeur_recherchee,
            ),
        ).fetchall()

    return [ligne_vers_facture(ligne) for ligne in lignes]


def supprimer_facture(
    identifiant: int,
    chemin_base: str | Path = CHEMIN_BASE_PAR_DEFAUT,
) -> bool:
    """Supprime une facture et indique si elle existait."""
    initialiser_base(chemin_base)

    with ouvrir_connexion(chemin_base) as connexion:
        curseur = connexion.execute(
            """
            DELETE FROM factures
            WHERE id = ?
            """,
            (identifiant,),
        )

    return curseur.rowcount > 0

def initialiser_corbeille(
    chemin_base: str | Path = CHEMIN_BASE_PAR_DEFAUT,
) -> Path:
    """Crée la table locale de corbeille si nécessaire."""
    chemin = initialiser_base(chemin_base)

    with ouvrir_connexion(chemin) as connexion:
        connexion.execute(
            """
            CREATE TABLE IF NOT EXISTS factures_corbeille (
                id INTEGER PRIMARY KEY,
                numero TEXT,
                date_facture TEXT,
                fournisseur TEXT,
                client TEXT,
                sous_total TEXT,
                tps TEXT,
                tvq TEXT,
                total TEXT,
                date_creation TEXT NOT NULL,
                date_suppression TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

    return chemin


def ligne_vers_facture_corbeille(
    ligne: sqlite3.Row,
) -> FactureCorbeille:
    """Transforme une ligne SQLite de corbeille en facture."""
    return FactureCorbeille(
        identifiant=ligne["id"],
        numero=ligne["numero"],
        date=ligne["date_facture"],
        fournisseur=ligne["fournisseur"],
        client=ligne["client"],
        sous_total=texte_vers_decimal(ligne["sous_total"]),
        tps=texte_vers_decimal(ligne["tps"]),
        tvq=texte_vers_decimal(ligne["tvq"]),
        total=texte_vers_decimal(ligne["total"]),
        date_creation=ligne["date_creation"],
        date_suppression=ligne["date_suppression"],
    )


def mettre_facture_corbeille(
    identifiant: int,
    chemin_base: str | Path = CHEMIN_BASE_PAR_DEFAUT,
) -> bool:
    """Déplace une facture active vers la corbeille locale."""
    initialiser_corbeille(chemin_base)

    with ouvrir_connexion(chemin_base) as connexion:
        ligne = connexion.execute(
            """
            SELECT *
            FROM factures
            WHERE id = ?
            """,
            (identifiant,),
        ).fetchone()

        if ligne is None:
            return False

        connexion.execute(
            """
            INSERT OR REPLACE INTO factures_corbeille (
                id, numero, date_facture, fournisseur, client,
                sous_total, tps, tvq, total, date_creation,
                date_suppression
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                ligne["id"],
                ligne["numero"],
                ligne["date_facture"],
                ligne["fournisseur"],
                ligne["client"],
                ligne["sous_total"],
                ligne["tps"],
                ligne["tvq"],
                ligne["total"],
                ligne["date_creation"],
            ),
        )
        connexion.execute(
            "DELETE FROM factures WHERE id = ?",
            (identifiant,),
        )

        reference_audit = ligne["numero"]

    from .audit_log import journaliser_sans_bloquer

    journaliser_sans_bloquer(
        "Facture mise à la corbeille",
        "facture",
        reference=reference_audit,
        chemin_base=chemin_base,
    )

    return True


def lister_factures_corbeille(
    chemin_base: str | Path = CHEMIN_BASE_PAR_DEFAUT,
) -> list[FactureCorbeille]:
    """Retourne les factures présentes dans la corbeille."""
    initialiser_corbeille(chemin_base)

    with ouvrir_connexion(chemin_base) as connexion:
        lignes = connexion.execute(
            """
            SELECT *
            FROM factures_corbeille
            ORDER BY date_suppression DESC, id DESC
            """
        ).fetchall()

    return [ligne_vers_facture_corbeille(ligne) for ligne in lignes]


def restaurer_facture(
    identifiant: int,
    chemin_base: str | Path = CHEMIN_BASE_PAR_DEFAUT,
) -> bool:
    """Restaure une facture depuis la corbeille."""
    initialiser_corbeille(chemin_base)

    with ouvrir_connexion(chemin_base) as connexion:
        ligne = connexion.execute(
            "SELECT * FROM factures_corbeille WHERE id = ?",
            (identifiant,),
        ).fetchone()

        if ligne is None:
            return False

        try:
            connexion.execute(
                """
                INSERT INTO factures (
                    numero, date_facture, fournisseur, client,
                    sous_total, tps, tvq, total, date_creation
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ligne["numero"],
                    ligne["date_facture"],
                    ligne["fournisseur"],
                    ligne["client"],
                    ligne["sous_total"],
                    ligne["tps"],
                    ligne["tvq"],
                    ligne["total"],
                    ligne["date_creation"],
                ),
            )
        except sqlite3.IntegrityError as erreur:
            raise ValueError(
                "Impossible de restaurer la facture : une facture active "
                "avec le même numéro existe déjà."
            ) from erreur

        connexion.execute(
            "DELETE FROM factures_corbeille WHERE id = ?",
            (identifiant,),
        )

        reference_audit = ligne["numero"]

    from .audit_log import journaliser_sans_bloquer

    journaliser_sans_bloquer(
        "Facture restaurée",
        "facture",
        reference=reference_audit,
        chemin_base=chemin_base,
    )

    return True


def supprimer_facture_corbeille(
    identifiant: int,
    chemin_base: str | Path = CHEMIN_BASE_PAR_DEFAUT,
) -> bool:
    """Supprime définitivement une facture de la corbeille."""
    initialiser_corbeille(chemin_base)

    with ouvrir_connexion(chemin_base) as connexion:
        curseur = connexion.execute(
            "DELETE FROM factures_corbeille WHERE id = ?",
            (identifiant,),
        )

    return curseur.rowcount > 0
