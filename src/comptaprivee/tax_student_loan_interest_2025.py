"""Bloc 5B fédéral : LIR 118.62, P105 (2025), T1 Québec ligne 31900.

Réclamation choisie par le comptable, jamais déduite automatiquement du solde
d'impôt. Les soldes d'ouverture documentés restent immuables. Aucun suivi ARC.
"""
from dataclasses import dataclass, replace
from decimal import Decimal

from .tax_rules_2025 import arrondir_cent
from .tax_federal_top_up_2025 import (
    CreditsFederauxNonRemboursables2025, calculer_credits_non_remboursables_2025,
    montant_decimal_2025,
)

ZERO = Decimal("0")
ANNEES_REPORTS = tuple(range(2020, 2025))
CONFIRMATIONS_5B = {
    "valide_par_comptable": "Validation comptable des montants et de la réclamation",
    "emprunteur_legal_confirme": "Le contribuable est l'emprunteur légal",
    "pret_gouvernemental_admissible_confirme": "Prêt sous une loi gouvernementale admissible (P105)",
    "paiement_par_contribuable_ou_personne_apparentee_confirme": "Paiement par le contribuable ou une personne apparentée",
    "montants_non_deja_reclames_confirmes": "Montants documentés et non déjà réclamés",
    "aucun_pret_prive_confirme": "Aucun prêt privé",
    "aucun_refinancement_inadmissible_confirme": "Aucun prêt combiné, renégocié ou reconsolidé avec un autre prêt",
    "aucun_interet_jugement_confirme": "Aucun intérêt découlant d'un jugement",
    "aucun_tiers_non_apparente_confirme": "Aucun tiers non apparenté ou lien non établi",
    "contribuable_vivant_confirme": "Contribuable vivant; aucun cas de décès",
    "aucun_transfert_confirme": "Aucun transfert du crédit à une autre personne",
}


@dataclass(frozen=True)
class InteretsPretEtudiant2025:
    interets_payes_2025: Decimal = ZERO
    reports: tuple[tuple[int, Decimal], ...] = ()
    montant_reclame_31900: Decimal = ZERO
    source: str = ""
    valide_par_comptable: bool = False
    emprunteur_legal_confirme: bool = False
    pret_gouvernemental_admissible_confirme: bool = False
    paiement_par_contribuable_ou_personne_apparentee_confirme: bool = False
    montants_non_deja_reclames_confirmes: bool = False
    aucun_pret_prive_confirme: bool = False
    aucun_refinancement_inadmissible_confirme: bool = False
    aucun_interet_jugement_confirme: bool = False
    aucun_tiers_non_apparente_confirme: bool = False
    contribuable_vivant_confirme: bool = False
    aucun_transfert_confirme: bool = False


def valider_interets_pret_etudiant_2025(p: InteretsPretEtudiant2025) -> InteretsPretEtudiant2025:
    courant = montant_decimal_2025(p.interets_payes_2025, "Intérêts 2025")
    reclame = montant_decimal_2025(p.montant_reclame_31900, "Ligne 31900")
    if not isinstance(p.source, str) or not isinstance(p.reports, tuple):
        raise ValueError("Source ou reports 31900 invalides.")
    reports = {}
    for entree in p.reports:
        if not isinstance(entree, tuple) or len(entree) != 2:
            raise ValueError("Chaque report doit contenir une année et un montant.")
        annee, montant = entree
        if type(annee) is not int or annee not in ANNEES_REPORTS or annee in reports:
            raise ValueError("Année de report hors fenêtre 2020–2024 ou dupliquée.")
        reports[annee] = montant_decimal_2025(montant, f"Report {annee}")
    for nom in CONFIRMATIONS_5B:
        if type(getattr(p, nom)) is not bool:
            raise ValueError(f"Confirmation booléenne obligatoire : {nom}.")
    total = courant + sum(reports.values(), ZERO)
    if reclame > total:
        raise ValueError("31900 dépasse les intérêts documentés disponibles.")
    if total:
        if not p.source.strip():
            raise ValueError("La source des intérêts et des reports est obligatoire.")
        for nom, libelle in CONFIRMATIONS_5B.items():
            if not getattr(p, nom):
                raise ValueError(f"Confirmation obligatoire : {libelle}.")
    return replace(p, interets_payes_2025=courant, montant_reclame_31900=reclame,
                   reports=tuple(sorted((a, m) for a, m in reports.items() if m)), source=p.source.strip())


@dataclass(frozen=True)
class ResultatInteretsPretEtudiant2025:
    total_disponible: Decimal = ZERO
    ligne_31900: Decimal = ZERO
    utilises_par_annee: tuple[tuple[int, Decimal], ...] = ()
    non_reclames_par_annee: tuple[tuple[int, Decimal], ...] = ()
    non_reclames_encore_reportables_2026: Decimal = ZERO
    non_reclame_2020_expirant: Decimal = ZERO
    augmentation_33800: Decimal = ZERO
    augmentation_34990: Decimal = ZERO
    augmentation_35000: Decimal = ZERO
    reduction_42900: Decimal = ZERO
    reduction_federale_apres_40500_et_abattement: Decimal = ZERO


