"""Dividendes canadiens 2025 : paire unique T5/RL-3, audit dans la documentation."""
from dataclasses import dataclass, replace
from decimal import Decimal

from .tax_employment_insurance_2025 import cotisation_fss_prestations_2025
from .tax_field_validation import STATUT_VALIDE, STATUT_CORRIGE_VALIDE
from .tax_field_extractor import formater_montant_fiscal
from .tax_rules_2025 import arrondir_cent

ZERO = Decimal('0')


@dataclass(frozen=True)
class ProfilDividendes2025:
    source: str = ''
    confirme: bool = False
    devise: str = 'CAD'
    compte_conjoint: bool = False
    frais_placement: bool = False
    cas_complexe: bool = False


@dataclass(frozen=True)
class Dividendes2025:
    ligne_166: Decimal = ZERO
    ligne_167: Decimal = ZERO
    ligne_12000: Decimal = ZERO
    ligne_12010: Decimal = ZERO
    ligne_128: Decimal = ZERO
    ligne_40425: Decimal = ZERO
    ligne_415: Decimal = ZERO
    cotisation_fss: Decimal = ZERO
    present: bool = False


def valider_profil_dividendes_2025(p):
    if not isinstance(p, ProfilDividendes2025):
        raise ValueError('Profil dividendes invalide.')
    for nom in ('confirme', 'compte_conjoint', 'frais_placement', 'cas_complexe'):
        if type(getattr(p, nom)) is not bool:
            raise ValueError('Les confirmations dividendes doivent être booléennes.')
    if not isinstance(p.source, str) or not isinstance(p.devise, str):
        raise ValueError('Source et devise dividendes doivent être du texte.')
    if p.devise != 'CAD' or p.compte_conjoint or p.frais_placement or p.cas_complexe:
        raise ValueError('Dividendes : étranger, conjoint, frais ou cas complexe hors périmètre 3C.')
    if p.confirme and not p.source.strip():
        raise ValueError('Justificatif des dividendes obligatoire.')
    return p


def detecter_dividendes_2025(dossier):
    cases = {'T5': {'10','11','12','24','25','26'}, 'RL-3': {'A1','A2','B','C'}}
    return any(d.case in cases.get(d.type_document, set()) and d.valeur_validee != ZERO
               for d in dossier.donnees_validees)


