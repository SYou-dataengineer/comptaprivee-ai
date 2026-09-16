"""Bloc 2D : exemples indépendants de la feuille fédérale 2025 et annexe F."""
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
import json
import fitz
import pytest
from src.comptaprivee.tax_old_age_security_2025 import (
    PrestationsPsv2025, consolider_prestations_psv_2025, appliquer_recuperation_psv_2025,
    lignes_resume_psv_2025,
)
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025, formater_estimation_fiscale_2025
from src.comptaprivee.tax_document_classifier import classifier_document_fiscal
from src.comptaprivee.tax_field_extractor import extraire_cases_fiscales
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from src.comptaprivee.tax_drug_insurance_2025 import AssuranceMedicamentsQuebec2025
from tests.test_tax_estimation_2025 import _dossier_52000, _validee
from tests.test_tax_rpp_2025 import profil_rpa
from tests.test_tax_union_dues_integration_2025 import _reer_5000, _cotisations_600
from tests.test_tax_age_retirement_integration_2025 import _profil_age_retraite
from tests.test_tax_federal_age_pension_integration_2025 import _profil_age_federal, _profil_pension_federal


def dossier_psv(pension='10000', supplements='2000', emploi=True):
    d = _dossier_52000()
    if not emploi:
        d = replace(d, documents=(), donnees_validees=())
    cases = {'18':pension, '19':pension, '20':'0', '21':supplements, '22':'1500', '23':'500'}
    return replace(d, documents=d.documents+(Path('T4A(OAS).pdf'),),
        donnees_validees=d.donnees_validees+tuple(_validee(Path('T4A(OAS).pdf'),'T4A(OAS)',c,v) for c,v in cases.items()))


def modifier(d,c,v):
    return replace(d, donnees_validees=tuple(x for x in d.donnees_validees if (x.type_document,x.case)!=('T4A(OAS)',c))+(_validee(Path('T4A(OAS).pdf'),'T4A(OAS)',c,v),))


def calcul(d=None, **kwargs):
    return calculer_estimation_fiscale_2025(d or dossier_psv(), psv_confirme=True, **kwargs)


@pytest.mark.parametrize('nom',['T4A(OAS).pdf','T4AOAS_2025.pdf','t4a-oas.pdf'])
def test_classification(nom):
    assert classifier_document_fiscal(nom).type_document == 'T4A(OAS)'
    assert classifier_document_fiscal('scan.pdf','T4A(OAS)').type_document == 'T4A(OAS)'


@pytest.mark.parametrize('autre',['T4A(P)','T4E','RL-2','T4'])
def test_classification_ambigue(autre):
    assert classifier_document_fiscal('scan.pdf','T4A(OAS) '+autre).type_document == 'À vérifier'


@pytest.mark.parametrize('case',['18','19','20','21','22','23'])
@pytest.mark.parametrize('montant',['1234.56','-1234.56'])
def test_extraction(case,montant):
    valeurs=extraire_cases_fiscales('T4A(OAS)',f'Box {case} Description {montant}','scan.pdf')
    assert len(valeurs)==1
    assert (valeurs[0].case,valeurs[0].valeur)==(case,Decimal(montant))


def test_case_vide_et_montants_francais():
    valeurs=extraire_cases_fiscales('T4A(OAS)','Case 21\nCase 22 1 500,00\nCase 23 500,00','scan.pdf')
    assert {x.case:x.valeur for x in valeurs}=={'22':Decimal('1500'),'23':Decimal('500')}


@pytest.mark.parametrize('v',['NaN','sNaN','Infinity','-1','0.001','1000000000'])
def test_montants_invalides(v):
    with pytest.raises(ValueError,match='Montant'):
        calcul(modifier(dossier_psv(),'21',v))


@pytest.mark.parametrize('confirme',[False,None,1,'true'])
def test_confirmation(confirme):
    with pytest.raises(ValueError):
        calculer_estimation_fiscale_2025(dossier_psv(),psv_confirme=confirme)


@pytest.mark.parametrize('case',['20','99'])
def test_remboursements_et_autres_cases_refuses(case):
    with pytest.raises(ValueError,match='hors périmètre'):
        calcul(modifier(dossier_psv(),case,'1'))


