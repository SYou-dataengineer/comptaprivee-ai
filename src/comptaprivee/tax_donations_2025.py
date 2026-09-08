from dataclasses import dataclass
from decimal import Decimal
from .tax_rules_2025 import arrondir_cent

ZERO = Decimal("0")
DEUX_CENTS = Decimal("200")
TAUX_FEDERAL_PREMIERS_200_2025 = Decimal("0.145")
TAUX_FEDERAL_EXCEDENT_2025 = Decimal("0.29")
SEUIL_FEDERAL_TAUX_SUPERIEUR_2025 = Decimal("253414")
TAUX_QUEBEC_PREMIERS_200_2025 = Decimal("0.20")
TAUX_QUEBEC_EXCEDENT_SIMPLE_2025 = Decimal("0.24")
SEUIL_QUEBEC_TAUX_SUPERIEUR_2025 = Decimal("129590")


@dataclass(frozen=True)
class DonsBienfaisance2025:
    montant_admissible_federal: Decimal = ZERO
    montant_admissible_quebec: Decimal = ZERO
    source_federale: str = ""
    source_quebec: str = ""
    valide_par_comptable: bool = False
    donataire_reconnu_confirme: bool = False
    dons_monetaires_2025_uniquement: bool = False
    aucun_report_anterieur: bool = False
    inclut_dons_jan_fev_2025: bool = False
    dons_jan_fev_deja_reclames_2024: bool = False


def aucun_don_bienfaisance_2025():
    return DonsBienfaisance2025()


def valider_dons_bienfaisance_2025(dons):
    fed = dons.montant_admissible_federal
    qc = dons.montant_admissible_quebec
    if fed < ZERO:
        raise ValueError("Le montant admissible fédéral des dons ne peut pas être négatif.")
    if qc < ZERO:
        raise ValueError("Le montant admissible Québec des dons ne peut pas être négatif.")
    if fed == ZERO and qc == ZERO:
        return dons
    if not dons.valide_par_comptable:
        raise ValueError("Les dons doivent être validés par le comptable.")
    if not dons.donataire_reconnu_confirme:
        raise ValueError("Le statut de donataire reconnu doit être confirmé.")
    if not dons.dons_monetaires_2025_uniquement:
        raise ValueError("Cette version accepte uniquement les dons monétaires faits en 2025.")
    if not dons.aucun_report_anterieur:
        raise ValueError("Cette version n'accepte pas encore les dons reportés d'une année antérieure.")
    if dons.inclut_dons_jan_fev_2025 and dons.dons_jan_fev_deja_reclames_2024:
        raise ValueError("Un don de janvier ou février 2025 déjà demandé en 2024 ne peut pas être demandé de nouveau.")
    if fed > ZERO and not dons.source_federale.strip():
        raise ValueError("La source fédérale du don est obligatoire.")
    if qc > ZERO and not dons.source_quebec.strip():
        raise ValueError("La source Québec du don est obligatoire.")
    return dons


def credit_federal_dons_2025(dons, revenu_imposable_federal):
    valider_dons_bienfaisance_2025(dons)
    if revenu_imposable_federal < ZERO:
        raise ValueError("Le revenu imposable fédéral ne peut pas être négatif.")
    if revenu_imposable_federal > SEUIL_FEDERAL_TAUX_SUPERIEUR_2025:
        raise ValueError("Le taux fédéral de 33 % est hors profil dans cette version.")
    montant = dons.montant_admissible_federal
    premiers = min(montant, DEUX_CENTS)
    excedent = max(montant - DEUX_CENTS, ZERO)
    return arrondir_cent(
        premiers * TAUX_FEDERAL_PREMIERS_200_2025
        + excedent * TAUX_FEDERAL_EXCEDENT_2025
    )


def credit_quebec_dons_2025(dons, revenu_imposable_quebec):
    valider_dons_bienfaisance_2025(dons)
    if revenu_imposable_quebec < ZERO:
        raise ValueError("Le revenu imposable Québec ne peut pas être négatif.")
    if revenu_imposable_quebec > SEUIL_QUEBEC_TAUX_SUPERIEUR_2025:
        raise ValueError("Le taux Québec de 25,75 % est hors profil dans cette version.")
    montant = dons.montant_admissible_quebec
    premiers = min(montant, DEUX_CENTS)
    excedent = max(montant - DEUX_CENTS, ZERO)
    return arrondir_cent(
        premiers * TAUX_QUEBEC_PREMIERS_200_2025
        + excedent * TAUX_QUEBEC_EXCEDENT_SIMPLE_2025
    )


from dataclasses import replace

from .tax_federal_2025 import ImpotFederalPreliminaire2025
from .tax_quebec_2025 import ImpotQuebecPreliminaire2025


def appliquer_credit_federal_dons_2025(
    impot: ImpotFederalPreliminaire2025,
    dons: DonsBienfaisance2025,
    revenu_imposable_federal: Decimal,
) -> ImpotFederalPreliminaire2025:
    """Applique le crédit fédéral pour dons après les crédits de base."""
    credit = credit_federal_dons_2025(
        dons,
        revenu_imposable_federal,
    )
    if credit == ZERO:
        return impot

    limitations = tuple(
        texte
        for texte in impot.limitations
        if texte != "Aucun don ni crédit transféré."
    ) + (
        "Crédit fédéral pour dons de bienfaisance admissibles inclus.",
    )

    return replace(
        impot,
        impot_federal_de_base=max(
            arrondir_cent(impot.impot_federal_de_base - credit),
            ZERO,
        ),
        limitations=limitations,
    )


def appliquer_credit_quebec_dons_2025(
    impot: ImpotQuebecPreliminaire2025,
    dons: DonsBienfaisance2025,
    revenu_imposable_quebec: Decimal,
) -> ImpotQuebecPreliminaire2025:
    """Applique le crédit Québec pour dons après les crédits déjà intégrés."""
    credit = credit_quebec_dons_2025(
        dons,
        revenu_imposable_quebec,
    )
    if credit == ZERO:
        return impot

    limitations = tuple(
        texte
        for texte in impot.limitations
        if texte != "Aucun crédit handicap, médical, scolarité ou don."
    ) + (
        "Aucun crédit handicap, médical ou scolarité.",
        "Crédit Québec pour dons de bienfaisance admissibles inclus.",
    )

    return replace(
        impot,
        impot_quebec_preliminaire=max(
            arrondir_cent(impot.impot_quebec_preliminaire - credit),
            ZERO,
        ),
        limitations=limitations,
    )
