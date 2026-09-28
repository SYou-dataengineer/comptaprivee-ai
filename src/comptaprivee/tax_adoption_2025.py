"""ARC 2025, ligne 31300; LIR 118.01. Admissibilité validée sur pièces."""
from dataclasses import asdict, dataclass, fields
from datetime import date
from decimal import Decimal, InvalidOperation

from .tax_rules_2025 import arrondir_cent

ZERO = Decimal("0")
PLAFOND_ADOPTION_2025 = Decimal("19580")
CATEGORIES_ADOPTION = ("agence", "judiciaire", "voyage_sejour", "traduction",
    "institution_etrangere", "immigration", "autres_obligatoires")
CONFIRMATIONS_ADOPTION = {
    "valide_par_comptable": "Identités, dates et pièces vérifiées par le comptable",
    "admissibilite_confirmee": "Adoption reconnue au Canada; organismes et frais admissibles, raisonnables et nécessaires vérifiés",
    "paiements_confirmes": "Frais engagés pendant la période et effectivement payés; aucune facture comptée deux fois",
    "aides_verifiees": "Toutes les aides reçues ou à recevoir par quiconque sont incluses; toute exception imposable est déjà incluse au revenu et non déductible",
    "partage_confirme": "Part convenue avec tous les autres demandeurs, plafond commun et absence de double demande vérifiés",
}


@dataclass(frozen=True)
class DepenseAdoption2025:
    date_engagement: str = ""
    categorie: str = ""
    montant: Decimal = ZERO
    source: str = ""


@dataclass(frozen=True)
class EnfantAdopte2025:
    nom: str = ""
    naissance: str = ""
    inscription: str = ""
    demande_cour: str = ""
    ordonnance: str = ""
    residence_permanente: str = ""
    depenses: tuple[DepenseAdoption2025, ...] = ()
    aides: Decimal = ZERO
    aides_imposables_non_deductibles: Decimal = ZERO
    part_pourcentage: Decimal = Decimal("100")
    source: str = ""


@dataclass(frozen=True)
class Adoption2025:
    enfants: tuple[EnfantAdopte2025, ...] = ()
    valide_par_comptable: bool = False
    admissibilite_confirmee: bool = False
    paiements_confirmes: bool = False
    aides_verifiees: bool = False
    partage_confirme: bool = False


@dataclass(frozen=True)
class ResultatEnfantAdopte2025:
    nom: str
    debut: str
    fin: str
    depenses: Decimal
    aides_deductibles: Decimal
    net: Decimal
    base_plafonnee: Decimal
    part_pourcentage: Decimal
    montant_31300: Decimal
    reste_autres_demandeurs: Decimal


@dataclass(frozen=True)
class ResultatAdoption2025:
    enfants: tuple[ResultatEnfantAdopte2025, ...] = ()
    montant_31300: Decimal = ZERO


def _montant(v, nom):
    if not isinstance(v, Decimal) or not v.is_finite() or v < ZERO:
        raise ValueError(f"{nom} doit être un Decimal fini non négatif.")
    try:
        if arrondir_cent(v) != v:
            raise ValueError(f"{nom} doit avoir au plus deux décimales.")
    except ArithmeticError as erreur:
        raise ValueError(f"{nom} dépasse la capacité du calcul.") from erreur
    return v


def _date(v, nom):
    if not isinstance(v, str):
        raise ValueError(f"{nom} : date attendue au format AAAA-MM-JJ.")
    try:
        resultat = date.fromisoformat(v)
        if resultat.isoformat() != v:
            raise ValueError()
        return resultat
    except ValueError as erreur:
        raise ValueError(f"{nom} : date invalide, format AAAA-MM-JJ requis.") from erreur


