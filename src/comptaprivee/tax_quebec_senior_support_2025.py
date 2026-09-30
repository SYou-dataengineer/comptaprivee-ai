"""6J : soutien aux aînés 2025, ligne 463, profil individuel borné."""
from dataclasses import dataclass, fields
from datetime import date
from decimal import Decimal, localcontext
from textwrap import wrap

from .tax_rules_2025 import arrondir_cent

ZERO = Decimal(0)
CONFIRMATIONS_6J = {
    "residence_confirmee": "Résident du Canada toute l'année et du Québec fin 2025",
    "citoyennete_confirmee": "Citoyen canadien; statut admissible vérifié pour ce profil borné",
    "sans_famille_confirme": "Aucun conjoint ni personne à charge dans ce profil individuel borné",
    "absence_deces_confirmee": "Aucun décès en 2025",
    "absence_exoneration_confirmee": "Aucune exonération d'impôt excluant le crédit",
    "absence_detention_confirmee": "Aucune détention en 2025 dans ce profil borné",
    "absence_cas_particuliers_confirmee": "Aucune faillite, résidence partielle ou situation familiale particulière",
    "valide_par_comptable": "Admissibilité, sources et limites vérifiées par le comptable",
}


@dataclass(frozen=True)
class SoutienAinesQuebec2025:
    activer: bool = False
    naissance: str = ""
    source: str = ""
    residence_confirmee: bool = False
    citoyennete_confirmee: bool = False
    sans_famille_confirme: bool = False
    absence_deces_confirmee: bool = False
    absence_exoneration_confirmee: bool = False
    absence_detention_confirmee: bool = False
    absence_cas_particuliers_confirmee: bool = False
    valide_par_comptable: bool = False


def montant_soutien(v, nom):
    if (not isinstance(v, Decimal) or not v.is_finite()
            or not ZERO <= v <= Decimal("999999999.99") or v != arrondir_cent(v)):
        raise ValueError("Soutien aux aînés : Decimal non négatif au cent requis pour " + nom)
    return v


def valider_soutien_aines_quebec_2025(p):
    if not isinstance(p, SoutienAinesQuebec2025):
        raise ValueError("Profil soutien aux aînés invalide.")
    for f in fields(p):
        v = getattr(p, f.name)
        if type(v) is not type(f.default):
            raise ValueError("Type soutien aux aînés invalide : " + f.name)
        if isinstance(v, str) and (len(v) > 2000 or any(ord(c) < 32 for c in v)):
            raise ValueError("Texte soutien aux aînés invalide : " + f.name)
    if not p.activer:
        if p != SoutienAinesQuebec2025():
            raise ValueError("Activez le soutien aux aînés ou effacez explicitement les faits.")
        return p
    try:
        naissance = date.fromisoformat(p.naissance)
        if naissance.isoformat() != p.naissance:
            raise ValueError()
    except ValueError as erreur:
        raise ValueError("Naissance soutien aux aînés : AAAA-MM-JJ requis.") from erreur
    if naissance > date(1955, 12, 31):
        raise ValueError("Soutien aux aînés : 70 ans fin 2025 requis.")
    if not p.source.strip():
        raise ValueError("Source soutien aux aînés obligatoire.")
    for nom, libelle in CONFIRMATIONS_6J.items():
        if not getattr(p, nom):
            raise ValueError("Confirmation obligatoire : " + libelle)
    return p


@dataclass(frozen=True)
class ResultatSoutienAinesQuebec2025:
    revenu_familial_275: Decimal = ZERO
    reduction_exacte: Decimal = ZERO
    reduction_au_cent: Decimal = ZERO
    credit_ligne_463: Decimal = ZERO


def calculer_soutien_aines_quebec_2025(p, *, revenu_net_275):
    valider_soutien_aines_quebec_2025(p)
    if not p.activer:
        return ResultatSoutienAinesQuebec2025()
    montant_soutien(revenu_net_275, "275")
    with localcontext() as contexte:
        contexte.prec = 28
        exacte = max(revenu_net_275 - Decimal(27835), ZERO) * Decimal(".054")
        reduction = arrondir_cent(exacte)
        credit = max(Decimal(2000) - reduction, ZERO)
    return ResultatSoutienAinesQuebec2025(revenu_net_275, exacte, reduction, credit)


def soutien_aines_vers_dict(p):
    valider_soutien_aines_quebec_2025(p)
    return {f.name: getattr(p, f.name) for f in fields(p)}


def soutien_aines_depuis_dict(v):
    if v is None:
        return SoutienAinesQuebec2025()
    if not isinstance(v, dict) or set(v) - {f.name for f in fields(SoutienAinesQuebec2025)}:
        raise ValueError("Profil soutien aux aînés : JSON ou clés invalides.")
    return valider_soutien_aines_quebec_2025(SoutienAinesQuebec2025(**v))


def lignes_soutien_aines_quebec_2025(p, r):
    if not p.activer:
        return []
    return ["", "SOUTIEN AUX AÎNÉS QUÉBEC 2025 - LIGNE 463 (6J)",
        f"Naissance : {p.naissance}; profil individuel, admissibilité vérifiée par le comptable.",
        *wrap("Sources : " + p.source, width=50),
        f"Revenu familial = ligne Québec 275 recalculée : {r.revenu_familial_275:.2f} $.",
        "Maximum 2000.00 $; seuil de réduction 27835.00 $; taux 5,40 %.",
        f"Réduction exacte = max(275 - 27835, 0) x 0,054 : {r.reduction_exacte:f} $.",
        f"Réduction au cent : {r.reduction_au_cent:.2f} $; convention monétaire générale du moteur.",
        f"Ligne 463 = max(2000 - réduction, 0) : {r.credit_ligne_463:.2f} $.",
        "Crédit remboursable ajouté une seule fois; impôts de base et abattement fédéral inchangés.",
        "Revenu familial maximal publié pour une personne seule : 64873 $; extinction selon la formule.",
        "Limites logicielles : citoyen canadien, résidence annuelle, aucun conjoint ni personne à charge,",
        "aucun décès, exonération, détention, faillite ou résidence partielle.",
        "Source : Revenu Québec, crédit d'impôt pour soutien aux aînés, ligne 463, paramètres 2025."]
