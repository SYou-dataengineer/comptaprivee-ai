"""Fonds de travailleurs fédéraux 2025 : LIR 127.4, lignes 41300/41400.

Profils Québec FTQ/Fondaction. L'admissibilité provinciale est nécessaire;
ce module ne calcule pas encore le crédit québécois de la ligne 424.
"""
from dataclasses import asdict, dataclass, fields
from datetime import date
from decimal import Decimal, InvalidOperation

from .tax_rules_2025 import arrondir_cent

ZERO = Decimal("0")
TAUX = Decimal("0.15")
FONDS_ADMIS = ("FTQ A", "Fondaction A", "Fondaction B")
REGIMES_ADMIS = ("direct", "REER", "REER conjoint", "CELI")
CONFIRMATIONS_FONDS = {
    "valide_par_comptable": "Pièces, dates, titulaires et choix vérifiés par le comptable",
    "acquisitions_initiales": "Premières acquisitions ou souscriptions irrévocables payées; premier détenteur inscrit vérifié",
    "admissibilite_provinciale": "Actions admissibles au crédit provincial, y compris les conditions du souscripteur et du bénéficiaire du régime",
    "aides_verifiees": "Toutes les aides publiques reçues ou à recevoir sont déclarées, hors crédits d'impôt",
    "historique_verifie": "Crédits effectivement déduits en 2024 rapprochés de la déclaration cotisée, sans double utilisation",
    "aucun_partage": "Aucune action réclamée par deux personnes, notamment dans un REER de conjoint",
    "aucun_traitement_special": "Aucun échange, remplacement RAP/REEP, annulation, rachat, remboursement 211.9, décès ou acquisition réputée par décision ministérielle",
}


@dataclass(frozen=True)
class SituationFonds2025:
    nom: str = ""
    naissance: str = ""
    rente_retraite: bool = False
    conge_sans_retour: bool = False
    rachat_demande: bool = False
    revenu_emploi_entreprise: Decimal = ZERO


@dataclass(frozen=True)
class AcquisitionFonds2025:
    date_acquisition: str = ""
    fonds: str = ""
    regime: str = "direct"
    souscripteur: str = "contribuable"
    rentier: str = "contribuable"
    montant: Decimal = ZERO
    aide_publique: Decimal = ZERO
    credit_utilise_2024: Decimal = ZERO
    source_2024: str = ""
    cout_reserve_2026: Decimal = ZERO
    source: str = ""


@dataclass(frozen=True)
class FondsTravailleurs2025:
    acquisitions: tuple[AcquisitionFonds2025, ...] = ()
    contribuable: SituationFonds2025 = SituationFonds2025()
    conjoint: SituationFonds2025 = SituationFonds2025()
    source: str = ""
    valide_par_comptable: bool = False
    acquisitions_initiales: bool = False
    admissibilite_provinciale: bool = False
    aides_verifiees: bool = False
    historique_verifie: bool = False
    aucun_partage: bool = False
    aucun_traitement_special: bool = False


@dataclass(frozen=True)
class ResultatFondsTravailleurs2025:
    cout_net_total: Decimal = ZERO
    cout_reserve_2026: Decimal = ZERO
    credit_utilise_2024: Decimal = ZERO
    ligne_41300: Decimal = ZERO
    ligne_41400: Decimal = ZERO


def montant_fonds_2025(v, nom):
    if not isinstance(v, Decimal) or not v.is_finite() or v < ZERO:
        raise ValueError(f"{nom} doit être un Decimal fini non négatif.")
    try:
        if arrondir_cent(v) != v:
            raise ValueError(f"{nom} exige au plus deux décimales.")
    except ArithmeticError as erreur:
        raise ValueError(f"{nom} dépasse la capacité du calcul.") from erreur
    return v


def _cle(v):
    return " ".join(v.split()).casefold()


