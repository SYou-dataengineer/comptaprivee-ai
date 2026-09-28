"""Fournitures scolaires 2025 : LIR 122.9, RIR 9600, lignes 46800/46900."""
from dataclasses import asdict, dataclass, fields
from datetime import date
from decimal import Decimal, InvalidOperation

from .tax_rules_2025 import arrondir_cent

ZERO = Decimal("0")
CATEGORIES_FOURNITURES = (
    "consommables", "livres", "jeux et casse-têtes", "contenants", "logiciels éducatifs",
    "calculatrices", "stockage externe", "webcams microphones casques", "projecteurs",
    "pointeurs sans fil", "jouets éducatifs électroniques", "minuteries numériques",
    "haut-parleurs", "diffusion vidéo", "imprimantes", "ordinateurs et tablettes",
)
PROVINCES_EMPLOI = ("AB", "BC", "MB", "NB", "NL", "NS", "NT", "NU", "ON", "PE", "QC", "SK", "YT")
CONFIRMATIONS_EDUCATEUR = {
    "valide_par_comptable": "Dépenses, aides et pièces vérifiées par le comptable",
    "emploi_admissible": "Emploi au Canada en 2025 comme enseignant ou éducateur dans une école primaire/secondaire ou garderie réglementée",
    "qualification_valide": "Certificat, permis ou diplôme reconnu et valide dans la province ou le territoire de l'emploi",
    "usage_emploi": "Achats personnels pour enseigner ou faciliter l'apprentissage, directement utilisés dans cet emploi; usage personnel exclu",
    "aides_verifiees": "Aides reçues ou auxquelles l'éducateur a droit vérifiées; exception imposable et non déductible justifiée",
    "aucune_autre_deduction": "Montants réclamés ici jamais déduits du revenu ni de l'impôt fédéral de quiconque, notamment au T777",
    "profil_ordinaire": "Résidence au Canada toute l'année; déclaration ordinaire sans faillite ni déclaration spéciale de décès",
}


@dataclass(frozen=True)
class DepenseEducateur2025:
    date_paiement: str = ""
    description: str = ""
    categorie: str = ""
    montant: Decimal = ZERO
    aide: Decimal = ZERO
    aide_imposable_non_deductible: Decimal = ZERO
    source: str = ""


@dataclass(frozen=True)
class FournituresEducateur2025:
    depenses: tuple[DepenseEducateur2025, ...] = ()
    employeur: str = ""
    province_emploi: str = ""
    source_qualification: str = ""
    source: str = ""
    ordinateur_employeur_disponible: bool = False
    attestation_demandee: bool = False
    attestation_fournie: bool = False
    source_attestation: str = ""
    rapprochement_t777: str = ""
    valide_par_comptable: bool = False
    emploi_admissible: bool = False
    qualification_valide: bool = False
    usage_emploi: bool = False
    aides_verifiees: bool = False
    aucune_autre_deduction: bool = False
    profil_ordinaire: bool = False


@dataclass(frozen=True)
class ResultatFournituresEducateur2025:
    paiements: Decimal = ZERO
    aides_exclues: Decimal = ZERO
    depenses_admissibles: Decimal = ZERO
    ligne_46800: Decimal = ZERO
    ligne_46900: Decimal = ZERO
    attestation_manquante: bool = False


def montant_educateur_2025(v, nom):
    if not isinstance(v, Decimal) or not v.is_finite() or v < ZERO:
        raise ValueError(f"{nom} doit être un Decimal fini non négatif.")
    try:
        if v != arrondir_cent(v):
            raise ValueError(f"{nom} exige au plus deux décimales.")
    except ArithmeticError as erreur:
        raise ValueError(f"{nom} dépasse la capacité du calcul.") from erreur
    return v


def valider_depenses_educateur_2025(depenses):
    if type(depenses) is not tuple:
        raise ValueError("Les dépenses d'éducateur doivent former un tuple immuable.")
    sources = set()
    for d in depenses:
        if not isinstance(d, DepenseEducateur2025):
            raise ValueError("Dépense d'éducateur invalide.")
        for nom in ("date_paiement", "description", "categorie", "source"):
            if not isinstance(getattr(d, nom), str) or not getattr(d, nom).strip():
                raise ValueError("Champ de dépense obligatoire : " + nom)
        try:
            jour = date.fromisoformat(d.date_paiement)
            if jour.isoformat() != d.date_paiement or jour.year != 2025:
                raise ValueError()
        except ValueError as erreur:
            raise ValueError("Paiement en 2025 requis, date AAAA-MM-JJ.") from erreur
        if d.categorie not in CATEGORIES_FOURNITURES:
            raise ValueError("Catégorie non admissible aux fournitures scolaires.")
        for nom in ("montant", "aide", "aide_imposable_non_deductible"):
            montant_educateur_2025(getattr(d, nom), nom)
        if not ZERO < d.montant or not ZERO <= d.aide_imposable_non_deductible <= d.aide <= d.montant:
            raise ValueError("Paiement positif requis; aides et portion imposable ne peuvent dépasser leur assiette.")
        cle = " ".join(d.source.split()).casefold()
        if cle in sources:
            raise ValueError("La même dépense d'éducateur est réclamée deux fois.")
        sources.add(cle)


