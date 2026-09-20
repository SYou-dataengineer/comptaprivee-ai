"""Bloc 2F : exemples indépendants, exclusions et chaîne applicative."""
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
import json
import fitz
import pytest
from src.comptaprivee.tax_rrsp_withdrawals_2025 import *
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025, formater_estimation_fiscale_2025
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
from src.comptaprivee.tax_document_classifier import classifier_document_fiscal
from src.comptaprivee.tax_field_extractor import extraire_cases_fiscales
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from tests.test_tax_estimation_2025 import _dossier_52000, _validee
from tests.test_tax_pension_income_2025 import modifier


def profil_retraits(nature='REER_ORDINAIRE'):
    return ProfilRetraits2025(nature,'Feuillet complet et T3012A approuvé si requis',True)


def dossier_retraits(nature='REER_ORDINAIRE',montant='20000',emploi=False):
    d=_dossier_52000()
    if not emploi:d=replace(d,documents=(),donnees_validees=())
    t,c,cq=NATURES_RETRAITS[nature]
    cases=[(t,c,montant),('RL-2',cq,montant),(t,'30' if t=='T4RSP' else '022','1500'),('RL-2','J','2000')]
    return replace(d,documents=d.documents+(Path(t+'.pdf'),Path('RL-2.pdf')),
        donnees_validees=d.donnees_validees+tuple(_validee(Path(ty+'.pdf'),ty,ca,v) for ty,ca,v in cases))


def calcul(nature='REER_ORDINAIRE',dossier=None,**kw):
    return calculer_estimation_fiscale_2025(dossier or dossier_retraits(nature),profil_retraits=profil_retraits(nature),**kw)


@pytest.mark.parametrize('nature',NATURES_RETRAITS)
@pytest.mark.parametrize('emploi',[False,True])
def test_revenus_deductions_retenues_fss(nature,emploi):
    e=calcul(nature,dossier_retraits(nature,emploi=emploi));r=e.retraits
    remboursement=nature=='COTISATIONS_INUTILISEES'
    assert r.ligne_12900==(0 if nature=='FORFAIT_RPA' else 20000)
    assert r.ligne_13000==(20000 if nature=='FORFAIT_RPA' else 0)
    assert r.ligne_154==20000
    assert r.ligne_23200==r.ligne_250_6==(20000 if remboursement else 0)
    assert e.revenu.revenu_total_federal==(72000 if emploi else 20000)
    assert e.revenu.revenu_net_federal==(51515 if emploi else 0)+(0 if remboursement else 20000)
    assert e.revenu.revenu_net_quebec==(50095 if emploi else 0)+(0 if remboursement else 20000)
    assert r.cotisation_fss==(0 if remboursement else Decimal('18.70'))
    assert e.rapprochement.retenues_totales==(17200 if emploi else 3500)
    assert not e.credits_federaux_age_pension.reclamer_montant_pension
    assert not e.montants_age_retraite.reclamer_revenus_retraite


@pytest.mark.parametrize('case',['16','18','20','22','24','25','26','27','28','30','34','35','36','37','40'])
@pytest.mark.parametrize('valeur',['123.45','-123.45'])
def test_extraction_t4rsp(case,valeur):
    d=extraire_cases_fiscales('T4RSP',f'Case {case} {valeur}','scan.pdf')
    assert [(x.case,x.valeur) for x in d]==[(case,Decimal(valeur))]


def test_classification_et_case_vide():
    assert classifier_document_fiscal('T4RSP.pdf').type_document=='T4RSP'
    assert classifier_document_fiscal('scan.pdf','T4RSP').type_document=='T4RSP'
    assert classifier_document_fiscal('scan.pdf','T4RSP T4').type_document=='À vérifier'
    assert [(x.case,x.valeur) for x in extraire_cases_fiscales('T4RSP','Case 22\nCase 30 100.00','scan.pdf')]==[('30',Decimal('100'))]


