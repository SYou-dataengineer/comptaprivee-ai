"""Orchestration de l'estimation fiscale locale 2025.

Ce module relie les briques déjà validées :
dossier fiscal verrouillé -> consolidation -> revenu -> fédéral -> Québec
-> rapprochement.

Il ne transmet aucune déclaration et conserve explicitement le statut
d'estimation soumise à validation comptable.
"""

from dataclasses import dataclass
from decimal import Decimal

from .tax_adjustments_2025 import (
    AjustementReer2025,
    appliquer_ajustement_reer_2025,
)
from .tax_engine_input_2025 import (
    BaseFiscaleEmploi2025,
    consolider_base_fiscale_emploi_2025,
)
from .tax_federal_2025 import (
    ImpotFederalPreliminaire2025,
    calculer_impot_federal_preliminaire_2025,
)
from .tax_income_2025 import (
    RevenuNetImposable2025,
    calculer_revenu_net_imposable_2025,
)
from .tax_quebec_2025 import (
    ImpotQuebecPreliminaire2025,
    calculer_impot_quebec_preliminaire_2025,
)
from .tax_reconciliation_2025 import (
    RapprochementFiscal2025,
    calculer_rapprochement_fiscal_2025,
)
from .tax_validated_case import DossierFiscalValide


@dataclass(frozen=True)
class EstimationFiscale2025:
    dossier: DossierFiscalValide
    base: BaseFiscaleEmploi2025
    revenu: RevenuNetImposable2025
    federal: ImpotFederalPreliminaire2025
    quebec: ImpotQuebecPreliminaire2025
    rapprochement: RapprochementFiscal2025
    ajustement_reer: AjustementReer2025


def calculer_estimation_fiscale_2025(
    dossier: DossierFiscalValide,
    ajustement_reer: AjustementReer2025 | None = None,
) -> EstimationFiscale2025:
    """Exécute le pipeline fiscal local 2025 sur un dossier verrouillé."""
    if dossier.annee_fiscale != 2025:
        raise ValueError(
            "L'estimation fiscale automatique est disponible "
            "uniquement pour l'année 2025."
        )

    base = consolider_base_fiscale_emploi_2025(dossier)
    revenu = calculer_revenu_net_imposable_2025(base)

    ajustement_reer_effectif = (
        ajustement_reer
        if ajustement_reer is not None
        else AjustementReer2025()
    )
    revenu = appliquer_ajustement_reer_2025(
        revenu,
        ajustement_reer_effectif,
    )

    federal = calculer_impot_federal_preliminaire_2025(base, revenu)
    quebec = calculer_impot_quebec_preliminaire_2025(revenu)
    rapprochement = calculer_rapprochement_fiscal_2025(
        base,
        federal,
        quebec,
    )

    return EstimationFiscale2025(
        dossier=dossier,
        base=base,
        revenu=revenu,
        federal=federal,
        quebec=quebec,
        rapprochement=rapprochement,
        ajustement_reer=ajustement_reer_effectif,
    )


def formater_montant_estimation(valeur: Decimal) -> str:
    """Formate un montant en présentation française."""
    texte = f"{valeur:,.2f}"
    texte = texte.replace(",", "\u00a0").replace(".", ",")
    return f"{texte} $"


def formater_estimation_fiscale_2025(
    estimation: EstimationFiscale2025,
) -> str:
    """Construit le résumé lisible destiné à la fenêtre de validation."""
    base = estimation.base
    revenu = estimation.revenu
    federal = estimation.federal
    quebec = estimation.quebec
    final = estimation.rapprochement

    lignes = [
        "ESTIMATION FISCALE 2025 — VALIDATION COMPTABLE OBLIGATOIRE",
        "",
        f"Client : {estimation.dossier.client}",
        f"Année fiscale : {estimation.dossier.annee_fiscale}",
        f"Province : {estimation.dossier.province}",
        "",
        "REVENU",
        f"Revenu d'emploi fédéral : {formater_montant_estimation(base.revenu_emploi_federal)}",
        f"Revenu net fédéral : {formater_montant_estimation(revenu.revenu_net_federal)}",
        f"Revenu imposable fédéral : {formater_montant_estimation(revenu.revenu_imposable_federal)}",
        f"Revenu d'emploi Québec : {formater_montant_estimation(base.revenu_emploi_quebec)}",
        f"Revenu net Québec : {formater_montant_estimation(revenu.revenu_net_quebec)}",
        f"Revenu imposable Québec : {formater_montant_estimation(revenu.revenu_imposable_quebec)}",
        *(
            [
                "",
                "AJUSTEMENTS VALIDÉS",
                "Déduction REER/RPAC/RVER : "
                f"{formater_montant_estimation(estimation.ajustement_reer.deduction_reer)}",
                "Plafond individuel confirmé : "
                f"{formater_montant_estimation(estimation.ajustement_reer.plafond_reer_confirme)}",
                "Source du plafond : "
                f"{estimation.ajustement_reer.source_plafond_reer}",
            ]
            if estimation.ajustement_reer.deduction_reer
            > Decimal("0")
            else []
        ),
        "",
        "FÉDÉRAL",
        f"Impôt fédéral brut : {formater_montant_estimation(federal.impot_brut)}",
        f"Crédits non remboursables inclus : {formater_montant_estimation(federal.credits_non_remboursables)}",
        f"Impôt fédéral de base : {formater_montant_estimation(final.impot_federal_de_base)}",
        f"Abattement Québec (16,5 %) : -{formater_montant_estimation(final.abattement_quebec)}",
        f"Impôt fédéral après abattement : {formater_montant_estimation(final.impot_federal_apres_abattement)}",
        "",
        "QUÉBEC",
        f"Impôt Québec brut : {formater_montant_estimation(quebec.impot_brut)}",
        f"Crédit personnel de base : -{formater_montant_estimation(quebec.credit_personnel_base)}",
        f"Impôt Québec préliminaire : {formater_montant_estimation(final.impot_quebec_preliminaire)}",
        "",
        "RAPPROCHEMENT",
        f"Impôt total préliminaire : {formater_montant_estimation(final.impot_total_preliminaire)}",
        f"Retenue fédérale T4 : {formater_montant_estimation(final.retenue_federale)}",
        f"Retenue Québec RL-1 : {formater_montant_estimation(final.retenue_quebec)}",
        f"Retenues totales : {formater_montant_estimation(final.retenues_totales)}",
        "",
        f"RÉSULTAT : {final.resultat}",
    ]

    if final.remboursement_estime > Decimal("0"):
        lignes.append(
            "Montant : "
            f"{formater_montant_estimation(final.remboursement_estime)}"
        )
    elif final.solde_estime > Decimal("0"):
        lignes.append(
            "Montant : "
            f"{formater_montant_estimation(final.solde_estime)}"
        )
    else:
        lignes.append("Montant : 0,00 $")

    lignes.extend(
        [
            "",
            f"Statut : {final.statut}",
            "",
            "LIMITATIONS ACTUELLES",
        ]
    )

    for limitation in final.limitations:
        lignes.append(f"• {limitation}")

    lignes.extend(
        [
            "",
            "Aucune donnée n'a quitté l'ordinateur.",
            "Aucune déclaration n'a été transmise à l'ARC "
            "ou à Revenu Québec.",
        ]
    )

    return "\n".join(lignes)
