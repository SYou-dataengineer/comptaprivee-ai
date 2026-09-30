"""6I : prime au travail individuelle, annexe P 2025.

Sources déjà auditées : TP-1.D.P (2025-12), parties A/C/E et guide ligne 456.
Les produits exacts sont conservés; les lignes monétaires sont représentées
au cent selon la convention générale du moteur, non une règle RQ spécifique.
"""
from dataclasses import dataclass, fields
from datetime import date
from decimal import Decimal, InvalidOperation, localcontext
from textwrap import wrap

from .tax_rules_2025 import arrondir_cent

ZERO = Decimal(0)
NOTE_ARRONDI_6I = (
    "Aucune règle d'arrondi spécifique aux lignes 76/83 n'a été trouvée dans "
    "les sources officielles 2025 consultées; le moteur utilise sa convention "
    "monétaire générale au cent, sans présenter celle-ci comme une règle fiscale "
    "particulière de l'annexe P."
)


CONFIRMATIONS_6I = {
    "residence_confirmee": "Résidence au Canada toute l'année et au Québec fin 2025",
    "citoyennete_confirmee": "Citoyenneté canadienne vérifiée pour ce profil borné",
    "sans_conjoint_confirme": "Aucun conjoint en 2025 dans ce profil borné",
    "sans_enfant_confirme": "Aucun enfant à charge ou désigné",
    "emploi_101_confirme": "Travail limité à 101, avec case 211 vérifiée; aucune autre composante de P",
    "absence_293_confirmee": "Aucun revenu de travail donnant droit à la déduction 293",
    "non_etudiant_confirme": "Non étudiant à temps plein selon la définition Québec de la ligne 456",
    "absence_transfert_s_confirmee": "Aucun transfert aux parents aux lignes 20.1/20.2 de l'annexe S",
    "non_designe_confirme": "Demandeur non désigné comme enfant dans une autre annexe P",
    "absence_allocation_confirmee": "Aucune Allocation famille reçue pour le demandeur dans ce profil",
    "absence_detention_confirmee": "Aucune détention en 2025 dans ce profil borné",
    "absence_cas_particuliers_confirmee": "Aucun décès, faillite ou résidence partielle",
    "absence_supplement_confirmee": "Absence de droit au supplément de transition et de RL-5 V",
    "statut_adaptee_verifie": "Droit 376 et historique des prestations 2020-2025 vérifiés",
    "avances_exhaustives_confirmees": "Avances RL-19 A exhaustives ou absence vérifiée; case B absente",
    "valide_par_comptable": "Faits, justificatifs et limites vérifiés par le comptable",
}


@dataclass(frozen=True)
class PrimeTravailQuebec2025:
    activer: bool = False
    naissance: str = ""
    source: str = ""
    droit_376_confirme: bool = False
    prestations_contraintes_2020_2025_confirmees: bool = False
    avances_rl19_a: Decimal = Decimal(0)
    residence_confirmee: bool = False
    citoyennete_confirmee: bool = False
    sans_conjoint_confirme: bool = False
    sans_enfant_confirme: bool = False
    emploi_101_confirme: bool = False
    absence_293_confirmee: bool = False
    non_etudiant_confirme: bool = False
    absence_transfert_s_confirmee: bool = False
    non_designe_confirme: bool = False
    absence_allocation_confirmee: bool = False
    absence_detention_confirmee: bool = False
    absence_cas_particuliers_confirmee: bool = False
    absence_supplement_confirmee: bool = False
    statut_adaptee_verifie: bool = False
    avances_exhaustives_confirmees: bool = False
    valide_par_comptable: bool = False


def montant_prime_travail(v: Decimal, nom: str) -> Decimal:
    if (not isinstance(v, Decimal) or not v.is_finite()
            or not Decimal(0) <= v <= Decimal("999999999.99") or v != arrondir_cent(v)):
        raise ValueError("Prime au travail : Decimal non négatif au cent requis pour " + nom)
    return v


