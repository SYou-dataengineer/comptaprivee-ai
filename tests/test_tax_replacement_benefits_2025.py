"""2H : exemples indépendants, frontières net/imposable et refus explicites."""
from dataclasses import replace
from decimal import Decimal as D
from pathlib import Path
import json
import fitz
import pytest
from src.comptaprivee.tax_replacement_benefits_2025 import *
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025, formater_estimation_fiscale_2025
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
from src.comptaprivee.tax_document_classifier import classifier_document_fiscal
from src.comptaprivee.tax_field_extractor import extraire_cases_fiscales
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from tests.test_tax_estimation_2025 import _dossier_52000, _validee
from tests.test_tax_pension_income_2025 import modifier


def profil_remplacement(nature='CNESST'):
    return ProfilRemplacement2025(nature,'Feuillets courants complets et exclusions revus',True)


def dossier_remplacement(nature='CNESST',montant='5000',emploi=False):
    d=_dossier_52000()
    if not emploi:d=replace(d,documents=(),donnees_validees=())
    c,cq=NATURES_REMPLACEMENT[nature]
    cases=[('RL-5',cq,montant)] if nature=='SAAQ' else [('T5007',c,montant),('RL-5',cq,montant)]
    if nature in {'CNESST','SAAQ'}:cases.append(('RL-5','M','2000'))
    pieces=(Path('RL-5.pdf'),) if nature=='SAAQ' else (Path('T5007.pdf'),Path('RL-5.pdf'))
    return replace(d,documents=d.documents+pieces,
        donnees_validees=d.donnees_validees+tuple(_validee(Path(t+'.pdf'),t,c,v) for t,c,v in cases))


def calcul(nature='CNESST',dossier=None,**kw):
    return calculer_estimation_fiscale_2025(dossier or dossier_remplacement(nature),profil_remplacement=profil_remplacement(nature),**kw)


@pytest.mark.parametrize('nature',NATURES_REMPLACEMENT)
@pytest.mark.parametrize('emploi',[False,True])
def test_net_imposable_et_redressement(nature,emploi):
    e=calcul(nature,dossier_remplacement(nature,emploi=emploi));r=e.remplacement
    c= nature=='CNESST'; s=nature=='SAAQ'; indemnites=c or s
    assert r.ligne_14400==(5000 if c else 0)
    assert r.ligne_14500==(0 if indemnites else 5000)
    assert r.ligne_25000==(0 if s else 5000)
    assert r.ligne_147==(0 if indemnites else 5000)
    assert r.ligne_148==r.ligne_295==(5000 if indemnites else 0)
    assert r.ligne_358==(2000 if indemnites else 0)
    assert e.revenu.revenu_total_federal==(52000 if emploi else 0)+(0 if s else 5000)
    assert e.revenu.revenu_net_federal==(51515 if emploi else 0)+(0 if s else 5000)
    assert e.revenu.revenu_imposable_federal==(51515 if emploi else 0)
    assert e.revenu.revenu_net_quebec==(55095 if emploi else 5000)
    assert e.revenu.revenu_imposable_quebec==(50095 if emploi else 0)+(0 if indemnites else 5000)
    assert e.quebec.montant_personnel_base==18571
    assert e.quebec.credit_personnel_base==(D('2319.94') if indemnites else D('2599.94'))
    assert e.rapprochement.retenues_totales==(13700 if emploi else 0)
    if emploi and indemnites:
        reference=calculer_estimation_fiscale_2025(_dossier_52000())
        assert e.quebec.impot_quebec_preliminaire-reference.quebec.impot_quebec_preliminaire==280
        assert e.federal.impot_federal_de_base==reference.federal.impot_federal_de_base


@pytest.mark.parametrize('ty,c',[('T5007','10'),('T5007','11')]+[('RL-5',c) for c in 'ABCDEHKMOP'])
@pytest.mark.parametrize('v',['123.45','-123.45'])
def test_extraction(ty,c,v):
    assert [(x.case,x.valeur) for x in extraire_cases_fiscales(ty,f'Case {c} {v}','scan.pdf')]==[(c,D(v))]


@pytest.mark.parametrize('ty',['T5007','RL-5'])
def test_classification(ty):
    assert classifier_document_fiscal(ty+'.pdf').type_document==ty
    assert classifier_document_fiscal('scan.pdf',ty).type_document==ty
    assert classifier_document_fiscal('scan.pdf',ty+' T4').type_document=='À vérifier'


@pytest.mark.parametrize('c',list('ABDEFGHIJKLNOP')+['Q1','Q2','Q3','Q4'])
def test_cases_hors_perimetre(c):
    with pytest.raises(ValueError,match='hors périmètre'):calcul(dossier=modifier(dossier_remplacement(),'RL-5',c,'1'))


@pytest.mark.parametrize('v',['-1','NaN','Infinity','0.001','1000000000'])
def test_montants_invalides(v):
    with pytest.raises(ValueError):calcul(dossier=modifier(dossier_remplacement(),'RL-5','C',v))


