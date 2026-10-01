"""7C : autonome pur, annexes U/R, S8 Québec partie 3 et S10 partie A 2025.

Les lignes monétaires réutilisées sont quantifiées au cent, conformément à la
mécanique ligne par ligne retenue pour ces formulaires. Le traitement des demi-
cents suit la convention logicielle générale, pas une règle fiscale spécifique.
"""
from dataclasses import dataclass, fields, is_dataclass, replace
from datetime import date
from decimal import Decimal

from .tax_multiple_jurisdictions_2025 import bloquer_estimation_interprovinciale_2025
from .tax_rules_2025 import arrondir_cent, deduction_travailleur_quebec_2025
from .tax_self_employment_2025 import calculer_entreprises_2025

ZERO = Decimal('0')
D = Decimal
CONFIRMATIONS_7C = {
    'residence_quebec_annee': 'Résident du Canada et du Québec toute l’année 2025',
    'autonome_pur': 'Revenus exclusivement autonomes 7B, sans emploi ni autre revenu',
    'sans_rente_choix_invalidite': 'Aucune rente RRQ/RPC, invalidité RRQ/RPC, cessation ou révocation de choix',
    'sans_rpc_le35': 'Aucun RPC, aucune ligne 96/96.1/96.2, aucun LE-35',
    'sans_facultatif': 'Aucune cotisation facultative RRQ ni adhésion AE autonome',
    'sans_exoneration': 'Aucun revenu exonéré, aucune déduction 293/297, aucune ressource intermédiaire/familiale',
    'sans_acomptes': 'Aucun acompte provisionnel ni autre paiement ou retenue à rapprocher',
    'sans_autres_profils': 'Aucun autre crédit ou déduction demandé; prime au travail et ACT non demandées',
    'couverture_privee_annee': 'Assurance médicaments privée admissible toute l’année; aucune cotisation RAMQ',
    'valide_par_comptable': 'Périmètre annuel, date de naissance et pièces validés par le comptable',
}


@dataclass(frozen=True)
class ProfilCotisationsAutonomes2025:
    activer: bool = False
    naissance: str = ''
    source: str = ''
    residence_quebec_annee: bool = False
    autonome_pur: bool = False
    sans_rente_choix_invalidite: bool = False
    sans_rpc_le35: bool = False
    sans_facultatif: bool = False
    sans_exoneration: bool = False
    sans_acomptes: bool = False
    sans_autres_profils: bool = False
    couverture_privee_annee: bool = False
    valide_par_comptable: bool = False


def valider_profil_7c(p):
    if not isinstance(p, ProfilCotisationsAutonomes2025):
        raise ValueError('7C : profil invalide.')
    for n in ('activer', *CONFIRMATIONS_7C):
        if type(getattr(p,n)) is not bool:
            raise ValueError('7C : booléen strict requis : '+n)
    if not isinstance(p.naissance,str) or not isinstance(p.source,str):
        raise ValueError('7C : naissance et source textuelles requises.')
    if not p.activer:
        if p != ProfilCotisationsAutonomes2025():
            raise ValueError('7C : faits présents dans un profil désactivé.')
        return p
    try:
        naissance=date.fromisoformat(p.naissance)
    except ValueError as exc:
        raise ValueError('7C : date de naissance ISO requise.') from exc
    if naissance.isoformat()!=p.naissance or not date(1961,1,1)<=naissance<=date(2006,12,31):
        raise ValueError('7C : 18 ans acquis avant 2025 et moins de 65 ans fin 2025 requis; prorata exclu.')
    if not p.source.strip():
        raise ValueError('7C : source comptable obligatoire.')
    for n,t in CONFIRMATIONS_7C.items():
        if not getattr(p,n): raise ValueError('7C : confirmation obligatoire : '+t)
    return p


def profil_7c_vers_json(p):
    valider_profil_7c(p)
    return {f.name:getattr(p,f.name) for f in fields(p)}


def profil_7c_depuis_json(v):
    if v is None: return ProfilCotisationsAutonomes2025()
    if not isinstance(v,dict) or set(v)-{f.name for f in fields(ProfilCotisationsAutonomes2025)}:
        raise ValueError('7C : profil JSON invalide.')
    return valider_profil_7c(ProfilCotisationsAutonomes2025(**v))


@dataclass(frozen=True)
class CotisationsAutonomes2025:
    revenu_net: Decimal
    rrq_445: Decimal
    rrq_deduction_248: Decimal
    rqap_439: Decimal
    rqap_deduction_248: Decimal
    deduction_22200: Decimal
    deduction_22300: Decimal
    base_31000: Decimal
    base_31215: Decimal
    fss_446: Decimal
    lignes_u: tuple[tuple[str, Decimal], ...]
    lignes_s8: tuple[tuple[str, Decimal], ...]
    lignes_r: tuple[tuple[str, Decimal], ...]


