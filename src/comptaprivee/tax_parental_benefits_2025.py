"""RQAP ordinaire 2025 : T4E/RL-6 appariés, sans double comptage.

Sources et exclusions : docs/moteur_fiscal_2025.md, bloc 2A.
Les remboursements concernent exclusivement des prestations de 2025.
"""
from dataclasses import dataclass, replace
from decimal import Decimal

from .tax_field_validation import STATUT_VALIDE, STATUT_CORRIGE_VALIDE
from .tax_field_extractor import formater_montant_fiscal
from .tax_income_2025 import RevenuNetImposable2025
from .tax_rules_2025 import arrondir_cent
from .tax_validated_case import DossierFiscalValide

ZERO = Decimal("0")


@dataclass(frozen=True)
class PrestationsRqap2025:
    prestations: Decimal = ZERO
    remboursement: Decimal = ZERO
    retenue_federale: Decimal = ZERO
    retenue_quebec: Decimal = ZERO
    cotisation_fss: Decimal = ZERO
    present: bool = False


def valider_confirmation_rqap(confirme: bool) -> bool:
    if type(confirme) is not bool:
        raise ValueError("La confirmation RQAP doit être un booléen.")
    return confirme


def consolider_prestations_rqap_2025(
    dossier: DossierFiscalValide, confirme: bool = False,
) -> PrestationsRqap2025:
    """Exige une revue des feuillets complets, y compris les cases non extraites."""
    valider_confirmation_rqap(confirme)
    if any(d.type_document not in {"T4", "RL-1", "T4E", "RL-6"} for d in dossier.donnees_validees):
        raise ValueError("Revenu de retraite ou autre feuillet hors périmètre du moteur actuel.")
    donnees = [d for d in dossier.donnees_validees if d.type_document in {"T4E", "RL-6"}]
    if not donnees:
        if confirme:
            raise ValueError("Aucun T4E/RL-6 validé pour confirmer le profil RQAP.")
        return PrestationsRqap2025()
    if dossier.annee_fiscale != 2025 or dossier.province.casefold() not in {"québec", "quebec"}:
        raise ValueError("Le profil RQAP exige un dossier Québec 2025.")
    if not confirme:
        raise ValueError("Confirmez le profil RQAP 2025 après vérification complète des feuillets.")
    documents = {t: {d.document.resolve() for d in donnees if d.type_document == t} for t in ("T4E", "RL-6")}
    if any(len(x) != 1 for x in documents.values()) or documents["T4E"] == documents["RL-6"]:
        raise ValueError("Le profil RQAP exige exactement un T4E et un RL-6 distincts et appariés.")
    pieces = {p.resolve() for p in dossier.documents}
    valeurs = {}
    for d in donnees:
        cle = (d.type_document, d.case)
        if cle in valeurs:
            raise ValueError("Case RQAP dupliquée : " + str(cle))
        if d.document.resolve() not in pieces or d.statut not in {STATUT_VALIDE, STATUT_CORRIGE_VALIDE}:
            raise ValueError("Source ou validation comptable RQAP manquante.")
        montant = d.valeur_validee
        if (not isinstance(montant, Decimal) or not montant.is_finite() or montant < ZERO
                or montant > Decimal("999999999.99") or montant != montant.quantize(Decimal("0.01"))):
            raise ValueError("Montant RQAP invalide : fini, positif ou nul, au cent près requis.")
        valeurs[cle] = montant
    def case(t, c):
        return valeurs.get((t, c), ZERO)
    for cle in (("T4E", "14"), ("T4E", "36"), ("RL-6", "A")):
        if cle not in valeurs:
            raise ValueError("Case RQAP obligatoire absente : " + str(cle))
    autorisees = {"T4E": {"14", "36", "22", "23", "26", "27", "30"}, "RL-6": {"A", "D", "G"}}
    for (t, c), montant in valeurs.items():
        if c not in autorisees[t] and montant:
            raise ValueError(f"{t} case {c} : assurance-emploi ou situation hors profil RQAP ordinaire.")
    brut = case("T4E", "14")
    if brut != case("T4E", "36") or brut != case("RL-6", "A"):
        raise ValueError("Prestations incohérentes : T4E 14 = T4E 36 = RL-6 A requis; AE exclue.")
    remboursement = case("T4E", "30")
    if remboursement != case("RL-6", "D") or case("T4E", "23") != case("RL-6", "G"):
        raise ValueError("Remboursement ou retenue Québec incohérents entre T4E et RL-6.")
    if any(("T4E", c) in valeurs for c in ("26", "27")):
        if remboursement != case("T4E", "26") + case("T4E", "27"):
            raise ValueError("T4E : la case 30 doit égaler les cases 26 et 27.")
    if remboursement > brut:
        raise ValueError("Remboursement supérieur aux prestations 2025 : traitement distinct requis.")
    # Annexe F 2025 : le salaire est soustrait; RPA/REER ne réduisent pas
    # l'assiette. Le remboursement ligne 246 admissible est déduit ligne 41.
    assiette = brut - remboursement
    if assiette <= Decimal("63060"):
        fss = min(Decimal("150"), max(ZERO, (assiette - Decimal("18130")) * Decimal("0.01")))
    else:
        fss = min(Decimal("1000"), Decimal("150") + (assiette - Decimal("63060")) * Decimal("0.01"))
    return PrestationsRqap2025(brut, remboursement, case("T4E", "22"), case("RL-6", "G"), arrondir_cent(fss), True)


