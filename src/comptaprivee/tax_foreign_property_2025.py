"""7J : inventaire et obligations seulement; aucun revenu ni crédit calculé.

Coûts fiscaux en CAD déjà établis, chronologie exhaustive confirmée.
Le maximum de la somme n'est pas la somme des maxima individuels.
"""
from dataclasses import dataclass, fields
from datetime import datetime
from decimal import Decimal, InvalidOperation

ZERO = Decimal('0.00')
SEUIL = Decimal('100000.00')
SEUIL_DETAIL = Decimal('250000.00')
DEBUT = '2025-01-01T00:00:00'
FIN = '2025-12-31T23:59:59'
TYPES_7J = {
    'compte': 'Compte bancaire étranger - catégorie T1135 1',
    'actions': 'Actions de société non résidente non affiliée - catégorie 2',
    'dette': 'Dette due par un non-résident non affilié - catégorie 3',
    'fiducie_simple': 'Participation acquise contre paiement, fiducie non résidente simple - catégorie 4',
    'metaux_precieux': 'Métaux précieux détenus hors Canada - catégorie 6',
    'immeuble': 'Immeuble étranger déterminé sans usage personnel - catégorie 5',
}
# Premier périmètre : codes ISO alpha-3 explicites; aucun pays libre inventé.
PAYS_7J = {
    'USA': 'États-Unis', 'FRA': 'France', 'GBR': 'Royaume-Uni', 'DEU': 'Allemagne',
    'CHE': 'Suisse', 'BEL': 'Belgique', 'ESP': 'Espagne', 'ITA': 'Italie',
    'PRT': 'Portugal', 'NLD': 'Pays-Bas', 'LUX': 'Luxembourg', 'IRL': 'Irlande',
    'JPN': 'Japon', 'AUS': 'Australie', 'NZL': 'Nouvelle-Zélande', 'MEX': 'Mexique',
    'IND': 'Inde', 'CHN': 'Chine', 'HKG': 'Hong Kong', 'SGP': 'Singapour',
    'MAR': 'Maroc', 'DZA': 'Algérie', 'TUN': 'Tunisie', 'BRA': 'Brésil',
}
AVERTISSEMENT = ('Cette préparation ne remplace pas la déclaration du revenu étranger ni '
                 'le calcul du crédit pour impôt étranger.')
AVERTISSEMENT_ARRIVEE = (
    'Nouvel arrivant en 2025 : le formulaire TP-1079.8.BE n’est pas requis pour '
    'cette année selon Revenu Québec. La réponse à la ligne 25 n’est pas automatisée '
    'par ComptaPrivée AI et doit être validée lors de la préparation de la déclaration.'
)


@dataclass(frozen=True)
class CoutEtranger2025:
    moment: str
    cout: Decimal


@dataclass(frozen=True)
class BienEtranger2025:
    reference: str
    nature: str
    pays: str
    cout_debut: Decimal
    cout_maximal: Decimal
    cout_fin: Decimal
    revenu_brut_connu: Decimal
    gain_perte_connu: Decimal
    source: str
    couts: tuple[CoutEtranger2025, ...]
    qualification_confirmee: bool = False
    exclusion: str = ''


@dataclass(frozen=True)
class InventaireEtranger2025:
    biens: tuple[BienEtranger2025, ...] = ()
    source: str = ''
    confirme: bool = False
    chronologie_complete: bool = False
    particulier_quebec: bool = False
    premiere_residence_2025: bool = False


def _montant(v, signe=False):
    if (not isinstance(v, Decimal) or not v.is_finite()
            or abs(v) > Decimal('999999999.99') or (not signe and v < ZERO)
            or v != v.quantize(Decimal('.01'))):
        raise ValueError('7J : montant Decimal fini au cent requis; coût/revenu non négatif.')


def _texte(v):
    if not isinstance(v, str) or not v.strip():
        raise ValueError('7J : référence et source documentée obligatoires.')


