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
    credit_quebec_dons_2025,
)
from .tax_disability_2025 import (
    credit_federal_handicap_2025,
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
        formule_impot_federal += " - crédit impôt étranger 40500 confirmé via T2209"
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
                "Impôt fédéral de base",
                "FÉDÉRAL",
                "Crédit impôt étranger ligne 40500",
                "T2209 — " + cc.source_t2209,
                "Montant T2209 2025 confirmé; crédit non remboursable",
                c.ligne_40500,
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

    if aidant_enfant_federal.reclamer_montant:
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

    if aidant_30450_federal.reclamer_montant:
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
                    + ", limité à 8 601 $ = ligne 30450 "
                    + formater_montant_estimation(montant_30450)
                    + "; ligne 51120 = "
                    + str(nombre_51120)
                    + " personne à charge; crédit fédéral × 14,5 %; "
                    + "aucune ligne 30300/30400 pour cette même personne; "
                    + "aucune pension alimentaire; aucun partage; "
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
                    "Montant fédéral 2025 de 10 138 $ × 14,5 % "
                    "— personne elle-même, 18 ans ou plus"
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
