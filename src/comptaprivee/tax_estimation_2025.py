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
from .tax_donations_2025 import (
    DonsBienfaisance2025,
    appliquer_credit_federal_dons_2025,
    appliquer_credit_quebec_dons_2025,
    credit_federal_dons_2025,
    credit_quebec_dons_2025,
)
from .tax_disability_2025 import (
    CreditDeficience2025,
    appliquer_credit_federal_handicap_2025,
    appliquer_credit_quebec_deficience_2025,
    credit_federal_handicap_2025,
    credit_quebec_deficience_2025,
)
from .tax_drug_insurance_2025 import (
    AssuranceMedicamentsQuebec2025,
    code_exemption_case_449_2025,
    cotisation_assurance_medicaments_2025,
    valider_assurance_medicaments_2025,
)
from .tax_medical_expenses_2025 import (
    FraisMedicaux2025,
    appliquer_credit_federal_frais_medicaux_2025,
    appliquer_credit_quebec_frais_medicaux_2025,
    credit_federal_frais_medicaux_2025,
    credit_quebec_frais_medicaux_2025,
)
from .tax_tuition_2025 import (
    FraisScolarite2025,
    appliquer_credit_federal_frais_scolarite_2025,
    appliquer_credit_quebec_frais_scolarite_2025,
    credit_federal_frais_scolarite_2025,
    credit_quebec_frais_scolarite_2025,
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
from .tax_union_dues_2025 import (
    CotisationsSyndicalesProfessionnelles2025,
    appliquer_credit_quebec_cotisations_2025,
    appliquer_deduction_federale_cotisations_2025,
    credit_quebec_cotisations_2025,
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
    cotisations_syndicales: CotisationsSyndicalesProfessionnelles2025
    dons_bienfaisance: DonsBienfaisance2025
    frais_medicaux: FraisMedicaux2025
    frais_scolarite: FraisScolarite2025
    credit_deficience: CreditDeficience2025
    assurance_medicaments: AssuranceMedicamentsQuebec2025


def calculer_estimation_fiscale_2025(
    dossier: DossierFiscalValide,
    ajustement_reer: AjustementReer2025 | None = None,
    cotisations_syndicales: (
        CotisationsSyndicalesProfessionnelles2025 | None
    ) = None,
    dons_bienfaisance: DonsBienfaisance2025 | None = None,
    frais_medicaux: FraisMedicaux2025 | None = None,
    frais_scolarite: FraisScolarite2025 | None = None,
    credit_deficience: CreditDeficience2025 | None = None,
    assurance_medicaments: (
        AssuranceMedicamentsQuebec2025 | None
    ) = None,
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

    cotisations_effectives = (
        cotisations_syndicales
        if cotisations_syndicales is not None
        else CotisationsSyndicalesProfessionnelles2025()
    )

    revenu = appliquer_deduction_federale_cotisations_2025(
        revenu,
        cotisations_effectives,
    )

    dons_effectifs = (
        dons_bienfaisance
        if dons_bienfaisance is not None
        else DonsBienfaisance2025()
    )

    frais_medicaux_effectifs = (
        frais_medicaux
        if frais_medicaux is not None
        else FraisMedicaux2025()
    )

    frais_scolarite_effectifs = (
        frais_scolarite
        if frais_scolarite is not None
        else FraisScolarite2025()
    )

    credit_deficience_effectif = (
        credit_deficience
        if credit_deficience is not None
        else CreditDeficience2025()
    )

    assurance_medicaments_effective = (
        assurance_medicaments
        if assurance_medicaments is not None
        else AssuranceMedicamentsQuebec2025()
    )
    valider_assurance_medicaments_2025(
        assurance_medicaments_effective
    )

    if (
        assurance_medicaments_effective.type_couverture.strip()
        and assurance_medicaments_effective.revenu_ligne_275
        != revenu.revenu_net_quebec
    ):
        raise ValueError(
            "Le revenu de la ligne 275 utilisé pour l'assurance "
            "médicaments doit correspondre au revenu net Québec "
            "calculé pour ce dossier."
        )

    federal = calculer_impot_federal_preliminaire_2025(base, revenu)
    federal = appliquer_credit_federal_dons_2025(
        federal,
        dons_effectifs,
        revenu.revenu_imposable_federal,
    )
    federal = appliquer_credit_federal_frais_medicaux_2025(
        federal,
        frais_medicaux_effectifs,
        revenu.revenu_net_federal,
    )
    federal = appliquer_credit_federal_frais_scolarite_2025(
        federal,
        frais_scolarite_effectifs,
    )
    federal = appliquer_credit_federal_handicap_2025(
        federal,
        credit_deficience_effectif,
    )
    quebec = calculer_impot_quebec_preliminaire_2025(revenu)
    quebec = appliquer_credit_quebec_cotisations_2025(
        quebec,
        cotisations_effectives,
    )
    quebec = appliquer_credit_quebec_dons_2025(
        quebec,
        dons_effectifs,
        revenu.revenu_imposable_quebec,
    )
    quebec = appliquer_credit_quebec_frais_medicaux_2025(
        quebec,
        frais_medicaux_effectifs,
        revenu.revenu_net_quebec,
    )
    quebec = appliquer_credit_quebec_frais_scolarite_2025(
        quebec,
        frais_scolarite_effectifs,
    )
    quebec = appliquer_credit_quebec_deficience_2025(
        quebec,
        credit_deficience_effectif,
    )
    rapprochement = calculer_rapprochement_fiscal_2025(
        base,
        federal,
        quebec,
        cotisation_assurance_medicaments=(
            cotisation_assurance_medicaments_2025(
                assurance_medicaments_effective
            )
        ),
    )

    return EstimationFiscale2025(
        dossier=dossier,
        base=base,
        revenu=revenu,
        federal=federal,
        quebec=quebec,
        rapprochement=rapprochement,
        ajustement_reer=ajustement_reer_effectif,
        cotisations_syndicales=cotisations_effectives,
        dons_bienfaisance=dons_effectifs,
        frais_medicaux=frais_medicaux_effectifs,
        frais_scolarite=frais_scolarite_effectifs,
        credit_deficience=credit_deficience_effectif,
        assurance_medicaments=assurance_medicaments_effective,
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
        *(
            [
                "",
                "COTISATIONS SYNDICALES / PROFESSIONNELLES VALIDÉES",
                "Cotisations fédérales — ligne 21200 : "
                f"{formater_montant_estimation(estimation.cotisations_syndicales.montant_federal_admissible)}",
                "Source fédérale : "
                f"{estimation.cotisations_syndicales.source_federale}",
                "Base Québec — ligne 397.1 : "
                f"{formater_montant_estimation(estimation.cotisations_syndicales.montant_quebec_admissible)}",
                "Crédit Québec (10 %) : "
                f"{formater_montant_estimation(credit_quebec_cotisations_2025(estimation.cotisations_syndicales))}",
                "Source Québec : "
                f"{estimation.cotisations_syndicales.source_quebec}",
            ]
            if (
                estimation.cotisations_syndicales.montant_federal_admissible
                > Decimal("0")
                or estimation.cotisations_syndicales.montant_quebec_admissible
                > Decimal("0")
            )
            else []
        ),
        *(
            [
                "",
                "DONS DE BIENFAISANCE VALIDÉS",
                "Montant admissible fédéral : "
                f"{formater_montant_estimation(estimation.dons_bienfaisance.montant_admissible_federal)}",
                "Crédit fédéral — ligne 34900 : "
                f"{formater_montant_estimation(credit_federal_dons_2025(estimation.dons_bienfaisance, revenu.revenu_imposable_federal))}",
                "Source fédérale : "
                f"{estimation.dons_bienfaisance.source_federale}",
                "Montant admissible Québec : "
                f"{formater_montant_estimation(estimation.dons_bienfaisance.montant_admissible_quebec)}",
                "Crédit Québec — ligne 395 : "
                f"{formater_montant_estimation(credit_quebec_dons_2025(estimation.dons_bienfaisance, revenu.revenu_imposable_quebec))}",
                "Source Québec : "
                f"{estimation.dons_bienfaisance.source_quebec}",
            ]
            if (
                estimation.dons_bienfaisance.montant_admissible_federal
                > Decimal("0")
                or estimation.dons_bienfaisance.montant_admissible_quebec
                > Decimal("0")
            )
            else []
        ),
        *(
            [
                "",
                "FRAIS MÉDICAUX VALIDÉS",
                "Montant admissible fédéral : "
                f"{formater_montant_estimation(estimation.frais_medicaux.montant_admissible_federal)}",
                "Crédit fédéral — lignes 33099 / 33200 : "
                f"{formater_montant_estimation(credit_federal_frais_medicaux_2025(estimation.frais_medicaux, revenu.revenu_net_federal))}",
                "Source fédérale : "
                f"{estimation.frais_medicaux.source_federale}",
                "Montant admissible Québec : "
                f"{formater_montant_estimation(estimation.frais_medicaux.montant_admissible_quebec)}",
                "Crédit Québec — ligne 381 : "
                f"{formater_montant_estimation(credit_quebec_frais_medicaux_2025(estimation.frais_medicaux, revenu.revenu_net_quebec))}",
                "Source Québec : "
                f"{estimation.frais_medicaux.source_quebec}",
            ]
            if (
                estimation.frais_medicaux.montant_admissible_federal
                > Decimal("0")
                or estimation.frais_medicaux.montant_admissible_quebec
                > Decimal("0")
            )
            else []
        ),
        *(
            [
                "",
                "FRAIS DE SCOLARITÉ / EXAMEN VALIDÉS",
                "Montant admissible fédéral : "
                f"{formater_montant_estimation(estimation.frais_scolarite.montant_admissible_federal)}",
                "Crédit fédéral — ligne 32300 : "
                f"{formater_montant_estimation(credit_federal_frais_scolarite_2025(estimation.frais_scolarite))}",
                "Source fédérale : "
                f"{estimation.frais_scolarite.source_federale}",
                "Montant admissible Québec : "
                f"{formater_montant_estimation(estimation.frais_scolarite.montant_admissible_quebec)}",
                "Crédit Québec — ligne 398 : "
                f"{formater_montant_estimation(credit_quebec_frais_scolarite_2025(estimation.frais_scolarite))}",
                "Source Québec : "
                f"{estimation.frais_scolarite.source_quebec}",
            ]
            if (
                estimation.frais_scolarite.montant_admissible_federal
                > Decimal("0")
                or estimation.frais_scolarite.montant_admissible_quebec
                > Decimal("0")
            )
            else []
        ),
        *(
            [
                "",
                "HANDICAP / DÉFICIENCE VALIDÉ(E)",
                *(
                    [
                        "Montant fédéral — ligne 31600 : "
                        "10 138,00 $",
                        "Crédit fédéral — ligne 31600 : "
                        f"{formater_montant_estimation(credit_federal_handicap_2025(estimation.credit_deficience))}",
                        "Source fédérale : "
                        f"{estimation.credit_deficience.source_federale}",
                    ]
                    if estimation.credit_deficience.reclamer_federal
                    else []
                ),
                *(
                    [
                        "Montant Québec — ligne 376 : "
                        "4 123,00 $",
                        "Crédit Québec — ligne 376 : "
                        f"{formater_montant_estimation(credit_quebec_deficience_2025(estimation.credit_deficience))}",
                        "Source Québec : "
                        f"{estimation.credit_deficience.source_quebec}",
                    ]
                    if estimation.credit_deficience.reclamer_quebec
                    else []
                ),
            ]
            if (
                estimation.credit_deficience.reclamer_federal
                or estimation.credit_deficience.reclamer_quebec
            )
            else []
        ),
        *(
            [
                "",
                "ASSURANCE MÉDICAMENTS QUÉBEC VALIDÉE",
                (
                    "Type de couverture : "
                    + (
                        "Régime public"
                        if (
                            estimation.assurance_medicaments
                            .type_couverture.strip().lower()
                            == "public"
                        )
                        else "Couverture collective"
                    )
                ),
                "Revenu net Québec / ligne 275 : "
                f"{formater_montant_estimation(estimation.assurance_medicaments.revenu_ligne_275)}",
                "Ligne 48 — annexe K : "
                f"{formater_montant_estimation(estimation.assurance_medicaments.revenu_ligne_48_annexe_k)}",
                "Cotisation Québec — ligne 447 : "
                f"{formater_montant_estimation(estimation.rapprochement.cotisation_assurance_medicaments)}",
                *(
                    [
                        "Code d'exemption — case 449 : "
                        f"{code_exemption_case_449_2025(estimation.assurance_medicaments)}",
                    ]
                    if code_exemption_case_449_2025(
                        estimation.assurance_medicaments
                    )
                    else []
                ),
                "Source : "
                f"{estimation.assurance_medicaments.source}",
            ]
            if estimation.assurance_medicaments.type_couverture.strip()
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