def _date(v, nom):
    try:
        d = date.fromisoformat(v)
        if d.isoformat() != v:
            raise ValueError()
        return d
    except (ValueError, TypeError) as erreur:
        raise ValueError(f"{nom} exige une date AAAA-MM-JJ valide.") from erreur


def valider_situation_fonds_2025(s, *, vide=False):
    if not isinstance(s, SituationFonds2025):
        raise ValueError("Situation du détenteur de fonds invalide.")
    if not isinstance(s.nom, str) or not isinstance(s.naissance, str):
        raise ValueError("Nom et naissance du détenteur invalides.")
    for nom in ("rente_retraite", "conge_sans_retour", "rachat_demande"):
        if type(getattr(s, nom)) is not bool:
            raise ValueError("Situation retraite non booléenne : " + nom)
    montant_fonds_2025(s.revenu_emploi_entreprise, "Revenus d'emploi et d'entreprise")
    if vide:
        if s != SituationFonds2025():
            raise ValueError("Situation renseignée sans acquisition correspondante.")
        return
    naissance = _date(s.naissance, "Naissance")
    if not s.nom.strip() or naissance > date(2025, 12, 31):
        raise ValueError("Identité du détenteur invalide.")
    if naissance < date(1961, 1, 1):
        raise ValueError("Naissance avant 1961 : crédit provincial 2025 indisponible.")
    retraite = s.rente_retraite or s.conge_sans_retour
    if s.revenu_emploi_entreprise > Decimal(3500) and not s.rachat_demande:
        retraite = False  # Déjà vérifié : moins de 65 ans à la fin de 2025.
    if naissance < date(1981, 1, 1) and retraite:
        raise ValueError("Retraite ou préretraite : crédit provincial 2025 indisponible.")
    if s.rachat_demande:
        raise ValueError("Rachat demandé : traitement spécialisé non couvert par ce profil.")


def valider_acquisitions_fonds_2025(acquisitions):
    if type(acquisitions) is not tuple:
        raise ValueError("Les acquisitions doivent former un tuple immuable.")
    sources = set()
    for a in acquisitions:
        if not isinstance(a, AcquisitionFonds2025):
            raise ValueError("Acquisition de fonds invalide.")
        for nom in ("fonds", "regime", "souscripteur", "rentier", "source", "source_2024"):
            if not isinstance(getattr(a, nom), str):
                raise ValueError("Texte d'acquisition invalide : " + nom)
        jour = _date(a.date_acquisition, "Acquisition")
        if not date(2025, 1, 1) <= jour <= date(2026, 3, 2):
            raise ValueError("Acquisition requise entre le 1 janvier 2025 et le 2 mars 2026.")
        if a.fonds not in FONDS_ADMIS or a.regime not in REGIMES_ADMIS:
            raise ValueError("Fonds ou régime non couvert par le profil Québec.")
        if a.souscripteur not in ("contribuable", "conjoint") or a.rentier not in ("contribuable", "conjoint"):
            raise ValueError("Souscripteur ou rentier invalide.")
        if a.regime != "REER conjoint" and (a.souscripteur != "contribuable" or a.rentier != "contribuable"):
            raise ValueError("Les acquisitions d'un tiers exigent un REER conjoint admissible.")
        if a.regime == "REER conjoint" and a.souscripteur == a.rentier:
            raise ValueError("Le REER conjoint exige deux personnes distinctes.")
        for nom in ("montant", "aide_publique", "credit_utilise_2024", "cout_reserve_2026"):
            montant_fonds_2025(getattr(a, nom), nom)
        if a.montant == ZERO or a.aide_publique > a.montant:
            raise ValueError("Paiement positif et aide publique au plus égale au paiement requis.")
        net = a.montant - a.aide_publique
        if a.cout_reserve_2026 > net or (jour.year != 2026 and a.cout_reserve_2026):
            raise ValueError("Réservation 2026 permise uniquement sur le coût net des achats de 2026.")
        if a.credit_utilise_2024:
            if jour > date(2025, 3, 1) or not a.source_2024.strip():
                raise ValueError("Crédit 2024 : acquisition des 60 premiers jours de 2025 et source requises.")
            if a.credit_utilise_2024 > min(Decimal(750), arrondir_cent(net * TAUX)):
                raise ValueError("Crédit utilisé en 2024 supérieur au crédit possible de l'acquisition.")
        elif a.source_2024.strip():
            raise ValueError("Source 2024 renseignée sans crédit utilisé.")
        if not a.source.strip() or _cle(a.source) in sources:
            raise ValueError("Source d'acquisition obligatoire et unique.")
        sources.add(_cle(a.source))


