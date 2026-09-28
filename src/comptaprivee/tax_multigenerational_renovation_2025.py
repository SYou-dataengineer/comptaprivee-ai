"""Annexe 12 fédérale 2025 : rénovations multigénérationnelles, 45354/45355.

Sources : LIR 122.92; L.C. 2022, ch. 19, art. 19(2); annexe 5000-S12 E (25).
Les faits d'admissibilité et les pièces exigent une validation comptable.
"""
from dataclasses import asdict, dataclass, fields
from datetime import date
from decimal import Decimal, InvalidOperation

from .tax_rules_2025 import arrondir_cent

ZERO = Decimal("0")
PLAFOND_RENOVATION = Decimal("50000")
TAUX_MULTIGENERATIONNEL = Decimal("0.145")
LIENS_PROCHE = ("parent", "grand-parent", "enfant", "petit-enfant", "frère ou sœur",
                "oncle ou tante", "neveu ou nièce")
ROLES_DEMANDEUR = ("particulier déterminé occupant", "conjoint occupant",
                   "proche occupant", "proche propriétaire")
CONFIRMATIONS_RENOVATION = {
    "valide_par_comptable": "Faits, dépenses, aides et pièces vérifiés par le comptable",
    "logement_admissible": "Logement au Canada, terrain admissible, propriété en 2025 du particulier déterminé ou d'un proche admissible (ou de leur fiducie)",
    "occupation_confirmee": "Le particulier déterminé et le proche indiqué habitent normalement le logement ou devraient raisonnablement l'habiter dans les 12 mois de la fin des travaux",
    "unite_conforme": "Création d'un logement secondaire autonome avec entrée privée, cuisine, salle de bain et espace de couchage, conforme aux exigences locales",
    "travaux_admissibles": "Rénovation durable et intégrante permettant la cohabitation; fin des travaux en 2025 attestée",
    "demandeur_admissible": "Rôle du demandeur vérifié : occupation attendue sous 12 mois, ou proche admissible propriétaire/bénéficiaire de la fiducie propriétaire",
    "historique_verifie": "Aucune autre rénovation réclamée à vie pour le particulier déterminé; même rénovation et autres demandes rapprochées",
    "depenses_verifiees": "Dépenses raisonnables propres au demandeur, engagées avant la fin des travaux; biens/services et paiements après 2022; exclusions et aides reçues ou à recevoir vérifiées",
    "aucun_double_credit": "Aucune portion réclamée ici n'est réclamée comme frais médicaux fédéraux ou pour l'accessibilité domiciliaire par quiconque",
    "partage_confirme": "Accord de partage vérifié; toutes les bases réclamées par les autres personnes admissibles sont indiquées",
}


@dataclass(frozen=True)
class DepenseRenovation2025:
    date_piece: str = ""
    date_bien_service: str = ""
    date_paiement: str = ""
    fournisseur: str = ""
    description: str = ""
    montant: Decimal = ZERO
    aide: Decimal = ZERO
    fournisseur_lie: bool = False
    numero_tps: str = ""
    source: str = ""


@dataclass(frozen=True)
class PartAutreDemandeur2025:
    personne: str = ""
    base_reclamee: Decimal = ZERO
    source: str = ""


@dataclass(frozen=True)
class RenovationMultigenerationnelle2025:
    logement: str = ""
    unite: str = ""
    particulier: str = ""
    naissance_particulier: str = ""
    ciph_admissible: bool = False
    source_ciph: str = ""
    proche: str = ""
    naissance_proche: str = ""
    lien_proche: str = ""
    lien_avec_conjoint: bool = False
    role_demandeur: str = ""
    source_role: str = ""
    date_fin: str = ""
    source: str = ""
    attribution_fiducie: bool = False
    source_attribution: str = ""
    depenses: tuple[DepenseRenovation2025, ...] = ()
    autres_demandes: tuple[PartAutreDemandeur2025, ...] = ()
    valide_par_comptable: bool = False
    logement_admissible: bool = False
    occupation_confirmee: bool = False
    unite_conforme: bool = False
    travaux_admissibles: bool = False
    demandeur_admissible: bool = False
    historique_verifie: bool = False
    depenses_verifiees: bool = False
    aucun_double_credit: bool = False
    partage_confirme: bool = False


