"""3D : vente unique d'actions cotées, PBR indépendant, sans reports de pertes."""
from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal
import re

from .tax_employment_insurance_2025 import cotisation_fss_prestations_2025
from .tax_field_validation import STATUT_VALIDE, STATUT_CORRIGE_VALIDE
from .tax_field_extractor import formater_montant_fiscal
from .tax_rules_2025 import arrondir_cent

ZERO = Decimal('0')
PLAFOND_PRUDENT_IMR = Decimal('177882')
CHAMPS_CAPITAL = (
    ('source', 'Justificatif de vente et appariement T5008/RL-18'),
    ('titre', 'Société canadienne et catégorie des actions cotées (SHS)'),
    ('date_acquisition', 'Acquisition du lot unique (AAAA-MM-JJ, depuis 2000)'),
    ('date_cession', 'Disposition en 2025 (AAAA-MM-JJ)'),
    ('pbr', "PBR fiscal du lot entier, frais d'achat inclus (CAD)"),
    ('source_pbr', "Preuve indépendante du PBR : acquisition et frais d'achat"),
    ('frais_courtage', 'Courtage de vente déjà retiré du RL-18 21 (CAD, zéro explicite)'),
    ('frais_autres', 'Autres frais de disposition hors courtage (CAD, zéro explicite)'),
    ('source_frais', 'Justificatif de la ventilation des frais de disposition'),
)


@dataclass(frozen=True)
class ProfilCapital2025:
    source: str = ''
    titre: str = ''
    date_acquisition: str = ''
    date_cession: str = ''
    pbr: str = ''
    source_pbr: str = ''
    frais_courtage: str = ''
    frais_autres: str = ''
    source_frais: str = ''
    confirme: bool = False
    pbr_confirme: bool = False
    devise: str = 'CAD'
    compte_conjoint: bool = False
    cas_complexe: bool = False
    reports_pertes: bool = False
    perte_apparente: bool = False


@dataclass(frozen=True)
class GainsCapital2025:
    produit: Decimal = ZERO
    produit_rl18: Decimal = ZERO
    pbr: Decimal = ZERO
    frais_courtage: Decimal = ZERO
    frais_autres: Decimal = ZERO
    gain_perte: Decimal = ZERO
    ligne_12700: Decimal = ZERO
    ligne_139: Decimal = ZERO
    perte_nette_2025: Decimal = ZERO
    cotisation_fss: Decimal = ZERO
    present: bool = False


def montant_capital_2025(texte):
    if not isinstance(texte, str) or not re.fullmatch(r'\d{1,9}(?:[.,]\d{1,2})?', texte.strip()):
        raise ValueError('Montant capital : texte numérique non négatif au cent près requis.')
    return Decimal(texte.strip().replace(',', '.'))


def valider_profil_capital_2025(p):
    if not isinstance(p, ProfilCapital2025):
        raise ValueError('Profil capital invalide.')
    for nom in ('confirme','pbr_confirme','compte_conjoint','cas_complexe','reports_pertes','perte_apparente'):
        if type(getattr(p,nom)) is not bool:
            raise ValueError('Les confirmations capital doivent être booléennes.')
    for nom in tuple(n for n,_ in CHAMPS_CAPITAL)+('devise',):
        if not isinstance(getattr(p,nom),str):
            raise ValueError('Les champs capital doivent être du texte.')
    if p.devise != 'CAD' or p.compte_conjoint or p.cas_complexe or p.reports_pertes or p.perte_apparente:
        raise ValueError('Capital : étranger, conjoint, perte apparente, cas complexe ou reports de pertes hors périmètre 3D.')
    for nom in ('pbr','frais_courtage','frais_autres'):
        if getattr(p,nom): montant_capital_2025(getattr(p,nom))
    dates={}
    for nom in ('date_acquisition','date_cession'):
        texte=getattr(p,nom)
        if texte:
            try:
                dates[nom]=date.fromisoformat(texte)
                if dates[nom].isoformat()!=texte: raise ValueError()
            except ValueError as erreur:
                raise ValueError('Date capital invalide : format AAAA-MM-JJ requis.') from erreur
    if 'date_acquisition' in dates and not 2000 <= dates['date_acquisition'].year <= 2025:
        raise ValueError('Acquisition hors périmètre : lot acheté depuis 2000 requis.')
    if 'date_cession' in dates and dates['date_cession'].year != 2025:
        raise ValueError('Disposition en 2025 requise.')
    if len(dates)==2 and (dates['date_cession']-dates['date_acquisition']).days <= 30:
        raise ValueError('Acquisition dans les 30 jours avant la vente ou dates incohérentes : hors périmètre.')
    if p.pbr_confirme and (not p.source_pbr.strip() or not p.pbr):
        raise ValueError('Preuve indépendante et montant PBR obligatoires avant confirmation.')
    if p.confirme and (not p.pbr_confirme or any(not getattr(p,n).strip() for n,_ in CHAMPS_CAPITAL)):
        raise ValueError('Capital : tous les justificatifs, dates, montants et la confirmation PBR sont obligatoires.')
    return p


def detecter_capital_2025(dossier):
    return any(d.type_document in {'T5008','RL-18'} for d in dossier.donnees_validees)