def test_sources_doublons_annee_statut_et_manquants():
    d=dossier_psv()
    for invalide in (
        replace(d,annee_fiscale=2024), replace(d,province='Ontario'),
        replace(d,documents=d.documents[:-1]),
        replace(d,donnees_validees=d.donnees_validees+(d.donnees_validees[-1],)),
        replace(d,donnees_validees=d.donnees_validees[:-1]+(replace(d.donnees_validees[-1],statut='À vérifier'),)),
        replace(d,donnees_validees=tuple(x for x in d.donnees_validees if x.case!='18')),
        modifier(d,'19','10001'),
        replace(d,documents=d.documents+(Path('autre.pdf'),),donnees_validees=d.donnees_validees+(_validee(Path('autre.pdf'),'T4A(OAS)','18','100'),)),
    ):
        with pytest.raises(ValueError):
            calcul(invalide)
    with pytest.raises(ValueError,match='T4A'):
        calcul(_dossier_52000())


@pytest.mark.parametrize('t',['T4E','RL-6','T4A(P)','RL-2','T4A','T4RIF'])
def test_profils_mixtes_refuses(t):
    d=dossier_psv()
    d=replace(d,donnees_validees=d.donnees_validees+(_validee(Path('autre.pdf'),t,'14','100'),))
    with pytest.raises(ValueError,match='hors périmètre'):
        calcul(d)


@pytest.mark.parametrize('pension,supplements',[('10000','0'),('10000','12000'),('0','12000'),('0','0')])
def test_sans_emploi_net_distinct_imposable(pension,supplements):
    e=calcul(dossier_psv(pension,supplements,False))
    assert e.base.nombre_t4==e.base.nombre_rl1==0
    assert e.revenu.revenu_total_federal==e.revenu.revenu_total_quebec==Decimal(pension)+Decimal(supplements)
    assert e.revenu.revenu_net_federal==e.revenu.revenu_net_quebec==Decimal(pension)+Decimal(supplements)
    assert e.revenu.revenu_imposable_federal==e.revenu.revenu_imposable_quebec==Decimal(pension)
    assert e.federal.montant_canadien_emploi==0
    assert e.revenu.deduction_travailleur_quebec==0
    assert e.prestations_psv.recuperation==0
    assert e.rapprochement.retenues_totales==2000
    assert e.rapprochement.impot_total_preliminaire==e.rapprochement.impot_federal_apres_abattement+e.rapprochement.impot_quebec_preliminaire


def test_emploi_deductions_et_retenues_sans_double_compte():
    e=calcul()
    assert e.revenu.revenu_total_federal==e.revenu.revenu_total_quebec==64000
    assert e.revenu.revenu_net_federal==63515
    assert e.revenu.revenu_net_quebec==62095
    assert e.revenu.revenu_imposable_federal==61515
    assert e.revenu.revenu_imposable_quebec==60095
    assert e.rapprochement.retenue_federale==9000
    assert e.rapprochement.retenue_quebec==6700
    autre=calcul(cotisations_rpa=profil_rpa(),ajustement_reer=_reer_5000(),cotisations_syndicales=_cotisations_600())
    assert autre.revenu.revenu_net_federal==54915
    assert autre.revenu.revenu_net_quebec==54095
    assert autre.revenu.revenu_imposable_federal==52915
    assert autre.revenu.revenu_imposable_quebec==52095


@pytest.mark.parametrize('net,pension,supplements,recup,deduction',[
 ('93453.99','10000','2000','0','2000'),('93454','10000','2000','0','2000'),
 ('93454.03','10000','2000','0','2000'),('93454.04','10000','2000','0.01','2000'),
 ('100000','10000','2000','981.90','2000'),
 ('160120.67','10000','2000','10000','2000'),
 ('166787.33','10000','2000','11000','1000'),
 ('200000','10000','2000','12000','0'),
 ('100000','0','2000','981.90','1018.10'),
 ('200000','0','0','0','0'),
])
def test_feuille_recuperation_seuil_arrondi_plafond(net,pension,supplements,recup,deduction):
    revenu=calcul().revenu
    revenu=replace(revenu,revenu_net_federal=Decimal(net),revenu_imposable_federal=Decimal(net),
        revenu_net_quebec=Decimal(net)-1000,revenu_imposable_quebec=Decimal(net)-1000)
    p=PrestationsPsv2025(pension=Decimal(pension),supplements=Decimal(supplements),present=True)
    r,p=appliquer_recuperation_psv_2025(revenu,p)
    assert p.recuperation==Decimal(recup)
    assert p.deduction_supplements==Decimal(deduction)
    assert r.revenu_net_federal==Decimal(net)-Decimal(recup)
    assert r.revenu_net_quebec==Decimal(net)-1000-Decimal(recup)
    assert r.revenu_imposable_federal==r.revenu_net_federal-Decimal(deduction)
    assert r.revenu_imposable_quebec==r.revenu_net_quebec-Decimal(deduction)