@dataclass(frozen=True)
class RenovationsMultigenerationnelles2025:
    renovations: tuple[RenovationMultigenerationnelle2025, ...] = ()
    resident_annee_complete: bool = False
    profil_ordinaire: bool = False
    rapprochement_medical_accessibilite: str = ""


@dataclass(frozen=True)
class ResultatRenovation2025:
    depenses: Decimal
    aides: Decimal
    depenses_nettes: Decimal
    autres_demandes: Decimal
    plafond_disponible: Decimal
    base_retenue: Decimal


@dataclass(frozen=True)
class ResultatMultigenerationnel2025:
    renovations: tuple[ResultatRenovation2025, ...] = ()
    ligne_45354: Decimal = ZERO
    ligne_45355: Decimal = ZERO


def _cle(texte):
    return " ".join(texte.split()).casefold()


def _texte(v, nom, *, obligatoire=True):
    if not isinstance(v, str) or (obligatoire and not v.strip()):
        raise ValueError(f"Texte requis ou invalide : {nom}.")


def _booleen(v, nom):
    if type(v) is not bool:
        raise ValueError(f"Valeur booléenne requise : {nom}.")


def _date(v, nom):
    _texte(v, nom)
    try:
        jour = date.fromisoformat(v)
        if jour.isoformat() != v:
            raise ValueError()
    except ValueError as erreur:
        raise ValueError(f"Date AAAA-MM-JJ requise : {nom}.") from erreur
    return jour


def montant_multigenerationnel_2025(v, nom):
    if not isinstance(v, Decimal) or not v.is_finite() or v < ZERO:
        raise ValueError(f"{nom} doit être un Decimal fini non négatif.")
    try:
        if v != arrondir_cent(v):
            raise ValueError(f"{nom} exige au plus deux décimales.")
    except ArithmeticError as erreur:
        raise ValueError(f"{nom} dépasse la capacité du calcul.") from erreur
    return v


def calculer_renovation_multigenerationnelle_2025(p):
    if not isinstance(p, RenovationMultigenerationnelle2025):
        raise ValueError("Profil de rénovation invalide.")
    for nom in ("logement", "unite", "particulier", "proche", "lien_proche", "role_demandeur", "source_role", "source"):
        _texte(getattr(p, nom), nom)
    for nom in ("source_ciph", "source_attribution"):
        _texte(getattr(p, nom), nom, obligatoire=False)
    for nom in (*CONFIRMATIONS_RENOVATION, "ciph_admissible", "lien_avec_conjoint", "attribution_fiducie"):
        _booleen(getattr(p, nom), nom)
    for nom, libelle in CONFIRMATIONS_RENOVATION.items():
        if not getattr(p, nom):
            raise ValueError("Confirmation obligatoire : " + libelle)
    fin = _date(p.date_fin, "Fin des travaux")
    if fin.year != 2025:
        raise ValueError("Les travaux doivent être terminés en 2025.")
    naissance = _date(p.naissance_particulier, "Naissance du particulier déterminé")
    age = 2025 - naissance.year
    if age < 18 or (age < 65 and not p.ciph_admissible):
        raise ValueError("Particulier déterminé : 65 ans ou plus, ou adulte admissible au CIPH en 2025.")
    if p.ciph_admissible != bool(p.source_ciph.strip()):
        raise ValueError("La source du CIPH doit correspondre à son statut admissible.")
    if _date(p.naissance_proche, "Naissance du proche").year > 2007 or p.lien_proche not in LIENS_PROCHE:
        raise ValueError("Le proche occupant doit être adulte fin 2025 et avoir un lien familial admissible.")
    if _cle(p.particulier) == _cle(p.proche):
        raise ValueError("Le particulier déterminé et le proche sont deux personnes distinctes.")
    if p.role_demandeur not in ROLES_DEMANDEUR:
        raise ValueError("Rôle du demandeur non admissible.")
    if p.attribution_fiducie != bool(p.source_attribution.strip()):
        raise ValueError("Une attribution de fiducie exige sa notification et sa ventilation documentées.")
    if type(p.depenses) is not tuple or not p.depenses:
        raise ValueError("Une rénovation exige un tuple non vide de dépenses.")
    sources = set()
    total, aides = ZERO, ZERO
    for d in p.depenses:
        if not isinstance(d, DepenseRenovation2025):
            raise ValueError("Dépense de rénovation invalide.")
        for nom in ("fournisseur", "description", "source"):
            _texte(getattr(d, nom), nom)
        _texte(d.numero_tps, "Numéro TPS/TVH", obligatoire=False)
        _booleen(d.fournisseur_lie, "Fournisseur lié")
        if d.fournisseur_lie and not d.numero_tps.strip():
            raise ValueError("Un fournisseur lié doit être inscrit à la TPS/TVH; référence obligatoire.")
        # À la date de fin, le comptable confirme que l'engagement précède
        # l'achèvement effectif : une date seule ne donne pas l'heure.
        if _date(d.date_piece, "Date de pièce/contrat") > fin:
            raise ValueError("La pièce établissant la dépense doit précéder la fin des travaux.")
        if not date(2023, 1, 1) <= _date(d.date_bien_service, "Bien/service") <= fin:
            raise ValueError("Bien/service acquis après 2022 et au plus tard à la fin des travaux requis.")
        if _date(d.date_paiement, "Paiement") < date(2023, 1, 1):
            raise ValueError("Paiement après 2022 requis.")
        montant_multigenerationnel_2025(d.montant, "Dépense")
        montant_multigenerationnel_2025(d.aide, "Aide")
        if d.montant <= ZERO or d.aide > d.montant:
            raise ValueError("Dépense positive requise; aide limitée à cette dépense.")
        if _cle(d.source) in sources:
            raise ValueError("Même pièce ou portion de dépense réclamée plusieurs fois.")
        sources.add(_cle(d.source))
        total += d.montant
        aides += d.aide
    if type(p.autres_demandes) is not tuple:
        raise ValueError("Les autres demandes doivent former un tuple.")
    personnes, autres = set(), ZERO
    for a in p.autres_demandes:
        if not isinstance(a, PartAutreDemandeur2025):
            raise ValueError("Part d'un autre demandeur invalide.")
        _texte(a.personne, "Autre demandeur")
        _texte(a.source, "Source de partage")
        montant_multigenerationnel_2025(a.base_reclamee, "Base réclamée par l'autre demandeur")
        if _cle(a.personne) in personnes:
            raise ValueError("Autre demandeur indiqué plusieurs fois.")
        personnes.add(_cle(a.personne))
        autres += a.base_reclamee
    if autres > PLAFOND_RENOVATION:
        raise ValueError("Les bases des autres demandes dépassent le plafond de 50 000 $.")
    net = montant_multigenerationnel_2025(total - aides, "Dépenses nettes")
    disponible = PLAFOND_RENOVATION - autres
    return ResultatRenovation2025(total, aides, net, autres, disponible, min(net, disponible))


