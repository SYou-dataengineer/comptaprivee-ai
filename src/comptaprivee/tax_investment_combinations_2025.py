"""Bloc 3H-A : combinaison contrôlée intérêts + dividendes canadiens 2025.

Cette première fondation ne branche pas encore la combinaison au moteur global.
Elle consolide une paire T5/RL-3 contenant simultanément :
- intérêts T5 13 / RL-3 D;
- dividendes T5 10/11/12/24/25/26 et RL-3 A1/A2/B/C;
et calcule une seule assiette FSS globale sur les revenus de placement visés.
"""
from dataclasses import dataclass, replace
from decimal import Decimal

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

def lignes_resume_interets_dividendes_2025(combinaison: CombinaisonInteretsDividendes2025) -> list[str]:
    if not combinaison.present:
        return []
    return [
        "",
        "COMBINAISON CONTRÔLÉE 2025 — BLOC 3H-A",
        "Intérêts canadiens + dividendes canadiens validés sur la même paire T5/RL-3.",
        f"Assiette FSS globale 446 : {combinaison.assiette_fss:.2f} $ (130 + 166 + 167; majoration exclue).",
        f"FSS globale 446 : {combinaison.cotisation_fss:.2f} $; comptée une seule fois.",
        "Les crédits dividendes 40425/415 restent appliqués séparément.",
    ]
