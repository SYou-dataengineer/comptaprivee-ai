"""Frais médicaux familiaux fédéraux 2025, 33099 / 33199 / 33200.

ARC lignes 33099/33199 et feuille fédérale 2025 : seuil du demandeur pour
33099, seuil propre à chaque autre personne à charge pour 33199.
L'admissibilité des dépenses et la dépendance sont vérifiées sur pièces.
"""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from .tax_rules_2025 import arrondir_cent

ZERO = Decimal("0")
LIENS_MEDICAUX = ("soi-même", "conjoint", "enfant", "petit-enfant", "parent",
                  "grand-parent", "frère ou sœur", "oncle ou tante", "neveu ou nièce")
CONFIRMATIONS_MEDICALES_FAMILLE = {
    "valide_par_comptable": "Admissibilité, pièces et données validées par le comptable",
    "paiement_verifie": "Dépenses payées par le demandeur ou son conjoint dans la période retenue",
    "remboursements_verifies": "Aides, remboursements et exception des remboursements imposables vérifiés",
    "aucune_double_demande": "Aucune dépense retenue déjà réclamée, ni attribuée à un autre demandeur",
    "liens_dependance_verifies": "Liens familiaux et dépendance financière vérifiés pour les personnes à charge",
    "conflits_verifies": "Rapprochement effectué avec handicap, soins, garde, soutien handicap et rénovation",
    "profil_ordinaire": "Aucun décès ni traitement spécial nécessitant une période ou un calcul distinct",
}


@dataclass(frozen=True)
class PersonneFraisMedicaux2025:
    reference: str = ""
    nom: str = ""
    naissance: str = ""
    lien: str = ""
    lien_avec_conjoint: bool = False
    resident_canada_dans_annee: bool = False
    revenu_net_23600: Decimal = ZERO
    source_revenu: str = ""
    source_lien_dependance: str = ""


@dataclass(frozen=True)
class DepenseMedicaleFamiliale2025:
    reference: str = ""
    personne: str = ""
    date_paiement: str = ""
    description: str = ""
    montant_paye: Decimal = ZERO
    remboursements: Decimal = ZERO
    remboursements_imposables_non_deduits: Decimal = ZERO
    part_reclamee_ailleurs: Decimal = ZERO
    source: str = ""


@dataclass(frozen=True)
class FraisMedicauxFamilleFederaux2025:
    demandeur: str = ""
    debut_periode: str = ""
    fin_periode: str = ""
    personnes: tuple[PersonneFraisMedicaux2025, ...] = ()
    depenses: tuple[DepenseMedicaleFamiliale2025, ...] = ()
    valide_par_comptable: bool = False
    paiement_verifie: bool = False
    remboursements_verifies: bool = False
    aucune_double_demande: bool = False
    liens_dependance_verifies: bool = False
    conflits_verifies: bool = False
    profil_ordinaire: bool = False


@dataclass(frozen=True)
class ResultatPersonneMedicale2025:
    reference: str
    ligne: str
    frais_nets: Decimal
    revenu_net: Decimal
    seuil: Decimal
    montant_admissible: Decimal


@dataclass(frozen=True)
class ResultatMedicalFamilial2025:
    personnes: tuple[ResultatPersonneMedicale2025, ...] = ()
    ligne_33099: Decimal = ZERO
    seuil_demandeur: Decimal = ZERO
    net_33099: Decimal = ZERO
    ligne_33199: Decimal = ZERO
    ligne_33200: Decimal = ZERO


def montant_medical_familial(v, nom, *, signe=False):
    if not isinstance(v, Decimal) or not v.is_finite() or (not signe and v < ZERO):
        raise ValueError(nom + " doit être un Decimal fini" + ("." if signe else " non négatif."))
    try:
        if v != arrondir_cent(v):
            raise ValueError(nom + " exige au plus deux décimales.")
    except ArithmeticError as erreur:
        raise ValueError(nom + " hors capacité.") from erreur
    return v


def _date(v, nom):
    try:
        if not isinstance(v, str) or date.fromisoformat(v).isoformat() != v:
            raise ValueError()
        return date.fromisoformat(v)
    except ValueError as erreur:
        raise ValueError(nom + " : format AAAA-MM-JJ requis.") from erreur


def _texte(v, nom):
    if not isinstance(v, str) or not v.strip():
        raise ValueError(nom + " obligatoire.")
    return " ".join(v.split()).casefold()


