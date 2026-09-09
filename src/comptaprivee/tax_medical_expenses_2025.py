"""Frais médicaux 2025 - profil emploi Québec simple.

Portée volontairement limitée : particulier sans conjoint ni personne à
charge, frais admissibles déjà vérifiés, remboursements soustraits, reçus
confirmés et période de 12 mois se terminant en 2025. Aucun crédit
remboursable ni règle spéciale n'est traité ici.
"""

from dataclasses import dataclass, replace
from decimal import Decimal

from .tax_federal_2025 import ImpotFederalPreliminaire2025
from .tax_quebec_2025 import ImpotQuebecPreliminaire2025
from .tax_rules_2025 import arrondir_cent

ZERO = Decimal("0")
TROIS_POUR_CENT = Decimal("0.03")
SEUIL_MAX_FEDERAL_FRAIS_MEDICAUX_2025 = Decimal("2834")
TAUX_CREDIT_FEDERAL_2025 = Decimal("0.145")
TAUX_CREDIT_QUEBEC_FRAIS_MEDICAUX_2025 = Decimal("0.20")


@dataclass(frozen=True)
class FraisMedicaux2025:
    montant_admissible_federal: Decimal = ZERO
    montant_admissible_quebec: Decimal = ZERO
    source_federale: str = ""
    source_quebec: str = ""
    valide_par_comptable: bool = False
    recus_confirmes: bool = False
    remboursements_soustraits: bool = False
    periode_12_mois_fin_2025_confirmee: bool = False
    aucune_periode_deja_reclamee: bool = False
    profil_individuel_sans_conjoint_dependant: bool = False


def aucun_frais_medical_2025() -> FraisMedicaux2025:
    return FraisMedicaux2025()


def valider_frais_medicaux_2025(frais: FraisMedicaux2025) -> FraisMedicaux2025:
    fed = frais.montant_admissible_federal
    qc = frais.montant_admissible_quebec

    if fed < ZERO:
        raise ValueError(
            "Le montant admissible fédéral des frais médicaux "
            "ne peut pas être négatif."
        )

    if qc < ZERO:
        raise ValueError(
            "Le montant admissible Québec des frais médicaux "
            "ne peut pas être négatif."
        )

    if fed == ZERO and qc == ZERO:
        return frais

    if not frais.valide_par_comptable:
        raise ValueError(
            "Les frais médicaux doivent être validés par le comptable."
        )

    if not frais.recus_confirmes:
        raise ValueError(
            "Les reçus et pièces justificatives doivent être confirmés."
        )

    if not frais.remboursements_soustraits:
        raise ValueError(
            "Les remboursements reçus ou à recevoir doivent être "
            "soustraits avant le calcul."
        )

    if not frais.periode_12_mois_fin_2025_confirmee:
        raise ValueError(
            "La période de 12 mois consécutifs se terminant en 2025 "
            "doit être confirmée."
        )

    if not frais.aucune_periode_deja_reclamee:
        raise ValueError(
            "Cette version exige qu'aucune partie de la période n'ait "
            "déjà servi à une demande antérieure."
        )

    if not frais.profil_individuel_sans_conjoint_dependant:
        raise ValueError(
            "Cette première version accepte uniquement le profil "
            "individuel sans conjoint ni personne à charge."
        )

    if fed > ZERO and not frais.source_federale.strip():
        raise ValueError(
            "La source fédérale des frais médicaux est obligatoire."
        )

    if qc > ZERO and not frais.source_quebec.strip():
        raise ValueError(
            "La source Québec des frais médicaux est obligatoire."
        )

    return frais


def montant_frais_medicaux_federal_apres_seuil_2025(
    frais: FraisMedicaux2025,
    revenu_net_federal: Decimal,
) -> Decimal:
    valider_frais_medicaux_2025(frais)

    if revenu_net_federal < ZERO:
        raise ValueError(
            "Le revenu net fédéral ne peut pas être négatif."
        )

    seuil = min(
        arrondir_cent(revenu_net_federal * TROIS_POUR_CENT),
        SEUIL_MAX_FEDERAL_FRAIS_MEDICAUX_2025,
    )

    return max(
        arrondir_cent(frais.montant_admissible_federal - seuil),
        ZERO,
    )


