"""Crédits pour handicap / déficience grave et prolongée - 2025.

Profil volontairement limité de ComptaPrivée :
- personne elle-même;
- résidente du Québec et du Canada toute l'année;
- 18 ans ou plus au 1er janvier 2025;
- aucun transfert du montant fédéral à une personne de soutien;
- aucune situation de soins en établissement ou de préposé nécessitant
  l'application de règles spéciales;
- admissibilité et pièces déjà vérifiées par le comptable.

Références visées :
- fédéral : ligne 31600, montant pour personnes handicapées;
- Québec : ligne 376, montant pour déficience grave et prolongée.

Les montants 2025 utilisés dans ce profil sont :
- 10 138 $ au fédéral;
- 4 123 $ au Québec.
"""

from dataclasses import dataclass, replace
from decimal import Decimal

from .tax_federal_2025 import (
    FEDERAL_CREDIT_RATE_2025,
    ImpotFederalPreliminaire2025,
)
from .tax_quebec_2025 import (
    QUEBEC_BASIC_CREDIT_RATE_2025,
    ImpotQuebecPreliminaire2025,
)
from .tax_rules_2025 import arrondir_cent


ZERO = Decimal("0")
MONTANT_FEDERAL_HANDICAP_2025 = Decimal("10138")
MONTANT_QUEBEC_DEFICIENCE_2025 = Decimal("4123")


@dataclass(frozen=True)
class CreditDeficience2025:
    """Choix et validations pour les crédits liés à une déficience."""

    reclamer_federal: bool = False
    reclamer_quebec: bool = False

    source_federale: str = ""
    source_quebec: str = ""

    valide_par_comptable: bool = False
    age_18_plus_au_1_janvier_2025: bool = False
    deficience_12_mois_confirmee: bool = False
    profil_soi_meme_resident_quebec: bool = False

    ciph_approuve_arc: bool = False
    attestation_quebec_confirmee: bool = False

    aucun_conflit_soins_prepose_etablissement: bool = False
    aucun_transfert_federal: bool = False


def aucun_credit_deficience_2025() -> CreditDeficience2025:
    """Retourne un profil vide, sans crédit réclamé."""
    return CreditDeficience2025()


def valider_credit_deficience_2025(
    credit: CreditDeficience2025,
) -> CreditDeficience2025:
    """Valide le profil simple avant tout calcul."""
    if not credit.reclamer_federal and not credit.reclamer_quebec:
        return credit

    if not credit.valide_par_comptable:
        raise ValueError(
            "Le crédit pour handicap ou déficience doit être "
            "validé par le comptable."
        )

    if not credit.age_18_plus_au_1_janvier_2025:
        raise ValueError(
            "Cette version accepte uniquement une personne qui avait "
            "18 ans ou plus au 1er janvier 2025."
        )

    if not credit.deficience_12_mois_confirmee:
        raise ValueError(
            "La durée d'au moins 12 mois consécutifs doit être confirmée."
        )

    if not credit.profil_soi_meme_resident_quebec:
        raise ValueError(
            "Cette version accepte uniquement le crédit pour soi-même "
            "dans un profil résident Québec/Canada."
        )

    if not credit.aucun_conflit_soins_prepose_etablissement:
        raise ValueError(
            "Les règles particulières relatives aux soins d'un préposé "
            "ou aux soins en établissement doivent être exclues ou "
            "validées avant le calcul."
        )

    if credit.reclamer_federal:
        if not credit.ciph_approuve_arc:
            raise ValueError(
                "L'admissibilité au CIPH doit être approuvée par l'ARC."
            )

        if not credit.source_federale.strip():
            raise ValueError(
                "La source fédérale du CIPH est obligatoire."
            )

        if not credit.aucun_transfert_federal:
            raise ValueError(
                "Cette version ne traite pas le transfert du montant "
                "fédéral pour personnes handicapées."
            )

    if credit.reclamer_quebec:
        if not credit.attestation_quebec_confirmee:
            raise ValueError(
                "L'attestation professionnelle requise au Québec "
                "doit être confirmée."
            )

        if not credit.source_quebec.strip():
            raise ValueError(
                "La source Québec de l'attestation est obligatoire."
            )

    return credit