def appliquer_prestations_rqap_2025(revenu: RevenuNetImposable2025, prestations: PrestationsRqap2025) -> RevenuNetImposable2025:
    if not prestations.present:
        return revenu
    ajout = prestations.prestations - prestations.remboursement
    return replace(
        revenu,
        revenu_total_federal=revenu.revenu_total_federal + prestations.prestations,
        revenu_total_quebec=revenu.revenu_total_quebec + prestations.prestations,
        revenu_net_federal=max(ZERO, revenu.revenu_total_federal + ajout - revenu.deduction_rrq_amelioree_federale),
        revenu_imposable_federal=max(ZERO, revenu.revenu_total_federal + ajout - revenu.deduction_rrq_amelioree_federale),
        revenu_net_quebec=max(ZERO, revenu.revenu_total_quebec + ajout - revenu.deduction_rrq_quebec - revenu.deduction_travailleur_quebec),
        revenu_imposable_quebec=max(ZERO, revenu.revenu_total_quebec + ajout - revenu.deduction_rrq_quebec - revenu.deduction_travailleur_quebec),
        profil="Emploi Québec et RQAP ordinaire 2025",
        limitations=revenu.limitations + ("RQAP 2025 inclus; remboursements d'années antérieures et rétroactivité exclus.",),
    )


def lignes_resume_rqap_2025(p: PrestationsRqap2025) -> list[str]:
    if not p.present:
        return []
    fmt = formater_montant_fiscal
    return [
        "", "PRESTATIONS RQAP 2025 - FEUILLETS VALIDÉS",
        f"Fédéral 11900 (T4E 14/36) : {fmt(p.prestations)}",
        f"Fédéral 11905 (inclus dans 11900) : {fmt(p.prestations)}",
        f"Québec 110 (RL-6 A) : {fmt(p.prestations)}",
        f"Déduction 23200 / 246 (T4E 30 / RL-6 D) : {fmt(p.remboursement)}",
        f"Retenue fédérale 43700 (T4E 22) : {fmt(p.retenue_federale)}",
        f"Retenue Québec 451 (RL-6 G = T4E 23) : {fmt(p.retenue_quebec)}",
        f"FSS Québec 446 (annexe F 2025) : {fmt(p.cotisation_fss)}",
        "Profil confirmé : résidence Canada/Québec toute l'année, feuillets 2025 complets.",
        "RQAP ordinaire uniquement; remboursements limités aux prestations de 2025.",
        "Sans AE, prestations exonérées, rétroactivité ni remboursement d'années antérieures.",
    ]
