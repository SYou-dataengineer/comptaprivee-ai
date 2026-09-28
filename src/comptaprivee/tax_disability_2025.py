"""Crédits pour handicap / déficience grave et prolongée - 2025.

Profil volontairement limité de ComptaPrivée :
- personne elle-même;
- résidente du Québec et du Canada toute l'année;
- profil historique adulte; naissance et soins détaillés pour le fédéral 5R;
- supplément fédéral des moins de 18 ans au 31 décembre 2025;
- Québec inchangé, encore limité aux adultes au 1er janvier;
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
from datetime import date
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
SUPPLEMENT_HANDICAP_MINEUR_2025 = Decimal("5914")
SEUIL_SOINS_HANDICAP_MINEUR_2025 = Decimal("3464")


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
    # Champs 5R facultatifs : les anciens JSON conservent le profil adulte.
    naissance_federale: str = ""
    soins_reclames_federaux: Decimal = ZERO
    source_soins_federaux: str = ""
    soins_federaux_valides: bool = False


def supplement_handicap_mineur_2025(naissance: str, soins: Decimal) -> Decimal:
    """Feuille fédérale 2025, 31600 : dépenses réclamées par quiconque."""
    if not isinstance(naissance, str):
        raise ValueError("Date de naissance fédérale invalide.")
    try:
        jour = date.fromisoformat(naissance)
        if jour.isoformat() != naissance or jour > date(2025, 12, 31):
            raise ValueError()
    except ValueError as erreur:
        raise ValueError("Naissance au plus tard en 2025, format AAAA-MM-JJ requis.") from erreur
    if not isinstance(soins, Decimal) or not soins.is_finite() or soins < ZERO:
        raise ValueError("Les frais de garde/soins doivent être un Decimal fini non négatif.")
    try:
        if soins != arrondir_cent(soins):
            raise ValueError("Les frais de garde/soins exigent au plus deux décimales.")
    except ArithmeticError as erreur:
        raise ValueError("Frais de garde/soins hors capacité.") from erreur
    if jour.year <= 2007:
        return ZERO
    return max(SUPPLEMENT_HANDICAP_MINEUR_2025 - max(soins - SEUIL_SOINS_HANDICAP_MINEUR_2025, ZERO), ZERO)


def montant_federal_handicap_2025(credit: CreditDeficience2025) -> Decimal:
    valider_credit_deficience_2025(credit)
    if not credit.reclamer_federal:
        return ZERO
    supplement = (supplement_handicap_mineur_2025(credit.naissance_federale, credit.soins_reclames_federaux)
                  if credit.naissance_federale else ZERO)
    return MONTANT_FEDERAL_HANDICAP_2025 + supplement


def lignes_handicap_detaille_2025(credit: CreditDeficience2025) -> list[str]:
    if not credit.naissance_federale:
        return []
    montant = montant_federal_handicap_2025(credit)
    return ["", "HANDICAP FÉDÉRAL — DÉTAIL DU SUPPLÉMENT 2025",
        f"Naissance : {credit.naissance_federale}; âge et soins validés par le comptable.",
        f"Garde/soins payés en 2025, réclamés par quiconque : {credit.soins_reclames_federaux:.2f} $",
        "Source et rapprochement des soins : " + credit.source_soins_federaux,
        f"Supplément si moins de 18 ans au 31 décembre : {montant - MONTANT_FEDERAL_HANDICAP_2025:.2f} $",
        "Formule mineur : max(5914 - max(soins - 3464, 0), 0); adulte : 0.",
        f"Montant 31600 : 10138 + supplément = {montant:.2f} $; crédit à 14,5 %."]


def aucun_credit_deficience_2025() -> CreditDeficience2025:
    """Retourne un profil vide, sans crédit réclamé."""
    return CreditDeficience2025()


def valider_credit_deficience_2025(
    credit: CreditDeficience2025,
) -> CreditDeficience2025:
    """Valide le profil simple avant tout calcul."""
    if not isinstance(credit, CreditDeficience2025):
        raise ValueError("Profil handicap/déficience invalide.")
    if not isinstance(credit.naissance_federale, str) or not isinstance(credit.source_soins_federaux, str):
        raise ValueError("Naissance et source de soins fédérales doivent être du texte.")
    if type(credit.soins_federaux_valides) is not bool:
        raise ValueError("Validation des soins fédéraux non booléenne.")
    # Valider les montants même dans un profil inactif.
    supplement_handicap_mineur_2025(credit.naissance_federale or "2000-01-01", credit.soins_reclames_federaux)
    if credit.naissance_federale:
        if not credit.reclamer_federal:
            raise ValueError("La naissance fédérale détaillée exige une demande fédérale.")
        if not credit.soins_federaux_valides or not credit.source_soins_federaux.strip():
            raise ValueError("Frais de garde/soins, y compris zéro, et leur source doivent être validés.")
        majeur_janvier = date.fromisoformat(credit.naissance_federale) <= date(2007, 1, 1)
        if credit.age_18_plus_au_1_janvier_2025 != majeur_janvier:
            raise ValueError("La confirmation d'âge au 1er janvier contredit la date de naissance.")
    elif credit.soins_reclames_federaux or credit.source_soins_federaux or credit.soins_federaux_valides:
        raise ValueError("Une date de naissance est requise pour les données de soins fédérales.")
    if not credit.reclamer_federal and not credit.reclamer_quebec:
        return credit

    if not credit.valide_par_comptable:
        raise ValueError(
            "Le crédit pour handicap ou déficience doit être "
            "validé par le comptable."
        )

    if not credit.age_18_plus_au_1_janvier_2025 and (credit.reclamer_quebec or not credit.naissance_federale):
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
        montant_federal_handicap_2025(credit)
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
