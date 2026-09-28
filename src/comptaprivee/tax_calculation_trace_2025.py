"""Trace explicable du calcul fiscal local 2025.

Cette brique ne modifie aucun résultat fiscal. Elle explique une estimation
déjà calculée à partir d'un dossier verrouillé et validé par le comptable.
"""

from dataclasses import dataclass, replace
from decimal import Decimal


def construire_trace_fractionnement_2025(r):
    """Identités de conservation et formules auditées du dossier conjoint."""
    return (
        f'T1032 : 21000 cédant = 11600 bénéficiaire = {r.choix.montant_federal}; maximum = 50 % x {r.choix.cedant.t4a_016}.',
        f'Annexe Q : 245 cédant = 123 bénéficiaire = {r.choix.montant_quebec}.',
        f'Retenue fédérale déplacée = {r.choix.cedant.t4a_022} x {r.choix.montant_federal} / {r.choix.cedant.t4a_016} = {r.retenue_federale_transferee}.',
        f'Retenue Québec déplacée = {r.choix.cedant.rl2_j} x {r.choix.montant_quebec} / {r.choix.cedant.rl2_a} = {r.retenue_quebec_transferee}.',
        f'Revenus nets fédéraux conservés : {r.cedant.revenu_net_federal} + {r.beneficiaire.revenu_net_federal}.',
        f'Revenu familial Québec inchangé : {r.revenu_familial_quebec}.',
        f'Annexe B : somme des montants âge/retraite des deux personnes, moins une seule réduction familiale = {r.montant_361_couple}.',
        '31400 RPA : minimum du revenu de pension après fractionnement et de 2 000 $.',
        'FSS : pension Québec après 123/245; impôt fédéral après crédits et abattement Québec de 16,5 %.',
        'Solde de chaque conjoint = impôts fédéral + Québec + FSS - retenues après répartition.',
    )

