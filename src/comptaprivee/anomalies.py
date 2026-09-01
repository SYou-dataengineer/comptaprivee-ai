"""Détection locale d'anomalies dans les factures enregistrées."""

from dataclasses import dataclass
from decimal import Decimal

from .database import FactureEnregistree


TOLERANCE_MONTANT = Decimal("0.02")


@dataclass(frozen=True)
class AnomalieFacture:
    """Anomalie détectée dans une facture enregistrée."""

    identifiant: int
    numero: str
    niveau: str
    message: str


def detecter_anomalies_facture(
    facture: FactureEnregistree,
) -> list[AnomalieFacture]:
    """Détecte les principales anomalies comptables d'une facture."""
    anomalies: list[AnomalieFacture] = []
    numero = facture.numero or f"ID {facture.identifiant}"

    def ajouter(niveau: str, message: str) -> None:
        anomalies.append(
            AnomalieFacture(
                identifiant=facture.identifiant,
                numero=numero,
                niveau=niveau,
                message=message,
            )
        )

    if not facture.numero:
        ajouter(
            "À vérifier",
            "Numéro de facture manquant.",
        )

    if not facture.date:
        ajouter(
            "À vérifier",
            "Date de facture manquante.",
        )

    if not facture.fournisseur:
        ajouter(
            "À vérifier",
            "Fournisseur manquant.",
        )

    if facture.total is None:
        ajouter(
            "À vérifier",
            "Total manquant.",
        )

    montants = {
        "sous-total": facture.sous_total,
        "TPS": facture.tps,
        "TVQ": facture.tvq,
        "total": facture.total,
    }

    for nom, montant in montants.items():
        if montant is not None and montant < Decimal("0"):
            ajouter(
                "Erreur",
                f"Montant négatif détecté pour {nom}.",
            )

    if facture.tps is None:
        ajouter(
            "À vérifier",
            "TPS manquante.",
        )

    if facture.tvq is None:
        ajouter(
            "À vérifier",
            "TVQ manquante.",
        )

    valeurs_total = (
        facture.sous_total,
        facture.tps,
        facture.tvq,
        facture.total,
    )

    if all(valeur is not None for valeur in valeurs_total):
        assert facture.sous_total is not None
        assert facture.tps is not None
        assert facture.tvq is not None
        assert facture.total is not None

        total_calcule = (
            facture.sous_total
            + facture.tps
            + facture.tvq
        )

        if abs(total_calcule - facture.total) > TOLERANCE_MONTANT:
            ajouter(
                "Erreur",
                (
                    "Total incohérent : "
                    f"{total_calcule:.2f} attendu, "
                    f"{facture.total:.2f} enregistré."
                ),
            )

    if (
        facture.sous_total is not None
        and facture.total is not None
        and facture.total < facture.sous_total
    ):
        ajouter(
            "Erreur",
            "Le total est inférieur au sous-total.",
        )

    return anomalies


def detecter_anomalies(
    factures: list[FactureEnregistree],
) -> list[AnomalieFacture]:
    """Détecte les anomalies sur une liste de factures."""
    resultat: list[AnomalieFacture] = []

    for facture in factures:
        resultat.extend(
            detecter_anomalies_facture(facture)
        )

    return resultat