def calculer_medical_familial_2025(p, *, demandeur, revenu_net, annee=2025):
    from dataclasses import fields
    montant_medical_familial(revenu_net, "Revenu net du demandeur", signe=True)
    if not isinstance(p, FraisMedicauxFamilleFederaux2025):
        raise ValueError("Profil médical familial invalide.")
    for f in fields(p):
        v = getattr(p, f.name)
        if f.type is bool and type(v) is not bool:
            raise ValueError("Confirmation médicale non booléenne : " + f.name)
        if f.type is str and not isinstance(v, str):
            raise ValueError("Texte médical invalide : " + f.name)
    if type(p.personnes) is not tuple or type(p.depenses) is not tuple:
        raise ValueError("Personnes et dépenses doivent former des tuples.")
    if not p.personnes or not p.depenses:
        if p != FraisMedicauxFamilleFederaux2025():
            raise ValueError("Profil médical incomplet : personnes et dépenses requises.")
        return ResultatMedicalFamilial2025()
    if annee != 2025 or _texte(p.demandeur, "Demandeur") != _texte(demandeur, "Client"):
        raise ValueError("Année ou demandeur du profil médical divergent.")
    for nom, libelle in CONFIRMATIONS_MEDICALES_FAMILLE.items():
        if not getattr(p, nom):
            raise ValueError("Confirmation obligatoire : " + libelle)
    debut, fin = _date(p.debut_periode, "Début"), _date(p.fin_periode, "Fin")
    # Les reçus peuvent couvrir une partie de la fenêtre choisie; une période
    # plus courte est incluse dans une fenêtre de douze mois finissant en 2025.
    limite = date(fin.year - 1, fin.month, fin.day)
    if fin.year != 2025 or not limite < debut <= fin:
        raise ValueError("Période comprise dans douze mois consécutifs se terminant en 2025 requise.")
    personnes, noms, compte = {}, set(), {"soi-même": 0, "conjoint": 0}
    for x in p.personnes:
        if not isinstance(x, PersonneFraisMedicaux2025):
            raise ValueError("Personne médicale invalide.")
        for f in fields(x):
            if f.type is str and not isinstance(getattr(x, f.name), str):
                raise ValueError("Texte de la personne invalide : " + f.name)
        ref, nom = _texte(x.reference, "Référence personne"), _texte(x.nom, "Nom personne")
        if ref in personnes or nom in noms or x.lien not in LIENS_MEDICAUX:
            raise ValueError("Personne dupliquée ou lien invalide.")
        naissance = _date(x.naissance, "Naissance")
        if naissance > date(2025, 12, 31):
            raise ValueError("Naissance postérieure à 2025.")
        if type(x.lien_avec_conjoint) is not bool or type(x.resident_canada_dans_annee) is not bool:
            raise ValueError("Confirmation de lien ou résidence non booléenne.")
        if x.lien in compte:
            compte[x.lien] += 1
            if compte[x.lien] > 1 or x.lien_avec_conjoint:
                raise ValueError("Personne ou conjoint dupliqué, ou lien contradictoire.")
        if x.lien == "soi-même" and nom != _texte(demandeur, "Client"):
            raise ValueError("La personne elle-même doit correspondre au demandeur.")
        if x.lien != "soi-même" and nom == _texte(demandeur, "Client"):
            raise ValueError("Le demandeur ne peut pas être sa propre personne à charge.")
        ligne = "33099" if x.lien in ("soi-même", "conjoint") or (x.lien == "enfant" and naissance.year >= 2008) else "33199"
        montant_medical_familial(x.revenu_net_23600, "23600 de la personne", signe=True)
        if ligne == "33199":
            _texte(x.source_revenu, "Source du revenu net")
            if x.lien not in ("enfant", "petit-enfant") and not x.resident_canada_dans_annee:
                raise ValueError("Résidence canadienne pendant l'année requise pour ce lien.")
        elif x.revenu_net_23600 or x.source_revenu:
            raise ValueError("Le revenu individuel n'est pas requis pour le groupe 33099.")
        _texte(x.source_lien_dependance, "Source du lien et de la dépendance")
        personnes[ref] = (x, ligne)
        noms.add(nom)
    totaux = {ref: ZERO for ref in personnes}
    recus = set()
    for d in p.depenses:
        if not isinstance(d, DepenseMedicaleFamiliale2025):
            raise ValueError("Dépense médicale invalide.")
        ref, personne = _texte(d.reference, "Référence reçu"), _texte(d.personne, "Référence bénéficiaire")
        if ref in recus or personne not in personnes:
            raise ValueError("Reçu dupliqué ou bénéficiaire absent.")
        if not debut <= _date(d.date_paiement, "Paiement") <= fin:
            raise ValueError("Paiement hors période commune.")
        _texte(d.description, "Description")
        _texte(d.source, "Source reçu")
        for nom in ("montant_paye", "remboursements", "remboursements_imposables_non_deduits", "part_reclamee_ailleurs"):
            montant_medical_familial(getattr(d, nom), nom)
        if d.remboursements > d.montant_paye or d.remboursements_imposables_non_deduits > d.remboursements:
            raise ValueError("Remboursements contradictoires.")
        net = d.montant_paye - d.remboursements + d.remboursements_imposables_non_deduits - d.part_reclamee_ailleurs
        if net < ZERO:
            raise ValueError("La part réclamée ailleurs dépasse les frais disponibles.")
        totaux[personne] += net
        recus.add(ref)
    resultats, total33099, total33199 = [], ZERO, ZERO
    for ref, (x, ligne) in personnes.items():
        seuil = min(arrondir_cent(max(x.revenu_net_23600, ZERO) * Decimal(".03")), Decimal(2834)) if ligne == "33199" else ZERO
        admissible = max(totaux[ref] - seuil, ZERO)
        resultats.append(ResultatPersonneMedicale2025(x.reference, ligne, totaux[ref], x.revenu_net_23600, seuil, admissible))
        if ligne == "33099":
            total33099 += totaux[ref]
        else:
            total33199 += admissible
    seuil = min(arrondir_cent(max(revenu_net, ZERO) * Decimal(".03")), Decimal(2834))
    net33099 = max(total33099 - seuil, ZERO)
    return ResultatMedicalFamilial2025(tuple(resultats), total33099, seuil, net33099, total33199, net33099 + total33199)


