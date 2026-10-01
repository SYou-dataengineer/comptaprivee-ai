"""7E : catégorie 1 régulière existante, sans mouvement ni régime accéléré.

Les soldes et choix fédéral/Québec sont indépendants. Arrondi au cent suivant
la convention monétaire générale du moteur, sans règle fiscale inventée.
"""
from dataclasses import dataclass, fields
from datetime import date
from decimal import Decimal, InvalidOperation
from .tax_rules_2025 import arrondir_cent

ZERO = Decimal('0')
TAUX = Decimal('.04')
SOURCE_FEDERALE = 'https://www.canada.ca/fr/agence-revenu/services/formulaires-publications/publications/t4036/revenus-location.html'
SOURCE_QUEBEC = 'https://www.revenuquebec.ca/fr/services-en-ligne/formulaires-et-publications/tpw-130-g/guide-relatif-a-la-deduction-pour-amortissement/'
MONTANTS_7E = ('fnacc_federale', 'pnacc_quebec', 'dpa_federale', 'dpa_quebec', 'additions_2025', 'taux')
CONFIRMATIONS_7E = {
    'categorie_reguliere': 'Une seule catégorie 1 régulière à 4 %, bâtiment résidentiel, aucun régime accéléré/RII ni passation immédiate',
    'terrain_exclu': 'Terrain intégralement exclu des soldes amortissables',
    'soldes_valides': 'FNACC fédérale et PNACC Québec vérifiées séparément au 1er janvier 2025, sources et écarts documentés',
    'sans_mouvement': 'Aucune acquisition, addition, disposition, récupération, perte finale, aide ou autre rajustement en 2025',
    'usage_inchange': 'Bien disponible avant 2025, toujours détenu fin 2025; aucun changement d’usage',
    'choix_valides': 'DPA choisies séparément par le contribuable et validées par le comptable',
}


@dataclass(frozen=True)
class DpaLocation2025:
    categorie: str = '1'
    taux: Decimal = TAUX
    fnacc_federale: Decimal = ZERO
    pnacc_quebec: Decimal = ZERO
    dpa_federale: Decimal = ZERO
    dpa_quebec: Decimal = ZERO
    additions_2025: Decimal = ZERO
    acquisition: str = ''
    mise_service: str = ''
    source: str = ''
    source_federale: str = SOURCE_FEDERALE
    source_quebec: str = SOURCE_QUEBEC
    disposition: bool = False
    recuperation: bool = False
    perte_finale: bool = False
    accelere: bool = False
    categorie_reguliere: bool = False
    terrain_exclu: bool = False
    soldes_valides: bool = False
    sans_mouvement: bool = False
    usage_inchange: bool = False
    choix_valides: bool = False


def _montant(v, nom):
    if (not isinstance(v, Decimal) or not v.is_finite() or v < ZERO
            or v > Decimal('999999999.99') or v != v.quantize(Decimal('.01'))):
        raise ValueError('7E : montant Decimal fini non négatif au cent requis : ' + nom)


def valider_dpa_location_2025(p):
    if not isinstance(p, DpaLocation2025):
        raise ValueError('7E : profil DPA unique invalide.')
    for n in MONTANTS_7E:
        _montant(getattr(p,n), n)
    if p.categorie != '1' or p.taux != TAUX:
        raise ValueError('7E : catégorie 1 régulière et taux 4 % uniquement.')
    if p.additions_2025:
        raise ValueError('7E : aucune acquisition/addition 2025 supportée.')
    for n in ('disposition', 'recuperation', 'perte_finale', 'accelere'):
        if type(getattr(p,n)) is not bool or getattr(p,n):
            raise ValueError('7E : hors périmètre : ' + n)
    for n, texte in CONFIRMATIONS_7E.items():
        if getattr(p,n) is not True:
            raise ValueError('7E : confirmation obligatoire : ' + texte)
    dates = []
    for n in ('acquisition', 'mise_service'):
        v = getattr(p,n)
        try:
            d = date.fromisoformat(v)
        except (ValueError, TypeError) as exc:
            raise ValueError('7E : date ISO obligatoire : ' + n) from exc
        if d.isoformat() != v or not date(1900,1,1) <= d < date(2025,1,1):
            raise ValueError('7E : acquisition et disponibilité avant 2025 requises.')
        dates.append(d)
    if dates[1] < dates[0]:
        raise ValueError('7E : disponibilité pour le propriétaire antérieure à son acquisition.')
    if not isinstance(p.source,str) or not p.source.strip():
        raise ValueError('7E : source des soldes et choix obligatoire.')
    if p.source_federale != SOURCE_FEDERALE or p.source_quebec != SOURCE_QUEBEC:
        raise ValueError('7E : références officielles du profil non reconnues.')
    return p