def valider_prime_travail_quebec_2025(p: PrimeTravailQuebec2025) -> PrimeTravailQuebec2025:
    if not isinstance(p, PrimeTravailQuebec2025):
        raise ValueError("Profil prime au travail invalide.")
    for f in fields(p):
        v = getattr(p, f.name)
        if type(v) is not type(f.default):
            raise ValueError("Type prime au travail invalide : " + f.name)
        if isinstance(v, str) and (len(v) > 2000 or any(ord(c) < 32 for c in v)):
            raise ValueError("Texte prime au travail invalide : " + f.name)
    montant_prime_travail(p.avances_rl19_a, "RL-19 A")
    if not p.activer:
        if p != PrimeTravailQuebec2025():
            raise ValueError("Activez le profil prime au travail ou effacez explicitement ses faits et avances.")
        return p
    try:
        naissance = date.fromisoformat(p.naissance)
        if naissance.isoformat() != p.naissance:
            raise ValueError()
    except ValueError as erreur:
        raise ValueError("Naissance prime au travail : AAAA-MM-JJ requis.") from erreur
    if naissance > date(2007, 12, 31):
        raise ValueError("Le profil prime au travail exige 18 ans fin 2025.")
    if not p.source.strip():
        raise ValueError("Source prime au travail obligatoire.")
    for nom, libelle in CONFIRMATIONS_6I.items():
        if not getattr(p, nom):
            raise ValueError("Confirmation obligatoire : " + libelle)
    return p


@dataclass(frozen=True)
class BasePrimeTravailQuebec2025:
    revenu_travail_ligne_29: Decimal
    revenu_familial_ligne_54: Decimal
    comparer_colonne_adaptee: bool
    avances_rl19_a: Decimal


def preparer_prime_travail_quebec_2025(
    p: PrimeTravailQuebec2025, *, salaire_101: Decimal,
    avantages_211: Decimal, revenu_net_275: Decimal,
) -> BasePrimeTravailQuebec2025 | None:
    """Les entrées doivent provenir du dossier recalculé; pas de revenu manuel.

    Aucun arrondi de calcul fiscal ici : seulement contrôle de précision des
    entrées et soustraction exacte. La prime adaptée nécessite les deux colonnes.
    """
    valider_prime_travail_quebec_2025(p)
    if not p.activer:
        return None
    for nom, v in (("101", salaire_101), ("211", avantages_211), ("275", revenu_net_275)):
        montant_prime_travail(v, nom)
    if avantages_211 > salaire_101:
        raise ValueError("La case 211 ne peut dépasser la ligne 101.")
    return BasePrimeTravailQuebec2025(
        salaire_101 - avantages_211, revenu_net_275,
        p.droit_376_confirme or p.prestations_contraintes_2020_2025_confirmees,
        p.avances_rl19_a,
    )


@dataclass(frozen=True)
class ColonnePrimeTravail2025:
    plafond: Decimal
    exclusion: Decimal
    taux: Decimal
    maximum_revenu: Decimal
    ligne_68: Decimal
    ligne_72: Decimal
    produit_76_exact: Decimal
    ligne_76: Decimal
    ligne_82: Decimal
    produit_83_exact: Decimal
    ligne_83: Decimal
    ligne_84: Decimal
    seuils_respectes: bool


@dataclass(frozen=True)
class ResultatPrimeTravailQuebec2025:
    base: BasePrimeTravailQuebec2025 | None = None
    ordinaire: ColonnePrimeTravail2025 | None = None
    adaptee: ColonnePrimeTravail2025 | None = None
    credit_ligne_456: Decimal = ZERO
    avances_ligne_441: Decimal = ZERO


def _colonne(base, plafond, exclusion, taux, maximum_revenu):
    # Précision indépendante du contexte Decimal de l'appelant.
    with localcontext() as contexte:
        contexte.prec = 28
        l68 = min(base.revenu_travail_ligne_29, plafond)
        l72 = max(l68 - exclusion, ZERO)
        exact76 = l72 * taux
        l76 = arrondir_cent(exact76)
        l82 = max(base.revenu_familial_ligne_54 - plafond, ZERO)
        exact83 = l82 * Decimal("0.10")
        l83 = arrondir_cent(exact83)
        admissible = base.revenu_travail_ligne_29 > exclusion and base.revenu_familial_ligne_54 < maximum_revenu
        l84 = max(l76 - l83, ZERO) if admissible else ZERO
    return ColonnePrimeTravail2025(plafond, exclusion, taux, maximum_revenu,
        l68, l72, exact76, l76, l82, exact83, l83, l84, admissible)


def calculer_prime_travail_quebec_2025(p, *, salaire_101, avantages_211, revenu_net_275):
    base = preparer_prime_travail_quebec_2025(p, salaire_101=salaire_101,
        avantages_211=avantages_211, revenu_net_275=revenu_net_275)
    if base is None:
        return ResultatPrimeTravailQuebec2025()
    ordinaire = _colonne(base, Decimal(12620), Decimal(2400), Decimal(".116"), Decimal(24475))
    adaptee = (_colonne(base, Decimal(17798), Decimal(1200), Decimal(".136"), Decimal(40371))
        if base.comparer_colonne_adaptee else None)
    credit = max(ordinaire.ligne_84, adaptee.ligne_84 if adaptee else ZERO)
    return ResultatPrimeTravailQuebec2025(base, ordinaire, adaptee, credit, p.avances_rl19_a)