def calculer_cotisations_autonomes_2025(dossier, profil):
    bloquer_estimation_interprovinciale_2025(dossier)
    if dossier.biens_locatifs:
        raise ValueError('7C : combinaison avec location 7D hors périmètre.')
    valider_profil_7c(profil)
    if not profil.activer:
        raise ValueError('7C : profil annuel non activé; garde-fou 7B conservé.')
    if dossier.annee_fiscale!=2025 or dossier.province.casefold() not in ('québec','quebec'):
        raise ValueError('7C : Québec 2025 uniquement.')
    if any((d.type_document=='T4' and d.case in ('16','16A') and d.valeur_validee)
           or (d.case in ('96','96.1','96.2') and d.valeur_validee) for d in dossier.donnees_validees):
        raise ValueError('7C : RPC / lignes 96, 96.1, 96.2 : LE-35 requis, hors périmètre.')
    if dossier.donnees_validees or dossier.documents:
        raise ValueError('7C : autonome pur seulement; emploi + autonome et autres feuillets exclus.')
    entreprises=calculer_entreprises_2025(dossier.entreprises)
    if not entreprises: raise ValueError('7C : entreprise 7B requise.')
    net=sum((e.revenu_net for e in entreprises),ZERO)
    # Annexe U partie C, pages 4 à 7. Lignes exclues explicitement nulles.
    u={}
    def ligne(n,v):
        u[n]=arrondir_cent(D(v))
        return u[n]
    for n in ('31','31.2','32','34','35','41'): ligne(n,ZERO)
    ligne('30',net);ligne('31.1',u['30']+u['31']);ligne('31.3',max(u['31.1']-u['31.2'],ZERO))
    ligne('33',u['31.3']+u['32']);ligne('36',u['34']+u['35']);ligne('38',u['36']/D('.064'))
    ligne('39',3500);ligne('40',u['38']+u['39']);ligne('42',max(u['40']-u['41'],ZERO))
    ligne('43',max(u['33']-u['42'],ZERO));ligne('44',71300);ligne('45',u['39'])
    ligne('46',max(u['44']-u['45'],ZERO));ligne('47',u['38']);ligne('47.1',max(u['46']-u['47'],ZERO))
    ligne('47.2',min(u['43'],u['47.1']));ligne('48',u['47.2']*D('.128'))
    ligne('53',81200);ligne('54',u['44']);ligne('55',u['53']-u['54'])
    ligne('56',u['41']);ligne('57',u['44']);ligne('58',max(u['56']-u['57'],ZERO))
    ligne('59',min(u['55'],u['58']));ligne('60',u['59']*D('.04'));ligne('61',min(u['35'],u['60']))
    ligne('62',u['61']/D('.04'));ligne('63',u['35']);ligne('64',u['61']);ligne('65',max(u['63']-u['64'],ZERO))
    ligne('66',u['65']/D('.04'));ligne('67',u['34']);ligne('68',min(u['33']+u['41'],D(71300)))
    ligne('69',u['39']);ligne('70',max(u['68']-u['69'],ZERO));ligne('71',min(u['70']*D('.064'),D('4339.20')))
    ligne('72',max(u['67']-u['71'],ZERO));ligne('73',u['72']/D('.04'))
    ligne('74',u['62']+u['66']+u['73'] if u['73'] else ZERO)
    ligne('75',u['40']+u['74']);ligne('76',min(u['41'],u['75']));ligne('77',u['33']+u['76'])
    ligne('78',u['44']);ligne('79',max(u['77']-u['78'],ZERO));ligne('80',u['74'])
    ligne('81',max(u['79']-u['80'],ZERO));ligne('82',u['55']);ligne('83',u['74'])
    ligne('84',max(u['82']-u['83'],ZERO));ligne('85',u['33']);ligne('86',u['74'])
    ligne('87',u['41']);ligne('88',u['44']);ligne('89',max(u['87']-u['88'],ZERO))
    ligne('90',max(u['86']-u['89'],ZERO));ligne('91',max(u['85']-u['90'],ZERO))
    ligne('92',min(u['81'],u['84'],u['91']));ligne('93',u['92']*D('.08'))
    ligne('93.1',u['48']);ligne('94',u['93']+u['93.1']);ligne('95.1',u['71'])
    ligne('95.2',u['41']);ligne('95.3',u['33']);ligne('95.4',u['95.2']+u['95.3'])
    ligne('95.5',min(u['53'],u['95.4']));ligne('95.6',u['44']);ligne('95.7',max(u['95.5']-u['95.6'],ZERO))
    ligne('95.8',u['95.7']*D('.04'));ligne('95',u['95.1']+u['95.8']);ligne('96',u['36'])
    ligne('97',max(u['95']-u['96'],ZERO));ligne('98',u['97']*2);ligne('99',min(u['94'],u['98']))
    ligne('100',u['48']);ligne('101',u['100']*D('.421875'));ligne('102',u['48'])
    ligne('103',u['102']*D('.156250'));ligne('104',u['34']);ligne('105',u['104']*D('.156250'))
    ligne('106',u['33']);ligne('107',u['41']);ligne('108',u['106']+u['107']);ligne('109',u['39'])
    ligne('110',max(u['108']-u['109'],ZERO));ligne('111',min(u['46'],u['110']));ligne('112',u['111']*D('.01'))
    ligne('113',min(u['105'],u['112']));ligne('114',u['101']+u['103']+u['113'])
    ligne('115',min(u['93'],u['99']));ligne('116',u['34']);ligne('116.1',u['111'])
    ligne('116.2',u['116.1']*D('.064'));ligne('116.3',max(u['116']-u['116.2'],ZERO))
    ligne('116.4',u['35']);ligne('116.5',u['116.3']+u['116.4']);ligne('117.5',u['41'])
    ligne('117.6',u['33']);ligne('117.7',u['117.5']+u['117.6']);ligne('117.8',u['44'])
    ligne('117.9',max(u['117.7']-u['117.8'],ZERO));ligne('118',u['53']);ligne('118.1',u['44'])
    ligne('118.2',max(u['118']-u['118.1'],ZERO));ligne('118.3',min(u['117.9'],u['118.2']))
    ligne('122',u['118.3']*D('.04'));ligne('123',min(u['116.5'],u['122']))
    ligne('124',u['114']+u['115']+u['123'])
    # Annexe 8 Québec, partie 3. Crédit 31000 distinct de la déduction 22200.
    s={'1':u['30'],'2':ZERO};s['3']=s['1']+s['2'];s['4']=min(D(81200),s['3']);s['5']=D(71300)
    s['6']=max(s['4']-s['5'],ZERO);s['7']=max(s['4']-s['6'],ZERO);s['8']=D(3500)
    s['9']=max(s['7']-s['8'],ZERO);s['10']=arrondir_cent(s['9']*D('.108'))
    s['11']=arrondir_cent(s['9']*D('.02'));s['12']=arrondir_cent(s['6']*D('.08'))
    s['13']=s['11']+s['12'];s['14']=arrondir_cent(s['10']*D('.5'));s['15']=s['13']+s['14']
    # Annexe R A et annexe 10 A : aucun revenu d'emploi dans ce profil.
    r={'10':net,'11':ZERO,'12':net,'13':D(98000),'14':ZERO,'16':ZERO,'18':ZERO,'20':D(98000)}
    r['22']=min(r['12'],r['20'])
    r['24']=arrondir_cent(r['22']*D('.00878')) if net>=D(2000) else ZERO
    r['26']=arrondir_cent(r['24']*D('.43736'))
    # Annexe F 43/43.1 : déductions autonomes, sans déduire la ligne 201.
    from .tax_employment_insurance_2025 import cotisation_fss_prestations_2025
    assiette=max(net-r['26']-u['101']-u['103']-u['115'],ZERO)
    return CotisationsAutonomes2025(net,u['99'],u['124'],r['24'],r['26'],s['15'],r['26'],
        s['14'],r['24']-r['26'],cotisation_fss_prestations_2025(assiette),
        tuple(u.items()),tuple(s.items()),tuple(r.items()))


