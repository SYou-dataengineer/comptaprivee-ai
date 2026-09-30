"""Annexe C 2025 : enfants propres, RL-24, famille stable, emploi ordinaire."""
from dataclasses import dataclass, fields
from datetime import date
from decimal import Decimal, InvalidOperation
from .tax_rules_2025 import arrondir_cent

ZERO = Decimal(0)
CATEGORIES_GARDE_QUEBEC = ("ordinaire", "infirmité", "déficience grave et prolongée")
TAUX_GARDE_QUEBEC = ((24795, "0.78"), (43725, "0.75"), (45340, "0.74"),
    (46970, "0.73"), (48570, "0.72"), (50195, "0.71"), (119835, "0.70"))
CONFIRMATIONS_6F = {
    "residence_confirmee": "Demandeur et conjoint résidents du Canada toute l'année et du Québec au 31 décembre 2025",
    "famille_stable_confirmee": "Situation conjugale stable; aucun décès, faillite, exonération spéciale ni garde partagée",
    "enfants_confirmes": "Enfants du demandeur ou du conjoint, vivant avec l'un d'eux lors des frais; identité et condition vérifiées, attestation Québec conforme si déficience",
    "emploi_confirme": "Demandeur ou conjoint en emploi lors des frais; conditions d'admissibilité vérifiées",
    "rl24_confirmes": "Frais payés par le demandeur ou le conjoint; cases E/identification RL-24 vérifiées; services 2025 au Canada par un prestataire résident",
    "exclusions_confirmees": "Aucun frais subventionné, médical, scolaire, personnel, versé à un parent de l'enfant ou au conjoint; aucun hébergement",
    "aucune_aide_confirmee": "Aucune allocation case 201 RL-1/J RL-5 ni autre aide ou remboursement à retrancher",
    "partage_confirme": "Parts convenues avec le conjoint vérifiées; aucun autre demandeur ni double utilisation des mêmes frais",
    "avances_confirmees": "Tous les versements anticipés personnels RL-19 case C vérifiés, y compris si supérieurs au crédit",
    "valide_par_comptable": "Faits, sources et périmètre validés par le comptable",
}


@dataclass(frozen=True)
class EnfantGardeQuebec2025:
    reference: str = ""
    nom: str = ""
    naissance: str = ""
    categorie: str = "ordinaire"
    frais_rl24_e: Decimal = ZERO
    source: str = ""


@dataclass(frozen=True)
class FraisGardeQuebec2025:
    reclamer: bool = False
    enfants: tuple[EnfantGardeQuebec2025, ...] = ()
    conjoint_nom: str = ""
    revenu_net_conjoint: Decimal = ZERO
    credit_demande_conjoint: Decimal = ZERO
    source_conjoint: str = ""
    avances_rl19_c: Decimal = ZERO
    source: str = ""
    residence_confirmee: bool = False
    famille_stable_confirmee: bool = False
    enfants_confirmes: bool = False
    emploi_confirme: bool = False
    rl24_confirmes: bool = False
    exclusions_confirmees: bool = False
    aucune_aide_confirmee: bool = False
    partage_confirme: bool = False
    avances_confirmees: bool = False
    valide_par_comptable: bool = False


def normaliser_garde(n):
    return " ".join(n.split()).casefold()


def montant_garde_quebec(v, nom="montant"):
    if (not isinstance(v, Decimal) or not v.is_finite() or not ZERO <= v <= Decimal("999999999.99")
            or v != arrondir_cent(v)):
        raise ValueError("Montant de garde Québec invalide : " + nom)
    return v


def montant_garde_depuis_champ(v):
    if not isinstance(v, str):
        raise ValueError("Montant de garde Québec : texte décimal requis.")
    try:
        return montant_garde_quebec(Decimal(v.strip().replace(" ", "").replace(",", ".") or "0"))
    except InvalidOperation as erreur:
        raise ValueError("Montant de garde Québec illisible.") from erreur


def valider_enfant_garde_quebec_2025(e):
    if not isinstance(e, EnfantGardeQuebec2025):
        raise ValueError("Fiche enfant garde Québec invalide.")
    for nom in ("reference", "nom", "naissance", "categorie", "source"):
        v = getattr(e, nom)
        if not isinstance(v, str) or not v.strip() or len(v) > 2000 or any(ord(c) < 32 for c in v):
            raise ValueError("Champ enfant garde Québec invalide : " + nom)
    montant_garde_quebec(e.frais_rl24_e, "case E RL-24")
    if e.categorie not in CATEGORIES_GARDE_QUEBEC:
        raise ValueError("Catégorie d'enfant garde Québec inconnue.")
    try:
        naissance = date.fromisoformat(e.naissance)
        if naissance.isoformat() != e.naissance or naissance > date(2025, 12, 31):
            raise ValueError()
    except ValueError as erreur:
        raise ValueError("Date de naissance de l'enfant invalide, AAAA-MM-JJ requis.") from erreur
    if e.categorie == "ordinaire" and naissance.year < 2009:
        raise ValueError("Enfant ordinaire hors du seuil d'âge de l'annexe C 2025.")
    return e


