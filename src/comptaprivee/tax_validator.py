"""Validation fiscale avancée des factures québécoises."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from .facture_parser import DonneesFacture


TPS_TAUX = Decimal("0.05")
TVQ_TAUX = Decimal("0.09975")
TOLERANCE = Decimal("0.02")


@dataclass(frozen=True)
class ResultatFiscal:
    """Résultat détaillé des contrôles fiscaux."""

    valide: bool
    erreurs: tuple[str, ...]
    avertissements: tuple[str, ...]


def _arrondir_monnaie(valeur: Decimal) -> Decimal:
    return valeur.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def valider_fiscalite(
    facture: DonneesFacture,
) -> ResultatFiscal:
    """Valide TPS, TVQ et cohérence du total."""
    erreurs: list[str] = []
    avertissements: list[str] = []

    if facture.sous_total is None:
        erreurs.append("Sous-total manquant.")

    if facture.total is None:
        erreurs.append("Total manquant.")

    if facture.sous_total is not None:
        tps_attendue = _arrondir_monnaie(
            facture.sous_total * TPS_TAUX
        )
        tvq_attendue = _arrondir_monnaie(
            facture.sous_total * TVQ_TAUX
        )

        if facture.tps is None:
            avertissements.append(
                "TPS manquante ou non détectée."
            )
        elif abs(facture.tps - tps_attendue) > TOLERANCE:
            erreurs.append(
                "TPS incohérente : "
                f"{facture.tps:.2f} au lieu de "
                f"{tps_attendue:.2f}."
            )

        if facture.tvq is None:
            avertissements.append(
                "TVQ manquante ou non détectée."
            )
        elif abs(facture.tvq - tvq_attendue) > TOLERANCE:
            erreurs.append(
                "TVQ incohérente : "
                f"{facture.tvq:.2f} au lieu de "
                f"{tvq_attendue:.2f}."
            )

    if (
        facture.sous_total is not None
        and facture.total is not None
        and facture.tps is not None
        and facture.tvq is not None
    ):
        total_attendu = _arrondir_monnaie(
            facture.sous_total
            + facture.tps
            + facture.tvq
        )

        if abs(facture.total - total_attendu) > TOLERANCE:
            erreurs.append(
                "Total incohérent : "
                f"{facture.total:.2f} au lieu de "
                f"{total_attendu:.2f}."
            )

    return ResultatFiscal(
        valide=not erreurs,
        erreurs=tuple(erreurs),
        avertissements=tuple(avertissements),
    )

def appliquer_validation_fiscale(
    facture: DonneesFacture,
    validation,
):
    """Fusionne le contrôle fiscal avec la validation comptable."""
    from .invoice_validator import (
        ResultatValidation,
        StatutValidation,
    )

    fiscal = valider_fiscalite(facture)

    erreurs = list(validation.erreurs)
    avertissements = list(validation.avertissements)

    for message in fiscal.erreurs:
        if message not in erreurs:
            erreurs.append(message)

    for message in fiscal.avertissements:
        if message not in avertissements:
            avertissements.append(message)

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