def calculer_fonds_travailleurs_2025(p, *, client=None, annee=2025):
    if not isinstance(p, FondsTravailleurs2025) or not isinstance(p.source, str):
        raise ValueError("Profil de fonds de travailleurs invalide.")
    valider_acquisitions_fonds_2025(p.acquisitions)
    for nom in CONFIRMATIONS_FONDS:
        if type(getattr(p, nom)) is not bool:
            raise ValueError("Confirmation non booléenne : " + nom)
        if p.acquisitions and not getattr(p, nom):
            raise ValueError("Confirmation obligatoire : " + CONFIRMATIONS_FONDS[nom])
    conjoint = any(a.regime == "REER conjoint" for a in p.acquisitions)
    valider_situation_fonds_2025(p.contribuable, vide=not p.acquisitions)
    valider_situation_fonds_2025(p.conjoint, vide=not conjoint)
    if not p.acquisitions:
        if p.source.strip():
            raise ValueError("Profil sans acquisitions : source vide requise.")
        return ResultatFondsTravailleurs2025()
    if annee != 2025 or not p.source.strip():
        raise ValueError("Année 2025 et source de validation requises.")
    if client is not None and (not isinstance(client, str) or _cle(client) != _cle(p.contribuable.nom)):
        raise ValueError("Le détenteur ne correspond pas au contribuable du dossier.")
    if conjoint and _cle(p.contribuable.nom) == _cle(p.conjoint.nom):
        raise ValueError("Contribuable et conjoint doivent être distincts.")
    net = sum((a.montant - a.aide_publique for a in p.acquisitions), ZERO)
    reserve = sum((a.cout_reserve_2026 for a in p.acquisitions), ZERO)
    ancien = sum((a.credit_utilise_2024 for a in p.acquisitions), ZERO)
    if ancien > Decimal(750):
        raise ValueError("Le total effectivement utilisé en 2024 ne peut pas dépasser 750 $.")
    assiette = montant_fonds_2025(net - reserve, "Coût net 41300")
    # 127.4(5) : soustraire l'utilisation antérieure AVANT le plafond annuel.
    credit = arrondir_cent(min(Decimal(750), max(ZERO, assiette * TAUX - ancien)))
    return ResultatFondsTravailleurs2025(net, reserve, ancien, assiette, credit)


def fonds_vers_dict(p):
    brut = asdict(p)
    for nom in ("contribuable", "conjoint"):
        brut[nom]["revenu_emploi_entreprise"] = format(getattr(p, nom).revenu_emploi_entreprise, ".2f")
    brut["acquisitions"] = [dict(asdict(a), **{n: format(getattr(a, n), ".2f") for n in
        ("montant", "aide_publique", "credit_utilise_2024", "cout_reserve_2026")}) for a in p.acquisitions]
    return brut


