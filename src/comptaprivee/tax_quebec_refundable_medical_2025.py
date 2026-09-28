"""Annexe B 2025, partie D et grille 462.1 : salarié individuel Québec."""
from dataclasses import dataclass, fields
from datetime import date
from decimal import Decimal
from .tax_rules_2025 import arrondir_cent

ZERO = Decimal(0)
CONFIRMATIONS_6E = {
    "residence_confirmee": "Résident du Canada toute l'année et du Québec au 31 décembre 2025",
    "profil_individuel_confirme": "Sans conjoint ni personne à charge dans ce profil individuel",
    "emploi_101_confirme": "Revenus d'emploi limités à la ligne 101; aucune ligne 105/107",
    "aucun_autre_travail_confirme": "Aucun revenu indépendant, incitation au travail ni protection des salariés à intégrer",
    "aucun_soutien_250_confirme": "Aucune déduction pour soutien à une personne handicapée, ligne 250 point 7",
    "profil_simple_confirme": "Contribuable vivant, sans faillite ni résidence partielle au Canada",
    "valide_par_comptable": "Naissance, feuillets, frais et périmètre vérifiés par le comptable",
}


@dataclass(frozen=True)
class MedicalRemboursableQuebec2025:
    reclamer: bool = False
    naissance: str = ""
    source: str = ""
    residence_confirmee: bool = False
    profil_individuel_confirme: bool = False
    emploi_101_confirme: bool = False
    aucun_autre_travail_confirme: bool = False
    aucun_soutien_250_confirme: bool = False
    profil_simple_confirme: bool = False
    valide_par_comptable: bool = False


def valider_medical_remboursable_quebec_2025(p):
    if not isinstance(p, MedicalRemboursableQuebec2025):
        raise ValueError("Profil médical remboursable Québec invalide.")
    for f in fields(p):
        if type(getattr(p, f.name)) is not type(f.default):
            raise ValueError("Type du profil médical Québec 462 invalide : " + f.name)
    if not p.reclamer:
        if p.naissance or p.source:
            raise ValueError("Activez le profil médical 462 ou effacez les données.")
        return p
    try:
        naissance = date.fromisoformat(p.naissance)
        if naissance.isoformat() != p.naissance:
            raise ValueError()
    except ValueError as erreur:
        raise ValueError("Naissance médicale 462 : date AAAA-MM-JJ requise.") from erreur
    if naissance > date(2007, 12, 31):
        raise ValueError("Le crédit médical remboursable exige 18 ans au 31 décembre 2025.")
    if not p.source.strip():
        raise ValueError("Source médicale Québec 462 obligatoire.")
    for nom, libelle in CONFIRMATIONS_6E.items():
        if not getattr(p, nom):
            raise ValueError("Confirmation obligatoire : " + libelle)
    return p


def montant_medical_remboursable_quebec(v, nom):
    if (not isinstance(v, Decimal) or not v.is_finite()
            or not ZERO <= v <= Decimal("999999999.99") or v != arrondir_cent(v)):
        raise ValueError("Montant médical remboursable Québec invalide : " + nom)
    return v


def avantages_ancien_emploi_211_2025(dossier):
    """Une case 211 validée par feuillet, sans compensation de valeurs invalides."""
    total, documents = ZERO, set()
    for d in dossier.donnees_validees:
        if d.type_document != "RL-1" or d.case != "211":
            continue
        cle = str(d.document)
        if cle in documents:
            raise ValueError("Case 211 dupliquée pour le même feuillet RL-1.")
        documents.add(cle)
        total += montant_medical_remboursable_quebec(d.valeur_validee, "case 211")
    return total


@dataclass(frozen=True)
class ResultatMedicalRemboursableQuebec2025:
    revenu_travail: Decimal = ZERO
    revenu_familial: Decimal = ZERO
    base_ligne_381: Decimal = ZERO
    credit_ligne_44: Decimal = ZERO
    reduction_ligne_48: Decimal = ZERO
    credit_ligne_462: Decimal = ZERO


def calculer_medical_remboursable_quebec_2025(p, *, salaire=ZERO, deduction_205=ZERO,
        deduction_207=ZERO, avantages_211=ZERO, revenu_net=ZERO, base_381=ZERO):
    valider_medical_remboursable_quebec_2025(p)
    for nom, v in (("101", salaire), ("205", deduction_205), ("207", deduction_207),
                   ("case 211", avantages_211), ("275", revenu_net), ("381", base_381)):
        montant_medical_remboursable_quebec(v, nom)
    if not p.reclamer:
        return ResultatMedicalRemboursableQuebec2025()
    if avantages_211 > salaire:
        raise ValueError("La case 211 ne peut dépasser le salaire de la ligne 101.")
    travail = max(salaire - deduction_205 - deduction_207 - avantages_211, ZERO)
    brut = min(arrondir_cent(base_381 * Decimal(".25")), Decimal(1466))
    reduction = arrondir_cent(max(revenu_net - Decimal(28335), ZERO) * Decimal(".05"))
    credit = max(brut - reduction, ZERO) if travail >= Decimal(3750) else ZERO
    return ResultatMedicalRemboursableQuebec2025(travail, revenu_net, base_381, brut, reduction, credit)


def medical_remboursable_quebec_vers_dict(p):
    valider_medical_remboursable_quebec_2025(p)
    return {f.name: getattr(p, f.name) for f in fields(p)}


def medical_remboursable_quebec_depuis_dict(v):
    if v is None:
        return MedicalRemboursableQuebec2025()
    if not isinstance(v, dict) or set(v) - {f.name for f in fields(MedicalRemboursableQuebec2025)}:
        raise ValueError("Profil médical remboursable Québec ou clés inconnues invalides.")
    return valider_medical_remboursable_quebec_2025(MedicalRemboursableQuebec2025(**v))


def lignes_medical_remboursable_quebec_2025(p, r):
    if not p.reclamer:
        return []
    return ["", "CRÉDIT MÉDICAL REMBOURSABLE QUÉBEC — ANNEXE B, PARTIE D",
        f"Naissance : {p.naissance}; source : {p.source}; validation comptable confirmée.",
        f"Revenu de travail = max(101 - 205 - 207 - case 211, 0) : {r.revenu_travail:.2f} $; minimum 3750.00 $",
        f"Revenu familial individuel = revenu net 275 : {r.revenu_familial:.2f} $",
        f"Base médicale ligne 381 après seuil de 3 % : {r.base_ligne_381:.2f} $; ligne 250 point 7 : 0.00 $",
        f"Ligne 44 = min(381 × 25 %, 1466) : {r.credit_ligne_44:.2f} $",
        f"Réduction ligne 48 = max(275 - 28335, 0) × 5 % : {r.reduction_ligne_48:.2f} $",
        f"Ligne 462 point 1 = max(44 - 48, 0) si travail >= 3750 : {r.credit_ligne_462:.2f} $",
        "Crédit remboursable ajouté une seule fois au rapprochement; crédit médical non remboursable conservé.",
        "Profil individuel salarié; situations familiales, autres revenus de travail et soutien 250 point 7 à intégrer séparément."]
