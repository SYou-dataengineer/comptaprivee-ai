"""Bloc 3H-A : combinaison contrôlée intérêts + dividendes canadiens 2025.

Cette fondation est branchée au moteur global et sert aussi de base aux Blocs 3H-B et 3H-C.
Elle consolide une paire T5/RL-3 contenant simultanément :
- intérêts T5 13 / RL-3 D;
- dividendes T5 10/11/12/24/25/26 et RL-3 A1/A2/B/C;
et calcule une seule assiette FSS globale sur les revenus de placement visés.
"""
from dataclasses import dataclass, replace
from decimal import Decimal

from .tax_capital_gains_2025 import (
    GainsCapital2025,
    ProfilCapital2025,
    consolider_capital_2025,
)
from .tax_dividend_income_2025 import (
    Dividendes2025,
    ProfilDividendes2025,
    consolider_dividendes_2025,
)
from .tax_employment_insurance_2025 import cotisation_fss_prestations_2025
from .tax_interest_income_2025 import (
    Interets2025,
    ProfilInterets2025,
    consolider_interets_2025,
)
from .tax_validated_case import DossierFiscalValide

ZERO = Decimal("0")

CASES_INTERETS = {
    ("T5", "13"),
    ("T5", "23"),
    ("RL-3", "D"),
}
CASES_DIVIDENDES = {
    ("T5", "10"),
    ("T5", "11"),
    ("T5", "12"),
    ("T5", "24"),
    ("T5", "25"),
    ("T5", "26"),
    ("T5", "23"),
    ("RL-3", "A1"),
    ("RL-3", "A2"),
    ("RL-3", "B"),
    ("RL-3", "C"),
}
CASES_COMBINEES = CASES_INTERETS | CASES_DIVIDENDES


@dataclass(frozen=True)
class CombinaisonInteretsDividendes2025:
    interets: Interets2025 = Interets2025()
    dividendes: Dividendes2025 = Dividendes2025()
    assiette_fss: Decimal = ZERO
    cotisation_fss: Decimal = ZERO
    present: bool = False
    avec_frais: bool = False
    avec_capital: bool = False
    avec_reports: bool = False

@dataclass(frozen=True)
class CombinaisonPlacementsCanadiens2025:
    interets: Interets2025 = Interets2025()
    dividendes: Dividendes2025 = Dividendes2025()
    capital: GainsCapital2025 = GainsCapital2025()
    assiette_fss: Decimal = ZERO
    cotisation_fss: Decimal = ZERO
    present: bool = False


def _dossier_filtre(
    dossier: DossierFiscalValide,
    cases: set[tuple[str, str]],
) -> DossierFiscalValide:
    donnees = tuple(
        d
        for d in dossier.donnees_validees
        if d.type_document in {"T4", "RL-1"}
        or (d.type_document, d.case) in cases
    )
    documents_utilises = {d.document.resolve() for d in donnees}
    documents = tuple(
        p for p in dossier.documents if p.resolve() in documents_utilises
    )
    return replace(
        dossier,
        documents=documents,
        donnees_validees=donnees,
    )



def _montant_non_nul_detectable(valeur: Decimal) -> bool:
    """Détection tolérante : les validateurs métiers restent responsables des montants invalides."""
    return valeur.is_finite() and not valeur.is_zero()


def detecter_interets_dividendes_2025(dossier: DossierFiscalValide) -> bool:
    """Détecte uniquement la présence simultanée de montants finis non nuls 3H-A."""
    interets = any(
        (d.type_document, d.case) in {("T5", "13"), ("RL-3", "D")}
        and _montant_non_nul_detectable(d.valeur_validee)
        for d in dossier.donnees_validees
    )
    dividendes = any(
        (d.type_document, d.case)
        in {
            ("T5", "10"),
            ("T5", "24"),
            ("RL-3", "A1"),
            ("RL-3", "A2"),
        }
        and _montant_non_nul_detectable(d.valeur_validee)
        for d in dossier.donnees_validees
    )
    return interets and dividendes


