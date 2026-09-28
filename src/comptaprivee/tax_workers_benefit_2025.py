"""ACT : annexe 6 Québec 5005-S6 (25), individu salarié sans famille admissible."""
from dataclasses import dataclass
from decimal import Decimal
from .tax_federal_top_up_2025 import montant_decimal_2025
from .tax_rules_2025 import arrondir_cent

ZERO = Decimal("0")


@dataclass(frozen=True)
class AllocationTravailleurs2025:
    reclamer_base: bool = False
    reclamer_supplement: bool = False
    age_fin_2025: int = 0
    avances_rc210_case10: Decimal = ZERO
    avances_rc210_case11: Decimal = ZERO
    source: str = ""
    valide_par_comptable: bool = False
    residence_canada_annee_quebec_fin: bool = False
    sans_conjoint_ni_personne_charge: bool = False
    pas_etudiant_temps_plein_plus_13_semaines: bool = False
    pas_detention_90_jours: bool = False
    aucune_exemption_diplomatique: bool = False
    emploi_10100_uniquement: bool = False
    aucun_revenu_autonome_bourse_exonere: bool = False
    aucun_ajustement_puge_reei: bool = False
    aucun_deces_faillite: bool = False
    rc210_exhaustifs_ou_absence_confirmee: bool = False
    admissibilite_ciph_confirmee: bool = False

    @property
    def present(self) -> bool:
        return bool(self.reclamer_base or self.reclamer_supplement
                    or self.avances_rc210_case10 or self.avances_rc210_case11)


CONFIRMATIONS_ACT = {
    "valide_par_comptable": "Données ACT validées par le comptable",
    "residence_canada_annee_quebec_fin": "Résident du Canada toute l'année et du Québec fin 2025",
    "sans_conjoint_ni_personne_charge": "Sans conjoint ni personne à charge — profil individuel",
    "pas_etudiant_temps_plein_plus_13_semaines": "Pas d'études à temps plein pendant plus de 13 semaines en 2025",
    "pas_detention_90_jours": "Aucune détention de 90 jours ou plus en 2025",
    "aucune_exemption_diplomatique": "Aucune exemption fiscale diplomatique en 2025",
    "emploi_10100_uniquement": "Revenu de travail limité à 10100; aucun revenu 10400",
    "aucun_revenu_autonome_bourse_exonere": "Aucun revenu autonome, bourse imposable ou revenu exonéré à intégrer",
    "aucun_ajustement_puge_reei": "Aucun revenu ni remboursement PUGE/REEI à ajuster",
    "aucun_deces_faillite": "Aucun décès ni faillite — traitements hors profil",
    "rc210_exhaustifs_ou_absence_confirmee": "Toutes les avances RC210 saisies, ou absence de RC210 confirmée",
}


def valider_allocation_travailleurs_2025(p: AllocationTravailleurs2025) -> AllocationTravailleurs2025:
    if not isinstance(p, AllocationTravailleurs2025):
        raise ValueError("Profil ACT invalide.")
    for nom in ("reclamer_base", "reclamer_supplement", "admissibilite_ciph_confirmee", *CONFIRMATIONS_ACT):
        if type(getattr(p, nom)) is not bool:
            raise ValueError("Confirmation ACT non booléenne : " + nom)
    for nom in ("avances_rc210_case10", "avances_rc210_case11"):
        v = getattr(p, nom)
        if montant_decimal_2025(v, nom) != v:
            raise ValueError("Les avances RC210 doivent être exprimées en cents.")
    if type(p.age_fin_2025) is not int or not 0 <= p.age_fin_2025 <= 120:
        raise ValueError("Âge ACT invalide.")
    if not isinstance(p.source, str):
        raise ValueError("Source ACT invalide.")
    if p.present:
        if p.age_fin_2025 < 19:
            raise ValueError("Le profil ACT individuel exige au moins 19 ans fin 2025.")
        if not p.source.strip():
            raise ValueError("Source ACT obligatoire.")
        for nom, libelle in CONFIRMATIONS_ACT.items():
            if not getattr(p, nom):
                raise ValueError("Confirmation obligatoire : " + libelle)
        if p.reclamer_supplement and not p.admissibilite_ciph_confirmee:
            raise ValueError("Admissibilité au CIPH obligatoire pour le supplément ACT.")
    return p


