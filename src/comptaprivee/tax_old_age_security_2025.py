"""Bloc 2D : PSV ordinaire, suppléments et récupération 2025.

Sources et exclusions : docs/moteur_fiscal_2025.md.
"""
from dataclasses import dataclass, replace
from decimal import Decimal, ROUND_HALF_UP
from .tax_field_extractor import formater_montant_fiscal
from .tax_field_validation import STATUT_VALIDE, STATUT_CORRIGE_VALIDE
from .tax_income_2025 import RevenuNetImposable2025
from .tax_validated_case import DossierFiscalValide

ZERO = Decimal("0")
SEUIL_RECUPERATION_PSV = Decimal("93454")

@dataclass(frozen=True)
class PrestationsPsv2025:
    pension: Decimal = ZERO
    supplements: Decimal = ZERO
    retenue_federale: Decimal = ZERO
    retenue_quebec: Decimal = ZERO
    revenu_avant_recuperation: Decimal = ZERO
    recuperation: Decimal = ZERO
    supplements_recuperes: Decimal = ZERO
    deduction_supplements: Decimal = ZERO
    present: bool = False


def valider_confirmation_psv(confirme: bool) -> bool:
    if type(confirme) is not bool:
        raise ValueError("La confirmation PSV doit être un booléen.")
    return confirme


def consolider_prestations_psv_2025(dossier: DossierFiscalValide, confirme: bool = False) -> PrestationsPsv2025:
    valider_confirmation_psv(confirme)
    if any(d.type_document not in {"T4", "RL-1", "T4A(OAS)"} for d in dossier.donnees_validees):
        raise ValueError("PSV : AE, RQAP, RRQ/RPC et autres revenus combinés hors périmètre.")
    donnees = [d for d in dossier.donnees_validees if d.type_document in {"T4A(OAS)"}]
    if not donnees:
        if confirme:
            raise ValueError("Aucun T4A(OAS) validé pour confirmer le profil PSV.")
        return PrestationsPsv2025()
    if dossier.annee_fiscale != 2025 or dossier.province.casefold() not in {"québec", "quebec"}:
        raise ValueError("Le profil PSV exige un dossier Québec 2025.")
    if not confirme:
        raise ValueError("Confirmez le profil PSV : bénéficiaire, absence de rétroactivité, décès et remboursements.")
    docs = {t: {d.document.resolve() for d in donnees if d.type_document == t} for t in ("T4A(OAS)",)}
    if len(docs["T4A(OAS)"]) != 1:
        raise ValueError("Un seul T4A(OAS) est requis.")
    valeurs = {}
    pieces = {p.resolve() for p in dossier.documents}
    for d in donnees:
        cle = (d.type_document, d.case)
        if cle in valeurs:
            raise ValueError("Case PSV dupliquée : " + str(cle))
        if d.document.resolve() not in pieces or d.statut not in {STATUT_VALIDE, STATUT_CORRIGE_VALIDE}:
            raise ValueError("Source ou validation comptable PSV manquante.")
        m = d.valeur_validee
        if (not isinstance(m, Decimal) or not m.is_finite() or m < ZERO
                or m > Decimal("999999999.99") or m != m.quantize(Decimal("0.01"))):
            raise ValueError("Montant PSV invalide : fini, positif ou nul, au cent près requis.")
        valeurs[cle] = m
    def case(c):
        return valeurs.get(("T4A(OAS)", c), ZERO)
    if ("T4A(OAS)", "18") not in valeurs:
        raise ValueError("Case T4A(OAS) 18 obligatoire, même si nulle pour des suppléments seuls.")
    for (_, c), m in valeurs.items():
        if c not in {"18", "19", "21", "22", "23"} and m:
            raise ValueError(f"T4A(OAS) case {c} : remboursement ou autre montant hors périmètre PSV.")
    if ("T4A(OAS)", "19") in valeurs and case("19") != case("18"):
        raise ValueError("T4A(OAS) 19 et 18 doivent concorder sans remboursement case 20.")
    return PrestationsPsv2025(pension=case("18"), supplements=case("21"),
        retenue_federale=case("22"), retenue_quebec=case("23"), present=True)


def appliquer_revenu_psv_2025(revenu: RevenuNetImposable2025, p: PrestationsPsv2025) -> RevenuNetImposable2025:
    if not p.present:
        return revenu
    noms = ("revenu_total_federal", "revenu_net_federal", "revenu_imposable_federal",
            "revenu_total_quebec", "revenu_net_quebec", "revenu_imposable_quebec")
    return replace(revenu, **{n: getattr(revenu, n) + p.pension + p.supplements for n in noms},
                   profil="PSV et suppléments ordinaires Québec 2025, avec ou sans emploi")


def appliquer_recuperation_psv_2025(revenu: RevenuNetImposable2025, p: PrestationsPsv2025):
    """Après les déductions ordinaires, avant crédits; aucun ajustement PUGE/REEI/AE."""
    if not p.present:
        return revenu, p
    net = revenu.revenu_net_federal
    recuperation = min(p.pension + p.supplements,
        (max(ZERO, net - SEUIL_RECUPERATION_PSV) * Decimal("0.15")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    recuperes = max(ZERO, recuperation - p.pension)
    deduction = max(ZERO, p.supplements - recuperes)
    p = replace(p, revenu_avant_recuperation=net, recuperation=recuperation,
                supplements_recuperes=recuperes, deduction_supplements=deduction)
    revenu = replace(revenu,
        revenu_net_federal=max(ZERO, revenu.revenu_net_federal-recuperation),
        revenu_net_quebec=max(ZERO, revenu.revenu_net_quebec-recuperation),
        revenu_imposable_federal=max(ZERO, revenu.revenu_imposable_federal-recuperation-deduction),
        revenu_imposable_quebec=max(ZERO, revenu.revenu_imposable_quebec-recuperation-deduction))
    return revenu, p


def lignes_resume_psv_2025(p: PrestationsPsv2025, calcul_effectue: bool = True) -> list[str]:
    if not p.present:
        return []
    fmt = formater_montant_fiscal
    lignes = ["", "PSV ET SUPPLÉMENTS 2025 - T4A(OAS) VALIDÉ",
        f"PSV 11300 / Québec 114 (case 18) : {fmt(p.pension)}",
        f"Suppléments 14600 / Québec 148, code 07 (case 21) : {fmt(p.supplements)}",
        f"Retenue fédérale 43700 (case 22) : {fmt(p.retenue_federale)}",
        f"Retenue Québec 451 (case 23) : {fmt(p.retenue_quebec)}"]
    if calcul_effectue:
        lignes += [f"Revenu avant récupération 23400 : {fmt(p.revenu_avant_recuperation)}",
            f"Récupération 23500 / 42200 / Québec 250 point 3 : {fmt(p.recuperation)}",
            f"Dont suppléments récupérés : {fmt(p.supplements_recuperes)}",
            f"Déduction suppléments 25000 / Québec 295 : {fmt(p.deduction_supplements)}"]
    else:
        lignes += ["Récupération et déduction des suppléments : à calculer après les déductions ordinaires."]
    return lignes + ["FSS Québec 446 : 0,00 $ (PSV et suppléments exclus de l'assiette).",
        "Aucun crédit de pension 31400/361; case 19 non additionnée; retenues distinctes de la récupération.",
        "Profil confirmé : bénéficiaire du dossier; Canada/Québec toute l'année 2025.",
        "Sans rétroactivité, décès, remboursement, AE/RQAP/RRQ ou autre revenu hors profil."]