def consolider_interets_dividendes_2025(
    dossier: DossierFiscalValide,
    profil_interets: ProfilInterets2025,
    profil_dividendes: ProfilDividendes2025,
) -> CombinaisonInteretsDividendes2025:
    """Valide une seule paire T5/RL-3 combinant intérêts et dividendes."""
    if dossier.annee_fiscale != 2025:
        raise ValueError("Combinaison 3H-A : année 2025 requise.")
    if dossier.province.casefold() not in {"québec", "quebec"}:
        raise ValueError("Combinaison 3H-A : dossier Québec requis.")
    if profil_interets.nature != "T5_RL3":
        raise ValueError(
            "Combinaison 3H-A : seuls les intérêts T5/RL-3 sont couverts."
        )
    if not profil_interets.confirme or not profil_dividendes.confirme:
        raise ValueError(
            "Combinaison 3H-A : confirmez séparément intérêts et dividendes."
        )

    autorises = {"T4", "RL-1", "T5", "RL-3"}
    if any(d.type_document not in autorises for d in dossier.donnees_validees):
        raise ValueError(
            "Combinaison 3H-A : autre placement, prestation ou feuillet hors périmètre."
        )

    for d in dossier.donnees_validees:
        if (
            d.type_document in {"T5", "RL-3"}
            and d.valeur_validee != ZERO
            and (d.type_document, d.case) not in CASES_COMBINEES
        ):
            raise ValueError(
                "Combinaison 3H-A : case T5/RL-3 non couverte ou autre revenu présent."
            )

    dossier_interets = _dossier_filtre(dossier, CASES_INTERETS)
    dossier_dividendes = _dossier_filtre(dossier, CASES_DIVIDENDES)

    interets = consolider_interets_2025(
        dossier_interets,
        profil_interets,
    )
    dividendes = consolider_dividendes_2025(
        dossier_dividendes,
        profil_dividendes,
    )

    if not interets.present:
        raise ValueError("Combinaison 3H-A : intérêts absents.")
    if not dividendes.present or dividendes.ligne_166 + dividendes.ligne_167 <= ZERO:
        raise ValueError("Combinaison 3H-A : dividendes réels positifs absents.")

    # Annexe F : les dividendes entrent dans le revenu total au montant
    # imposable, puis la majoration (128 - 166 - 167) est retirée.
    # L'assiette combinée correspond donc ici aux intérêts ligne 130
    # plus les dividendes réels lignes 166 + 167.
    assiette_fss = (
        interets.ligne_130
        + dividendes.ligne_166
        + dividendes.ligne_167
    )
    cotisation_fss = cotisation_fss_prestations_2025(assiette_fss)

    interets = replace(interets, cotisation_fss=cotisation_fss)
    dividendes = replace(dividendes, cotisation_fss=ZERO)

    return CombinaisonInteretsDividendes2025(
        interets=interets,
        dividendes=dividendes,
        assiette_fss=assiette_fss,
        cotisation_fss=cotisation_fss,
        present=True,
    )

