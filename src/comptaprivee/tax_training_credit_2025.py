"""CCF 2025 : annexe 11, ligne 45350; données documentées, aucun suivi ARC."""
from dataclasses import dataclass
from decimal import Decimal

from .tax_federal_top_up_2025 import montant_decimal_2025
from .tax_rules_2025 import arrondir_cent

ZERO = Decimal("0")


@dataclass(frozen=True)
class Formation2025:
    frais_canadiens: Decimal = ZERO
    plafond_avis_2025: Decimal = ZERO
    age_fin_2025: int = 0
    source: str = ""
    reclamer_maximum: bool = False
    valide_par_comptable: bool = False
    resident_canada_toute_annee: bool = False
    declaration_2025_confirmee: bool = False
    frais_etablissement_canadien_admissibles: bool = False
    plafond_avis_confirme: bool = False
    aucun_deces_ni_faillite: bool = False


CONFIRMATIONS_FORMATION = {
    "valide_par_comptable": "Frais et choix de réclamer validés par le comptable",
    "resident_canada_toute_annee": "Résidence au Canada pendant toute l'année 2025",
    "declaration_2025_confirmee": "Déclaration de revenus 2025 à produire",
    "frais_etablissement_canadien_admissibles": "Frais 2025 admissibles au CCF, établissement canadien ou examen admissible vérifié",
    "plafond_avis_confirme": "Plafond 2025 vérifié sur le dernier avis ARC de cotisation ou nouvelle cotisation",
    "aucun_deces_ni_faillite": "Aucun décès ni faillite : ces traitements sont hors profil 5C",
}


def valider_formation_2025(p: Formation2025) -> Formation2025:
    if not isinstance(p, Formation2025):
        raise ValueError("Profil formation invalide.")
    for nom in ("frais_canadiens", "plafond_avis_2025"):
        valeur = getattr(p, nom)
        montant_decimal_2025(valeur, nom)
        if valeur != arrondir_cent(valeur):
            raise ValueError("Les montants formation doivent être au cent près.")
    if type(p.age_fin_2025) is not int or not 0 <= p.age_fin_2025 <= 120:
        raise ValueError("Âge fin 2025 invalide.")
    if not isinstance(p.source, str):
        raise ValueError("Source formation invalide.")
    for nom in ("reclamer_maximum", *CONFIRMATIONS_FORMATION):
        if type(getattr(p, nom)) is not bool:
            raise ValueError("Confirmation formation non booléenne : " + nom)
    if p.plafond_avis_2025 > Decimal("1500"):
        raise ValueError("Plafond 2025 incohérent : au plus six accumulations de 250 $ depuis 2019.")
    if p.frais_canadiens or p.plafond_avis_2025 or p.reclamer_maximum:
        if not p.source.strip():
            raise ValueError("Source des frais et de l'avis ARC obligatoire.")
        for nom, libelle in CONFIRMATIONS_FORMATION.items():
            if not getattr(p, nom):
                raise ValueError("Confirmation obligatoire : " + libelle)
    if p.reclamer_maximum:
        if not 26 <= p.age_fin_2025 <= 65:
            raise ValueError("Le CCF 2025 exige un âge de 26 à 65 ans au 31 décembre.")
        if p.plafond_avis_2025 <= ZERO or p.frais_canadiens <= ZERO:
            raise ValueError("Frais et plafond positifs requis pour réclamer le CCF.")
    return p


def credit_formation_2025(p: Formation2025) -> Decimal:
    valider_formation_2025(p)
    if not p.reclamer_maximum:
        return ZERO
    return min(p.plafond_avis_2025, arrondir_cent(p.frais_canadiens * Decimal("0.5")))


def lignes_formation_2025(p: Formation2025) -> list[str]:
    if p == Formation2025():
        return []
    credit = credit_formation_2025(p)
    return ["", "CRÉDIT CANADIEN POUR LA FORMATION 2025 — BLOC 5C",
            f"Source validée par le comptable : {p.source}",
            f"Frais canadiens admissibles : {p.frais_canadiens:.2f} $",
            f"Plafond avis ARC 2025 : {p.plafond_avis_2025:.2f} $",
            f"Ligne 45350 remboursable : {credit:.2f} $",
            "Choix du maximum : minimum du plafond et de 50 % des frais; sinon aucune réclamation.",
            f"Réduction des frais fédéraux et Québec : {credit:.2f} $ dans chaque juridiction.",
            "Aucune accumulation future calculée; aucun suivi automatique ARC."]