def fonds_depuis_dict(valeur, *, client=None, annee=2025):
    def lire(v, classe, montants=()):
        if not isinstance(v, dict) or set(v) - {f.name for f in fields(classe)}:
            raise ValueError("Champs enregistrés de fonds de travailleurs invalides.")
        v = dict(v)
        for nom in montants:
            x = v.get(nom, "0")
            if not isinstance(x, (str, int)) or isinstance(x, bool):
                raise ValueError("Montant enregistré de fonds invalide.")
            try:
                v[nom] = montant_fonds_2025(Decimal(x), nom)
            except (InvalidOperation, ValueError) as erreur:
                raise ValueError("Montant enregistré de fonds invalide.") from erreur
        return v
    brut = lire({} if valeur is None else valeur, FondsTravailleurs2025)
    acquisitions = brut.get("acquisitions", [])
    if not isinstance(acquisitions, list):
        raise ValueError("Liste d'acquisitions enregistrée invalide.")
    brut["acquisitions"] = tuple(AcquisitionFonds2025(**lire(a, AcquisitionFonds2025,
        ("montant", "aide_publique", "credit_utilise_2024", "cout_reserve_2026"))) for a in acquisitions)
    for nom in ("contribuable", "conjoint"):
        brut[nom] = SituationFonds2025(**lire(brut.get(nom, {}), SituationFonds2025, ("revenu_emploi_entreprise",)))
    p = FondsTravailleurs2025(**brut)
    calculer_fonds_travailleurs_2025(p, client=client, annee=annee)
    return p


def verifier_fonds_conjoint_2025(p, autre, nom_conjoint):
    if p.conjoint.nom and _cle(p.conjoint.nom) != _cle(nom_conjoint):
        raise ValueError("Le conjoint des fonds diffère du dossier importé.")
    if {_cle(a.source) for a in p.acquisitions} & {_cle(a.source) for a in autre.acquisitions}:
        raise ValueError("La même acquisition de fonds figure dans les deux dossiers.")


def lignes_fonds_travailleurs_2025(p, r, final):
    if not p.acquisitions:
        return []
    lignes = ["", "FONDS DE TRAVAILLEURS FÉDÉRAUX — BLOC 5O",
        f"Source : {p.source}; validation comptable confirmée"]
    for role, s in (("Contribuable", p.contribuable), ("Conjoint", p.conjoint)):
        if s.nom:
            lignes.append(f"{role} : {s.nom}, naissance {s.naissance}; emploi/entreprise {s.revenu_emploi_entreprise:.2f} $; "
                f"rente retraite : {'oui' if s.rente_retraite else 'non'}; congé sans retour : {'oui' if s.conge_sans_retour else 'non'}; aucun rachat demandé.")
    for a in p.acquisitions:
        lignes.append(f"{a.date_acquisition} — {a.fonds}, {a.regime}; souscripteur {a.souscripteur}, rentier {a.rentier}; "
            f"paiement {a.montant:.2f} $, aide {a.aide_publique:.2f} $; source : {a.source}")
        if a.credit_utilise_2024:
            lignes.append(f"Crédit effectivement déduit en 2024 : {a.credit_utilise_2024:.2f} $; pièce : {a.source_2024}")
        if a.cout_reserve_2026:
            lignes.append(f"Coût réservé à 2026 : {a.cout_reserve_2026:.2f} $")
    lignes += [f"Coût net affecté à 2025 — 41300 : {r.ligne_41300:.2f} $",
        f"Crédit calculé — 41400 : {r.ligne_41400:.2f} $ = min(750 $, 15 % du coût net moins crédit utilisé en 2024)",
        f"Crédit utilisé : {final.credit_fonds_utilise:.2f} $; non utilisé en 2025 : {r.ligne_41400 - final.credit_fonds_utilise:.2f} $",
        f"Total 41600 : {final.credits_ligne_41600:.2f} $; impôt 41700 : {final.impot_federal_ligne_41700:.2f} $",
        "Après 40500 et 41000, avant 41500; revenu, 33500/34990, 42900 et abattement inchangés.",
        "Aucun report fédéral général; possibilité propre aux acquisitions de début 2026 à réexaminer en 2026.",
        "Admissibilité provinciale contrôlée; crédit Québec 424 distinct, non calculé par ce bloc."]
    return lignes
