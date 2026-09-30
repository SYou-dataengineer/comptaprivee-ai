"""Préparation annexe D 2025 : faits et audit, sans montant de solidarité.

Sources : Revenu Québec, TP-1.D.D (2025-12), pages 1 et 2 et TP-1.G
(2025-12), pages 12-13. Période juillet 2026 à juin 2027, distincte du TP-1.
"""

from dataclasses import dataclass, fields
from datetime import date
from decimal import Decimal
from textwrap import wrap

from .tax_rules_2025 import arrondir_cent


CONFIRMATIONS_6H = {
    "residence_annuelle_confirmee": "Résidence au Québec et au Canada toute l'année 2025",
    "citoyennete_confirmee": "Citoyenneté canadienne au 31 décembre 2025 vérifiée",
    "sans_conjoint_confirme": "Aucun conjoint au sens de l'annexe D pendant toute l'année 2025",
    "sans_enfant_confirme": "Aucun enfant à charge en 2025",
    "logement_non_admissible_confirme": "Lieu principal de résidence au 31 décembre 2025 non admissible à la composante logement, après examen de l'annexe D",
    "hors_village_nordique_confirme": "Lieu principal de résidence hors d'un village nordique au 31 décembre 2025",
    "vie_seule_verifiee": "Réponse sur la vie seule dans une habitation vérifiée pour toute l'année 2025",
    "absence_detention_confirmee": "Aucune détention en 2025 dans ce premier périmètre logiciel",
    "absence_allocation_pour_soi_confirmee": "Aucune Allocation famille versée pour le demandeur lui-même en décembre 2025",
    "absence_cas_particuliers_confirmee": "Aucun décès, faillite ou changement de résidence à traiter dans ce profil",
    "valide_par_comptable": "Faits, sources et limites du profil vérifiés par le comptable",
}


@dataclass(frozen=True)
class SolidariteQuebec2025:
    activer: bool = False
    naissance: str = ""
    source: str = ""
    vit_seul_toute_annee: bool = False
    residence_annuelle_confirmee: bool = False
    citoyennete_confirmee: bool = False
    sans_conjoint_confirme: bool = False
    sans_enfant_confirme: bool = False
    logement_non_admissible_confirme: bool = False
    hors_village_nordique_confirme: bool = False
    vie_seule_verifiee: bool = False
    absence_detention_confirmee: bool = False
    absence_allocation_pour_soi_confirmee: bool = False
    absence_cas_particuliers_confirmee: bool = False
    valide_par_comptable: bool = False


def valider_solidarite_quebec_2025(profil: SolidariteQuebec2025) -> SolidariteQuebec2025:
    """Valider le sous-profil logiciel, sans conclure au droit à un montant."""
    if not isinstance(profil, SolidariteQuebec2025):
        raise ValueError("Profil solidarité Québec invalide.")
    for champ in fields(profil):
        valeur = getattr(profil, champ.name)
        if type(valeur) is not type(champ.default):
            raise ValueError("Type solidarité Québec invalide : " + champ.name)
        if isinstance(valeur, str) and (len(valeur) > 2000 or any(ord(c) < 32 for c in valeur)):
            raise ValueError("Texte solidarité Québec invalide : " + champ.name)
    if not profil.activer:
        if profil != SolidariteQuebec2025():
            raise ValueError("Activez le profil solidarité ou effacez ses données et confirmations.")
        return profil
    try:
        naissance = date.fromisoformat(profil.naissance)
        if naissance.isoformat() != profil.naissance:
            raise ValueError()
    except ValueError as erreur:
        raise ValueError("Naissance solidarité : date AAAA-MM-JJ requise.") from erreur
    if naissance > date(2007, 12, 31):
        raise ValueError("Profil solidarité limité aux personnes de 18 ans ou plus fin 2025.")
    if not profil.source.strip():
        raise ValueError("Source solidarité obligatoire.")
    for nom, libelle in CONFIRMATIONS_6H.items():
        if not getattr(profil, nom):
            raise ValueError("Confirmation obligatoire : " + libelle)
    return profil