@dataclass(frozen=True)
class DpaJuridiction2025:
    ouverture: Decimal
    maximum_theorique: Decimal
    maximum_admissible: Decimal
    choisie: Decimal
    fermeture: Decimal
    revenu_avant: Decimal
    revenu_apres: Decimal


@dataclass(frozen=True)
class ResultatDpaLocation2025:
    federal: DpaJuridiction2025
    quebec: DpaJuridiction2025


def calculer_dpa_location_2025(p, revenu_avant):
    valider_dpa_location_2025(p)
    _montant(revenu_avant, 'revenu avant DPA')
    def calcul(solde, choix, juridiction):
        maximum = arrondir_cent(solde * TAUX)
        admissible = min(maximum, revenu_avant)
        if choix > maximum:
            raise ValueError('7E : DPA ' + juridiction + ' supérieure au maximum de la catégorie.')
        if choix > revenu_avant:
            raise ValueError('7E : DPA ' + juridiction + ' créerait une perte locative.')
        return DpaJuridiction2025(solde, maximum, admissible, choix,
                                  solde - choix, revenu_avant, revenu_avant - choix)
    return ResultatDpaLocation2025(calcul(p.fnacc_federale,p.dpa_federale,'fédérale'),
                                   calcul(p.pnacc_quebec,p.dpa_quebec,'Québec'))


def dpa_location_vers_json(p):
    if p is None:
        return None
    valider_dpa_location_2025(p)
    return {f.name:str(getattr(p,f.name)) if f.name in MONTANTS_7E else getattr(p,f.name) for f in fields(p)}


def dpa_location_depuis_json(v):
    if v is None:
        return None
    if not isinstance(v,dict) or set(v) - {f.name for f in fields(DpaLocation2025)}:
        raise ValueError('7E : profil JSON ou champs non supportés.')
    d = dict(v)
    for n in MONTANTS_7E:
        if n not in d:
            raise ValueError('7E : montant JSON obligatoire manquant : ' + n)
        valeur = d[n]
        if not isinstance(valeur,str):
            raise ValueError('7E : montants JSON en chaînes décimales requis.')
        try:
            d[n] = Decimal(valeur)
        except InvalidOperation as exc:
            raise ValueError('7E : montant JSON invalide.') from exc
    return valider_dpa_location_2025(DpaLocation2025(**d))


def lignes_dpa_location_2025(p, resultat):
    lignes = ['', 'DPA LOCATION 2025 - 7E : CATÉGORIE 1 RÉGULIÈRE, TAUX 4 %',
        f'Acquisition : {p.acquisition}; disponible pour utilisation : {p.mise_service}',
        f'Sources des soldes/choix : {p.source}',
        'Terrain exclu; aucune acquisition/addition 2025 (0.00 $), disposition ou autre mouvement.',
        'Première année : sans objet; aucune demi-année, accélération ou RII calculé.',
        'Plafond admissible = minimum(solde ouverture x 4 %, revenu locatif avant DPA).']
    for nom, r in (('Fédéral / FNACC',resultat.federal),('Québec / PNACC',resultat.quebec)):
        lignes += [nom, f'Solde ouverture / base admissible : {r.ouverture:.2f} $',
            f'DPA maximale théorique : {r.maximum_theorique:.2f} $; plafond après revenu : {r.maximum_admissible:.2f} $',
            f'Revenu avant DPA : {r.revenu_avant:.2f} $; DPA choisie : {r.choisie:.2f} $',
            f'Revenu après DPA : {r.revenu_apres:.2f} $', f'Solde final = ouverture - DPA choisie : {r.fermeture:.2f} $']
    lignes += ['Sources officielles : T776 F (25), section A; T4036 2025, catégorie 1.',
        'Québec : TP-128 (2025-10), partie 6; TPW-130.G applicable à 2025, sections 4.2 et 5.1.',
        'Demi-cents : convention monétaire générale du logiciel, non règle fiscale spécifique.']
    return lignes
