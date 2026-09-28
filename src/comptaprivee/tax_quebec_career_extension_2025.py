"""RQ TP-752.PC (2025-10), ligne 391 : profil salarié admissible borné."""
from dataclasses import dataclass, fields, replace
from datetime import date
from decimal import Decimal
from .tax_rules_2025 import arrondir_cent

ZERO = Decimal(0)
CONFIRMATIONS_6D = {
    "residence_confirmee": "Résident du Québec et du Canada toute l'année 2025",
    "emploi_admissible_confirme": "Revenus de travail limités au salaire RL-1 du dossier; aucun autre revenu de travail admissible",
    "aucun_lien_dependance_confirme": "Aucun salaire d'un employeur lié ni d'une société de personnes ayant un membre lié",
    "aucune_exclusion_confirmee": "Aucun avantage d'ancien emploi case 211, ni déduction 293/297 liée au salaire",
    "aucun_retroactif_confirme": "Aucun salaire rétroactif se rapportant à une année passée",
    "profil_simple_confirme": "Contribuable vivant, sans faillite; aucun travail autonome ou autre profil de travail spécialisé",
    "valide_par_comptable": "Naissance, feuillets et périmètre vérifiés par le comptable",
}


@dataclass(frozen=True)
class ProlongationCarriereQuebec2025:
    reclamer: bool = False
    naissance: str = ""
    source: str = ""
    residence_confirmee: bool = False
    emploi_admissible_confirme: bool = False
    aucun_lien_dependance_confirme: bool = False
    aucune_exclusion_confirmee: bool = False
    aucun_retroactif_confirme: bool = False
    profil_simple_confirme: bool = False
    valide_par_comptable: bool = False


def valider_carriere_quebec_2025(p):
    for f in fields(p):
        if type(getattr(p, f.name)) is not type(f.default):
            raise ValueError("Type du profil 391 invalide : " + f.name)
    if not p.reclamer:
        if p.naissance or p.source:
            raise ValueError("Activez le profil 391 ou effacez les données.")
        return p
    try:
        naissance = date.fromisoformat(p.naissance)
        if naissance.isoformat() != p.naissance:
            raise ValueError()
    except ValueError as erreur:
        raise ValueError("Date de naissance 391 invalide : AAAA-MM-JJ obligatoire.") from erreur
    if naissance > date(1960, 12, 31):
        raise ValueError("La prolongation de carrière exige 65 ans au 31 décembre 2025.")
    if not p.source.strip():
        raise ValueError("Source naissance et feuillets obligatoire pour 391.")
    for nom, libelle in CONFIRMATIONS_6D.items():
        if not getattr(p, nom): raise ValueError("Confirmation obligatoire : " + libelle)
    return p


@dataclass(frozen=True)
class ResultatCarriereQuebec2025:
    revenu_travail: Decimal = ZERO
    revenu_net: Decimal = ZERO
    base_ligne_16: Decimal = ZERO
    credit_ligne_35: Decimal = ZERO
    reduction_ligne_39: Decimal = ZERO
    credit_reduit_ligne_40: Decimal = ZERO
    plafond_impot_ligne_49: Decimal = ZERO
    credit_ligne_391: Decimal = ZERO


def calculer_carriere_quebec_2025(p, *, salaire=ZERO, revenu_net=ZERO, impot_401=ZERO,
                                 montant_359=ZERO, montant_361=ZERO, montant_367=ZERO):
    valider_carriere_quebec_2025(p)
    for nom, v in (("salaire", salaire), ("275", revenu_net), ("401", impot_401),
                   ("359", montant_359), ("361", montant_361), ("367", montant_367)):
        if (not isinstance(v, Decimal) or not v.is_finite() or not ZERO <= v <= Decimal("999999999.99")
                or v != arrondir_cent(v)):
            raise ValueError("Montant TP-752.PC invalide : " + nom)
    if not p.reclamer: return ResultatCarriereQuebec2025()
    base = min(max(salaire - Decimal(7500), ZERO), Decimal(12500))
    credit = arrondir_cent(base * Decimal(".14"))
    reduction = arrondir_cent(max(revenu_net - Decimal(56500), ZERO) * Decimal(".07"))
    reduit = max(credit - reduction, ZERO)
    plafond = max(impot_401 - arrondir_cent((montant_359 + montant_361 + montant_367) * Decimal(".14")), ZERO)
    return ResultatCarriereQuebec2025(salaire, revenu_net, base, credit, reduction, reduit, plafond, min(reduit, plafond))


def appliquer_carriere_quebec_2025(impot, p, r):
    if not p.reclamer: return impot
    return replace(impot, impot_quebec_preliminaire=max(impot.impot_quebec_preliminaire - r.credit_ligne_391, ZERO),
        limitations=impot.limitations + ("Prolongation de carrière Québec 391 : salarié 65 ans et plus, plafond fiscal et réduction selon revenu net 2025.",))


def carriere_quebec_vers_dict(p):
    valider_carriere_quebec_2025(p)
    return {f.name: getattr(p, f.name) for f in fields(p)}


def carriere_quebec_depuis_dict(v):
    if v is None: return ProlongationCarriereQuebec2025()
    if not isinstance(v, dict) or set(v) - {f.name for f in fields(ProlongationCarriereQuebec2025)}:
        raise ValueError("Profil prolongation de carrière ou clés inconnues invalides.")
    return valider_carriere_quebec_2025(ProlongationCarriereQuebec2025(**v))


def lignes_carriere_quebec_2025(p, r):
    if not p.reclamer: return []
    return ["", "PROLONGATION DE CARRIÈRE QUÉBEC — TP-752.PC / LIGNE 391",
        f"Naissance : {p.naissance}; 65 ans ou plus au 31 décembre 2025",
        f"Salaire admissible recalculé : {r.revenu_travail:.2f} $; revenu net 275 : {r.revenu_net:.2f} $",
        f"Ligne 16 = min(max(salaire - 7500, 0), 12500) : {r.base_ligne_16:.2f} $",
        f"Crédit ligne 35 à 14 % : {r.credit_ligne_35:.2f} $; maximum 1750.00 $",
        f"Réduction ligne 39 = max(revenu net - 56500, 0) × 7 % : {r.reduction_ligne_39:.2f} $",
        f"Crédit réduit ligne 40 : {r.credit_reduit_ligne_40:.2f} $",
        f"Plafond ligne 49 = max(401 - (359 + 361 + 367) × 14 %, 0) : {r.plafond_impot_ligne_49:.2f} $",
        f"Ligne 391 = minimum de 40 et 49 : {r.credit_ligne_391:.2f} $; non remboursable",
        f"Source : {p.source}; validation comptable : confirmée.",
        "Salaire sans lien de dépendance ni rétroactivité, exclusions vérifiées; autres revenus de travail hors périmètre 6D."]
