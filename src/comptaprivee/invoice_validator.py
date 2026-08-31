"""Validation locale des données comptables extraites."""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum

from .facture_parser import DonneesFacture


TOLERANCE_MONTANT = Decimal("0.02")


class StatutValidation(str, Enum):
    """Statuts possibles après la validation d'une facture."""

    VALIDE = "VALIDE"
    A_VERIFIER = "À VÉRIFIER"
    ERREUR = "ERREUR"


@dataclass(frozen=True)
class ResultatValidation:
    """Résultat détaillé de la validation comptable."""

    statut: StatutValidation
    erreurs: tuple[str, ...] = field(default_factory=tuple)
    avertissements: tuple[str, ...] = field(default_factory=tuple)

    @property
    def est_valide(self) -> bool:
        """Indique si la facture ne contient aucun problème."""
        return self.statut == StatutValidation.VALIDE

    @property
    def autorise_export(self) -> bool:
        """Indique si l'export peut être effectué."""
        return self.statut != StatutValidation.ERREUR


def verifier_champs_obligatoires(
    facture: DonneesFacture,
) -> list[str]:
    """Retourne les avertissements pour les champs absents."""
    avertissements = []

    if not facture.numero:
        avertissements.append(
            "Le numéro de facture n'a pas été détecté."
        )

    if not facture.date:
        avertissements.append(
            "La date de la facture n'a pas été détectée."
        )

    if not facture.fournisseur:
        avertissements.append(
            "Le fournisseur n'a pas été détecté."
        )

    if facture.total is None:
        avertissements.append(
            "Le total de la facture n'a pas été détecté."
        )

    return avertissements


def verifier_montants_negatifs(
    facture: DonneesFacture,
) -> list[str]:
    """Détecte les montants comptables négatifs."""
    erreurs = []

    montants = {
        "sous-total": facture.sous_total,
        "TPS": facture.tps,
        "TVQ": facture.tvq,
        "total": facture.total,
    }

    for nom, montant in montants.items():
        if montant is not None and montant < Decimal("0"):
            erreurs.append(
                f"Le montant « {nom} » ne peut pas être négatif."
            )

    return erreurs


def verifier_calcul_total(
    facture: DonneesFacture,
) -> tuple[list[str], list[str]]:
    """Vérifie la cohérence entre sous-total, taxes et total."""
    erreurs = []
    avertissements = []

    montants_calcul = (
        facture.sous_total,
        facture.tps,
        facture.tvq,
        facture.total,
    )

    if all(montant is not None for montant in montants_calcul):
        assert facture.sous_total is not None
        assert facture.tps is not None
        assert facture.tvq is not None
        assert facture.total is not None

        total_calcule = (
            facture.sous_total
            + facture.tps
            + facture.tvq
        )
        difference = abs(total_calcule - facture.total)

        if difference > TOLERANCE_MONTANT:
            erreurs.append(
                "Le total est incohérent : "
                f"{facture.sous_total:.2f} + "
                f"{facture.tps:.2f} + "
                f"{facture.tvq:.2f} = "
                f"{total_calcule:.2f}, "
                f"mais le total indiqué est "
                f"{facture.total:.2f}."
            )
    else:
        champs_manquants = []

        if facture.sous_total is None:
            champs_manquants.append("sous-total")

        if facture.tps is None:
            champs_manquants.append("TPS")

        if facture.tvq is None:
            champs_manquants.append("TVQ")

        if facture.total is None:
            champs_manquants.append("total")

        avertissements.append(
            "Le calcul du total ne peut pas être vérifié. "
            "Montants manquants : "
            + ", ".join(champs_manquants)
            + "."
        )

    if (
        facture.sous_total is not None
        and facture.total is not None
        and facture.total < facture.sous_total
    ):
        erreurs.append(
            "Le total ne peut pas être inférieur au sous-total."
        )

    return erreurs, avertissements


def valider_facture(
    facture: DonneesFacture,
) -> ResultatValidation:
    """Valide les principaux champs d'une facture."""
    erreurs = verifier_montants_negatifs(facture)
    avertissements = verifier_champs_obligatoires(facture)

    erreurs_calcul, avertissements_calcul = (
        verifier_calcul_total(facture)
    )

    erreurs.extend(erreurs_calcul)
    avertissements.extend(avertissements_calcul)

    if erreurs:
        statut = StatutValidation.ERREUR
    elif avertissements:
        statut = StatutValidation.A_VERIFIER
    else:
        statut = StatutValidation.VALIDE

    return ResultatValidation(
        statut=statut,
        erreurs=tuple(erreurs),
        avertissements=tuple(avertissements),
    )