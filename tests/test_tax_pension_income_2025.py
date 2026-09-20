"""Bloc 2E : règles d'âge, nature, crédits distincts et feuillets appariés."""
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
import json
import fitz
import pytest
from src.comptaprivee.tax_pension_income_2025 import *
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025, formater_estimation_fiscale_2025
from src.comptaprivee.tax_document_classifier import classifier_document_fiscal
from src.comptaprivee.tax_field_extractor import extraire_cases_fiscales
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from src.comptaprivee.tax_federal_age_pension_2025 import montant_pension_federal_2025
from src.comptaprivee.tax_age_retirement_2025 import montant_revenus_retraite_2025
from tests.test_tax_estimation_2025 import _dossier_52000, _validee
from tests.test_tax_union_dues_integration_2025 import _reer_5000, _cotisations_600
from tests.test_tax_rpp_2025 import profil_rpa


def profil_pensions(nature='RPA',age=64,**kw):
    return ProfilPensions2025(nature,age,'Date de naissance validée',True,**kw)


def dossier_pensions(nature='RPA',montant='20000',emploi=False):
    t,c,tq,cq=NATURES_PENSIONS[nature]
    d=_dossier_52000()
    if not emploi:d=replace(d,documents=(),donnees_validees=())
    cases=[(t,c,montant),(tq,cq,montant)]
    if t=='T4A':cases.append((t,'022','1500'))
    if t=='T4RIF':cases += [(t,'28','1500'),(t,'24','5000'),(tq,'B-1','5000')]
    if t=='T3':cases.append((t,'26',montant))
    if tq=='RL-2':cases.append((tq,'J','2000'))
    return replace(d,documents=d.documents+(Path(t+'.pdf'),Path(tq+'.pdf')),donnees_validees=d.donnees_validees+tuple(_validee(Path(ty+'.pdf'),ty,ca,v) for ty,ca,v in cases))


def modifier(d,t,c,v):
    return replace(d,donnees_validees=tuple(x for x in d.donnees_validees if (x.type_document,x.case)!=(t,c))+(_validee(Path(t+'.pdf'),t,c,v),))


def calcul(nature='RPA',age=64,dossier=None,**kw):
    return calculer_estimation_fiscale_2025(dossier or dossier_pensions(nature),profil_pensions=profil_pensions(nature,age),**kw)


@pytest.mark.parametrize('t',['T4A','T4RIF','T3','T5','RL-16','T4A(P)','T4A(OAS)','RL-2'])
def test_classification_distincte(t):
    assert classifier_document_fiscal(t+'.pdf').type_document==t
    assert classifier_document_fiscal('scan.pdf',t).type_document==t


@pytest.mark.parametrize('texte',['T4A T4RIF','T4A T4A(P)','T3 RL-16','T5 RL-2','T4 T4A'])
def test_classification_ambigue(texte):
    assert classifier_document_fiscal('scan.pdf',texte).type_document=='À vérifier'


@pytest.mark.parametrize('t,c,libelle',[
 ('T4A','016','Case 016'),('T4A','016','Case 16'),('T4A','024','Box 024'),('T4A','133','Code 133'),('T4A','194','Case 194'),
 ('T4RIF','16','Case 16'),('T4RIF','22','Case 22'),('T4RIF','28','Case 28'),('T3','31','Box 31'),('T3','26','Box 26'),
 ('T5','19','Box 19'),('RL-2','A','Case A'),('RL-2','B','Case B'),('RL-2','B-2','Code B-2'),('RL-16','D','Case D')])
@pytest.mark.parametrize('v',['20000.00','-20000.00'])
def test_extraction_signee(t,c,libelle,v):
    donnees=extraire_cases_fiscales(t,libelle+' '+v,'scan.pdf')
    assert [(x.case,x.valeur) for x in donnees]==[(c,Decimal(v))]


def test_case_trois_chiffres_vide_pas_de_capture_suivante():
    d=extraire_cases_fiscales('T4A','Case 016\nCase 194 20 000,00','scan.pdf')
    assert [(x.case,x.valeur) for x in d]==[('194',Decimal('20000'))]


@pytest.mark.parametrize('nature',list(NATURES_PENSIONS))
@pytest.mark.parametrize('age',[64,65])
def test_matrice_age_nature_et_credits(nature,age):
    e=calcul(nature,age);p=e.pensions
    admissible=age>=65 or nature in {'RPA','T3_RPA','VIAGERE_VARIABLE'}
    assert p.ligne_11500==(20000 if admissible else 0)
    assert p.ligne_12100==(20000 if nature=='T5_RENTE' and age<65 else 0)
    assert p.ligne_13000==(20000 if not admissible and nature!='T5_RENTE' else 0)
    assert p.ligne_122==p.admissible_quebec==20000
    assert p.admissible_federal==(20000 if admissible else 0)
    assert montant_pension_federal_2025(e.credits_federaux_age_pension)==(2000 if admissible else 0)
    assert montant_revenus_retraite_2025(e.montants_age_retraite)==3470
    assert e.revenu.revenu_total_federal==e.revenu.revenu_total_quebec==20000
    assert e.revenu.revenu_net_federal==e.revenu.revenu_imposable_quebec==20000
    assert p.cotisation_fss==Decimal('18.70')
    assert e.base.nombre_t4==e.base.nombre_rl1==0 and e.federal.montant_canadien_emploi==0
    assert not e.credits_federaux_age_pension.reclamer_montant_age and not e.montants_age_retraite.reclamer_age


