"""Bloc 2C : prestations RRQ/RPC ordinaires; sources dans moteur_fiscal_2025.md."""
from dataclasses import dataclass, fields, replace
from decimal import Decimal

from .tax_employment_insurance_2025 import cotisation_fss_prestations_2025
from .tax_engine_input_2025 import BaseFiscaleEmploi2025
from .tax_field_extractor import formater_montant_fiscal
from .tax_field_validation import STATUT_VALIDE, STATUT_CORRIGE_VALIDE
from .tax_income_2025 import RevenuNetImposable2025
from .tax_validated_case import DossierFiscalValide

ZERO = Decimal("0")


@dataclass(frozen=True)
class PrestationsRrqRpc2025:
    prestations: Decimal = ZERO
    retraite: Decimal = ZERO
    survivant: Decimal = ZERO
    invalidite: Decimal = ZERO
    enfant: Decimal = ZERO
    apres_retraite: Decimal = ZERO
    retenue_federale: Decimal = ZERO
    retenue_quebec: Decimal = ZERO
    cotisation_fss: Decimal = ZERO
    releve_2_present: bool = False
    present: bool = False


def valider_confirmation_rrq_rpc(confirme: bool) -> bool:
    if type(confirme) is not bool:
        raise ValueError("La confirmation RRQ/RPC doit être un booléen.")
    return confirme


def consolider_prestations_rrq_rpc_2025(
    dossier: DossierFiscalValide, confirme: bool = False,
) -> PrestationsRrqRpc2025:
    valider_confirmation_rrq_rpc(confirme)
    if any(d.type_document not in {"T4", "RL-1", "T4A(P)", "RL-2"} for d in dossier.donnees_validees):
        raise ValueError("RRQ/RPC : AE, RQAP, PSV et autres revenus combinés hors périmètre.")
    donnees = [d for d in dossier.donnees_validees if d.type_document in {"T4A(P)", "RL-2"}]
    if not donnees:
        if confirme:
            raise ValueError("Aucun T4A(P) validé pour confirmer le profil RRQ/RPC.")
        return PrestationsRrqRpc2025()
    if dossier.annee_fiscale != 2025 or dossier.province.casefold() not in {"québec", "quebec"}:
        raise ValueError("Le profil RRQ/RPC exige un dossier Québec 2025.")
    if not confirme:
        raise ValueError("Confirmez le profil RRQ/RPC : bénéficiaire, absence de rétroactivité, décès et remboursements.")
    docs = {t: {d.document.resolve() for d in donnees if d.type_document == t} for t in ("T4A(P)", "RL-2")}
    if len(docs["T4A(P)"]) != 1 or len(docs["RL-2"]) > 1 or docs["T4A(P)"] & docs["RL-2"]:
        raise ValueError("Un seul T4A(P) et au plus un RL-2 distinct et apparié sont requis.")
    valeurs = {}
    pieces = {p.resolve() for p in dossier.documents}
    for d in donnees:
        cle = (d.type_document, d.case)
        if cle in valeurs:
            raise ValueError("Case RRQ/RPC dupliquée : " + str(cle))
        if d.document.resolve() not in pieces or d.statut not in {STATUT_VALIDE, STATUT_CORRIGE_VALIDE}:
            raise ValueError("Source ou validation comptable RRQ/RPC manquante.")
        m = d.valeur_validee
        if (not isinstance(m, Decimal) or not m.is_finite() or m < ZERO
                or m > Decimal("999999999.99") or m != m.quantize(Decimal("0.01"))):
            raise ValueError("Montant RRQ/RPC invalide : fini, positif ou nul, au cent près requis.")
        valeurs[cle] = m
    def case(t, c):
        return valeurs.get((t, c), ZERO)
    if ("T4A(P)", "20") not in valeurs:
        raise ValueError("Case T4A(P) 20 obligatoire.")
    autorisees = {"T4A(P)": {"14", "15", "16", "17", "19", "20", "21", "22", "23"}, "RL-2": {"C", "J"}}
    for (t, c), m in valeurs.items():
        if c not in autorisees[t] and m:
            raise ValueError(f"{t} case {c} : décès, remboursement ou autre prestation hors périmètre RRQ/RPC.")
    for c in ("21", "23"):
        m = case("T4A(P)", c)
        if m != m.to_integral_value() or m > 12:
            raise ValueError("T4A(P) : nombre de mois invalide (0 à 12 entiers).")
    brut = case("T4A(P)", "20")
    if sum((case("T4A(P)", c) for c in ("14", "15", "16", "17", "19")), ZERO) > brut:
        raise ValueError("Sous-cases T4A(P) supérieures au total 20.")
    # Certains feuillets RRQ ne détaillent pas toutes les sous-cases : la
    # confirmation couvre la nature du solde et les renseignements non extraits.
    rl2 = bool(docs["RL-2"])
    if rl2 and (("RL-2", "C") not in valeurs or case("RL-2", "C") != brut):
        raise ValueError("T4A(P) 20 et RL-2 C doivent concorder exactement, sans double compte.")
    salaire = any(d.type_document in {"T4", "RL-1"} and d.valeur_validee > ZERO
                  for d in dossier.donnees_validees)
    if salaire and (case("T4A(P)", "16") or case("T4A(P)", "21") or case("T4A(P)", "17")):
        raise ValueError("Invalidité ou rente d'enfant avec salaire : cotisations et proratisation hors périmètre.")
    if case("T4A(P)", "17") and any(case("T4A(P)", c) for c in ("14", "15", "16", "19")):
        raise ValueError("Rente d'enfant : bénéficiaires ou prestations mixtes hors périmètre.")
    return PrestationsRrqRpc2025(
        prestations=brut, retraite=case("T4A(P)", "14"), survivant=case("T4A(P)", "15"),
        invalidite=case("T4A(P)", "16"), enfant=case("T4A(P)", "17"),
        apres_retraite=case("T4A(P)", "19"), retenue_federale=case("T4A(P)", "22"),
        retenue_quebec=case("RL-2", "J"), cotisation_fss=cotisation_fss_prestations_2025(brut),
        releve_2_present=rl2, present=True,
    )


