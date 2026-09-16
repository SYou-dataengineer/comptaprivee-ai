"""AE ordinaire 2025, T4E : revenu, remboursement et récupération.

Références officielles et périmètre : docs/moteur_fiscal_2025.md, bloc 2B.
"""
from dataclasses import dataclass, replace
from decimal import Decimal

from .tax_field_extractor import formater_montant_fiscal
from .tax_field_validation import STATUT_VALIDE, STATUT_CORRIGE_VALIDE
from .tax_income_2025 import RevenuNetImposable2025
from .tax_rules_2025 import arrondir_cent
from .tax_validated_case import DossierFiscalValide

ZERO = Decimal("0")
SEUIL_RECUPERATION_AE_2025 = Decimal("82125")


def cotisation_fss_prestations_2025(assiette: Decimal) -> Decimal:
    """Annexe F 2025 : assiette établie par le profil, sans RPA/REER."""
    if not isinstance(assiette, Decimal) or not assiette.is_finite() or assiette < ZERO:
        raise ValueError("Assiette FSS invalide.")
    if assiette <= Decimal("63060"):
        montant = min(Decimal("150"), max(ZERO, (assiette - Decimal("18130")) * Decimal("0.01")))
    else:
        montant = min(Decimal("1000"), Decimal("150") + (assiette - Decimal("63060")) * Decimal("0.01"))
    return arrondir_cent(montant)


@dataclass(frozen=True)
class PrestationsAe2025:
    prestations: Decimal = ZERO
    regulieres: Decimal = ZERO
    maternite_parentales: Decimal = ZERO
    remboursement: Decimal = ZERO
    taux_remboursement: Decimal = ZERO
    retenue_federale: Decimal = ZERO
    retenue_quebec: Decimal = ZERO
    revenu_avant_recuperation: Decimal = ZERO
    recuperation: Decimal = ZERO
    cotisation_fss: Decimal = ZERO
    present: bool = False


def valider_confirmation_ae(confirme: bool) -> bool:
    if type(confirme) is not bool:
        raise ValueError("La confirmation AE doit être un booléen.")
    return confirme


def consolider_prestations_ae_2025(dossier: DossierFiscalValide, confirme: bool = False) -> PrestationsAe2025:
    valider_confirmation_ae(confirme)
    if any(d.type_document not in {"T4", "RL-1", "T4E"} for d in dossier.donnees_validees):
        raise ValueError("AE : combinaison RQAP, retraite ou autre feuillet hors périmètre.")
    donnees = [d for d in dossier.donnees_validees if d.type_document == "T4E"]
    if not donnees:
        if confirme:
            raise ValueError("Aucun T4E validé pour confirmer le profil AE.")
        return PrestationsAe2025()
    if dossier.annee_fiscale != 2025 or dossier.province.casefold() not in {"québec", "quebec"}:
        raise ValueError("Le profil AE exige un dossier Québec 2025.")
    if not confirme:
        raise ValueError("Confirmez le profil assurance-emploi 2025 après revue complète du T4E.")
    if len({d.document.resolve() for d in donnees}) != 1:
        raise ValueError("Le profil AE exige exactement un T4E; feuillets multiples exclus.")
    pieces = {p.resolve() for p in dossier.documents}
    valeurs = {}
    for d in donnees:
        if d.case in valeurs:
            raise ValueError("Case T4E dupliquée : " + d.case)
        if d.document.resolve() not in pieces or d.statut not in {STATUT_VALIDE, STATUT_CORRIGE_VALIDE}:
            raise ValueError("Source ou validation comptable AE manquante.")
        m = d.valeur_validee
        if (not isinstance(m, Decimal) or not m.is_finite() or m < ZERO
                or m > Decimal("999999999.99") or m != m.quantize(Decimal("0.01"))):
            raise ValueError("Montant AE invalide : fini, positif ou nul et au cent près requis.")
        valeurs[d.case] = m
    for case in ("7", "14"):
        if case not in valeurs:
            raise ValueError("Case T4E obligatoire absente : " + case)
    if valeurs["7"] not in {ZERO, Decimal("30")}:
        raise ValueError("T4E case 7 : seuls les taux 0 % et 30 % sont pris en charge.")
    autorisees = {"7", "14", "15", "22", "23", "26", "27", "30", "37"}
    for c, m in valeurs.items():
        if c not in autorisees and m:
            raise ValueError(f"T4E case {c} : hors profil AE ordinaire (RQAP, aide, exonération ou autre cas).")
    brut = valeurs["14"]
    regulieres = valeurs.get("15", ZERO)
    parentales = valeurs.get("37", ZERO)
    remboursement = valeurs.get("30", ZERO)
    if regulieres + parentales > brut:
        raise ValueError("T4E incohérent : cases 15 et 37 supérieures au total de la case 14.")
    if remboursement > brut:
        raise ValueError("Remboursement supérieur aux prestations : années antérieures hors périmètre.")
    if any(c in valeurs for c in ("26", "27")):
        if remboursement != valeurs.get("26", ZERO) + valeurs.get("27", ZERO):
            raise ValueError("T4E : la case 30 doit égaler les cases 26 et 27.")
    return PrestationsAe2025(
        prestations=brut, regulieres=regulieres, maternite_parentales=parentales,
        remboursement=remboursement, taux_remboursement=valeurs["7"],
        retenue_federale=valeurs.get("22", ZERO), retenue_quebec=valeurs.get("23", ZERO), present=True,
    )