def consolider_interets_dividendes_capital_2025(
    dossier: DossierFiscalValide,
    profil_interets: ProfilInterets2025,
    profil_dividendes: ProfilDividendes2025,
    profil_capital: ProfilCapital2025,
) -> CombinaisonPlacementsCanadiens2025:
    # Bloc 3H-C : intérêts + dividendes T5/RL-3 et une vente simple T5008/RL-18.
    if dossier.annee_fiscale != 2025:
        raise ValueError("Combinaison 3H-C : année 2025 requise.")
    if dossier.province.casefold() not in {"québec", "quebec"}:
        raise ValueError("Combinaison 3H-C : dossier Québec requis.")

    autorises = {"T4", "RL-1", "T5", "RL-3", "T5008", "RL-18"}
    if any(d.type_document not in autorises for d in dossier.donnees_validees):
        raise ValueError(
            "Combinaison 3H-C : autre placement, prestation ou feuillet hors périmètre."
        )

    dossier_interets_dividendes = _dossier_filtre(dossier, CASES_COMBINEES)
    combinaison = consolider_interets_dividendes_2025(
        dossier_interets_dividendes,
        profil_interets,
        profil_dividendes,
    )

    donnees_capital = tuple(
        d
        for d in dossier.donnees_validees
        if d.type_document in {"T4", "RL-1", "T5008", "RL-18"}
    )
    documents_capital = {d.document.resolve() for d in donnees_capital}
    dossier_capital = replace(
        dossier,
        documents=tuple(
            p for p in dossier.documents if p.resolve() in documents_capital
        ),
        donnees_validees=donnees_capital,
    )
    capital = consolider_capital_2025(dossier_capital, profil_capital)
    if not capital.present:
        raise ValueError("Combinaison 3H-C : gain/perte en capital absent.")

    assiette_fss = (
        combinaison.interets.ligne_130
        + combinaison.dividendes.ligne_166
        + combinaison.dividendes.ligne_167
        + capital.ligne_139
    )
    cotisation_fss = cotisation_fss_prestations_2025(assiette_fss)

    interets = replace(combinaison.interets, cotisation_fss=cotisation_fss)
    dividendes = replace(combinaison.dividendes, cotisation_fss=ZERO)
    capital = replace(capital, cotisation_fss=ZERO)

    return CombinaisonPlacementsCanadiens2025(
        interets=interets,
        dividendes=dividendes,
        capital=capital,
        assiette_fss=assiette_fss,
        cotisation_fss=cotisation_fss,
        present=True,
    )


def lignes_resume_interets_dividendes_2025(combinaison: CombinaisonInteretsDividendes2025) -> list[str]:
    if not combinaison.present:
        return []
    if combinaison.avec_capital and combinaison.avec_frais:
        bloc = "3H-D"
        formule = "130 + 166 + 167 + 139 - 231; majoration exclue"
    elif combinaison.avec_capital and combinaison.avec_reports:
        bloc = "3H-E"
        formule = "130 + 166 + 167 + 139; reports 25300/290 sans effet FSS"
    elif combinaison.avec_capital:
        bloc = "3H-C"
        formule = "130 + 166 + 167 + 139; majoration exclue"
    elif combinaison.avec_frais:
        bloc = "3H-B"
        formule = "130 + 166 + 167 - 231; majoration exclue"
    else:
        bloc = "3H-A"
        formule = "130 + 166 + 167; majoration exclue"
    lignes = [
        "",
        f"COMBINAISON CONTRÔLÉE 2025 — BLOC {bloc}",
        "Intérêts canadiens + dividendes canadiens validés sur la même paire T5/RL-3.",
        f"Assiette FSS globale 446 : {combinaison.assiette_fss:.2f} $ ({formule}).",
        f"FSS globale 446 : {combinaison.cotisation_fss:.2f} $; comptée une seule fois.",
        "Les crédits dividendes 40425/415 restent appliqués séparément.",
    ]
    if combinaison.avec_frais:
        lignes.append(
            "Frais de placement 3E validés : la ligne 231 réduit l'assiette FSS; "
            "le report 252 n'a aucun effet sur cette assiette."
        )
    if combinaison.avec_capital:
        lignes.append(
            "Gain en capital 3D validé : seule la ligne 139 positive entre dans "
            "l'assiette FSS; une perte 2025 ne réduit pas les intérêts/dividendes."
        )
    if combinaison.avec_capital and combinaison.avec_frais:
        lignes.append(
            "Bloc 3H-D : la ligne 231 réduit l'assiette FSS après ajout de la ligne "
            "139; la ligne 252 reste sans effet sur cette assiette."
        )
    if combinaison.avec_capital and combinaison.avec_reports:
        lignes.append(
            "Bloc 3H-E : les reports 25300/290 réduisent seulement le revenu "
            "imposable; ils ne modifient ni le revenu total/net ni l'assiette FSS."
        )
    return lignes
