"""Export PDF local du rapport d'estimation fiscale 2025."""

from pathlib import Path
import re
import textwrap
import fitz
from .tax_capital_loss_carryovers_2025 import lignes_resume_reports_pertes_2025
from .tax_investment_expenses_2025 import lignes_resume_frais_placement_2025
from .tax_capital_gains_2025 import lignes_resume_capital_2025
from .tax_dividend_income_2025 import lignes_resume_dividendes_2025
from .tax_interest_income_2025 import lignes_resume_interets_2025
from .tax_investment_combinations_2025 import (
    CombinaisonInteretsDividendes2025,
    lignes_resume_interets_dividendes_2025,
)
from .tax_foreign_investment_2025 import (
    lignes_resume_placement_etranger_2025,
    lignes_resume_credit_impot_etranger_2025,
)
from .tax_replacement_benefits_2025 import lignes_resume_remplacement_2025
from .tax_rrsp_withdrawals_2025 import lignes_resume_retraits_2025
from .tax_pension_income_2025 import lignes_resume_pensions_2025
from .tax_old_age_security_2025 import lignes_resume_psv_2025
from .tax_cpp_qpp_benefits_2025 import lignes_resume_rrq_rpc_2025
from .tax_employment_insurance_2025 import lignes_resume_ae_2025
from .tax_parental_benefits_2025 import lignes_resume_rqap_2025
from .tax_rpp_2025 import lignes_resume_rpa_2025