def appliquer_revenu_ae_2025(revenu: RevenuNetImposable2025, ae: PrestationsAe2025) -> RevenuNetImposable2025:
    """Avant RPA/REER : 11900 et Québec 111; déduction 23200/246."""
    if not ae.present:
        return revenu
    net_fed = max(ZERO, revenu.revenu_total_federal + ae.prestations - ae.remboursement - revenu.deduction_rrq_amelioree_federale)
    net_qc = max(ZERO, revenu.revenu_total_quebec + ae.prestations - ae.remboursement - revenu.deduction_rrq_quebec - revenu.deduction_travailleur_quebec)
    return replace(revenu,
        revenu_total_federal=revenu.revenu_total_federal + ae.prestations,
        revenu_total_quebec=revenu.revenu_total_quebec + ae.prestations,
        revenu_net_federal=net_fed, revenu_imposable_federal=net_fed,
        revenu_net_quebec=net_qc, revenu_imposable_quebec=net_qc,
        profil="Emploi Québec et assurance-emploi ordinaire 2025",
    )


def appliquer_recuperation_ae_2025(revenu: RevenuNetImposable2025, ae: PrestationsAe2025) -> tuple[RevenuNetImposable2025, PrestationsAe2025]:
    """Après les déductions, avant les crédits; pas de boucle sur la ligne 23600.

    Les ajustements PUGE/REEI et la PSV sont exclus du profil. La ligne 23400
    est donc le revenu net fédéral avant cette récupération.
    """
    if not ae.present:
        return revenu, ae
    recup = ZERO
    if ae.taux_remboursement == Decimal("30"):
        recup = arrondir_cent(Decimal("0.30") * min(
            max(ZERO, ae.regulieres - ae.remboursement),
            max(ZERO, revenu.revenu_net_federal - SEUIL_RECUPERATION_AE_2025),
        ))
    ae = replace(ae, revenu_avant_recuperation=revenu.revenu_net_federal,
        recuperation=recup,
        cotisation_fss=cotisation_fss_prestations_2025(ae.prestations - ae.remboursement - recup))
    return replace(revenu,
        revenu_net_federal=max(ZERO, revenu.revenu_net_federal - recup),
        revenu_imposable_federal=max(ZERO, revenu.revenu_imposable_federal - recup),
        revenu_net_quebec=max(ZERO, revenu.revenu_net_quebec - recup),
        revenu_imposable_quebec=max(ZERO, revenu.revenu_imposable_quebec - recup),
    ), ae


def lignes_resume_ae_2025(ae: PrestationsAe2025, *, calcul_effectue: bool = True) -> list[str]:
    if not ae.present:
        return []
    fmt = formater_montant_fiscal
    lignes = ["", "ASSURANCE-EMPLOI 2025 - T4E VALIDÉ",
        f"Revenu fédéral 11900 / Québec 111 (T4E 14) : {fmt(ae.prestations)}",
        f"Prestations régulières (T4E 15) : {fmt(ae.regulieres)}",
        f"11905, maternité/parentales (T4E 37, inclus dans 11900) : {fmt(ae.maternite_parentales)}",
        f"Remboursement 23200 / 246 (T4E 30) : {fmt(ae.remboursement)}",
        f"Taux de récupération (T4E 7) : {ae.taux_remboursement} %",
        f"Retenue fédérale 43700 (T4E 22) : {fmt(ae.retenue_federale)}",
        f"Retenue Québec 451 (T4E 23) : {fmt(ae.retenue_quebec)}",
    ]
    if calcul_effectue:
        lignes.extend([
            f"Revenu avant récupération, ligne 23400 : {fmt(ae.revenu_avant_recuperation)}",
            f"Récupération fédérale 23500 / 42200, Québec 250 : {fmt(ae.recuperation)}",
            f"FSS Québec 446, après remboursements 246 et 250 : {fmt(ae.cotisation_fss)}",
        ])
    else:
        lignes.append("Récupération et FSS déterminés lors du calcul après toutes les déductions.")
    lignes.extend([
        "Profil confirmé : T4E 2025 complet; résidence Canada/Québec toute l'année.",
        "AE ordinaire; remboursements de prestations de 2025 déjà incluses uniquement.",
        "Sans RQAP, PSV, REEI/PUGE, aide aux études, exonération ni rétroactivité.",
    ])
    return lignes
