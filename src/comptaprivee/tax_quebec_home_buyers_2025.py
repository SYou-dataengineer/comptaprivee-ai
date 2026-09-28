"""RQ TP-752.HA (2025-10), première habitation et partage, ligne 396.

Le plafond fiscal de la partie 5.1 est distinct du solde d'impôt final.
Les cas de handicap, décès et résidence partielle ne sont pas étendus ici.
"""
from dataclasses import dataclass, fields, replace
from datetime import date
from decimal import Decimal, InvalidOperation
from .tax_rules_2025 import arrondir_cent

ZERO = Decimal(0)
MAXIMUM_396 = Decimal(1400)
CONFIRMATIONS_6C = {
    "residence_confirmee": "Résident du Québec et du Canada toute l'année 2025",
    "acquisition_confirmee": "Acquisition par le contribuable ou son conjoint : droit publié et habitation habitable en 2025",
    "habitation_quebec_confirmee": "Habitation admissible située au Québec; propriété ou part de coopérative donnant droit de posséder",
    "premier_acheteur_confirme": "Aucune habitation occupée possédée par soi ou son conjoint du 1er janvier 2021 à l'acquisition",
    "residence_principale_confirmee": "Intention d'en faire son lieu principal de résidence au plus tard un an après l'acquisition",
    "partage_confirme": "Parts des autres personnes admissibles à 396 vérifiées; 0 si aucune",
    "profil_simple_confirme": "Première habitation, sans exception handicap, décès, faillite ni transfert de crédit entre conjoints",
    "valide_par_comptable": "Acte, admissibilité et partage vérifiés par le comptable",
}


@dataclass(frozen=True)
class AchatHabitationQuebec2025:
    reclamer: bool = False
    date_acquisition: str = ""
    reference_habitation: str = ""
    credit_demande_autres: Decimal = ZERO
    source: str = ""
    residence_confirmee: bool = False
    acquisition_confirmee: bool = False
    habitation_quebec_confirmee: bool = False
    premier_acheteur_confirme: bool = False
    residence_principale_confirmee: bool = False
    partage_confirme: bool = False
    profil_simple_confirme: bool = False
    valide_par_comptable: bool = False


def _montant(v, nom):
    if (not isinstance(v, Decimal) or not v.is_finite() or not ZERO <= v <= Decimal("999999999.99")
            or v != arrondir_cent(v)):
        raise ValueError("Montant TP-752.HA invalide : " + nom)
    return v


def valider_achat_quebec_2025(p):
    for f in fields(p):
        v = getattr(p, f.name)
        if isinstance(f.default, (str, bool)) and type(v) is not type(f.default):
            raise ValueError("Type du profil 396 invalide : " + f.name)
    _montant(p.credit_demande_autres, "parts des autres")
    if p.credit_demande_autres > MAXIMUM_396:
        raise ValueError("Les parts des autres dépassent le plafond commun de 1400 $.")
    if not p.reclamer:
        if p.credit_demande_autres or p.date_acquisition or p.reference_habitation or p.source:
            raise ValueError("Activez la demande 396 ou effacez ses données.")
        return p
    try:
        acquisition = date.fromisoformat(p.date_acquisition)
        if acquisition.year != 2025 or acquisition.isoformat() != p.date_acquisition:
            raise ValueError()
    except ValueError as erreur:
        raise ValueError("Date d'acquisition 396 : AAAA-MM-JJ en 2025 obligatoire.") from erreur
    if not p.reference_habitation.strip() or not p.source.strip():
        raise ValueError("Référence de l'habitation et source de l'acte/partage obligatoires.")
    for nom, libelle in CONFIRMATIONS_6C.items():
        if not getattr(p, nom):
            raise ValueError("Confirmation obligatoire : " + libelle)
    return p