from .tax_estimation_2025 import (
    EstimationFiscale2025,
    formater_montant_estimation,
)
from .tax_federal_spouse_2025 import (
    credit_federal_montant_conjoint_2025,
    montant_ligne_30300_2025,
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
    credit_federal_ligne_30425_2025,
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
from .tax_federal_age_pension_2025 import (
    credit_federal_age_pension_2025,
    montant_age_federal_2025,
    montant_pension_federal_2025,
)
from .tax_age_retirement_2025 import (
    MONTANT_REVENUS_RETRAITE_MAX_2025,
    SEUIL_REDUCTION_ANNEXE_B_2025,
    credit_quebec_age_retraite_2025,
    montant_age_2025,
    montant_ligne_361_age_retraite_2025,
    montant_revenus_retraite_2025,
    reduction_annexe_b_age_retraite_2025,
    revenu_retraite_net_admissible_2025,
)
from .tax_living_alone_2025 import (
    MONTANT_PERSONNE_VIVANT_SEULE_2025,
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
from .tax_disability_2025 import (
    MONTANT_FEDERAL_HANDICAP_2025,
    MONTANT_QUEBEC_DEFICIENCE_2025,
    credit_federal_handicap_2025,
    credit_quebec_deficience_2025,
)
from .tax_drug_insurance_2025 import (
    code_exemption_case_449_2025,
)


def nom_rapport_fiscal_pdf_2025(estimation: EstimationFiscale2025) -> str:
    client = re.sub(r"[^\w-]+", "_", estimation.dossier.client.strip())
    client = re.sub(r"_+", "_", client).strip("_") or "client"
    return (
        f"Estimation_Fiscale_"
        f"{estimation.dossier.annee_fiscale}_{client}.pdf"
    )


def _lignes(estimation: EstimationFiscale2025) -> list[str]:
    b = estimation.base
    r = estimation.revenu
    f = estimation.federal
    q = estimation.quebec
    x = estimation.rapprochement
    medical = estimation.frais_medicaux
    scolarite = estimation.frais_scolarite
    deficience = estimation.credit_deficience
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

    montant = (
        x.remboursement_estime
        if x.remboursement_estime
        else x.solde_estime
    )

    lignes = [
        "ESTIMATION FISCALE 2025 - VALIDATION COMPTABLE OBLIGATOIRE",
        "",
        f"Client : {estimation.dossier.client}",
        f"Année fiscale : {estimation.dossier.annee_fiscale}",
        f"Province : {estimation.dossier.province}",
        "",
        "REVENU",
        (
            "Revenu d'emploi fédéral : "
            f"{formater_montant_estimation(b.revenu_emploi_federal)}"
        ),
        (
            "Revenu net fédéral : "
            f"{formater_montant_estimation(r.revenu_net_federal)}"
        ),
        (
            "Revenu imposable fédéral : "
            f"{formater_montant_estimation(r.revenu_imposable_federal)}"
        ),
        (
            "Revenu d'emploi Québec : "
            f"{formater_montant_estimation(b.revenu_emploi_quebec)}"
        ),
        (
            "Revenu net Québec : "
            f"{formater_montant_estimation(r.revenu_net_quebec)}"
        ),
        (
            "Revenu imposable Québec : "
            f"{formater_montant_estimation(r.revenu_imposable_quebec)}"
        ),
    ]

    lignes.extend(lignes_resume_rpa_2025(estimation.cotisations_rpa))
    lignes.extend(lignes_resume_rqap_2025(estimation.prestations_rqap))
    lignes.extend(lignes_resume_ae_2025(estimation.prestations_ae))
    lignes.extend(lignes_resume_rrq_rpc_2025(estimation.prestations_rrq_rpc))
    lignes.extend(lignes_resume_psv_2025(estimation.prestations_psv))
    lignes.extend(lignes_resume_reports_pertes_2025(estimation.reports_pertes, estimation.profil_reports_pertes))
    lignes.extend(lignes_resume_frais_placement_2025(estimation.frais_placement, estimation.profil_frais_placement, estimation.reports_pertes.present))
    lignes.extend(lignes_resume_capital_2025(estimation.capital, estimation.profil_capital, estimation.reports_pertes.present))
    lignes.extend(lignes_resume_interets_dividendes_2025(CombinaisonInteretsDividendes2025(
        interets=estimation.interets,
        dividendes=estimation.dividendes,
        assiette_fss=estimation.interets.ligne_130 + estimation.dividendes.ligne_166 + estimation.dividendes.ligne_167,
        cotisation_fss=estimation.interets.cotisation_fss,
        present=estimation.interets.present and estimation.dividendes.present,
    )))
    lignes.extend(lignes_resume_dividendes_2025(estimation.dividendes, estimation.profil_dividendes))
    lignes.extend(lignes_resume_interets_2025(estimation.interets, estimation.profil_interets))
    lignes.extend(
        lignes_resume_placement_etranger_2025(
            estimation.placement_etranger,
            estimation.profil_placement_etranger,
        )
    )
    lignes.extend(
        lignes_resume_credit_impot_etranger_2025(
            estimation.credit_impot_etranger,
            estimation.profil_credit_impot_etranger,
        )
    )
    lignes.extend(lignes_resume_remplacement_2025(estimation.remplacement, estimation.profil_remplacement))
    lignes.extend(lignes_resume_retraits_2025(estimation.retraits, estimation.profil_retraits))
    lignes.extend(lignes_resume_pensions_2025(estimation.pensions, estimation.profil_pensions))
    if estimation.prestations_rqap.present or estimation.prestations_ae.present or estimation.prestations_rrq_rpc.present or estimation.prestations_psv.present or estimation.pensions.present or estimation.retraits.present or estimation.interets.present or estimation.placement_etranger.present or estimation.dividendes.present or estimation.capital.present:
        lignes.extend([
            f"Revenu total fédéral : {formater_montant_estimation(r.revenu_total_federal)}",
            f"Revenu total Québec : {formater_montant_estimation(r.revenu_total_quebec)}",
        ])

    if (
        medical.montant_admissible_federal > 0
        or medical.montant_admissible_quebec > 0
    ):
        credit_federal = credit_federal_frais_medicaux_2025(
            medical,
            r.revenu_net_federal,
        )
        credit_quebec = credit_quebec_frais_medicaux_2025(
            medical,
            r.revenu_net_quebec,
        )

        lignes.extend(
            [
                "",
                "FRAIS MÉDICAUX VALIDÉS",
                (
                    "Montant admissible fédéral : "
                    f"{formater_montant_estimation(
                        medical.montant_admissible_federal
                    )}"
                ),
                (
                    "Crédit fédéral - lignes 33099 / 33200 : "
                    f"{formater_montant_estimation(credit_federal)}"
                ),
                f"Source fédérale : {medical.source_federale}",
                (
                    "Montant admissible Québec : "
                    f"{formater_montant_estimation(
                        medical.montant_admissible_quebec
                    )}"
                ),
                (
                    "Crédit Québec - ligne 381 : "
                    f"{formater_montant_estimation(credit_quebec)}"
                ),
                f"Source Québec : {medical.source_quebec}",
                (
                    "Validation comptable : "
                    + (
                        "confirmée"
                        if medical.valide_par_comptable
                        else "non confirmée"
                    )
                ),
                (
                    "Reçus confirmés : "
                    + ("oui" if medical.recus_confirmes else "non")
                ),
                (
                    "Remboursements soustraits : "
                    + (
                        "oui"
                        if medical.remboursements_soustraits
                        else "non"
                    )
                ),
                (
                    "Période de 12 mois se terminant en 2025 : "
                    + (
                        "confirmée"
                        if medical.periode_12_mois_fin_2025_confirmee
                        else "non confirmée"
                    )
                ),
            ]
        )

    if (
        scolarite.montant_admissible_federal > 0
        or scolarite.montant_admissible_quebec > 0
    ):
        credit_federal_scolarite = (
            credit_federal_frais_scolarite_2025(
                scolarite
            )
        )
        credit_quebec_scolarite = (
            credit_quebec_frais_scolarite_2025(
                scolarite
            )
        )

        lignes.extend(
            [
                "",
                "FRAIS DE SCOLARITÉ / EXAMEN VALIDÉS",
                (
                    "Montant admissible fédéral : "
                    f"{formater_montant_estimation(
                        scolarite.montant_admissible_federal
                    )}"
                ),
                (
                    "Crédit fédéral - ligne 32300 : "
                    f"{formater_montant_estimation(
                        credit_federal_scolarite
                    )}"
                ),
                f"Source fédérale : {scolarite.source_federale}",
                (
                    "Montant admissible Québec : "
                    f"{formater_montant_estimation(
                        scolarite.montant_admissible_quebec
                    )}"
                ),
                (
                    "Crédit Québec - ligne 398 : "
                    f"{formater_montant_estimation(
                        credit_quebec_scolarite
                    )}"
                ),
                f"Source Québec : {scolarite.source_quebec}",
                (
                    "Validation comptable : "
                    + (
                        "confirmée"
                        if scolarite.valide_par_comptable
                        else "non confirmée"
                    )
                ),
                (
                    "Pièce fédérale confirmée : "
                    + (
                        "oui"
                        if scolarite.piece_federale_confirmee
                        else "non"
                    )
                ),
                (
                    "Reçu officiel Québec confirmé : "
                    + (
                        "oui"
                        if scolarite.recu_officiel_quebec_confirme
                        else "non"
                    )
                ),
                (
                    "Seuil de plus de 100 $ confirmé : "
                    + (
                        "oui"
                        if scolarite.seuil_100_confirme
                        else "non"
                    )
                ),
                (
                    "Remboursements soustraits : "
                    + (
                        "oui"
                        if scolarite.remboursements_soustraits
                        else "non"
                    )
                ),
                (
                    "Frais 2025 uniquement : "
                    + (
                        "oui"
                        if scolarite.frais_2025_uniquement
                        else "non"
                    )
                ),
                (
                    "Aucun report antérieur : "
                    + (
                        "oui"
                        if scolarite.aucun_report_anterieur
                        else "non"
                    )
                ),
                (
                    "Aucun transfert : "
                    + (
                        "oui"
                        if scolarite.aucun_transfert
                        else "non"
                    )
                ),
            ]
        )

    if (
        deficience.reclamer_federal
        or deficience.reclamer_quebec
    ):
        lignes.extend(
            [
                "",
                "HANDICAP / DÉFICIENCE VALIDÉ(E)",
            ]
        )

        if deficience.reclamer_federal:
            lignes.extend(
                [
                    (
                        "Montant fédéral — ligne 31600 : "
                        f"{formater_montant_estimation(
                            MONTANT_FEDERAL_HANDICAP_2025
                        )}"
                    ),
                    (
                        "Crédit fédéral — ligne 31600 : "
                        f"{formater_montant_estimation(
                            credit_federal_handicap_2025(
                                deficience
                            )
                        )}"
                    ),
                    (
                        "Source fédérale : "
                        f"{deficience.source_federale}"
                    ),
                ]
            )

        if deficience.reclamer_quebec:
            lignes.extend(
                [
                    (
                        "Montant Québec — ligne 376 : "
                        f"{formater_montant_estimation(
                            MONTANT_QUEBEC_DEFICIENCE_2025
                        )}"
                    ),
                    (
                        "Crédit Québec — ligne 376 : "
                        f"{formater_montant_estimation(
                            credit_quebec_deficience_2025(
                                deficience
                            )
                        )}"
                    ),
                    (
                        "Source Québec : "
                        f"{deficience.source_quebec}"
                    ),
                ]
            )

        lignes.extend(
            [
                (
                    "Validation comptable : "
                    + (
                        "confirmée"
                        if deficience.valide_par_comptable
                        else "non confirmée"
                    )
                ),
                (
                    "18 ans ou plus au 1er janvier 2025 : "
                    + (
                        "oui"
                        if deficience.age_18_plus_au_1_janvier_2025
                        else "non"
                    )
                ),
                (
                    "Déficience d'au moins 12 mois : "
                    + (
                        "confirmée"
                        if deficience.deficience_12_mois_confirmee
                        else "non confirmée"
                    )
                ),
                (
                    "Profil pour soi-même Québec/Canada : "
                    + (
                        "confirmé"
                        if deficience.profil_soi_meme_resident_quebec
                        else "non confirmé"
                    )
                ),
                (
                    "CIPH / T2201 approuvé par l'ARC : "
                    + (
                        "oui"
                        if deficience.ciph_approuve_arc
                        else "non"
                    )
                ),
                (
                    "Attestation professionnelle Québec : "
                    + (
                        "confirmée"
                        if deficience.attestation_quebec_confirmee
                        else "non confirmée"
                    )
                ),
                (
                    "Aucun conflit soins préposé / établissement : "
                    + (
                        "oui"
                        if (
                            deficience
                            .aucun_conflit_soins_prepose_etablissement
                        )
                        else "non"
                    )
                ),
                (
                    "Aucun transfert fédéral : "
                    + (
                        "oui"
                        if deficience.aucun_transfert_federal
                        else "non"
                    )
                ),
            ]
        )


    if accessibilite_domiciliaire_federale.reclamer_montant:
        montant_31285 = montant_ligne_31285_2025(
            accessibilite_domiciliaire_federale
        )
        credit_31285 = credit_federal_ligne_31285_2025(
            accessibilite_domiciliaire_federale
        )

        lignes.extend(
            [
                "",
                "ACCESSIBILITÉ DOMICILIAIRE - FÉDÉRAL 2025",
                (
                    "Dépenses admissibles - ligne 31285 : "
                    f"{formater_montant_estimation(montant_31285)}"
                ),
                (
                    "Crédit fédéral calculé - ligne 31285 : "
                    f"{formater_montant_estimation(credit_31285)}"
                ),
                "Maximum ligne 31285 : 20 000 $",
                "Taux du crédit fédéral 2025 : 14,5 %",
                "Demande pour soi-même : oui",
                (
                    "65 ans ou plus à la fin de 2025 : "
                    + (
                        "oui"
                        if accessibilite_domiciliaire_federale
                        .age_65_plus_fin_annee
                        else "non"
                    )
                ),
                (
                    "Admissible au CIPH en 2025 : "
                    + (
                        "oui"
                        if accessibilite_domiciliaire_federale
                        .admissible_ciph
                        else "non"
                    )
                ),
                "Logement situé au Canada : oui",
                "Logement appartenant au contribuable : oui",
                (
                    "Logement normalement habité par le contribuable : "
                    "oui"
                ),
                "Rénovation durable et intégrante : oui",
                (
                    "Accessibilité / mobilité / réduction du risque : "
                    "confirmée"
                ),
                "Travaux et biens de 2025 uniquement : oui",
                "Aucune part entreprise/location : oui",
                "Aucun partage de la demande ligne 31285 : oui",
                "Fournisseurs liés : règles confirmées",
                "Dépenses non admissibles exclues : oui",
                "Pièces justificatives conservées : oui",
                "Validation comptable : confirmée",
                (
                    "Source : "
                    f"{accessibilite_domiciliaire_federale.source_renovation}"
                ),
                (
                    "Ligne 34990 : garde-fou actif pour les profils "
                    "au-delà de la première tranche fédérale."
                ),
                (
                    "Profil simple : demande pour soi-même; partage et "
                    "ventilation entreprise/location non pris en charge "
                    "dans cette première version."
                ),
            ]
        )

    if achat_habitation_federal.reclamer_montant:
        montant_31270 = montant_ligne_31270_2025(
            achat_habitation_federal
        )
        credit_31270 = credit_federal_ligne_31270_2025(
            achat_habitation_federal
        )

        lignes.extend(
            [
                "",
                "ACHAT D'UNE HABITATION - FÉDÉRAL 2025",
                (
                    "Montant réclamé - ligne 31270 : "
                    f"{formater_montant_estimation(montant_31270)}"
                ),
                (
                    "Crédit fédéral calculé - ligne 31270 : "
                    f"{formater_montant_estimation(credit_31270)}"
                ),
                "Maximum ligne 31270 : 10 000 $",
                "Taux du crédit fédéral 2025 : 14,5 %",
                "Acquisition en 2025 : oui",
                "Habitation admissible : oui",
                "Habitation située au Canada : oui",
                (
                    "Habitation enregistrée au nom du contribuable "
                    "ou du conjoint : oui"
                ),
                "Première habitation : confirmée",
                (
                    "Année de l'achat et quatre années précédentes : "
                    "critère confirmé"
                ),
                (
                    "Intention de résidence principale dans un an : "
                    "confirmée"
                ),
                "Aucun partage du montant ligne 31270 : oui",
                (
                    "Exception handicap non utilisée dans ce profil "
                    "simple : oui"
                ),
                "Pièces justificatives conservées : oui",
                "Validation comptable : confirmée",
                (
                    "Source : "
                    f"{achat_habitation_federal.source_habitation}"
                ),
                (
                    "Ligne 34990 : garde-fou actif pour les profils "
                    "au-delà de la première tranche fédérale."
                ),
                (
                    "Profil simple : partage et exception handicap "
                    "non pris en charge dans cette première version."
                ),
            ]
        )

    if aidant_30450_federal.reclamer_montant:
        montant_30450 = montant_ligne_30450_2025(
            aidant_30450_federal
        )
        credit_30450 = credit_federal_ligne_30450_2025(
            aidant_30450_federal
        )
        nombre_51120 = nombre_personnes_charge_ligne_51120_2025(
            aidant_30450_federal
        )

        lignes.extend(
            [
                "",
                (
                    "AIDANT NATUREL - AUTRE PERSONNE À CHARGE 18+ - "
                    "FÉDÉRAL 2025"
                ),
                (
                    "Lien avec la personne : "
                    f"{aidant_30450_federal.lien_personne}"
                ),
                (
                    "Revenu net de la personne - ligne 23600 : "
                    f"{formater_montant_estimation(
                        aidant_30450_federal.revenu_net_personne_ligne_23600
                    )}"
                ),
                (
                    "Nombre de personnes à charge - ligne 51120 : "
                    f"{nombre_51120}"
                ),
                (
                    "Montant canadien pour aidant naturel - ligne 30450 : "
                    f"{formater_montant_estimation(montant_30450)}"
                ),
                (
                    "Crédit fédéral calculé - ligne 30450 : "
                    f"{formater_montant_estimation(credit_30450)}"
                ),
                "Base de calcul 2025 : 28 798 $",
                "Maximum ligne 30450 : 8 601 $",
                "Taux du crédit fédéral 2025 : 14,5 %",
                "Personne à charge âgée de 18 ans ou plus : oui",
                "Personne soutenue par le contribuable en 2025 : oui",
                "Infirmité physique ou mentale confirmée : oui",
                "Dépendance due à l'infirmité : oui",
                "Dépendance pendant une période considérable : oui",
                (
                    "Résidence au Canada confirmée lorsque requise : "
                    "oui"
                ),
                (
                    "Aucun montant ligne 30300/30400 pour cette "
                    "personne : oui"
                ),
                "Aucune pension alimentaire pour cette personne : oui",
                "Aucun partage de la réclamation 30450 : oui",
                (
                    "Preuve médicale admissible ou T2201 approuvé : "
                    "confirmée"
                ),
                "Validation comptable : confirmée",
                f"Source : {aidant_30450_federal.source_personne}",
                (
                    "Ligne 34990 : garde-fou actif pour les profils "
                    "au-delà de la première tranche fédérale."
                ),
                (
                    "Profil simple : une seule autre personne à charge; "
                    "les cas complexes ou partagés restent refusés."
                ),
            ]
        )

    if aidant_30425_federal.reclamer_montant:
        montant_30425 = montant_ligne_30425_2025(
            aidant_30425_federal
        )
        credit_30425 = credit_federal_ligne_30425_2025(
            aidant_30425_federal
        )
        ligne_source_30425 = (
            "30300"
            if aidant_30425_federal.type_personne == "conjoint"
            else "30400"
        )
        type_personne_30425 = (
            "conjoint"
            if aidant_30425_federal.type_personne == "conjoint"
            else "personne à charge admissible"
        )

        lignes.extend(
            [
                "",
                (
                    "AIDANT NATUREL - CONJOINT / PERSONNE À CHARGE - "
                    "FÉDÉRAL 2025"
                ),
                "Type de personne : " + type_personne_30425,
                (
                    "Revenu net de la personne - ligne 23600 : "
                    + formater_montant_estimation(
                        aidant_30425_federal
                        .revenu_net_personne_ligne_23600
                    )
                ),
                (
                    "Montant source - ligne "
                    + ligne_source_30425
                    + " : "
                    + formater_montant_estimation(
                        aidant_30425_federal
                        .montant_reclame_ligne_30300_ou_30400
                    )
                ),
                (
                    "Montant canadien pour aidant naturel - ligne 30425 : "
                    + formater_montant_estimation(montant_30425)
                ),
                (
                    "Crédit fédéral - ligne 30425 : "
                    + formater_montant_estimation(credit_30425)
                ),
                "Taux du crédit fédéral 2025 : 14,5 %",
                (
                    "Personne soutenue en 2025 : "
                    + (
                        "oui"
                        if aidant_30425_federal.personne_soutenue_en_2025
                        else "non"
                    )
                ),
                (
                    "Personne à charge 18 ans ou plus si applicable : "
                    + (
                        "oui"
                        if (
                            aidant_30425_federal
                            .personne_charge_18_ans_ou_plus_si_applicable
                        )
                        else "non"
                    )
                ),
                (
                    "Infirmité physique ou mentale : "
                    + (
                        "confirmée"
                        if aidant_30425_federal.infirmite_physique_ou_mentale
                        else "non confirmée"
                    )
                ),
                (
                    "Dépendance due uniquement à l'infirmité : "
                    + (
                        "oui"
                        if (
                            aidant_30425_federal
                            .dependance_due_uniquement_a_infirmite
                        )
                        else "non"
                    )
                ),
                (
                    "Dépendance pendant une période considérable : "
                    + (
                        "oui"
                        if aidant_30425_federal.dependance_periode_considerable
                        else "non"
                    )
                ),
                (
                    "Base aidant naturel de 2 687 $ incluse dans "
                    "30300/30400 : "
                    + (
                        "oui"
                        if aidant_30425_federal.montant_base_2687_inclus
                        else "non"
                    )
                ),
                (
                    "Un seul réclamant ligne 30425 : "
                    + (
                        "oui"
                        if aidant_30425_federal.un_seul_reclamant_30425
                        else "non"
                    )
                ),
                (
                    "Aucune réclamation partagée : "
                    + (
                        "oui"
                        if aidant_30425_federal.aucune_reclamation_partagee
                        else "non"
                    )
                ),
                (
                    "Preuve médicale admissible ou T2201 approuvé : "
                    + (
                        "confirmée"
                        if (
                            aidant_30425_federal
                            .preuve_medicale_ou_t2201_confirmee
                        )
                        else "non confirmée"
                    )
                ),
                (
                    "Validation comptable : "
                    + (
                        "confirmée"
                        if aidant_30425_federal.valide_par_comptable
                        else "non confirmée"
                    )
                ),
                "Source : " + aidant_30425_federal.source_personne,
                "Ligne 34990 : garde-fou actif",
            ]
        )

    if aidant_enfant_federal.reclamer_montant:
        nombre_enfants_30499 = nombre_enfants_ligne_30499_2025(
            aidant_enfant_federal
        )
        montant_30500 = montant_ligne_30500_2025(
            aidant_enfant_federal
        )
        credit_aidant_enfant = (
            credit_federal_aidant_enfant_moins18_2025(
                aidant_enfant_federal
            )
        )

        lignes.extend(
            [
                "",
                "AIDANT NATUREL - ENFANT DE MOINS DE 18 ANS - FÉDÉRAL 2025",
                (
                    "Nombre d'enfants - ligne 30499 : "
                    f"{nombre_enfants_30499}"
                ),
                (
                    "Montant admissible - ligne 30500 : "
                    f"{formater_montant_estimation(montant_30500)}"
                ),
                (
                    "Crédit fédéral - ligne 30500 : "
                    f"{formater_montant_estimation(
                        credit_aidant_enfant
                    )}"
                ),
                "Taux du crédit fédéral 2025 : 14,5 %",
                "Enfant biologique ou adopté : oui",
                "Enfant de moins de 18 ans à la fin de 2025 : oui",
                "Infirmité physique ou mentale confirmée : oui",
                (
                    "Dépendance longue, continue et de durée "
                    "indéterminée : oui"
                ),
                (
                    "Besoin de beaucoup plus d'aide que les enfants "
                    "du même âge : oui"
                ),
                "Enfant avec ses deux parents toute l'année 2025 : oui",
                "Aucune garde partagée : oui",
                "Aucune pension alimentaire : oui",
                "Aucun autre réclamant ligne 30500 : oui",
                "Aucun transfert au conjoint - ligne 32600 : oui",
                (
                    "Preuve médicale admissible ou T2201 approuvé : "
                    "confirmée"
                ),
                "Validation comptable : confirmée",
                f"Source : {aidant_enfant_federal.source_enfant}",
                (
                    "Ligne 34990 : garde-fou actif pour les profils "
                    "au-delà de la première tranche fédérale."
                ),
                (
                    "Combinaison ligne 30400 + ligne 30500 : "
                    "non supportée dans ce profil simple."
                ),
            ]
        )

    if personne_charge_admissible_federale.reclamer_montant:
        montant_30400 = montant_ligne_30400_2025(
            personne_charge_admissible_federale
        )
        credit_personne_charge_federal = (
            credit_federal_personne_charge_admissible_2025(
                personne_charge_admissible_federale
            )
        )

        lignes.extend(
            [
                "",
                "PERSONNE À CHARGE ADMISSIBLE - FÉDÉRAL 2025",
                (
                    "Revenu net du contribuable - ligne 23600 : "
                    f"{formater_montant_estimation(
                        personne_charge_admissible_federale
                        .revenu_net_contribuable_ligne_23600
                    )}"
                ),
                (
                    "Revenu net de la personne à charge : "
                    f"{formater_montant_estimation(
                        personne_charge_admissible_federale
                        .revenu_net_personne_charge_2025
                    )}"
                ),
                (
                    "Montant admissible - ligne 30400 : "
                    f"{formater_montant_estimation(
                        montant_30400
                    )}"
                ),
                (
                    "Crédit fédéral - ligne 30400 : "
                    f"{formater_montant_estimation(
                        credit_personne_charge_federal
                    )}"
                ),
                "Taux du crédit fédéral 2025 : 14,5 %",
                "Contribuable résident du Canada toute l'année 2025 : oui",
                "Aucun époux/conjoint pendant toute l'année 2025 : oui",
                "Personne à charge = enfant du contribuable : oui",
                "Enfant de moins de 18 ans à la fin de 2025 : oui",
                "Aucune déficience de l'enfant : oui",
                "Enfant soutenu par le contribuable en 2025 : oui",
                "Enfant ayant vécu avec le contribuable : oui",
                "Habitation maintenue par le contribuable : oui",
                "Enfant résident du Canada toute l'année 2025 : oui",
                "Aucune garde partagée : oui",
                "Aucune pension alimentaire : oui",
                "Un seul montant ligne 30400 par ménage : oui",
                "Aucun autre réclamant ligne 30400 : oui",
                "Revenu net de la personne à charge confirmé : oui",
                "Validation comptable : confirmée",
                (
                    "Source : "
                    f"{personne_charge_admissible_federale.source_personne_charge}"
                ),
                (
                    "Ligne 34990 : garde-fou actif pour les profils "
                    "au-delà de la première tranche fédérale."
                ),
            ]
        )

    if montant_conjoint_federal.reclamer_montant:
        montant_30300 = montant_ligne_30300_2025(
            montant_conjoint_federal
        )
        credit_conjoint_federal = (
            credit_federal_montant_conjoint_2025(
                montant_conjoint_federal
            )
        )

        lignes.extend(
            [
                "",
                "ÉPOUX / CONJOINT DE FAIT - FÉDÉRAL 2025",
                (
                    "Revenu net du contribuable - ligne 23600 : "
                    f"{formater_montant_estimation(
                        montant_conjoint_federal
                        .revenu_net_contribuable_ligne_23600
                    )}"
                ),
                (
                    "Revenu net du conjoint : "
                    f"{formater_montant_estimation(
                        montant_conjoint_federal
                        .revenu_net_conjoint_2025
                    )}"
                ),
                (
                    "Montant admissible - ligne 30300 : "
                    f"{formater_montant_estimation(
                        montant_30300
                    )}"
                ),
                (
                    "Crédit fédéral - ligne 30300 : "
                    f"{formater_montant_estimation(
                        credit_conjoint_federal
                    )}"
                ),
                "Taux du crédit fédéral 2025 : 14,5 %",
                "Contribuable résident du Canada toute l'année : oui",
                "Relation époux/conjoint de fait confirmée : oui",
                "Conjoint soutenu en 2025 : oui",
                "Même conjoint toute l'année 2025 : oui",
                "Aucune séparation/réconciliation en 2025 : oui",
                "Conjoint résident du Canada toute l'année : oui",
                "Aucune pension alimentaire liée à une séparation : oui",
                "Aucune déficience du conjoint : oui",
                "Un seul conjoint réclame le montant : oui",
                "Revenu net du conjoint confirmé : oui",
                "Validation comptable : confirmée",
                f"Source : {montant_conjoint_federal.source_conjoint}",
                (
                    "Ligne 34990 : garde-fou actif pour les profils "
                    "au-delà de la première tranche fédérale."
                ),
            ]
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
        credit_age_pension_federal = (
            credit_federal_age_pension_2025(
                credits_federaux_age_pension
            )
        )

        lignes.extend(
            [
                "",
                "ÂGE / PENSION - FÉDÉRAL 2025",
                (
                    "Revenu net fédéral - ligne 23600 : "
                    f"{formater_montant_estimation(
                        credits_federaux_age_pension
                        .revenu_net_ligne_23600
                    )}"
                ),
                (
                    "Montant en raison de l'âge - ligne 30100 : "
                    f"{formater_montant_estimation(
                        montant_age_federal
                    )}"
                ),
                (
                    "Montant pour revenu de pension - ligne 31400 : "
                    f"{formater_montant_estimation(
                        montant_pension_federal
                    )}"
                ),
                (
                    "Crédit fédéral âge / pension : "
                    f"{formater_montant_estimation(
                        credit_age_pension_federal
                    )}"
                ),
                "Taux du crédit fédéral 2025 : 14,5 %",
                (
                    "65 ans ou plus au 31 décembre 2025 : "
                    + (
                        "oui"
                        if (
                            credits_federaux_age_pension
                            .age_65_plus_31_decembre_2025
                        )
                        else "non"
                    )
                ),
                (
                    "Résident du Canada toute l'année 2025 : "
                    + (
                        "oui"
                        if (
                            credits_federaux_age_pension
                            .resident_canada_toute_annee
                        )
                        else "non"
                    )
                ),
                (
                    "Aucune règle spéciale décès : "
                    + (
                        "oui"
                        if (
                            credits_federaux_age_pension
                            .aucune_regle_deces
                        )
                        else "non"
                    )
                ),
                (
                    "Aucun fractionnement de pension T1032 : "
                    + (
                        "oui"
                        if (
                            credits_federaux_age_pension
                            .aucun_fractionnement_pension
                        )
                        else "non"
                    )
                ),
                (
                    "Aucun transfert entre conjoints : "
                    + (
                        "oui"
                        if (
                            credits_federaux_age_pension
                            .aucun_transfert_conjoint
                        )
                        else "non"
                    )
                ),
                (
                    "Validation comptable : "
                    + (
                        "confirmée"
                        if (
                            credits_federaux_age_pension
                            .valide_par_comptable
                        )
                        else "non confirmée"
                    )
                ),
            ]
        )

        if credits_federaux_age_pension.reclamer_montant_age:
            lignes.append(
                "Source âge : "
                f"{credits_federaux_age_pension.source_age}"
            )
        else:
            lignes.append("Ligne 30100 non réclamée")

        if credits_federaux_age_pension.reclamer_montant_pension:
            lignes.extend(
                [
                    (
                        "Revenu de pension admissible confirmé : "
                        + (
                            "oui"
                            if (
                                credits_federaux_age_pension
                                .revenu_pension_admissible_confirme
                            )
                            else "non"
                        )
                    ),
                    (
                        "Source pension : "
                        f"{credits_federaux_age_pension.source_pension}"
                    ),
                ]
            )
        else:
            lignes.append("Ligne 31400 non réclamée")

        lignes.append(
            "Ligne 34990 : garde-fou actif; calcul automatique "
            "limité au profil simple actuellement supporté."
        )

    if (
        montants_age_retraite.reclamer_age
        or montants_age_retraite.reclamer_revenus_retraite
    ):
        montant_age = montant_age_2025(
            montants_age_retraite
        )
        revenu_retraite_net = (
            revenu_retraite_net_admissible_2025(
                montants_age_retraite
            )
        )
        montant_retraite = montant_revenus_retraite_2025(
            montants_age_retraite
        )
        reduction_age_retraite = (
            reduction_annexe_b_age_retraite_2025(
                montants_age_retraite
            )
        )
        montant_ligne_361_age_retraite = (
            montant_ligne_361_age_retraite_2025(
                montants_age_retraite
            )
        )
        credit_age_retraite = (
            credit_quebec_age_retraite_2025(
                montants_age_retraite
            )
        )

        lignes.extend(
            [
                "",
                "ÂGE / REVENUS DE RETRAITE - QUÉBEC 2025",
                (
                    "Revenu familial net : "
                    f"{formater_montant_estimation(
                        montants_age_retraite.revenu_familial_net
                    )}"
                ),
                (
                    "Montant en raison de l'âge : "
                    f"{formater_montant_estimation(montant_age)}"
                ),
                (
                    "Revenu ligne 122 : "
                    f"{formater_montant_estimation(
                        montants_age_retraite.revenu_ligne_122
                    )}"
                ),
                (
                    "Revenu ligne 123 : "
                    f"{formater_montant_estimation(
                        montants_age_retraite.revenu_ligne_123
                    )}"
                ),
                (
                    "Revenu retraite net admissible : "
                    f"{formater_montant_estimation(
                        revenu_retraite_net
                    )}"
                ),
                (
                    "Montant pour revenus de retraite : "
                    f"{formater_montant_estimation(
                        montant_retraite
                    )}"
                ),
                "Coefficient revenus de retraite : 1,25",
                (
                    "Maximum revenus de retraite : "
                    f"{formater_montant_estimation(
                        MONTANT_REVENUS_RETRAITE_MAX_2025
                    )}"
                ),
                (
                    "Seuil de réduction : "
                    f"{formater_montant_estimation(
                        SEUIL_REDUCTION_ANNEXE_B_2025
                    )}"
                ),
                "Taux de réduction : 18,75 %",
                (
                    "Réduction annexe B : "
                    f"{formater_montant_estimation(
                        reduction_age_retraite
                    )}"
                ),
                (
                    "Annexe B / ligne 361 : "
                    f"{formater_montant_estimation(
                        montant_ligne_361_age_retraite
                    )}"
                ),
                (
                    "Crédit Québec : "
                    f"{formater_montant_estimation(
                        credit_age_retraite
                    )}"
                ),
                "Taux du crédit Québec : 14 %",
                (
                    "Transfert ligne 245 : "
                    f"{formater_montant_estimation(
                        montants_age_retraite
                        .transfert_revenus_retraite_ligne_245
                    )}"
                ),
                (
                    "Sans conjoint au 31 décembre 2025 : "
                    + (
                        "oui"
                        if (
                            montants_age_retraite
                            .aucun_conjoint_31_decembre_2025
                        )
                        else "non"
                    )
                ),
                (
                    "Résident Québec/Canada toute l'année : "
                    + (
                        "oui"
                        if (
                            montants_age_retraite
                            .resident_quebec_canada_toute_annee
                        )
                        else "non"
                    )
                ),
                (
                    "Aucun montant personne vivant seule combiné : "
                    + (
                        "oui"
                        if (
                            montants_age_retraite
                            .aucun_montant_personne_vivant_seule
                        )
                        else "non"
                    )
                ),
                (
                    "Revenus de retraite admissibles confirmés : "
                    + (
                        "oui"
                        if (
                            montants_age_retraite
                            .revenus_retraite_admissibles_confirmes
                        )
                        else "non"
                    )
                ),
                (
                    "PSV, RRQ et RPC exclus : "
                    + (
                        "oui"
                        if (
                            montants_age_retraite
                            .revenus_non_admissibles_exclus
                        )
                        else "non"
                    )
                ),
                (
                    "Validation comptable : "
                    + (
                        "confirmée"
                        if montants_age_retraite.valide_par_comptable
                        else "non confirmée"
                    )
                ),
            ]
        )

        if montants_age_retraite.reclamer_age:
            lignes.append(
                f"Source âge : {montants_age_retraite.source_age}"
            )

        if montants_age_retraite.reclamer_revenus_retraite:
            lignes.append(
                "Source retraite : "
                f"{montants_age_retraite.source_retraite}"
            )

    if personne_vivant_seule.reclamer_montant:
        montant_ligne_361 = (
            montant_ligne_361_personne_vivant_seule_2025(
                personne_vivant_seule
            )
        )
        credit_personne_seule = (
            credit_quebec_personne_vivant_seule_2025(
                personne_vivant_seule
            )
        )

        lignes.extend(
            [
                "",
                "PERSONNE VIVANT SEULE — QUÉBEC 2025",
                (
                    "Revenu familial net : "
                    f"{formater_montant_estimation(
                        personne_vivant_seule.revenu_familial_net
                    )}"
                ),
                (
                    "Montant de base : "
                    f"{formater_montant_estimation(
                        MONTANT_PERSONNE_VIVANT_SEULE_2025
                    )}"
                ),
                (
                    "Seuil de réduction : "
                    f"{formater_montant_estimation(
                        SEUIL_REDUCTION_ANNEXE_B_2025
                    )}"
                ),
                "Taux de réduction : 18,75 %",
                (
                    "Annexe B / ligne 361 : "
                    f"{formater_montant_estimation(
                        montant_ligne_361
                    )}"
                ),
                (
                    "Crédit Québec : "
                    f"{formater_montant_estimation(
                        credit_personne_seule
                    )}"
                ),
                "Taux du crédit Québec : 14 %",
                (
                    "Additionnel monoparental réclamé : "
                    + (
                        "oui"
                        if (
                            personne_vivant_seule
                            .reclamer_additionnel_monoparental
                        )
                        else "non"
                    )
                ),
                (
                    "Mois d'Allocation famille reçus en 2025 : "
                    f"{personne_vivant_seule.mois_allocation_famille_2025}"
                ),
                (
                    "Sans conjoint au 31 décembre 2025 : "
                    + (
                        "oui"
                        if (
                            personne_vivant_seule
                            .aucun_conjoint_31_decembre_2025
                        )
                        else "non"
                    )
                ),
                (
                    "Résident Québec/Canada toute l'année : "
                    + (
                        "oui"
                        if (
                            personne_vivant_seule
                            .resident_quebec_canada_toute_annee
                        )
                        else "non"
                    )
                ),
                (
                    "Habitation maintenue toute l'année : "
                    + (
                        "oui"
                        if (
                            personne_vivant_seule
                            .habitation_maintenue_par_contribuable
                        )
                        else "non"
                    )
                ),
                (
                    "Personnes autorisées dans l'habitation seulement : "
                    + (
                        "oui"
                        if (
                            personne_vivant_seule
                            .seulement_personnes_autorisees_dans_habitation
                        )
                        else "non"
                    )
                ),
                (
                    "Aucun montant âge/retraite combiné : "
                    + (
                        "oui"
                        if personne_vivant_seule.aucun_montant_age_ou_retraite
                        else "non"
                    )
                ),
                (
                    "Documents justificatifs confirmés : "
                    + (
                        "oui"
                        if (
                            personne_vivant_seule
                            .documents_justificatifs_confirmes
                        )
                        else "non"
                    )
                ),
                (
                    "Validation comptable : "
                    + (
                        "confirmée"
                        if personne_vivant_seule.valide_par_comptable
                        else "non confirmée"
                    )
                ),
                f"Source : {personne_vivant_seule.source}",
            ]
        )

    if assurance_medicaments.type_couverture.strip():
        type_couverture = (
            assurance_medicaments.type_couverture.strip().lower()
        )
        type_affiche = (
            "Régime public"
            if type_couverture == "public"
            else "Couverture collective"
        )
        code_449 = code_exemption_case_449_2025(
            assurance_medicaments
        )

        lignes.extend(
            [
                "",
                "ASSURANCE MÉDICAMENTS QUÉBEC VALIDÉE",
                f"Type de couverture : {type_affiche}",
                (
                    "Revenu net Québec — ligne 275 : "
                    f"{formater_montant_estimation(
                        assurance_medicaments.revenu_ligne_275
                    )}"
                ),
                (
                    "Annexe K — ligne 48 : "
                    f"{formater_montant_estimation(
                        assurance_medicaments.revenu_ligne_48_annexe_k
                    )}"
                ),
                (
                    "Cotisation Québec — ligne 447 : "
                    f"{formater_montant_estimation(
                        x.cotisation_assurance_medicaments
                    )}"
                ),
                *(
                    [
                        f"Case 449 — code : {code_449}",
                    ]
                    if code_449
                    else []
                ),
                f"Source : {assurance_medicaments.source}",
                (
                    "Couverture toute l'année 2025 : "
                    + (
                        "oui"
                        if assurance_medicaments.couverture_toute_annee
                        else "non"
                    )
                ),
                (
                    "Sans conjoint au 31 décembre 2025 : "
                    + (
                        "oui"
                        if (
                            assurance_medicaments
                            .sans_conjoint_31_decembre_2025
                        )
                        else "non"
                    )
                ),
                (
                    "Aucun mois d'exemption : "
                    + (
                        "oui"
                        if assurance_medicaments.aucun_mois_exempt
                        else "non"
                    )
                ),
                (
                    "Carte RAMQ 2025 confirmée : "
                    + (
                        "oui"
                        if assurance_medicaments.carte_ramq_valide_2025
                        else "non"
                    )
                ),
                (
                    "Situation validée par le comptable : "
                    + (
                        "oui"
                        if (
                            assurance_medicaments
                            .situation_validee_par_comptable
                        )
                        else "non"
                    )
                ),
                (
                    "Aucun cas particulier de l'annexe K : "
                    + (
                        "oui"
                        if assurance_medicaments.aucun_cas_particulier
                        else "non"
                    )
                ),
            ]
        )

    if cotisations_excedentaires.source.strip():
        lignes.extend(
            [
                "",
                "COTISATIONS EXCÉDENTAIRES VALIDÉES",
                (
                    "RRQ B.A payé : "
                    f"{formater_montant_estimation(
                        cotisations_excedentaires.rrq_ba
                    )}"
                ),
                (
                    "RRQ B.B payé : "
                    f"{formater_montant_estimation(
                        cotisations_excedentaires.rrq_bb
                    )}"
                ),
                (
                    "Gains admissibles RRQ : "
                    f"{formater_montant_estimation(
                        cotisations_excedentaires.gains_admissibles_rrq
                    )}"
                ),
                (
                    "Remboursement RRQ — ligne Québec 452 : "
                    f"{formater_montant_estimation(
                        x.remboursement_rrq_excedentaire
                    )}"
                ),
                (
                    "Assurance-emploi payée : "
                    f"{formater_montant_estimation(
                        cotisations_excedentaires.assurance_emploi
                    )}"
                ),
                (
                    "Gains assurables AE : "
                    f"{formater_montant_estimation(
                        cotisations_excedentaires.gains_assurables_ae
                    )}"
                ),
                (
                    "Remboursement assurance-emploi — ligne fédérale "
                    "45000 : "
                    f"{formater_montant_estimation(
                        x.remboursement_ae_excedentaire
                    )}"
                ),
                (
                    "RQAP payé : "
                    f"{formater_montant_estimation(
                        cotisations_excedentaires.rqap
                    )}"
                ),
                (
                    "Revenus assujettis RQAP : "
                    f"{formater_montant_estimation(
                        cotisations_excedentaires.revenus_assujettis_rqap
                    )}"
                ),
                (
                    "Remboursement RQAP — ligne Québec 457 : "
                    f"{formater_montant_estimation(
                        x.remboursement_rqap_excedentaire
                    )}"
                ),
                (
                    "Total remboursable RRQ / AE / RQAP : "
                    f"{formater_montant_estimation(
                        x.remboursements_cotisations_totaux
                    )}"
                ),
                f"Source : {cotisations_excedentaires.source}",
                (
                    "Situation validée par le comptable : "
                    + (
                        "oui"
                        if cotisations_excedentaires.valide_par_comptable
                        else "non"
                    )
                ),
                (
                    "Résident du Québec au 31 décembre 2025 : "
                    + (
                        "oui"
                        if (
                            cotisations_excedentaires
                            .resident_quebec_31_decembre_2025
                        )
                        else "non"
                    )
                ),
                (
                    "Emplois exercés au Québec uniquement : "
                    + (
                        "oui"
                        if cotisations_excedentaires.emploi_quebec_uniquement
                        else "non"
                    )
                ),
                (
                    "RRQ uniquement, sans RPC : "
                    + (
                        "oui"
                        if cotisations_excedentaires.rrq_uniquement_sans_rpc
                        else "non"
                    )
                ),
                (
                    "Aucun travail autonome : "
                    + (
                        "oui"
                        if cotisations_excedentaires.aucun_travail_autonome
                        else "non"
                    )
                ),
                (
                    "Profil RRQ standard 18 à 64 ans : "
                    + (
                        "oui"
                        if (
                            cotisations_excedentaires
                            .profil_rrq_standard_18_64
                        )
                        else "non"
                    )
                ),
                (
                    "Aucun cas particulier d'assurance-emploi : "
                    + (
                        "oui"
                        if cotisations_excedentaires.aucun_cas_particulier_ae
                        else "non"
                    )
                ),
                (
                    "Aucun cas particulier du RQAP : "
                    + (
                        "oui"
                        if (
                            cotisations_excedentaires
                            .aucun_cas_particulier_rqap
                        )
                        else "non"
                    )
                ),
                (
                    "Calcul standard RRQ / AE / RQAP confirmé : "
                    + (
                        "oui"
                        if cotisations_excedentaires.calcul_standard_confirme
                        else "non"
                    )
                ),
            ]
        )

    lignes.extend(
        [
            "",
            "FÉDÉRAL",
            (
                "Impôt fédéral brut : "
                f"{formater_montant_estimation(f.impot_brut)}"
            ),
            (
                "Crédits non remboursables : "
                f"{formater_montant_estimation(
                    f.credits_non_remboursables
                )}"
            ),
            (
                "Impôt fédéral de base : "
                f"{formater_montant_estimation(
                    x.impot_federal_de_base
                )}"
            ),
            (
                "Abattement Québec (16,5 %) : -"
                f"{formater_montant_estimation(x.abattement_quebec)}"
            ),
            (
                "Impôt fédéral après abattement : "
                f"{formater_montant_estimation(
                    x.impot_federal_apres_abattement
                )}"
            ),
            "",
            "QUÉBEC",
            (
                "Impôt Québec brut : "
                f"{formater_montant_estimation(q.impot_brut)}"
            ),
            (
                "Crédit personnel de base : -"
                f"{formater_montant_estimation(
                    q.credit_personnel_base
                )}"
            ),
            (
                "Impôt Québec préliminaire : "
                f"{formater_montant_estimation(
                    x.impot_quebec_preliminaire
                )}"
            ),
            "",
            "RAPPROCHEMENT",
            (
                "Impôt total préliminaire : "
                f"{formater_montant_estimation(
                    x.impot_total_preliminaire
                )}"
            ),
            (
                ("Retenue fédérale T4 + T4E : " if estimation.prestations_rqap.present or estimation.prestations_ae.present else ("Retenue fédérale T4 + T4A(P) : " if estimation.base.nombre_t4 else "Retenue fédérale T4A(P) : ") if estimation.prestations_rrq_rpc.present else ("Retenue fédérale " + ("T4 + " if estimation.base.nombre_t4 else "") + "T4A(OAS) : ") if estimation.prestations_psv.present else "Retenues fédérales emploi et pensions : " if estimation.pensions.present else "Retenues fédérales emploi et retraits : " if estimation.retraits.present else "Retenue fédérale T4 : ") +
                f"{formater_montant_estimation(x.retenue_federale)}"
            ),
            (
                ("Retenue Québec RL-1 + RL-6 : " if estimation.prestations_rqap.present else "Retenue Québec RL-1 + T4E : " if estimation.prestations_ae.present else ("Retenue Québec " + ("RL-1 + " if estimation.base.nombre_rl1 else "") + ("RL-2 : " if estimation.prestations_rrq_rpc.releve_2_present else "(aucun RL-2 reçu) : ")) if estimation.prestations_rrq_rpc.present else ("Retenue Québec " + ("RL-1 + " if estimation.base.nombre_rl1 else "") + "T4A(OAS) : ") if estimation.prestations_psv.present else "Retenues Québec emploi et pensions : " if estimation.pensions.present else "Retenues Québec emploi et retraits : " if estimation.retraits.present else "Retenue Québec RL-1 : ") +
                f"{formater_montant_estimation(x.retenue_quebec)}"
            ),
            (
                "Retenues totales : "
                f"{formater_montant_estimation(x.retenues_totales)}"
            ),
            "",
            f"RÉSULTAT : {x.resultat}",
            f"Montant : {formater_montant_estimation(montant)}",
            "",
            f"Statut : {x.statut}",
            "",
            "LIMITATIONS ACTUELLES",
        ]
    )

    lignes.extend(f"- {item}" for item in x.limitations)
    lignes.extend(
        [
            "",
            "Aucune donnée n'a quitté l'ordinateur.",
            (
                "Aucune déclaration n'a été transmise à l'ARC "
                "ou à Revenu Québec."
            ),
        ]
    )
    return lignes


