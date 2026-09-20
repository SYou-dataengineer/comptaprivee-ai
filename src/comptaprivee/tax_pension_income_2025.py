"""Bloc 2E : pensions domestiques ordinaires, profil simple validé 2025."""
from dataclasses import dataclass, replace
from decimal import Decimal
from .tax_employment_insurance_2025 import cotisation_fss_prestations_2025
from .tax_field_validation import STATUT_VALIDE, STATUT_CORRIGE_VALIDE
from .tax_field_extractor import formater_montant_fiscal
from .tax_federal_age_pension_2025 import CreditsFederauxAgePension2025
from .tax_age_retirement_2025 import MontantsAgeRetraite2025

ZERO = Decimal('0')
# Nature validée, feuillet fédéral, case principale, contrepartie Québec.
NATURES_PENSIONS = {
    'RPA': ('T4A', '016', 'RL-2', 'A'),
    'RENTE': ('T4A', '024', 'RL-2', 'B'),
    'VARIABLE': ('T4A', '133', 'RL-2', 'A'),
    'VIAGERE_VARIABLE': ('T4A', '133', 'RL-2', 'A'),
    'RPAC': ('T4A', '194', 'RL-2', 'B'),
    'FERR': ('T4RIF', '16', 'RL-2', 'B'),
    'T3_RPA': ('T3', '31', 'RL-16', 'D'),
    'T5_RENTE': ('T5', '19', 'RL-2', 'B'),
}
TYPES_PENSIONS = {'T4A', 'T4RIF', 'T3', 'T5', 'RL-16'}

@dataclass(frozen=True)
class ProfilPensions2025:
    nature: str = ''
    age_31_decembre: int | None = None
    source_age: str = ''
    confirme: bool = False
    deces_conjoint: bool = False
    revenu_etranger: bool = False

@dataclass(frozen=True)
class RevenusPensions2025:
    revenu: Decimal = ZERO
    ligne_11500: Decimal = ZERO
    ligne_13000: Decimal = ZERO
    ligne_12100: Decimal = ZERO
    ligne_122: Decimal = ZERO
    admissible_federal: Decimal = ZERO
    admissible_quebec: Decimal = ZERO
    retenue_federale: Decimal = ZERO
    retenue_quebec: Decimal = ZERO
    cotisation_fss: Decimal = ZERO
    source: str = ''
    present: bool = False


def valider_profil_pensions_2025(p):
    if not isinstance(p, ProfilPensions2025):
        raise ValueError('Profil pensions invalide.')
    for nom in ('confirme', 'deces_conjoint', 'revenu_etranger'):
        if type(getattr(p, nom)) is not bool:
            raise ValueError('Les confirmations pensions doivent être des booléens.')
    if not isinstance(p.nature, str) or not isinstance(p.source_age, str):
        raise ValueError('Nature et source âge pensions invalides.')
    if p.age_31_decembre is not None and (type(p.age_31_decembre) is not int or not 18 <= p.age_31_decembre <= 120):
        raise ValueError('Âge pensions au 31 décembre 2025 : entier de 18 à 120 requis.')
    if p.deces_conjoint or p.revenu_etranger:
        raise ValueError('Pensions : décès du conjoint et revenus étrangers hors périmètre.')
    if p.confirme and (p.nature not in NATURES_PENSIONS or p.age_31_decembre is None or not p.source_age.strip()):
        raise ValueError('Pensions : nature, âge au 31 décembre et source âge obligatoires.')
    return p