def calculer_enfants_adoptes_2025(enfants):
    """Validation des lignes avant confirmation du profil dans l'interface."""
    if type(enfants) is not tuple:
        raise ValueError("Les enfants adoptés doivent former un tuple immuable.")
    resultats, identites, pieces = [], set(), set()
    for e in enfants:
        if not isinstance(e, EnfantAdopte2025):
            raise ValueError("Enfant adopté invalide.")
        for nom in ("nom", "source"):
            if not isinstance(getattr(e, nom), str) or not getattr(e, nom).strip():
                raise ValueError("Champ obligatoire de l'adoption : " + nom)
        naissance = _date(e.naissance, "Naissance")
        cle = (" ".join(e.nom.split()).casefold(), naissance)
        if cle in identites:
            raise ValueError("Le même enfant est compté deux fois.")
        identites.add(cle)
        debut_dates = []
        for nom in ("inscription", "demande_cour"):
            v = getattr(e, nom)
            if v != "":
                debut_dates.append(_date(v, nom))
        if not debut_dates:
            raise ValueError("Une date d'inscription ou de demande à la cour est obligatoire.")
        debut = min(debut_dates)
        ordonnance = _date(e.ordonnance, "Ordonnance reconnue au Canada")
        residence = _date(e.residence_permanente, "Résidence permanente avec le demandeur")
        fin = max(ordonnance, residence)
        age = ordonnance.year - naissance.year - ((ordonnance.month, ordonnance.day) < (naissance.month, naissance.day))
        if naissance > min(ordonnance, residence) or age >= 18:
            raise ValueError("L'enfant doit être né et avoir moins de 18 ans à l'ordonnance.")
        if max(debut_dates) > fin or fin.year != 2025:
            raise ValueError("La période d'adoption doit être cohérente et se terminer en 2025.")
        if type(e.depenses) is not tuple or not e.depenses:
            raise ValueError("Des dépenses d'adoption documentées sont obligatoires.")
        total = ZERO
        for d in e.depenses:
            if not isinstance(d, DepenseAdoption2025):
                raise ValueError("Dépense d'adoption invalide.")
            if not isinstance(d.categorie, str) or d.categorie not in CATEGORIES_ADOPTION:
                raise ValueError("Catégorie de dépense d'adoption invalide.")
            if not isinstance(d.source, str) or not d.source.strip():
                raise ValueError("La source de chaque dépense est obligatoire.")
            engagement = _date(d.date_engagement, "Engagement de la dépense")
            if not debut <= engagement <= fin:
                raise ValueError("La dépense doit être engagée dans la période d'adoption.")
            if _montant(d.montant, "Dépense") == ZERO:
                raise ValueError("La dépense doit être positive.")
            # Référence de ligne unique, y compris pour une facture ventilée entre enfants.
            reference = " ".join(d.source.split()).casefold()
            if reference in pieces:
                raise ValueError("Pièce comptée deux fois : utiliser une référence distincte pour chaque portion justifiée.")
            pieces.add(reference)
            total += d.montant
        aides = _montant(e.aides, "Aides reçues ou à recevoir")
        exception = _montant(e.aides_imposables_non_deductibles, "Part imposable non déductible des aides")
        part = _montant(e.part_pourcentage, "Part convenue en pourcentage")
        if exception > aides or part > 100:
            raise ValueError("L'exception ne peut dépasser les aides; la part doit être comprise entre 0 et 100 %.")
        reduction = aides - exception
        net = max(total - reduction, ZERO)
        base = min(PLAFOND_ADOPTION_2025, net)
        montant = arrondir_cent(base * part / 100)
        resultats.append(ResultatEnfantAdopte2025(e.nom, debut.isoformat(), fin.isoformat(), total,
            reduction, net, base, part, montant, base - montant))
    return ResultatAdoption2025(tuple(resultats), sum((r.montant_31300 for r in resultats), ZERO))


def calculer_adoption_2025(p, annee=2025):
    if not isinstance(p, Adoption2025):
        raise ValueError("Profil d'adoption invalide.")
    for nom in CONFIRMATIONS_ADOPTION:
        if type(getattr(p, nom)) is not bool:
            raise ValueError("Confirmation d'adoption non booléenne : " + nom)
        if p.enfants and not getattr(p, nom):
            raise ValueError("Confirmation obligatoire : " + CONFIRMATIONS_ADOPTION[nom])
    if p.enfants and annee != 2025:
        raise ValueError("Ce profil d'adoption concerne uniquement 2025.")
    return calculer_enfants_adoptes_2025(p.enfants)


