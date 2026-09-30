"""6K : maintien à domicile 2025, composante loyers ordinaires uniquement."""
from dataclasses import dataclass, fields
from datetime import date
from decimal import Decimal, InvalidOperation, localcontext
from textwrap import wrap
from .tax_rules_2025 import arrondir_cent

ZERO = Decimal(0)
MOIS_2025 = ("Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre")
CONFIRMATIONS_6K = {
    "residence_confirmee": "Résident du Québec toute l'année 2025, admissibilité vérifiée",
    "autonomie_confirmee": "Personne autonome toute l'année; aucun cas non autonome",
    "sans_famille_confirme": "Aucun conjoint ni personne à charge toute l'année",
    "logement_ordinaire_confirme": "Logement locatif ordinaire admissible; aucun RPA, CHSLD, copropriété ou propriété",
    "occupation_confirmee": "Seul occupant, même logement loué et occupé toute l'année; aucun déménagement",
    "loyers_confirmes": "Douze loyers mensuels payés, baux et pièces justificatives vérifiés",
    "absence_autres_services_confirmee": "Aucun service supplémentaire des lignes 50 à 56 à intégrer dans ce profil",
    "absence_avances_confirmee": "Aucun versement anticipé de maintien à domicile, RL-19 D vérifié",
    "absence_double_demande_confirmee": "Aucun loyer/service réclamé ailleurs ou par une autre personne; aucun cumul médical",
    "absence_cas_particuliers_confirmee": "Aucun décès, faillite, exonération, absence ou résidence partielle",
    "valide_par_comptable": "Admissibilité, dépenses, sources et limites vérifiées par le comptable",
}


@dataclass(frozen=True)
class MaintienDomicileQuebec2025:
    activer: bool = False
    naissance: str = ""
    source: str = ""
    loyers_mensuels: tuple[Decimal, ...] = ()
    residence_confirmee: bool = False
    autonomie_confirmee: bool = False
    sans_famille_confirme: bool = False
    logement_ordinaire_confirme: bool = False
    occupation_confirmee: bool = False
    loyers_confirmes: bool = False
    absence_autres_services_confirmee: bool = False
    absence_avances_confirmee: bool = False
    absence_double_demande_confirmee: bool = False
    absence_cas_particuliers_confirmee: bool = False
    valide_par_comptable: bool = False


def montant_maintien(v, nom):
    if (not isinstance(v, Decimal) or not v.is_finite()
            or not ZERO <= v <= Decimal("999999999.99") or v != arrondir_cent(v)):
        raise ValueError("Maintien à domicile : Decimal non négatif au cent requis pour " + nom)
    return v


def montant_maintien_depuis_champ(v):
    if not isinstance(v, str) or len(v) > 40:
        raise ValueError("Loyer : texte décimal requis.")
    try:
        return montant_maintien(Decimal(v.replace(" ", "").replace("\u00a0", "").replace(",", ".") or "0"), "loyer")
    except InvalidOperation as erreur:
        raise ValueError("Loyer invalide.") from erreur


def valider_maintien_domicile_quebec_2025(p):
    if not isinstance(p, MaintienDomicileQuebec2025):
        raise ValueError("Profil maintien à domicile invalide.")
    for f in fields(p):
        v = getattr(p, f.name)
        if type(v) is not type(f.default):
            raise ValueError("Type maintien à domicile invalide : " + f.name)
        if isinstance(v, str) and (len(v) > 2000 or any(ord(c) < 32 for c in v)):
            raise ValueError("Texte maintien à domicile invalide : " + f.name)
    if not p.activer:
        if p != MaintienDomicileQuebec2025():
            raise ValueError("Activez le maintien à domicile ou effacez explicitement les faits.")
        return p
    try:
        naissance = date.fromisoformat(p.naissance)
        if naissance.isoformat() != p.naissance:
            raise ValueError()
    except ValueError as erreur:
        raise ValueError("Naissance maintien à domicile : AAAA-MM-JJ requis.") from erreur
    if naissance > date(1955, 1, 1):
        raise ValueError("Profil 6K borné : 70 ans dès le 1er janvier 2025 requis; anniversaire après le 1er janvier exclu.")
    if not p.source.strip():
        raise ValueError("Source maintien à domicile obligatoire.")
    if len(p.loyers_mensuels) != 12:
        raise ValueError("Douze loyers mensuels requis pour ce profil annuel.")
    for loyer in p.loyers_mensuels:
        montant_maintien(loyer, "loyer")
        if loyer <= ZERO:
            raise ValueError("Loyer mensuel strictement positif requis; logement gratuit hors profil.")
    for nom, libelle in CONFIRMATIONS_6K.items():
        if not getattr(p, nom):
            raise ValueError("Confirmation obligatoire : " + libelle)
    return p


