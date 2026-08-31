"""Traitement local de plusieurs documents comptables."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .csv_exporter import exporter_factures_csv
from .facture_parser import DonneesFacture, extraire_donnees_facture
from .invoice_validator import (
    ResultatValidation,
    StatutValidation,
    valider_facture,
)
from .main import extraire_texte_document


@dataclass(frozen=True)
class ErreurDocument:
    """Décrit une erreur rencontrée pendant le traitement."""

    chemin: Path
    message: str


@dataclass(frozen=True)
class DocumentTraite:
    """Associe un document à sa facture et à sa validation."""

    chemin: Path
    facture: DonneesFacture
    validation: ResultatValidation


@dataclass
class ResultatTraitementLot:
    """Contient les résultats d'un traitement par lot."""

    documents_traites: list[DocumentTraite] = field(
        default_factory=list
    )
    erreurs: list[ErreurDocument] = field(default_factory=list)

    @property
    def factures(self) -> list[DonneesFacture]:
        """Retourne les factures autorisées pour l'export."""
        return [
            document.facture
            for document in self.documents_traites
        ]

    @property
    def nombre_documents_reussis(self) -> int:
        """Retourne le nombre de documents exportables."""
        return len(self.documents_traites)

    @property
    def nombre_documents_en_erreur(self) -> int:
        """Retourne le nombre de documents bloqués."""
        return len(self.erreurs)

    @property
    def nombre_factures_valides(self) -> int:
        """Retourne le nombre de factures entièrement valides."""
        return sum(
            document.validation.statut
            == StatutValidation.VALIDE
            for document in self.documents_traites
        )

    @property
    def nombre_factures_a_verifier(self) -> int:
        """Retourne le nombre de factures nécessitant une vérification."""
        return sum(
            document.validation.statut
            == StatutValidation.A_VERIFIER
            for document in self.documents_traites
        )


def creer_message_erreurs_validation(
    validation: ResultatValidation,
) -> str:
    """Crée un message décrivant les erreurs comptables."""
    return "Validation comptable échouée : " + "; ".join(
        validation.erreurs
    )


def traiter_documents(
    chemins_documents: Iterable[str | Path],
) -> ResultatTraitementLot:
    """Extrait et valide plusieurs documents locaux."""
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
            validation = valider_facture(facture)

            if not validation.autorise_export:
                raise ValueError(
                    creer_message_erreurs_validation(validation)
                )

            resultat.documents_traites.append(
                DocumentTraite(
                    chemin=chemin,
                    facture=facture,
                    validation=validation,
                )
            )

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
    """Traite, valide et exporte les factures autorisées."""
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