@dataclass(frozen=True)
class ResultatAllocationTravailleurs2025:
    revenu_travail: Decimal = ZERO
    revenu_net_ajuste: Decimal = ZERO
    base_avant_reduction: Decimal = ZERO
    reduction_base: Decimal = ZERO
    base: Decimal = ZERO
    supplement_avant_reduction: Decimal = ZERO
    reduction_supplement: Decimal = ZERO
    supplement: Decimal = ZERO
    ligne_45300: Decimal = ZERO
    ligne_41500: Decimal = ZERO


def calculer_allocation_travailleurs_2025(p: AllocationTravailleurs2025, *,
        revenu_travail: Decimal, revenu_net: Decimal) -> ResultatAllocationTravailleurs2025:
    valider_allocation_travailleurs_2025(p)
    if not p.present:
        return ResultatAllocationTravailleurs2025()
    travail = montant_decimal_2025(revenu_travail, "Revenu travail ACT")
    net = montant_decimal_2025(revenu_net, "Revenu net ACT")
    base_avant = min(Decimal("3812.06"), arrondir_cent(max(travail - Decimal(2400), ZERO) * Decimal(".373"))) if p.reclamer_base else ZERO
    reduction_base = arrondir_cent(max(net - Decimal("14170.05"), ZERO) * Decimal(".20")) if p.reclamer_base else ZERO
    base = max(base_avant - reduction_base, ZERO)
    supp_avant = min(Decimal("851.31"), arrondir_cent(max(travail - Decimal(1200), ZERO) * Decimal(".40"))) if p.reclamer_supplement else ZERO
    reduction_supp = arrondir_cent(max(net - Decimal("33230.35"), ZERO) * Decimal(".20")) if p.reclamer_supplement else ZERO
    supp = max(supp_avant - reduction_supp, ZERO)
    credit = base + supp
    avances = min(credit, p.avances_rc210_case10 + p.avances_rc210_case11)
    return ResultatAllocationTravailleurs2025(travail, net, base_avant, reduction_base,
        base, supp_avant, reduction_supp, supp, credit, avances)


def lignes_allocation_travailleurs_2025(p: AllocationTravailleurs2025, r: ResultatAllocationTravailleurs2025) -> list[str]:
    if not p.present:
        return []
    return ["", "ALLOCATION CANADIENNE POUR LES TRAVAILLEURS — BLOC 5E",
        f"Source validée par le comptable : {p.source}",
        "Annexe 6 Québec 2025, profil individuel salarié; admissibilité confirmée.",
        f"Choix : base demandée {'oui' if p.reclamer_base else 'non'}; supplément demandé {'oui' if p.reclamer_supplement else 'non'}.",
        f"Revenu de travail 10100 : {r.revenu_travail:.2f} $; revenu net ajusté : {r.revenu_net_ajuste:.2f} $",
        f"Base : min(3812.06, 37.3 % de l'excédent sur 2400) = {r.base_avant_reduction:.2f} $",
        f"Réduction base : 20 % de l'excédent sur 14170.05 = {r.reduction_base:.2f} $",
        f"ACT de base après réduction : {r.base:.2f} $",
        f"Supplément CIPH : min(851.31, 40 % de l'excédent sur 1200) = {r.supplement_avant_reduction:.2f} $",
        f"Réduction supplément : 20 % de l'excédent sur 33230.35 = {r.reduction_supplement:.2f} $",
        f"Supplément après réduction : {r.supplement:.2f} $",
        f"Ligne 45300 remboursable : {r.ligne_45300:.2f} $",
        f"RC210 : case 10 {p.avances_rc210_case10:.2f} $; case 11 {p.avances_rc210_case11:.2f} $",
        f"Ligne 41500 : min(45300, avances RC210) = {r.ligne_41500:.2f} $",
        "41500 augmente l'impôt net 42000; base 42900 et abattement 44000 inchangés."]
