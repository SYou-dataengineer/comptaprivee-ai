"""Annexe H 2025, aide continue déjà accomplie, sans relève ni décès."""
from dataclasses import dataclass, fields
from datetime import date
from decimal import Decimal, InvalidOperation
from .tax_rules_2025 import arrondir_cent

ZERO = Decimal(0)
MODES_AIDANTE = ("déficience avec cohabitation", "déficience sans cohabitation", "70 ans avec cohabitation")
LIENS_ASCENDANTS = ("parent", "grand-parent", "oncle ou tante", "grand-oncle ou grand-tante", "autre ascendant direct")
LIENS_AIDANTE = ("conjoint", "enfant", "petit-enfant", "neveu ou nièce", "frère ou sœur", *LIENS_ASCENDANTS, "sans lien familial")
CONFIRMATIONS_6G = {
    "residence_confirmee": "Demandeur résident Québec au 31 décembre; personnes aidées résidentes du Canada pendant toute la période et logement principal au Québec",
    "habitation_confirmee": "Aucune résidence privée pour aînés ni installation du réseau public; habitation détenue ou louée par une personne autorisée en cas de cohabitation",
    "liens_confirmes": "Identités, dates de naissance et liens familiaux du demandeur ou de son conjoint vérifiés",
    "attestations_confirmees": "Pour les modes déficience : déficience grave et prolongée et besoin d'assistance attestés au Québec; attestation d'assistance soutenue valide si sans lien familial. Sans objet au volet 70 ans ou sans personne aidée",
    "periodes_confirmees": "Aide ou cohabitation continue réellement accomplie pendant les dates saisies; aucune période future présumée",
    "absence_remuneration_confirmee": "Aucune rémunération pour l'aide; demandeur et conjoint non exonérés d'impôt",
    "absence_demande_pour_soi_confirmee": "Personne ne réclame le crédit aidant pour le demandeur; sauf conjoint, personne ne réclame pour lui les lignes 367, 378 ou 381",
    "partage_confirme": "Parts convenues et autres aidants identifiés sur pièces; chaque aidant remplit personnellement les conditions de période complète de ce profil, sans rotation",
    "exclusions_confirmees": "Aucun décès, service de relève ni rajustement d'assistance sociale pour enfant majeur handicapé aux études secondaires",
    "avances_confirmees": "Tous les versements anticipés personnels RL-19 case H vérifiés, même supérieurs au crédit",
    "valide_par_comptable": "Faits, admissibilité, sources et limites validés par le comptable",
}


@dataclass(frozen=True)
class PersonneAideeQuebec2025:
    reference: str = ""
    nom: str = ""
    naissance: str = ""
    mode: str = MODES_AIDANTE[0]
    lien: str = "parent"
    debut: str = ""
    fin: str = ""
    adresse: str = ""
    revenu_net: Decimal = ZERO
    credit_autres: Decimal = ZERO
    source: str = ""


@dataclass(frozen=True)
class PersonneAidanteQuebec2025:
    reclamer: bool = False
    personnes: tuple[PersonneAideeQuebec2025, ...] = ()
    avances_rl19_h: Decimal = ZERO
    source: str = ""
    residence_confirmee: bool = False
    habitation_confirmee: bool = False
    liens_confirmes: bool = False
    attestations_confirmees: bool = False
    periodes_confirmees: bool = False
    absence_remuneration_confirmee: bool = False
    absence_demande_pour_soi_confirmee: bool = False
    partage_confirme: bool = False
    exclusions_confirmees: bool = False
    avances_confirmees: bool = False
    valide_par_comptable: bool = False


def identite_aidante(v):
    return " ".join(v.split()).casefold()


def montant_aidante(v, nom="montant"):
    if (not isinstance(v, Decimal) or not v.is_finite() or not ZERO <= v <= Decimal("999999999.99")
            or v != arrondir_cent(v)):
        raise ValueError("Montant personne aidante Québec invalide : " + nom)
    return v


def montant_aidante_depuis_champ(v):
    if not isinstance(v, str):
        raise ValueError("Personne aidante : montant décimal en texte requis.")
    try:
        return montant_aidante(Decimal(v.strip().replace(" ", "").replace(",", ".") or "0"))
    except InvalidOperation as erreur:
        raise ValueError("Montant personne aidante illisible.") from erreur


def _date(v):
    try:
        d = date.fromisoformat(v)
        if d.isoformat() != v:
            raise ValueError()
        return d
    except (ValueError, TypeError) as erreur:
        raise ValueError("Date personne aidante invalide : AAAA-MM-JJ requis.") from erreur


