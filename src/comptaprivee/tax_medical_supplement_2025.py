"""45200, feuille fédérale 2025 page 9 : profil individuel salarié simple."""
from dataclasses import dataclass
from decimal import Decimal
from .tax_federal_top_up_2025 import montant_decimal_2025
from .tax_rules_2025 import arrondir_cent

ZERO = Decimal("0")


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


CONFIRMATIONS_SUPPLEMENT = {
    "valide_par_comptable": "Données et demande validées par le comptable",
    "resident_canada_toute_annee": "Résidence au Canada pendant toute l'année 2025",
    "sans_conjoint_ni_personne_charge": "Sans conjoint ni personne à charge — profil simple",
    "emploi_10100_uniquement": "Revenu d'emploi limité à 10100, aucun autre emploi 10400",
    "aucun_regime_perte_salaire": "Aucun montant de régime d'assurance-salaire dans le revenu d'emploi",
    "aucun_revenu_autonome": "Aucun revenu de travail autonome",
    "aucun_ajustement_puge_reei": "Aucun revenu ni remboursement PUGE/REEI à ajuster",
    "aucune_ligne_21500_23100": "Aucune déduction 21500 ou 23100 à intégrer",
    "aucun_deces_faillite": "Aucun décès ni faillite — traitements hors profil",
}


def valider_supplement_medical_2025(p: SupplementMedical2025) -> SupplementMedical2025:
    if not isinstance(p, SupplementMedical2025):
        raise ValueError("Profil supplément médical invalide.")
    for nom in ("reclamer", *CONFIRMATIONS_SUPPLEMENT):
        if type(getattr(p, nom)) is not bool:
            raise ValueError("Confirmation supplément médical non booléenne : " + nom)
    if type(p.age_fin_2025) is not int or not 0 <= p.age_fin_2025 <= 120:
        raise ValueError("Âge fin 2025 invalide.")
    if not isinstance(p.source, str):
        raise ValueError("Source supplément médical invalide.")
    if p.reclamer:
        if p.age_fin_2025 < 18:
            raise ValueError("Le supplément médical exige au moins 18 ans à la fin de 2025.")
        if not p.source.strip():
            raise ValueError("Source du supplément médical obligatoire.")
        for nom, libelle in CONFIRMATIONS_SUPPLEMENT.items():
            if not getattr(p, nom):
                raise ValueError("Confirmation obligatoire : " + libelle)
    return p


@dataclass(frozen=True)
class ResultatSupplementMedical2025:
    revenu_travail: Decimal = ZERO
    revenu_familial_ajuste: Decimal = ZERO
    ligne_33200: Decimal = ZERO
    montant_avant_reduction: Decimal = ZERO
    reduction_revenu: Decimal = ZERO
    ligne_45200: Decimal = ZERO


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
    reduction = arrondir_cent(max(revenu_net - Decimal("33294"), ZERO) * Decimal(".05"))
    credit = max(avant - reduction, ZERO) if travail >= Decimal("4390") else ZERO
    return ResultatSupplementMedical2025(travail, revenu_net, medical, avant, reduction, credit)


def lignes_supplement_medical_2025(p: SupplementMedical2025, r: ResultatSupplementMedical2025) -> list[str]:
    if not p.reclamer:
        return []
    return ["", "SUPPLÉMENT REMBOURSABLE POUR FRAIS MÉDICAUX — BLOC 5D",
            f"Source validée par le comptable : {p.source}",
            f"Revenu de travail net admissible : {r.revenu_travail:.2f} $ (minimum 4390.00 $)",
            f"Revenu familial ajusté, profil individuel : {r.revenu_familial_ajuste:.2f} $",
            f"Base médicale 33200 : {r.ligne_33200:.2f} $; ligne 21500 : 0.00 $",
            f"Minimum de 1504.00 $ et 25 % de 33200 : {r.montant_avant_reduction:.2f} $",
            f"Réduction de 5 % du revenu au-delà de 33294.00 $ : {r.reduction_revenu:.2f} $",
            f"Ligne 45200 remboursable : {r.ligne_45200:.2f} $",
            "Ajout unique au rapprochement; frais médicaux non remboursables conservés."]