def consolider_capital_2025(dossier, profil):
    valider_profil_capital_2025(profil)
    if not profil.confirme:
        raise ValueError('Confirmez le PBR indépendant, la vente et les exclusions du bloc 3D.')
    if dossier.annee_fiscale != 2025 or dossier.province.casefold() not in {'québec','quebec'}:
        raise ValueError('Capital : dossier Québec 2025 requis.')
    if any(d.type_document not in {'T4','RL-1','T5008','RL-18'} for d in dossier.donnees_validees):
        raise ValueError('Capital : distributions, autres placements ou prestations hors périmètre 3D.')
    pieces={p.resolve() for p in dossier.documents}
    if pieces!={d.document.resolve() for d in dossier.donnees_validees}:
        raise ValueError('Capital : chaque document doit avoir des données validées.')
    valeurs,documents={}, {'T5008':set(),'RL-18':set()}
    for d in dossier.donnees_validees:
        if d.type_document not in documents: continue
        cle,m=(d.type_document,d.case),d.valeur_validee
        if cle in valeurs:
            raise ValueError('Case capital dupliquée : plusieurs transactions hors périmètre.')
        if d.statut not in {STATUT_VALIDE,STATUT_CORRIGE_VALIDE}:
            raise ValueError('Validation capital manquante.')
        if (not isinstance(m,Decimal) or not m.is_finite() or m<ZERO or m>Decimal('999999999.99') or m!=m.quantize(Decimal('.01'))):
            raise ValueError('Montant capital invalide : fini, non négatif, au cent près.')
        valeurs[cle]=m
        documents[d.type_document].add(d.document.resolve())
    if any(len(p)!=1 for p in documents.values()) or documents['T5008'] & documents['RL-18']:
        raise ValueError('Une seule paire T5008/RL-18 distincte, une transaction chacun, est requise.')
    if any((t,'21') not in valeurs for t in documents):
        raise ValueError('Cases 21 T5008 et RL-18 obligatoires.')
    # 20 est une information à comparer humainement, jamais une source de calcul du PBR.
    if any(c not in {'20','21'} and m for (t,c),m in valeurs.items()):
        raise ValueError('Autre case capital non nulle : titre ou opération hors périmètre 3D.')
    produit,net=valeurs['T5008','21'],valeurs['RL-18','21']
    pbr=montant_capital_2025(profil.pbr)
    courtage=montant_capital_2025(profil.frais_courtage)
    autres=montant_capital_2025(profil.frais_autres)
    if produit-courtage!=net:
        raise ValueError('Appariement incohérent : T5008 21 brut moins courtage doit égaler RL-18 21 net de courtage.')
    gain=produit-pbr-courtage-autres
    imposable=arrondir_cent(max(ZERO,gain)*Decimal('.5'))
    perte=arrondir_cent(max(ZERO,-gain)*Decimal('.5'))
    return GainsCapital2025(produit,net,pbr,courtage,autres,gain,imposable,imposable,perte,
                           cotisation_fss_prestations_2025(imposable),True)


def appliquer_capital_2025(revenu,p):
    # Borne supérieure sans déductions, valide uniquement dans le périmètre salaire + vente simple.
    if max(revenu.revenu_total_federal,revenu.revenu_total_quebec)+max(ZERO,p.gain_perte)>PLAFOND_PRUDENT_IMR:
        raise ValueError('Impôt minimum potentiel : salaire brut + gain intégral supérieur à 177 882 $, hors périmètre 3D.')
    return replace(revenu,**{f'revenu_{niveau}_{juridiction}':getattr(revenu,f'revenu_{niveau}_{juridiction}')+p.ligne_12700
        for niveau in ('total','net','imposable') for juridiction in ('federal','quebec')},
        profil='Vente unique actions canadiennes Québec 2025',
        limitations=('PBR indépendant confirmé; aucun report de pertes, distribution ou autre placement.',))


def lignes_resume_capital_2025(p,profil,reports=False):
    if not p.present: return []
    f=formater_montant_fiscal
    return ['', 'GAINS ET PERTES EN CAPITAL 2025 — BLOC 3D',
        f'Titre : {profil.titre}; acquisition {profil.date_acquisition}; vente {profil.date_cession}.',
        f'Justificatif vente : {profil.source}',
        f'PBR indépendant : {f(p.pbr)}; preuve : {profil.source_pbr}',
        'La case 20 des feuillets ne constitue jamais le PBR automatique.',
        f'Produit brut T5008 21 / annexe 3 13199 : {f(p.produit)}',
        f'RL-18 21 net de courtage : {f(p.produit_rl18)}',
        f'Courtage : {f(p.frais_courtage)}; autres frais de disposition : {f(p.frais_autres)}.',
        f'Justificatif frais : {profil.source_frais}',
        f'Gain/perte annexe 3 13200 / annexe G 10 : {f(p.gain_perte)}',
        f'Inclusion 50 %; fédéral 12700 / Québec 139 : {f(p.ligne_12700)}',
        'Seul le gain imposable positif augmente les revenus total, net et imposable.',
        f'Perte nette 2025 calculée à vérifier : {f(p.perte_nette_2025)}; ' + ('suivi dans le registre 3F.' if reports else 'aucun report utilisé ou certifié.'),
        'Une perte nette ne réduit ni le salaire ni les autres revenus.',
        f'FSS 446 sur le gain imposable : {f(p.cotisation_fss)}; aucune retenue ajoutée.',
        'Vente unique en CAD; hors T3/T5, pertes apparentes, étranger, conjoint, autres placements et IMR complexe.']
