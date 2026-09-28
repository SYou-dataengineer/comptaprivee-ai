"""RQ TP-1 2025 lignes 385/388/389 et annexe M, intérêts étudiants.

Le choix de réclamation appartient au contribuable; le crédit est calculé.
Les soldes Québec sont indépendants de la fenêtre fédérale de cinq ans.
"""
from dataclasses import dataclass, fields, replace
from decimal import Decimal, InvalidOperation
from .tax_rules_2025 import arrondir_cent

ZERO = Decimal(0)
CONFIRMATIONS_6B = {
    "emprunteur_confirme": "Le prêt étudiant a été consenti au contribuable",
    "loi_admissible_confirmee": "Prêt sous une loi admissible selon RQ, ligne 385",
    "payeur_lie_confirme": "Intérêts payés par le contribuable ou une personne liée",
    "exclusions_confirmees": "Aucun prêt privé, intégré à un autre prêt ou intérêt de jugement",
    "solde_quebec_confirme": "Solde Québec depuis 1998 vérifié et jamais utilisé pour ce crédit",
    "profil_simple_confirme": "Résident Québec/Canada toute l'année, vivant, sans faillite ni transfert de crédit",
    "valide_par_comptable": "Pièces, admissibilité et choix de réclamation validés par le comptable",
}


@dataclass(frozen=True)
class InteretsEtudiantsQuebec2025:
    interets_payes_2025: Decimal = ZERO
    solde_inutilise_1998_2024: Decimal = ZERO
    reclamation_385: Decimal = ZERO
    source: str = ""
    emprunteur_confirme: bool = False
    loi_admissible_confirmee: bool = False
    payeur_lie_confirme: bool = False
    exclusions_confirmees: bool = False
    solde_quebec_confirme: bool = False
    profil_simple_confirme: bool = False
    valide_par_comptable: bool = False


def montant_6b(v, nom):
    if (not isinstance(v, Decimal) or not v.is_finite() or not ZERO <= v <= Decimal("999999999.99")
            or v != arrondir_cent(v)):
        raise ValueError("Montant Québec 385 invalide : " + nom)
    return v


def valider_interets_quebec_2025(p):
    for nom in ("interets_payes_2025", "solde_inutilise_1998_2024", "reclamation_385"):
        montant_6b(getattr(p, nom), nom)
    if not isinstance(p.source, str):
        raise ValueError("Source Québec 385 invalide.")
    for nom in CONFIRMATIONS_6B:
        if type(getattr(p, nom)) is not bool:
            raise ValueError("Confirmation Québec 385 invalide : " + nom)
    total = p.interets_payes_2025 + p.solde_inutilise_1998_2024
    if p.reclamation_385 > total:
        raise ValueError("La réclamation 385 dépasse les intérêts Québec disponibles.")
    if total:
        if not p.source.strip():
            raise ValueError("Source des paiements et du solde Québec obligatoire.")
        for nom, libelle in CONFIRMATIONS_6B.items():
            if not getattr(p, nom):
                raise ValueError("Confirmation obligatoire : " + libelle)
    return p


@dataclass(frozen=True)
class ResultatInteretsQuebec2025:
    disponible_ligne_52: Decimal = ZERO
    ligne_385: Decimal = ZERO
    report_ligne_62: Decimal = ZERO
    credit_385: Decimal = ZERO
    ligne_388: Decimal = ZERO
    ligne_389: Decimal = ZERO
    ajout_credit_389: Decimal = ZERO


def calculer_interets_quebec_2025(p, *, base_medicale_381=ZERO):
    valider_interets_quebec_2025(p)
    montant_6b(base_medicale_381, "base médicale 381")
    disponible = p.solde_inutilise_1998_2024 + p.interets_payes_2025
    base = base_medicale_381 + p.reclamation_385
    credit = arrondir_cent(base * Decimal(".20"))
    return ResultatInteretsQuebec2025(disponible, p.reclamation_385, disponible - p.reclamation_385,
        arrondir_cent(p.reclamation_385 * Decimal(".20")), base, credit,
        credit - arrondir_cent(base_medicale_381 * Decimal(".20")))


def appliquer_interets_quebec_2025(impot, r):
    if not r.disponible_ligne_52:
        return impot
    return replace(impot, impot_quebec_preliminaire=max(impot.impot_quebec_preliminaire - r.ajout_credit_389, ZERO),
        limitations=impot.limitations + ("Intérêts étudiants Québec 385 : crédit non remboursable, choix et report annexe M distincts du fédéral.",))


def interets_quebec_vers_dict(p):
    valider_interets_quebec_2025(p)
    return {f.name: str(getattr(p, f.name)) if isinstance(f.default, Decimal) else getattr(p, f.name) for f in fields(p)}


def interets_quebec_depuis_dict(v):
    if v is None:
        return InteretsEtudiantsQuebec2025()
    if not isinstance(v, dict) or set(v) - {f.name for f in fields(InteretsEtudiantsQuebec2025)}:
        raise ValueError("Profil intérêts Québec ou clés inconnues invalides.")
    valeurs = dict(v)
    for f in fields(InteretsEtudiantsQuebec2025):
        if f.name in valeurs and isinstance(f.default, Decimal):
            if type(valeurs[f.name]) not in (str, int):
                raise ValueError("Montant JSON Québec 385 invalide.")
            try:
                valeurs[f.name] = Decimal(valeurs[f.name])
            except InvalidOperation as erreur:
                raise ValueError("Montant JSON Québec 385 invalide.") from erreur
    return valider_interets_quebec_2025(InteretsEtudiantsQuebec2025(**valeurs))


def lignes_interets_quebec_2025(p, r):
    if not r.disponible_ligne_52:
        return []
    return ["", "INTÉRÊTS ÉTUDIANTS QUÉBEC — ANNEXE M / LIGNE 385",
        f"Solde inutilisé 1998–2024, ligne 46 : {p.solde_inutilise_1998_2024:.2f} $",
        f"Intérêts payés 2025, ligne 48 : {p.interets_payes_2025:.2f} $",
        f"Disponible ligne 52 = 46 + 48 : {r.disponible_ligne_52:.2f} $",
        f"Réclamation choisie ligne 385 / annexe M ligne 60 : {r.ligne_385:.2f} $",
        f"Report ligne 62 = disponible - réclamation : {r.report_ligne_62:.2f} $; sans expiration de cinq ans",
        f"Crédit sur 385 à 20 % : {r.credit_385:.2f} $; non remboursable",
        f"Base commune 381 + 385, ligne 388 : {r.ligne_388:.2f} $; ligne 389 arrondie à 20 % : {r.ligne_389:.2f} $",
        f"Ajout au crédit 389 après crédit médical déjà calculé : {r.ajout_credit_389:.2f} $",
        "Une réclamation sans économie fiscale reste consommée; aucun report automatique de la portion réclamée.",
        "Solde Québec indépendant du fédéral; aucune admissibilité ni récupération des avis RQ automatique.",
        f"Source : {p.source}; validation comptable : confirmée."]