def _types(p):
    for f in fields(p):
        v = getattr(p, f.name)
        if isinstance(f.default, Decimal):
            montant_aidante(v, f.name)
        elif f.name != "personnes" and type(v) is not type(f.default):
            raise ValueError("Type personne aidante invalide : " + f.name)
        if isinstance(v, str) and (len(v) > 2000 or any(ord(c) < 32 for c in v)):
            raise ValueError("Texte personne aidante invalide : " + f.name)


def valider_personne_aidee_quebec_2025(e):
    if not isinstance(e, PersonneAideeQuebec2025):
        raise ValueError("Fiche personne aidée invalide.")
    _types(e)
    if any(not getattr(e, n).strip() for n in ("reference", "nom", "source")):
        raise ValueError("Référence, identité et sources personne aidée obligatoires.")
    if e.mode not in MODES_AIDANTE or e.lien not in LIENS_AIDANTE:
        raise ValueError("Mode ou lien familial personne aidée inconnu.")
    naissance, debut, fin = _date(e.naissance), _date(e.debut), _date(e.fin)
    if naissance > date(2007, 12, 31):
        raise ValueError("La personne aidée doit avoir au moins 18 ans fin 2025.")
    if e.mode == MODES_AIDANTE[2] and (naissance > date(1955, 12, 31) or e.lien not in LIENS_ASCENDANTS):
        raise ValueError("Volet 70 ans : âge ou lien familial inadmissible; conjoint exclu.")
    if e.mode != MODES_AIDANTE[1] and not e.adresse.strip():
        raise ValueError("Adresse de cohabitation obligatoire.")
    if e.mode == MODES_AIDANTE[1] and e.adresse:
        raise ValueError("Adresse de cohabitation présente en mode sans cohabitation.")
    jours_2025 = (min(fin, date(2025, 12, 31)) - max(debut, date(2025, 1, 1))).days + 1
    if (debut.year not in (2024, 2025) or fin > date(2026, 7, 1)
            or (fin - debut).days + 1 < 365 or jours_2025 < 183):
        raise ValueError("Période hors du profil : 365 jours consécutifs dont 183 en 2025; rotations à traiter séparément.")
    return e


def valider_aidante_quebec_2025(p):
    if not isinstance(p, PersonneAidanteQuebec2025) or type(p.personnes) is not tuple:
        raise ValueError("Profil ou liste des personnes aidées invalide.")
    _types(p)
    if not p.reclamer:
        if p.personnes or p.avances_rl19_h or p.source:
            raise ValueError("Activez le profil personne aidante ou effacez ses données.")
        return p
    if not p.source.strip():
        raise ValueError("Source du dossier et des avances personne aidante obligatoire.")
    refs, noms = set(), set()
    for e in p.personnes:
        valider_personne_aidee_quebec_2025(e)
        ref, nom = identite_aidante(e.reference), (identite_aidante(e.nom), e.naissance)
        if ref in refs or nom in noms:
            raise ValueError("Personne aidée dupliquée : référence ou identité.")
        refs.add(ref); noms.add(nom)
    if sum(e.lien == "conjoint" for e in p.personnes) > 1:
        raise ValueError("Plusieurs conjoints dans le profil personne aidante.")
    for nom, libelle in CONFIRMATIONS_6G.items():
        if not getattr(p, nom):
            raise ValueError("Confirmation obligatoire : " + libelle)
    return p


@dataclass(frozen=True)
class ResultatPersonneAideeQuebec2025:
    maximum: Decimal
    reduction_revenu: Decimal
    reduction_18_ans: Decimal
    disponible: Decimal
    credit: Decimal


@dataclass(frozen=True)
class ResultatAidanteQuebec2025:
    personnes: tuple[ResultatPersonneAideeQuebec2025, ...] = ()
    credit_ligne_462: Decimal = ZERO
    avances_ligne_441: Decimal = ZERO


def calculer_aidante_quebec_2025(p, *, demandeur=""):
    valider_aidante_quebec_2025(p)
    if not p.reclamer:
        return ResultatAidanteQuebec2025()
    resultats = []
    for e in p.personnes:
        if demandeur and identite_aidante(e.nom) == identite_aidante(demandeur):
            raise ValueError("La personne aidée doit différer du demandeur.")
        maximum = Decimal(2988 if e.mode == MODES_AIDANTE[0] else 1494)
        reduction = (ZERO if e.mode == MODES_AIDANTE[2] else
            min(Decimal(1494), arrondir_cent(max(e.revenu_net - Decimal(26520), ZERO) * Decimal(".16"))))
        apres_revenu = maximum - reduction
        naissance = _date(e.naissance)
        reduction_age = (arrondir_cent(apres_revenu * naissance.month / 12) if naissance.year == 2007 else ZERO)
        disponible = max(apres_revenu - reduction_age, ZERO)
        if e.credit_autres > disponible:
            raise ValueError("La part des autres aidants dépasse le crédit disponible pour cette personne.")
        resultats.append(ResultatPersonneAideeQuebec2025(maximum, reduction, reduction_age, disponible, disponible - e.credit_autres))
    return ResultatAidanteQuebec2025(tuple(resultats), sum((r.credit for r in resultats), ZERO), p.avances_rl19_h)


