"""2H : assistance sociale ordinaire, indemnités CNESST et SAAQ courantes.

Sources et exclusions documentées dans docs/moteur_fiscal_2025.md.
"""
from dataclasses import dataclass, replace
from decimal import Decimal
from .tax_field_validation import STATUT_VALIDE, STATUT_CORRIGE_VALIDE
from .tax_field_extractor import formater_montant_fiscal
from .tax_rules_2025 import arrondir_cent

ZERO = Decimal('0')
NATURES_REMPLACEMENT = {'ASSISTANCE_SOCIALE': ('11', 'A'), 'CNESST': ('10', 'C'), 'SAAQ': (None, 'D')}


@dataclass(frozen=True)
class ProfilRemplacement2025:
    nature: str = ''
    source: str = ''
    confirme: bool = False


@dataclass(frozen=True)
class PrestationsRemplacement2025:
    ligne_14400: Decimal = ZERO
    ligne_14500: Decimal = ZERO
    ligne_25000: Decimal = ZERO
    ligne_147: Decimal = ZERO
    ligne_148: Decimal = ZERO
    ligne_295: Decimal = ZERO
    ligne_358: Decimal = ZERO
    present: bool = False


def valider_profil_remplacement_2025(p):
    if not isinstance(p, ProfilRemplacement2025) or type(p.confirme) is not bool:
        raise ValueError('Profil remplacement : confirmation booléenne requise.')
    if not isinstance(p.nature, str) or not isinstance(p.source, str):
        raise ValueError('Nature et source remplacement invalides.')
    if p.nature and p.nature not in NATURES_REMPLACEMENT:
        raise ValueError('Nature particulière, retrait préventif et autres prestations : hors périmètre.')
    if p.confirme and (not p.nature or not p.source.strip()):
        raise ValueError('Nature et justificatif remplacement obligatoires.')
    return p


def detecter_remplacement_2025(dossier):
    return any(d.type_document in {'T5007', 'RL-5'} for d in dossier.donnees_validees)


def consolider_remplacement_2025(dossier, profil):
    valider_profil_remplacement_2025(profil)
    if not profil.confirme:
        raise ValueError('Confirmez les prestations de remplacement et les exclusions.')
    if dossier.annee_fiscale != 2025 or dossier.province.casefold() not in {'québec', 'quebec'}:
        raise ValueError('Prestations : dossier Québec 2025 requis.')
    if any(d.type_document not in {'T4', 'RL-1', 'T5007', 'RL-5'} for d in dossier.donnees_validees):
        raise ValueError('Autres prestations ou pensions : hors périmètre.')
    saaq = profil.nature == 'SAAQ'
    if saaq and any(d.type_document == 'T5007' for d in dossier.donnees_validees):
        raise ValueError('SAAQ ordinaire : RL-5 seul, aucun T5007; profil mixte hors périmètre.')
    valeurs = {}
    documents = {t: set() for t in (('RL-5',) if saaq else ('T5007', 'RL-5'))}
    pieces = {p.resolve() for p in dossier.documents}
    for d in dossier.donnees_validees:
        if d.type_document not in documents:
            continue
        cle = (d.type_document, d.case)
        m = d.valeur_validee
        if cle in valeurs:
            raise ValueError('Case prestations dupliquée.')
        if d.document.resolve() not in pieces or d.statut not in {STATUT_VALIDE, STATUT_CORRIGE_VALIDE}:
            raise ValueError('Source ou validation prestations manquante.')
        if (not isinstance(m, Decimal) or not m.is_finite() or m < ZERO
                or m > Decimal('999999999.99') or m != m.quantize(Decimal('.01'))):
            raise ValueError('Montant prestations invalide.')
        valeurs[cle] = m
        documents[d.type_document].add(d.document.resolve())
    if any(len(v) != 1 for v in documents.values()) or (not saaq and documents['T5007'] & documents['RL-5']):
        raise ValueError('Une seule paire T5007/RL-5 distincte, ou un RL-5 seul pour SAAQ, est requise.')
    cf, cq = NATURES_REMPLACEMENT[profil.nature]
    if ('RL-5', cq) not in valeurs or (not saaq and (('T5007', cf) not in valeurs or valeurs['T5007', cf] != valeurs['RL-5', cq])):
        raise ValueError('Cases principales obligatoires et égales, sans double compte.')
    cnesst = profil.nature == 'CNESST'
    autorisees = {('RL-5', cq)} if saaq else {('T5007', cf), ('RL-5', cq)}
    if cnesst or saaq:
        autorisees.add(('RL-5', 'M'))
        if ('RL-5', 'M') not in valeurs:
            raise ValueError('CNESST/SAAQ : case M explicite obligatoire, même nulle.')
    if any(m and cle not in autorisees for cle, m in valeurs.items()):
        raise ValueError('Nature mixte, autre aide, remboursement, rétroactivité ou autre case : hors périmètre.')
    m = valeurs.get(('RL-5', 'M'), ZERO)
    if m > Decimal('16713.90'):
        raise ValueError('Redressement 358 supérieur au plafond 2025 de 16 713,90 $.')
    brut = valeurs['RL-5', cq]
    return PrestationsRemplacement2025(
        ligne_14400=brut if cnesst else ZERO, ligne_14500=ZERO if cnesst or saaq else brut,
        ligne_25000=ZERO if saaq else brut, ligne_147=ZERO if cnesst or saaq else brut,
        ligne_148=brut if cnesst or saaq else ZERO, ligne_295=brut if cnesst or saaq else ZERO,
        ligne_358=m, present=True)


