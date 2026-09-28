"""Autres déductions simples 2025 — Bloc 4F.

Périmètre logiciel volontairement limité :
- montant fédéral ligne 23200 déjà établi et validé;
- montant Québec ligne 250, code 17 à la case 249, déjà établi et validé;
- déduction non déjà traitée par un autre bloc ComptaPrivée AI;
- nature et source documentées séparément par juridiction;
- validation comptable obligatoire.

Le moteur ne détermine pas l'admissibilité détaillée d'une catégorie.
Il applique uniquement des montants déjà établis et confirmés.

Sont explicitement hors périmètre 4F simple lorsque déjà traités ailleurs
ou lorsqu'un traitement fiscal spécialisé est requis :
- remboursements AE/RQAP;
- récupération de prestations sociales ligne 23500 / Québec 250 code 03;
- retraits REER/T3012A et déductions Québec 250 codes 04 à 06;
- frais juridiques, Québec code 08;
- remboursement de pension alimentaire, Québec code 12;
- CELIAPP déjà inclus, Québec code 13;
- soutien aux personnes handicapées, Québec code 07;
- abris fiscaux, revenu fractionné et autres calculs spécialisés;
- toute autre déduction disposant déjà d'une ligne ou d'un bloc dédié.
"""

from dataclasses import dataclass, replace
from decimal import Decimal

from .tax_income_2025 import RevenuNetImposable2025
from .tax_rules_2025 import arrondir_cent

ZERO = Decimal("0")


@dataclass(frozen=True)
class AutresDeductions2025:
    deduction_federale_23200: Decimal = ZERO
    deduction_quebec_250_code17: Decimal = ZERO
    nature_federale: str = ""
    nature_quebec: str = ""
    source_federale: str = ""
    source_quebec: str = ""
    valide_par_comptable: bool = False
    montant_federal_deja_etabli_confirme: bool = False
    montant_quebec_deja_etabli_confirme: bool = False
    aucune_autre_ligne_ou_bloc_applicable_confirme: bool = False
    remboursement_ae_ou_rqap: bool = False
    recuperation_prestations_sociales_23500: bool = False
    retrait_reer_ou_t3012a: bool = False
    frais_juridiques: bool = False
    remboursement_pension_alimentaire: bool = False
    transfert_ou_cotisations_inutilisees_regime: bool = False
    soutien_personne_handicapee: bool = False
    celiapp_montant_deja_inclus: bool = False
    abri_fiscal_ou_revenu_fractionne: bool = False
    autre_traitement_specialise: bool = False


def _montant_fini_non_negatif(valeur: Decimal, libelle: str) -> Decimal:
    if not valeur.is_finite():
        raise ValueError(f"{libelle} doit être un nombre fini.")
    if valeur < ZERO:
        raise ValueError(f"{libelle} ne peut pas être négatif.")
    return arrondir_cent(valeur)


