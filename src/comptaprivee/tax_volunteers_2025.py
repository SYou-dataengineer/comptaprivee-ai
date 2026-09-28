"""ARC 2025, 31220/31240 et choix de l'exemption T4-87 à 10105.

Les heures admissibles sont certifiées et validées sur pièces, non inférées.
Le calcul fédéral ne modifie ni les revenus ni les crédits Québec.
"""
from dataclasses import dataclass
from decimal import Decimal

from .tax_field_validation import STATUT_VALIDE, STATUT_CORRIGE_VALIDE
from .tax_rules_2025 import arrondir_cent

ZERO = Decimal("0")
CHOIX_BENEVOLES = ("exoneration", "pompiers", "sauvetage")
CONFIRMATIONS_BENEVOLES = {
    "valide_par_comptable": "Choix, organismes, certificats et feuillets validés par le comptable",
    "choix_confirme": "Choix fédéral confirmé : exemption OU un seul crédit, jamais les deux",
    "revenus_verifies": "Toutes les cases 87 sont validées et exclues des cases 14; aucune autre exemption conservée avec le crédit",
    "heures_certifiees": "Pour un crédit : heures admissibles certifiées par chaque service ou organisme compétent",
    "aucun_double_compte": "Pour un crédit : aucune heure comptée deux fois entre organismes ou activités",
}


@dataclass(frozen=True)
class ActiviteBenevole2025:
    organisme: str = ""
    nature: str = ""
    heures: Decimal = ZERO
    source: str = ""
    organisme_admissible: bool = False
    services_similaires_remuneres: bool = False


@dataclass(frozen=True)
class Benevoles2025:
    choix: str = ""
    activites: tuple[ActiviteBenevole2025, ...] = ()
    source: str = ""
    valide_par_comptable: bool = False
    choix_confirme: bool = False
    revenus_verifies: bool = False
    heures_certifiees: bool = False
    aucun_double_compte: bool = False


@dataclass(frozen=True)
class ResultatBenevoles2025:
    heures_pompiers: Decimal = ZERO
    heures_sauvetage: Decimal = ZERO
    heures_exclues: Decimal = ZERO
    cases_87: tuple[tuple[str, Decimal], ...] = ()
    reintegration_10100: Decimal = ZERO
    exemption_10105: Decimal = ZERO
    ligne_credit: str = ""
    base_credit: Decimal = ZERO


def _decimal(valeur, nom):
    if not isinstance(valeur, Decimal) or not valeur.is_finite() or valeur < ZERO:
        raise ValueError(f"{nom} doit être un Decimal fini non négatif.")
    try:
        if arrondir_cent(valeur) != valeur:
            raise ValueError(f"{nom} doit avoir au plus deux décimales.")
    except ArithmeticError as erreur:
        raise ValueError(f"{nom} dépasse la capacité du calcul.") from erreur
    return valeur


def valider_benevoles_2025(p):
    if not isinstance(p, Benevoles2025) or type(p.activites) is not tuple:
        raise ValueError("Profil de services bénévoles invalide.")
    if not isinstance(p.choix, str) or p.choix not in ("", *CHOIX_BENEVOLES):
        raise ValueError("Choisissez l'exonération, les pompiers ou la recherche-sauvetage.")
    if not isinstance(p.source, str):
        raise ValueError("La source du choix doit être un texte.")
    for nom in CONFIRMATIONS_BENEVOLES:
        if type(getattr(p, nom)) is not bool:
            raise ValueError("Confirmation non booléenne : " + nom)
    if not p.choix:
        if p.activites or p.source.strip():
            raise ValueError("Un choix fiscal est obligatoire pour ce profil.")
        return p
    if not p.source.strip():
        raise ValueError("La source du choix fiscal est obligatoire.")
    controles = tuple(CONFIRMATIONS_BENEVOLES) if p.choix != "exoneration" else (
        "valide_par_comptable", "choix_confirme", "revenus_verifies")
    for nom in controles:
        if not getattr(p, nom):
            raise ValueError("Confirmation obligatoire : " + CONFIRMATIONS_BENEVOLES[nom])
    valider_activites_benevoles_2025(p.activites)
    if p.choix in ("pompiers", "sauvetage"):
        admissibles = tuple(a for a in p.activites if a.organisme_admissible and not a.services_similaires_remuneres)
        if sum((a.heures for a in admissibles), ZERO) < Decimal(200) or not any(a.nature == p.choix for a in admissibles):
            raise ValueError("Le crédit exige 200 heures admissibles combinées et des services dans l'activité choisie.")
    return p


