"""Pension alimentaire payée simple 2025 — Bloc 4E.

Périmètre initial :
- payeur d'une pension périodique à un époux/conjoint de fait actuel ou ancien;
- ordonnance d'un tribunal ou entente écrite;
- bénéficiaire et payeur vivant séparés au moment du paiement;
- montant total fédéral ligne 21999 déjà établi;
- partie déductible fédérale ligne 22000 déjà établie;
- montant déductible Québec ligne 225 déjà établi;
- ordonnance/entente enregistrée auprès de l'ARC lorsque requis;
- validation comptable et sources conservées localement.

Sont explicitement hors périmètre :
- pension alimentaire pour enfant;
- ordonnances/ententes antérieures à mai 1997 ou choix T1157;
- arrérages, paiements rétroactifs ou forfaitaires;
- remboursement de pension alimentaire;
- frais juridiques ou comptables;
- plusieurs bénéficiaires;
- année de séparation avec arbitrage entre déduction et crédits personnels;
- situations où les lignes 30300/30400/30425/30450/30500 interagissent
  avec le bénéficiaire ou la personne visée.
"""

from dataclasses import dataclass, replace
from decimal import Decimal

from .tax_income_2025 import RevenuNetImposable2025
from .tax_rules_2025 import arrondir_cent

ZERO = Decimal("0")


@dataclass(frozen=True)
class PensionAlimentairePayee2025:
    total_paye_federal_21999: Decimal = ZERO
    deduction_federale_22000: Decimal = ZERO
    deduction_quebec_225: Decimal = ZERO
    source_federale: str = ""
    source_quebec: str = ""
    valide_par_comptable: bool = False
    ordonnance_ou_entente_ecrite_confirmee: bool = False
    paiement_periodique_conjoint_ex_conjoint_confirme: bool = False
    vie_separee_au_moment_paiement_confirmee: bool = False
    enregistrement_arc_confirme: bool = False
    montant_federal_confirme: bool = False
    montant_quebec_confirme: bool = False
    aucun_credit_personnel_lie_confirme: bool = False
    pension_enfant: bool = False
    regime_avant_mai_1997_ou_t1157: bool = False
    arrerages_ou_retroactif: bool = False
    paiement_forfaitaire: bool = False
    remboursement_pension: bool = False
    frais_juridiques_ou_comptables: bool = False
    plusieurs_beneficiaires: bool = False
    annee_changement_etat_civil_avec_choix_credit: bool = False


def _montant_fini_non_negatif(valeur: Decimal, libelle: str) -> Decimal:
    if not valeur.is_finite():
        raise ValueError(f"{libelle} doit être un nombre fini.")
    if valeur < ZERO:
        raise ValueError(f"{libelle} ne peut pas être négatif.")
    return arrondir_cent(valeur)