@pytest.mark.parametrize('nature',list(NATURES_PENSIONS))
def test_retenues_et_fss_ajoutes_une_fois(nature):
    e=calcul(nature);p=e.pensions;r=e.rapprochement
    assert r.retenue_federale==(1500 if nature not in {'T3_RPA','T5_RENTE'} else 0)
    assert r.retenue_quebec==(0 if nature=='T3_RPA' else 2000)
    assert r.impot_total_preliminaire==r.impot_federal_apres_abattement+r.impot_quebec_preliminaire+p.cotisation_fss


@pytest.mark.parametrize('age',[None,True,'65',17,121,64.5])
def test_age_invalide(age):
    with pytest.raises(ValueError):calculer_estimation_fiscale_2025(dossier_pensions(),profil_pensions=profil_pensions(age=age))


@pytest.mark.parametrize('nom,v',[('confirme',False),('confirme',1),('confirme','true'),('source_age',''),('nature','INCONNUE'),('deces_conjoint',True),('revenu_etranger',True)])
def test_profil_refuse(nom,v):
    with pytest.raises(ValueError):
        calculer_estimation_fiscale_2025(dossier_pensions(),profil_pensions=replace(profil_pensions(),**{nom:v}))


@pytest.mark.parametrize('v',['NaN','sNaN','Infinity','-1','0.001','1000000000'])
def test_montants_invalides(v):
    with pytest.raises(ValueError,match='Montant'):
        calcul(dossier=modifier(dossier_pensions(),'T4A','016',v))


@pytest.mark.parametrize('nature,t,c',[('RPA','T4A','109'),('RPA','T4A','018'),('RPA','T4A','024'),('FERR','T4RIF','22'),('FERR','T4RIF','18'),('FERR','RL-2','B-2'),('FERR','RL-2','B-3'),('FERR','RL-2','B-4'),('T3_RPA','T3','25'),('T3_RPA','RL-16','F'),('T5_RENTE','T5','13'),('RPA','RL-2','A-1')])
def test_cas_complexes_refuses(nature,t,c):
    with pytest.raises(ValueError,match='hors périmètre'):
        calcul(nature,dossier=modifier(dossier_pensions(nature),t,c,'100'))


def test_t3_26_et_ferr_24_sans_double_compte():
    assert calcul('T3_RPA').pensions.revenu==20000
    assert calcul('FERR').pensions.revenu==20000
    for d,n in [(modifier(dossier_pensions('T3_RPA'),'T3','26','21000'),'T3_RPA'),(modifier(dossier_pensions('FERR'),'T4RIF','24','21000'),'FERR'),(modifier(dossier_pensions('FERR'),'RL-2','B-1','6000'),'FERR')]:
        with pytest.raises(ValueError):calcul(n,dossier=d)


def test_feuillets_sources_statuts_et_appariement():
    d=dossier_pensions()
    for mauvais in [replace(d,annee_fiscale=2024),replace(d,province='Ontario'),replace(d,documents=d.documents[:-1]),
        replace(d,donnees_validees=d.donnees_validees+(d.donnees_validees[0],)),
        replace(d,donnees_validees=d.donnees_validees[:-1]+(replace(d.donnees_validees[-1],statut='À vérifier'),)),
        modifier(d,'RL-2','A','19999'),
        replace(d,donnees_validees=tuple(x for x in d.donnees_validees if x.type_document!='RL-2')),
        modifier(d,'T4A','16','20000'),
        replace(d,documents=d.documents+(Path('autre.pdf'),),donnees_validees=d.donnees_validees+(_validee(Path('autre.pdf'),'T4A','016','1'),))]:
        with pytest.raises(ValueError):calcul(dossier=mauvais)


@pytest.mark.parametrize('t',['T4A(P)','T4A(OAS)','T4E','RL-6','T4RSP','T5'])
def test_autres_revenus_refuses(t):
    d=dossier_pensions();d=replace(d,donnees_validees=d.donnees_validees+(_validee(Path('autre.pdf'),t,'16','1'),))
    with pytest.raises(ValueError,match='hors périmètre'):calcul(dossier=d)


@pytest.mark.parametrize('montant,fss',[('0','0'),('18130','0'),('18131','0.01'),('33130','150'),('63060','150'),('63061','150.01'),('148060','1000')])
def test_bareme_fss(montant,fss):
    p=consolider_pensions_2025(dossier_pensions(montant=montant),profil_pensions())
    assert p.cotisation_fss==Decimal(fss)