def medical_familial_vers_dict(p):
    from dataclasses import asdict
    calculer_medical_familial_2025(p, demandeur=p.demandeur, revenu_net=ZERO)
    def convertir(v):
        if isinstance(v, Decimal):
            return format(v, ".2f")
        if isinstance(v, dict):
            return {k: convertir(x) for k, x in v.items()}
        if isinstance(v, (tuple, list)):
            return [convertir(x) for x in v]
        return v
    return convertir(asdict(p))


def verifier_combinaison_medicale_famille(p, frais_individuels, act_present=False):
    if not p.personnes:
        return
    if frais_individuels.montant_admissible_federal:
        raise ValueError("Les frais médicaux fédéraux individuels et détaillés ne peuvent pas être cumulés; regroupez les reçus dans le profil détaillé.")
    if any(x.lien != "soi-même" for x in p.personnes):
        if frais_individuels.montant_admissible_quebec:
            raise ValueError("Frais médicaux familiaux Québec : extension de l'annexe B requise; le profil Québec individuel est incompatible.")
        if act_present or frais_individuels.supplement.reclamer:
            raise ValueError("ACT et supplément médical familiaux nécessitent leur extension dédiée; profil individuel incompatible.")


def medical_familial_depuis_dict(v):
    from dataclasses import fields
    def lire(brut, classe):
        if not isinstance(brut, dict) or set(brut) - {f.name for f in fields(classe)}:
            raise ValueError("Champs du profil médical familial invalides.")
        valeurs = dict(brut)
        for f in fields(classe):
            if f.type is Decimal:
                x = valeurs.get(f.name, "0")
                if type(x) not in (str, int):
                    raise ValueError("Montant médical JSON invalide.")
                try:
                    valeurs[f.name] = Decimal(x)
                except ArithmeticError as erreur:
                    raise ValueError("Montant médical JSON invalide.") from erreur
        if classe is FraisMedicauxFamilleFederaux2025:
            for nom, enfant in (("personnes", PersonneFraisMedicaux2025), ("depenses", DepenseMedicaleFamiliale2025)):
                lignes = valeurs.get(nom, [])
                if not isinstance(lignes, list):
                    raise ValueError("Liste médicale JSON invalide.")
                valeurs[nom] = tuple(lire(x, enfant) for x in lignes)
        return classe(**valeurs)
    p = lire({} if v is None else v, FraisMedicauxFamilleFederaux2025)
    calculer_medical_familial_2025(p, demandeur=p.demandeur, revenu_net=ZERO)
    return p


def lignes_medical_familial_2025(p, r):
    if not p.personnes:
        return ()
    lignes = ["FRAIS MÉDICAUX FAMILIAUX FÉDÉRAUX — VALIDÉS PAR LE COMPTABLE",
        f"Demandeur : {p.demandeur}; période commune : {p.debut_periode} au {p.fin_periode}."]
    for x, v in zip(p.personnes, r.personnes):
        lignes.extend((f"{x.nom} ({x.lien}) : ligne {v.ligne}; frais nets {v.frais_nets:.2f} $.",
                       "Source du lien et soutien : " + x.source_lien_dependance))
        if v.ligne == "33199":
            lignes.append(f"23600 : {v.revenu_net:.2f} $; source : {x.source_revenu}; seuil min(3 %, 2834) : {v.seuil:.2f} $; net : {v.montant_admissible:.2f} $.")
    lignes.extend(f"Reçu {d.reference} : {d.date_paiement}; {d.description}; payé {d.montant_paye:.2f} $; remboursements {d.remboursements:.2f} $ dont imposables non déduits {d.remboursements_imposables_non_deduits:.2f} $; autres demandes {d.part_reclamee_ailleurs:.2f} $; source : {d.source}." for d in p.depenses)
    lignes.extend((f"33099 : {r.ligne_33099:.2f} $ - seuil demandeur {r.seuil_demandeur:.2f} $ = {r.net_33099:.2f} $ (minimum zéro).",
        f"33199 : somme des frais nets après seuil individuel = {r.ligne_33199:.2f} $.",
        f"33200 : {r.net_33099:.2f} + {r.ligne_33199:.2f} = {r.ligne_33200:.2f} $; inclusion unique dans 33500.",
        "Admissibilité et absence de double demande validées sur pièces; calcul Québec familial distinct."))
    return tuple(lignes)