def calculer_fournitures_educateur_2025(p, *, annee=2025, deduction_t777=ZERO):
    if not isinstance(p, FournituresEducateur2025):
        raise ValueError("Profil éducateur invalide.")
    textes = ("employeur", "province_emploi", "source_qualification", "source", "source_attestation", "rapprochement_t777")
    for nom in textes:
        if not isinstance(getattr(p, nom), str):
            raise ValueError("Texte du profil éducateur invalide : " + nom)
    for nom in (*CONFIRMATIONS_EDUCATEUR, "ordinateur_employeur_disponible", "attestation_demandee", "attestation_fournie"):
        if type(getattr(p, nom)) is not bool:
            raise ValueError("Confirmation éducateur non booléenne : " + nom)
    valider_depenses_educateur_2025(p.depenses)
    montant_educateur_2025(deduction_t777, "Déduction T777")
    if not p.depenses:
        if any(getattr(p, n).strip() for n in textes) or p.attestation_demandee or p.attestation_fournie or p.ordinateur_employeur_disponible:
            raise ValueError("Le profil éducateur sans dépenses doit être vide.")
        return ResultatFournituresEducateur2025()
    if annee != 2025:
        raise ValueError("Le crédit éducateur exige l'année 2025.")
    for nom in CONFIRMATIONS_EDUCATEUR:
        if not getattr(p, nom):
            raise ValueError("Confirmation obligatoire : " + CONFIRMATIONS_EDUCATEUR[nom])
    if not all(getattr(p, n).strip() for n in ("employeur", "source", "source_qualification")) or p.province_emploi not in PROVINCES_EMPLOI:
        raise ValueError("Employeur, province canadienne, qualification et source obligatoires.")
    if p.ordinateur_employeur_disponible and any(d.categorie == "ordinateurs et tablettes" for d in p.depenses):
        raise ValueError("Ordinateur ou tablette fourni par l'employeur pour usage hors classe : achat informatique non admissible.")
    if p.attestation_fournie != bool(p.source_attestation.strip()):
        raise ValueError("La source de l'attestation doit correspondre à son statut fourni.")
    if deduction_t777 and not p.rapprochement_t777.strip():
        raise ValueError("T777 présent : source de rapprochement distinct des fournitures obligatoire pour éviter un double compte.")
    paiements = sum((d.montant for d in p.depenses), ZERO)
    aides = sum((d.aide - d.aide_imposable_non_deductible for d in p.depenses), ZERO)
    admissible = montant_educateur_2025(paiements - aides, "Dépenses nettes")
    manquante = p.attestation_demandee and not p.attestation_fournie
    base = ZERO if manquante else min(Decimal(1000), admissible)
    return ResultatFournituresEducateur2025(paiements, aides, admissible, base, arrondir_cent(base * Decimal("0.25")), manquante)


def educateur_vers_dict(p):
    brut = asdict(p)
    brut["depenses"] = [dict(asdict(d), **{n: format(getattr(d, n), ".2f") for n in
        ("montant", "aide", "aide_imposable_non_deductible")}) for d in p.depenses]
    return brut


def educateur_depuis_dict(valeur, *, annee=2025, deduction_t777=ZERO):
    def champs(v, classe):
        if not isinstance(v, dict) or set(v) - {f.name for f in fields(classe)}:
            raise ValueError("Champs éducateur enregistrés invalides.")
        return dict(v)
    brut = champs({} if valeur is None else valeur, FournituresEducateur2025)
    depenses = brut.get("depenses", [])
    if not isinstance(depenses, list):
        raise ValueError("Liste des dépenses d'éducateur invalide.")
    lignes = []
    for d in depenses:
        v = champs(d, DepenseEducateur2025)
        for nom in ("montant", "aide", "aide_imposable_non_deductible"):
            x = v.get(nom, "0")
            if not isinstance(x, (str, int)) or isinstance(x, bool):
                raise ValueError("Montant éducateur enregistré invalide.")
            try:
                v[nom] = montant_educateur_2025(Decimal(x), nom)
            except (ValueError, InvalidOperation) as erreur:
                raise ValueError("Montant éducateur enregistré invalide.") from erreur
        lignes.append(DepenseEducateur2025(**v))
    brut["depenses"] = tuple(lignes)
    p = FournituresEducateur2025(**brut)
    calculer_fournitures_educateur_2025(p, annee=annee, deduction_t777=deduction_t777)
    return p


def lignes_fournitures_educateur_2025(p, r):
    if not p.depenses:
        return []
    lignes = ["", "FOURNITURES SCOLAIRES D'ÉDUCATEUR — BLOC 5P",
        f"Employeur : {p.employeur} ({p.province_emploi}); qualification : {p.source_qualification}",
        f"Source : {p.source}; validation comptable confirmée"]
    for d in p.depenses:
        lignes.append(f"{d.date_paiement} — {d.description} ({d.categorie}) : {d.montant:.2f} $; "
            f"aide {d.aide:.2f} $ dont imposable non déductible {d.aide_imposable_non_deductible:.2f} $; source : {d.source}")
    lignes += [f"Dépenses nettes : {r.depenses_admissibles:.2f} $; aides exclues : {r.aides_exclues:.2f} $",
        f"Base plafonnée — 46800 : {r.ligne_46800:.2f} $; maximum 1000 $",
        f"Crédit remboursable — 46900 : {r.ligne_46900:.2f} $ = 25 % de 46800; maximum 250 $",
        "Sans réduction pour impôt insuffisant; revenu, 33500/34990 et abattement Québec inchangés."]
    if r.attestation_manquante:
        lignes.append("Attestation demandée par l'ARC non fournie : crédit nul selon 122.9(2)c).")
    if p.source_attestation:
        lignes.append("Attestation fournie : " + p.source_attestation)
    if p.rapprochement_t777:
        lignes.append("Absence de double déduction T777 rapprochée : " + p.rapprochement_t777)
    return lignes