def adoption_vers_dict(p):
    brut = asdict(p)
    brut["enfants"] = []
    for e in p.enfants:
        v = asdict(e)
        for nom in ("aides", "aides_imposables_non_deductibles", "part_pourcentage"):
            v[nom] = format(getattr(e, nom), ".2f")
        v["depenses"] = [dict(asdict(d), montant=format(d.montant, ".2f")) for d in e.depenses]
        brut["enfants"].append(v)
    return brut


def verifier_partage_adoption_2025(p, autre):
    """Rapproche les demandes quand le dossier brut du conjoint est disponible."""
    a, b = calculer_adoption_2025(p), calculer_adoption_2025(autre)
    normaliser = lambda e: (" ".join(e.nom.split()).casefold(), e.naissance)
    autres = {normaliser(e): r for e, r in zip(autre.enfants, b.enfants)}
    for e, r in zip(p.enfants, a.enfants):
        s = autres.get(normaliser(e))
        if s is not None and r.montant_31300 + s.montant_31300 > max(r.base_plafonnee, s.base_plafonnee):
            raise ValueError("Les demandes d'adoption des deux conjoints dépassent le maximum commun de l'enfant.")


def adoption_depuis_dict(valeur, annee=2025):
    def champs(v, classe):
        if not isinstance(v, dict) or set(v) - {f.name for f in fields(classe)}:
            raise ValueError("Champs d'adoption enregistrés invalides.")
        return dict(v)
    def liste(v):
        if not isinstance(v, list):
            raise ValueError("Une liste d'adoption est attendue.")
        return v
    def decimal(v):
        if not isinstance(v, (str, int)) or isinstance(v, bool):
            raise ValueError("Montant d'adoption enregistré invalide.")
        try:
            return _montant(Decimal(v), "Montant enregistré")
        except (InvalidOperation, ValueError) as erreur:
            raise ValueError("Montant d'adoption enregistré invalide.") from erreur
    brut = {} if valeur is None else champs(valeur, Adoption2025)
    enfants = []
    for e in liste(brut.get("enfants", [])):
        v = champs(e, EnfantAdopte2025)
        depenses = []
        for d in liste(v.get("depenses", [])):
            frais = champs(d, DepenseAdoption2025)
            frais["montant"] = decimal(frais.get("montant", "0"))
            depenses.append(DepenseAdoption2025(**frais))
        v["depenses"] = tuple(depenses)
        for nom, defaut in (("aides", "0"), ("aides_imposables_non_deductibles", "0"), ("part_pourcentage", "100")):
            v[nom] = decimal(v.get(nom, defaut))
        enfants.append(EnfantAdopte2025(**v))
    brut["enfants"] = tuple(enfants)
    p = Adoption2025(**brut)
    calculer_adoption_2025(p, annee)
    return p


def lignes_adoption_2025(p, r):
    if not p.enfants:
        return []
    lignes = ["", "FRAIS D'ADOPTION — BLOC 5M — LIGNE 31300", "Validation comptable, admissibilité, aides et partage confirmés"]
    for e, v in zip(p.enfants, r.enfants):
        lignes += [f"{e.nom} : période du {v.debut} au {v.fin}; source : {e.source}"]
        for d in e.depenses:
            lignes.append(f"{d.date_engagement} — {d.categorie} : {d.montant:.2f} $; source : {d.source}")
        lignes += [f"Dépenses {v.depenses:.2f} $; aides {e.aides:.2f} $ dont exception imposable non déductible {e.aides_imposables_non_deductibles:.2f} $",
            f"Net {v.net:.2f} $; plafond 19 580 $ : {v.base_plafonnee:.2f} $; part {v.part_pourcentage:.2f} %",
            f"Ligne 31300 : {v.montant_31300:.2f} $; maximum restant pour les autres demandeurs : {v.reste_autres_demandeurs:.2f} $"]
    lignes += [f"Total ligne 31300 : {r.montant_31300:.2f} $; inclus dans 33500 avant la scolarité.",
        "Aucun revenu modifié; crédit Québec à traiter séparément."]
    return lignes
