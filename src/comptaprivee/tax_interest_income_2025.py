"""Bloc 3A : intérêts canadiens ordinaires, une paire T5/RL-3 en CAD.

Sources 2025, audit et exclusions : docs/moteur_fiscal_2025.md.
"""
from dataclasses import dataclass, replace
from decimal import Decimal

from .tax_employment_insurance_2025 import cotisation_fss_prestations_2025
from .tax_field_validation import STATUT_VALIDE, STATUT_CORRIGE_VALIDE
from .tax_field_extractor import formater_montant_fiscal

ZERO = Decimal('0')


@dataclass(frozen=True)
class ProfilInterets2025:
    source: str = ''
    confirme: bool = False
    devise: str = 'CAD'
    compte_conjoint: bool = False
    frais_placement: bool = False
    deja_declares: bool = False


@dataclass(frozen=True)
class Interets2025:
    ligne_12100: Decimal = ZERO
    ligne_130: Decimal = ZERO
    cotisation_fss: Decimal = ZERO
    present: bool = False


def valider_profil_interets_2025(p):
    if not isinstance(p, ProfilInterets2025):
        raise ValueError('Profil intérêts invalide.')
    for nom in ('confirme', 'compte_conjoint', 'frais_placement', 'deja_declares'):
        if type(getattr(p, nom)) is not bool:
            raise ValueError('Les confirmations intérêts doivent être booléennes.')
    if not isinstance(p.source, str) or not isinstance(p.devise, str):
        raise ValueError('Source et devise intérêts doivent être du texte.')
    if p.devise != 'CAD' or p.compte_conjoint or p.frais_placement or p.deja_declares:
        raise ValueError('Intérêts : devise étrangère, compte conjoint, frais ou intérêts déjà déclarés hors périmètre 3A.')
    if p.confirme and not p.source.strip():
        raise ValueError('Justificatif des intérêts obligatoire.')
    return p


def detecter_interets_2025(dossier):
    # T5 19 est déjà couvert par les pensions; ne pas détourner ce parcours.
    return any(d.type_document == 'RL-3' or
               (d.type_document == 'T5' and d.case == '13' and d.valeur_validee != ZERO)
               for d in dossier.donnees_validees)


def consolider_interets_2025(dossier, profil):
    valider_profil_interets_2025(profil)
    if not profil.confirme:
        raise ValueError('Confirmez les intérêts canadiens et les exclusions du Bloc 3A.')
    if dossier.annee_fiscale != 2025 or dossier.province.casefold() not in {'québec', 'quebec'}:
        raise ValueError('Intérêts : dossier Québec 2025 requis.')
    if any(d.type_document not in {'T4', 'RL-1', 'T5', 'RL-3'} for d in dossier.donnees_validees):
        raise ValueError('Intérêts avec autre revenu, T3, T5008 ou prestation : hors périmètre 3A.')
    valeurs = {}
    documents = {t: set() for t in ('T5', 'RL-3')}
    pieces = {p.resolve() for p in dossier.documents}
    if pieces != {d.document.resolve() for d in dossier.donnees_validees}:
        raise ValueError('Chaque pièce doit avoir des données validées; document non traité hors périmètre 3A.')
    for d in dossier.donnees_validees:
        if d.type_document not in documents:
            continue
        cle = (d.type_document, d.case)
        m = d.valeur_validee
        if cle in valeurs:
            raise ValueError('Case intérêts dupliquée; aucune somme implicite de plusieurs feuillets.')
        if d.document.resolve() not in pieces or d.statut not in {STATUT_VALIDE, STATUT_CORRIGE_VALIDE}:
            raise ValueError('Source ou validation intérêts manquante.')
        if (not isinstance(m, Decimal) or not m.is_finite() or m < ZERO
                or m > Decimal('999999999.99') or m != m.quantize(Decimal('.01'))):
            raise ValueError('Montant intérêts invalide : fini, non négatif et au cent près.')
        valeurs[cle] = m
        documents[d.type_document].add(d.document.resolve())
    if any(len(v) != 1 for v in documents.values()) or documents['T5'] & documents['RL-3']:
        raise ValueError('Une seule paire T5/RL-3 distincte est requise.')
    if ('T5', '13') not in valeurs or ('RL-3', 'D') not in valeurs or valeurs['T5', '13'] != valeurs['RL-3', 'D']:
        raise ValueError('T5 13 et RL-3 D obligatoires et égaux, sans double compte.')
    if ('T5', '23') in valeurs and valeurs['T5', '23'] != 1:
        raise ValueError('T5 23 : seul un particulier titulaire unique est couvert, hors périmètre sinon.')
    if any(m and cle not in {('T5', '13'), ('T5', '23'), ('RL-3', 'D')} for cle, m in valeurs.items()):
        raise ValueError('Dividendes, rente, gain, revenu/impôt étranger ou autre case hors périmètre 3A.')
    montant = valeurs['T5', '13']
    return Interets2025(montant, montant, cotisation_fss_prestations_2025(montant), True)


def appliquer_interets_2025(revenu, p):
    return replace(revenu,
        revenu_total_federal=revenu.revenu_total_federal + p.ligne_12100,
        revenu_net_federal=revenu.revenu_net_federal + p.ligne_12100,
        revenu_imposable_federal=revenu.revenu_imposable_federal + p.ligne_12100,
        revenu_total_quebec=revenu.revenu_total_quebec + p.ligne_130,
        revenu_net_quebec=revenu.revenu_net_quebec + p.ligne_130,
        revenu_imposable_quebec=revenu.revenu_imposable_quebec + p.ligne_130,
        profil='Intérêts canadiens ordinaires Québec 2025',
        limitations=('Intérêts canadiens ordinaires appariés T5/RL-3, avec ou sans emploi; autres placements exclus.',))


def lignes_resume_interets_2025(p, profil):
    if not p.present:
        return []
    f = formater_montant_fiscal
    return ['', 'INTÉRÊTS CANADIENS 2025 — BLOC 3A',
        f'Justificatif : {profil.source}',
        f'T5 13 / fédéral 12100 : {f(p.ligne_12100)}',
        f'RL-3 D / Québec 130 : {f(p.ligne_130)}',
        'Montants appariés : revenu total, net et imposable augmentés une seule fois par juridiction.',
        f'FSS 446 sur les intérêts : {f(p.cotisation_fss)}; aucune retenue ajoutée.',
        'CAD, titulaire unique; sans frais, revenus étrangers, dividendes, gains ou intérêts déjà déclarés.',
        'Intérêts sans feuillet, comptes communs et combinaisons avec pensions/prestations hors périmètre.']
