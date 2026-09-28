"""45200, feuille fédérale 2025 page 9 : salarié, seul ou avec famille."""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from .tax_federal_top_up_2025 import montant_decimal_2025
from .tax_rules_2025 import arrondir_cent

ZERO = Decimal("0")
SITUATIONS_SUPPLEMENT = ("sans conjoint", "conjoint", "séparation de 90 jours", "conjoint décédé")


@dataclass(frozen=True)
class SupplementMedical2025:
    reclamer: bool = False
    age_fin_2025: int = 0
    source: str = ""
    valide_par_comptable: bool = False
    resident_canada_toute_annee: bool = False
    sans_conjoint_ni_personne_charge: bool = False
    emploi_10100_uniquement: bool = False
    aucun_regime_perte_salaire: bool = False
    aucun_revenu_autonome: bool = False
    aucun_ajustement_puge_reei: bool = False
    aucune_ligne_21500_23100: bool = False
    aucun_deces_faillite: bool = False
    mode_familial: bool = False
    situation_conjugale: str = ""
    nom_conjoint: str = ""
    revenu_net_conjoint: Decimal = ZERO
    source_conjoint: str = ""
    donnees_familiales_verifiees: bool = False


CONFIRMATIONS_SUPPLEMENT = {
    "valide_par_comptable": "Données et demande validées par le comptable",
    "resident_canada_toute_annee": "Résidence au Canada pendant toute l'année 2025",
    "sans_conjoint_ni_personne_charge": "Sans conjoint ni personne à charge — profil simple",
    "emploi_10100_uniquement": "Revenu d'emploi limité à 10100, aucun autre emploi 10400",
    "aucun_regime_perte_salaire": "Aucun montant de régime d'assurance-salaire dans le revenu d'emploi",
    "aucun_revenu_autonome": "Aucun revenu de travail autonome",
    "aucun_ajustement_puge_reei": "Aucun revenu ni remboursement PUGE/REEI à ajuster, pour vous et le conjoint retenu",
    "aucune_ligne_21500_23100": "Aucune déduction 21500 ou 23100 à intégrer",
    "aucun_deces_faillite": "Demandeur vivant à la fin de 2025, aucune faillite",
}

LIBELLE_FAMILLE_SUPPLEMENT = (
    "Situation et revenu du conjoint vérifiés sur pièces; séparation, si choisie, "
    "due à la rupture pendant au moins 90 jours incluant le 31 décembre 2025; "
    "décès, si choisi, survenu au plus tard le 31 décembre 2025; aucun autre conjoint à intégrer"
)


def revenu_conjoint_supplement(v):
    if not isinstance(v, Decimal) or not v.is_finite():
        raise ValueError("Revenu net du conjoint : Decimal fini requis.")
    try:
        if v != v.quantize(Decimal(".01")):
            raise ValueError("Revenu net du conjoint : cents requis.")
    except InvalidOperation as exc:
        raise ValueError("Revenu net du conjoint trop grand.") from exc
    return v


def valider_supplement_medical_2025(p: SupplementMedical2025) -> SupplementMedical2025:
    if not isinstance(p, SupplementMedical2025):
        raise ValueError("Profil supplément médical invalide.")
    for nom in ("reclamer", "mode_familial", "donnees_familiales_verifiees", *CONFIRMATIONS_SUPPLEMENT):
        if type(getattr(p, nom)) is not bool:
            raise ValueError("Confirmation supplément médical non booléenne : " + nom)
    if type(p.age_fin_2025) is not int or not 0 <= p.age_fin_2025 <= 120:
        raise ValueError("Âge fin 2025 invalide.")
    if not isinstance(p.source, str):
        raise ValueError("Source supplément médical invalide.")
    for nom in ("situation_conjugale", "nom_conjoint", "source_conjoint"):
        if not isinstance(getattr(p, nom), str):
            raise ValueError("Champ familial invalide : " + nom)
    revenu_conjoint_supplement(p.revenu_net_conjoint)
    if not p.mode_familial:
        if any((p.situation_conjugale, p.nom_conjoint, p.revenu_net_conjoint,
                p.source_conjoint, p.donnees_familiales_verifiees)):
            raise ValueError("Données familiales présentes sans mode familial.")
    else:
        if p.situation_conjugale not in SITUATIONS_SUPPLEMENT:
            raise ValueError("Situation conjugale du supplément médical obligatoire.")
        if p.sans_conjoint_ni_personne_charge:
            raise ValueError("Le mode familial ne peut confirmer le profil individuel sans famille.")
        if p.situation_conjugale == "sans conjoint":
            if p.nom_conjoint or p.revenu_net_conjoint or p.source_conjoint:
                raise ValueError("Données de conjoint incompatibles avec sans conjoint.")
        elif not p.nom_conjoint.strip() or not p.source_conjoint.strip():
            raise ValueError("Nom et source du conjoint obligatoires, y compris en cas d'exclusion.")
    if p.reclamer:
        if p.age_fin_2025 < 18:
            raise ValueError("Le supplément médical exige au moins 18 ans à la fin de 2025.")
        if not p.source.strip():
            raise ValueError("Source du supplément médical obligatoire.")
        for nom, libelle in CONFIRMATIONS_SUPPLEMENT.items():
            if p.mode_familial and nom == "sans_conjoint_ni_personne_charge":
                continue
            if not getattr(p, nom):
                raise ValueError("Confirmation obligatoire : " + libelle)
        if p.mode_familial and not p.donnees_familiales_verifiees:
            raise ValueError("Situation et données familiales à vérifier par le comptable.")
    return p


