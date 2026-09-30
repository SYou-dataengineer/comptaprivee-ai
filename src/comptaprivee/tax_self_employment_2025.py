"""7B : faits et revenu autonome simple, sans finalisation fiscale avant 7C.

T2125 F (25), p. 3; T4002 2025, p. 49; TP-80 (2025-10), p. 3.
"""
from dataclasses import dataclass, fields
from datetime import date
from decimal import Decimal, InvalidOperation

ZERO = Decimal("0")
CONFIRMATIONS_7B = {
    "proprietaire_unique": "Propriétaire unique, sans associé",
    "services_quebec": "Services ordinaires au Québec seulement; aucun revenu étranger ni établissement hors Québec",
    "comptabilite_exercice": "Comptabilité d'exercice; revenus gagnés et dépenses engagées pour cet exercice",
    "sans_taxes": "Aucune TPS/TVQ/TVH collectée, récupérable ou à régulariser",
    "sans_cas_complexe": "Sans stocks, agriculture/pêche, DPA, véhicule, domicile, réserves, subvention, changement de fin d'exercice ou cessation",
    "depenses_admissibles": "Dépenses courantes entièrement professionnelles et admissibles dans les deux déclarations; sans prorata, remboursement ni immobilisation",
    "sans_double_compte": "Sources exhaustives, aucun revenu ou dépense déjà compté ailleurs ou dans une autre entreprise",
    "sans_deces_faillite": "Aucun décès ni faillite",
    "valide_par_comptable": "Faits et pièces justificatives vérifiés par le comptable",
}
MESSAGE_7C = ("7B : revenus autonomes préparés, mais estimation finale bloquée. "
    "RRQ/RQAP autonomes, déductions associées et crédits dépendants nécessitent 7C "
    "ou un sous-bloc ultérieur. Aucun impôt, remboursement ou solde annuel calculé.")


@dataclass(frozen=True)
class Entreprise2025:
    reference: str = ""
    nature: str = "entreprise"
    debut: str = "2025-01-01"
    fin: str = "2025-12-31"
    revenu_brut: Decimal = ZERO
    frais_bureau: Decimal = ZERO
    frais_comptables: Decimal = ZERO
    source: str = ""
    proprietaire_unique: bool = False
    services_quebec: bool = False
    comptabilite_exercice: bool = False
    sans_taxes: bool = False
    sans_cas_complexe: bool = False
    depenses_admissibles: bool = False
    sans_double_compte: bool = False
    sans_deces_faillite: bool = False
    valide_par_comptable: bool = False


@dataclass(frozen=True)
class ResultatEntreprise2025:
    faits: Entreprise2025
    depenses: Decimal
    revenu_net: Decimal


def calculer_entreprises_2025(entreprises: tuple[Entreprise2025, ...]) -> tuple[ResultatEntreprise2025, ...]:
    if not isinstance(entreprises, tuple):
        raise ValueError("7B : liste immuable d'entreprises requise.")
    references = set()
    resultats = []
    for e in entreprises:
        if not isinstance(e, Entreprise2025):
            raise ValueError("7B : fiche entreprise invalide.")
        for nom in ("reference", "source", "nature", "debut", "fin"):
            if not isinstance(getattr(e, nom), str) or not getattr(e, nom).strip():
                raise ValueError("7B : champ obligatoire invalide : " + nom)
        cle = " ".join(e.reference.split()).casefold()
        if cle in references:
            raise ValueError("7B : doublon d'entreprise.")
        references.add(cle)
        if e.nature not in {"entreprise", "profession"}:
            raise ValueError("7B : nature hors périmètre.")
        try:
            debut, fin = date.fromisoformat(e.debut), date.fromisoformat(e.fin)
        except ValueError as exc:
            raise ValueError("7B : dates ISO invalides.") from exc
        if (debut.isoformat() != e.debut or fin.isoformat() != e.fin
                or debut.year != 2025 or fin != date(2025, 12, 31) or debut > fin):
            raise ValueError("7B : exercice commençant en 2025 et terminé le 31 décembre 2025 requis.")
        for nom in ("revenu_brut", "frais_bureau", "frais_comptables"):
            v = getattr(e, nom)
            if (not isinstance(v, Decimal) or not v.is_finite() or v < ZERO
                    or v > Decimal("999999999.99") or v != v.quantize(Decimal(".01"))):
                raise ValueError("7B : montant Decimal fini, positif ou nul, au cent requis : " + nom)
        for nom, texte in CONFIRMATIONS_7B.items():
            if getattr(e, nom) is not True:
                raise ValueError("7B : confirmation obligatoire : " + texte)
        depenses = e.frais_bureau + e.frais_comptables
        net = e.revenu_brut - depenses
        if net < ZERO:
            raise ValueError("7B : perte hors périmètre; traitement des pertes à vérifier dans un sous-bloc ultérieur.")
        resultats.append(ResultatEntreprise2025(e, depenses, net))
    return tuple(resultats)


def entreprises_vers_json(entreprises):
    calculer_entreprises_2025(entreprises)
    return [{f.name: str(getattr(e, f.name)) if isinstance(getattr(e, f.name), Decimal)
             else getattr(e, f.name) for f in fields(e)} for e in entreprises]