def calculer_multigenerationnel_2025(p, *, annee=2025, autres_frais_reclames=False):
    if not isinstance(p, RenovationsMultigenerationnelles2025) or type(p.renovations) is not tuple:
        raise ValueError("Profil multigénérationnel invalide.")
    for nom in ("resident_annee_complete", "profil_ordinaire"):
        _booleen(getattr(p, nom), nom)
    _booleen(autres_frais_reclames, "Présence de frais médicaux ou d'accessibilité")
    _texte(p.rapprochement_medical_accessibilite, "Rapprochement des frais", obligatoire=False)
    if not p.renovations:
        if p.rapprochement_medical_accessibilite.strip():
            raise ValueError("Un profil sans rénovation doit être vide.")
        return ResultatMultigenerationnel2025()
    if annee != 2025 or not p.resident_annee_complete or not p.profil_ordinaire:
        raise ValueError("Profil 2025 résident toute l'année, sans faillite ni décès requis; les cas spéciaux ne sont pas encore couverts.")
    if autres_frais_reclames and not p.rapprochement_medical_accessibilite.strip():
        raise ValueError("Frais médicaux/accessibilité présents : rapprochement documenté des dépenses distinctes obligatoire.")
    resultats, personnes, logements, sources = [], set(), set(), set()
    for renovation in p.renovations:
        resultat = calculer_renovation_multigenerationnelle_2025(renovation)
        personne = _cle(renovation.particulier)
        logement = (_cle(renovation.logement), _cle(renovation.unite))
        if personne in personnes or logement in logements:
            raise ValueError("Une seule rénovation par particulier déterminé et par logement secondaire; plafond commun à regrouper.")
        personnes.add(personne)
        logements.add(logement)
        for d in renovation.depenses:
            if _cle(d.source) in sources:
                raise ValueError("Même pièce ou portion utilisée dans plusieurs rénovations.")
            sources.add(_cle(d.source))
        resultats.append(resultat)
    base = montant_multigenerationnel_2025(sum((r.base_retenue for r in resultats), ZERO), "Ligne 45354")
    return ResultatMultigenerationnel2025(tuple(resultats), base, arrondir_cent(base * TAUX_MULTIGENERATIONNEL))