@dataclass(frozen=True)
class ResultatSupplementMedical2025:
    revenu_travail: Decimal = ZERO
    revenu_familial_ajuste: Decimal = ZERO
    ligne_33200: Decimal = ZERO
    montant_avant_reduction: Decimal = ZERO
    reduction_revenu: Decimal = ZERO
    ligne_45200: Decimal = ZERO
    revenu_conjoint_retenu: Decimal = ZERO


def calculer_supplement_medical_2025(p: SupplementMedical2025, *, emploi: Decimal,
        deduction_20700: Decimal, deduction_21200: Decimal, deduction_22900: Decimal,
        revenu_net: Decimal, ligne_33200: Decimal) -> ResultatSupplementMedical2025:
    valider_supplement_medical_2025(p)
    if not p.reclamer:
        return ResultatSupplementMedical2025()
    emploi, rpa, syndicat, depenses, revenu_net, medical = (
        montant_decimal_2025(v, n) for n, v in (
            ("emploi", emploi), ("20700", deduction_20700), ("21200", deduction_21200),
            ("22900", deduction_22900), ("revenu net", revenu_net), ("33200", ligne_33200)))
    travail = max(emploi - rpa - syndicat - depenses, ZERO)
    avant = min(Decimal("1504"), arrondir_cent(medical * Decimal(".25")))
    conjoint = max(p.revenu_net_conjoint, ZERO) if p.mode_familial and p.situation_conjugale == "conjoint" else ZERO
    familial = revenu_net + conjoint
    reduction = arrondir_cent(max(familial - Decimal("33294"), ZERO) * Decimal(".05"))
    credit = max(avant - reduction, ZERO) if travail >= Decimal("4390") else ZERO
    return ResultatSupplementMedical2025(travail, familial, medical, avant, reduction, credit, conjoint)


def verifier_famille_supplement_2025(p, *, demandeur, medical, conjoint_30300,
        personne_30400, conjoint_32600=None, noms_conjoints=(), act_individuel=False):
    """Rapproche les données brutes partagées entre profils, sans recalcul fiscal."""
    if not p.reclamer or not p.mode_familial:
        return
    if act_individuel:
        raise ValueError("ACT individuel incompatible avec le supplément familial; extension ACT familiale requise.")
    normaliser = lambda nom: " ".join(nom.split()).casefold()
    if p.nom_conjoint and normaliser(p.nom_conjoint) == normaliser(demandeur):
        raise ValueError("Le conjoint du supplément médical doit différer du demandeur.")
    noms = list(noms_conjoints) + [x.nom for x in medical.personnes if x.lien == "conjoint"]
    if conjoint_32600 is not None:
        noms.append(conjoint_32600.nom_conjoint)
    if any(n and normaliser(n) != normaliser(p.nom_conjoint) for n in noms):
        raise ValueError("Identité du conjoint divergente entre supplément médical et autres profils.")
    if conjoint_30300.reclamer_montant or conjoint_32600 is not None:
        if p.situation_conjugale != "conjoint":
            raise ValueError("Les profils 30300/32600 actuels exigent un conjoint présent toute l'année.")
        revenus = []
        if conjoint_30300.reclamer_montant:
            revenus.append(conjoint_30300.revenu_net_conjoint_2025)
        if conjoint_32600 is not None:
            revenus.append(conjoint_32600.revenu_net_conjoint)
        if any(r != max(p.revenu_net_conjoint, ZERO) for r in revenus):
            raise ValueError("Revenu net du conjoint divergent entre supplément médical et 30300/32600.")
    if personne_30400.reclamer_montant and p.situation_conjugale == "conjoint":
        raise ValueError("Le profil 30400 actuel exige l'absence de conjoint; situation 45200 contradictoire.")


def lignes_supplement_medical_2025(p: SupplementMedical2025, r: ResultatSupplementMedical2025) -> list[str]:
    if not p.reclamer:
        return []
    return ["", "SUPPLÉMENT REMBOURSABLE POUR FRAIS MÉDICAUX — BLOC 5D",
            f"Source validée par le comptable : {p.source}",
            f"Revenu de travail net admissible : {r.revenu_travail:.2f} $ (minimum 4390.00 $)",
            *([f"Situation familiale validée : {p.situation_conjugale}",
               f"Conjoint : {p.nom_conjoint or 'aucun'}; source : {p.source_conjoint or 'sans objet'}",
               f"Revenu net déclaré du conjoint : {p.revenu_net_conjoint:.2f} $; retenu : {r.revenu_conjoint_retenu:.2f} $",
               "Sans ajustements PUGE/REEI; revenus des personnes à charge exclus du revenu familial."] if p.mode_familial else []),
            f"Revenu familial ajusté : {r.revenu_familial_ajuste:.2f} $",
            f"Base médicale 33200 : {r.ligne_33200:.2f} $; ligne 21500 : 0.00 $",
            f"Minimum de 1504.00 $ et 25 % de 33200 : {r.montant_avant_reduction:.2f} $",
            f"Réduction de 5 % du revenu au-delà de 33294.00 $ : {r.reduction_revenu:.2f} $",
            f"Ligne 45200 remboursable : {r.ligne_45200:.2f} $",
            "Ajout unique au rapprochement; frais médicaux non remboursables conservés."]