def entreprises_depuis_json(valeur):
    if valeur is None:
        return ()
    if not isinstance(valeur, list):
        raise ValueError("7B : liste JSON d'entreprises invalide.")
    entreprises = []
    for brut in valeur:
        if not isinstance(brut, dict) or set(brut) - {f.name for f in fields(Entreprise2025)}:
            raise ValueError("7B : fiche JSON invalide ou champs non pris en charge.")
        donnees = dict(brut)
        for nom in ("revenu_brut", "frais_bureau", "frais_comptables"):
            v = donnees.get(nom, "0")
            if not isinstance(v, str):
                raise ValueError("7B : montants JSON exprimés en chaînes décimales requis.")
            try:
                donnees[nom] = Decimal(v)
            except InvalidOperation as exc:
                raise ValueError("7B : montant JSON invalide.") from exc
        entreprises.append(Entreprise2025(**donnees))
    resultat = tuple(entreprises)
    calculer_entreprises_2025(resultat)
    return resultat


@dataclass(frozen=True)
class PreparationAutonome2025:
    client: str
    entreprises: tuple[ResultatEntreprise2025, ...]
    revenu_total_federal: Decimal
    revenu_total_quebec: Decimal
    revenu_net_federal_avant_7c: Decimal
    revenu_275_avant_7c: Decimal
    salaire_federal: Decimal
    salaire_quebec: Decimal


def preparer_revenus_autonomes_2025(dossier, entreprises) -> PreparationAutonome2025:
    """Préparation emploi + entreprises seulement, avant déductions personnelles/7C.

    Aucune cotisation salariale présumée définitive : le profil mixte de 7C
    devra relire les cotisations réelles et les formulaires complets.
    """
    from .tax_engine_input_2025 import consolider_base_fiscale_emploi_2025
    from .tax_rules_2025 import deduction_travailleur_quebec_2025
    if entreprises != dossier.entreprises:
        raise ValueError("7B : les entreprises doivent correspondre aux faits du dossier.")
    r = calculer_entreprises_2025(entreprises)
    if not r:
        raise ValueError("7B : aucune entreprise à préparer.")
    if dossier.annee_fiscale != 2025 or dossier.province.casefold() not in {"québec", "quebec"}:
        raise ValueError("7B : dossier Québec 2025 requis.")
    fed = qc = ZERO
    if dossier.donnees_validees:
        if any(d.type_document not in {"T4", "RL-1"} for d in dossier.donnees_validees):
            raise ValueError("7B : combinaison avec revenus autres que salaire hors périmètre.")
        base = consolider_base_fiscale_emploi_2025(dossier)
        # Les avantages d'ancien emploi et les revenus exonérés ont une autre base 201.
        permis = {"T4": {"14", "17", "17A", "18", "22", "24", "26", "55", "56"},
                  "RL-1": {"A", "B.A", "B.B", "C", "E", "G", "H", "I"}}
        if any(d.case not in permis[d.type_document] and d.valeur_validee
               for d in dossier.donnees_validees):
            raise ValueError("7B : préparation combinée limitée au salaire ordinaire sans autres ajustements.")
        fed, qc = base.revenu_emploi_federal, base.revenu_emploi_quebec
    net = sum((x.revenu_net for x in r), ZERO)
    return PreparationAutonome2025(dossier.client, r, fed + net, qc + net,
        fed + net, qc + net - deduction_travailleur_quebec_2025(qc + net), fed, qc)


def lignes_preparation_autonome_2025(p):
    lignes = ["PRÉPARATION DES REVENUS AUTONOMES 2025 - 7B", f"Client : {p.client}",
        MESSAGE_7C, "Périmètre de cet état : salaires ordinaires et entreprises ci-dessous uniquement.",
        "Les autres profils, crédits et déductions personnels du dossier ne sont pas intégrés à cet état.",
        "Les revenus nets provisoires précèdent TOUTES les déductions RRQ/RQAP (emploi et autonome).",
        "Ne pas reporter les revenus nets provisoires dans une déclaration finale."]
    for r in p.entreprises:
        e = r.faits
        lignes += ["", f"Entreprise : {e.reference} ({e.nature})", f"Exercice : {e.debut} au {e.fin}",
            f"Source : {e.source}", f"Revenu brut : {e.revenu_brut:.2f} $",
            f"Petits frais de bureau (T2125 8810 / TP-80 222) : {e.frais_bureau:.2f} $",
            f"Tenue comptable courante (8860 / 228) : {e.frais_comptables:.2f} $",
            f"Dépenses : {r.depenses:.2f} $; net = brut - dépenses : {r.revenu_net:.2f} $",
            f"Revenu net fédéral {'13500' if e.nature == 'entreprise' else '13700'} : {r.revenu_net:.2f} $",
            f"Revenu net Québec annexe L / ligne 164 : {r.revenu_net:.2f} $"]
        lignes += ["Confirmations comptables : " + texte + " : oui"
                   for texte in CONFIRMATIONS_7B.values()]
    lignes += ["", f"Salaires fédéral / Québec : {p.salaire_federal:.2f} $ / {p.salaire_quebec:.2f} $",
        f"Revenu total fédéral préparé : {p.revenu_total_federal:.2f} $",
        f"Revenu total Québec préparé : {p.revenu_total_quebec:.2f} $",
        f"Revenu net fédéral AVANT cotisations et déductions personnelles : {p.revenu_net_federal_avant_7c:.2f} $",
        f"Base provisoire Québec 275 AVANT cotisations et déductions personnelles : {p.revenu_275_avant_7c:.2f} $",
        "Déduction travailleur 201 appliquée une fois à emploi + revenu net autonome admissible.",
        "Crédits liés au revenu, dont prime au travail et ACT : non calculés dans cette préparation.",
        "Sources : T4002 2025 p. 49; T2125 F (25) p. 3; TP-80 (2025-10) p. 3; RQ lignes 164/201.",
        "Aucune déclaration produite ou transmise. Validation comptable obligatoire."]
    return tuple(lignes)