def multigenerationnel_vers_dict(p):
    def convertir(v):
        if isinstance(v, Decimal):
            return format(v, ".2f")
        if isinstance(v, dict):
            return {k: convertir(x) for k, x in v.items()}
        if isinstance(v, (tuple, list)):
            return [convertir(x) for x in v]
        return v
    calculer_multigenerationnel_2025(p)
    return convertir(asdict(p))


def multigenerationnel_depuis_dict(valeur, *, annee=2025, autres_frais_reclames=False):
    enfants = {RenovationsMultigenerationnelles2025: {"renovations": RenovationMultigenerationnelle2025},
               RenovationMultigenerationnelle2025: {"depenses": DepenseRenovation2025, "autres_demandes": PartAutreDemandeur2025}}
    def lire(v, classe):
        if not isinstance(v, dict) or set(v) - {f.name for f in fields(classe)}:
            raise ValueError("Champs multigénérationnels enregistrés invalides.")
        v = dict(v)
        for nom, enfant in enfants.get(classe, {}).items():
            lignes = v.get(nom, [])
            if not isinstance(lignes, list):
                raise ValueError("Liste multigénérationnelle enregistrée invalide.")
            v[nom] = tuple(lire(x, enfant) for x in lignes)
        for champ in fields(classe):
            if champ.type is Decimal:
                x = v.get(champ.name, "0")
                if not isinstance(x, (str, int)) or isinstance(x, bool):
                    raise ValueError("Montant multigénérationnel enregistré invalide.")
                try:
                    v[champ.name] = montant_multigenerationnel_2025(Decimal(x), champ.name)
                except (InvalidOperation, ValueError) as erreur:
                    raise ValueError("Montant multigénérationnel enregistré invalide.") from erreur
        return classe(**v)
    p = lire({} if valeur is None else valeur, RenovationsMultigenerationnelles2025)
    calculer_multigenerationnel_2025(p, annee=annee, autres_frais_reclames=autres_frais_reclames)
    return p


def lignes_multigenerationnelles_2025(p, r):
    if not p.renovations:
        return []
    lignes = ["", "RÉNOVATIONS MULTIGÉNÉRATIONNELLES — BLOC 5Q",
              "Admissibilité et pièces validées par le comptable; déclaration ordinaire, résidence annuelle confirmée."]
    for projet, calcul in zip(p.renovations, r.renovations):
        lignes += [f"{projet.logement} — {projet.unite}; fin : {projet.date_fin}",
            f"Particulier déterminé : {projet.particulier}; proche : {projet.proche}; rôle : {projet.role_demandeur}",
            f"Sources : {projet.source}; rôle : {projet.source_role}"]
        for d in projet.depenses:
            lignes.append(f"{d.date_piece} — {d.fournisseur} : {d.description}; payé {d.montant:.2f} $, aides {d.aide:.2f} $; pièce : {d.source}")
        for a in projet.autres_demandes:
            lignes.append(f"Autre demandeur : {a.personne}; base {a.base_reclamee:.2f} $; accord : {a.source}")
        lignes += [f"Dépenses nettes : {calcul.depenses_nettes:.2f} $; plafond disponible : 50000 - {calcul.autres_demandes:.2f} = {calcul.plafond_disponible:.2f} $",
            f"Base retenue : min(dépenses nettes, plafond disponible) = {calcul.base_retenue:.2f} $"]
        if projet.source_ciph:
            lignes.append("CIPH : " + projet.source_ciph)
        if projet.source_attribution:
            lignes.append("Attribution de fiducie : " + projet.source_attribution)
    lignes += [f"Total des bases — 45354 : {r.ligne_45354:.2f} $",
        f"Crédit remboursable — 45355 : 45354 × 14,5 % = {r.ligne_45355:.2f} $",
        "Ajout unique aux paiements; revenu, crédits non remboursables et abattement Québec inchangés."]
    if p.rapprochement_medical_accessibilite:
        lignes.append("Rapprochement médical/accessibilité : " + p.rapprochement_medical_accessibilite)
    return lignes