from .tax_family_workers_benefit_2025 import trace_act_familial_2025
from .tax_age_retirement_2025 import (
    credit_quebec_age_retraite_2025,
    montant_age_2025,
    montant_ligne_361_age_retraite_2025,
    montant_revenus_retraite_2025,
    reduction_annexe_b_age_retraite_2025,
)
from .tax_federal_home_accessibility_2025 import (
    credit_federal_ligne_31285_2025,
    montant_ligne_31285_2025,
)
from .tax_federal_home_buyers_2025 import (
    credit_federal_ligne_31270_2025,
    montant_ligne_31270_2025,
)
from .tax_federal_caregiver_other_dependant_2025 import (
    description_partage_30450_2025,
    details_personnes_30450_2025,
    credit_federal_ligne_30450_2025,
    montant_ligne_30450_2025,
    nombre_personnes_charge_ligne_51120_2025,
)
from .tax_federal_caregiver_spouse_dependant_2025 import (
    TYPE_CONJOINT,
    credit_federal_ligne_30425_2025,
    montant_brut_avant_30300_30400_ligne_30425_2025,
    montant_ligne_30425_2025,
)
from .tax_federal_caregiver_child_2025 import (
    details_enfants_30500_2025,
    credit_federal_aidant_enfant_moins18_2025,
    montant_ligne_30500_2025,
    nombre_enfants_ligne_30499_2025,
)
from .tax_federal_eligible_dependant_2025 import (
    credit_federal_personne_charge_admissible_2025,
    montant_ligne_30400_2025,
)
from .tax_federal_spouse_2025 import (
    credit_federal_montant_conjoint_2025,
    montant_ligne_30300_2025,
)
from .tax_federal_age_pension_2025 import (
    credit_federal_age_pension_2025,
    montant_age_federal_2025,
    montant_pension_federal_2025,
)
from .tax_donations_2025 import (
    credit_federal_dons_2025,
    ventiler_credit_federal_dons_2025, ventiler_credit_quebec_dons_2025,
    credit_quebec_dons_2025,
)
from .tax_disability_2025 import (
    credit_federal_handicap_2025,
    montant_federal_handicap_2025,
    credit_quebec_deficience_2025,
)
from .tax_drug_insurance_2025 import (
    code_exemption_case_449_2025,
)
from .tax_living_alone_2025 import (
    credit_quebec_personne_vivant_seule_2025,
    montant_ligne_361_personne_vivant_seule_2025,
)
from .tax_medical_expenses_2025 import (
    credit_federal_frais_medicaux_2025,
    credit_quebec_frais_medicaux_2025,
)
from .tax_tuition_2025 import (
    credit_federal_frais_scolarite_2025,
    credit_quebec_frais_scolarite_2025,
)
from .tax_child_care_2025 import (
    deduction_frais_garde_federale_2025,
    limite_deux_tiers_revenu_gagne_2025,
    plafond_enfants_frais_garde_2025,
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
    formule_resultat: str
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
    deduction_celiapp = estimation.deduction_celiapp
    frais_garde_federaux = estimation.frais_garde_federaux
    depenses_emploi = estimation.depenses_emploi
    frais_demenagement = estimation.frais_demenagement
    pension_alimentaire = estimation.pension_alimentaire_payee
    autres_deductions = estimation.autres_deductions
    cotisations = estimation.cotisations_syndicales
    dons = estimation.dons_bienfaisance
    frais_medicaux = estimation.frais_medicaux
    frais_scolarite = estimation.frais_scolarite
    credit_deficience = estimation.credit_deficience
    assurance_medicaments = estimation.assurance_medicaments
    cotisations_excedentaires = estimation.cotisations_excedentaires
    personne_vivant_seule = estimation.personne_vivant_seule
    montants_age_retraite = estimation.montants_age_retraite
    credits_federaux_age_pension = (
        estimation.credits_federaux_age_pension
    )
    montant_conjoint_federal = (
        estimation.montant_conjoint_federal
    )
    personne_charge_admissible_federale = (
        estimation.personne_charge_admissible_federale
    )
    aidant_30425_federal = (
        estimation.aidant_conjoint_personne_charge_federal
    )
    accessibilite_domiciliaire_federale = (
        estimation.accessibilite_domiciliaire_federale
    )
    achat_habitation_federal = (
        estimation.achat_habitation_federal
    )
    aidant_30450_federal = (
        estimation.aidant_autre_personne_charge_federal
    )
    aidant_enfant_federal = (
        estimation.aidant_enfant_federal
    )

    formule_revenu_federal = (
        "Revenu d'emploi - déduction RRQ améliorée"
    )
    formule_revenu_quebec = (
        "Revenu Québec - déduction travailleur - déduction RRQ"
    )

    rqap = estimation.prestations_rqap
    rrq_rpc = estimation.prestations_rrq_rpc
    pensions = estimation.pensions
    psv = estimation.prestations_psv
    ae = estimation.prestations_ae
    if rqap.present:
        formule_revenu_federal += " + RQAP 11900 - remboursement 23200"
        formule_revenu_quebec += " + RQAP 110 - remboursement 246"

    if estimation.cotisations_rpa.montant_federal:
        formule_revenu_federal += " - déduction RPA ligne 20700"
    if estimation.cotisations_rpa.montant_quebec:
        formule_revenu_quebec += " - déduction RPA ligne 205"

    if ajustement_reer.deduction_reer > Decimal("0"):
        formule_revenu_federal += " - déduction REER validée"
        formule_revenu_quebec += " - déduction REER validée"

    if deduction_celiapp.deduction > Decimal("0"):
        formule_revenu_federal += " - déduction CELIAPP 20805"
        formule_revenu_quebec += " - déduction CELIAPP 215"

    deduction_frais_garde = deduction_frais_garde_federale_2025(
        frais_garde_federaux
    )
    if deduction_frais_garde > Decimal("0"):
        formule_revenu_federal += (
            " - frais de garde T778 / ligne 21400"
        )

    if depenses_emploi.deduction_federale_t777 > Decimal("0"):
        formule_revenu_federal += (
            " - dépenses d'emploi T777 / ligne 22900"
        )
    if depenses_emploi.deduction_quebec_tp59 > Decimal("0"):
        formule_revenu_quebec += (
            " - dépenses d'emploi TP-59 / ligne 207 code 07"
        )

    if frais_demenagement.deduction_federale_t1m > Decimal("0"):
        formule_revenu_federal += (
            " - frais de déménagement T1-M / ligne 21900"
        )
    if frais_demenagement.deduction_quebec_tp348 > Decimal("0"):
        formule_revenu_quebec += (
            " - frais de déménagement TP-348 / ligne 228"
        )

    if pension_alimentaire.deduction_federale_22000 > Decimal("0"):
        formule_revenu_federal += (
            " - pension alimentaire déductible / ligne 22000"
        )
    if pension_alimentaire.deduction_quebec_225 > Decimal("0"):
        formule_revenu_quebec += (
            " - pension alimentaire déductible / ligne 225"
        )

    if autres_deductions.deduction_federale_23200 > Decimal("0"):
        formule_revenu_federal += (
            " - autres déductions validées / ligne 23200"
        )
    if autres_deductions.deduction_quebec_250_code17 > Decimal("0"):
        formule_revenu_quebec += (
            " - autres déductions validées / ligne 250 code 17"
        )

    if cotisations.montant_federal_admissible > Decimal("0"):
        formule_revenu_federal += (
            " - cotisations syndicales/professionnelles validées"
        )
    if ae.present:
        formule_revenu_federal += " + AE 11900 - remboursement 23200 - récupération 23500"
        formule_revenu_quebec += " + AE 111 - remboursement 246 - récupération 250"

    if rrq_rpc.present:
        formule_revenu_federal += " + RRQ/RPC 11400 (T4A(P) 20)"
        formule_revenu_quebec += " + RRQ/RPC 119 (RL-2 C ou T4A(P) 20)"

    if psv.present:
        formule_revenu_federal += " + PSV 11300 + suppléments 14600 - récupération 23500 - déduction 25000"
        formule_revenu_quebec += " + PSV 114 + suppléments 148 - récupération 250 - déduction 295"

    if estimation.reports_pertes.present:
        formule_revenu_federal += " - pertes 25300 (imposable uniquement)"
        formule_revenu_quebec += " - pertes 290 + rajustement 276 (imposable uniquement)"
    if estimation.frais_placement.present:
        formule_revenu_federal += " - frais 22100"
        formule_revenu_quebec += " - frais 231 + rajustement 260 - report 252"
    if estimation.capital.present:
        formule_revenu_federal += " + gain imposable positif 12700"
        formule_revenu_quebec += " + gain imposable positif 139"
    if estimation.dividendes.present:
        formule_revenu_federal += " + dividendes majorés 12000 (12010 déjà inclus)"
        formule_revenu_quebec += " + dividendes majorés 128"
    if estimation.interets.present:
        formule_revenu_federal += " + intérêts directs 12100 + intérêts T3 13000"
        formule_revenu_quebec += " + intérêts 130"
    if estimation.placement_etranger.present:
        formule_revenu_federal += " + revenu étranger brut 12100"
        formule_revenu_quebec += " + revenu étranger brut 130"
    if estimation.remplacement.present:
        formule_revenu_federal += " + prestations 14400/14500 (25000 déduit uniquement de l’imposable)"
        formule_revenu_quebec += " + prestations 147/148 (295 déduit uniquement de l’imposable)"
    if estimation.retraits.present:
        formule_revenu_federal += " + retraits 12900/13000 - 23200"
        formule_revenu_quebec += " + retraits 154 - 250.6"
    if pensions.present:
        formule_revenu_federal += " + pensions 11500 / 13000 / 12100 selon âge et nature"
        formule_revenu_quebec += " + pensions 122, sans double compte des feuillets"

    formule_impot_federal = (
        "Impôt fédéral brut - crédits non remboursables de base"
    )
    if dons.montant_admissible_federal > Decimal("0") or dons.reports_federaux.activer:
        formule_impot_federal += " - crédit dons ligne 34900"
    if frais_medicaux.montant_admissible_federal > Decimal("0"):
        formule_impot_federal += (
            " - crédit frais médicaux lignes 33099 / 33200"
        )
    if frais_scolarite.montant_admissible_federal > Decimal("0"):
        formule_impot_federal += (
            " - crédit frais de scolarité ligne 32300"
        )
    if credit_deficience.reclamer_federal:
        formule_impot_federal += (
            " - crédit handicap ligne 31600"
        )
    if (
        credits_federaux_age_pension.reclamer_montant_age
        or credits_federaux_age_pension.reclamer_montant_pension
    ):
        formule_impot_federal += (
            " - crédit âge/pension lignes 30100/31400"
        )
    if montant_conjoint_federal.reclamer_montant:
        formule_impot_federal += (
            " - crédit conjoint ligne 30300"
        )
    if personne_charge_admissible_federale.reclamer_montant:
        formule_impot_federal += (
            " - crédit personne à charge admissible ligne 30400"
        )
    if aidant_30425_federal.reclamer_montant:
        formule_impot_federal += (
            " - crédit aidant naturel ligne 30425"
        )
    if accessibilite_domiciliaire_federale.reclamer_montant:
        formule_impot_federal += (
            " - crédit accessibilité domiciliaire ligne 31285"
        )
    if achat_habitation_federal.reclamer_montant:
        formule_impot_federal += (
            " - crédit achat habitation ligne 31270"
        )
    if aidant_30450_federal.reclamer_montant:
        formule_impot_federal += (
            " - crédit aidant naturel ligne 30450"
        )
    if aidant_enfant_federal.reclamer_montant:
        formule_impot_federal += (
            " - crédit aidant naturel enfant ligne 30500"
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
    if credit_deficience.reclamer_quebec:
        formule_impot_quebec += (
            " - crédit déficience ligne 376"
        )
    if personne_vivant_seule.reclamer_montant:
        formule_impot_quebec += (
            " - crédit personne vivant seule ligne 361"
        )
    if (
        montants_age_retraite.reclamer_age
        or montants_age_retraite.reclamer_revenus_retraite
    ):
        formule_impot_quebec += (
            " - crédit âge/retraite ligne 361"
        )

    if estimation.dividendes.present:
        formule_impot_federal += " - crédit dividendes 40425, plancher zéro avant abattement"
        formule_impot_quebec += " - crédit dividendes 415, plancher zéro"
    if estimation.credit_impot_etranger.present:
        formule_impot_quebec += " - crédit impôt étranger 409 confirmé via TP-772"
    formule_impot_total = (
        "Impôt fédéral après abattement + impôt Québec"
    )
    if rqap.present:
        formule_impot_total += " + FSS Québec 446"
    if ae.present:
        formule_impot_total += " + récupération AE 42200 (sans abattement) + FSS Québec 446"
    if estimation.capital.present:
        formule_impot_total += " + FSS capital 446 sur gain imposable"
    if estimation.dividendes.present:
        formule_impot_total += " + FSS dividendes 446 (montants réels)"
    if estimation.interets.present:
        formule_impot_total += " + FSS intérêts 446 (sans abattement)"
    if estimation.placement_etranger.present:
        formule_impot_total += " + FSS placement étranger 446"
    if estimation.retraits.present:
        formule_impot_total += " + FSS retraits 446"
    if pensions.present:
        formule_impot_total += " + FSS pensions 446 (sans abattement)"
    if psv.present:
        formule_impot_total += " + récupération PSV 42200 (sans abattement); FSS PSV nul"
    if rrq_rpc.present:
        formule_impot_total += " + FSS RRQ/RPC 446 (sans abattement)"
    if assurance_medicaments.type_couverture.strip():
        formule_impot_total += (
            " + cotisation assurance médicaments ligne 447"
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

    if federal.credits_federaux_complets is not None:
        composantes = "; ".join(
            part for part in formule_impot_federal.split(" - ")[1:]
            if not part.startswith("crédit dividendes")
        )
        formule_impot_federal = (
            "max(impôt brut - ligne 35000 - crédit dividendes 40425, 0)"
            "; composantes déjà incluses dans 35000 : " + composantes
        )

    lignes = (
        _ligne(
            1, "REVENU FÉDÉRAL", "Revenu d'emploi fédéral",
            "T4 cases 14 + 87 — crédit bénévoles choisi" if estimation.resultat_benevoles.reintegration_10100 else "T4 case 14 — valeur validée",
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
            formule_impot_federal + " = ligne 42900, avant 40500",
            final.impot_federal_de_base,
        ),
        _ligne(
            10, "FÉDÉRAL", "Abattement Québec",
            "Rapprochement fiscal 2025",
            "16,5 % de la ligne 42900, avant crédit étranger 40500",
            final.abattement_quebec,
        ),
        _ligne(
            11, "FÉDÉRAL", "Impôt fédéral après abattement",
            "Rapprochement fiscal 2025",
            ("max(impôt après 40500 - crédits 41600 (41000 + 41400), 0) + avances ACT 41500 - abattement 44000"
             if final.credits_ligne_41600 else "Impôt fédéral après 40500 + avances ACT 41500 - abattement Québec remboursable 44000"
             if final.avances_act_ligne_41500 else "Impôt fédéral après 40500 - abattement Québec remboursable 44000"),
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
            ("(Montant personnel de base - redressement 358) × taux du crédit"
             if estimation.remplacement.present else "Montant personnel de base × taux du crédit"),
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
            formule_impot_total,
            final.impot_total_preliminaire,
        ),
        _ligne(
            16, "RAPPROCHEMENT", "Retenues totales",
            ("T4 22 + T4E 22 + RL-1 E + RL-6 G (T4E 23 non additionné)" if rqap.present
             else "T4 22 + RL-1 E + T4E 22 et 23 — valeurs validées" if ae.present
             else "T4 22 + RL-1 E + T4A(P) 22 + RL-2 J (si reçu)" if rrq_rpc.present
             else "T4 22 + RL-1 E + T4A(OAS) 22/23" if psv.present
             else "Retenues salariales + T4A 022 ou T4RIF 28 + RL-2 J" if pensions.present
             else "T4 case 22 + RL-1 case E — valeurs validées"),
            "Retenue fédérale + retenue Québec",
            final.retenues_totales,
        ),
    )

    if estimation.placement_etranger.present:
        p = estimation.placement_etranger
        pc = estimation.profil_placement_etranger
        c = estimation.credit_impot_etranger
        cc = estimation.profil_credit_impot_etranger
        for cible, section, libelle, source, formule, montant in (
            (
                "Revenu imposable fédéral",
                "REVENU FÉDÉRAL",
                "Placement étranger ligne 12100",
                "T5 case 15 — " + pc.source,
                "Revenu étranger brut validé, déjà en CAD",
                p.revenu_brut_federal,
            ),
            (
                "Revenu imposable Québec",
                "REVENU QUÉBEC",
                "Placement étranger ligne 130",
                "RL-3 case F — " + pc.source,
                "Revenu brut de placement à l'étranger validé",
                p.revenu_brut_quebec,
            ),
            (
                "Abattement Québec",
                "FÉDÉRAL",
                "Crédit impôt étranger ligne 40500",
                "T2209 — " + cc.source_t2209,
                "Minimum du T2209 confirmé et de 42900; sans effet sur la base de 44000",
                federal.credit_etranger_ligne_40500,
            ),
            (
                "Abattement Québec", "FÉDÉRAL",
                "Impôt fédéral après ligne 40500", "T1 Québec 2025, partie C",
                "max(ligne 42900 - crédit 40500 utilisable, 0)",
                federal.impot_federal_apres_credit_etranger,
            ),
            (
                "Impôt Québec préliminaire",
                "QUÉBEC",
                "Crédit impôt étranger ligne 409",
                "TP-772 — " + cc.source_tp772,
                "Montant TP-772 2025 confirmé; crédit non remboursable",
                c.ligne_409,
            ),
            (
                "Impôt total préliminaire",
                "QUÉBEC",
                "FSS placement étranger ligne 446",
                "Annexe F 2025",
                "Cotisation FSS calculée sur le revenu de placement ligne 130",
                p.cotisation_fss,
            ),
        ):
            lignes = _inserer_ligne_avant(
                lignes,
                cible,
                _ligne(0, section, libelle, source, formule, montant),
            )

    if rqap.present:
        for cible, section, libelle, source, formule, montant in (
            ("Déduction RRQ améliorée", "REVENU FÉDÉRAL", "RQAP ligne 11900", "T4E 14 = 36", "Prestations brutes", rqap.prestations),
            ("Déduction RRQ améliorée", "INFORMATION", "RQAP ligne 11905", "T4E 36", "Déjà inclus dans 11900; ne pas additionner", rqap.prestations),
            ("Revenu imposable fédéral", "REVENU FÉDÉRAL", "Remboursement ligne 23200", "T4E 30", "Remboursement des prestations de 2025", rqap.remboursement),
            ("Déduction travailleur Québec", "REVENU QUÉBEC", "RQAP ligne 110", "RL-6 A", "Prestations brutes", rqap.prestations),
            ("Revenu imposable Québec", "REVENU QUÉBEC", "Remboursement ligne 246", "RL-6 D", "Remboursement des prestations de 2025", rqap.remboursement),
            ("Impôt total préliminaire", "QUÉBEC", "FSS ligne 446", "Annexe F 2025", "Assiette = RQAP - remboursement; seuils 18 130 / 63 060; plafonds 150 / 1 000", rqap.cotisation_fss),
        ):
            lignes = _inserer_ligne_avant(lignes, cible, _ligne(0, section, libelle, source, formule, montant))

    for cible, section, libelle, source, montant in (
        ("Revenu imposable fédéral", "REVENU FÉDÉRAL", "Déduction RPA ligne 20700",
         estimation.cotisations_rpa.source_federale, estimation.cotisations_rpa.montant_federal),
        ("Revenu imposable Québec", "REVENU QUÉBEC", "Déduction RPA ligne 205",
         estimation.cotisations_rpa.source_quebec, estimation.cotisations_rpa.montant_quebec),
    ):
        if montant:
            lignes = _inserer_ligne_avant(lignes, cible, _ligne(
                0, section, libelle, source,
                "Cotisations RPA pour services courants validées; ARC 20700 / RQ 205", montant,
            ))

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

    if deduction_celiapp.deduction > Decimal("0"):
        lignes = _inserer_ligne_avant(
            lignes,
            "Revenu imposable fédéral",
            _ligne(
                0,
                "REVENU FÉDÉRAL",
                "Déduction CELIAPP 4A validée",
                (
                    "ARC annexe 15 / ligne 20805; "
                    "Revenu Québec ligne 215 — "
                    + deduction_celiapp.source_droits
                ),
                (
                    "Montant réclamé limité aux cotisations directes 2025 "
                    "et aux droits de déduction confirmés"
                ),
                deduction_celiapp.deduction,
            ),
        )

    if deduction_frais_garde > Decimal("0"):
        plafond_garde = plafond_enfants_frais_garde_2025(
            frais_garde_federaux
        )
        limite_deux_tiers_garde = limite_deux_tiers_revenu_gagne_2025(
            frais_garde_federaux
        )
        lignes = _inserer_ligne_avant(
            lignes,
            "Revenu imposable fédéral",
            _ligne(
                0,
                "REVENU FÉDÉRAL",
                "Frais de garde fédéraux 4B — T778 / ligne 21400",
                (
                    "ARC T778 / ligne 21400 — "
                    + frais_garde_federaux.source
                    + " — validation comptable"
                ),
                (
                    "Minimum de : frais admissibles payés "
                    + formater_montant_estimation(
                        frais_garde_federaux.frais_admissibles_payes
                    )
                    + "; plafond selon enfants "
                    + formater_montant_estimation(plafond_garde)
                    + "; 2/3 du revenu gagné "
                    + formater_montant_estimation(limite_deux_tiers_garde)
                    + ". Déduction retenue : "
                    + formater_montant_estimation(deduction_frais_garde)
                ),
                deduction_frais_garde,
            ),
        )

    if depenses_emploi.deduction_federale_t777 > Decimal("0"):
        lignes = _inserer_ligne_avant(
            lignes,
            "Revenu imposable fédéral",
            _ligne(
                0,
                "REVENU FÉDÉRAL",
                "Dépenses d'emploi 4C — T777 / ligne 22900",
                (
                    "ARC T2200 + T777 / ligne 22900 — "
                    + depenses_emploi.source_federale
                    + " — validation comptable"
                ),
                (
                    "Montant T777 validé, dépenses exigées par le contrat "
                    "et non remboursées"
                ),
                depenses_emploi.deduction_federale_t777,
            ),
        )

    if depenses_emploi.deduction_quebec_tp59 > Decimal("0"):
        lignes = _inserer_ligne_avant(
            lignes,
            "Revenu imposable Québec",
            _ligne(
                0,
                "REVENU QUÉBEC",
                "Dépenses d'emploi 4C — TP-59 / ligne 207 code 07",
                (
                    "Revenu Québec TP-64.3 + TP-59 / ligne 207 code 07 — "
                    + depenses_emploi.source_quebec
                    + " — validation comptable"
                ),
                (
                    "Montant TP-59 validé, dépenses exigées par le contrat "
                    "et non remboursées"
                ),
                depenses_emploi.deduction_quebec_tp59,
            ),
        )

    if frais_demenagement.deduction_federale_t1m > Decimal("0"):
        lignes = _inserer_ligne_avant(
            lignes,
            "Revenu imposable fédéral",
            _ligne(
                0,
                "REVENU FÉDÉRAL",
                "Frais de déménagement 4D — T1-M / ligne 21900",
                (
                    "ARC T1-M / ligne 21900 — "
                    + frais_demenagement.source_federale
                    + " — validation comptable"
                ),
                (
                    "Montant T1-M validé; déménagement pour emploi, "
                    "règle des 40 km confirmée et remboursements "
                    "employeur déjà pris en compte"
                ),
                frais_demenagement.deduction_federale_t1m,
            ),
        )

    if frais_demenagement.deduction_quebec_tp348 > Decimal("0"):
        lignes = _inserer_ligne_avant(
            lignes,
            "Revenu imposable Québec",
            _ligne(
                0,
                "REVENU QUÉBEC",
                "Frais de déménagement 4D — TP-348 / ligne 228",
                (
                    "Revenu Québec TP-348 / ligne 228 — "
                    + frais_demenagement.source_quebec
                    + " — validation comptable"
                ),
                (
                    "Montant TP-348 validé; déménagement pour emploi, "
                    "règle des 40 km confirmée et remboursements "
                    "employeur déjà pris en compte"
                ),
                frais_demenagement.deduction_quebec_tp348,
            ),
        )

    if pension_alimentaire.total_paye_federal_21999 > Decimal("0"):
        lignes = _inserer_ligne_avant(
            lignes,
            "Revenu imposable fédéral",
            _ligne(
                0,
                "INFORMATION FÉDÉRALE",
                "Pension alimentaire 4E — total payé ligne 21999",
                (
                    "ARC lignes 21999/22000 — "
                    + pension_alimentaire.source_federale
                    + " — validation comptable"
                ),
                (
                    "Total payé déclaré à la ligne 21999; "
                    "montant informationnel distinct de la déduction 22000"
                ),
                pension_alimentaire.total_paye_federal_21999,
            ),
        )

    if pension_alimentaire.deduction_federale_22000 > Decimal("0"):
        lignes = _inserer_ligne_avant(
            lignes,
            "Revenu imposable fédéral",
            _ligne(
                0,
                "REVENU FÉDÉRAL",
                "Pension alimentaire 4E — déduction ligne 22000",
                (
                    "ARC lignes 21999/22000 — "
                    + pension_alimentaire.source_federale
                    + " — validation comptable"
                ),
                (
                    "Partie déductible fédérale validée; ordonnance ou "
                    "entente écrite et séparation confirmées"
                ),
                pension_alimentaire.deduction_federale_22000,
            ),
        )

    if pension_alimentaire.deduction_quebec_225 > Decimal("0"):
        lignes = _inserer_ligne_avant(
            lignes,
            "Revenu imposable Québec",
            _ligne(
                0,
                "REVENU QUÉBEC",
                "Pension alimentaire 4E — déduction ligne 225",
                (
                    "Revenu Québec ligne 225 — "
                    + pension_alimentaire.source_quebec
                    + " — validation comptable"
                ),
                (
                    "Montant Québec déductible validé; cas d'arrérages, "
                    "rétroactifs et anciens régimes exclus du Bloc 4E simple"
                ),
                pension_alimentaire.deduction_quebec_225,
            ),
        )

    if autres_deductions.deduction_federale_23200 > Decimal("0"):
        lignes = _inserer_ligne_avant(
            lignes,
            "Revenu imposable fédéral",
            _ligne(
                0,
                "REVENU FÉDÉRAL",
                "Autres déductions 4F — ligne 23200",
                (
                    "ARC ligne 23200 — "
                    + autres_deductions.source_federale
                    + " — validation comptable"
                ),
                (
                    "Montant déjà établi et validé; nature : "
                    + autres_deductions.nature_federale
                    + "; aucune autre ligne ou bloc dédié applicable confirmé"
                ),
                autres_deductions.deduction_federale_23200,
            ),
        )

    if autres_deductions.deduction_quebec_250_code17 > Decimal("0"):
        lignes = _inserer_ligne_avant(
            lignes,
            "Revenu imposable Québec",
            _ligne(
                0,
                "REVENU QUÉBEC",
                "Autres déductions 4F — ligne 250 code 17",
                (
                    "Revenu Québec ligne 250 / case 249 code 17 — "
                    + autres_deductions.source_quebec
                    + " — validation comptable"
                ),
                (
                    "Montant déjà établi et validé; nature : "
                    + autres_deductions.nature_quebec
                    + "; autres codes spécialisés exclus du Bloc 4F simple"
                ),
                autres_deductions.deduction_quebec_250_code17,
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

    if dons.montant_admissible_federal > Decimal("0") or dons.reports_federaux.activer:
        lignes = _inserer_ligne_avant(
            lignes,
            "Impôt fédéral de base",
            _ligne(
                0,
                "FÉDÉRAL",
                "Crédit fédéral pour dons",
                (
                    "ARC annexe 9 / ligne 34900 — "
                    + (dons.source_federale or dons.reports_federaux.source)
                    + " — validation comptable"
                ),
                (
                    "14,5 % des premiers 200 $; 33 % de min(excédent dons, max(26000 - 253414, 0)); "
                    "29 % du reste; arrondi de chaque composante"
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
                    "20 % des premiers 200 $; 25,75 % de min(excédent dons, max(299 - 129590, 0)); "
                    "24 % du reste; arrondi de chaque composante"
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
                    "32300 utilisé selon annexe 11 × 14,5 %" if frais_scolarite.reports_federaux.activer else
                    "Montant admissible 2025 × 14,5 % — aucun report/transfert dans ce profil"
                ),
                credit_federal_frais_scolarite_2025(
                    frais_scolarite, resultat_reports=estimation.resultat_reports_scolarite
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

    if aidant_enfant_federal.enfants_detailles:
        lignes = _inserer_ligne_avant(lignes, "Impôt fédéral de base", _ligne(
            0, "FÉDÉRAL", "Crédit fédéral — enfants 30499 / 30500",
            "Annexe 5 2025; identités distinctes et validation comptable confirmées. "
            + " ; ".join(details_enfants_30500_2025(aidant_enfant_federal)),
            f"30499 = {nombre_enfants_ligne_30499_2025(aidant_enfant_federal)} × 2687 $ "
            f"= 30500 {montant_ligne_30500_2025(aidant_enfant_federal):.2f} $; crédit = total × 14,5 %, arrondi une fois.",
            credit_federal_aidant_enfant_moins18_2025(aidant_enfant_federal)))

    if aidant_enfant_federal.reclamer_montant and not aidant_enfant_federal.enfants_detailles:
        montant_30500 = montant_ligne_30500_2025(
            aidant_enfant_federal
        )
        nombre_enfants_30499 = nombre_enfants_ligne_30499_2025(
            aidant_enfant_federal
        )

        lignes = _inserer_ligne_avant(
            lignes,
            "Impôt fédéral de base",
            _ligne(
                0,
                "FÉDÉRAL",
                "Crédit fédéral — aidant naturel enfant de moins de 18 ans",
                (
                    "ARC lignes 30499 / 30500 — "
                    + aidant_enfant_federal.source_enfant
                    + (" — même enfant 30400/30500 : " + aidant_enfant_federal.reference_enfant if aidant_enfant_federal.enfant_reclame_30400 else "")
                    + " — validation comptable"
                ),
                (
                    str(nombre_enfants_30499)
                    + " enfant admissible × "
                    + formater_montant_estimation(montant_30500)
                    + " = ligne 30500 "
                    + formater_montant_estimation(montant_30500)
                    + "; crédit fédéral × 14,5 % — "
                    + "preuve médicale ou T2201 confirmée, "
                    + "aucune garde partagée, aucune pension alimentaire"
                ),
                credit_federal_aidant_enfant_moins18_2025(
                    aidant_enfant_federal
                ),
            ),
        )

    if personne_charge_admissible_federale.reclamer_montant:
        montant_ligne_30400 = montant_ligne_30400_2025(
            personne_charge_admissible_federale
        )
        montant_personnel_contribuable_30400 = (
            montant_ligne_30400
            + (
                personne_charge_admissible_federale
                .revenu_net_personne_charge_2025
            )
        )
        libelle_base_30400 = "Montant personnel fédéral"
        if (
            personne_charge_admissible_federale
            .aidant_naturel_base_2687_inclus
        ):
            libelle_base_30400 += (
                " + base aidant naturel 2 687 $"
            )

        lignes = _inserer_ligne_avant(
            lignes,
            "Impôt fédéral de base",
            _ligne(
                0,
                "FÉDÉRAL",
                "Crédit fédéral — personne à charge admissible",
                (
                    "ARC annexe 5 / ligne 30400 — "
                    + (
                        personne_charge_admissible_federale
                        .source_personne_charge
                    )
                    + " — validation comptable"
                ),
                (
                    libelle_base_30400
                    + " "
                    + formater_montant_estimation(
                        montant_personnel_contribuable_30400
                    )
                    + " - revenu net de la personne à charge "
                    + formater_montant_estimation(
                        personne_charge_admissible_federale
                        .revenu_net_personne_charge_2025
                    )
                    + " = ligne 30400 "
                    + formater_montant_estimation(
                        montant_ligne_30400
                    )
                    + "; crédit fédéral × 14,5 % — "
                    + "profil enfant de moins de 18 ans, "
                    + "sans garde partagée ni pension alimentaire"
                ),
                credit_federal_personne_charge_admissible_2025(
                    personne_charge_admissible_federale
                ),
            ),
        )

    if montant_conjoint_federal.reclamer_montant:
        montant_ligne_30300 = montant_ligne_30300_2025(
            montant_conjoint_federal
        )
        montant_personnel_contribuable = (
            montant_ligne_30300
            + montant_conjoint_federal.revenu_net_conjoint_2025
        )
        libelle_base_30300 = "Montant personnel fédéral"
        if montant_conjoint_federal.aidant_naturel_base_2687_inclus:
            libelle_base_30300 += (
                " + base aidant naturel 2 687 $"
            )

        lignes = _inserer_ligne_avant(
            lignes,
            "Impôt fédéral de base",
            _ligne(
                0,
                "FÉDÉRAL",
                "Crédit fédéral — époux / conjoint",
                (
                    "ARC ligne 30300 — "
                    + montant_conjoint_federal.source_conjoint
                    + " — validation comptable"
                ),
                (
                    libelle_base_30300
                    + " "
                    + formater_montant_estimation(
                        montant_personnel_contribuable
                    )
                    + " - revenu net du conjoint "
                    + formater_montant_estimation(
                        montant_conjoint_federal.revenu_net_conjoint_2025
                    )
                    + " = ligne 30300 "
                    + formater_montant_estimation(
                        montant_ligne_30300
                    )
                    + "; crédit fédéral × 14,5 %"
                ),
                credit_federal_montant_conjoint_2025(
                    montant_conjoint_federal
                ),
            ),
        )

    if accessibilite_domiciliaire_federale.reclamer_montant:
        montant_31285 = montant_ligne_31285_2025(
            accessibilite_domiciliaire_federale
        )

        lignes = _inserer_ligne_avant(
            lignes,
            "Impôt fédéral de base",
            _ligne(
                0,
                "FÉDÉRAL",
                "Crédit fédéral — accessibilité domiciliaire",
                (
                    "ARC ligne 31285 — "
                    + accessibilite_domiciliaire_federale.source_renovation
                    + " — validation comptable"
                ),
                (
                    "Dépenses admissibles "
                    + formater_montant_estimation(
                        montant_31285
                    )
                    + " (maximum 20 000 $) × 14,5 %; "
                    + "particulier déterminé 65 ans ou plus / CIPH; "
                    + "demande pour soi-même; "
                    + "logement situé au Canada et appartenant au contribuable; "
                    + "rénovation durable et intégrante; "
                    + "accessibilité / mobilité / réduction du risque; "
                    + "travaux et biens 2025 uniquement; "
                    + "aucun partage; aucune part entreprise/location; "
                    + "règles fournisseurs liés confirmées; "
                    + "dépenses non admissibles exclues; "
                    + "pièces justificatives conservées"
                ),
                credit_federal_ligne_31285_2025(
                    accessibilite_domiciliaire_federale
                ),
            ),
        )

    if achat_habitation_federal.reclamer_montant:
        montant_31270 = montant_ligne_31270_2025(
            achat_habitation_federal
        )

        lignes = _inserer_ligne_avant(
            lignes,
            "Impôt fédéral de base",
            _ligne(
                0,
                "FÉDÉRAL",
                "Crédit fédéral — achat d'une habitation",
                (
                    "ARC ligne 31270 — "
                    + achat_habitation_federal.source_habitation
                    + " — validation comptable"
                ),
                (
                    "Montant admissible réclamé "
                    + formater_montant_estimation(montant_31270)
                    + " (maximum 10 000 $) × 14,5 %; "
                    + "Première habitation confirmée; "
                    + "aucune habitation possédée et habitée pendant "
                    + "l'année de l'achat ou les quatre années précédentes; "
                    + "intention de résidence principale dans un an; "
                    + "aucun partage; exception handicap non utilisée; "
                    + "pièces justificatives conservées"
                ),
                credit_federal_ligne_31270_2025(
                    achat_habitation_federal
                ),
            ),
        )

    if aidant_30450_federal.personnes_detaillees:
        lignes = _inserer_ligne_avant(lignes, "Impôt fédéral de base", _ligne(
            0, "FÉDÉRAL", "Crédit fédéral — aidants 30450 / 51120",
            "Annexe 5 2025; identités distinctes et validation comptable confirmées. "
            + " ; ".join(details_personnes_30450_2025(aidant_30450_federal)),
            f"Somme des parts individuelles = {montant_ligne_30450_2025(aidant_30450_federal):.2f} $; "
            f"51120 = {nombre_personnes_charge_ligne_51120_2025(aidant_30450_federal)}; "
            "crédit = total × 14,5 %, arrondi une fois; 34990/35000 dans l'ordre T1.",
            credit_federal_ligne_30450_2025(aidant_30450_federal)))

    if aidant_30450_federal.reclamer_montant and not aidant_30450_federal.personnes_detaillees:
        montant_30450 = montant_ligne_30450_2025(
            aidant_30450_federal
        )
        nombre_51120 = nombre_personnes_charge_ligne_51120_2025(
            aidant_30450_federal
        )

        lignes = _inserer_ligne_avant(
            lignes,
            "Impôt fédéral de base",
            _ligne(
                0,
                "FÉDÉRAL",
                "Crédit fédéral — aidant naturel autre personne à charge",
                (
                    "ARC Annexe 5 / ligne 30450 — "
                    + aidant_30450_federal.source_personne
                    + " — validation comptable"
                ),
                (
                    "28 798 $ - revenu net ligne 23600 "
                    + formater_montant_estimation(
                        aidant_30450_federal
                        .revenu_net_personne_ligne_23600
                    )
                    + ", limité à 8 601 $, moins les parts attribuées aux autres soutiens = ligne 30450 "
                    + formater_montant_estimation(montant_30450)
                    + "; ligne 51120 = "
                    + str(nombre_51120)
                    + " personne à charge; crédit fédéral × 14,5 %; "
                    + "aucune ligne 30300/30400 pour cette même personne; "
                    + "aucune pension alimentaire; "
                    + description_partage_30450_2025(aidant_30450_federal) + "; "
                    + "preuve médicale ou T2201 confirmée"
                ),
                credit_federal_ligne_30450_2025(
                    aidant_30450_federal
                ),
            ),
        )

    if aidant_30425_federal.reclamer_montant:
        montant_brut_30425 = (
            montant_brut_avant_30300_30400_ligne_30425_2025(
                aidant_30425_federal
            )
        )
        montant_30425 = montant_ligne_30425_2025(
            aidant_30425_federal
        )
        type_personne_30425 = (
            "conjoint — ligne 30300"
            if aidant_30425_federal.type_personne == TYPE_CONJOINT
            else "personne à charge admissible — ligne 30400"
        )

        lignes = _inserer_ligne_avant(
            lignes,
            "Impôt fédéral de base",
            _ligne(
                0,
                "FÉDÉRAL",
                (
                    "Crédit fédéral — aidant naturel "
                    "conjoint / personne à charge"
                ),
                (
                    "ARC Annexe 5 / ligne 30425 — "
                    + aidant_30425_federal.source_personne
                    + " — validation comptable"
                ),
                (
                    "28 798 $ - revenu net "
                    + formater_montant_estimation(
                        aidant_30425_federal
                        .revenu_net_personne_ligne_23600
                    )
                    + ", limité à 8 601 $ = "
                    + formater_montant_estimation(
                        montant_brut_30425
                    )
                    + "; moins montant réclamé pour "
                    + type_personne_30425
                    + " "
                    + formater_montant_estimation(
                        aidant_30425_federal
                        .montant_reclame_ligne_30300_ou_30400
                    )
                    + " = ligne 30425 "
                    + formater_montant_estimation(
                        montant_30425
                    )
                    + "; crédit fédéral × 14,5 %"
                ),
                credit_federal_ligne_30425_2025(
                    aidant_30425_federal
                ),
            ),
        )

    if (
        credits_federaux_age_pension.reclamer_montant_age
        or credits_federaux_age_pension.reclamer_montant_pension
    ):
        montant_age_federal = montant_age_federal_2025(
            credits_federaux_age_pension
        )
        montant_pension_federal = montant_pension_federal_2025(
            credits_federaux_age_pension
        )

        sources_federales = []
        if credits_federaux_age_pension.reclamer_montant_age:
            sources_federales.append(
                credits_federaux_age_pension.source_age
            )
        if credits_federaux_age_pension.reclamer_montant_pension:
            sources_federales.append(
                credits_federaux_age_pension.source_pension
            )

        lignes = _inserer_ligne_avant(
            lignes,
            "Impôt fédéral de base",
            _ligne(
                0,
                "FÉDÉRAL",
                "Crédit fédéral — âge / pension",
                (
                    "ARC ligne 30100 / ligne 31400 — "
                    + " — ".join(sources_federales)
                    + " — validation comptable"
                ),
                (
                    "Montant ligne 30100 "
                    + formater_montant_estimation(montant_age_federal)
                    + " + montant ligne 31400 "
                    + formater_montant_estimation(montant_pension_federal)
                    + " = base admissible; crédit fédéral × 14,5 %"
                ),
                credit_federal_age_pension_2025(
                    credits_federaux_age_pension
                ),
            ),
        )

    if credit_deficience.reclamer_federal:
        lignes = _inserer_ligne_avant(
            lignes,
            "Impôt fédéral de base",
            _ligne(
                0,
                "FÉDÉRAL",
                "Crédit fédéral pour personnes handicapées",
                (
                    "ARC ligne 31600 — "
                    + credit_deficience.source_federale
                    + " — admissibilité CIPH validée"
                ),
                (
                    f"31600 = {montant_federal_handicap_2025(credit_deficience)} $; crédit = 31600 × 14,5 %; "
                    "base 10 138 + supplément mineur max(5914 - max(soins - 3464, 0), 0), si applicable"
                ),
                credit_federal_handicap_2025(
                    credit_deficience
                ),
            ),
        )

    if credit_deficience.reclamer_quebec:
        lignes = _inserer_ligne_avant(
            lignes,
            "Impôt Québec préliminaire",
            _ligne(
                0,
                "QUÉBEC",
                "Crédit Québec pour déficience grave et prolongée",
                (
                    "Revenu Québec ligne 376 — "
                    + credit_deficience.source_quebec
                    + " — attestation professionnelle validée"
                ),
                (
                    "Montant Québec 2025 de 4 123 $ × 14 % "
                    "— profil simple validé"
                ),
                credit_quebec_deficience_2025(
                    credit_deficience
                ),
            ),
        )

    if (
        montants_age_retraite.reclamer_age
        or montants_age_retraite.reclamer_revenus_retraite
    ):
        montant_age = montant_age_2025(montants_age_retraite)
        montant_retraite = montant_revenus_retraite_2025(
            montants_age_retraite
        )
        reduction = reduction_annexe_b_age_retraite_2025(
            montants_age_retraite
        )
        montant_ligne_361_age_retraite = (
            montant_ligne_361_age_retraite_2025(
                montants_age_retraite
            )
        )
        sources = []
        if montants_age_retraite.reclamer_age:
            sources.append(montants_age_retraite.source_age)
        if montants_age_retraite.reclamer_revenus_retraite:
            sources.append(montants_age_retraite.source_retraite)

        lignes = _inserer_ligne_avant(
            lignes,
            "Impôt Québec préliminaire",
            _ligne(
                0,
                "QUÉBEC",
                "Crédit Québec — âge / revenus de retraite",
                (
                    "Revenu Québec annexe B / ligne 361 — "
                    + " — ".join(sources)
                    + " — validation comptable"
                ),
                (
                    "Montant âge "
                    + formater_montant_estimation(montant_age)
                    + " + montant revenus de retraite "
                    + formater_montant_estimation(montant_retraite)
                    + " - réduction annexe B "
                    + formater_montant_estimation(reduction)
                    + " = ligne 361 "
                    + formater_montant_estimation(
                        montant_ligne_361_age_retraite
                    )
                    + "; seuil 42 090 $, réduction 18,75 %, "
                    + "puis crédit Québec × 14 %"
                ),
                credit_quebec_age_retraite_2025(
                    montants_age_retraite
                ),
            ),
        )

    if personne_vivant_seule.reclamer_montant:
        montant_ligne_361 = (
            montant_ligne_361_personne_vivant_seule_2025(
                personne_vivant_seule
            )
        )
        lignes = _inserer_ligne_avant(
            lignes,
            "Impôt Québec préliminaire",
            _ligne(
                0,
                "QUÉBEC",
                "Crédit Québec — personne vivant seule",
                (
                    "Revenu Québec annexe B / ligne 361 — "
                    + personne_vivant_seule.source
                    + " — validation comptable"
                ),
                (
                    "Montant ligne 361 "
                    + formater_montant_estimation(montant_ligne_361)
                    + " × 14 %; montant de base 2 128 $, "
                    "réduction de 18,75 % du revenu familial net "
                    "excédant 42 090 $"
                ),
                credit_quebec_personne_vivant_seule_2025(
                    personne_vivant_seule
                ),
            ),
        )

    if assurance_medicaments.type_couverture.strip():
        type_couverture = (
            assurance_medicaments.type_couverture.strip().lower()
        )
        code_449 = code_exemption_case_449_2025(
            assurance_medicaments
        )

        if type_couverture == "collectif":
            formule_assurance = (
                "Couverture collective toute l'année — "
                f"case 449 code {code_449} — cotisation 0 $"
            )
        elif code_449 == "32":
            formule_assurance = (
                "Régime public — revenu ligne 275 ≤ 19 890 $ — "
                "case 449 code 32 — cotisation 0 $"
            )
        else:
            formule_assurance = (
                "Régime public toute l'année — ligne 48 annexe K "
                "> 8 181 $ — cotisation maximale 2025 de 755 $"
            )

        lignes = _inserer_ligne_avant(
            lignes,
            "Impôt total préliminaire",
            _ligne(
                0,
                "QUÉBEC",
                "Cotisation assurance médicaments Québec",
                (
                    "Revenu Québec annexe K / ligne 447 — "
                    + assurance_medicaments.source
                    + " — validation comptable"
                ),
                formule_assurance,
                final.cotisation_assurance_medicaments,
            ),
        )

    if cotisations_excedentaires.source.strip():
        nouvelles_lignes = (
            _ligne(
                0,
                "REMBOURSEMENTS",
                "Remboursement RRQ excédentaire",
                (
                    "Revenu Québec ligne 452 — "
                    + cotisations_excedentaires.source
                    + " — validation comptable"
                ),
                (
                    "RRQ B.A + B.B payées - cotisations RRQ attendues "
                    "selon les gains admissibles validés"
                ),
                final.remboursement_rrq_excedentaire,
            ),
            _ligne(
                0,
                "REMBOURSEMENTS",
                "Remboursement assurance-emploi excédentaire",
                (
                    "ARC ligne 45000 — "
                    + cotisations_excedentaires.source
                    + " — validation comptable"
                ),
                (
                    "Cotisation AE payée - prime AE Québec attendue "
                    "selon les gains assurables validés"
                ),
                final.remboursement_ae_excedentaire,
            ),
            _ligne(
                0,
                "REMBOURSEMENTS",
                "Remboursement RQAP excédentaire",
                (
                    "Revenu Québec ligne 457 — "
                    + cotisations_excedentaires.source
                    + " — validation comptable"
                ),
                (
                    "Cotisation RQAP payée - cotisation attendue selon "
                    "les revenus assujettis; remboursement complet si "
                    "les revenus assujettis sont sous 2 000 $"
                ),
                final.remboursement_rqap_excedentaire,
            ),
        )
        lignes = tuple(
            replace(ligne, ordre=i + 1)
            for i, ligne in enumerate(
                lignes + nouvelles_lignes
            )
        )

    if ae.present:
        for cible, section, libelle, source, formule, montant in (
            ("Déduction RRQ améliorée", "REVENU FÉDÉRAL", "AE ligne 11900", "T4E 14", "Prestations totales, sans exonération", ae.prestations),
            ("Déduction RRQ améliorée", "INFORMATION", "AE ligne 11905", "T4E 37", "Maternité/parentales déjà incluses dans 11900", ae.maternite_parentales),
            ("Revenu imposable fédéral", "REVENU FÉDÉRAL", "Remboursement AE 23200", "T4E 30", "Trop-payé remboursé, distinct de la récupération", ae.remboursement),
            ("Revenu imposable fédéral", "REVENU FÉDÉRAL", "Revenu avant récupération 23400", "Revenus et déductions validés", "Revenu net avant la ligne 23500; aucun ajustement PUGE/REEI", ae.revenu_avant_recuperation),
            ("Revenu imposable fédéral", "REVENU FÉDÉRAL", "Récupération AE 23500", "T4E tableau 2025, cases 7/15/30", "Si taux 30 % : 30 % × min(max(0,15-30), max(0,23400-82125)); sinon 0", ae.recuperation),
            ("Déduction travailleur Québec", "REVENU QUÉBEC", "AE ligne 111", "T4E 14", "Prestations totales", ae.prestations),
            ("Revenu imposable Québec", "REVENU QUÉBEC", "Remboursement AE 246", "T4E 30", "Trop-payé de 2025 remboursé", ae.remboursement),
            ("Revenu imposable Québec", "REVENU QUÉBEC", "Récupération AE 250", "Québec 250 point 3", "Report de la ligne fédérale 23500", ae.recuperation),
            ("Impôt total préliminaire", "FÉDÉRAL", "Récupération AE 42200", "Tableau T4E 2025", "Ajout de 23500 au montant à payer, sans abattement Québec", ae.recuperation),
            ("Impôt total préliminaire", "QUÉBEC", "FSS AE ligne 446", "Annexe F 2025", "Assiette = AE - remboursement 246 - récupération 250; barème FSS", ae.cotisation_fss),
        ):
            lignes = _inserer_ligne_avant(lignes, cible, _ligne(0, section, libelle, source, formule, montant))

    if rrq_rpc.present:
        for cible, section, libelle, source, formule, montant in (
            ("Déduction RRQ améliorée", "REVENU FÉDÉRAL", "RRQ/RPC 11400", "T4A(P) 20", "Total; sous-cases 14 à 19 non additionnées", rrq_rpc.prestations),
            ("Déduction RRQ améliorée", "INFORMATION", "Invalidité RRQ/RPC 11410", "T4A(P) 16", "Déjà incluse dans 11400", rrq_rpc.invalidite),
            ("Déduction travailleur Québec", "REVENU QUÉBEC", "RRQ/RPC 119", "RL-2 C" if rrq_rpc.releve_2_present else "T4A(P) 20, sans RL-2", "Même prestation, sans double compte", rrq_rpc.prestations),
            ("Impôt total préliminaire", "QUÉBEC", "FSS RRQ/RPC 446", "Annexe F 2025", "Assiette RRQ/RPC; RPA/REER non déduits; sans abattement", rrq_rpc.cotisation_fss),
            ("Retenues totales", "RETENUES", "Retenue RRQ/RPC 43700", "T4A(P) 22", "Ajout aux retenues salariales", rrq_rpc.retenue_federale),
            ("Retenues totales", "RETENUES", "Retenue RRQ/RPC 451", "RL-2 J", "Ajout une fois si RL-2 reçu", rrq_rpc.retenue_quebec),
        ):
            lignes = _inserer_ligne_avant(lignes, cible, _ligne(0, section, libelle, source, formule, montant))

    if psv.present:
        for cible, section, libelle, source, formule, montant in (
            ("Déduction RRQ améliorée", "REVENU FÉDÉRAL", "PSV 11300", "T4A(OAS) 18", "Pension imposable; case 19 non additionnée", psv.pension),
            ("Déduction RRQ améliorée", "REVENU FÉDÉRAL", "Suppléments 14600", "T4A(OAS) 21", "Inclus dans le revenu net", psv.supplements),
            ("Revenu imposable fédéral", "REVENU FÉDÉRAL", "Revenu avant récupération PSV 23400", "Revenus et déductions validés", "Après RPA/REER/cotisations; sans ajustement PUGE/REEI/AE", psv.revenu_avant_recuperation),
            ("Revenu imposable fédéral", "REVENU FÉDÉRAL", "Récupération PSV 23500", "Feuille fédérale 2025", "min(11300 + 14600, 15 % × max(0, 23400 - 93454))", psv.recuperation),
            ("Revenu imposable fédéral", "REVENU FÉDÉRAL", "Revenu net fédéral 23600", "Après récupération", "23400 - 23500; suppléments encore inclus", revenu.revenu_net_federal),
            ("Revenu imposable fédéral", "REVENU FÉDÉRAL", "Suppléments déductibles 25000", "ARC 25000", "max(0,14600 - max(0,23500 - 11300))", psv.deduction_supplements),
            ("Déduction travailleur Québec", "REVENU QUÉBEC", "PSV 114", "T4A(OAS) 18", "Même pension qu'au fédéral", psv.pension),
            ("Déduction travailleur Québec", "REVENU QUÉBEC", "Suppléments 148", "T4A(OAS) 21", "Code 07 à 149", psv.supplements),
            ("Revenu imposable Québec", "REVENU QUÉBEC", "Récupération PSV 250 point 3", "Québec 250", "Report de 23500", psv.recuperation),
            ("Revenu imposable Québec", "REVENU QUÉBEC", "Revenu net Québec 275", "Après récupération", "Suppléments encore inclus avant 295", revenu.revenu_net_quebec),
            ("Revenu imposable Québec", "REVENU QUÉBEC", "Suppléments déductibles 295", "Québec 295", "148 - suppléments récupérés dans 23500", psv.deduction_supplements),
            ("Impôt total préliminaire", "FÉDÉRAL", "Récupération PSV 42200", "Feuille fédérale 2025", "Ajout de 23500 sans abattement Québec", psv.recuperation),
            ("Impôt total préliminaire", "QUÉBEC", "FSS PSV 446", "Annexe F 2025, lignes 22 et 29", "PSV et suppléments exclus de l'assiette", Decimal("0")),
            ("Retenues totales", "RETENUES", "Retenue PSV 43700", "T4A(OAS) 22", "Inclut la récupération retenue à la source; ajout une fois", psv.retenue_federale),
            ("Retenues totales", "RETENUES", "Retenue PSV 451", "T4A(OAS) 23", "Ajout une fois", psv.retenue_quebec),
        ):
            lignes = _inserer_ligne_avant(lignes, cible, _ligne(0, section, libelle, source, formule, montant))

    if pensions.present:
        for cible, section, libelle, formule, montant in (
            ("Déduction RRQ améliorée", "REVENU FÉDÉRAL", "Pensions 11500", "Selon nature et âge au 31 décembre; sans décès", pensions.ligne_11500),
            ("Déduction RRQ améliorée", "REVENU FÉDÉRAL", "Pensions 13000", "FERR/rentes/RPAC non admissibles à 11500", pensions.ligne_13000),
            ("Déduction RRQ améliorée", "REVENU FÉDÉRAL", "Rente T5 12100", "Rente ordinaire avant 65 ans, sans décès", pensions.ligne_12100),
            ("Déduction travailleur Québec", "REVENU QUÉBEC", "Pensions 122", "RL-2 A/B ou RL-16 D, sans double compte", pensions.ligne_122),
            ("Impôt total préliminaire", "INFORMATION", "Revenu admissible pension 31400", "Portion admissible avant plafond 2 000 $; crédit calculé séparément", pensions.admissible_federal),
            ("Impôt total préliminaire", "INFORMATION", "Revenu admissible retraite 361", "Portion admissible avant coefficient, plafond et réduction annexe B", pensions.admissible_quebec),
            ("Impôt total préliminaire", "QUÉBEC", "FSS pensions 446", "Assiette pension brute; RPA/REER non déduits; sans abattement", pensions.cotisation_fss),
            ("Retenues totales", "RETENUES", "Retenue pensions 43700", "T4A 022 ou T4RIF 28, ajout une fois", pensions.retenue_federale),
            ("Retenues totales", "RETENUES", "Retenue pensions 451", "RL-2 J, ajout une fois", pensions.retenue_quebec),
        ):
            lignes = _inserer_ligne_avant(lignes, cible, _ligne(0, section, libelle, pensions.source, formule, montant))

    if estimation.retraits.present:
        r = estimation.retraits
        for libelle, montant in (("REER 12900",r.ligne_12900),("Forfait 13000",r.ligne_13000),("Déduction 23200",r.ligne_23200),("Retraits 154",r.ligne_154),("Déduction 250.6",r.ligne_250_6),("FSS retraits 446",r.cotisation_fss),("Retenue retraits 43700",r.retenue_federale),("Retenue retraits 451",r.retenue_quebec)):
            lignes = _inserer_ligne_avant(lignes, "Impôt total préliminaire", _ligne(0,"RETRAITS",libelle,estimation.profil_retraits.source,"Feuillets appariés, sans double compte",montant))

    if estimation.remplacement.present:
        r = estimation.remplacement
        for code in ("14400", "14500", "25000", "147", "148", "295", "358"):
            lignes = _inserer_ligne_avant(lignes, "Impôt total préliminaire", _ligne(0,"REMPLACEMENT", "Prestations " + code, estimation.profil_remplacement.source, "25000/295 réduisent l’imposable, pas le net; 358 réduit le montant personnel; FSS nul", getattr(r, "ligne_" + code)))

    if estimation.interets.present:
        r = estimation.interets
        profil = estimation.profil_interets
        source = profil.source if profil.nature == 'T5_RL3' else f'{profil.identifiant_source}; {profil.date_debut} au {profil.date_fin}; {profil.source}'
        for libelle, montant in (("Intérêts 12100",r.ligne_12100),("Intérêts T3 13000",r.ligne_13000),("Intérêts 130",r.ligne_130),("FSS intérêts 446",r.cotisation_fss)):
            lignes = _inserer_ligne_avant(lignes, "Impôt total préliminaire", _ligne(0,"INTÉRÊTS",libelle,source,("Source intérêts validée; FSS après frais 231, sans report 252 ni abattement" if estimation.frais_placement.present else "Source intérêts validée; une seule inclusion par juridiction; FSS annexe F sans abattement"),montant))

    if estimation.dividendes.present:
        r = estimation.dividendes
        for code in ("166", "167", "12000", "12010", "128", "40425", "415"):
            lignes = _inserer_ligne_avant(lignes, "Impôt total préliminaire", _ligne(0,"DIVIDENDES", "Dividendes " + code, estimation.profil_dividendes.source, "Réel 166/167; imposable 12000/128; 12010 inclus dans 12000; crédits non remboursables distincts du revenu", getattr(r, "ligne_" + code)))
        lignes = _inserer_ligne_avant(lignes, "Impôt total préliminaire", _ligne(0,"QUÉBEC", "FSS dividendes 446", "Annexe F 2025", ("Assiette = réels 166 + 167 - frais 231; majoration exclue; sans abattement" if estimation.frais_placement.present else "Assiette = réels 166 + 167; majoration exclue; sans abattement"), r.cotisation_fss))

    if estimation.interets.present and estimation.dividendes.present:
        if (
            estimation.capital.present
            and estimation.frais_placement.present
            and estimation.reports_pertes.present
        ):
            bloc_combinaison = "3H-F"
            formule_combinaison = (
                "Assiette globale = 130 + 166 + 167 + 139 - 231; majoration exclue; "
                "reports 25300/290 et annexe N 252/276 sans effet FSS; "
                "cotisation portée une seule fois"
            )
        elif estimation.capital.present and estimation.frais_placement.present:
            bloc_combinaison = "3H-D"
            formule_combinaison = (
                "Assiette globale = 130 + 166 + 167 + 139 - 231; majoration exclue; "
                "252 sans effet; perte 2025 non déductible des autres revenus; "
                "cotisation portée une seule fois"
            )
        elif estimation.capital.present and estimation.reports_pertes.present:
            bloc_combinaison = "3H-E"
            formule_combinaison = (
                "Assiette globale = 130 + 166 + 167 + 139; majoration exclue; "
                "reports 25300/290 sans effet sur revenu total/net et FSS; "
                "cotisation portée une seule fois"
            )
        elif estimation.capital.present:
            bloc_combinaison = "3H-C"
            formule_combinaison = (
                "Assiette globale = 130 + 166 + 167 + 139; majoration exclue; "
                "perte 2025 non déductible des autres revenus; cotisation portée une seule fois"
            )
        elif estimation.frais_placement.present:
            bloc_combinaison = "3H-B"
            formule_combinaison = (
                "Assiette globale = 130 + 166 + 167 - 231; majoration exclue; "
                "252 sans effet; cotisation portée une seule fois"
            )
        else:
            bloc_combinaison = "3H-A"
            formule_combinaison = (
                "Assiette globale = 130 + 166 + 167; majoration exclue; "
                "cotisation portée une seule fois"
            )
        lignes = _inserer_ligne_avant(
            lignes,
            "Impôt total préliminaire",
            _ligne(
                0,
                f"COMBINAISON {bloc_combinaison}",
                f"FSS combinée {bloc_combinaison} ligne 446",
                "Annexe F 2025",
                formule_combinaison,
                estimation.interets.cotisation_fss,
            ),
        )

    if estimation.frais_placement.present:
        r = estimation.frais_placement
        for libelle, valeur, formule in (
            ("Frais 22100 / 231", r.ligne_231, "Gestion/garde + intérêts admissibles; hors frais de transaction"),
            ("Revenus annexe N 36", r.revenus_n36, "128 + 130 + 139 dans le périmètre 3E"),
            ("Rajustement 260", r.ligne_260, "max(0, frais N18 - revenus N36)"),
            ("Rajustement 276", r.ligne_276, "Annexe N : pertes 3F si présentes, sinon 0"),
            ("Solde ouverture N70", r.solde_ouverture, "Solde Québec vérifié avant utilisation 2025"),
            ("Report 252 / N78", r.ligne_252, "Demande <= min(N70, max(0, N36 - N18 - N54))"),
            ("Solde clôture N80", r.solde_cloture, "N70 + 260 + 276 - 252; solde frais distinct des pertes"),
            ("Assiette FSS après frais", r.assiette_fss, "Intérêts + dividendes réels + gain imposable - 231; 252 sans effet"),
            ("FSS final 3E", r.cotisation_fss, "Annexe F, remplace le FSS avant frais, une seule cotisation")):
            lignes = _inserer_ligne_avant(lignes, "Impôt total préliminaire", _ligne(0, "FRAIS PLACEMENT", libelle, estimation.profil_frais_placement.source, formule, valeur))
    if estimation.reports_pertes.present:
        r = estimation.reports_pertes
        for libelle, valeur, formule in (
            ("Pertes antérieures 25300", r.ligne_25300, "Imposable fédéral seulement; plafond 12700 et solde ARC; ordre chronologique"),
            ("Pertes antérieures 290 / N52", r.ligne_290, "Imposable Québec seulement; plafond 139 et solde RQ; ordre chronologique"),
            ("Rajustement pertes 276 / N64", r.ligne_276, "max(0, 290 - max(0, N36 - N18)); ajouté à l'imposable et au solde frais"),
            ("Perte nouvelle 2025", r.perte_2025, "Perte nette 3D, une seule addition au registre futur; aucune déduction courante")):
            lignes = _inserer_ligne_avant(lignes, "Impôt total préliminaire", _ligne(0, "REPORTS PERTES", libelle, estimation.profil_reports_pertes.source_federale + " / " + estimation.profil_reports_pertes.source_quebec, formule, valeur))
        for solde in r.soldes:
            for nom, valeur in vars(solde).items():
                if nom != "annee":
                    lignes = _inserer_ligne_avant(lignes, "Impôt total préliminaire", _ligne(0, "REPORTS PERTES", str(solde.annee) + " " + nom, "Registre confirmé ARC/RQ", "Ouverture immuable - utilisation; 2025 = nouvelle perte nette", valeur))
    if estimation.capital.present:
        r = estimation.capital
        for libelle, valeur, formule in (("Produit brut 13199",r.produit,"T5008 21 = RL-18 21 + courtage"),("PBR indépendant",r.pbr,"Preuve distincte de la case 20"),("Frais de disposition",r.frais_courtage+r.frais_autres,"Courtage + autres frais; aucune double déduction"),("Gain/perte 13200 / G 10",r.gain_perte,"Produit brut - PBR - courtage - autres frais"),("Gain imposable 12700 / 139",r.ligne_12700,"50 % du gain positif; aucune perte déduite du salaire"),("Perte nette 2025 à vérifier",r.perte_nette_2025,"50 % de la perte; aucun report utilisé ou certifié"),("FSS capital 446",r.cotisation_fss,("Assiette = gain imposable 139 - frais 231; annexe F 2025" if estimation.frais_placement.present else "Assiette = gain imposable 139; annexe F 2025"))):
            lignes = _inserer_ligne_avant(lignes, "Impôt total préliminaire", _ligne(0,"CAPITAL", libelle, estimation.profil_capital.source, formule, valeur))

    credits = federal.credits_federaux_complets
    if credits is not None:
        section = "CRÉDIT COMPENSATOIRE FÉDÉRAL 2025"
        source = "T1 Québec 2025; feuille fédérale 5000-D1; annexe 9"
        audit = (
            _ligne(0, section, "Base ligne 33500", source,
                   " + ".join(f"{code} ({valeur:.2f})" for code, valeur in credits.montants_par_ligne),
                   credits.base_ligne_33500),
            _ligne(0, section, "Base ligne 33800", source, "33500 × 14,5 %", credits.credit_ligne_33800),
            _ligne(0, section, "Annexe 9 ligne 22", source, "min(dons réclamés, 200 $) × 14,5 %", credits.annexe9_ligne22),
            _ligne(0, section, "Ligne 34990", source,
                   "max(33800 + annexe 9 ligne 22 - 8 319,38 $, 0) × 3,45 %",
                   credits.credit_compensatoire_ligne_34990),
            _ligne(0, section, "Total ligne 35000", source,
                   "33800 + 34900 + 34990; application unique à l'impôt brut",
                   credits.total_credits_ligne_35000),
        )
        for ligne_audit in audit:
            lignes = _inserer_ligne_avant(lignes, "Impôt fédéral de base", ligne_audit)

    pret = estimation.interets_pret_etudiant
    rpret = estimation.resultat_interets_pret_etudiant
    if rpret.total_disponible:
        section = "INTÉRÊTS SUR PRÊTS ÉTUDIANTS 2025 — BLOC 5B"
        audit = [
            ("Intérêts payés en 2025", pret.interets_payes_2025, "Montant documenté, payé par contribuable ou personne apparentée"),
            ("Ligne fédérale 31900", rpret.ligne_31900, "Choix comptable; répartition 2020 → 2025; inclus une fois dans 33500"),
        ]
        audit += [(f"Intérêts {a} réclamés", m, "Plus ancien d'abord : 2020 → 2025") for a, m in rpret.utilises_par_annee]
        audit += [(f"Intérêts {a} non réclamés", m, "Ouverture documentée moins réclamation choisie") for a, m in rpret.non_reclames_par_annee]
        audit += [
            ("Incidence 31900 sur 33800", rpret.augmentation_33800, "Différence avec/sans 31900, arrondi global à 14,5 %"),
            ("Incidence 31900 sur 34990", rpret.augmentation_34990, "34990 recalculée par 5A"),
            ("Incidence 31900 sur 35000", rpret.augmentation_35000, "33800 + 34900 + 34990; aucune soustraction supplémentaire"),
            ("Réduction 42900 attribuable à 31900", rpret.reduction_42900, "Avec/sans 31900, après 40425, avant 40500, plancher zéro"),
            ("Économie fédérale réelle 5B", rpret.reduction_federale_apres_40500_et_abattement, "Avec/sans 31900 après 40500 et abattement de 16,5 % de 42900"),
            ("Solde non réclamé reportable en 2026", rpret.non_reclames_encore_reportables_2026, "Années 2021–2025 seulement; soldes documentés, aucun suivi ARC"),
            ("Solde 2020 expirant après 2025", rpret.non_reclame_2020_expirant, "2020 encore utilisable en 2025, pas en 2026"),
        ]
        for libelle, valeur, formule in audit:
            lignes = _inserer_ligne_avant(lignes, "Base ligne 33500", _ligne(0, section, libelle, pret.source, formule, valeur))

    if final.credit_formation_ligne_45350:
        for libelle, montant, formule in (
            ("Frais fédéraux nets après CCF", frais_scolarite.montant_net_federal, "Frais fédéraux bruts moins 45350; annexe 11 ligne 6"),
            ("Frais Québec nets après CCF", frais_scolarite.montant_net_quebec, "Annexe T : 40.6 moins 40.7"),
            ("Crédit formation remboursable 45350", final.credit_formation_ligne_45350, "min(plafond avis ARC, frais canadiens × 50 %); ajouté une fois aux paiements, après impôt"),
        ):
            lignes = lignes + (_ligne(len(lignes) + 1, "FORMATION 2025 — BLOC 5C", libelle,
                frais_scolarite.formation.source, formule, montant),)

    if frais_medicaux.supplement.reclamer:
        r = estimation.resultat_supplement_medical
        for libelle, montant, formule in (
            ("Revenu de travail pour 45200", r.revenu_travail, "max(10100 - 20700 - 21200 - 22900, 0); autres postes exclus du profil; minimum 4390"),
            ("Revenu familial ajusté 45200", r.revenu_familial_ajuste,
             (f"23600 du demandeur + max(23600 conjoint, 0) si conjoint retenu; situation : {frais_medicaux.supplement.situation_conjugale}; "
              f"revenu conjoint retenu {r.revenu_conjoint_retenu:.2f}; source {frais_medicaux.supplement.source_conjoint}; sans ajustements PUGE/REEI"
              if frais_medicaux.supplement.mode_familial else "23600, profil individuel sans ajustements PUGE/REEI")),
            ("Plafond médical avant réduction", r.montant_avant_reduction, "min(1504, 33200 × 25 %); 21500 exclu"),
            ("Réduction du supplément médical", r.reduction_revenu, "max(revenu familial - 33294, 0) × 5 %"),
            ("Supplément médical remboursable 45200", r.ligne_45200, "Si revenu travail >= 4390 : max(plafond - réduction, 0), sinon 0"),
        ):
            lignes += (_ligne(len(lignes) + 1, "SUPPLÉMENT MÉDICAL — BLOC 5D", libelle,
                frais_medicaux.supplement.source, formule, montant),)

    if estimation.allocation_travailleurs.famille.activer:
        for libelle, montant, formule in trace_act_familial_2025(estimation.resultat_allocation_travailleurs.famille):
            lignes += (_ligne(len(lignes) + 1, "ACT FAMILIALE — BLOC 5U", libelle,
                estimation.allocation_travailleurs.famille.source, formule, montant),)

    if estimation.allocation_travailleurs.present and not estimation.allocation_travailleurs.famille.activer:
        r = estimation.resultat_allocation_travailleurs
        for libelle, montant, formule in (
            ("Revenu travail ACT", r.revenu_travail, "10100 brut, profil salarié sans 10400 ni autres revenus de travail"),
            ("Revenu net ajusté ACT", r.revenu_net_ajuste, "23600, sans conjoint ni ajustements PUGE/REEI"),
            ("ACT avant réduction", r.base_avant_reduction, "Si base demandée : min(3812.06, max(travail - 2400, 0) × 37.3 %)"),
            ("Réduction ACT", r.reduction_base, "Si base demandée : max(net - 14170.05, 0) × 20 %"),
            ("Supplément ACT avant réduction", r.supplement_avant_reduction, "Si supplément demandé : min(851.31, max(travail - 1200, 0) × 40 %)"),
            ("Réduction supplément ACT", r.reduction_supplement, "Si supplément demandé : max(net - 33230.35, 0) × 20 %"),
            ("ACT remboursable 45300", r.ligne_45300, "Base et supplément après réduction, chacun avec plancher zéro"),
            ("Avances ACT 41500", r.ligne_41500, "min(45300, RC210 cases 10 + 11); ajouté à 42000, hors 42900"),
        ):
            lignes += (_ligne(len(lignes) + 1, "ACT QUÉBEC — BLOC 5E", libelle,
                estimation.allocation_travailleurs.source, formule, montant),)

    if frais_scolarite.reports_federaux.activer:
        r = estimation.resultat_reports_scolarite
        for libelle, montant, formule in (
            ("Report scolarité antérieur disponible", frais_scolarite.reports_federaux.report_avis_2024, "Dernier avis ARC 2024, annexe 11 ligne 9"),
            ("Capacité scolarité annexe 11", r.capacite_annexe11, "max(26000 si <=57375, sinon brut / 14.5 %, moins ligne 105; 0)"),
            ("Report scolarité antérieur utilisé", r.report_anterieur_utilise, "min(report disponible, capacité), utilisé en premier"),
            ("Frais 2025 utilisés", r.frais_2025_utilises, "min(frais nets après CCF, capacité restante)"),
            ("Scolarité réclamée 32300", r.ligne_32300, "Report utilisé + frais 2025 utilisés; intégré une seule fois à 33500"),
            ("Maximum de scolarité transférable", r.transfert_maximal, "max(min(frais 2025 nets, 5000) - frais 2025 utilisés, 0)"),
            ("Transfert sortant 32700", r.ligne_32700, "Montant désigné sur le certificat, au plus le maximum calculé"),
            ("Report scolarité fédéral futur", r.report_futur, "Report antérieur + frais 2025 nets - 32300 - 32700"),
        ):
            lignes += (_ligne(len(lignes) + 1, "REPORTS SCOLARITÉ — BLOC 5F", libelle,
                frais_scolarite.reports_federaux.source, formule, montant),)

    transfert = frais_scolarite.reports_federaux.transfert_sortant
    if transfert.present:
        lignes += (_ligne(len(lignes) + 1, "TRANSFERT SCOLARITÉ — BLOC 5G", "Bénéficiaire du transfert sortant",
            transfert.source, f"Autorisation signée : {transfert.beneficiaire} ({transfert.relation}); montant désigné validé",
            estimation.resultat_reports_scolarite.ligne_32700),)

    for designation in estimation.transferts_scolarite_recus.designations:
        lignes += (_ligne(len(lignes) + 1, "SCOLARITÉ REÇUE — BLOC 5H", "Désignation reçue : " + designation.nom_etudiant,
            designation.source, "Certificat signé, annexe 11 et plafond vérifiés par le comptable; référence " + designation.reference_etudiant,
            designation.montant_certificat),)
    if estimation.transferts_scolarite_recus.designations:
        lignes += (_ligne(len(lignes) + 1, "SCOLARITÉ REÇUE — BLOC 5H", "Scolarité reçue 32400",
            "Certificats des étudiants", "Somme des désignations; une fois dans 33500, puis 33800/34990/35000; aucun report chez le bénéficiaire",
            sum((d.montant_certificat for d in estimation.transferts_scolarite_recus.designations), Decimal("0"))),)

    if estimation.dons_bienfaisance.reports_federaux.activer:
        p = estimation.dons_bienfaisance.reports_federaux
        r = estimation.resultat_reports_dons
        for libelle, montant, formule in (
            ("Dons disponibles", r.disponible, "Dons courants + reports 2020–2024"),
            ("Plafond fédéral des dons", r.plafond_75, "Revenu net 23600 × 75 %"),
            ("Dons réclamés", r.montant_reclame, "Choix confirmé, au plus disponible et plafond; base 34900 et annexe 9 ligne 22"),
            ("Dons 2020 expirant après 2025", r.expiration_2020, "Solde non utilisé, exclu des reports futurs"),
        ):
            lignes += (_ligne(len(lignes) + 1, "REPORTS DONS — BLOC 5I", libelle, p.source, formule, montant),)
        sources = {x.annee: x.source for x in p.reports}
        sources[2025] = estimation.dons_bienfaisance.source_federale
        for annee, montant in r.utilisations:
            lignes += (_ligne(len(lignes) + 1, "REPORTS DONS — BLOC 5I", f"Dons {annee} utilisés", sources[annee],
                "Antérieurs avant courants; plus anciens d'abord", montant),)
        for annee, montant in r.reports_futurs:
            lignes += (_ligne(len(lignes) + 1, "REPORTS DONS — BLOC 5I", f"Dons {annee} reportables", sources[annee],
                f"Solde non réclamé; dernière année {annee + 5}", montant),)

    ventilations_dons = []
    if dons.montant_admissible_federal or dons.reports_federaux.activer:
        ventilations_dons.append(("fédéraux", ventiler_credit_federal_dons_2025(dons, revenu.revenu_imposable_federal),
            dons.source_federale or dons.reports_federaux.source, ("14,5 %", "29 %", "33 %")))
    if dons.montant_admissible_quebec:
        ventilations_dons.append(("Québec", ventiler_credit_quebec_dons_2025(dons, revenu.revenu_imposable_quebec),
            dons.source_quebec, ("20 %", "24 %", "25,75 %")))
    for juridiction, ventilation, source, taux in ventilations_dons:
        for base_dons, pourcentage in zip((ventilation.base_premiers_200, ventilation.base_taux_intermediaire, ventilation.base_taux_superieur), taux):
            lignes += (_ligne(len(lignes) + 1, "TAUX DES DONS — BLOC 5J", f"Dons {juridiction} — base à {pourcentage}",
                source, "Répartition selon revenu imposable; composante du crédit pour dons", base_dons),)

    if estimation.transfert_conjoint.activer:
        r = estimation.resultat_transfert_conjoint
        for libelle, montant, formule in (
            ("Conjoint — annexe 2 ligne 6", r.total_ligne_6, "30100 + 30500 + 31400 + 31600 + scolarité désignée 36000"),
            ("Conjoint — équivalent ligne 7", r.equivalent_ligne_7, "26000 si <= 57375; sinon impôt brut / 14,5 %"),
            ("Conjoint — base T1 Québec ligne 100", r.base_ligne_100, "Somme T1 lignes 87 à 99; exclut 31900 et montants familiaux"),
            ("Conjoint — annexe 2 ligne 11", r.total_ligne_11, "30000 + T1 Québec ligne 100 + 32300"),
            ("Conjoint — réduction 36100", r.reduction_36100, "max(ligne 7 - ligne 11, 0)"),
            ("Transfert du conjoint — ligne 32600", r.ligne_32600, "max(ligne 6 - 36100, 0); inclus une fois dans 33500"),
        ):
            lignes += (_ligne(len(lignes) + 1, "TRANSFERT CONJOINT — BLOC 5K", libelle,
                estimation.transfert_conjoint.source + " — " + r.nom_conjoint, formule, montant),)

    if estimation.benevoles.choix:
        r = estimation.resultat_benevoles
        for libelle, montant, formule in (
            ("Bénévoles — heures admissibles", r.heures_pompiers + r.heures_sauvetage, "Heures certifiées, organismes admissibles; services rémunérés similaires exclus"),
            ("Case 87 réintégrée à 10100", r.reintegration_10100, "Crédit choisi : somme des cases 87 ajoutée aux cases 14"),
            ("Revenu exonéré — ligne 10105", r.exemption_10105, "Exonération choisie : cases 87, sans crédit 31220/31240"),
        ):
            lignes += (_ligne(len(lignes) + 1, "SERVICES BÉNÉVOLES — BLOC 5L", libelle,
                estimation.benevoles.source, formule, montant),)
        if r.ligne_credit:
            lignes += (_ligne(len(lignes) + 1, "SERVICES BÉNÉVOLES — BLOC 5L", "Base bénévoles — ligne " + r.ligne_credit,
                estimation.benevoles.source, "6000 $; au moins 200 heures; inclus une fois avant 32300 dans 33500", r.base_credit),)

    if estimation.contributions_politiques.recus:
        p, r = estimation.contributions_politiques, estimation.resultat_contributions_politiques
        for libelle, montant, formule in (
            ("Contributions politiques — 40900", r.ligne_40900, "Paiements monétaires moins avantages, reçus validés une seule fois"),
            ("Crédit politique — 41000", r.ligne_41000, "75 % jusqu'à 400; 50 % des 350 suivants; 1/3 au-delà; maximum 650"),
            ("Impôt fédéral — 41700", final.impot_federal_ligne_41700, "max(40600 - 41600, 0); 41600 = 41000 + 41400 dans ce profil"),
            ("Crédit politique utilisé", final.credit_politique_utilise, "min(41000, 40600); aucun report de l'inutilisé"),
        ):
            lignes = _inserer_ligne_avant(lignes, "Impôt fédéral après abattement",
                _ligne(0, "CONTRIBUTIONS POLITIQUES — BLOC 5N", libelle, p.source, formule, montant))

    if estimation.renovations_multigenerationnelles.renovations:
        p, r = estimation.renovations_multigenerationnelles, estimation.resultat_multigenerationnel
        for projet, calcul in zip(p.renovations, r.renovations):
            lignes += (_ligne(len(lignes) + 1, "RÉNOVATION MULTIGÉNÉRATIONNELLE — BLOC 5Q",
                projet.logement + " — " + projet.unite, projet.source,
                f"min({calcul.depenses_nettes}, 50000 - {calcul.autres_demandes})", calcul.base_retenue),)
        for libelle, montant, formule in (
            ("Base multigénérationnelle — 45354", r.ligne_45354, "Somme des bases retenues par rénovation après partage"),
            ("Crédit multigénérationnel remboursable — 45355", r.ligne_45355, "45354 × 14,5 %; ajouté une fois aux paiements sans plafond d'impôt"),
        ):
            lignes += (_ligne(len(lignes) + 1, "RÉNOVATION MULTIGÉNÉRATIONNELLE — BLOC 5Q", libelle,
                "; ".join(x.source for x in p.renovations), formule, montant),)

    if estimation.fournitures_educateur.depenses:
        p, r = estimation.fournitures_educateur, estimation.resultat_fournitures_educateur
        for libelle, montant, formule in (
            ("Fournitures scolaires nettes", r.depenses_admissibles, "Paiements moins aides hors exception imposable non déductible"),
            ("Fournitures scolaires — 46800", r.ligne_46800, "min(1000, dépenses nettes); zéro si attestation demandée non fournie"),
            ("Crédit éducateur remboursable — 46900", r.ligne_46900, "46800 × 25 %; ajouté une fois aux paiements, sans plafond d'impôt"),
        ):
            lignes += (_ligne(len(lignes) + 1, "FOURNITURES SCOLAIRES — BLOC 5P", libelle, p.source, formule, montant),)

    if estimation.fonds_travailleurs.acquisitions:
        p, r = estimation.fonds_travailleurs, estimation.resultat_fonds_travailleurs
        for libelle, montant, formule in (
            ("Fonds de travailleurs — 41300", r.ligne_41300, "Paiements moins aides publiques hors crédits; coût réservé à 2026 exclu"),
            ("Fonds : crédit utilisé en 2024", r.credit_utilise_2024, "Utilisation effective sur les acquisitions des 60 premiers jours de 2025"),
            ("Fonds de travailleurs — 41400", r.ligne_41400, "min(750, max(0, 41300 × 15 % - crédit utilisé en 2024)); LIR 127.4(5)"),
            ("Crédit fonds utilisé", final.credit_fonds_utilise, "min(41400, max(40600 - 41000, 0))"),
            ("Total des crédits — 41600", final.credits_ligne_41600, "41000 + 41400; avant avances ACT 41500"),
            ("Impôt après fonds — 41700", final.impot_federal_ligne_41700, "max(40600 - 41600, 0); abattement 44000 inchangé"),
        ):
            lignes = _inserer_ligne_avant(lignes, "Impôt fédéral après abattement",
                _ligne(0, "FONDS DE TRAVAILLEURS — BLOC 5O", libelle, p.source, formule, montant))

    for e, r in zip(estimation.adoption.enfants, estimation.resultat_adoption.enfants):
        source = e.source + " — " + e.nom
        for libelle, montant, formule in (
            ("Dépenses d'adoption", r.depenses, f"Somme des frais payés, engagés du {r.debut} au {r.fin}"),
            ("Aides à retrancher", r.aides_deductibles, "Aides reçues ou à recevoir moins exception imposable non déductible"),
            ("Base d'adoption plafonnée", r.base_plafonnee, "min(19580, max(dépenses - aides à retrancher, 0))"),
            ("Adoption — ligne 31300", r.montant_31300, f"Base plafonnée × part convenue {r.part_pourcentage} %; avant scolarité et dans 33500"),
            ("Adoption — solde maximal des autres demandeurs", r.reste_autres_demandeurs, "Base plafonnée moins part du demandeur"),
        ):
            lignes += (_ligne(len(lignes) + 1, "FRAIS D'ADOPTION — BLOC 5M", libelle, source, formule, montant),)

    if estimation.transferts_handicap.transferts:
        for t, d in zip(estimation.transferts_handicap.transferts, estimation.resultat_transferts_handicap.donneurs):
            c = d.calcul
            source = t.nom_donneur + " : " + t.source + "; " + t.rapprochement_30400_30450
            for libelle, valeur, formule in (
                ("Donneur — base handicap 31600", c.montant_31600, "10 138 + supplément mineur net des soins"),
                ("Donneur — impôt hypothétique", c.impot_avant_handicap, "Impôt brut moins crédits 118 à 118.07/118.7 et compensatoire permis; ajouts partie I inclus"),
                ("Donneur — crédit handicap disponible", c.credit_disponible, "max(31600 × 14,5 % - impôt hypothétique, 0)"),
                ("Donneur — crédit handicap utilisé", c.credit_utilise, "Crédit DTC total moins crédit inutilisé selon 118.3(2)"),
                ("Donneur — base handicap utilisée", c.base_utilisee, "Base 31600 moins base transférable arrondie au cent"),
                ("Donneur — base disponible", c.base_disponible, "min(31600, crédit disponible / 14,5 %), au cent"),
                ("Donneur — part reçue", d.base_retenue, "Base disponible moins autres parts; choix de part limitée si activé"),
            ):
                lignes = _inserer_ligne_avant(lignes, "Base ligne 33500", _ligne(0, "TRANSFERT HANDICAP 31800", libelle, source, formule, valeur))
        lignes = _inserer_ligne_avant(lignes, "Base ligne 33500", _ligne(0,
            "TRANSFERT HANDICAP 31800", "Handicap transféré — ligne 31800", "LIR 118.3(2); dossiers validés",
            "Somme des parts reçues; incluse une fois avant scolarité; aucun effet sur revenus ou Québec",
            estimation.resultat_transferts_handicap.ligne_31800))

    if estimation.frais_medicaux_famille.personnes:
        p, r = estimation.frais_medicaux_famille, estimation.resultat_medical_familial
        for personne, calcul in zip(p.personnes, r.personnes):
            if calcul.ligne == "33199":
                lignes = _inserer_ligne_avant(lignes, "Base ligne 33500", _ligne(0,
                    "FRAIS MÉDICAUX FAMILIAUX", "33199 — " + personne.nom,
                    personne.source_lien_dependance + "; " + personne.source_revenu,
                    f"max({calcul.frais_nets} - min(3 % × max({calcul.revenu_net}, 0), 2834), 0)", calcul.montant_admissible))
        for libelle, valeur, formule in (
            ("Frais médicaux familiaux — 33099", r.ligne_33099, "Somme des reçus nets du demandeur, conjoint et enfants mineurs"),
            ("Frais médicaux familiaux — 33199", r.ligne_33199, "Somme après seuil propre à chaque autre personne à charge"),
            ("Frais médicaux familiaux — 33200", r.ligne_33200, f"max(33099 - {r.seuil_demandeur}, 0) + 33199; une inclusion dans 33500"),
        ):
            lignes = _inserer_ligne_avant(lignes, "Base ligne 33500", _ligne(0,
                "FRAIS MÉDICAUX FAMILIAUX", libelle, p.debut_periode + " au " + p.fin_periode + "; reçus validés", formule, valeur))

    prochain_ordre = len(lignes) + 1

    if final.remboursement_estime > Decimal("0"):
        montant = final.remboursement_estime
        if final.remboursements_cotisations_totaux > Decimal("0"):
            formule = (
                "Retenues + remboursements cotisations RRQ/AE/RQAP "
                "- impôt total préliminaire"
            )
        else:
            formule = "Retenues totales - impôt total préliminaire"
    elif final.solde_estime > Decimal("0"):
        montant = final.solde_estime
        if final.remboursements_cotisations_totaux > Decimal("0"):
            formule = (
                "Impôt total préliminaire - retenues - remboursements "
                "cotisations RRQ/AE/RQAP"
            )
        else:
            formule = "Impôt total préliminaire - retenues totales"
    else:
        montant = Decimal("0")
        formule = "Retenues totales = impôt total préliminaire"

    if final.credit_formation_ligne_45350:
        formule = ("Retenues + remboursements cotisations + crédit formation 45350 - impôt total"
                   if final.remboursement_estime else
                   "Impôt total - retenues - remboursements cotisations - crédit formation 45350")

    if final.supplement_medical_ligne_45200:
        formule = ("Retenues + remboursements cotisations + crédits 45350/45200 - impôt total"
                   if final.remboursement_estime else
                   "Impôt total - retenues - remboursements cotisations - crédits 45350/45200")

    if final.allocation_travailleurs_ligne_45300:
        formule = ("Retenues + remboursements cotisations + crédits 45200/45300/45350 - impôt total incluant 41500"
                   if final.remboursement_estime else
                   "Impôt total incluant 41500 - retenues - remboursements cotisations - crédits 45200/45300/45350")

    if final.credit_educateur_ligne_46900 or final.credit_multigenerationnel_ligne_45355:
        formule = ("Retenues + remboursements cotisations + crédits 45200/45300/45350/45355/46900 - impôt total incluant 41500"
                   if final.remboursement_estime else
                   "Impôt total incluant 41500 - retenues - remboursements cotisations - crédits 45200/45300/45350/45355/46900")

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
        formule_resultat=formule,
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