def verifier_options_annuelles_7c(options):
    """Aucune option existante non vide ne peut être ignorée en autonome pur."""
    for nom, valeur in options.items():
        if nom == 'dossier' or valeur is None or valeur is False:
            continue
        if is_dataclass(valeur) and valeur == type(valeur)():
            continue
        raise ValueError('7C : combinaison non validée avec '+nom+
                         '; crédits et déductions supplémentaires hors périmètre, dont 6I/ACT.')


def appliquer_revenu_autonome_2025(revenu, c):
    fed=arrondir_cent(c.revenu_net-c.deduction_22200-c.deduction_22300)
    travailleur=deduction_travailleur_quebec_2025(c.revenu_net)
    qc=arrondir_cent(c.revenu_net-travailleur-c.rrq_deduction_248-c.rqap_deduction_248)
    return replace(revenu, revenu_total_federal=c.revenu_net, revenu_net_federal=fed,
        revenu_imposable_federal=max(fed,ZERO), revenu_total_quebec=c.revenu_net,
        revenu_net_quebec=qc, revenu_imposable_quebec=max(qc,ZERO),
        deduction_travailleur_quebec=travailleur, deduction_rrq_quebec=c.rrq_deduction_248,
        deduction_autonome_22200=c.deduction_22200, deduction_autonome_22300=c.deduction_22300,
        deduction_rqap_autonome_quebec=c.rqap_deduction_248,
        profil='Autonome pur Québec 2025 (7C)', limitations=('Profil autonome pur validé; autres revenus et crédits exclus.',))


