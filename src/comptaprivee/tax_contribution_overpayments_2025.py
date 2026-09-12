"""Cotisations salariales payées en trop - Québec 2025.

Version prudente pour un profil d'emploi Québec simple.

Cette version calcule les remboursements à partir des cotisations réellement
retenues ET des gains validés sur les feuillets :

- RRQ, ligne Québec 452 :
  comparaison des cotisations B.A + B.B avec les cotisations RRQ attendues
  selon les gains admissibles;
- assurance-emploi, ligne fédérale 45000 :
  comparaison avec la prime attendue au taux Québec 2025;
- RQAP, ligne Québec 457 :
  comparaison avec la prime attendue, avec remboursement complet lorsque
  les revenus assujettis au RQAP sont inférieurs à 2 000 $.

Le profil supporté reste volontairement limité :
- résident du Québec au 31 décembre 2025;
- emplois exercés au Québec seulement;
- RRQ seulement, sans RPC;
- aucun travail autonome;
- profil RRQ standard 18 à 64 ans pendant toute l'année;
- aucun cas particulier AE/RQAP;
- données validées par le comptable.

Les cas exigeant une proratisation, un choix spécial, du travail hors Québec,
du RPC, du travail autonome ou un formulaire avancé sont refusés plutôt que
d'estimer un remboursement incorrect.
"""

from dataclasses import dataclass
from decimal import Decimal

from .tax_rules_2025 import (
    EI_MAX_INSURABLE_EARNINGS_QUEBEC_2025,
    EI_RATE_QUEBEC_2025,
    QPIP_MAX_INSURABLE_EARNINGS_2025,
    QPIP_RATE_EMPLOYEE_2025,
    QPP_ADDITIONAL_MAX_PENSIONABLE_EARNINGS_2025,
    QPP_BA_TOTAL_RATE_EMPLOYEE_2025,
    QPP_BASIC_EXEMPTION_2025,
    QPP_MAX_PENSIONABLE_EARNINGS_2025,
    QPP_SECOND_ADDITIONAL_RATE_EMPLOYEE_2025,
    arrondir_cent,
)


ZERO = Decimal("0")
SEUIL_REVENUS_RQAP_REMBOURSEMENT_COMPLET_2025 = Decimal("2000")


@dataclass(frozen=True)
class CotisationsExcedentaires2025:
    """Entrées validées servant au calcul des paiements en trop."""

    rrq_ba: Decimal = ZERO
    rrq_bb: Decimal = ZERO
    gains_admissibles_rrq: Decimal = ZERO

    assurance_emploi: Decimal = ZERO
    gains_assurables_ae: Decimal = ZERO

    rqap: Decimal = ZERO
    revenus_assujettis_rqap: Decimal = ZERO

    source: str = ""
    valide_par_comptable: bool = False

    resident_quebec_31_decembre_2025: bool = False
    emploi_quebec_uniquement: bool = False
    rrq_uniquement_sans_rpc: bool = False
    aucun_travail_autonome: bool = False
    profil_rrq_standard_18_64: bool = False
    aucun_cas_particulier_ae: bool = False
    aucun_cas_particulier_rqap: bool = False
    calcul_standard_confirme: bool = False


@dataclass(frozen=True)
class RemboursementsCotisations2025:
    """Résultat des cotisations salariales payées en trop."""

    rrq_ligne_452: Decimal = ZERO
    assurance_emploi_ligne_45000: Decimal = ZERO
    rqap_ligne_457: Decimal = ZERO

    @property
    def total(self) -> Decimal:
        return arrondir_cent(
            self.rrq_ligne_452
            + self.assurance_emploi_ligne_45000
            + self.rqap_ligne_457
        )


def aucune_cotisation_excedentaire_2025() -> CotisationsExcedentaires2025:
    """Retourne un profil vide qui ne modifie pas le calcul fiscal."""
    return CotisationsExcedentaires2025()


def _profil_vide(donnees: CotisationsExcedentaires2025) -> bool:
    return donnees == CotisationsExcedentaires2025()


def valider_cotisations_excedentaires_2025(
    donnees: CotisationsExcedentaires2025,
) -> CotisationsExcedentaires2025:
    """Valide le profil simple avant tout calcul de remboursement."""
    for nom, montant in (
        ("RRQ B.A", donnees.rrq_ba),
        ("RRQ B.B", donnees.rrq_bb),
        ("gains admissibles RRQ", donnees.gains_admissibles_rrq),
        ("assurance-emploi", donnees.assurance_emploi),
        ("gains assurables AE", donnees.gains_assurables_ae),
        ("RQAP", donnees.rqap),
        ("revenus assujettis au RQAP", donnees.revenus_assujettis_rqap),
    ):
        if montant < ZERO:
            raise ValueError(f"{nom} ne peut pas être négatif.")

    if _profil_vide(donnees):
        return donnees

    if not donnees.valide_par_comptable:
        raise ValueError(
            "Les cotisations excédentaires doivent être validées "
            "par le comptable."
        )

    if not donnees.resident_quebec_31_decembre_2025:
        raise ValueError(
            "Cette version exige une résidence au Québec "
            "au 31 décembre 2025."
        )

    if not donnees.emploi_quebec_uniquement:
        raise ValueError(
            "Cette version accepte uniquement des emplois exercés "
            "au Québec en 2025."
        )

    if not donnees.rrq_uniquement_sans_rpc:
        raise ValueError(
            "Cette version accepte uniquement des cotisations au RRQ, "
            "sans cotisation au RPC."
        )

    if not donnees.aucun_travail_autonome:
        raise ValueError(
            "Le travail autonome n'est pas pris en charge dans ce calcul."
        )

    if not donnees.profil_rrq_standard_18_64:
        raise ValueError(
            "Cette version exige un profil RRQ standard de 18 à 64 ans "
            "pendant toute l'année, sans proratisation."
        )

    if not donnees.aucun_cas_particulier_ae:
        raise ValueError(
            "Les cas particuliers d'assurance-emploi doivent être "
            "traités avec les formulaires officiels."
        )

    if not donnees.aucun_cas_particulier_rqap:
        raise ValueError(
            "Les cas particuliers du RQAP doivent être traités "
            "avec les formulaires officiels."
        )

    if not donnees.calcul_standard_confirme:
        raise ValueError(
            "Le calcul standard RRQ / AE / RQAP doit être confirmé "
            "par le comptable."
        )

    if not donnees.source.strip():
        raise ValueError(
            "La source justificative des cotisations est obligatoire."
        )

    return donnees