def consolider_pensions_2025(dossier, profil=ProfilPensions2025()):
    valider_profil_pensions_2025(profil)
    if not profil.confirme:
        raise ValueError('Confirmez le profil pensions : nature, âge et exclusions après revue complète des feuillets.')
    if dossier.annee_fiscale != 2025 or dossier.province.casefold() not in {'québec', 'quebec'}:
        raise ValueError('Les pensions exigent un dossier Québec 2025.')
    t, c, tq, cq = NATURES_PENSIONS[profil.nature]
    if any(d.type_document not in {'T4', 'RL-1', t, tq} for d in dossier.donnees_validees):
        raise ValueError('Pensions : plusieurs natures, AE/RQAP/RRQ/PSV ou autres feuillets hors périmètre.')
    donnees = [d for d in dossier.donnees_validees if d.type_document in {t, tq}]
    docs = {ty:{d.document.resolve() for d in donnees if d.type_document==ty} for ty in (t,tq)}
    if len(docs[t])!=1 or len(docs[tq])!=1 or docs[t]&docs[tq]:
        raise ValueError(f'Un seul {t} et un seul {tq} distinct et apparié sont requis.')
    valeurs={}; pieces={p.resolve() for p in dossier.documents}
    for d in donnees:
        case = d.case.zfill(3) if t == 'T4A' and d.type_document == t and d.case.isdigit() else d.case
        cle=(d.type_document,case)
        if cle in valeurs:
            raise ValueError('Case pensions dupliquée : '+str(cle))
        if d.document.resolve() not in pieces or d.statut not in {STATUT_VALIDE,STATUT_CORRIGE_VALIDE}:
            raise ValueError('Source ou validation comptable pensions manquante.')
        m=d.valeur_validee
        if not isinstance(m,Decimal) or not m.is_finite() or m<ZERO or m>Decimal('999999999.99') or m!=m.quantize(Decimal('.01')):
            raise ValueError('Montant pensions invalide : fini, non négatif et au cent près requis.')
        valeurs[cle]=m
    def case(ty,ca): return valeurs.get((ty,ca),ZERO)
    if (t,c) not in valeurs or (tq,cq) not in valeurs or case(t,c)!=case(tq,cq):
        raise ValueError('Cases principales pensions obligatoires et montants fédéral/Québec égaux, sans double compte.')
    autorisees={t:{c},tq:{cq}}
    retenue={'T4A':'022','T4RIF':'28'}.get(t)
    if retenue: autorisees[t].add(retenue)
    if tq=='RL-2': autorisees[tq].add('J')
    if t=='T5' and (t,'23') in valeurs:
        # Code bénéficiaire administratif, maintenant extrait avec les intérêts 3A.
        if case(t,'23') != 1:
            raise ValueError('T5 23 : bénéficiaire autre que particulier unique hors périmètre pensions.')
        autorisees[t].add('23')
    if t=='T3':
        autorisees[t].add('26')
        if (t,'26') not in valeurs or case(t,'26')!=case(t,'31'):
            raise ValueError('T3 : 26 doit égaler 31; autres revenus de fiducie hors périmètre.')
    if t=='T4RIF':
        autorisees[t].add('24');autorisees[tq].add('B-1')
        if case(t,'24')>case(t,c) or case(tq,'B-1')>case(tq,cq):
            raise ValueError('Excédent FERR supérieur au paiement total.')
        if (t,'24') in valeurs and (tq,'B-1') in valeurs and case(t,'24')!=case(tq,'B-1'):
            raise ValueError('Excédents T4RIF 24 et RL-2 B-1 incohérents.')
    for (ty,ca),m in valeurs.items():
        if ca not in autorisees[ty] and m:
            raise ValueError(f'{ty} case {ca} : transfert, décès, revenu étranger ou autre montant hors périmètre pensions.')
    revenu=case(t,c)
    admissible = profil.age_31_decembre>=65 or profil.nature in {'RPA','VIAGERE_VARIABLE','T3_RPA'}
    ligne='11500' if admissible else ('12100' if t=='T5' else '13000')
    return RevenusPensions2025(revenu=revenu,**{'ligne_'+ligne:revenu},ligne_122=revenu,
        admissible_federal=revenu if admissible else ZERO,admissible_quebec=revenu,
        retenue_federale=case(t,retenue) if retenue else ZERO,retenue_quebec=case(tq,'J') if tq=='RL-2' else ZERO,
        cotisation_fss=cotisation_fss_prestations_2025(revenu),source=f'{t} {c} / {tq} {cq}',present=True)


def appliquer_pensions_2025(revenu,p):
    noms=('revenu_total_federal','revenu_net_federal','revenu_imposable_federal','revenu_total_quebec','revenu_net_quebec','revenu_imposable_quebec')
    return replace(revenu,**{n:getattr(revenu,n)+p.revenu for n in noms},profil='Pensions domestiques ordinaires Québec 2025')


def credit_pension_federal_depuis_feuillets(p,profil,revenu):
    if not p.admissible_federal: return CreditsFederauxAgePension2025()
    return CreditsFederauxAgePension2025(reclamer_montant_pension=True,
        age_65_plus_31_decembre_2025=profil.age_31_decembre>=65,revenu_net_ligne_23600=revenu.revenu_net_federal,
        revenu_pension_admissible=p.admissible_federal,resident_canada_toute_annee=True,aucune_regle_deces=True,
        aucun_fractionnement_pension=True,aucun_transfert_conjoint=True,revenu_pension_admissible_confirme=True,
        valide_par_comptable=True,source_pension=p.source,source_age=profil.source_age)


def credit_retraite_quebec_depuis_feuillets(p,revenu):
    if not p.admissible_quebec: return MontantsAgeRetraite2025()
    return MontantsAgeRetraite2025(reclamer_revenus_retraite=True,revenu_ligne_122=p.admissible_quebec,
        revenu_familial_net=revenu.revenu_net_quebec,aucun_conjoint_31_decembre_2025=True,
        resident_quebec_canada_toute_annee=True,aucun_montant_personne_vivant_seule=True,
        revenus_retraite_admissibles_confirmes=True,revenus_non_admissibles_exclus=True,
        valide_par_comptable=True,source_retraite=p.source)


def lignes_resume_pensions_2025(p,profil):
    if not p.present:return []
    f=formater_montant_fiscal
    return ['', 'PENSIONS, FERR ET RENTES 2025 - FEUILLETS VALIDÉS',
        f'Nature : {profil.nature}; âge au 31 décembre : {profil.age_31_decembre}; source : {profil.source_age}',
        f'Feuillets appariés : {p.source}',
        f'Revenus fédéraux 11500 / 13000 / 12100 : {f(p.ligne_11500)} / {f(p.ligne_13000)} / {f(p.ligne_12100)}',
        f'Revenu Québec 122 : {f(p.ligne_122)}',
        f'Revenu admissible fédéral 31400 / Québec 361 : {f(p.admissible_federal)} / {f(p.admissible_quebec)}',
        f'Retenues pensions 43700 / 451 : {f(p.retenue_federale)} / {f(p.retenue_quebec)}',
        f'FSS pensions 446 (assiette {f(p.revenu)}) : {f(p.cotisation_fss)}',
        'Admissibilité distincte des crédits; plafonds et réduction appliqués ensuite. Aucun double compte des feuillets.',
        'Sans décès, revenu étranger, transfert, fractionnement, rétroactivité ni autre revenu hors profil.']