@dataclass(frozen=True)
class BaseSolidariteQuebec2025:
    """Faits préparés seulement : aucun montant de crédit ni droit garanti."""

    revenu_familial: Decimal
    additionnel_vie_seule_a_etudier: bool
    annee_reference: int = 2025
    debut_periode: date = date(2026, 7, 1)
    fin_periode: date = date(2027, 6, 30)


def preparer_solidarite_quebec_2025(
    profil: SolidariteQuebec2025, *, revenu_net_quebec: Decimal
) -> BaseSolidariteQuebec2025 | None:
    """Recevoir le revenu Québec recalculé; jamais un crédit saisi manuellement.

    Le résultat n'est pas un paiement à ajouter au rapprochement TP-1 2025.
    Aucun taux, plafond ou montant de solidarité n'est calculé dans ce périmètre.
    """
    valider_solidarite_quebec_2025(profil)
    if (not isinstance(revenu_net_quebec, Decimal) or not revenu_net_quebec.is_finite()
            or not Decimal(0) <= revenu_net_quebec <= Decimal("999999999.99")
            or revenu_net_quebec != arrondir_cent(revenu_net_quebec)):
        raise ValueError("Revenu net Québec 275 : Decimal fini, non négatif et au cent requis.")
    if not profil.activer:
        return None
    return BaseSolidariteQuebec2025(revenu_net_quebec, profil.vit_seul_toute_annee)


def solidarite_quebec_vers_dict(profil: SolidariteQuebec2025) -> dict:
    """Sérialiser les faits seuls; la base de revenu est recalculée au chargement."""
    valider_solidarite_quebec_2025(profil)
    return {champ.name: getattr(profil, champ.name) for champ in fields(profil)}


def solidarite_quebec_depuis_dict(valeur) -> SolidariteQuebec2025:
    if valeur is None:
        return SolidariteQuebec2025()
    if not isinstance(valeur, dict) or set(valeur) - {champ.name for champ in fields(SolidariteQuebec2025)}:
        raise ValueError("Profil solidarité : objet JSON ou clés invalides.")
    return valider_solidarite_quebec_2025(SolidariteQuebec2025(**valeur))


def lignes_solidarite_quebec_2025(
    profil: SolidariteQuebec2025, base: BaseSolidariteQuebec2025 | None
) -> tuple[str, ...]:
    """Audit narratif distinct des lignes monétaires de la déclaration."""
    if not profil.activer or base is None:
        return ()
    return (
        "",
        "SOLIDARITÉ QUÉBEC - PRÉPARATION ANNEXE D 2025 (6H)",
        "Période visée : juillet 2026 à juin 2027.",
        "Composante TVQ demandée / admissibilité préparée, sans droit à un versement garanti.",
        f"Faits 2025 : naissance {profil.naissance}; adulte au 31 décembre 2025.",
        "Résidence Québec/Canada toute l'année, dont le 31 décembre 2025; citoyenneté canadienne confirmée.",
        "Sans conjoint ni enfant en 2025; logement non admissible et hors village nordique confirmés.",
        "Vie seule dans une habitation pendant toute l'année 2025 : "
        + ("oui" if profil.vit_seul_toute_annee else "non") + "; réponse vérifiée.",
        "Absence de détention, d'Allocation famille pour soi et de cas particuliers confirmée.",
        f"Revenu familial préparé : ligne Québec 275 recalculée = {base.revenu_familial:.2f} $.",
        *wrap(f"Source des faits : {profil.source}; validation comptable confirmée.", width=50),
        "Montant monétaire non calculé par ComptaPrivée AI.",
        "Montant final déterminé séparément par Revenu Québec.",
        "Aucun effet sur le remboursement/solde TP-1 2025, ni sur l'impôt fédéral ou Québec.",
        "Préparation seulement : aucune annexe D officielle produite ni transmise.",
        "Références : RQ TP-1.D.D (2025-12), pages 1-2; TP-1.G (2025-12), pages 12-13.",
    )
