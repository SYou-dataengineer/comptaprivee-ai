"""6L : ligne 390 Québec 2025, bénévoles non rémunérés de même activité."""
from dataclasses import dataclass, fields, replace
from decimal import Decimal
from textwrap import wrap
from .tax_volunteers_2025 import calculer_benevoles_2025
from .tax_rules_2025 import arrondir_cent

ZERO = Decimal(0)
CONFIRMATIONS_390 = {
    "residence_confirmee": "Résident Québec/Canada toute l'année 2025; aucun cas particulier",
    "admissibilite_quebec_confirmee": "Services et organismes de 5L admissibles distinctement selon Revenu Québec 2025",
    "certificats_quebec_confirmes": "Certificats Québec vérifiés pour toutes les heures retenues de l'activité choisie",
    "absence_remuneration_confirmee": "Aucune rémunération pour ces services; aucune case RL-1 L-2 ou T4 87 positive",
    "unicite_confirmee": "Un seul crédit Québec, aucune heure en double, aucun service similaire rémunéré",
    "valide_par_comptable": "Faits, choix Québec, certificats et limites vérifiés par le comptable",
}


@dataclass(frozen=True)
class VolontairesQuebec2025:
    activer: bool = False
    source: str = ""
    residence_confirmee: bool = False
    admissibilite_quebec_confirmee: bool = False
    certificats_quebec_confirmes: bool = False
    absence_remuneration_confirmee: bool = False
    unicite_confirmee: bool = False
    valide_par_comptable: bool = False


def valider_volontaires_quebec_2025(p):
    if not isinstance(p, VolontairesQuebec2025):
        raise ValueError("Profil volontaires Québec invalide.")
    for f in fields(p):
        v = getattr(p, f.name)
        if type(v) is not type(f.default):
            raise ValueError("Type volontaires Québec invalide : " + f.name)
        if isinstance(v, str) and (len(v) > 2000 or any(ord(c) < 32 for c in v)):
            raise ValueError("Source volontaires Québec invalide.")
    if not p.activer:
        if p != VolontairesQuebec2025():
            raise ValueError("Activez les volontaires Québec ou effacez explicitement le profil.")
        return p
    if not p.source.strip():
        raise ValueError("Source volontaires Québec obligatoire.")
    for nom, libelle in CONFIRMATIONS_390.items():
        if not getattr(p, nom):
            raise ValueError("Confirmation obligatoire : " + libelle)
    return p


@dataclass(frozen=True)
class ResultatVolontairesQuebec2025:
    activite: str = ""
    heures_admissibles: Decimal = ZERO
    credit_ligne_390: Decimal = ZERO
    reduction_impot_effective: Decimal = ZERO


def calculer_volontaires_quebec_2025(p, *, benevoles, dossier, impot_disponible):
    valider_volontaires_quebec_2025(p)
    if not p.activer:
        return ResultatVolontairesQuebec2025()
    if (not isinstance(impot_disponible, Decimal) or not impot_disponible.is_finite()
            or impot_disponible < ZERO or impot_disponible != arrondir_cent(impot_disponible)):
        raise ValueError("Impôt disponible Québec invalide.")
    r = calculer_benevoles_2025(benevoles, dossier)
    if benevoles.choix not in ("pompiers", "sauvetage"):
        raise ValueError("390 : préparer les activités et le choix pompiers/sauvetage dans Services bénévoles 5L.")
    if any(d.valeur_validee != ZERO and (d.type_document, d.case) in (("RL-1", "L-2"), ("T4", "87"))
            for d in dossier.donnees_validees):
        raise ValueError("390 : rémunération L-2/87 hors du profil non rémunéré; inclusion fiscale à traiter séparément.")
    if any(a.nature != benevoles.choix or a.services_similaires_remuneres or not a.organisme_admissible for a in benevoles.activites):
        raise ValueError("390 : une seule nature d'activité, organismes admissibles, aucun service rémunéré dans ce profil.")
    heures = r.heures_pompiers if benevoles.choix == "pompiers" else r.heures_sauvetage
    if heures < Decimal(200):
        raise ValueError("390 : au moins 200 heures admissibles certifiées requises.")
    credit = arrondir_cent(Decimal(5404) * Decimal(".14"))
    return ResultatVolontairesQuebec2025(benevoles.choix, heures, credit, min(credit, impot_disponible))


def appliquer_volontaires_quebec_2025(impot, r):
    if not r.credit_ligne_390:
        return impot
    return replace(impot, impot_quebec_preliminaire=max(impot.impot_quebec_preliminaire-r.credit_ligne_390, ZERO),
        limitations=impot.limitations+("Volontaires Québec 390 : non rémunérés, heures et admissibilité Québec confirmées; non remboursable.",))


def volontaires_vers_dict(p):
    valider_volontaires_quebec_2025(p)
    return {f.name: getattr(p, f.name) for f in fields(p)}


def volontaires_depuis_dict(v):
    if v is None:
        return VolontairesQuebec2025()
    if not isinstance(v, dict) or set(v)-{f.name for f in fields(VolontairesQuebec2025)}:
        raise ValueError("Profil volontaires Québec : JSON ou clés invalides.")
    return valider_volontaires_quebec_2025(VolontairesQuebec2025(**v))


def lignes_volontaires_quebec_2025(p, r):
    if not p.activer:
        return []
    return ["", "VOLONTAIRES QUÉBEC 2025 - LIGNE 390 (6L)",
        *wrap("Sources Québec : " + p.source, width=50),
        f"Activité : {r.activite}; heures certifiées Québec : {r.heures_admissibles:.2f}; minimum 200.",
        f"Ligne 390 : 5404 $ x 14 % = {r.credit_ligne_390:.2f} $; un seul crédit non remboursable.",
        f"Réduction d'impôt effectivement disponible à cette étape : {r.reduction_impot_effective:.2f} $; plancher zéro.",
        "Crédit Québec distinct des lignes fédérales 31220/31240; aucune addition aux crédits remboursables.",
        "Profil non rémunéré uniquement : RL-1 L-2 et T4 87 positifs refusés, aucune inclusion de revenu simulée.",
        "Les cas rémunérés exigent notamment le traitement de L-2; activité mixte, résidence partielle et autres cas exclus.",
        "Sources : Revenu Québec, ligne 390 et paramètres 2025 fournis pour l'audit de clôture."]