def valider_autres_deductions_2025(
    profil: AutresDeductions2025,
) -> AutresDeductions2025:
    federal = _montant_fini_non_negatif(
        profil.deduction_federale_23200,
        "La déduction fédérale ligne 23200",
    )
    quebec = _montant_fini_non_negatif(
        profil.deduction_quebec_250_code17,
        "La déduction Québec ligne 250 code 17",
    )

    profil = replace(
        profil,
        deduction_federale_23200=federal,
        deduction_quebec_250_code17=quebec,
        nature_federale=profil.nature_federale.strip(),
        nature_quebec=profil.nature_quebec.strip(),
        source_federale=profil.source_federale.strip(),
        source_quebec=profil.source_quebec.strip(),
    )

    if federal == ZERO and quebec == ZERO:
        return profil

    if any(
        (
            profil.remboursement_ae_ou_rqap,
            profil.recuperation_prestations_sociales_23500,
            profil.retrait_reer_ou_t3012a,
            profil.frais_juridiques,
            profil.remboursement_pension_alimentaire,
            profil.transfert_ou_cotisations_inutilisees_regime,
            profil.soutien_personne_handicapee,
            profil.celiapp_montant_deja_inclus,
            profil.abri_fiscal_ou_revenu_fractionne,
            profil.autre_traitement_specialise,
        )
    ):
        raise ValueError(
            "La situation indiquée est hors périmètre 4F simple ou déjà "
            "traitée par un autre bloc fiscal."
        )

    if not profil.valide_par_comptable:
        raise ValueError(
            "Les autres déductions doivent être validées par le comptable."
        )

    if not profil.aucune_autre_ligne_ou_bloc_applicable_confirme:
        raise ValueError(
            "Il faut confirmer qu'aucune autre ligne ou aucun bloc dédié "
            "ne s'applique à cette déduction."
        )

    if federal > ZERO:
        if not profil.montant_federal_deja_etabli_confirme:
            raise ValueError(
                "Le montant fédéral ligne 23200 déjà établi doit être confirmé."
            )
        if not profil.nature_federale:
            raise ValueError(
                "La nature de la déduction fédérale ligne 23200 est obligatoire."
            )
        if not profil.source_federale:
            raise ValueError(
                "La source fédérale de la ligne 23200 est obligatoire."
            )

    if quebec > ZERO:
        if not profil.montant_quebec_deja_etabli_confirme:
            raise ValueError(
                "Le montant Québec ligne 250 code 17 déjà établi doit être confirmé."
            )
        if not profil.nature_quebec:
            raise ValueError(
                "La nature de la déduction Québec ligne 250 code 17 est obligatoire."
            )
        if not profil.source_quebec:
            raise ValueError(
                "La source Québec de la ligne 250 code 17 est obligatoire."
            )

    return profil


def appliquer_autres_deductions_2025(
    revenu: RevenuNetImposable2025,
    profil: AutresDeductions2025,
) -> RevenuNetImposable2025:
    if revenu.annee_fiscale != 2025:
        raise ValueError(
            "Les autres déductions actuelles acceptent uniquement l'année 2025."
        )

    profil = valider_autres_deductions_2025(profil)
    federal = profil.deduction_federale_23200
    quebec = profil.deduction_quebec_250_code17

    if federal == ZERO and quebec == ZERO:
        return revenu

    limitations = tuple(
        texte
        for texte in revenu.limitations
        if texte != "Aucune autre déduction de revenu net ou imposable."
    ) + (
        "Autres déductions simples — fédéral ligne 23200 inclus.",
        "Autres déductions simples — Québec ligne 250 code 17 inclus.",
        "Admissibilité détaillée non calculée : montants déjà établis et "
        "validés par le comptable.",
    )

    return replace(
        revenu,
        revenu_net_federal=max(
            arrondir_cent(revenu.revenu_net_federal - federal),
            ZERO,
        ),
        revenu_imposable_federal=max(
            arrondir_cent(revenu.revenu_imposable_federal - federal),
            ZERO,
        ),
        revenu_net_quebec=max(
            arrondir_cent(revenu.revenu_net_quebec - quebec),
            ZERO,
        ),
        revenu_imposable_quebec=max(
            arrondir_cent(revenu.revenu_imposable_quebec - quebec),
            ZERO,
        ),
        profil=revenu.profil + " + autres déductions 4F",
        limitations=limitations,
    )


def lignes_resume_autres_deductions_2025(
    profil: AutresDeductions2025,
) -> list[str]:
    profil = valider_autres_deductions_2025(profil)
    if (
        profil.deduction_federale_23200 == ZERO
        and profil.deduction_quebec_250_code17 == ZERO
    ):
        return []

    lignes = ["", "AUTRES DÉDUCTIONS 2025 VALIDÉES — BLOC 4F"]

    if profil.deduction_federale_23200 > ZERO:
        lignes.extend(
            [
                "Déduction fédérale — ligne 23200 : "
                f"{profil.deduction_federale_23200:.2f} $",
                f"Nature fédérale : {profil.nature_federale}",
                f"Source fédérale : {profil.source_federale}",
            ]
        )

    if profil.deduction_quebec_250_code17 > ZERO:
        lignes.extend(
            [
                "Déduction Québec — ligne 250, code 17 (case 249) : "
                f"{profil.deduction_quebec_250_code17:.2f} $",
                f"Nature Québec : {profil.nature_quebec}",
                f"Source Québec : {profil.source_quebec}",
            ]
        )

    return lignes