def valider_garde_quebec_2025(p):
    if not isinstance(p, FraisGardeQuebec2025) or type(p.enfants) is not tuple:
        raise ValueError("Profil ou liste d'enfants garde Québec invalide.")
    for f in fields(p):
        v = getattr(p, f.name)
        if isinstance(f.default, Decimal):
            montant_garde_quebec(v, f.name)
        elif f.name != "enfants" and type(v) is not type(f.default):
            raise ValueError("Type du profil garde Québec invalide : " + f.name)
        if isinstance(v, str) and (len(v) > 2000 or any(ord(c) < 32 for c in v)):
            raise ValueError("Texte du profil garde Québec invalide : " + f.name)
    if not p.reclamer:
        if any((p.enfants, p.conjoint_nom, p.revenu_net_conjoint, p.credit_demande_conjoint,
                p.source_conjoint, p.avances_rl19_c, p.source)):
            raise ValueError("Activez le profil garde Québec ou effacez les données.")
        return p
    if not p.source.strip():
        raise ValueError("Source du dossier et des avances garde Québec obligatoire.")
    if p.conjoint_nom:
        if not p.conjoint_nom.strip() or not p.source_conjoint.strip():
            raise ValueError("Identité et source du revenu/part du conjoint obligatoires.")
    elif any((p.revenu_net_conjoint, p.credit_demande_conjoint, p.source_conjoint)):
        raise ValueError("Données du conjoint présentes sans conjoint garde Québec.")
    references, identites = set(), set()
    for e in p.enfants:
        valider_enfant_garde_quebec_2025(e)
        ref, identite = normaliser_garde(e.reference), (normaliser_garde(e.nom), e.naissance)
        if ref in references or identite in identites:
            raise ValueError("Enfant garde Québec dupliqué : référence ou identité.")
        references.add(ref); identites.add(identite)
    for nom, libelle in CONFIRMATIONS_6F.items():
        if not getattr(p, nom):
            raise ValueError("Confirmation obligatoire : " + libelle)
    return p


@dataclass(frozen=True)
class ResultatGardeQuebec2025:
    frais_ligne_41: Decimal = ZERO
    plafond_ligne_50: Decimal = ZERO
    revenu_familial_ligne_80: Decimal = ZERO
    base_ligne_85: Decimal = ZERO
    taux_ligne_92: Decimal = ZERO
    credit_familial_ligne_94: Decimal = ZERO
    credit_ligne_455: Decimal = ZERO
    avances_ligne_441: Decimal = ZERO
    plafonds_enfants: tuple[Decimal, ...] = ()


def calculer_garde_quebec_2025(p, *, revenu_net=ZERO, demandeur=""):
    valider_garde_quebec_2025(p)
    montant_garde_quebec(revenu_net, "275 du demandeur")
    if not p.reclamer:
        return ResultatGardeQuebec2025()
    if demandeur and (normaliser_garde(p.conjoint_nom) == normaliser_garde(demandeur)
            or any(normaliser_garde(e.nom) == normaliser_garde(demandeur) for e in p.enfants)):
        raise ValueError("Le conjoint et les enfants doivent différer du demandeur.")
    plafonds = tuple(Decimal(16800) if e.categorie == "déficience grave et prolongée" else
        Decimal(12275) if int(e.naissance[:4]) >= 2019 else Decimal(6180) for e in p.enfants)
    frais = sum((e.frais_rl24_e for e in p.enfants), ZERO)
    plafond = sum(plafonds, ZERO)
    familial = revenu_net + p.revenu_net_conjoint
    taux = next((Decimal(t) for limite, t in TAUX_GARDE_QUEBEC if familial <= limite), Decimal(".67"))
    base = min(frais, plafond)
    credit = arrondir_cent(base * taux)
    if p.credit_demande_conjoint > credit:
        raise ValueError("La part du conjoint dépasse le crédit familial de garde Québec.")
    return ResultatGardeQuebec2025(frais, plafond, familial, base, taux, credit,
        credit - p.credit_demande_conjoint, p.avances_rl19_c, plafonds)