@pytest.mark.parametrize('t,c',[('T4RSP',c) for c in ['16','18','20','24','25','26','27','28','34','35','36','37','40']]+[('RL-2',c) for c in ['A','B','D','E','F','G','H','I','K','L','O','C-1','C-3','C-9']])
def test_exclusions(t,c):
    with pytest.raises(ValueError,match='hors périmètre'):
        calcul(dossier=modifier(dossier_retraits(),t,c,'100'))


@pytest.mark.parametrize('m',['-1','NaN','Infinity','0.001','1000000000'])
def test_montant_invalide(m):
    with pytest.raises(ValueError):calcul(dossier=modifier(dossier_retraits(),'T4RSP','22',m))


def test_sources_doublons_appariement_confirmation():
    d=dossier_retraits()
    for faux in [replace(d,documents=d.documents[:-1]),replace(d,donnees_validees=d.donnees_validees*2),
                 modifier(d,'RL-2','C','1'),replace(d,donnees_validees=d.donnees_validees[1:]),
                 replace(d,donnees_validees=tuple(replace(x,statut='À vérifier') for x in d.donnees_validees)),
                 replace(d,annee_fiscale=2024),replace(d,province='Ontario')]:
        with pytest.raises(ValueError):calcul(dossier=faux)
    with pytest.raises(ValueError,match='Confirmez'):calculer_estimation_fiscale_2025(d)


@pytest.mark.parametrize('nom',['ae_confirme','rqap_confirme','rrq_rpc_confirme','psv_confirme'])
def test_concurrence(nom):
    with pytest.raises(ValueError):calcul(**{nom:True})


@pytest.mark.parametrize('nature',NATURES_RETRAITS)
def test_stockage_trace_pdf(tmp_path,nature):
    e=calcul(nature);p=sauvegarder_dossier_fiscal(e.dossier,estimation=e,destination=tmp_path/'d.json')
    charge=charger_dossier_fiscal(p)
    assert calculer_estimation_fiscale_2025(charge.dossier,profil_retraits=charge.profil_retraits)==e
    assert '12900 / 13000' in formater_estimation_fiscale_2025(e)
    trace=construire_trace_calcul_fiscal_2025(e)
    assert next(x.montant for x in trace.lignes if x.libelle=='Retraits 154')==20000
    assert [x.ordre for x in trace.lignes]==list(range(1,len(trace.lignes)+1))
    pdf=exporter_rapport_fiscal_pdf_2025(e,tmp_path/'r.pdf')
    with fitz.open(pdf) as doc:
        assert 'RETRAITS REER' in ''.join(page.get_text() for page in doc)
        for page in doc:
            for x0,y0,x1,y1,*_ in page.get_text('blocks'):
                assert 0<=x0<x1<=page.rect.width and 0<=y0<y1<=page.rect.height
    raw=json.loads(p.read_text(encoding='utf-8'));del raw['profil_retraits'];p.write_text(json.dumps(raw),encoding='utf-8')
    assert not charger_dossier_fiscal(p).profil_retraits.confirme


@pytest.mark.parametrize('raw',[None,[],True,{'confirme':1},{'nature':'AUTRE'},{'source':3},{'inconnu':True}])
def test_json_invalide(tmp_path,raw):
    p=sauvegarder_dossier_fiscal(dossier_retraits(),destination=tmp_path/'d.json')
    contenu=json.loads(p.read_text(encoding='utf-8'));contenu['profil_retraits']=raw;p.write_text(json.dumps(contenu),encoding='utf-8')
    with pytest.raises(ValueError):charger_dossier_fiscal(p)


@pytest.mark.parametrize('t,c',[('T4','66'),('T4','67'),('T4A','106')])
def test_forfaits_exclus_detectes_sans_confirmation(t,c):
    d=modifier(_dossier_52000(),t,c,'100')
    with pytest.raises(ValueError):calculer_estimation_fiscale_2025(d)
