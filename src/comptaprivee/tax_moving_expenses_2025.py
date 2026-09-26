"""Frais de déménagement simples 2025 — Bloc 4D.

Périmètre initial :
- employé salarié ordinaire;
- déménagement pour occuper un emploi à un nouveau lieu de travail;
- nouveau domicile au moins 40 km plus près du nouveau lieu de travail;
- déménagement à l'intérieur du Canada;
- remboursements/allocations de l'employeur déjà pris en compte;
- montant fédéral déjà établi au T1-M et reporté à la ligne 21900;
- montant Québec déjà établi au TP-348 et reporté à la ligne 228;
- aucune détermination détaillée des catégories de frais dans ce sous-bloc.

Sont explicitement hors périmètre : travail autonome, étudiant à temps plein,
déménagement international, report de frais d'années antérieures et plusieurs
déménagements admissibles.
"""

from dataclasses import dataclass, replace
from decimal import Decimal

from .tax_income_2025 import RevenuNetImposable2025
from .tax_rules_2025 import arrondir_cent

ZERO = Decimal("0")


@dataclass(frozen=True)
class FraisDemenagement2025:
    deduction_federale_t1m: Decimal = ZERO
    deduction_quebec_tp348: Decimal = ZERO
    source_federale: str = ""
    source_quebec: str = ""
    valide_par_comptable: bool = False
    salarie_ordinaire_confirme: bool = False
    demenagement_pour_emploi_confirme: bool = False
    rapprochement_40km_confirme: bool = False
    demenagement_interieur_canada_confirme: bool = False
    remboursements_employeur_pris_en_compte_confirme: bool = False
    t1m_confirme: bool = False
    tp348_confirme: bool = False
    travailleur_autonome: bool = False
    etudiant_temps_plein: bool = False
    demenagement_international: bool = False
    report_annees_anterieures: bool = False
    plusieurs_demenagements_admissibles: bool = False


def _montant_fini_non_negatif(valeur: Decimal, libelle: str) -> Decimal:
    if not valeur.is_finite():
        raise ValueError(f"{libelle} doit être un nombre fini.")
    if valeur < ZERO:
        raise ValueError(f"{libelle} ne peut pas être négatif.")
    return arrondir_cent(valeur)


def valider_frais_demenagement_2025(
    profil: FraisDemenagement2025,
) -> FraisDemenagement2025:
    federal = _montant_fini_non_negatif(
        profil.deduction_federale_t1m,
        "La déduction fédérale T1-M / ligne 21900",
    )
    quebec = _montant_fini_non_negatif(
        profil.deduction_quebec_tp348,
        "La déduction Québec TP-348 / ligne 228",
    )

    profil = replace(
        profil,
        deduction_federale_t1m=federal,
        deduction_quebec_tp348=quebec,
        source_federale=profil.source_federale.strip(),
        source_quebec=profil.source_quebec.strip(),
    )

    if federal == ZERO and quebec == ZERO:
        return profil

    if any(
        (
            profil.travailleur_autonome,
            profil.etudiant_temps_plein,
            profil.demenagement_international,
            profil.report_annees_anterieures,
            profil.plusieurs_demenagements_admissibles,
        )
    ):
        raise ValueError(
            "La situation indiquée est hors périmètre 4D simple et nécessite "
            "un traitement avancé des frais de déménagement."
        )

    if not profil.valide_par_comptable:
        raise ValueError(
            "Les frais de déménagement doivent être validés par le comptable."
        )
    if not profil.salarie_ordinaire_confirme:
        raise ValueError(
            "Le Bloc 4D simple exige un employé salarié ordinaire."
        )
    if not profil.demenagement_pour_emploi_confirme:
        raise ValueError(
            "Le déménagement doit être confirmé comme ayant été effectué "
            "pour occuper un emploi à un nouveau lieu de travail."
        )
    if not profil.rapprochement_40km_confirme:
        raise ValueError(
            "Le nouveau domicile doit être confirmé comme étant au moins "
            "40 km plus près du nouveau lieu de travail."
        )
    if not profil.demenagement_interieur_canada_confirme:
        raise ValueError(
            "Le Bloc 4D simple exige un déménagement à l'intérieur du Canada."
        )
    if not profil.remboursements_employeur_pris_en_compte_confirme:
        raise ValueError(
            "Les remboursements ou allocations de l'employeur doivent être "
            "confirmés comme déjà pris en compte."
        )

    if federal > ZERO:
        if not profil.t1m_confirme:
            raise ValueError(
                "Le T1-M doit être confirmé pour la déduction fédérale 4D."
            )
        if not profil.source_federale:
            raise ValueError(
                "La source fédérale T1-M est obligatoire."
            )

    if quebec > ZERO:
        if not profil.tp348_confirme:
            raise ValueError(
                "Le TP-348 doit être confirmé pour la déduction Québec 4D."
            )
        if not profil.source_quebec:
            raise ValueError(
                "La source Québec TP-348 est obligatoire."
            )

    return profil


def appliquer_frais_demenagement_2025(
    revenu: RevenuNetImposable2025,
    profil: FraisDemenagement2025,
) -> RevenuNetImposable2025:
    if revenu.annee_fiscale != 2025:
        raise ValueError(
            "Les frais de déménagement actuels acceptent uniquement "
            "l'année 2025."
        )

    profil = valider_frais_demenagement_2025(profil)
    federal = profil.deduction_federale_t1m
    quebec = profil.deduction_quebec_tp348

    if federal == ZERO and quebec == ZERO:
        return revenu

    limitations = tuple(
        texte
        for texte in revenu.limitations
        if texte != "Aucune autre déduction de revenu net ou imposable."
    ) + (
        "Frais de déménagement simples T1-M / ligne 21900 inclus au fédéral.",
        "Frais de déménagement simples TP-348 / ligne 228 inclus au Québec.",
        "Travail autonome, études, déménagement international, reports et "
        "déménagements multiples hors périmètre 4D.",
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
        profil=revenu.profil + " + frais de déménagement 4D",
        limitations=limitations,
    )


def lignes_resume_frais_demenagement_2025(
    profil: FraisDemenagement2025,
) -> list[str]:
    profil = valider_frais_demenagement_2025(profil)
    if (
        profil.deduction_federale_t1m == ZERO
        and profil.deduction_quebec_tp348 == ZERO
    ):
        return []

    lignes = ["", "FRAIS DE DÉMÉNAGEMENT 2025 VALIDÉS — BLOC 4D"]

    if profil.deduction_federale_t1m > ZERO:
        lignes.extend(
            [
                (
                    "Déduction fédérale T1-M — ligne 21900 : "
                    f"{profil.deduction_federale_t1m:.2f} $"
                ),
                f"Source fédérale : {profil.source_federale}",
            ]
        )

    if profil.deduction_quebec_tp348 > ZERO:
        lignes.extend(
            [
                (
                    "Déduction Québec TP-348 — ligne 228 : "
                    f"{profil.deduction_quebec_tp348:.2f} $"
                ),
                f"Source Québec : {profil.source_quebec}",
            ]
        )

    return lignes
