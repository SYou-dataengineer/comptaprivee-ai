"""Bloc 2F : retraits et paiements uniques domestiques, sans transfert.

Références 2025 et exclusions : docs/moteur_fiscal_2025.md.
"""
from dataclasses import dataclass, replace
from decimal import Decimal

from .tax_employment_insurance_2025 import cotisation_fss_prestations_2025
from .tax_field_validation import STATUT_VALIDE, STATUT_CORRIGE_VALIDE
from .tax_field_extractor import formater_montant_fiscal

ZERO = Decimal('0')
NATURES_RETRAITS = {
    'REER_ORDINAIRE': ('T4RSP', '22', 'C'),
    'COTISATIONS_INUTILISEES': ('T4RSP', '20', 'F'),
    'FORFAIT_RPA': ('T4A', '018', 'C'),
}


@dataclass(frozen=True)
class ProfilRetraits2025:
    nature: str = ''
    source: str = ''
    confirme: bool = False


@dataclass(frozen=True)
class Retraits2025:
    ligne_12900: Decimal = ZERO
    ligne_13000: Decimal = ZERO
    ligne_23200: Decimal = ZERO
    ligne_154: Decimal = ZERO
    ligne_250_6: Decimal = ZERO
    retenue_federale: Decimal = ZERO
    retenue_quebec: Decimal = ZERO
    cotisation_fss: Decimal = ZERO
    present: bool = False


def valider_profil_retraits_2025(p):
    if not isinstance(p, ProfilRetraits2025) or type(p.confirme) is not bool:
        raise ValueError('Profil retraits : confirmation booléenne requise.')
    if not isinstance(p.nature, str) or not isinstance(p.source, str):
        raise ValueError('Nature et source retraits invalides.')
    if p.nature and p.nature not in NATURES_RETRAITS:
        raise ValueError('Nature de retrait hors périmètre.')
    if p.confirme and (not p.nature or not p.source.strip()):
        raise ValueError('Nature et justificatif requis; T3012A approuvé pour les cotisations inutilisées.')
    return p


def detecter_retraits_2025(dossier):
    return any(d.type_document == 'T4RSP'
               or (d.type_document == 'T4A' and d.case.zfill(3) in {'018', '106'})
               or (d.type_document == 'T4' and d.case in {'66', '67'})
               for d in dossier.donnees_validees)


def consolider_retraits_2025(dossier, profil):
    valider_profil_retraits_2025(profil)
    if not profil.confirme:
        raise ValueError('Confirmez le profil retraits et les exclusions; calcul hors périmètre sans cette revue.')
    if dossier.annee_fiscale != 2025 or dossier.province.casefold() not in {'québec', 'quebec'}:
        raise ValueError('Retraits : dossier Québec 2025 requis.')
    t, c, cq = NATURES_RETRAITS[profil.nature]
    if any(d.type_document not in {'T4', 'RL-1', t, 'RL-2'} for d in dossier.donnees_validees):
        raise ValueError('Retraits : autres revenus ou prestations hors périmètre.')
    if any(d.type_document == 'T4' and d.case in {'66','67'} and d.valeur_validee
           for d in dossier.donnees_validees):
        raise ValueError('Allocations de retraite T4 66/67 : transfert et appariement RL-1 hors périmètre.')
    valeurs = {}
    documents = {ty: set() for ty in (t, 'RL-2')}
    pieces = {p.resolve() for p in dossier.documents}
    for d in dossier.donnees_validees:
        if d.type_document not in documents:
            continue
        ca = d.case.zfill(3) if d.type_document == 'T4A' else d.case
        cle = (d.type_document, ca)
        if cle in valeurs:
            raise ValueError('Case retraits dupliquée.')
        if d.document.resolve() not in pieces or d.statut not in {STATUT_VALIDE, STATUT_CORRIGE_VALIDE}:
            raise ValueError('Source ou validation retraits manquante.')
        montant = d.valeur_validee
        if (not isinstance(montant, Decimal) or not montant.is_finite()
                or montant < ZERO or montant > Decimal('999999999.99')
                or montant != montant.quantize(Decimal('.01'))):
            raise ValueError('Montant retraits invalide; négatifs et cas 23200 complexes hors périmètre.')
        valeurs[cle] = montant
        documents[d.type_document].add(d.document.resolve())
    if any(len(v) != 1 for v in documents.values()) or documents[t] & documents['RL-2']:
        raise ValueError('Une seule paire de feuillets distincts est requise.')
    if (t,c) not in valeurs or ('RL-2',cq) not in valeurs or valeurs[t,c] != valeurs['RL-2',cq]:
        raise ValueError('Cases principales retraits obligatoires et égales, sans double compte.')
    retenue = '30' if t == 'T4RSP' else '022'
    autorisees = {(t,c), (t,retenue), ('RL-2',cq), ('RL-2','J')}
    if any(m and cle not in autorisees for cle,m in valeurs.items()):
        raise ValueError('Retraits : RAP/REEP, décès, conjoint, transfert ou autre case hors périmètre.')
    brut = valeurs[t,c]
    remboursement = brut if profil.nature == 'COTISATIONS_INUTILISEES' else ZERO
    return Retraits2025(
        ligne_12900=brut if t == 'T4RSP' else ZERO,
        ligne_13000=brut if t == 'T4A' else ZERO,
        ligne_23200=remboursement, ligne_154=brut, ligne_250_6=remboursement,
        retenue_federale=valeurs.get((t,retenue),ZERO), retenue_quebec=valeurs.get(('RL-2','J'),ZERO),
        cotisation_fss=cotisation_fss_prestations_2025(brut-remboursement), present=True)


def appliquer_retraits_2025(revenu, p):
    brut = p.ligne_12900 + p.ligne_13000
    return replace(revenu,
        revenu_total_federal=revenu.revenu_total_federal+brut,
        revenu_net_federal=revenu.revenu_net_federal+brut-p.ligne_23200,
        revenu_imposable_federal=revenu.revenu_imposable_federal+brut-p.ligne_23200,
        revenu_total_quebec=revenu.revenu_total_quebec+p.ligne_154,
        revenu_net_quebec=revenu.revenu_net_quebec+p.ligne_154-p.ligne_250_6,
        revenu_imposable_quebec=revenu.revenu_imposable_quebec+p.ligne_154-p.ligne_250_6,
        profil='Retraits REER et sommes forfaitaires Québec 2025')


def lignes_resume_retraits_2025(p, profil):
    if not p.present:
        return []
    f = formater_montant_fiscal
    return ['', 'RETRAITS REER ET SOMMES FORFAITAIRES 2025',
        f'Nature : {profil.nature}; justificatif : {profil.source}',
        f'Revenu fédéral 12900 / 13000 : {f(p.ligne_12900)} / {f(p.ligne_13000)}',
        f'Déduction fédérale 23200 : {f(p.ligne_23200)}',
        f'Revenu Québec 154 / déduction 250 point 6 : {f(p.ligne_154)} / {f(p.ligne_250_6)}',
        f'Retenues 43700 / 451 : {f(p.retenue_federale)} / {f(p.retenue_quebec)}',
        f'FSS 446 : {f(p.cotisation_fss)}',
        'Aucun crédit pension 31400/361; aucun ajout à 122. Feuillets appariés, comptés une fois.',
        'Sans RAP/REEP, décès, conjoint, transfert, rétroactivité ou autre revenu hors profil.']