def credit_federal_handicap_2025(
    credit: CreditDeficience2025,
) -> Decimal:
    """Calcule le crédit fédéral non remboursable de la ligne 31600."""
    valider_credit_deficience_2025(credit)

    if not credit.reclamer_federal:
        return ZERO

    return arrondir_cent(
        MONTANT_FEDERAL_HANDICAP_2025
        * FEDERAL_CREDIT_RATE_2025
    )


def credit_quebec_deficience_2025(
    credit: CreditDeficience2025,
) -> Decimal:
    """Calcule le crédit Québec associé au montant de la ligne 376."""
    valider_credit_deficience_2025(credit)

    if not credit.reclamer_quebec:
        return ZERO

    return arrondir_cent(
        MONTANT_QUEBEC_DEFICIENCE_2025
        * QUEBEC_BASIC_CREDIT_RATE_2025
    )


def appliquer_credit_federal_handicap_2025(
    impot: ImpotFederalPreliminaire2025,
    credit: CreditDeficience2025,
) -> ImpotFederalPreliminaire2025:
    """Applique le crédit fédéral, sans rendre l'impôt négatif."""
    montant = credit_federal_handicap_2025(credit)

    if montant == ZERO:
        return impot

    remplacements = {
        (
            "Aucun crédit pour handicap, frais médicaux ou scolarité."
        ): "Aucun crédit pour frais médicaux ou scolarité.",
        (
            "Aucun crédit pour handicap ou frais médicaux."
        ): "Aucun crédit pour frais médicaux.",
        (
            "Aucun crédit pour handicap ou scolarité."
        ): "Aucun crédit pour scolarité.",
    }

    limitations = []
    for texte in impot.limitations:
        if texte == "Aucun crédit pour handicap.":
            continue
        limitations.append(remplacements.get(texte, texte))

    limitations.append(
        "Crédit fédéral pour personnes handicapées inclus."
    )

    return replace(
        impot,
        impot_federal_de_base=max(
            arrondir_cent(
                impot.impot_federal_de_base - montant
            ),
            ZERO,
        ),
        limitations=tuple(limitations),
    )


def appliquer_credit_quebec_deficience_2025(
    impot: ImpotQuebecPreliminaire2025,
    credit: CreditDeficience2025,
) -> ImpotQuebecPreliminaire2025:
    """Applique le crédit Québec, sans rendre l'impôt négatif."""
    montant = credit_quebec_deficience_2025(credit)

    if montant == ZERO:
        return impot

    remplacements = {
        (
            "Aucun crédit handicap, médical, scolarité ou don."
        ): "Aucun crédit médical, scolarité ou don.",
        (
            "Aucun crédit handicap, médical ou scolarité."
        ): "Aucun crédit médical ou scolarité.",
        (
            "Aucun crédit handicap, médical ou don."
        ): "Aucun crédit médical ou don.",
        (
            "Aucun crédit handicap, scolarité ou don."
        ): "Aucun crédit scolarité ou don.",
        "Aucun crédit handicap ou médical.": "Aucun crédit médical.",
        "Aucun crédit handicap ou scolarité.": "Aucun crédit scolarité.",
        "Aucun crédit handicap ou don.": "Aucun crédit don.",
    }

    limitations = []
    for texte in impot.limitations:
        if texte == "Aucun crédit handicap.":
            continue
        limitations.append(remplacements.get(texte, texte))

    limitations.append(
        "Crédit Québec pour déficience grave et prolongée inclus."
    )

    return replace(
        impot,
        impot_quebec_preliminaire=max(
            arrondir_cent(
                impot.impot_quebec_preliminaire - montant
            ),
            ZERO,
        ),
        limitations=tuple(limitations),
    )