def test_m_obligatoire_et_plafond():
    d=dossier_remplacement()
    with pytest.raises(ValueError,match='case M'):calcul(dossier=replace(d,donnees_validees=d.donnees_validees[:-1]))
    with pytest.raises(ValueError,match='plafond'):calcul(dossier=modifier(d,'RL-5','M','16713.91'))
    for v in ['0','16713.90']:
        assert calcul(dossier=modifier(d,'RL-5','M',v)).remplacement.ligne_358==D(v)


def test_sources_doublons_appariement_confirmation():
    d=dossier_remplacement()
    for faux in [replace(d,documents=d.documents[:-1]),replace(d,donnees_validees=d.donnees_validees*2),
                 modifier(d,'RL-5','C','1'),replace(d,donnees_validees=d.donnees_validees[1:]),
                 replace(d,donnees_validees=tuple(replace(x,statut='À vérifier') for x in d.donnees_validees)),
                 replace(d,annee_fiscale=2024),replace(d,province='Ontario')]:
        with pytest.raises(ValueError):calcul(dossier=faux)
    with pytest.raises(ValueError,match='Confirmez'):calculer_estimation_fiscale_2025(d)


@pytest.mark.parametrize('nom',['ae_confirme','rqap_confirme','rrq_rpc_confirme','psv_confirme'])
def test_concurrence(nom):
    with pytest.raises(ValueError):calcul(**{nom:True})


@pytest.mark.parametrize('nature',['SAAQ_DECES','RETRAIT_PREVENTIF','AUTRES'])
def test_nature_non_couverte(nature):
    with pytest.raises(ValueError,match='hors périmètre'):valider_profil_remplacement_2025(profil_remplacement(nature))


@pytest.mark.parametrize('nature',NATURES_REMPLACEMENT)
def test_stockage_trace_pdf(tmp_path,nature):
    e=calcul(nature);p=sauvegarder_dossier_fiscal(e.dossier,estimation=e,destination=tmp_path/'d.json')
    charge=charger_dossier_fiscal(p)
    assert calculer_estimation_fiscale_2025(charge.dossier,profil_remplacement=charge.profil_remplacement)==e
    assert 'Déduction 25000' in formater_estimation_fiscale_2025(e)
    trace=construire_trace_calcul_fiscal_2025(e)
    assert next(x.montant for x in trace.lignes if x.libelle=='Prestations 25000')==(0 if nature=='SAAQ' else 5000)
    pdf=exporter_rapport_fiscal_pdf_2025(e,tmp_path/'r.pdf')
    with fitz.open(pdf) as doc:
        assert 'PRESTATIONS DE REMPLACEMENT' in ''.join(page.get_text() for page in doc)
        for page in doc:
            for x0,y0,x1,y1,*_ in page.get_text('blocks'):
                assert 0<=x0<x1<=page.rect.width and 0<=y0<y1<=page.rect.height
    raw=json.loads(p.read_text(encoding='utf-8'));del raw['profil_remplacement'];p.write_text(json.dumps(raw),encoding='utf-8')
    assert not charger_dossier_fiscal(p).profil_remplacement.confirme


@pytest.mark.parametrize('champ,v',[('confirme',1),('confirme','true'),('source',None),('nature',None)])
def test_types_profil(champ,v):
    with pytest.raises(ValueError):valider_profil_remplacement_2025(replace(profil_remplacement(),**{champ:v}))


@pytest.mark.parametrize('raw',[None,[],True,{'confirme':1},{'nature':'SAAQ_DECES'},{'source':3},{'inconnu':True}])
def test_json_invalide(tmp_path,raw):
    p=sauvegarder_dossier_fiscal(dossier_remplacement(),destination=tmp_path/'d.json')
    contenu=json.loads(p.read_text(encoding='utf-8'));contenu['profil_remplacement']=raw;p.write_text(json.dumps(contenu),encoding='utf-8')
    with pytest.raises(ValueError):charger_dossier_fiscal(p)


def test_fss_nul_et_credit_non_remboursable():
    e=calcul(dossier=dossier_remplacement(montant='80000'))
    assert e.revenu.revenu_net_federal==80000
    assert e.revenu.revenu_imposable_federal==0
    assert e.quebec.impot_quebec_preliminaire==0
    assert e.rapprochement.impot_total_preliminaire==0


def test_ramq_publique_refusee():
    from src.comptaprivee.tax_drug_insurance_2025 import AssuranceMedicamentsQuebec2025
    with pytest.raises(ValueError,match='RAMQ publique'):
        calcul(assurance_medicaments=AssuranceMedicamentsQuebec2025(type_couverture='public'))


def test_saaq_refuse_feuillet_federal_et_m_absent():
    d=dossier_remplacement('SAAQ')
    with pytest.raises(ValueError,match='T5007'):
        calcul('SAAQ',modifier(d,'T5007','10','5000'))
    with pytest.raises(ValueError,match='case M'):
        calcul('SAAQ',replace(d,donnees_validees=d.donnees_validees[:-1]))