def valider_pension_alimentaire_payee_2025(
    profil: PensionAlimentairePayee2025,
) -> PensionAlimentairePayee2025:
    total = _montant_fini_non_negatif(
        profil.total_paye_federal_21999,
        "Le total payé fédéral ligne 21999",
    )
    federal = _montant_fini_non_negatif(
        profil.deduction_federale_22000,
        "La déduction fédérale ligne 22000",
    )
    quebec = _montant_fini_non_negatif(
        profil.deduction_quebec_225,
        "La déduction Québec ligne 225",
    )

    profil = replace(
        profil,
        total_paye_federal_21999=total,
        deduction_federale_22000=federal,
        deduction_quebec_225=quebec,
        source_federale=profil.source_federale.strip(),
        source_quebec=profil.source_quebec.strip(),
    )

    if federal > total:
        raise ValueError(
            "La déduction fédérale ligne 22000 ne peut pas dépasser "
            "le total payé ligne 21999."
        )

    if total == ZERO and federal == ZERO and quebec == ZERO:
        return profil

    if any(
        (
            profil.pension_enfant,
            profil.regime_avant_mai_1997_ou_t1157,
            profil.arrerages_ou_retroactif,
            profil.paiement_forfaitaire,
            profil.remboursement_pension,
            profil.frais_juridiques_ou_comptables,
            profil.plusieurs_beneficiaires,
            profil.annee_changement_etat_civil_avec_choix_credit,
        )
    ):
        raise ValueError(
            "La situation indiquée est hors périmètre 4E simple et nécessite "
            "un traitement avancé des pensions alimentaires."
        )

    confirmations = (
        (
            profil.valide_par_comptable,
            "La pension alimentaire doit être validée par le comptable.",
        ),
        (
            profil.ordonnance_ou_entente_ecrite_confirmee,
            "Une ordonnance d'un tribunal ou une entente écrite doit être confirmée.",
        ),
        (
            profil.paiement_periodique_conjoint_ex_conjoint_confirme,
            "Le Bloc 4E simple exige une pension périodique versée à un "
            "époux/conjoint de fait actuel ou ancien.",
        ),
        (
            profil.vie_separee_au_moment_paiement_confirmee,
            "Le payeur et le bénéficiaire doivent être confirmés comme vivant "
            "séparés au moment du paiement.",
        ),
        (
            profil.aucun_credit_personnel_lie_confirme,
            "L'absence d'interaction avec les crédits personnels fédéraux "
            "liés au bénéficiaire doit être confirmée.",
        ),
    )
    for condition, message in confirmations:
        if not condition:
            raise ValueError(message)

    if federal > ZERO or total > ZERO:
        if not profil.enregistrement_arc_confirme:
            raise ValueError(
                "L'enregistrement de l'ordonnance ou de l'entente auprès "
                "de l'ARC doit être confirmé."
            )
        if not profil.montant_federal_confirme:
            raise ValueError(
                "Les lignes fédérales 21999/22000 doivent être confirmées."
            )
        if not profil.source_federale:
            raise ValueError(
                "La source fédérale des lignes 21999/22000 est obligatoire."
            )

    if quebec > ZERO:
        if not profil.montant_quebec_confirme:
            raise ValueError(
                "La ligne Québec 225 doit être confirmée."
            )
        if not profil.source_quebec:
            raise ValueError(
                "La source Québec de la ligne 225 est obligatoire."
            )

    return profil


def appliquer_pension_alimentaire_payee_2025(
    revenu: RevenuNetImposable2025,
    profil: PensionAlimentairePayee2025,
) -> RevenuNetImposable2025:
    if revenu.annee_fiscale != 2025:
        raise ValueError(
            "La pension alimentaire actuelle accepte uniquement l'année 2025."
        )

    profil = valider_pension_alimentaire_payee_2025(profil)
    federal = profil.deduction_federale_22000
    quebec = profil.deduction_quebec_225

    if (
        profil.total_paye_federal_21999 == ZERO
        and federal == ZERO
        and quebec == ZERO
    ):
        return revenu

    limitations = tuple(
        texte
        for texte in revenu.limitations
        if texte != "Aucune autre déduction de revenu net ou imposable."
    ) + (
        "Pension alimentaire payée simple — lignes fédérales 21999/22000 incluse.",
        "Pension alimentaire payée simple — ligne Québec 225 incluse.",
        "Pension pour enfant, anciens régimes, arrérages et interactions "
        "avec crédits personnels hors périmètre 4E.",
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
        profil=revenu.profil + " + pension alimentaire payée 4E",
        limitations=limitations,
    )


def lignes_resume_pension_alimentaire_payee_2025(
    profil: PensionAlimentairePayee2025,
) -> list[str]:
    profil = valider_pension_alimentaire_payee_2025(profil)
    if (
        profil.total_paye_federal_21999 == ZERO
        and profil.deduction_federale_22000 == ZERO
        and profil.deduction_quebec_225 == ZERO
    ):
        return []

    lignes = ["", "PENSION ALIMENTAIRE PAYÉE 2025 VALIDÉE — BLOC 4E"]

    if profil.total_paye_federal_21999 > ZERO:
        lignes.append(
            "Total payé fédéral — ligne 21999 : "
            f"{profil.total_paye_federal_21999:.2f} $"
        )

    if profil.deduction_federale_22000 > ZERO:
        lignes.extend(
            [
                "Déduction fédérale — ligne 22000 : "
                f"{profil.deduction_federale_22000:.2f} $",
                f"Source fédérale : {profil.source_federale}",
            ]
        )

    if profil.deduction_quebec_225 > ZERO:
        lignes.extend(
            [
                "Déduction Québec — ligne 225 : "
                f"{profil.deduction_quebec_225:.2f} $",
                f"Source Québec : {profil.source_quebec}",
            ]
        )

    return lignes
