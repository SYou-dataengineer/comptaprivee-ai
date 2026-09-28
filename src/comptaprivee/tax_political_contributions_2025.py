"""Contributions politiques fédérales 2025, LIR 127(3), T1 40900/41000.

Le taux légal du troisième palier est un tiers; l'arrondi est au cent.
L'admissibilité des reçus et le choix entre conjoints sont validés sur pièces.
"""
from dataclasses import asdict, dataclass, fields
from datetime import date
from decimal import Decimal, InvalidOperation

from .tax_rules_2025 import arrondir_cent

ZERO = Decimal("0")
TYPES_BENEFICIAIRES_POLITIQUES = ("parti", "association", "candidat")
CONFIRMATIONS_POLITIQUES = {
    "valide_par_comptable": "Contributions et pièces fiscales vérifiées par le comptable",
    "recus_officiels": "Reçus officiels signés par un agent autorisé; bénéficiaires fédéraux admissibles vérifiés",
    "contributions_monetaires": "Paiements monétaires personnels en 2025, hors contributions en nature et attributions de sociétés de personnes",
    "avantages_verifies": "Valeur de tous les avantages reçus ou attendus vérifiée; montant admissible rapproché des reçus",
    "aucun_double_compte": "Reçus réclamés une seule fois, exclus des dons de bienfaisance et des demandes du conjoint",
    "aucune_exclusion": "Aucun paiement en qualité d'agent ni avantage financier public exclu par la LIR 127(4.1)",
}


@dataclass(frozen=True)
class RecuPolitique2025:
    date_paiement: str = ""
    donateur: str = "contribuable"
    nom_donateur: str = ""
    beneficiaire: str = ""
    type_beneficiaire: str = ""
    montant: Decimal = ZERO
    avantage: Decimal = ZERO
    source: str = ""


@dataclass(frozen=True)
class ContributionsPolitiques2025:
    recus: tuple[RecuPolitique2025, ...] = ()
    nom_conjoint: str = ""
    source: str = ""
    valide_par_comptable: bool = False
    recus_officiels: bool = False
    contributions_monetaires: bool = False
    avantages_verifies: bool = False
    aucun_double_compte: bool = False
    aucune_exclusion: bool = False


@dataclass(frozen=True)
class ResultatContributionsPolitiques2025:
    paiements: Decimal = ZERO
    avantages: Decimal = ZERO
    ligne_40900: Decimal = ZERO
    ligne_41000: Decimal = ZERO


def montant_politique_2025(v, nom):
    if not isinstance(v, Decimal) or not v.is_finite() or v < ZERO:
        raise ValueError(f"{nom} doit être un Decimal fini non négatif.")
    try:
        if v != arrondir_cent(v):
            raise ValueError(f"{nom} doit avoir au plus deux décimales.")
    except ArithmeticError as erreur:
        raise ValueError(f"{nom} dépasse la capacité du calcul.") from erreur
    return v


def _normaliser(v):
    return " ".join(v.split()).casefold()


def credit_politique_federal_2025(total):
    total = montant_politique_2025(total, "Contributions admissibles 40900")
    if total <= 400:
        credit = total * Decimal("0.75")
    elif total <= 750:
        credit = Decimal(300) + (total - 400) * Decimal("0.50")
    else:
        credit = min(Decimal(650), Decimal(475) + (total - 750) / 3)
    return arrondir_cent(credit)


def valider_recus_politiques_2025(recus):
    if type(recus) is not tuple:
        raise ValueError("Les reçus politiques doivent former un tuple immuable.")
    vus = set()
    for r in recus:
        if not isinstance(r, RecuPolitique2025):
            raise ValueError("Reçu politique invalide.")
        for nom in ("date_paiement", "donateur", "nom_donateur", "beneficiaire", "type_beneficiaire", "source"):
            if not isinstance(getattr(r, nom), str) or not getattr(r, nom).strip():
                raise ValueError("Champ du reçu politique obligatoire : " + nom)
        if r.donateur not in ("contribuable", "conjoint") or r.type_beneficiaire not in TYPES_BENEFICIAIRES_POLITIQUES:
            raise ValueError("Donateur ou bénéficiaire politique invalide.")
        try:
            jour = date.fromisoformat(r.date_paiement)
            if jour.isoformat() != r.date_paiement or jour.year != 2025:
                raise ValueError()
        except ValueError as erreur:
            raise ValueError("Date de paiement en 2025 requise, format AAAA-MM-JJ.") from erreur
        if montant_politique_2025(r.montant, "Paiement") == ZERO:
            raise ValueError("Le paiement politique doit être positif.")
        if montant_politique_2025(r.avantage, "Avantage") > r.montant:
            raise ValueError("L'avantage ne peut pas dépasser le paiement.")
        cle = _normaliser(r.source)
        if cle in vus:
            raise ValueError("Reçu politique compté deux fois.")
        vus.add(cle)
    return recus


