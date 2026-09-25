"""Dépenses d'emploi simples 2025 — Bloc 4C.

Périmètre initial :
- employé salarié ordinaire;
- dépenses exigées par le contrat de travail et non remboursées;
- montant fédéral déjà établi sur le T777 et reporté à la ligne 22900;
- montant Québec déjà établi sur le TP-59 et reporté à la ligne 207,
  code 07;
- T2200 et TP-64.3 confirmés lorsque la juridiction correspondante
  comporte une déduction;
- aucune détermination détaillée des catégories de dépenses dans ce
  sous-bloc.

Sont explicitement hors périmètre : employé à commission, véhicule/CCA,
voyages/repas/logement, bureau à domicile, outils ou profils spécialisés.
"""

from dataclasses import dataclass, replace
from decimal import Decimal

from .tax_income_2025 import RevenuNetImposable2025
from .tax_rules_2025 import arrondir_cent

ZERO = Decimal("0")


@dataclass(frozen=True)
class DepensesEmploi2025:
    deduction_federale_t777: Decimal = ZERO
    deduction_quebec_tp59: Decimal = ZERO
    source_federale: str = ""
    source_quebec: str = ""
    valide_par_comptable: bool = False
    salarie_ordinaire_confirme: bool = False
    contrat_exige_depenses_confirme: bool = False
    non_remboursees_confirme: bool = False
    t2200_confirme: bool = False
    t777_confirme: bool = False
    tp_64_3_confirme: bool = False
    tp_59_confirme: bool = False
    employe_a_commission: bool = False
    vehicule_ou_cca: bool = False
    voyage_repas_logement: bool = False
    bureau_a_domicile: bool = False
    outils_ou_profil_specialise: bool = False


def _montant_fini_non_negatif(valeur: Decimal, libelle: str) -> Decimal:
    if not valeur.is_finite():
        raise ValueError(f"{libelle} doit être un nombre fini.")
    if valeur < ZERO:
        raise ValueError(f"{libelle} ne peut pas être négatif.")
    return arrondir_cent(valeur)


def valider_depenses_emploi_2025(profil: DepensesEmploi2025) -> DepensesEmploi2025:
    federal = _montant_fini_non_negatif(
        profil.deduction_federale_t777,
        "La déduction fédérale T777 / ligne 22900",
    )
    quebec = _montant_fini_non_negatif(
        profil.deduction_quebec_tp59,
        "La déduction Québec TP-59 / ligne 207",
    )

    profil = replace(
        profil,
        deduction_federale_t777=federal,
        deduction_quebec_tp59=quebec,
        source_federale=profil.source_federale.strip(),
        source_quebec=profil.source_quebec.strip(),
    )

    if federal == ZERO and quebec == ZERO:
        return profil

    if any(
        (
            profil.employe_a_commission,
            profil.vehicule_ou_cca,
            profil.voyage_repas_logement,
            profil.bureau_a_domicile,
            profil.outils_ou_profil_specialise,
        )
    ):
        raise ValueError(
            "La situation indiquée est hors périmètre 4C simple et "
            "nécessite un traitement des dépenses d'emploi avancé."
        )

    if not profil.valide_par_comptable:
        raise ValueError(
            "Les dépenses d'emploi doivent être validées par le comptable."
        )
    if not profil.salarie_ordinaire_confirme:
        raise ValueError(
            "Le Bloc 4C simple exige un employé salarié ordinaire."
        )
    if not profil.contrat_exige_depenses_confirme:
        raise ValueError(
            "Le contrat de travail doit exiger que le salarié acquitte "
            "les dépenses réclamées."
        )
    if not profil.non_remboursees_confirme:
        raise ValueError(
            "Les dépenses réclamées doivent être non remboursées."
        )

    if federal > ZERO:
        if not profil.t2200_confirme:
            raise ValueError(
                "Le T2200 doit être confirmé pour la déduction fédérale 4C."
            )
        if not profil.t777_confirme:
            raise ValueError(
                "Le T777 doit être confirmé pour la déduction fédérale 4C."
            )
        if not profil.source_federale:
            raise ValueError(
                "La source fédérale T2200/T777 est obligatoire."
            )

    if quebec > ZERO:
        if not profil.tp_64_3_confirme:
            raise ValueError(
                "Le TP-64.3 doit être confirmé pour la déduction Québec 4C."
            )
        if not profil.tp_59_confirme:
            raise ValueError(
                "Le TP-59 doit être confirmé pour la déduction Québec 4C."
            )
        if not profil.source_quebec:
            raise ValueError(
                "La source Québec TP-64.3/TP-59 est obligatoire."
            )

    return profil


def appliquer_depenses_emploi_2025(
    revenu: RevenuNetImposable2025,
    profil: DepensesEmploi2025,
) -> RevenuNetImposable2025:
    if revenu.annee_fiscale != 2025:
        raise ValueError(
            "Les dépenses d'emploi actuelles acceptent uniquement "
            "l'année 2025."
        )

    profil = valider_depenses_emploi_2025(profil)
    federal = profil.deduction_federale_t777
    quebec = profil.deduction_quebec_tp59

    if federal == ZERO and quebec == ZERO:
        return revenu

    limitations = tuple(
        texte
        for texte in revenu.limitations
        if texte != "Aucune autre déduction de revenu net ou imposable."
    ) + (
        "Dépenses d'emploi simples T777 / ligne 22900 incluses au fédéral.",
        "Dépenses d'emploi simples TP-59 / ligne 207 code 07 incluses au Québec.",
        "Commission, véhicule/CCA, voyages, bureau à domicile et profils spécialisés hors périmètre 4C.",
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
        profil=revenu.profil + " + dépenses d'emploi 4C",
        limitations=limitations,
    )


def lignes_resume_depenses_emploi_2025(
    profil: DepensesEmploi2025,
) -> list[str]:
    profil = valider_depenses_emploi_2025(profil)
    if (
        profil.deduction_federale_t777 == ZERO
        and profil.deduction_quebec_tp59 == ZERO
    ):
        return []

    lignes = ["", "DÉPENSES D'EMPLOI 2025 VALIDÉES — BLOC 4C"]

    if profil.deduction_federale_t777 > ZERO:
        lignes.extend(
            [
                (
                    "Déduction fédérale T777 — ligne 22900 : "
                    f"{profil.deduction_federale_t777:.2f} $"
                ),
                f"Source fédérale : {profil.source_federale}",
            ]
        )

    if profil.deduction_quebec_tp59 > ZERO:
        lignes.extend(
            [
                (
                    "Déduction Québec TP-59 — ligne 207, code 07 : "
                    f"{profil.deduction_quebec_tp59:.2f} $"
                ),
                f"Source Québec : {profil.source_quebec}",
            ]
        )

    return lignes
