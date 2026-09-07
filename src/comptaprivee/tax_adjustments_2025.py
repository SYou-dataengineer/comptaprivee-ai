"""Déduction REER/RPAC/RVER validée - année fiscale 2025.

Cette première brique prépare l'intégration d'une déduction REER dans le
moteur fiscal sans modifier encore le calcul principal.

Règles de sécurité de cette version :
- le montant est fourni et validé par le comptable;
- le plafond individuel doit être confirmé à partir d'une source ARC;
- la déduction ne peut pas dépasser ce plafond;
- les transferts REER et remboursements RAP/REEP sont hors profil.
"""

from dataclasses import dataclass
from decimal import Decimal

ZERO = Decimal("0")


@dataclass(frozen=True)
class AjustementReer2025:
    deduction_reer: Decimal = ZERO
    plafond_reer_confirme: Decimal = ZERO
    source_plafond_reer: str = ""
    valide_par_comptable: bool = False
    inclut_transfert_reer: bool = False
    inclut_remboursement_rap_reep: bool = False


def valider_ajustement_reer_2025(
    ajustement: AjustementReer2025,
) -> AjustementReer2025:
    if ajustement.deduction_reer < ZERO:
        raise ValueError(
            "La déduction REER ne peut pas être négative."
        )

    if ajustement.plafond_reer_confirme < ZERO:
        raise ValueError(
            "Le plafond REER confirmé ne peut pas être négatif."
        )

    if ajustement.deduction_reer == ZERO:
        return ajustement

    if not ajustement.valide_par_comptable:
        raise ValueError(
            "La déduction REER doit être validée par le comptable."
        )

    if not ajustement.source_plafond_reer.strip():
        raise ValueError(
            "La source du plafond REER confirmé est obligatoire."
        )

    if ajustement.plafond_reer_confirme == ZERO:
        raise ValueError(
            "Le plafond individuel REER doit être confirmé."
        )

    if ajustement.deduction_reer > ajustement.plafond_reer_confirme:
        raise ValueError(
            "La déduction REER dépasse le plafond individuel confirmé."
        )

    if ajustement.inclut_transfert_reer:
        raise ValueError(
            "Les transferts REER exigent un traitement avancé."
        )

    if ajustement.inclut_remboursement_rap_reep:
        raise ValueError(
            "Les remboursements RAP/REEP désignés ne sont pas "
            "une déduction REER ordinaire."
        )

    return ajustement


def deduction_reer_federale_2025(
    ajustement: AjustementReer2025,
) -> Decimal:
    valider_ajustement_reer_2025(ajustement)
    return ajustement.deduction_reer


def deduction_reer_quebec_2025(
    ajustement: AjustementReer2025,
) -> Decimal:
    """Retourne la déduction Québec pour le profil REER ordinaire.

    Les transferts sont volontairement refusés par la validation, car
    Revenu Québec peut demander un traitement différent à la ligne 250.
    """
    valider_ajustement_reer_2025(ajustement)
    return ajustement.deduction_reer

from .tax_income_2025 import RevenuNetImposable2025
from .tax_rules_2025 import arrondir_cent


def appliquer_ajustement_reer_2025(
    revenu: RevenuNetImposable2025,
    ajustement: AjustementReer2025,
) -> RevenuNetImposable2025:
    """Applique une déduction REER validée au revenu fédéral et Québec."""
    from dataclasses import replace

    if revenu.annee_fiscale != 2025:
        raise ValueError(
            "L'ajustement REER actuel accepte uniquement l'année 2025."
        )

    valider_ajustement_reer_2025(ajustement)
    deduction = arrondir_cent(ajustement.deduction_reer)

    if deduction == ZERO:
        return revenu

    limitations = tuple(
        texte
        for texte in revenu.limitations
        if texte != "Aucune autre déduction de revenu net ou imposable."
    ) + (
        "Déduction REER/RPAC/RVER ordinaire validée incluse.",
        "Transferts REER et remboursements RAP/REEP hors profil.",
    )

    return replace(
        revenu,
        revenu_net_federal=max(
            arrondir_cent(revenu.revenu_net_federal - deduction),
            ZERO,
        ),
        revenu_imposable_federal=max(
            arrondir_cent(
                revenu.revenu_imposable_federal - deduction
            ),
            ZERO,
        ),
        revenu_net_quebec=max(
            arrondir_cent(revenu.revenu_net_quebec - deduction),
            ZERO,
        ),
        revenu_imposable_quebec=max(
            arrondir_cent(
                revenu.revenu_imposable_quebec - deduction
            ),
            ZERO,
        ),
        profil=revenu.profil + " + REER validé",
        limitations=limitations,
    )

def normaliser_montant_reer_2025(
    valeur: str | Decimal | int | float | None,
) -> Decimal:
    """Convertit une saisie comptable locale en Decimal à deux décimales."""
    if valeur is None:
        return ZERO

    if isinstance(valeur, Decimal):
        montant = valeur
    else:
        texte = str(valeur).strip()
        if not texte:
            return ZERO

        texte = (
            texte.replace("\u00a0", "")
            .replace("\u202f", "")
            .replace(" ", "")
            .replace("$", "")
            .replace("CAD", "")
            .replace("cad", "")
            .replace(",", ".")
        )

        try:
            montant = Decimal(texte)
        except Exception as erreur:
            raise ValueError(
                "Montant REER invalide. Exemple accepté : 5 000,00"
            ) from erreur

    if not montant.is_finite():
        raise ValueError("Le montant REER doit être un nombre fini.")

    return arrondir_cent(montant)


def creer_ajustement_reer_depuis_champs_2025(
    deduction_reer,
    plafond_reer_confirme,
    source_plafond_reer: str,
    valide_par_comptable: bool,
) -> AjustementReer2025:
    """Crée et valide l'ajustement à partir des champs de l'interface."""
    ajustement = AjustementReer2025(
        deduction_reer=normaliser_montant_reer_2025(deduction_reer),
        plafond_reer_confirme=normaliser_montant_reer_2025(
            plafond_reer_confirme
        ),
        source_plafond_reer=str(source_plafond_reer).strip(),
        valide_par_comptable=bool(valide_par_comptable),
    )
    return valider_ajustement_reer_2025(ajustement)