def prime_travail_vers_dict(p):
    valider_prime_travail_quebec_2025(p)
    return {f.name: str(getattr(p, f.name)) if isinstance(getattr(p, f.name), Decimal)
        else getattr(p, f.name) for f in fields(p)}


def prime_travail_depuis_dict(v):
    if v is None:
        return PrimeTravailQuebec2025()
    if not isinstance(v, dict) or set(v) - {f.name for f in fields(PrimeTravailQuebec2025)}:
        raise ValueError("Profil prime au travail : objet JSON ou clés invalides.")
    valeurs = dict(v)
    if "avances_rl19_a" in valeurs:
        brut = valeurs["avances_rl19_a"]
        if not isinstance(brut, str) or len(brut) > 40:
            raise ValueError("Avances prime au travail : chaîne décimale requise.")
        try:
            valeurs["avances_rl19_a"] = Decimal(brut)
        except InvalidOperation as erreur:
            raise ValueError("Avances prime au travail invalides.") from erreur
    return valider_prime_travail_quebec_2025(PrimeTravailQuebec2025(**valeurs))


def montant_prime_depuis_champ(texte):
    try:
        v = Decimal(texte.replace(" ", "").replace("\u00a0", "").replace(",", ".").replace("$", "") or "0")
    except (InvalidOperation, AttributeError) as erreur:
        raise ValueError("Avances prime au travail invalides.") from erreur
    return montant_prime_travail(v, "RL-19 A")


def lignes_prime_travail_quebec_2025(p, r):
    if not p.activer:
        return []
    lignes = ["", "PRIME AU TRAVAIL QUÉBEC 2025 - ANNEXE P (6I)",
        f"Naissance : {p.naissance}; profil adulte, sans conjoint ni enfant; validation comptable confirmée.",
        *wrap("Sources : " + p.source, width=50),
        f"P 29 = 101 - case 211 : {r.base.revenu_travail_ligne_29:.2f} $",
        f"P 54 = revenu familial, ligne Québec 275 recalculée : {r.base.revenu_familial_ligne_54:.2f} $",
        f"Droit 376 confirmé : {'oui' if p.droit_376_confirme else 'non'}; prestations admissibles 2020-2025 : "
        + ("oui" if p.prestations_contraintes_2020_2025_confirmees else "non")]
    for nom, c in (("Ordinaire", r.ordinaire), ("Adaptée", r.adaptee)):
        if c is None:
            continue
        lignes.extend([f"{nom} : plafond 66/80 = {c.plafond:.2f}; exclusion 70 = {c.exclusion:.2f}; taux = {c.taux * 100}%.",
            f"68 = min(29, 66) : {c.ligne_68:.2f}; 72 = max(68 - 70, 0) : {c.ligne_72:.2f}.",
            f"76 : produit exact {c.produit_76_exact:f}; montant au cent {c.ligne_76:.2f} $.",
            f"82 = max(54 - 80, 0) : {c.ligne_82:.2f}; réduction 83 au taux de 10 %.",
            f"83 : produit exact {c.produit_83_exact:f}; montant au cent {c.ligne_83:.2f} $.",
            f"Travail > {c.exclusion:.2f} et revenu familial < {c.maximum_revenu:.2f} : "
            + ("oui" if c.seuils_respectes else "non; crédit nul"),
            f"84 = max(76 - 83, 0), sous réserve des seuils : {c.ligne_84:.2f} $."])
    lignes.extend([f"87/89/90 : montant retenu (maximum des colonnes admissibles), ligne 456 : {r.credit_ligne_456:.2f} $.",
        f"Avances RL-19 A intégrales, ligne 441 : {r.avances_ligne_441:.2f} $; distinctes de C/H et du RC210.",
        "Crédit ajouté une seule fois; avances comptées séparément, même supérieures au crédit.",
        NOTE_ARRONDI_6I,
        "Convention : produits exacts conservés; arrondir_cent (ROUND_HALF_UP) aux lignes 76 et 83 avant soustraction.",
        "Supplément de transition exclu; RL-5 V/RL-19 B et situations familiales hors profil.",
        "Bouclier fiscal 460 non calculé : examen séparé requis, même si la prime est nulle.",
        "Source : RQ TP-1.D.P (2025-12), pages 1-2; guide 2025, ligne 456."])
    return lignes