def lignes_annuelles_autonomes_2025(e, *, detail=False):
    c=e.cotisations_autonomes
    if c is None: return ()
    p=e.dossier.profil_cotisations_autonomes
    r=e.revenu;f=e.federal;q=e.quebec;x=e.rapprochement
    lignes=['ESTIMATION ANNUELLE AUTONOME PURE 2025 - 7C',f'Client : {e.dossier.client}',
        'Validation comptable obligatoire. Aucune déclaration transmise.',
        f'Naissance : {p.naissance}; source : {p.source}',
        'Résidence Québec toute année; sans emploi, RPC, rente, choix ni cotisation facultative.',
        'Couverture médicaments privée annuelle confirmée; aucun acompte ou retenue.',
        'Aucun autre crédit ou déduction demandé, notamment prime au travail / ACT.',
        'Lignes monétaires quantifiées au cent avant réutilisation.',
        'Demi-cents : convention générale du logiciel, pas règle fiscale propre aux annexes.']
    for a in calculer_entreprises_2025(e.dossier.entreprises):
        b=a.faits
        lignes += ['',f'Entreprise : {b.reference} ({b.nature}); exercice {b.debut} au {b.fin}',
            f'Source : {b.source}',f'Brut {b.revenu_brut:.2f} - bureau {b.frais_bureau:.2f} - comptabilité {b.frais_comptables:.2f} = net {a.revenu_net:.2f} $',
            f'Fédéral {"13500" if b.nature=="entreprise" else "13700"}; Québec annexe L / 164 : {a.revenu_net:.2f} $']
    lignes += ['',f'Revenus totaux fédéral / Québec : {c.revenu_net:.2f} $',
        f'RRQ payable Québec 445 = U99 : {c.rrq_445:.2f} $',
        f'Déduction RRQ Québec 248 = U124 : {c.rrq_deduction_248:.2f} $',
        f'RQAP payable Québec 439 = R24 : {c.rqap_439:.2f} $',
        f'Déduction RQAP Québec 248 = R26 : {c.rqap_deduction_248:.2f} $',
        f'Total ligne 248 : {c.rrq_deduction_248+c.rqap_deduction_248:.2f} $',
        f'Déduction fédérale RRQ autonome 22200 : {c.deduction_22200:.2f} $',
        f'Déduction fédérale RQAP autonome 22300 : {c.deduction_22300:.2f} $',
        f'Base crédit fédéral RRQ 31000 : {c.base_31000:.2f} $',
        f'Base crédit fédéral RQAP 31215 : {c.base_31215:.2f} $',
        'Lignes emploi 30800 / 22215 : 0.00 $; aucun report RRQ fédéral 42100.',
        f'Revenu net fédéral = total - 22200 - 22300 : {r.revenu_net_federal:.2f} $',
        f'Déduction travailleur Québec 201 : {r.deduction_travailleur_quebec:.2f} $',
        f'Revenu Québec 275 = total - 201 - 248 : {r.revenu_net_quebec:.2f} $',
        f'Impôt fédéral brut : {f.impot_brut:.2f} $; crédits non remboursables : {f.credits_federaux_complets.total_credits_ligne_35000:.2f} $',
        f'Impôt fédéral de base : {f.impot_federal_de_base:.2f} $',
        f'Abattement Québec : {x.abattement_quebec:.2f} $',
        f'Impôt Québec : {q.impot_quebec_preliminaire:.2f} $',
        f'FSS Québec 446 (annexe F après déductions autonomes) : {c.fss_446:.2f} $',
        '445 + 439 + 446 ajoutées UNE fois, après impôts; déductions distinctes en amont.',
        f'Total impôts et cotisations : {x.impot_total_preliminaire:.2f} $',
        f'{x.resultat} : {max(x.solde_estime,x.remboursement_estime):.2f} $',
        'Sources 2025 : TP-1.D.U partie C p.4-7; TP-1.D.R partie A; TP-1.D.F.',
        'Fédéral : 5005-S8 partie 3 p.5-6; 5005-S10 partie A p.1.']
    if detail:
        for nom, valeurs in [('U',c.lignes_u),('S8 partie 3',c.lignes_s8),('R partie A',c.lignes_r)]:
            lignes += ['', 'LIGNES MONÉTAIRES '+nom]
            lignes += [f'{nom} ligne {n} : {v:.2f} $' for n,v in valeurs]
        lignes += ['S10 A : 7 = R24; 9 = R26; 10 = ligne 7 - ligne 9.',
                   'FSS : assiette = net - R26 - U101 - U103 - U115.']
    return tuple(lignes)
