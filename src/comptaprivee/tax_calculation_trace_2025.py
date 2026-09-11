"""Trace explicable du calcul fiscal local 2025.

Cette brique ne modifie aucun résultat fiscal. Elle explique une estimation
déjà calculée à partir d'un dossier verrouillé et validé par le comptable.
"""

from dataclasses import dataclass, replace
from decimal import Decimal

from .tax_donations_2025 import (
    credit_federal_dons_2025,
    credit_quebec_dons_2025,
)
from .tax_medical_expenses_2025 import (
    credit_federal_frais_medicaux_2025,
    credit_quebec_frais_medicaux_2025,
)
from .tax_tuition_2025 import (
    credit_federal_frais_scolarite_2025,
    credit_quebec_frais_scolarite_2025,
)
from .tax_estimation_2025 import (
    EstimationFiscale2025,
    formater_montant_estimation,
)
from .tax_union_dues_2025 import (
    credit_quebec_cotisations_2025,
)


@dataclass(frozen=True)
class LigneTraceCalcul2025:
    ordre: int
    section: str
    libelle: str
    source: str
    formule: str
    montant: Decimal


@dataclass(frozen=True)
class TraceCalculFiscal2025:
    client: str
    annee_fiscale: int
    province: str
    lignes: tuple[LigneTraceCalcul2025, ...]
    resultat: str
    montant_resultat: Decimal
    avertissements: tuple[str, ...]
    limitations: tuple[str, ...]


def _ligne(ordre, section, libelle, source, formule, montant):
    return LigneTraceCalcul2025(
        ordre=ordre,
        section=section,
        libelle=libelle,
        source=source,
        formule=formule,
        montant=montant,
    )


def _inserer_ligne_avant(lignes, libelle_cible, nouvelle_ligne):
    index = next(
        (i for i, ligne in enumerate(lignes) if ligne.libelle == libelle_cible),
        None,
    )
    if index is None:
        raise ValueError("Point d'insertion introuvable : " + libelle_cible)
    resultat = lignes[:index] + (nouvelle_ligne,) + lignes[index:]
    return tuple(
        replace(ligne, ordre=i + 1)
        for i, ligne in enumerate(resultat)
    )