def repartir_interets_pret_etudiant_2025(p: InteretsPretEtudiant2025) -> ResultatInteretsPretEtudiant2025:
    p = valider_interets_pret_etudiant_2025(p)
    a_reclamer = p.montant_reclame_31900
    utilises, restants = [], []
    disponibles = p.reports + ((2025, p.interets_payes_2025),)
    for annee, montant in disponibles:
        pris = min(a_reclamer, montant)
        a_reclamer -= pris
        if pris:
            utilises.append((annee, pris))
        if montant > pris:
            restants.append((annee, montant - pris))
    return ResultatInteretsPretEtudiant2025(
        total_disponible=sum((m for _, m in disponibles), ZERO),
        ligne_31900=p.montant_reclame_31900,
        utilises_par_annee=tuple(utilises), non_reclames_par_annee=tuple(restants),
        non_reclames_encore_reportables_2026=sum((m for a, m in restants if a > 2020), ZERO),
        non_reclame_2020_expirant=dict(restants).get(2020, ZERO),
    )


def mesurer_incidence_interets_2025(
    r: ResultatInteretsPretEtudiant2025, credits: CreditsFederauxNonRemboursables2025,
    impot_brut: Decimal, credit_dividendes: Decimal, credit_etranger_demande: Decimal,
) -> ResultatInteretsPretEtudiant2025:
    """Comparaison avec/sans 31900, autres entrées constantes; aucun débit ajouté."""
    if not r.ligne_31900:
        return r
    sans = calculer_credits_non_remboursables_2025(
        tuple((code, valeur) for code, valeur in credits.montants_par_ligne if code != "31900"),
        credits.annexe9_ligne22, credits.credit_dons_ligne_34900,
    )
    def soldes(c):
        base = max(arrondir_cent(impot_brut - c.total_credits_ligne_35000 - credit_dividendes), ZERO)
        net = max(base - credit_etranger_demande, ZERO) - arrondir_cent(base * Decimal(".165"))
        return base, net
    avant, apres = soldes(sans), soldes(credits)
    return replace(r,
        augmentation_33800=credits.credit_ligne_33800 - sans.credit_ligne_33800,
        augmentation_34990=credits.credit_compensatoire_ligne_34990 - sans.credit_compensatoire_ligne_34990,
        augmentation_35000=credits.total_credits_ligne_35000 - sans.total_credits_ligne_35000,
        reduction_42900=avant[0] - apres[0],
        reduction_federale_apres_40500_et_abattement=avant[1] - apres[1],
    )


def lignes_resume_interets_pret_etudiant_2025(p: InteretsPretEtudiant2025, r: ResultatInteretsPretEtudiant2025) -> list[str]:
    if not r.total_disponible:
        return []
    lignes = ["", "INTÉRÊTS SUR PRÊTS ÉTUDIANTS 2025 VALIDÉS — BLOC 5B",
        f"Intérêts payés en 2025 : {p.interets_payes_2025:.2f} $",
        f"Ligne fédérale 31900 : {r.ligne_31900:.2f} $", f"Source : {p.source}",
        "Ordre de réclamation : 2020 → 2021 → 2022 → 2023 → 2024 → 2025."]
    lignes += [f"Année {a} effectivement réclamée : {m:.2f} $" for a, m in r.utilises_par_annee]
    lignes += [f"Année {a} non réclamée : {m:.2f} $" for a, m in r.non_reclames_par_annee]
    lignes += [
        f"Non réclamé encore reportable en 2026 (années 2021–2025) : {r.non_reclames_encore_reportables_2026:.2f} $",
        f"Non réclamé 2020 expirant après 2025 : {r.non_reclame_2020_expirant:.2f} $",
        f"Augmentation 33800 : {r.augmentation_33800:.2f} $; augmentation 34990 : {r.augmentation_34990:.2f} $",
        f"Augmentation 35000 : {r.augmentation_35000:.2f} $; réduction 42900 : {r.reduction_42900:.2f} $",
        f"Réduction fédérale après 40500 et abattement Québec : {r.reduction_federale_apres_40500_et_abattement:.2f} $",
        "Réclamation choisie par le comptable; aucune optimisation ni suivi automatique ARC.",
        "Une réclamation sans économie d'impôt peut gaspiller des intérêts : les montants réclamés ne sont pas remis automatiquement en report.",
        "Crédit Québec distinct (ligne 385) : profil 6B séparé; aucun report implicite de ces soldes fédéraux.",
    ]
    return lignes
