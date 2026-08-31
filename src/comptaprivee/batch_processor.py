"""Traitement local de plusieurs documents comptables."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .csv_exporter import exporter_factures_csv
from .facture_parser import DonneesFacture, extraire_donnees_facture
from .main import extraire_texte_document


@dataclass
class ErreurDocument:
    """Décrit une erreur rencontrée pendant le traitement d'un document."""

    chemin: Path
    message: str


@dataclass
class ResultatTraitementLot:
    """Contient les résultats d'un traitement de plusieurs documents."""

    factures: list[DonneesFacture] = field(default_factory=list)
    erreurs: list[ErreurDocument] = field(default_factory=list)

    @property
    def nombre_documents_reussis(self) -> int:
        """Retourne le nombre de documents analysés correctement."""
        return len(self.factures)

    @property
    def nombre_documents_en_erreur(self) -> int:
        """Retourne le nombre de documents qui ont produit une erreur."""
        return len(self.erreurs)


def traiter_documents(
    chemins_documents: Iterable[str | Path],
) -> ResultatTraitementLot:
    """Extrait les factures de plusieurs documents locaux."""
    resultat = ResultatTraitementLot()

    for chemin_document in chemins_documents:
        chemin = Path(chemin_document)

        try:
            texte = extraire_texte_document(chemin)

            if not texte.strip():
                raise ValueError(
                    "Aucun texte détecté dans ce document."
                )

            facture = extraire_donnees_facture(texte)
            resultat.factures.append(facture)

        except (FileNotFoundError, ValueError, OSError) as erreur:
            resultat.erreurs.append(
                ErreurDocument(
                    chemin=chemin,
                    message=str(erreur),
                )
            )

    return resultat


def traiter_et_exporter_documents(
    chemins_documents: Iterable[str | Path],
    chemin_csv: str | Path,
) -> ResultatTraitementLot:
    """Traite plusieurs documents et exporte les réussites dans un CSV."""
    resultat = traiter_documents(chemins_documents)

    if not resultat.factures:
        raise ValueError(
            "Aucune facture valide n'a été trouvée pour l'export."
        )

    exporter_factures_csv(
        resultat.factures,
        chemin_csv,
    )

    return resultat