def verifier_garde_conjoint_2025(p, r, *, demandeur, revenu_net, conjoint):
    """Si un instantané 32600 existe, rapprocher ses entrées et son recalcul Québec."""
    autre = conjoint.garde_quebec_conjoint
    if p.reclamer:
        if (normaliser_garde(p.conjoint_nom) != normaliser_garde(conjoint.nom_conjoint)
                or p.revenu_net_conjoint != conjoint.revenu_net_quebec_conjoint):
            raise ValueError("Identité ou revenu Québec du conjoint divergent de son dossier recalculé.")
        if p.credit_demande_conjoint != conjoint.credit_garde_quebec_conjoint:
            raise ValueError("Part de garde Québec du conjoint divergente de son crédit recalculé.")
    if autre.reclamer:
        if (normaliser_garde(autre.conjoint_nom) != normaliser_garde(demandeur)
                or autre.revenu_net_conjoint != revenu_net):
            raise ValueError("Demandeur ou revenu Québec déclaré dans la garde du conjoint divergent.")
        if autre.credit_demande_conjoint != r.credit_ligne_455:
            raise ValueError("Part de garde attribuée au demandeur divergente de sa ligne 455.")
        if p.reclamer:
            def pool(profil):
                return sorted((normaliser_garde(e.nom), e.naissance, e.categorie, e.frais_rl24_e) for e in profil.enfants)
            if pool(p) != pool(autre):
                raise ValueError("Les deux annexes C doivent utiliser les mêmes enfants et frais familiaux.")


def garde_quebec_vers_dict(p):
    valider_garde_quebec_2025(p)
    def convertir(v):
        return str(v) if isinstance(v, Decimal) else v
    return {f.name: ([{c.name: convertir(getattr(e, c.name)) for c in fields(e)} for e in p.enfants]
        if f.name == "enfants" else convertir(getattr(p, f.name))) for f in fields(p)}


def garde_quebec_depuis_dict(v):
    if v is None:
        return FraisGardeQuebec2025()
    if not isinstance(v, dict) or set(v) - {f.name for f in fields(FraisGardeQuebec2025)}:
        raise ValueError("Profil garde Québec ou clés inconnues invalides.")
    valeurs = dict(v)
    for nom in ("revenu_net_conjoint", "credit_demande_conjoint", "avances_rl19_c"):
        if nom in valeurs:
            valeurs[nom] = montant_garde_depuis_champ(valeurs[nom])
    enfants = valeurs.get("enfants", [])
    if not isinstance(enfants, list):
        raise ValueError("Enfants garde Québec : liste JSON requise.")
    resultats = []
    for brut in enfants:
        if not isinstance(brut, dict) or set(brut) - {f.name for f in fields(EnfantGardeQuebec2025)}:
            raise ValueError("Fiche enfant garde Québec ou clés inconnues invalides.")
        e = dict(brut)
        if "frais_rl24_e" in e:
            e["frais_rl24_e"] = montant_garde_depuis_champ(e["frais_rl24_e"])
        resultats.append(EnfantGardeQuebec2025(**e))
    valeurs["enfants"] = tuple(resultats)
    return valider_garde_quebec_2025(FraisGardeQuebec2025(**valeurs))


def lignes_garde_quebec_2025(p, r):
    if not p.reclamer:
        return []
    lignes = ["", "FRAIS DE GARDE QUÉBEC — ANNEXE C / LIGNE 455",
        f"Source du dossier/RL-19 : {p.source}; validation comptable confirmée."]
    for e, plafond in zip(p.enfants, r.plafonds_enfants):
        lignes.extend([f"{e.reference} — {e.nom}, né(e) le {e.naissance}; {e.categorie}",
            f"RL-24 E : {e.frais_rl24_e:.2f} $; plafond enfant : {plafond:.2f} $; source : {e.source}"])
    lignes.extend([f"Frais admissibles 41 : {r.frais_ligne_41:.2f} $; allocations/aides exclues de ce profil",
        f"Plafond familial 50 = somme des plafonds enfants : {r.plafond_ligne_50:.2f} $",
        f"Revenu familial 80 = 275 du demandeur + 275 du conjoint : {r.revenu_familial_ligne_80:.2f} $",
        f"Conjoint : {p.conjoint_nom or 'aucun'}; revenu : {p.revenu_net_conjoint:.2f} $; source : {p.source_conjoint or 'sans objet'}",
        f"Base 85 = min(41, 50) : {r.base_ligne_85:.2f} $; taux 92 : {r.taux_ligne_92 * 100:.0f} %",
        f"Crédit familial 94 = 85 × taux : {r.credit_familial_ligne_94:.2f} $; part convenue du conjoint : {p.credit_demande_conjoint:.2f} $",
        f"Ligne 455 = 94 - part du conjoint : {r.credit_ligne_455:.2f} $; remboursable",
        f"Avances personnelles RL-19 C, ligne 441 : {r.avances_ligne_441:.2f} $; sans plafond au crédit",
        "Bouclier fiscal 460 non calculé : faits et revenus 2024 nécessaires; examen séparé requis, même si le crédit 455 est nul.",
        "Déduction fédérale distincte; aucun crédit de garde Québec ne réduit le revenu net.",
        "Famille stable, enfants propres, emploi, RL-24 sans hébergement; autres situations à intégrer séparément."])
    return lignes