def calculer_contributions_politiques_2025(p, *, client=None, annee=2025):
    if not isinstance(p, ContributionsPolitiques2025):
        raise ValueError("Profil de contributions politiques invalide.")
    for nom in ("source", "nom_conjoint"):
        if not isinstance(getattr(p, nom), str):
            raise ValueError("Texte du profil politique invalide : " + nom)
    for nom in CONFIRMATIONS_POLITIQUES:
        if type(getattr(p, nom)) is not bool:
            raise ValueError("Confirmation politique non booléenne : " + nom)
        if p.recus and not getattr(p, nom):
            raise ValueError("Confirmation obligatoire : " + CONFIRMATIONS_POLITIQUES[nom])
    valider_recus_politiques_2025(p.recus)
    if not p.recus:
        if p.source.strip() or p.nom_conjoint.strip():
            raise ValueError("Le profil politique sans reçus doit être vide.")
        return ResultatContributionsPolitiques2025()
    if annee != 2025 or not p.source.strip():
        raise ValueError("Une source et l'année 2025 sont obligatoires pour ces contributions.")
    for r in p.recus:
        if r.donateur == "conjoint":
            if not p.nom_conjoint.strip() or _normaliser(r.nom_donateur) != _normaliser(p.nom_conjoint):
                raise ValueError("Le reçu doit appartenir au conjoint identifié.")
            if client is not None and _normaliser(client) == _normaliser(p.nom_conjoint):
                raise ValueError("Le contribuable et le conjoint doivent être distincts.")
        elif client is not None and _normaliser(r.nom_donateur) != _normaliser(client):
            raise ValueError("Le nom du donateur ne correspond pas au contribuable.")
    if p.nom_conjoint.strip() and not any(r.donateur == "conjoint" for r in p.recus):
        raise ValueError("Un conjoint est renseigné sans reçu de ce conjoint.")
    paiements = sum((r.montant for r in p.recus), ZERO)
    avantages = sum((r.avantage for r in p.recus), ZERO)
    total = paiements - avantages
    return ResultatContributionsPolitiques2025(paiements, avantages, total, credit_politique_federal_2025(total))


def politiques_vers_dict(p):
    brut = asdict(p)
    brut["recus"] = [dict(asdict(r), montant=format(r.montant, ".2f"), avantage=format(r.avantage, ".2f")) for r in p.recus]
    return brut


def politiques_depuis_dict(valeur, *, client=None, annee=2025):
    def champs(v, classe):
        if not isinstance(v, dict) or set(v) - {f.name for f in fields(classe)}:
            raise ValueError("Champs politiques enregistrés invalides.")
        return dict(v)
    brut = {} if valeur is None else champs(valeur, ContributionsPolitiques2025)
    recus = brut.get("recus", [])
    if not isinstance(recus, list):
        raise ValueError("La liste des reçus politiques est invalide.")
    lignes = []
    for r in recus:
        v = champs(r, RecuPolitique2025)
        for nom in ("montant", "avantage"):
            x = v.get(nom, "0")
            if not isinstance(x, (str, int)) or isinstance(x, bool):
                raise ValueError("Montant politique enregistré invalide.")
            try:
                v[nom] = montant_politique_2025(Decimal(x), nom)
            except (InvalidOperation, ValueError) as erreur:
                raise ValueError("Montant politique enregistré invalide.") from erreur
        lignes.append(RecuPolitique2025(**v))
    brut["recus"] = tuple(lignes)
    p = ContributionsPolitiques2025(**brut)
    calculer_contributions_politiques_2025(p, client=client, annee=annee)
    return p


def verifier_recus_politiques_conjoint_2025(p, autre, nom_conjoint):
    if p.nom_conjoint.strip() and _normaliser(p.nom_conjoint) != _normaliser(nom_conjoint):
        raise ValueError("Le conjoint des contributions politiques diffère du dossier importé.")
    sources = {_normaliser(r.source) for r in p.recus}
    if sources & {_normaliser(r.source) for r in autre.recus}:
        raise ValueError("Le même reçu politique est réclamé dans les deux dossiers.")


def lignes_contributions_politiques_2025(p, r, final):
    if not p.recus:
        return []
    lignes = ["", "CONTRIBUTIONS POLITIQUES FÉDÉRALES — BLOC 5N", f"Source : {p.source}; validation comptable confirmée"]
    for a in p.recus:
        lignes.append(f"{a.date_paiement} — {a.nom_donateur} ({a.donateur}) — {a.beneficiaire} ({a.type_beneficiaire}) : "
            f"{a.montant:.2f} $ moins avantage {a.avantage:.2f} $; reçu : {a.source}")
    lignes += [f"Contributions admissibles — 40900 : {r.ligne_40900:.2f} $",
        f"Crédit calculé — 41000 : {r.ligne_41000:.2f} $; maximum 650 $",
        "75 % des premiers 400 $, 50 % des 350 $ suivants, un tiers au-delà; arrondi au cent.",
        f"Crédit utilisé : {final.credit_politique_utilise:.2f} $; inutilisé sans report : {r.ligne_41000 - final.credit_politique_utilise:.2f} $",
        f"Impôt 40600 : {final.impot_federal_apres_credit_etranger:.2f} $; 41600 : {final.credit_politique_ligne_41000:.2f} $; 41700 : {final.impot_federal_ligne_41700:.2f} $",
        "Appliqué après 40500 et avant les avances 41500; 33500/34990 et base d'abattement 42900 inchangés."]
    return lignes