def construire_trace_calcul_fiscal_2025(
    estimation: EstimationFiscale2025,
) -> TraceCalculFiscal2025:
    dossier = estimation.dossier
    base = estimation.base
    revenu = estimation.revenu
    federal = estimation.federal
    quebec = estimation.quebec
    final = estimation.rapprochement
    ajustement_reer = estimation.ajustement_reer
    cotisations = estimation.cotisations_syndicales
    dons = estimation.dons_bienfaisance
    frais_medicaux = estimation.frais_medicaux
    frais_scolarite = estimation.frais_scolarite

    formule_revenu_federal = (
        "Revenu d'emploi - déduction RRQ améliorée"
    )
    formule_revenu_quebec = (
        "Revenu Québec - déduction travailleur - déduction RRQ"
    )

    if ajustement_reer.deduction_reer > Decimal("0"):
        formule_revenu_federal += " - déduction REER validée"
        formule_revenu_quebec += " - déduction REER validée"

    if cotisations.montant_federal_admissible > Decimal("0"):
        formule_revenu_federal += (
            " - cotisations syndicales/professionnelles validées"
        )

    formule_impot_federal = (
        "Impôt fédéral brut - crédits non remboursables de base"
    )
    if dons.montant_admissible_federal > Decimal("0"):
        formule_impot_federal += " - crédit dons ligne 34900"
    if frais_medicaux.montant_admissible_federal > Decimal("0"):
        formule_impot_federal += (
            " - crédit frais médicaux lignes 33099 / 33200"
        )
    if frais_scolarite.montant_admissible_federal > Decimal("0"):
        formule_impot_federal += (
            " - crédit frais de scolarité ligne 32300"
        )

    formule_impot_quebec = "Impôt Québec brut - crédit personnel de base"
    if cotisations.montant_quebec_admissible > Decimal("0"):
        formule_impot_quebec += (
            " - crédit cotisations syndicales/professionnelles (10 %)"
        )
    if dons.montant_admissible_quebec > Decimal("0"):
        formule_impot_quebec += " - crédit dons ligne 395"
    if frais_medicaux.montant_admissible_quebec > Decimal("0"):
        formule_impot_quebec += " - crédit frais médicaux ligne 381"
    if frais_scolarite.montant_admissible_quebec > Decimal("0"):
        formule_impot_quebec += (
            " - crédit frais de scolarité/examen ligne 398"
        )

    if dossier.annee_fiscale != 2025:
        raise ValueError(
            "La trace de calcul actuelle accepte uniquement l'année 2025."
        )

    if not (
        dossier.client
        == base.client
        == revenu.client
        == federal.client
        == quebec.client
        == final.client
    ):
        raise ValueError(
            "Client incohérent entre les modules fiscaux."
        )

    lignes = (
        _ligne(
            1, "REVENU FÉDÉRAL", "Revenu d'emploi fédéral",
            "T4 case 14 — valeur validée",
            "Somme des revenus d'emploi fédéraux validés",
            base.revenu_emploi_federal,
        ),
        _ligne(
            2, "REVENU FÉDÉRAL", "Déduction RRQ améliorée",
            "T4/RL-1 — cotisations RRQ validées",
            "Première + deuxième cotisation supplémentaire RRQ",
            revenu.deduction_rrq_amelioree_federale,
        ),
        _ligne(
            3, "REVENU FÉDÉRAL", "Revenu imposable fédéral",
            "Moteur fiscal local 2025",
            formule_revenu_federal,
            revenu.revenu_imposable_federal,
        ),
        _ligne(
            4, "REVENU QUÉBEC", "Revenu d'emploi Québec",
            "RL-1 case A — valeur validée",
            "Somme des revenus d'emploi Québec validés",
            base.revenu_emploi_quebec,
        ),
        _ligne(
            5, "REVENU QUÉBEC", "Déduction travailleur Québec",
            "Paramètres fiscaux 2025 du moteur local",
            "Déduction pour travailleurs calculée par le moteur",
            revenu.deduction_travailleur_quebec,
        ),
        _ligne(
            6, "REVENU QUÉBEC", "Revenu imposable Québec",
            "Moteur fiscal local 2025",
            formule_revenu_quebec,
            revenu.revenu_imposable_quebec,
        ),
        _ligne(
            7, "FÉDÉRAL", "Impôt fédéral brut",
            "Barèmes fédéraux 2025 intégrés",
            "Application des tranches au revenu imposable fédéral",
            federal.impot_brut,
        ),
        _ligne(
            8, "FÉDÉRAL", "Crédits non remboursables",
            "Montants fédéraux admissibles du profil validé",
            "Base des crédits × taux de crédit fédéral",
            federal.credits_non_remboursables,
        ),
        _ligne(
            9, "FÉDÉRAL", "Impôt fédéral de base",
            "Moteur fiscal local 2025",
            formule_impot_federal,
            final.impot_federal_de_base,
        ),
        _ligne(
            10, "FÉDÉRAL", "Abattement Québec",
            "Rapprochement fiscal 2025",
            "16,5 % de l'impôt fédéral de base",
            final.abattement_quebec,
        ),
        _ligne(
            11, "FÉDÉRAL", "Impôt fédéral après abattement",
            "Rapprochement fiscal 2025",
            "Impôt fédéral de base - abattement Québec",
            final.impot_federal_apres_abattement,
        ),
        _ligne(
            12, "QUÉBEC", "Impôt Québec brut",
            "Barèmes Québec 2025 intégrés",
            "Application des tranches au revenu imposable Québec",
            quebec.impot_brut,
        ),
        _ligne(
            13, "QUÉBEC", "Crédit personnel de base",
            "Montant personnel de base Québec 2025",
            "Montant personnel de base × taux du crédit",
            quebec.credit_personnel_base,
        ),
        _ligne(
            14, "QUÉBEC", "Impôt Québec préliminaire",
            "Moteur fiscal local 2025",
            formule_impot_quebec,
            final.impot_quebec_preliminaire,
        ),
        _ligne(
            15, "RAPPROCHEMENT", "Impôt total préliminaire",
            "Moteur fiscal local 2025",
            "Impôt fédéral après abattement + impôt Québec",
            final.impot_total_preliminaire,
        ),
        _ligne(
            16, "RAPPROCHEMENT", "Retenues totales",
            "T4 case 22 + RL-1 case E — valeurs validées",
            "Retenue fédérale + retenue Québec",
            final.retenues_totales,
        ),
    )

    if ajustement_reer.deduction_reer > Decimal("0"):
        lignes = _inserer_ligne_avant(
            lignes,
            "Revenu imposable fédéral",
            _ligne(
                0,
                "REVENU FÉDÉRAL",
                "Déduction REER/RPAC/RVER validée",
                "ARC ligne 20800 / Revenu Québec ligne 214 — validation comptable",
                "Montant réclamé limité au plafond individuel REER confirmé",
                ajustement_reer.deduction_reer,
            ),
        )

    if cotisations.montant_federal_admissible > Decimal("0"):
        lignes = _inserer_ligne_avant(
            lignes,
            "Revenu imposable fédéral",
            _ligne(
                0,
                "REVENU FÉDÉRAL",
                "Cotisations syndicales/professionnelles — fédéral",
                (
                    "ARC ligne 21200 — "
                    + cotisations.source_federale
                    + " — validation comptable et dédoublonnage"
                ),
                "Montant fédéral admissible déduit du revenu net et imposable",
                cotisations.montant_federal_admissible,
            ),
        )

    if cotisations.montant_quebec_admissible > Decimal("0"):
        lignes = _inserer_ligne_avant(
            lignes,
            "Impôt Québec préliminaire",
            _ligne(
                0,
                "QUÉBEC",
                "Crédit cotisations syndicales/professionnelles — Québec",
                (
                    "Revenu Québec ligne 397.1 — "
                    + cotisations.source_quebec
                    + " — validation comptable"
                ),
                "Base admissible validée × 10 %",
                credit_quebec_cotisations_2025(cotisations),
            ),
        )

    if dons.montant_admissible_federal > Decimal("0"):
        lignes = _inserer_ligne_avant(
            lignes,
            "Impôt fédéral de base",
            _ligne(
                0,
                "FÉDÉRAL",
                "Crédit fédéral pour dons",
                (
                    "ARC annexe 9 / ligne 34900 — "
                    + dons.source_federale
                    + " — validation comptable"
                ),
                (
                    "14,5 % des premiers 200 $ + 29 % de "
                    "l'excédent — profil simple 2025"
                ),
                credit_federal_dons_2025(
                    dons,
                    revenu.revenu_imposable_federal,
                ),
            ),
        )

    if dons.montant_admissible_quebec > Decimal("0"):
        lignes = _inserer_ligne_avant(
            lignes,
            "Impôt Québec préliminaire",
            _ligne(
                0,
                "QUÉBEC",
                "Crédit Québec pour dons",
                (
                    "Revenu Québec ligne 395 — "
                    + dons.source_quebec
                    + " — validation comptable"
                ),
                (
                    "20 % des premiers 200 $ + 24 % de "
                    "l'excédent — profil simple 2025"
                ),
                credit_quebec_dons_2025(
                    dons,
                    revenu.revenu_imposable_quebec,
                ),
            ),
        )

    if frais_medicaux.montant_admissible_federal > Decimal("0"):
        lignes = _inserer_ligne_avant(
            lignes,
            "Impôt fédéral de base",
            _ligne(
                0,
                "FÉDÉRAL",
                "Crédit fédéral pour frais médicaux",
                (
                    "ARC lignes 33099 / 33200 — "
                    + frais_medicaux.source_federale
                    + " — validation comptable"
                ),
                (
                    "Frais admissibles - moindre de 3 % du revenu net "
                    "ou 2 834 $, puis × 14,5 %"
                ),
                credit_federal_frais_medicaux_2025(
                    frais_medicaux,
                    revenu.revenu_net_federal,
                ),
            ),
        )

    if frais_medicaux.montant_admissible_quebec > Decimal("0"):
        lignes = _inserer_ligne_avant(
            lignes,
            "Impôt Québec préliminaire",
            _ligne(
                0,
                "QUÉBEC",
                "Crédit Québec pour frais médicaux",
                (
                    "Revenu Québec ligne 381 — "
                    + frais_medicaux.source_quebec
                    + " — validation comptable"
                ),
                (
                    "Frais admissibles - 3 % du revenu net Québec, "
                    "puis × 20 % — profil sans conjoint"
                ),
                credit_quebec_frais_medicaux_2025(
                    frais_medicaux,
                    revenu.revenu_net_quebec,
                ),
            ),
        )

    if frais_scolarite.montant_admissible_federal > Decimal("0"):
        lignes = _inserer_ligne_avant(
            lignes,
            "Impôt fédéral de base",
            _ligne(
                0,
                "FÉDÉRAL",
                "Crédit fédéral pour frais de scolarité",
                (
                    "ARC annexe 11 / ligne 32300 — "
                    + frais_scolarite.source_federale
                    + " — validation comptable"
                ),
                (
                    "Montant admissible 2025 × 14,5 % — "
                    "aucun report/transfert dans ce profil"
                ),
                credit_federal_frais_scolarite_2025(
                    frais_scolarite
                ),
            ),
        )

    if frais_scolarite.montant_admissible_quebec > Decimal("0"):
        lignes = _inserer_ligne_avant(
            lignes,
            "Impôt Québec préliminaire",
            _ligne(
                0,
                "QUÉBEC",
                "Crédit Québec pour frais de scolarité / examen",
                (
                    "Revenu Québec annexe T / ligne 398 — "
                    + frais_scolarite.source_quebec
                    + " — validation comptable"
                ),
                (
                    "Montant admissible 2025 × 8 % — "
                    "aucun report/transfert dans ce profil"
                ),
                credit_quebec_frais_scolarite_2025(
                    frais_scolarite
                ),
            ),
        )

    prochain_ordre = len(lignes) + 1

    if final.remboursement_estime > Decimal("0"):
        montant = final.remboursement_estime
        formule = "Retenues totales - impôt total préliminaire"
    elif final.solde_estime > Decimal("0"):
        montant = final.solde_estime
        formule = "Impôt total préliminaire - retenues totales"
    else:
        montant = Decimal("0")
        formule = "Retenues totales = impôt total préliminaire"

    lignes += (
        _ligne(
            prochain_ordre, "RÉSULTAT", final.resultat,
            "Rapprochement fiscal 2025",
            formule,
            montant,
        ),
    )

    return TraceCalculFiscal2025(
        client=dossier.client,
        annee_fiscale=dossier.annee_fiscale,
        province=dossier.province,
        lignes=lignes,
        resultat=final.resultat,
        montant_resultat=montant,
        avertissements=base.avertissements,
        limitations=final.limitations,
    )