def test_recuperation_apres_deductions_et_sans_abattement():
    # Montant fictif élevé pour exercer le branchement complet, pas une PSV annuelle réaliste.
    d=dossier_psv('45000','0')
    e=calcul(d)
    assert e.prestations_psv.revenu_avant_recuperation==96515
    assert e.prestations_psv.recuperation==Decimal('459.15')
    assert e.revenu.revenu_net_federal==Decimal('96055.85')
    assert e.revenu.revenu_net_quebec==Decimal('94635.85')
    r=e.rapprochement
    assert r.impot_total_preliminaire==r.impot_federal_apres_abattement+r.impot_quebec_preliminaire+Decimal('459.15')
    assert calcul(d,ajustement_reer=_reer_5000()).prestations_psv.recuperation==0


def test_credits_age_utilisent_net_avec_supplements_et_pension_exclue():
    d=dossier_psv('10000','12000',False)
    e=calcul(d,credits_federaux_age_pension=_profil_age_federal(revenu_net_ligne_23600=Decimal('22000')),
        montants_age_retraite=_profil_age_retraite(reclamer_revenus_retraite=False,revenu_ligne_122=Decimal('0'),revenu_familial_net=Decimal('22000')))
    assert e.revenu.revenu_net_federal==22000 and e.revenu.revenu_imposable_federal==10000
    with pytest.raises(ValueError,match='revenu net'):
        calcul(d,credits_federaux_age_pension=_profil_age_federal(revenu_net_ligne_23600=Decimal('10000')))
    with pytest.raises(ValueError,match='361'):
        calcul(d,montants_age_retraite=_profil_age_retraite(revenu_familial_net=Decimal('22000')))
    with pytest.raises(ValueError,match='31400'):
        calcul(d,credits_federaux_age_pension=replace(_profil_pension_federal(),revenu_net_ligne_23600=Decimal('22000')))


def test_ramq_avec_supplements_refusee():
    with pytest.raises(ValueError,match='RAMQ publique'):
        calcul(assurance_medicaments=AssuranceMedicamentsQuebec2025(type_couverture='public'))


def test_stockage_recalcul_et_ancien_json(tmp_path):
    d=dossier_psv(); e=calcul(d)
    p=sauvegarder_dossier_fiscal(d,estimation=e,destination=tmp_path/'d.json')
    charge=charger_dossier_fiscal(p)
    assert charge.psv_confirme and not charge.rrq_rpc_confirme and not charge.ae_confirme and not charge.rqap_confirme
    assert calcul(charge.dossier)==e
    with pytest.raises(ValueError,match='diffère'):
        sauvegarder_dossier_fiscal(d,estimation=e,psv_confirme=False,destination=p)
    contenu=json.loads(p.read_text(encoding='utf-8')); del contenu['psv_confirme']
    p.write_text(json.dumps(contenu),encoding='utf-8')
    charge=charger_dossier_fiscal(p)
    assert not charge.psv_confirme
    with pytest.raises(ValueError,match='Confirmez'):
        calculer_estimation_fiscale_2025(charge.dossier)


@pytest.mark.parametrize('v',[None,1,'true',[],{}])
def test_confirmation_json_invalide(tmp_path,v):
    p=sauvegarder_dossier_fiscal(dossier_psv(),psv_confirme=True,destination=tmp_path/'d.json')
    contenu=json.loads(p.read_text(encoding='utf-8')); contenu['psv_confirme']=v
    p.write_text(json.dumps(contenu),encoding='utf-8')
    with pytest.raises(ValueError,match='booléen'):
        charger_dossier_fiscal(p)


@pytest.mark.parametrize('autre',['ae_confirme','rqap_confirme','rrq_rpc_confirme'])
def test_confirmations_concurrentes_refusees(tmp_path,autre):
    d=dossier_psv()
    with pytest.raises(ValueError,match='hors périmètre'):
        calcul(d,**{autre:True})
    with pytest.raises(ValueError,match='hors périmètre'):
        sauvegarder_dossier_fiscal(d,psv_confirme=True,destination=tmp_path/'a.json',**{autre:True})
    p=sauvegarder_dossier_fiscal(d,psv_confirme=True,destination=tmp_path/'a.json')
    contenu=json.loads(p.read_text(encoding='utf-8')); contenu[autre]=True
    p.write_text(json.dumps(contenu),encoding='utf-8')
    with pytest.raises(ValueError):
        charger_dossier_fiscal(p)


