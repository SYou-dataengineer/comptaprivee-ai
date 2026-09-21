"""Bloc 3B, sources et périmètre : docs/moteur_fiscal_2025.md.

Une seule source économique; aucun calcul d'intérêts à partir d'un taux.
Les montants proviennent exclusivement des données validées du dossier.
"""
from datetime import date
from decimal import Decimal

from .tax_employment_insurance_2025 import cotisation_fss_prestations_2025
from .tax_field_validation import STATUT_VALIDE, STATUT_CORRIGE_VALIDE
from .tax_field_extractor import formater_montant_fiscal

NATURES_INTERETS_DOCUMENTES = ('BANQUE', 'REMBOURSEMENT_IMPOT', 'CPG_ANNUEL', 'T3_INTERETS')
ZERO = Decimal('0')


def valider_nature_interets_documentes_2025(p):
    for nom in ('nature', 'identifiant_source', 'date_debut', 'date_fin'):
        if not isinstance(getattr(p, nom), str):
            raise ValueError('Nature, identifiant et dates des intérêts doivent être du texte.')
    if p.nature == 'T5_RL3':
        if any((p.identifiant_source, p.date_debut, p.date_fin, p.echeancier_confirme, p.ventilation_confirmee)):
            raise ValueError('Le profil 3A ne peut pas contenir des données 3B.')
        return
    if p.nature not in NATURES_INTERETS_DOCUMENTES:
        raise ValueError('Nature des intérêts hors périmètre 3B.')
    if not p.confirme:
        return
    if not p.identifiant_source.strip():
        raise ValueError('Identifiant stable de la source économique obligatoire.')
    try:
        debut, fin = date.fromisoformat(p.date_debut), date.fromisoformat(p.date_fin)
    except ValueError as erreur:
        raise ValueError('Dates ISO AAAA-MM-JJ requises pour les intérêts.') from erreur
    if debut.isoformat() != p.date_debut or fin.isoformat() != p.date_fin or debut.year != 2025 or fin.year != 2025 or debut > fin:
        raise ValueError('Période 2025 ordonnée obligatoire; autre période hors périmètre 3B.')
    if p.nature == 'CPG_ANNUEL' and (p.date_debut != '2025-01-01' or p.date_fin != '2025-12-31' or not p.echeancier_confirme):
        raise ValueError('CPG : année complète janvier-décembre, échéancier et méthode Québec confirmés requis.')
    if p.nature == 'T3_INTERETS' and not p.ventilation_confirmee:
        raise ValueError('T3 : ventilation exclusivement intérêts canadiens du fonds obligatoire.')
    if p.nature != 'CPG_ANNUEL' and p.echeancier_confirme:
        raise ValueError('Confirmation CPG incompatible avec la nature choisie.')
    if p.nature != 'T3_INTERETS' and p.ventilation_confirmee:
        raise ValueError('Confirmation T3 incompatible avec la nature choisie.')


def consolider_interets_documentes_2025(dossier, profil):
    from .tax_interest_income_2025 import Interets2025, valider_profil_interets_2025
    valider_profil_interets_2025(profil)
    if profil.nature not in NATURES_INTERETS_DOCUMENTES:
        raise ValueError('Ce consolidateur exige une nature du Bloc 3B.')
    if not profil.confirme:
        raise ValueError('Confirmez les intérêts documentés 3B.')
    if dossier.annee_fiscale != 2025 or dossier.province.casefold() not in {'québec', 'quebec'}:
        raise ValueError('Intérêts documentés : Québec 2025 requis.')
    fiducie = profil.nature == 'T3_INTERETS'
    types = {'T3', 'RL-16'} if fiducie else {'INTERETS'}
    if any(d.type_document not in types | {'T4', 'RL-1'} for d in dossier.donnees_validees):
        raise ValueError('Cumul 3A/3B, autre source ou prestation hors périmètre 3B; risque de double compte.')
    pieces = {p.resolve() for p in dossier.documents}
    if pieces != {d.document.resolve() for d in dossier.donnees_validees}:
        raise ValueError('Chaque pièce doit avoir des données validées; document non traité.')
    valeurs = {}
    documents = {t:set() for t in types}
    for d in dossier.donnees_validees:
        if d.type_document not in types:
            continue
        cle = d.type_document, d.case
        m = d.valeur_validee
        if cle in valeurs:
            raise ValueError('Source ou case dupliquée : aucune addition implicite.')
        if d.document.resolve() not in pieces or d.statut not in {STATUT_VALIDE, STATUT_CORRIGE_VALIDE}:
            raise ValueError('Source ou validation des intérêts manquante.')
        if not isinstance(m, Decimal) or not m.is_finite() or m < ZERO or m > Decimal('999999999.99') or m != m.quantize(Decimal('.01')):
            raise ValueError('Montant intérêts invalide, fini, non négatif et au cent près requis.')
        valeurs[cle] = m
        documents[d.type_document].add(d.document.resolve())
    if any(len(v) != 1 for v in documents.values()) or (fiducie and documents['T3'] & documents['RL-16']):
        raise ValueError('Une seule source ou paire T3/RL-16 distincte est requise.')
    principales = {('T3','26'), ('RL-16','G')} if fiducie else {('INTERETS',profil.nature)}
    if not principales <= valeurs.keys():
        raise ValueError('Montants documentés obligatoires manquants pour la nature choisie.')
    montants = {valeurs[c] for c in principales}
    if len(montants) != 1:
        raise ValueError('T3 26 et RL-16 G doivent être égaux; aucune estimation de ventilation.')
    if any(m and c not in principales for c,m in valeurs.items()):
        raise ValueError('Autres revenus, montants déjà déclarés ou autre case hors périmètre 3B.')
    montant = montants.pop()
    return Interets2025(ligne_12100=ZERO if fiducie else montant, ligne_130=montant,
        cotisation_fss=cotisation_fss_prestations_2025(montant), present=True,
        ligne_13000=montant if fiducie else ZERO)


def lignes_resume_interets_documentes_2025(p, profil):
    f = formater_montant_fiscal
    return ['', 'INTÉRÊTS DOCUMENTÉS 2025 — BLOC 3B',
        f'Nature : {profil.nature}; source économique : {profil.identifiant_source}',
        f'Période : {profil.date_debut} au {profil.date_fin}',
        f'Justificatif : {profil.source}',
        f'Intérêts directs / fédéral 12100 : {f(p.ligne_12100)}',
        f'T3 26 exclusivement intérêts / fédéral 13000 : {f(p.ligne_13000)}',
        f'Québec 130 : {f(p.ligne_130)}; FSS 446 : {f(p.cotisation_fss)}',
        'Une inclusion par juridiction; aucune majoration, aucun crédit de dividendes ni retenue ajoutée.',
        *(['CPG : année civile complète, échéancier et méthode Québec confirmés; aucune période déjà déclarée.'] if profil.nature == 'CPG_ANNUEL' else []),
        *(['T3 : ventilation confirmée, intérêts canadiens uniquement; T3/RL-16 comptés une seule fois.'] if profil.nature == 'T3_INTERETS' else []),
        'Exclus : cumul T5/RL-3, sources multiples, frais, attribution, compte conjoint, devise, décès et cas complexes.']