def formater_trace_calcul_fiscal_2025(
    trace: TraceCalculFiscal2025,
) -> str:
    lignes = [
        "TRACE DE CALCUL FISCAL 2025 — VALIDATION COMPTABLE OBLIGATOIRE",
        "",
        f"Client : {trace.client}",
        f"Année fiscale : {trace.annee_fiscale}",
        f"Province : {trace.province}",
        "",
        (
            "Cette trace explique l'estimation déjà calculée. "
            "Elle ne refait pas l'OCR."
        ),
    ]

    section = None
    for ligne in trace.lignes:
        if ligne.section != section:
            lignes.extend(["", ligne.section])
            section = ligne.section
        lignes.extend(
            [
                f"[{ligne.ordre:02d}] {ligne.libelle}",
                f"Source  : {ligne.source}",
                f"Formule : {ligne.formule}",
                "Montant : "
                f"{formater_montant_estimation(ligne.montant)}",
            ]
        )

    if trace.avertissements:
        lignes.extend(["", "AVERTISSEMENTS"])
        lignes.extend(f"• {x}" for x in trace.avertissements)

    lignes.extend(["", "LIMITATIONS ACTUELLES"])
    lignes.extend(f"• {x}" for x in trace.limitations)

    lignes.extend(
        [
            "",
            "Aucune donnée n'a quitté l'ordinateur.",
            "Aucune déclaration n'a été transmise à l'ARC "
            "ou à Revenu Québec.",
        ]
    )
    return "\n".join(lignes)