def aidante_quebec_vers_dict(p):
    valider_aidante_quebec_2025(p)
    def valeur(v):
        return str(v) if isinstance(v, Decimal) else v
    return {f.name: ([{c.name: valeur(getattr(e, c.name)) for c in fields(e)} for e in p.personnes]
        if f.name == "personnes" else valeur(getattr(p, f.name))) for f in fields(p)}


def verifier_aidante_conjoint_2025(p, r, *, demandeur, conjoint):
    autre = conjoint.aidante_quebec_conjoint
    if not p.reclamer or not autre.reclamer:
        return
    if any(identite_aidante(e.nom) == identite_aidante(demandeur) for e in autre.personnes):
        raise ValueError("Le conjoint réclame le crédit personne aidante pour le demandeur lui-même.")
    if any(identite_aidante(e.nom) == identite_aidante(conjoint.nom_conjoint) for e in p.personnes):
        raise ValueError("La personne aidée réclame elle-même le crédit aidant dans son dossier conjoint.")
    autre_resultat = calculer_aidante_quebec_2025(autre)
    for e, t in zip(p.personnes, r.personnes):
        for a, u in zip(autre.personnes, autre_resultat.personnes):
            if (identite_aidante(e.nom), e.naissance) == (identite_aidante(a.nom), a.naissance):
                if e.mode != a.mode or e.revenu_net != a.revenu_net:
                    raise ValueError("Même personne aidée : mode ou revenu divergent entre les dossiers conjoints.")
                if e.credit_autres < u.credit or a.credit_autres < t.credit or t.credit + u.credit > t.disponible:
                    raise ValueError("Parts des aidants divergentes entre les dossiers conjoints.")


def aidante_quebec_depuis_dict(v):
    if v is None:
        return PersonneAidanteQuebec2025()
    if not isinstance(v, dict) or set(v) - {f.name for f in fields(PersonneAidanteQuebec2025)}:
        raise ValueError("Profil personne aidante ou clés inconnues invalides.")
    valeurs = dict(v)
    if "avances_rl19_h" in valeurs:
        valeurs["avances_rl19_h"] = montant_aidante_depuis_champ(valeurs["avances_rl19_h"])
    personnes = valeurs.get("personnes", [])
    if not isinstance(personnes, list):
        raise ValueError("Personnes aidées : liste JSON requise.")
    sorties = []
    for brut in personnes:
        if not isinstance(brut, dict) or set(brut) - {f.name for f in fields(PersonneAideeQuebec2025)}:
            raise ValueError("Fiche personne aidée ou clés inconnues invalides.")
        e = dict(brut)
        for nom in ("revenu_net", "credit_autres"):
            if nom in e: e[nom] = montant_aidante_depuis_champ(e[nom])
        sorties.append(PersonneAideeQuebec2025(**e))
    valeurs["personnes"] = tuple(sorties)
    return valider_aidante_quebec_2025(PersonneAidanteQuebec2025(**valeurs))


def lignes_aidante_quebec_2025(p, r):
    if not p.reclamer:
        return []
    lignes = ["", "PERSONNE AIDANTE QUÉBEC — ANNEXE H / LIGNE 462",
        f"Source du dossier/RL-19 : {p.source}; validation comptable confirmée."]
    for e, t in zip(p.personnes, r.personnes):
        lignes.extend([f"{e.reference} — {e.nom}, naissance {e.naissance}; lien : {e.lien}; {e.mode}",
            f"Période continue : {e.debut} au {e.fin}; habitation : {e.adresse or 'sans cohabitation'}; source : {e.source}",
            f"Revenu net de la personne aidée : {e.revenu_net:.2f} $; maximum : {t.maximum:.2f} $",
            f"Réduction revenu = min(1494, max(275 - 26520, 0) × 16 %) : {t.reduction_revenu:.2f} $ (aucune au volet 70 ans)",
            f"Réduction 18 ans, mois anniversaire inclus : {t.reduction_18_ans:.2f} $; disponible : {t.disponible:.2f} $",
            f"Part convenue des autres aidants : {e.credit_autres:.2f} $; crédit propre : {t.credit:.2f} $"])
    lignes.extend([f"Crédit remboursable 462 = somme des parts propres : {r.credit_ligne_462:.2f} $",
        f"Avances personnelles RL-19 H, ligne 441 : {r.avances_ligne_441:.2f} $; intégrales même si supérieures au crédit",
        "Aucun effet sur le revenu ou les impôts de base. Rotations entre aidants, décès, relève et rajustements d'assistance sociale hors de ce profil."])
    return lignes