def valider_activites_benevoles_2025(activites):
    if type(activites) is not tuple:
        raise ValueError("Les activités doivent être un tuple immuable.")
    vus = set()
    for a in activites:
        if not isinstance(a, ActiviteBenevole2025):
            raise ValueError("Activité bénévole invalide.")
        for nom in ("organisme", "source", "nature"):
            if not isinstance(getattr(a, nom), str) or not getattr(a, nom).strip():
                raise ValueError("Champ obligatoire de l'activité : " + nom)
        if a.nature not in ("pompiers", "sauvetage"):
            raise ValueError("Nature d'activité bénévole invalide.")
        cle = (" ".join(a.organisme.split()).casefold(), a.nature)
        if cle in vus:
            raise ValueError("Activité du même organisme comptée deux fois.")
        vus.add(cle)
        if not ZERO < _decimal(a.heures, "Heures certifiées") <= Decimal(8760):
            raise ValueError("Les heures doivent être positives, au plus 8760 par activité en 2025.")
        for nom in ("organisme_admissible", "services_similaires_remuneres"):
            if type(getattr(a, nom)) is not bool:
                raise ValueError("Confirmation d'activité non booléenne : " + nom)
    return activites


def calculer_benevoles_2025(p, dossier):
    valider_benevoles_2025(p)
    if not p.choix and not any((d.type_document, d.case) == ("T4", "87") for d in dossier.donnees_validees):
        return ResultatBenevoles2025()
    if dossier.annee_fiscale != 2025:
        raise ValueError("Les services bénévoles de ce module concernent uniquement 2025.")
    cases = []
    documents = set()
    for d in dossier.donnees_validees:
        if (d.type_document, d.case) != ("T4", "87"):
            continue
        if d.document in documents or d.document not in dossier.documents:
            raise ValueError("Case 87 dupliquée ou document absent du dossier.")
        documents.add(d.document)
        if d.statut not in (STATUT_VALIDE, STATUT_CORRIGE_VALIDE):
            raise ValueError("La case 87 doit être validée par le comptable.")
        if not any(x.document == d.document and (x.type_document, x.case) == ("T4", "14")
                   and x.statut in (STATUT_VALIDE, STATUT_CORRIGE_VALIDE) for x in dossier.donnees_validees):
            raise ValueError("La case 87 doit appartenir à un T4 avec case 14 validée.")
        montant = _decimal(d.valeur_validee, "T4 case 87")
        if montant > Decimal(1000):
            raise ValueError("La case 87 ne peut dépasser l'exemption de 1000 $ par employeur admissible.")
        cases.append((str(d.document), montant))
    montant87 = sum((v for _, v in cases), ZERO)
    if montant87 and not p.choix:
        raise ValueError("La case 87 exige un choix explicite dans Services bénévoles 2025.")
    heures = {"pompiers": ZERO, "sauvetage": ZERO}
    exclues = ZERO
    for a in p.activites:
        if a.organisme_admissible and not a.services_similaires_remuneres:
            heures[a.nature] += a.heures
        else:
            exclues += a.heures
    ligne = ""
    if p.choix in ("pompiers", "sauvetage"):
        if heures["pompiers"] + heures["sauvetage"] < Decimal(200) or not heures[p.choix]:
            raise ValueError("Le crédit exige 200 heures admissibles combinées et des services dans l'activité choisie.")
        ligne = "31220" if p.choix == "pompiers" else "31240"
    return ResultatBenevoles2025(
        heures_pompiers=heures["pompiers"], heures_sauvetage=heures["sauvetage"], heures_exclues=exclues,
        cases_87=tuple(cases), reintegration_10100=montant87 if ligne else ZERO,
        exemption_10105=montant87 if p.choix == "exoneration" else ZERO,
        ligne_credit=ligne, base_credit=Decimal(6000) if ligne else ZERO,
    )


def lignes_benevoles_2025(p, r):
    if not p.choix:
        return []
    lignes = ["", "SERVICES BÉNÉVOLES — BLOC 5L", f"Choix : {p.choix}; source : {p.source}; validation comptable confirmée"]
    for a in p.activites:
        statut = "retenues" if a.organisme_admissible and not a.services_similaires_remuneres else "exclues (organisme ou services rémunérés similaires)"
        lignes.append(f"{a.organisme} — {a.nature} : {a.heures:.2f} heures {statut}; source : {a.source}")
    lignes += [f"Heures admissibles : pompiers {r.heures_pompiers:.2f} + sauvetage {r.heures_sauvetage:.2f}; heures exclues : {r.heures_exclues:.2f}"]
    for source, montant in r.cases_87:
        lignes.append(f"T4 case 87 — {source} : {montant:.2f} $")
    lignes += [f"Case 87 ajoutée à 10100 : {r.reintegration_10100:.2f} $; exemption 10105 : {r.exemption_10105:.2f} $",
        "L'exemption et le crédit sont exclusifs; aucune modification des montants Québec."]
    if r.ligne_credit:
        lignes += [f"Base ligne {r.ligne_credit} : {r.base_credit:.2f} $ (seuil 200 heures)",
            "Base incluse une fois dans 33500 avant la scolarité; 33800, 34990 et 35000 recalculés."]
    return lignes