def appliquer_remplacement_2025(revenu, p):
    brut = p.ligne_14400 + p.ligne_14500
    qc = p.ligne_147 + p.ligne_148
    return replace(revenu,
        revenu_total_federal=revenu.revenu_total_federal + brut,
        revenu_net_federal=revenu.revenu_net_federal + brut,
        revenu_imposable_federal=revenu.revenu_imposable_federal + brut - p.ligne_25000,
        revenu_total_quebec=revenu.revenu_total_quebec + qc,
        revenu_net_quebec=revenu.revenu_net_quebec + qc,
        revenu_imposable_quebec=revenu.revenu_imposable_quebec + qc - p.ligne_295,
        profil='Prestations de remplacement Québec 2025')


def appliquer_redressement_358_2025(quebec, p):
    if not p.present:
        return quebec
    credit = arrondir_cent((quebec.montant_personnel_base - p.ligne_358) * quebec.taux_credit_personnel)
    return replace(quebec, credit_personnel_base=credit,
        impot_quebec_preliminaire=max(ZERO, quebec.impot_brut - credit),
        limitations=tuple(x for x in quebec.limitations if 'CNESST/SAAQ' not in x))


def lignes_resume_remplacement_2025(p, profil):
    if not p.present:
        return []
    f = formater_montant_fiscal
    return ['', 'AUTRES PRESTATIONS DE REMPLACEMENT 2025',
        f'Nature : {profil.nature}; justificatif : {profil.source}',
        f'Fédéral 14400 / 14500 : {f(p.ligne_14400)} / {f(p.ligne_14500)}',
        f'Déduction 25000 : {f(p.ligne_25000)}; revenu net conservé.',
        f'Québec 147 / 148 : {f(p.ligne_147)} / {f(p.ligne_148)}',
        f'Déduction 295 : {f(p.ligne_295)}; aucune déduction 295 pour 147.',
        f'Redressement 358 (RL-5 M) : {f(p.ligne_358)}; réduction du montant personnel avant crédit.',
        'Prestations exclues du FSS; aucune retenue ajoutée sur T5007/RL-5.',
        'Une nature; paire T5007/RL-5 ou RL-5 seul pour SAAQ; sans conjoint ni remboursement à l’employeur.',
        'SAAQ : indemnité de la victime non déclarable au fédéral; Québec 148 source 03 (CNESST : 01).',
        'Décès, rétroactivité, retrait préventif, autres aides, RAMQ publique et cas complexes exclus.']
