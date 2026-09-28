"""Annexe B 2025, parties A/B : combinaison sans conjoint, réduction unique.

RQ TP-1.D.B(2025-12), lignes 10 à 34; guide de la ligne 361.
Les profils historiques distincts restent disponibles sans activation commune.
"""
from dataclasses import dataclass, replace
from decimal import Decimal

from .tax_age_retirement_2025 import (
    valider_montants_age_retraite_2025, montant_age_2025, montant_revenus_retraite_2025)
from .tax_living_alone_2025 import (
    valider_personne_vivant_seule_2025, montant_additionnel_monoparental_2025)
from .tax_rules_2025 import arrondir_cent

ZERO = Decimal(0)


@dataclass(frozen=True)
class ResultatAnnexeBCombinee2025:
    revenu_familial: Decimal
    personne_seule: Decimal
    additionnel_monoparental: Decimal
    age: Decimal
    retraite: Decimal
    total_ligne_30: Decimal
    reduction_ligne_31: Decimal
    ligne_361: Decimal
    credit: Decimal


def calculer_annexe_b_combinee_2025(seule, age, *, revenu_net=None):
    valider_personne_vivant_seule_2025(seule)
    valider_montants_age_retraite_2025(age)
    if not (seule.combinaison_annexe_b_confirmee or age.combinaison_annexe_b_confirmee):
        return None
    if not (seule.combinaison_annexe_b_confirmee and age.combinaison_annexe_b_confirmee):
        raise ValueError("La combinaison annexe B doit être confirmée dans les deux profils.")
    if seule.revenu_familial_net != age.revenu_familial_net:
        raise ValueError("Revenus familiaux divergents dans l'annexe B combinée.")
    if revenu_net is not None and seule.revenu_familial_net != revenu_net:
        raise ValueError("Le revenu familial de l'annexe B doit correspondre au revenu net Québec recalculé.")
    revenu = seule.revenu_familial_net
    vivant_seul = Decimal(2128)
    supplement = montant_additionnel_monoparental_2025(seule)
    montant_age = montant_age_2025(age)
    retraite = montant_revenus_retraite_2025(age)
    total = vivant_seul + supplement + montant_age + retraite
    reduction = arrondir_cent(max(revenu - Decimal(42090), ZERO) * Decimal("0.1875"))
    montant = max(total - reduction, ZERO)
    return ResultatAnnexeBCombinee2025(revenu, vivant_seul, supplement, montant_age, retraite,
        total, reduction, montant, arrondir_cent(montant * Decimal("0.14")))


def appliquer_annexe_b_combinee_2025(impot, resultat):
    return replace(impot, impot_quebec_preliminaire=max(impot.impot_quebec_preliminaire - resultat.credit, ZERO),
        limitations=tuple(t for t in impot.limitations if t != "Aucun montant pour conjoint, personne à charge ou âge.")
        + ("Annexe B combinée, ligne 361 : réduction unique; sans conjoint.",))


def lignes_annexe_b_combinee_2025(seule, age):
    r = calculer_annexe_b_combinee_2025(seule, age)
    if r is None:
        return []
    return ["", "ANNEXE B COMBINÉE — QUÉBEC 2025 / LIGNE 361",
        f"Revenu familial, sans conjoint : {r.revenu_familial:.2f} $",
        f"Personne vivant seule : {r.personne_seule:.2f}; additionnel monoparental : {r.additionnel_monoparental:.2f} $",
        f"Âge : {r.age:.2f}; retraite : {r.retraite:.2f}; total ligne 30 : {r.total_ligne_30:.2f} $",
        f"Réduction unique ligne 31 = max(revenu - 42090, 0) × 18,75 % : {r.reduction_ligne_31:.2f} $",
        f"Ligne 361 = max(ligne 30 - ligne 31, 0) : {r.ligne_361:.2f} $; crédit à 14 % : {r.credit:.2f} $",
        f"Source logement : {seule.source}; source âge : {age.source_age}; source retraite : {age.source_retraite}",
        "Résidence, habitation, âge/revenus admissibles et combinaison validés par le comptable."]