def consolider_dividendes_2025(dossier, profil):
    valider_profil_dividendes_2025(profil)
    if not profil.confirme:
        raise ValueError('Confirmez les dividendes et les exclusions du bloc 3C.')
    if dossier.annee_fiscale != 2025 or dossier.province.casefold() not in {'québec','quebec'}:
        raise ValueError('Dividendes : dossier Québec 2025 requis.')
    if any(d.type_document not in {'T4','RL-1','T5','RL-3'} for d in dossier.donnees_validees):
        raise ValueError('Dividendes : T3/RL-16, autres placements ou prestations hors périmètre 3C.')
    pieces = {p.resolve() for p in dossier.documents}
    if pieces != {d.document.resolve() for d in dossier.donnees_validees}:
        raise ValueError('Dividendes : chaque document doit avoir des données validées.')
    valeurs, documents = {}, {'T5': set(), 'RL-3': set()}
    for d in dossier.donnees_validees:
        if d.type_document not in documents:
            continue
        cle, m = (d.type_document, d.case), d.valeur_validee
        if cle in valeurs:
            raise ValueError('Case dividendes dupliquée; plusieurs feuillets hors périmètre.')
        if d.statut not in {STATUT_VALIDE, STATUT_CORRIGE_VALIDE}:
            raise ValueError('Validation dividendes manquante.')
        if (not isinstance(m, Decimal) or not m.is_finite() or m < ZERO
                or m > Decimal('999999999.99') or m != m.quantize(Decimal('.01'))):
            raise ValueError('Montant dividendes invalide : fini, non négatif, au cent près.')
        valeurs[cle] = m
        documents[d.type_document].add(d.document.resolve())
    if any(len(p) != 1 for p in documents.values()) or documents['T5'] & documents['RL-3']:
        raise ValueError('Une seule paire T5/RL-3 distincte est requise.')
    requis = {('T5', c) for c in ('10','11','12','24','25','26')} | {('RL-3', c) for c in ('A1','A2','B','C')}
    if not requis <= valeurs.keys():
        raise ValueError('Cases dividendes réelles, imposables et crédits obligatoires, même nulles.')
    if ('T5','23') in valeurs and valeurs['T5','23'] != 1:
        raise ValueError('T5 23 : seul un particulier titulaire unique est couvert.')
    if any(m and cle not in requis | {('T5','23')} for cle,m in valeurs.items()):
        raise ValueError('Autre case non nulle : intérêts, étranger, gains ou cas complexe hors périmètre 3C.')
    a, o = valeurs['T5','24'], valeurs['T5','10']
    ta, to = arrondir_cent(a * Decimal('1.38')), arrondir_cent(o * Decimal('1.15'))
    attendus = {('RL-3','A1'): a, ('RL-3','A2'): o, ('T5','25'): ta, ('T5','11'): to,
        ('T5','26'): arrondir_cent(ta * Decimal('.150198')),
        ('T5','12'): arrondir_cent(to * Decimal('.090301')),
        ('RL-3','B'): ta + to,
        ('RL-3','C'): arrondir_cent(a * Decimal('.161460') + o * Decimal('.039330'))}
    for cle, attendu in attendus.items():
        if valeurs[cle] != attendu:
            raise ValueError(f'Dividendes incohérents : {cle[0]} {cle[1]}, appariement/majoration/crédit à vérifier. Aucun ajustement automatique.')
    return Dividendes2025(a, o, ta+to, to, ta+to,
        valeurs['T5','26']+valeurs['T5','12'], valeurs['RL-3','C'],
        cotisation_fss_prestations_2025(a+o), True)


def appliquer_dividendes_2025(revenu, p):
    return replace(revenu, **{
        f'revenu_{niveau}_{juridiction}': getattr(revenu, f'revenu_{niveau}_{juridiction}') + p.ligne_12000
        for niveau in ('total','net','imposable') for juridiction in ('federal','quebec')},
        profil='Dividendes canadiens T5/RL-3 Québec 2025',
        limitations=('Paire unique T5/RL-3, avec ou sans emploi; autres placements exclus.',))


def appliquer_credits_dividendes_2025(federal, quebec, p):
    # 40425 est distinct des crédits 35000; ne pas l'ajouter à la base 33800/34990.
    return (replace(federal, impot_federal_de_base=max(ZERO, federal.impot_federal_de_base-p.ligne_40425)),
            replace(quebec, impot_quebec_preliminaire=max(ZERO, quebec.impot_quebec_preliminaire-p.ligne_415)))


def lignes_resume_dividendes_2025(p, profil):
    if not p.present:
        return []
    f = formater_montant_fiscal
    return ['', 'DIVIDENDES CANADIENS 2025 — BLOC 3C', f'Justificatif : {profil.source}',
        f'Réels admissibles T5 24 / RL-3 A1 / 166 : {f(p.ligne_166)}',
        f'Réels ordinaires T5 10 / RL-3 A2 / 167 : {f(p.ligne_167)}',
        f'Imposables fédéral 12000 / Québec 128 : {f(p.ligne_12000)}',
        f'Sous-total ordinaire 12010 (déjà inclus dans 12000) : {f(p.ligne_12010)}',
        f'Crédits des feuillets 40425 : {f(p.ligne_40425)}; 415 : {f(p.ligne_415)}.',
        "Crédits non remboursables, limités à l'impôt disponible; aucun ajout au revenu ni aux retenues.",
        'Revenus total, net et imposable : montant majoré inclus une seule fois par juridiction.',
        f'FSS 446 sur les montants réels : {f(p.cotisation_fss)}; majoration exclue.',
        'Une paire T5/RL-3 en CAD. T3/RL-16, conjoint, étranger, frais, autres placements et cas complexes exclus.']