@dataclass(frozen=True)
class ResultatMaintienDomicileQuebec2025:
    revenu_familial_275: Decimal = ZERO
    loyers_retenus: tuple[Decimal, ...] = ()
    base_loyers_exacte: Decimal = ZERO
    depenses_ligne_75: Decimal = ZERO
    credit_ligne_458: Decimal = ZERO


def calculer_maintien_domicile_quebec_2025(p, *, revenu_net_275):
    valider_maintien_domicile_quebec_2025(p)
    if not p.activer:
        return ResultatMaintienDomicileQuebec2025()
    montant_maintien(revenu_net_275, "275")
    if revenu_net_275 > Decimal(71010):
        raise ValueError("Maintien à domicile 6K : revenu familial supérieur à 71010; grille de réduction hors profil.")
    with localcontext() as contexte:
        contexte.prec = 28
        retenus = tuple(min(max(loyer, Decimal(600)), Decimal(1200)) for loyer in p.loyers_mensuels)
        base_exacte = sum(retenus, ZERO) * Decimal(".05")
        depenses = min(arrondir_cent(base_exacte), Decimal(19500))
        credit = arrondir_cent(depenses * Decimal(".39"))
    return ResultatMaintienDomicileQuebec2025(revenu_net_275, retenus, base_exacte, depenses, credit)


def maintien_domicile_vers_dict(p):
    valider_maintien_domicile_quebec_2025(p)
    return {f.name: [str(v) for v in p.loyers_mensuels] if f.name == "loyers_mensuels" else getattr(p, f.name)
        for f in fields(p)}


def maintien_domicile_depuis_dict(v):
    if v is None:
        return MaintienDomicileQuebec2025()
    if not isinstance(v, dict) or set(v) - {f.name for f in fields(MaintienDomicileQuebec2025)}:
        raise ValueError("Profil maintien à domicile : JSON ou clés invalides.")
    valeurs = dict(v)
    if "loyers_mensuels" in valeurs:
        loyers = valeurs["loyers_mensuels"]
        if not isinstance(loyers, list) or len(loyers) > 12:
            raise ValueError("Liste de loyers invalide.")
        valeurs["loyers_mensuels"] = tuple(montant_maintien_depuis_champ(v) for v in loyers)
    return valider_maintien_domicile_quebec_2025(MaintienDomicileQuebec2025(**valeurs))


def lignes_maintien_domicile_quebec_2025(p, r):
    if not p.activer:
        return []
    lignes = ["", "MAINTIEN À DOMICILE QUÉBEC 2025 - ANNEXE J / 458 (6K)",
        f"Naissance : {p.naissance}; autonome, seul, 70 ans dès le début de 2025; 12 mois admissibles.",
        *wrap("Sources : " + p.source, width=50),
        f"Revenu familial = Québec 275 recalculée : {r.revenu_familial_275:.2f} $; limite du profil 71010.00 $.",
        "Logement locatif ordinaire : chaque loyer retenu entre 600 et 1200 $, composante admissible 5 %."]
    for mois, loyer, retenu in zip(MOIS_2025, p.loyers_mensuels, r.loyers_retenus):
        lignes.append(f"{mois} : loyer payé {loyer:.2f} $; loyer retenu {retenu:.2f} $.")
    lignes.extend([f"Base annuelle exacte = somme des loyers retenus x 5 % : {r.base_loyers_exacte:f} $.",
        f"Ligne 75 = dépenses au cent, plafond légal individuel autonome 19500 $ : {r.depenses_ligne_75:.2f} $.",
        "Convention monétaire générale : somme exacte, puis ligne 75 au cent, puis crédit au cent.",
        "Taux 39 %; réduction nulle dans ce profil (revenu <= 71010 $); maximum légal avant réduction 7605 $.",
        f"Ligne 458 = ligne 75 x 39 % : {r.credit_ligne_458:.2f} $; crédit remboursable ajouté une seule fois.",
        "Loyers seuls : dépenses au plus 720 $ et crédit au plus 280.80 $ dans ce sous-périmètre.",
        "Exclus : services supplémentaires J 50-56, soins infirmiers et cumul de frais médicaux; aucun double usage.",
        "Aucune avance de maintien à domicile dans ce profil; sinon refus, pas de solde incomplet silencieux.",
        "Autres habitations, couples, non-autonomie, déménagements, anniversaire des 70 ans après le 1er janvier exclus.",
        "Source : Revenu Québec, TP-1.D.J (2025-12), annexe J et ligne 458, paramètres 2025."])
    return lignes