def test_salaire_et_deductions_ordinaires():
    d=dossier_pensions(montant='2000',emploi=True)
    e=calcul(dossier=d)
    assert e.revenu.revenu_net_federal==53515 and e.revenu.revenu_net_quebec==52095
    autre=calcul(dossier=d,cotisations_rpa=profil_rpa(),ajustement_reer=_reer_5000(),cotisations_syndicales=_cotisations_600())
    assert autre.revenu.revenu_net_federal==44915 and autre.revenu.revenu_net_quebec==44095
    assert autre.pensions.cotisation_fss==0
    assert e.rapprochement.retenues_totales==17200


def test_profils_credits_doivent_concorder():
    e=calcul()
    for kwargs in [dict(credits_federaux_age_pension=replace(e.credits_federaux_age_pension,revenu_pension_admissible=Decimal('1'))),
        dict(credits_federaux_age_pension=replace(e.credits_federaux_age_pension,age_65_plus_31_decembre_2025=True)),
        dict(credits_federaux_age_pension=replace(e.credits_federaux_age_pension,revenu_net_ligne_23600=Decimal('1'))),
        dict(montants_age_retraite=replace(e.montants_age_retraite,revenu_ligne_122=Decimal('1'))),
        dict(montants_age_retraite=replace(e.montants_age_retraite,deduction_ligne_250_point_4=Decimal('1'))),
        dict(montants_age_retraite=replace(e.montants_age_retraite,revenu_familial_net=Decimal('1')))]:
        with pytest.raises(ValueError):calcul(**kwargs)
    with pytest.raises(ValueError,match='31400'):
        calcul('FERR',credits_federaux_age_pension=e.credits_federaux_age_pension)


def test_limites_existantes_maintenues():
    with pytest.raises(ValueError,match='34990'):calcul(dossier=dossier_pensions(emploi=True))


def test_stockage_recalcul_et_ancien_json(tmp_path):
    e=calcul();p=sauvegarder_dossier_fiscal(e.dossier,estimation=e,destination=tmp_path/'d.json')
    charge=charger_dossier_fiscal(p)
    assert charge.profil_pensions==e.profil_pensions
    assert calculer_estimation_fiscale_2025(charge.dossier,profil_pensions=charge.profil_pensions)==e
    with pytest.raises(ValueError,match='diffère'):sauvegarder_dossier_fiscal(e.dossier,estimation=e,profil_pensions=ProfilPensions2025(),destination=p)
    contenu=json.loads(p.read_text(encoding='utf-8'));del contenu['profil_pensions'];p.write_text(json.dumps(contenu),encoding='utf-8')
    charge=charger_dossier_fiscal(p)
    with pytest.raises(ValueError,match='Confirmez'):calculer_estimation_fiscale_2025(charge.dossier,profil_pensions=charge.profil_pensions)


@pytest.mark.parametrize('v',[None,[],True,{'confirme':1},{'age_31_decembre':'65'},{'inconnu':True},{'revenu_etranger':True}])
def test_json_invalide(tmp_path,v):
    p=sauvegarder_dossier_fiscal(dossier_pensions(),profil_pensions=profil_pensions(),destination=tmp_path/'d.json')
    contenu=json.loads(p.read_text(encoding='utf-8'));contenu['profil_pensions']=v;p.write_text(json.dumps(contenu),encoding='utf-8')
    with pytest.raises(ValueError):charger_dossier_fiscal(p)


@pytest.mark.parametrize('autre',['psv_confirme','ae_confirme','rqap_confirme','rrq_rpc_confirme'])
def test_confirmations_concurrentes(tmp_path,autre):
    with pytest.raises(ValueError,match='hors périmètre'):calcul(**{autre:True})
    with pytest.raises(ValueError,match='hors périmètre'):sauvegarder_dossier_fiscal(dossier_pensions(),profil_pensions=profil_pensions(),destination=tmp_path/'d.json',**{autre:True})


@pytest.mark.parametrize('nature,age',[('RPA',64),('FERR',65),('T5_RENTE',64),('T3_RPA',64)])
def test_resume_trace_pdf(tmp_path,nature,age):
    e=calcul(nature,age);texte=formater_estimation_fiscale_2025(e)
    for mot in ('11500','13000','12100','122','31400','361','43700','451','446','Sans décès'):assert mot in texte
    trace=construire_trace_calcul_fiscal_2025(e)
    assert [l.ordre for l in trace.lignes]==list(range(1,len(trace.lignes)+1))
    assert next(l for l in trace.lignes if l.libelle=='Pensions 122').montant==20000
    assert next(l for l in trace.lignes if l.libelle=='FSS pensions 446').montant==Decimal('18.70')
    p=exporter_rapport_fiscal_pdf_2025(e,tmp_path/'p.pdf')
    with fitz.open(p) as pdf:
        texte='\n'.join(page.get_text() for page in pdf)
        for mot in ('PENSIONS, FERR','31400','FSS pensions','Sans décès'):assert mot in texte
        for page in pdf:
            for x0,y0,x1,y1,*_ in page.get_text('blocks'):
                assert 0<=x0<x1<=page.rect.width and 0<=y0<y1<=page.rect.height
