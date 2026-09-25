"""Déduction CELIAPP simple 2025 — Bloc 4A.

Périmètre initial :
- cotisations directes 2025 seulement;
- aucun montant inutilisé d'une année antérieure réclamé;
- aucun transfert REER -> CELIAPP;
- aucun retrait en 2025;
- aucun excédent;
- résidence Canada/Québec toute l'année et titulaire confirmés.

La déduction est appliquée aux revenus net et imposable fédéral/Québec.
"""

from dataclasses import dataclass, replace
from decimal import Decimal

from .tax_income_2025 import RevenuNetImposable2025
from .tax_rules_2025 import arrondir_cent

ZERO = Decimal("0")


@dataclass(frozen=True)
class DeductionCeliapp2025:
    deduction: Decimal = ZERO
    cotisations_directes_2025: Decimal = ZERO
    droits_deduction_confirmes: Decimal = ZERO
    source_droits: str = ""
    valide_par_comptable: bool = False
    titulaire_confirme: bool = False
    residence_canada_quebec_annee_complete: bool = False
    inclut_cotisations_inutilisees_anterieures: bool = False
    inclut_transfert_reer: bool = False
    retrait_2025: bool = False
    excedent_2025: bool = False


def _montant_fini_non_negatif(valeur: Decimal, libelle: str) -> Decimal:
    if not valeur.is_finite():
        raise ValueError(f"{libelle} doit être un nombre fini.")
    if valeur < ZERO:
        raise ValueError(f"{libelle} ne peut pas être négatif.")
    return arrondir_cent(valeur)


def valider_deduction_celiapp_2025(
    profil: DeductionCeliapp2025,
) -> DeductionCeliapp2025:
    deduction = _montant_fini_non_negatif(
        profil.deduction, "La déduction CELIAPP"
    )
    cotisations = _montant_fini_non_negatif(
        profil.cotisations_directes_2025,
        "Les cotisations directes CELIAPP 2025",
    )
    droits = _montant_fini_non_negatif(
        profil.droits_deduction_confirmes,
        "Les droits de déduction CELIAPP confirmés",
    )

    profil = replace(
        profil,
        deduction=deduction,
        cotisations_directes_2025=cotisations,
        droits_deduction_confirmes=droits,
        source_droits=profil.source_droits.strip(),
    )

    if deduction == ZERO:
        return profil

    if not profil.valide_par_comptable:
        raise ValueError(
            "La déduction CELIAPP doit être validée par le comptable."
        )
    if not profil.titulaire_confirme:
        raise ValueError(
            "Le titulaire du CELIAPP doit être confirmé."
        )
    if not profil.residence_canada_quebec_annee_complete:
        raise ValueError(
            "Le Bloc 4A exige une résidence Canada/Québec pendant toute l'année 2025."
        )
    if not profil.source_droits:
        raise ValueError(
            "La source des droits de déduction CELIAPP confirmés est obligatoire."
        )
    if droits == ZERO:
        raise ValueError(
            "Les droits de déduction CELIAPP doivent être confirmés."
        )
    if cotisations == ZERO:
        raise ValueError(
            "Le Bloc 4A exige des cotisations directes CELIAPP en 2025."
        )
    if deduction > cotisations:
        raise ValueError(
            "La déduction CELIAPP ne peut pas dépasser les cotisations directes 2025 dans le Bloc 4A."
        )
    if deduction > droits:
        raise ValueError(
            "La déduction CELIAPP dépasse les droits de déduction confirmés."
        )
    if profil.inclut_cotisations_inutilisees_anterieures:
        raise ValueError(
            "Les cotisations CELIAPP inutilisées d'années antérieures sont hors périmètre 4A."
        )
    if profil.inclut_transfert_reer:
        raise ValueError(
            "Les transferts REER vers CELIAPP sont hors périmètre 4A."
        )
    if profil.retrait_2025:
        raise ValueError(
            "Les retraits CELIAPP 2025 sont hors périmètre 4A."
        )
    if profil.excedent_2025:
        raise ValueError(
            "Les excédents CELIAPP sont hors périmètre 4A."
        )

    return profil


def appliquer_deduction_celiapp_2025(
    revenu: RevenuNetImposable2025,
    profil: DeductionCeliapp2025,
) -> RevenuNetImposable2025:
    if revenu.annee_fiscale != 2025:
        raise ValueError(
            "La déduction CELIAPP actuelle accepte uniquement l'année 2025."
        )

    profil = valider_deduction_celiapp_2025(profil)
    deduction = profil.deduction
    if deduction == ZERO:
        return revenu

    limitations = tuple(
        texte
        for texte in revenu.limitations
        if texte != "Aucune autre déduction de revenu net ou imposable."
    ) + (
        "Déduction CELIAPP simple 20805/215 validée incluse.",
        "Reports antérieurs, transferts REER, retraits et excédents CELIAPP hors périmètre 4A.",
    )

    return replace(
        revenu,
        revenu_net_federal=max(
            arrondir_cent(revenu.revenu_net_federal - deduction), ZERO
        ),
        revenu_imposable_federal=max(
            arrondir_cent(revenu.revenu_imposable_federal - deduction), ZERO
        ),
        revenu_net_quebec=max(
            arrondir_cent(revenu.revenu_net_quebec - deduction), ZERO
        ),
        revenu_imposable_quebec=max(
            arrondir_cent(revenu.revenu_imposable_quebec - deduction), ZERO
        ),
        profil=revenu.profil + " + CELIAPP 4A",
        limitations=limitations,
    )


def lignes_resume_celiapp_2025(profil: DeductionCeliapp2025) -> list[str]:
    profil = valider_deduction_celiapp_2025(profil)
    if profil.deduction == ZERO:
        return []
    return [
        "",
        "CELIAPP 2025 VALIDÉ — BLOC 4A",
        f"Déduction fédérale — ligne 20805 : {profil.deduction:.2f} $",
        f"Déduction Québec — ligne 215 : {profil.deduction:.2f} $",
        f"Cotisations directes 2025 : {profil.cotisations_directes_2025:.2f} $",
        f"Droits de déduction confirmés : {profil.droits_deduction_confirmes:.2f} $",
        f"Source : {profil.source_droits}",
    ]