def valider_inventaire_etranger_2025(p):
    if p is None: return
    if type(p) is not InventaireEtranger2025:
        raise ValueError('7J : inventaire immuable requis.')
    _texte(p.source)
    for n in ('confirme', 'chronologie_complete', 'particulier_quebec', 'premiere_residence_2025'):
        if type(getattr(p,n)) is not bool:
            raise ValueError('7J : confirmations booléennes requises.')
    if not (p.confirme and p.chronologie_complete and p.particulier_quebec):
        raise ValueError('7J : qualification, exhaustivité, coûts CAD, chronologie et résidence à confirmer.')
    if not isinstance(p.biens, tuple):
        raise ValueError('7J : inventaire immuable requis.')
    refs = set()
    for b in p.biens:
        if type(b) is not BienEtranger2025:
            raise ValueError('7J : fiche de bien invalide.')
        _texte(b.reference); _texte(b.source)
        ref=b.reference.strip().casefold()
        if ref in refs: raise ValueError('7J : doublon de bien.')
        refs.add(ref)
        if not isinstance(b.nature, str) or b.nature not in TYPES_7J:
            raise ValueError('7J : type ambigu, personnel, enregistré ou hors périmètre.')
        if not isinstance(b.pays, str) or b.pays not in PAYS_7J:
            raise ValueError('7J : pays inconnu ou hors liste supportée; code ISO alpha-3 requis.')
        if b.qualification_confirmee is not True or type(b.qualification_confirmee) is not bool:
            raise ValueError('7J : qualification du bien dans les deux juridictions à confirmer.')
        if not isinstance(b.exclusion,str) or b.exclusion:
            raise ValueError('7J : bien exclu; personnel, régime enregistré, entreprise active, affiliée ou structure complexe.')
        for n in ('cout_debut','cout_maximal','cout_fin','revenu_brut_connu'):
            _montant(getattr(b,n))
        _montant(b.gain_perte_connu, signe=True)
        if not isinstance(b.couts,tuple) or len(b.couts)<2:
            raise ValueError('7J : coûts inconnus; chronologie complète avec début et fin requise.')
        precedent=''
        for c in b.couts:
            if type(c) is not CoutEtranger2025 or not isinstance(c.moment,str):
                raise ValueError('7J : état de coût daté invalide.')
            try: instant=datetime.fromisoformat(c.moment)
            except ValueError as exc: raise ValueError('7J : instant ISO invalide.') from exc
            if (instant.tzinfo is not None or instant.isoformat(timespec='seconds') != c.moment
                    or not DEBUT <= c.moment <= FIN or c.moment <= precedent):
                raise ValueError('7J : instants 2025 ordonnés, distincts, même référence horaire, précision seconde requis.')
            _montant(c.cout); precedent=c.moment
        if b.couts[0].moment != DEBUT or b.couts[-1].moment != FIN:
            raise ValueError('7J : coûts de début et de fin explicites requis, zéro si absent.')
        if (b.cout_debut != b.couts[0].cout or b.cout_fin != b.couts[-1].cout
                or b.cout_maximal != max(c.cout for c in b.couts)):
            raise ValueError('7J : agrégation incohérente; début/maximum/fin différents de la chronologie.')


def inventaire_etranger_vers_json(p):
    valider_inventaire_etranger_2025(p)
    if p is None: return None
    def serialiser(v):
        if isinstance(v,Decimal): return str(v)
        if isinstance(v,tuple): return [serialiser(x) for x in v]
        if hasattr(v,'__dataclass_fields__'): return {f.name:serialiser(getattr(v,f.name)) for f in fields(v)}
        return v
    return serialiser(p)


def inventaire_etranger_depuis_json(v):
    if v is None: return None
    def objet(d,cls,decimaux=()):
        if not isinstance(d,dict) or set(d)-{f.name for f in fields(cls)}:
            raise ValueError('7J : champ JSON inconnu; aucun revenu imposable/crédit automatique accepté.')
        r=dict(d)
        for n in decimaux:
            if not isinstance(r.get(n),str): raise ValueError('7J : montant JSON décimal explicite en texte requis.')
            try:r[n]=Decimal(r[n])
            except InvalidOperation as exc:raise ValueError('7J : montant JSON invalide.') from exc
        return r
    d=objet(v,InventaireEtranger2025)
    if not isinstance(d.get('biens',[]),list): raise ValueError('7J : tableau JSON de biens requis.')
    biens=[]
    try:
        for b in d.get('biens',[]):
            x=objet(b,BienEtranger2025,('cout_debut','cout_maximal','cout_fin','revenu_brut_connu','gain_perte_connu'))
            if not isinstance(x.get('couts'),list): raise ValueError('7J : tableau JSON des coûts requis.')
            x['couts']=tuple(CoutEtranger2025(**objet(c,CoutEtranger2025,('cout',))) for c in x['couts'])
            biens.append(BienEtranger2025(**x))
        d['biens']=tuple(biens);p=InventaireEtranger2025(**d)
    except TypeError as exc:raise ValueError('7J : faits JSON incomplets.') from exc
    valider_inventaire_etranger_2025(p)
    return p


@dataclass(frozen=True)
class PreparationBiensEtrangers2025:
    cout_total_maximal: Decimal
    moment_maximal: str
    t1135_requis: bool
    methode_federale: str
    tp1079_requis: bool
    ligne_25: bool | None
    exception_nouvel_arrivant: bool


