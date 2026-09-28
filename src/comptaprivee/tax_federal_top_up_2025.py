"""T1 Québec 2025, partie B; feuille 5000-D1 (25), ligne 34990.

33500 est une somme de montants admissibles; 33800 est un crédit fiscal.
34990 complète ce crédit; 35000 additionne 33800, 34900 et 34990.
40425 et 40500 sont exclus. Ce module ne détermine aucune admissibilité.
"""

from dataclasses import dataclass
from decimal import Decimal

from .tax_rules_2025 import arrondir_cent

ZERO = Decimal("0")
TAUX_CREDITS_2025 = Decimal("0.145")
SEUIL_CREDIT_COMPENSATOIRE_2025 = Decimal("8319.38")
TAUX_CREDIT_COMPENSATOIRE_2025 = Decimal("0.0345")
SOURCE_34990_2025 = "https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5000-d1/5000-d1-25e.pdf"
# Seulement les lignes déjà prises en charge; 33099 brut est remplacé par 33200.
LIGNES_BASE_33500 = frozenset({
    "30000", "30100", "30300", "30400", "30425", "30450", "30500",
    "30800", "31200", "31205", "31260", "31270", "31285", "31400",
    "31600", "32300", "33200",
})


def montant_decimal_2025(valeur: Decimal, libelle: str) -> Decimal:
    if not isinstance(valeur, Decimal) or not valeur.is_finite() or valeur < ZERO:
        raise ValueError(f"{libelle} doit être un Decimal fini non négatif.")
    return arrondir_cent(valeur)


def calculer_base_33500_2025(montants: tuple[tuple[str, Decimal], ...]) -> Decimal:
    codes = set()
    total = ZERO
    for code, valeur in montants:
        if code not in LIGNES_BASE_33500 or code in codes:
            raise ValueError(f"Ligne 33500 inconnue ou comptée deux fois : {code}.")
        codes.add(code)
        total += montant_decimal_2025(valeur, code)
    return arrondir_cent(total)


def calculer_ligne_33800_2025(base_33500: Decimal) -> Decimal:
    return arrondir_cent(montant_decimal_2025(base_33500, "33500") * TAUX_CREDITS_2025)


def calculer_annexe9_ligne22_2025(dons_admissibles: Decimal) -> Decimal:
    """Crédit sur les premiers 200 $ réclamés, et non le total 34900."""
    dons = montant_decimal_2025(dons_admissibles, "Dons réclamés")
    return arrondir_cent(min(dons, Decimal("200")) * TAUX_CREDITS_2025)


def calculer_credit_compensatoire_2025(
    ligne_33800: Decimal, annexe9_ligne22: Decimal,
) -> Decimal:
    credit = montant_decimal_2025(ligne_33800, "33800")
    dons = montant_decimal_2025(annexe9_ligne22, "Annexe 9 ligne 22")
    if dons > Decimal("29.00"):
        raise ValueError("Annexe 9 ligne 22 ne peut pas dépasser 29,00 $ en 2025.")
    excedent = max(credit + dons - SEUIL_CREDIT_COMPENSATOIRE_2025, ZERO)
    return arrondir_cent(excedent * TAUX_CREDIT_COMPENSATOIRE_2025)


@dataclass(frozen=True)
class CreditsFederauxNonRemboursables2025:
    montants_par_ligne: tuple[tuple[str, Decimal], ...]
    base_ligne_33500: Decimal
    credit_ligne_33800: Decimal
    annexe9_ligne22: Decimal
    credit_dons_ligne_34900: Decimal
    credit_compensatoire_ligne_34990: Decimal
    total_credits_ligne_35000: Decimal


def calculer_credits_non_remboursables_2025(
    montants: tuple[tuple[str, Decimal], ...],
    annexe9_ligne22: Decimal,
    credit_dons_ligne_34900: Decimal,
) -> CreditsFederauxNonRemboursables2025:
    base = calculer_base_33500_2025(montants)
    credit = calculer_ligne_33800_2025(base)
    dons22 = montant_decimal_2025(annexe9_ligne22, "Annexe 9 ligne 22")
    dons = montant_decimal_2025(credit_dons_ligne_34900, "34900")
    if dons22 > dons:
        raise ValueError("Annexe 9 ligne 22 doit être incluse dans 34900.")
    compensation = calculer_credit_compensatoire_2025(credit, dons22)
    return CreditsFederauxNonRemboursables2025(
        tuple((code, montant_decimal_2025(valeur, code)) for code, valeur in montants),
        base, credit, dons22, dons, compensation,
        arrondir_cent(credit + dons + compensation),
    )


def valider_scolarite_sans_report_2025(
    frais: Decimal, revenu_imposable: Decimal, impot_brut: Decimal, base_ligne105: Decimal,
) -> Decimal:
    """Annexe 11 Québec, lignes 11–17 : sans report, transfert ni formation.

    Ligne 105 précède scolarité, médical, dons et compensation. Aucun calcul
    circulaire avec 34990. L'excédent reste refusé dans le profil actuel.
    """
    frais = montant_decimal_2025(frais, "Scolarité")
    revenu = montant_decimal_2025(revenu_imposable, "Revenu imposable")
    brut = montant_decimal_2025(impot_brut, "Impôt brut")
    base = montant_decimal_2025(base_ligne105, "Ligne 105")
    equivalent = revenu if revenu <= Decimal("57375") else brut / TAUX_CREDITS_2025
    disponible = arrondir_cent(max(equivalent - base, ZERO))
    if frais > disponible:
        raise ValueError("Une partie de la scolarité doit être reportée; report hors profil 5A (annexe 11).")
    return frais


def lignes_resume_credit_compensatoire_2025(
    resultat: CreditsFederauxNonRemboursables2025 | None,
) -> list[str]:
    if resultat is None:
        return []
    return [
        "", "CRÉDIT COMPENSATOIRE FÉDÉRAL 2025",
        f"Base des montants admissibles — ligne 33500 : {resultat.base_ligne_33500:.2f} $",
        f"Crédit ligne 33800 : {resultat.credit_ligne_33800:.2f} $",
        f"Annexe 9 ligne 22 : {resultat.annexe9_ligne22:.2f} $",
        "Seuil : 8 319,38 $; taux : 3,45 % (feuille fédérale 2025).",
        f"Ligne 34990 : {resultat.credit_compensatoire_ligne_34990:.2f} $",
        f"Total des crédits — ligne 35000 : {resultat.total_credits_ligne_35000:.2f} $",
    ]