def exporter_rapport_fiscal_pdf_2025(
    estimation: EstimationFiscale2025,
    destination: str | Path,
) -> Path:
    chemin = Path(destination)
    if chemin.suffix.lower() != ".pdf":
        chemin = chemin.with_suffix(".pdf")
    chemin.parent.mkdir(parents=True, exist_ok=True)

    doc = fitz.open()
    try:
        page = doc.new_page()
        y = 55
        for ligne in _lignes(estimation):
            morceaux = textwrap.wrap(
                ligne,
                width=92,
                break_long_words=False,
            ) or [""]
            for morceau in morceaux:
                if y > 750:
                    page = doc.new_page()
                    y = 55
                page.insert_text(
                    (48, y),
                    morceau,
                    fontsize=10,
                    fontname="helv",
                )
                y += 15
            if not ligne:
                y += 4

        doc.set_metadata(
            {
                "title": (
                    "Estimation fiscale 2025 - "
                    f"{estimation.dossier.client}"
                ),
                "author": "ComptaPrivée AI",
                "subject": (
                    "Estimation locale - "
                    "validation comptable obligatoire"
                ),
            }
        )
        doc.save(chemin, garbage=3, deflate=True)
    finally:
        doc.close()

    return chemin


def exporter_fractionnement_pdf_2025(resultat, destination):
    """Rapport commun des deux déclarations; données exclusivement locales."""
    from .tax_pension_splitting_2025 import lignes_fractionnement_2025
    from .tax_calculation_trace_2025 import construire_trace_fractionnement_2025
    chemin=Path(destination).with_suffix('.pdf')
    chemin.parent.mkdir(parents=True,exist_ok=True)
    with fitz.open() as doc:
        page=doc.new_page();y=55
        lignes=lignes_fractionnement_2025(resultat)+['','TRACE DU CHOIX CONJOINT']+list(construire_trace_fractionnement_2025(resultat))
        for ligne in lignes:
            for morceau in textwrap.wrap(ligne,width=88,break_long_words=True) or ['']:
                if y>750:page=doc.new_page();y=55
                page.insert_text((48,y),morceau,fontsize=10,fontname='helv');y+=15
        doc.set_metadata({'title':'Fractionnement de pension 2025 - estimation du couple','author':'ComptaPrivée AI'})
        doc.save(chemin,garbage=3,deflate=True)
    return chemin