def cotisation_rrq_attendue_2025(
    gains_admissibles: Decimal,
) -> Decimal:
    """Calcule B.A + B.B attendues pour un profil RRQ standard 2025."""
    if gains_admissibles < ZERO:
        raise ValueError(
            "Les gains admissibles RRQ ne peuvent pas être négatifs."
        )

    plafond_ba = min(
        gains_admissibles,
        QPP_MAX_PENSIONABLE_EARNINGS_2025,
    )
    gains_ba = max(
        plafond_ba - QPP_BASIC_EXEMPTION_2025,
        ZERO,
    )
    ba = arrondir_cent(
        gains_ba * QPP_BA_TOTAL_RATE_EMPLOYEE_2025
    )

    gains_bb = max(
        min(
            gains_admissibles,
            QPP_ADDITIONAL_MAX_PENSIONABLE_EARNINGS_2025,
        )
        - QPP_MAX_PENSIONABLE_EARNINGS_2025,
        ZERO,
    )
    bb = arrondir_cent(
        gains_bb * QPP_SECOND_ADDITIONAL_RATE_EMPLOYEE_2025
    )

    return arrondir_cent(ba + bb)


def cotisation_ae_attendue_2025(
    gains_assurables: Decimal,
) -> Decimal:
    """Calcule la prime AE Québec attendue pour 2025."""
    if gains_assurables < ZERO:
        raise ValueError(
            "Les gains assurables AE ne peuvent pas être négatifs."
        )

    return arrondir_cent(
        min(
            gains_assurables,
            EI_MAX_INSURABLE_EARNINGS_QUEBEC_2025,
        )
        * EI_RATE_QUEBEC_2025
    )


def cotisation_rqap_attendue_2025(
    revenus_assujettis: Decimal,
) -> Decimal:
    """Calcule la cotisation RQAP attendue pour 2025."""
    if revenus_assujettis < ZERO:
        raise ValueError(
            "Les revenus assujettis au RQAP ne peuvent pas être négatifs."
        )

    return arrondir_cent(
        min(
            revenus_assujettis,
            QPIP_MAX_INSURABLE_EARNINGS_2025,
        )
        * QPIP_RATE_EMPLOYEE_2025
    )


def remboursement_rrq_2025(
    donnees: CotisationsExcedentaires2025,
) -> Decimal:
    """Retourne le paiement RRQ en trop à la ligne Québec 452."""
    valider_cotisations_excedentaires_2025(donnees)

    if _profil_vide(donnees):
        return ZERO

    paye = arrondir_cent(donnees.rrq_ba + donnees.rrq_bb)
    attendu = cotisation_rrq_attendue_2025(
        donnees.gains_admissibles_rrq
    )
    return arrondir_cent(max(paye - attendu, ZERO))


def remboursement_assurance_emploi_2025(
    donnees: CotisationsExcedentaires2025,
) -> Decimal:
    """Retourne le paiement AE en trop à la ligne fédérale 45000."""
    valider_cotisations_excedentaires_2025(donnees)

    if _profil_vide(donnees):
        return ZERO

    attendu = cotisation_ae_attendue_2025(
        donnees.gains_assurables_ae
    )
    return arrondir_cent(
        max(donnees.assurance_emploi - attendu, ZERO)
    )


def remboursement_rqap_2025(
    donnees: CotisationsExcedentaires2025,
) -> Decimal:
    """Retourne le paiement RQAP en trop à la ligne Québec 457."""
    valider_cotisations_excedentaires_2025(donnees)

    if _profil_vide(donnees):
        return ZERO

    if (
        donnees.revenus_assujettis_rqap
        < SEUIL_REVENUS_RQAP_REMBOURSEMENT_COMPLET_2025
    ):
        return arrondir_cent(donnees.rqap)

    attendu = cotisation_rqap_attendue_2025(
        donnees.revenus_assujettis_rqap
    )
    return arrondir_cent(max(donnees.rqap - attendu, ZERO))


def calculer_remboursements_cotisations_2025(
    donnees: CotisationsExcedentaires2025,
) -> RemboursementsCotisations2025:
    """Calcule les remboursements simples supportés."""
    valider_cotisations_excedentaires_2025(donnees)

    if _profil_vide(donnees):
        return RemboursementsCotisations2025()

    return RemboursementsCotisations2025(
        rrq_ligne_452=remboursement_rrq_2025(donnees),
        assurance_emploi_ligne_45000=(
            remboursement_assurance_emploi_2025(donnees)
        ),
        rqap_ligne_457=remboursement_rqap_2025(donnees),
    )