@dataclass(frozen=True)
class ResultatAchatQuebec2025:
    impot_ligne_25: Decimal = ZERO
    base_ligne_26: Decimal = ZERO
    credit_ligne_27: Decimal = ZERO
    autres_credits_ligne_28: Decimal = ZERO
    plafond_impot_ligne_30: Decimal = ZERO
    disponible_ligne_37: Decimal = ZERO
    credit_ligne_396: Decimal = ZERO


def calculer_achat_quebec_2025(p, *, impot_401=ZERO, montant_359=ZERO, montant_361=ZERO,
                              montant_367=ZERO, credit_391=ZERO, credit_397=ZERO):
    valider_achat_quebec_2025(p)
    for nom, v in (("401", impot_401), ("359", montant_359), ("361", montant_361),
                   ("367", montant_367), ("391", credit_391), ("397", credit_397)):
        _montant(v, nom)
    if not p.reclamer:
        return ResultatAchatQuebec2025()
    base = montant_359 + montant_361 + montant_367
    credit = arrondir_cent(base * Decimal(".14"))
    autres = credit_391 + credit_397
    plafond = max(impot_401 - credit - autres, ZERO)
    disponible = MAXIMUM_396 - p.credit_demande_autres
    return ResultatAchatQuebec2025(impot_401, base, credit, autres, plafond, disponible, min(plafond, disponible))


def appliquer_achat_quebec_2025(impot, p, r):
    if not p.reclamer:
        return impot
    return replace(impot, impot_quebec_preliminaire=max(impot.impot_quebec_preliminaire - r.credit_ligne_396, ZERO),
        limitations=impot.limitations + ("Achat habitation Québec 396 : plafond d'impôt TP-752.HA et plafond partagé de 1400 $ appliqués.",))


def achat_quebec_vers_dict(p):
    valider_achat_quebec_2025(p)
    return {f.name: str(getattr(p, f.name)) if isinstance(f.default, Decimal) else getattr(p, f.name) for f in fields(p)}


def achat_quebec_depuis_dict(v):
    if v is None: return AchatHabitationQuebec2025()
    if not isinstance(v, dict) or set(v) - {f.name for f in fields(AchatHabitationQuebec2025)}:
        raise ValueError("Profil achat Québec ou clés inconnues invalides.")
    valeurs = dict(v)
    if "credit_demande_autres" in valeurs:
        if type(valeurs["credit_demande_autres"]) not in (str, int):
            raise ValueError("Part des autres 396 invalide.")
        try: valeurs["credit_demande_autres"] = Decimal(valeurs["credit_demande_autres"])
        except InvalidOperation as erreur: raise ValueError("Part des autres 396 invalide.") from erreur
    return valider_achat_quebec_2025(AchatHabitationQuebec2025(**valeurs))


def lignes_achat_quebec_2025(p, r):
    if not p.reclamer: return []
    return ["", "ACHAT HABITATION QUÉBEC — TP-752.HA / LIGNE 396",
        f"Habitation : {p.reference_habitation}; acquisition : {p.date_acquisition}",
        f"Impôt 401 / formulaire ligne 25 : {r.impot_ligne_25:.2f} $",
        f"Base 359 + 361 + 367 / ligne 26 : {r.base_ligne_26:.2f} $; à 14 % / ligne 27 : {r.credit_ligne_27:.2f} $",
        f"Crédits 391 + 397 / ligne 28 : {r.autres_credits_ligne_28:.2f} $",
        f"Plafond fiscal ligne 30 = max(25 - 27 - 28, 0) : {r.plafond_impot_ligne_30:.2f} $",
        f"Plafond commun : 1400.00 $; autres demandes : {p.credit_demande_autres:.2f} $; disponible ligne 37 : {r.disponible_ligne_37:.2f} $",
        f"Ligne 396 = min(ligne 30, ligne 37) : {r.credit_ligne_396:.2f} $; non remboursable",
        f"Source acte et partage : {p.source}; validation comptable : confirmée.",
        "Première habitation au Québec; exception handicap, décès et résidence partielle hors périmètre 6C."]