def preparer_biens_etrangers_2025(dossier):
    p=dossier.biens_etrangers
    valider_inventaire_etranger_2025(p)
    if p is None:return None
    if dossier.annee_fiscale != 2025 or dossier.province.casefold() not in ('québec','quebec'):
        raise ValueError('7J : particulier Québec 2025 seulement.')
    # Les états de tous les biens sont rapprochés au même instant.
    changements={}
    for b in p.biens:
        for c in b.couts:
            changements.setdefault(c.moment,[]).append((b.reference,c.cout))
    courants={};maximum=ZERO;moment=DEBUT
    for instant in sorted(changements):
        courants.update(changements[instant])
        total=sum(courants.values(),ZERO)
        if total>maximum: maximum=total;moment=instant
    if p.premiere_residence_2025:
        # Dispense fédérale indépendante : T1135 E(23), p. 4, art. 233.7.
        # Ligne 25 indéterminée : décision produit, pas une réponse fiscale « non ».
        return PreparationBiensEtrangers2025(maximum,moment,False,'aucune',False,None,True)
    requis=maximum>SEUIL
    methode='aucune' if not requis else 'partie A possible' if maximum<SEUIL_DETAIL else 'partie B requise'
    return PreparationBiensEtrangers2025(maximum,moment,requis,methode,requis,requis,False)


def lignes_biens_etrangers_2025(dossier):
    r=preparer_biens_etrangers_2025(dossier)
    if r is None:return ()
    p=dossier.biens_etrangers
    lignes=['BIENS ÉTRANGERS 2025 - PRÉPARATION 7J',f'Source du contrôle : {p.source}',
        f'Coût total maximal simultané : {r.cout_total_maximal:.2f} $ CA, au {r.moment_maximal}.',
        'Seuil : strictement plus de 100 000 $ CA; coût fiscal, pas la JVM.',
        'T1135 requis : '+('oui' if r.t1135_requis else 'non'),
        'Méthode fédérale : '+r.methode_federale+'; hors dispense, partie B obligatoire dès 250 000 $ CA.',
        'TP-1079.8.BE requis : '+('oui' if r.tp1079_requis else 'non'),
        'Ligne 25 Québec : '+('à valider manuellement' if r.ligne_25 is None else 'oui' if r.ligne_25 else 'non'),
        'Exception nouvel arrivant Québec : '+('oui' if r.exception_nouvel_arrivant else 'non')]
    if r.exception_nouvel_arrivant:
        lignes += [AVERTISSEMENT_ARRIVEE,
            'Limite prudente du logiciel pour la ligne 25, et non interprétation fiscale définitive.',
            'T1135 : dispense indépendante de première résidence, ARC T1135 E(23), page 4, article 233.7.',
            'Inventaire, sauvegarde et préparation PDF disponibles; aucun TP-1079.8.BE produit.',
            'Estimation annuelle hors périmètre pour résidence partielle (7K), indépendamment de la dispense.']
    for b in p.biens:
        lignes += [f'{b.reference} : {TYPES_7J[b.nature]}; {b.pays} ({PAYS_7J[b.pays]}).',
            f'Coût début {b.cout_debut:.2f}; maximum individuel {b.cout_maximal:.2f}; fin {b.cout_fin:.2f} $ CA.',
            f'Revenu brut connu {b.revenu_brut_connu:.2f}; gain/perte connu {b.gain_perte_connu:.2f} $ CA (information seulement).',
            'Source : '+b.source]
        lignes += [f'  {c.moment} : coût fiscal {c.cout:.2f} $ CA' for c in b.couts]
    lignes += [AVERTISSEMENT,'Le revenu étranger doit être déclaré même sous le seuil.',
        'Aucun revenu, gain, impôt ou crédit étranger calculé ni ajouté aux revenus par 7J.',
        'Coûts CAD déjà établis et confirmés; aucune conversion de devises ni estimation de JVM.',
        'Inventaire préparatoire : aucun formulaire officiel complet produit ou transmis.']
    return tuple(lignes)


def verifier_annuel_biens_etrangers_2025(dossier):
    """Les faits déclaratifs ne produisent aucun montant dans la déclaration."""
    p=dossier.biens_etrangers
    if p is None: return
    valider_inventaire_etranger_2025(p)
    if p.premiere_residence_2025:
        raise ValueError('7J : résidence partielle; estimation annuelle hors périmètre, préparation externe requise (7K).')
    if dossier.deces is not None and p.biens:
        raise ValueError('7J / 7H : biens étrangers au décès; déclaration finale externe requise.')
    preparer_biens_etrangers_2025(dossier)