def credit_federal_frais_medicaux_2025(
    frais: FraisMedicaux2025,
    revenu_net_federal: Decimal,
) -> Decimal:
    montant = montant_frais_medicaux_federal_apres_seuil_2025(
        frais,
        revenu_net_federal,
    )
    return arrondir_cent(
        montant * TAUX_CREDIT_FEDERAL_2025
    )


def montant_frais_medicaux_quebec_apres_seuil_2025(
    frais: FraisMedicaux2025,
    revenu_familial_quebec: Decimal,
) -> Decimal:
    valider_frais_medicaux_2025(frais)

    if revenu_familial_quebec < ZERO:
        raise ValueError(
            "Le revenu familial Québec ne peut pas être négatif."
        )

    seuil = arrondir_cent(
        revenu_familial_quebec * TROIS_POUR_CENT
    )

    return max(
        arrondir_cent(frais.montant_admissible_quebec - seuil),
        ZERO,
    )


def credit_quebec_frais_medicaux_2025(
    frais: FraisMedicaux2025,
    revenu_familial_quebec: Decimal,
) -> Decimal:
    montant = montant_frais_medicaux_quebec_apres_seuil_2025(
        frais,
        revenu_familial_quebec,
    )
    return arrondir_cent(
        montant * TAUX_CREDIT_QUEBEC_FRAIS_MEDICAUX_2025
    )


def appliquer_credit_federal_frais_medicaux_2025(
    impot: ImpotFederalPreliminaire2025,
    frais: FraisMedicaux2025,
    revenu_net_federal: Decimal,
) -> ImpotFederalPreliminaire2025:
    """Applique le crédit fédéral non remboursable pour frais médicaux."""
    credit = credit_federal_frais_medicaux_2025(
        frais,
        revenu_net_federal,
    )

    if credit == ZERO:
        return impot

    limitations = tuple(
        (
            "Aucun crédit pour handicap ou scolarité."
            if texte
            == "Aucun crédit pour handicap, frais médicaux ou scolarité."
            else texte
        )
        for texte in impot.limitations
    )

    limitations += (
        "Crédit fédéral pour frais médicaux admissibles inclus.",
    )

    return replace(
        impot,
        impot_federal_de_base=max(
            arrondir_cent(
                impot.impot_federal_de_base - credit
            ),
            ZERO,
        ),
        limitations=limitations,
    )


def appliquer_credit_quebec_frais_medicaux_2025(
    impot: ImpotQuebecPreliminaire2025,
    frais: FraisMedicaux2025,
    revenu_familial_quebec: Decimal,
) -> ImpotQuebecPreliminaire2025:
    """Applique le crédit Québec non remboursable pour frais médicaux."""
    credit = credit_quebec_frais_medicaux_2025(
        frais,
        revenu_familial_quebec,
    )

    if credit == ZERO:
        return impot

    nouvelles_limitations = []

    for texte in impot.limitations:
        if texte == "Aucun crédit handicap, médical, scolarité ou don.":
            nouvelles_limitations.append(
                "Aucun crédit handicap, scolarité ou don."
            )
        elif texte == "Aucun crédit handicap, médical ou scolarité.":
            nouvelles_limitations.append(
                "Aucun crédit handicap ou scolarité."
            )
        else:
            nouvelles_limitations.append(texte)

    nouvelles_limitations.append(
        "Crédit Québec pour frais médicaux admissibles inclus."
    )

    return replace(
        impot,
        impot_quebec_preliminaire=max(
            arrondir_cent(
                impot.impot_quebec_preliminaire - credit
            ),
            ZERO,
        ),
        limitations=tuple(nouvelles_limitations),
    )