def base_sans_emploi_rrq_rpc_2025(dossier: DossierFiscalValide) -> BaseFiscaleEmploi2025:
    """Base salariale vide, sans inventer de T4/RL-1; profil déjà validé."""
    if any(d.type_document in {"T4", "RL-1"} for d in dossier.donnees_validees):
        raise ValueError("Des feuillets salariaux doivent suivre la consolidation d'emploi.")
    identite = dict(client=dossier.client, annee_fiscale=dossier.annee_fiscale, province=dossier.province,
                    nombre_t4=0, nombre_rl1=0, avertissements=())
    return BaseFiscaleEmploi2025(**{f.name: identite.get(f.name, ZERO) for f in fields(BaseFiscaleEmploi2025)})


def revenu_sans_emploi_rrq_rpc_2025(dossier: DossierFiscalValide) -> RevenuNetImposable2025:
    identite = dict(client=dossier.client, annee_fiscale=dossier.annee_fiscale, province=dossier.province,
                    profil="RRQ/RPC sans emploi 2025", limitations=("Prestations ordinaires validées uniquement.",))
    return RevenuNetImposable2025(**{f.name: identite.get(f.name, ZERO) for f in fields(RevenuNetImposable2025)})


def appliquer_prestations_rrq_rpc_2025(revenu: RevenuNetImposable2025, p: PrestationsRrqRpc2025) -> RevenuNetImposable2025:
    if not p.present:
        return revenu
    noms = ("revenu_total_federal", "revenu_net_federal", "revenu_imposable_federal",
            "revenu_total_quebec", "revenu_net_quebec", "revenu_imposable_quebec")
    return replace(revenu, **{n: getattr(revenu, n) + p.prestations for n in noms},
                   profil="RRQ/RPC ordinaire Québec 2025, avec ou sans emploi")


def lignes_resume_rrq_rpc_2025(p: PrestationsRrqRpc2025) -> list[str]:
    if not p.present:
        return []
    fmt = formater_montant_fiscal
    return ["", "PRESTATIONS RRQ/RPC 2025 - FEUILLETS VALIDÉS",
        f"Revenu fédéral 11400 (T4A(P) 20) : {fmt(p.prestations)}",
        f"Revenu Québec 119 ({'RL-2 C' if p.releve_2_present else 'T4A(P) 20, aucun RL-2 reçu'}) : {fmt(p.prestations)}",
        f"Retraite / survivant (14 / 15) : {fmt(p.retraite)} / {fmt(p.survivant)}",
        f"Invalidité 11410 (16, déjà comprise dans 11400) : {fmt(p.invalidite)}",
        f"Rente d'enfant (17), revenu du bénéficiaire enfant : {fmt(p.enfant)}",
        f"Après-retraite (19, compris dans 20) : {fmt(p.apres_retraite)}",
        f"Retenue fédérale 43700 (T4A(P) 22) : {fmt(p.retenue_federale)}",
        f"Retenue Québec 451 (RL-2 J) : {fmt(p.retenue_quebec)}",
        f"FSS Québec 446, assiette RRQ/RPC {fmt(p.prestations)} : {fmt(p.cotisation_fss)}",
        "Aucun double compte des sous-cases ou du RL-2. Aucun crédit de pension 31400/361.",
        "Profil confirmé : bénéficiaire du dossier; Canada/Québec toute l'année 2025.",
        "Sans rétroactivité, prestation de décès, remboursement ni partage de rente.",
    ]
