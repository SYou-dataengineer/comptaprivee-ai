"""RPA canadien, services courants 2025 : lignes 20700 et 205.

Sources et périmètre : docs/moteur_fiscal_2025.md. Aucun plafond REER
n'est appliqué aux cotisations RPA. Les situations spéciales sont exclues.
"""

from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation
import textwrap

from .tax_income_2025 import RevenuNetImposable2025
from .tax_validated_case import DossierFiscalValide

ZERO = Decimal("0")
SOURCE_ARC = "https://www.canada.ca/fr/agence-revenu/services/impot/particuliers/sujets/tout-votre-declaration-revenus/declaration-revenus/remplir-declaration-revenus/deductions-credits-depenses/ligne-20700-deduction-regimes-pension-agrees.html"
SOURCE_RQ = "https://www.revenuquebec.ca/fr/citoyens/declaration-de-revenus/produire-votre-declaration-de-revenus/comment-remplir-votre-declaration-de-revenus/aide-par-ligne/201-a-260-revenu-net/ligne-205/"


@dataclass(frozen=True)
class CotisationsRpa2025:
    montant_federal: Decimal = ZERO
    montant_quebec: Decimal = ZERO
    source_federale: str = ""
    source_quebec: str = ""
    services_courants_uniquement: bool = False
    valide_par_comptable: bool = False


def montant_rpa_depuis_champ(valeur: str) -> Decimal:
    """Saisie monétaire en dollars; refuse arrondis silencieux et non-finis."""
    if not isinstance(valeur, str):
        raise ValueError("Le montant RPA doit être une chaîne monétaire.")
    texte = valeur.strip().replace("\u00a0", "").replace("\u202f", "")
    texte = texte.replace(" ", "").replace("$", "").replace(",", ".")
    try:
        montant = Decimal(texte or "0")
        _valider_montant(montant)
    except (InvalidOperation, ValueError) as erreur:
        raise ValueError("Montant RPA invalide : utilisez un montant positif à deux décimales au maximum.") from erreur
    return montant


def _valider_montant(montant):
    if (not isinstance(montant, Decimal) or not montant.is_finite()
            or montant < ZERO or montant > Decimal("999999999.99")):
        raise ValueError("Montant RPA invalide ou hors capacité de saisie.")
    if montant != montant.quantize(Decimal("0.01")):
        raise ValueError("Le montant RPA doit être exprimé au cent près.")


def valider_cotisations_rpa_2025(profil: CotisationsRpa2025) -> CotisationsRpa2025:
    if not isinstance(profil, CotisationsRpa2025):
        raise ValueError("Profil RPA invalide.")
    for montant in (profil.montant_federal, profil.montant_quebec):
        _valider_montant(montant)
    for valeur in (profil.services_courants_uniquement, profil.valide_par_comptable):
        if type(valeur) is not bool:
            raise ValueError("Les confirmations RPA doivent être booléennes.")
    for source in (profil.source_federale, profil.source_quebec):
        if not isinstance(source, str) or len(source) > 1000 or any(ord(c) < 32 for c in source):
            raise ValueError("Source RPA invalide (texte sur une ligne, 1 000 caractères maximum).")
    if profil.montant_quebec > profil.montant_federal:
        raise ValueError("La déduction RPA Québec ligne 205 ne peut dépasser la ligne fédérale 20700.")
    if profil.montant_federal > ZERO:
        if not profil.services_courants_uniquement:
            raise ValueError("Confirmez les services courants seulement : rachats, reports, transferts, conventions de retraite et régimes étrangers exclus.")
        if not profil.valide_par_comptable:
            raise ValueError("Les cotisations RPA doivent être validées par le comptable.")
        if not profil.source_federale.strip():
            raise ValueError("La source fédérale RPA est obligatoire.")
        if profil.montant_quebec > ZERO and not profil.source_quebec.strip():
            raise ValueError("La source Québec RPA est obligatoire.")
    return profil


def verifier_rpa_dossier_2025(dossier: DossierFiscalValide, profil: CotisationsRpa2025) -> None:
    """Les cases validées contrôlent la saisie; elles ne s'y additionnent pas."""
    valider_cotisations_rpa_2025(profil)
    if dossier.annee_fiscale != 2025 or dossier.province.strip().lower() not in {"québec", "quebec"}:
        raise ValueError("Le profil RPA accepte uniquement un dossier Québec 2025.")
    for donnee in dossier.donnees_validees:
        if ((donnee.type_document == "RL-1" and donnee.case in {"D-1", "D-2", "D-3"})
                or (donnee.type_document == "T4" and donnee.case in {"74", "75"})):
            _valider_montant(donnee.valeur_validee)
            if donnee.valeur_validee:
                raise ValueError("RPA : services passés ou convention de retraite hors profil; traitement avancé requis.")
    for type_document, case, montant in (
        ("T4", "20", profil.montant_federal),
        ("RL-1", "D", profil.montant_quebec),
    ):
        donnees = [d for d in dossier.donnees_validees if d.type_document == type_document and d.case == case]
        if len({str(d.document) for d in donnees}) != len(donnees):
            raise ValueError("Une case RPA validée est dupliquée.")
        for donnee in donnees:
            _valider_montant(donnee.valeur_validee)
        if donnees and sum((d.valeur_validee for d in donnees), ZERO) != montant:
            raise ValueError(f"Le montant RPA doit correspondre à {type_document} case {case}; ouvrez Cotisations RPA 2025.")


def appliquer_cotisations_rpa_2025(revenu: RevenuNetImposable2025, profil: CotisationsRpa2025) -> RevenuNetImposable2025:
    valider_cotisations_rpa_2025(profil)
    if revenu.annee_fiscale != 2025 or revenu.province.strip().lower() not in {"québec", "quebec"}:
        raise ValueError("Le calcul RPA accepte uniquement le Québec 2025.")
    if not profil.montant_federal:
        return revenu
    return replace(
        revenu,
        revenu_net_federal=max(ZERO, revenu.revenu_net_federal - profil.montant_federal),
        revenu_imposable_federal=max(ZERO, revenu.revenu_imposable_federal - profil.montant_federal),
        revenu_net_quebec=max(ZERO, revenu.revenu_net_quebec - profil.montant_quebec),
        revenu_imposable_quebec=max(ZERO, revenu.revenu_imposable_quebec - profil.montant_quebec),
        profil=revenu.profil + " + RPA services courants",
        limitations=tuple(x for x in revenu.limitations if x != "Aucune autre déduction de revenu net ou imposable.") + (
            "RPA services courants inclus (20700/205); rachats, reports, transferts et régimes étrangers exclus.",
        ),
    )


def lignes_resume_rpa_2025(profil: CotisationsRpa2025) -> list[str]:
    if not profil.montant_federal:
        return []
    def montant(valeur):
        return f"{valeur:,.2f}".replace(",", "\u00a0").replace(".", ",") + " $"
    return [
        "", "COTISATIONS RPA 2025 - SERVICES COURANTS",
        "Déduction fédérale - ligne 20700 : " + montant(profil.montant_federal),
        "Déduction Québec - ligne 205 : " + montant(profil.montant_quebec),
        *textwrap.wrap("Source fédérale : " + profil.source_federale, width=48),
        *textwrap.wrap("Source Québec : " + profil.source_quebec, width=48),
        "Validation comptable et services courants : confirmés.",
        "Rachats, reports, transferts, conventions de retraite et régimes étrangers exclus.",
        "Références : ARC ligne 20700; Revenu Québec ligne 205 (2025).",
    ]