@pytest.mark.parametrize('emploi',[True,False])
def test_resume_trace_pdf(tmp_path,emploi):
    e=calcul(dossier_psv(emploi=emploi))
    texte=formater_estimation_fiscale_2025(e)
    for mot in ('11300','14600','25000','23500','42200','43700','114','148','295','250 point 3','451','446','rétroactivité'):
        assert mot in texte
    trace=construire_trace_calcul_fiscal_2025(e)
    assert [l.ordre for l in trace.lignes]==list(range(1,len(trace.lignes)+1))
    montants={l.libelle:l.montant for l in trace.lignes}
    assert montants['PSV 11300']==10000
    assert montants['Suppléments déductibles 25000']==montants['Suppléments déductibles 295']==2000
    assert montants['Revenu net fédéral 23600']==e.revenu.revenu_net_federal
    assert montants['FSS PSV 446']==0
    p=exporter_rapport_fiscal_pdf_2025(e,tmp_path/'psv.pdf')
    with fitz.open(p) as pdf:
        texte='\n'.join(page.get_text() for page in pdf)
        for mot in ('T4A(OAS)','FSS Québec 446','Sans rétroactivité','23500 / 42200','25000 / Québec 295'):
            assert mot in texte
        for page in pdf:
            for x0,y0,x1,y1,*_ in page.get_text('blocks'):
                assert 0<=x0<x1<=page.rect.width
                assert 0<=y0<y1<=page.rect.height


def test_cases_facultatives_absentes_et_apercu_sans_fausse_recuperation():
    d=dossier_psv()
    d=replace(d,donnees_validees=tuple(x for x in d.donnees_validees if x.type_document!='T4A(OAS)' or x.case=='18'))
    p=consolider_prestations_psv_2025(d,True)
    assert p.supplements==p.retenue_federale==p.retenue_quebec==0
    assert 'à calculer' in '\n'.join(lignes_resume_psv_2025(p,calcul_effectue=False))


def test_limites_existantes_preservees():
    with pytest.raises(ValueError,match='34990'):
        calcul(credits_federaux_age_pension=_profil_age_federal(revenu_net_ligne_23600=Decimal('63515')))
    with pytest.raises(ValueError,match='hors profil'):
        calcul(dossier_psv('180000','0',False))


def test_recuperation_psv_avec_salaire_90000_et_pension_8000():
    d=dossier_psv('8000','0')
    cases={('T4','14'):'90000',('T4','17'):'4339.20',('T4','17A'):'396',
        ('T4','18'):'860.67',('T4','24'):'65700',('T4','26'):'81200',
        ('T4','55'):'444.60',('T4','56'):'90000',
        ('RL-1','A'):'90000',('RL-1','B.A'):'4339.20',('RL-1','B.B'):'396',
        ('RL-1','C'):'860.67',('RL-1','G'):'81200',('RL-1','H'):'444.60',('RL-1','I'):'90000'}
    sources={x.type_document:x.document for x in d.donnees_validees}
    d=replace(d,donnees_validees=tuple(x for x in d.donnees_validees if (x.type_document,x.case) not in cases)+tuple(
        _validee(sources[t],t,c,v) for (t,c),v in cases.items()))
    e=calcul(d)
    # RRQ supplémentaire : (71 300 - 3 500) × 1 % + 396 = 1 074 $.
    # RRQ supplémentaire : (71 300 - 3 500) × 1 % + 396 = 1 074 $.
    assert e.prestations_psv.revenu_avant_recuperation==96926
    assert e.prestations_psv.recuperation==Decimal('520.80')
    assert e.revenu.revenu_net_federal==Decimal('96405.20')
    assert e.revenu.revenu_net_quebec==Decimal('94985.20')
    r=e.rapprochement
    assert r.impot_total_preliminaire==r.impot_federal_apres_abattement+r.impot_quebec_preliminaire+Decimal('520.80')
    assert calcul(d,ajustement_reer=_reer_5000()).prestations_psv.recuperation==0
