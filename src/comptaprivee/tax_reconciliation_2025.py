"""Rapprochement fiscal préliminaire Canada + Québec 2025.

Cette étape rapproche :
- l'impôt fédéral de base déjà calculé;
- l'abattement remboursable du Québec de 16,5 %;
- l'impôt Québec préliminaire;
- les retenues d'impôt déjà prélevées sur le T4 et le RL-1.

Le résultat est une ESTIMATION DE BASE pour le profil emploi Québec simple.
Il ne constitue pas une déclaration fiscale complète et ne doit pas être
transmis à l'ARC ou à Revenu Québec sans validation comptable finale.

Sont notamment hors profil : crédits familiaux, médicaux, études, dons,
assurance médicaments, cotisations excédentaires, CNESST/SAAQ, revenus
autonomes, plusieurs employeurs et autres situations particulières.
"""

from dataclasses import dataclass
from decimal import Decimal

from .tax_engine_input_2025 import BaseFiscaleEmploi2025
from .tax_federal_2025 import ImpotFederalPreliminaire2025
from .tax_quebec_2025 import ImpotQuebecPreliminaire2025
from .tax_rules_2025 import QUEBEC_ABATEMENT_RATE, arrondir_cent


ZERO = Decimal("0")


@dataclass(frozen=True)
class RapprochementFiscal2025:
    client: str
    annee_fiscale: int
    province: str

    impot_federal_de_base: Decimal
    abattement_quebec: Decimal
    impot_federal_apres_abattement: Decimal

    impot_quebec_preliminaire: Decimal
    impot_total_preliminaire: Decimal

    retenue_federale: Decimal
    retenue_quebec: Decimal
    retenues_totales: Decimal

    remboursement_estime: Decimal
    solde_estime: Decimal
    resultat: str

    statut: str
    limitations: tuple[str, ...]


def _verifier_coherence(
    base: BaseFiscaleEmploi2025,
    federal: ImpotFederalPreliminaire2025,
    quebec: ImpotQuebecPreliminaire2025,
) -> None:
    if base.client != federal.client or base.client != quebec.client:
        raise ValueError(
            "Les modules fiscal, fédéral et Québec ne concernent "
            "pas le même client."
        )

    if (
        base.annee_fiscale != federal.annee_fiscale
        or base.annee_fiscale != quebec.annee_fiscale
    ):
        raise ValueError(
            "Les modules n'utilisent pas la même année fiscale."
        )

    if base.annee_fiscale != 2025:
        raise ValueError(
            "Cette version du rapprochement accepte uniquement 2025."
        )

    if base.province.strip().lower() not in {"québec", "quebec"}:
        raise ValueError(
            "L'abattement automatique de cette version exige "
            "un dossier Québec."
        )


def calculer_rapprochement_fiscal_2025(
    base: BaseFiscaleEmploi2025,
    federal: ImpotFederalPreliminaire2025,
    quebec: ImpotQuebecPreliminaire2025,
) -> RapprochementFiscal2025:
    """Calcule une estimation de base du remboursement ou du solde."""
    _verifier_coherence(base, federal, quebec)

    abattement = arrondir_cent(
        federal.impot_federal_de_base
        * QUEBEC_ABATEMENT_RATE
    )

    federal_apres_abattement = max(
        arrondir_cent(
            federal.impot_federal_de_base - abattement
        ),
        ZERO,
    )

    impot_total = arrondir_cent(
        federal_apres_abattement
        + quebec.impot_quebec_preliminaire
    )

    retenues_totales = arrondir_cent(
        base.impot_federal_retenu
        + base.impot_quebec_retenu
    )

    difference = arrondir_cent(
        retenues_totales - impot_total
    )

    if difference > ZERO:
        remboursement = difference
        solde = ZERO
        resultat = "Remboursement estimé"
    elif difference < ZERO:
        remboursement = ZERO
        solde = abs(difference)
        resultat = "Solde estimé"
    else:
        remboursement = ZERO
        solde = ZERO
        resultat = "Équilibre estimé"

    return RapprochementFiscal2025(
        client=base.client,
        annee_fiscale=base.annee_fiscale,
        province=base.province,
        impot_federal_de_base=federal.impot_federal_de_base,
        abattement_quebec=abattement,
        impot_federal_apres_abattement=federal_apres_abattement,
        impot_quebec_preliminaire=quebec.impot_quebec_preliminaire,
        impot_total_preliminaire=impot_total,
        retenue_federale=base.impot_federal_retenu,
        retenue_quebec=base.impot_quebec_retenu,
        retenues_totales=retenues_totales,
        remboursement_estime=remboursement,
        solde_estime=solde,
        resultat=resultat,
        statut="ESTIMATION DE BASE — validation comptable obligatoire",
        limitations=(
            "Le calcul couvre uniquement le profil emploi Québec simple 2025.",
            "L'abattement Québec est calculé à 16,5 % de l'impôt fédéral de base.",
            "Les retenues T4 et RL-1 sont comparées aux impôts préliminaires.",
            "Aucun crédit familial, médical, étude, don ou handicap.",
            "Aucune prime d'assurance médicaments ni contribution Québec additionnelle.",
            "Aucun remboursement de cotisations excédentaires RRQ/AE/RQAP.",
            "Aucun revenu autonome, placement, location ou gain en capital.",
            "Aucun traitement avancé CNESST/SAAQ.",
            "Aucune transmission ARC ou Revenu Québec.",
        ),
    )
