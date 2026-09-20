from dataclasses import replace
from decimal import Decimal as D
import json
import fitz
import pytest
from src.comptaprivee.tax_pension_splitting_2025 import *
from src.comptaprivee.tax_pension_splitting_storage import *
from src.comptaprivee.tax_report_pdf_2025 import exporter_fractionnement_pdf_2025
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_fractionnement_2025


def choix():
    return ChoixFractionnement2025(
        ConjointPension2025('CEDANT-FICTIF',65,D('50000'),D('50000'),D('5000'),D('6000'),'T4A/RL-2 et âge revus',True),
        ConjointPension2025('BENEFICIAIRE-FICTIF',64,D('30000'),D('30000'),D('3000'),D('2000'),'T4A/RL-2 et âge revus',True),
        D('10000'),D('5000'),D('1000'),True)


def test_exemple_independant_et_conservation():
    r=calculer_fractionnement_2025(choix());c,b=r.cedant,r.beneficiaire
    assert c.ligne_21000==b.ligne_11600==10000
    assert c.ligne_245==b.ligne_123==5000
    assert (c.revenu_total_federal,c.revenu_net_federal)==(50000,40000)
    assert (b.revenu_total_federal,b.revenu_net_federal)==(40000,40000)
    assert (c.revenu_total_quebec,c.revenu_net_quebec)==(50000,45000)
    assert (b.revenu_total_quebec,b.revenu_net_quebec)==(35000,35000)
    assert c.retenue_43700+b.retenue_43700==8000
    assert c.retenue_quebec+b.retenue_quebec==8000
    assert r.retenue_federale_transferee==1000 and r.retenue_quebec_transferee==600
    assert c.montant_30100==9028 and b.montant_30100==0
    assert c.montant_31400==b.montant_31400==2000
    assert c.montant_361+b.montant_361==r.montant_361_couple==D('3737.87')
    assert (c.impot_federal,b.impot_federal)==(D('1554.96'),D('2648.03'))
    assert (c.impot_quebec,b.impot_quebec)==(D('3560.06'),D('1916.76'))
    assert c.fss_446==b.fss_446==150


@pytest.mark.parametrize('f,q',[('0','0'),('10000','0'),('0','10000'),('10000','10000'),('20000','15000')])
def test_choix_independants(f,q):
    r=calculer_fractionnement_2025(replace(choix(),montant_federal=D(f),montant_quebec=D(q)))
    assert r.cedant.revenu_net_federal+r.beneficiaire.revenu_net_federal==80000
    assert r.cedant.revenu_net_quebec+r.beneficiaire.revenu_net_quebec==80000
    assert r.cedant.retenue_43700+r.beneficiaire.retenue_43700==8000


def test_age_distinct_federal_quebec():
    p=choix();p=replace(p,cedant=replace(p.cedant,age=64),montant_quebec=D('0'),montant_361_cedant=D('0'))
    r=calculer_fractionnement_2025(p);assert r.cedant.ligne_21000==10000 and r.cedant.ligne_245==0
    with pytest.raises(ValueError,match='65 ans'):calculer_fractionnement_2025(replace(p,montant_quebec=D('1')))


@pytest.mark.parametrize('role',['cedant','beneficiaire'])
@pytest.mark.parametrize('champ,v',[('confirme',False),('confirme',1),('age',None),('age',True),('age',64.5),('age',17),('age',121),('identifiant',''),('source',''),('rl2_a',D('1')),('t4a_022',D('-1')),('rl2_j',D('NaN'))])
def test_donnees_conjoints_refusees(role,champ,v):
    p=choix();p=replace(p,**{role:replace(getattr(p,role),**{champ:v})})
    with pytest.raises(ValueError):calculer_fractionnement_2025(p)


@pytest.mark.parametrize('champ,v',[('montant_federal',D('25000.01')),('montant_quebec',D('25000.01')),('montant_federal',D('-1')),('montant_federal',D('0.001')),('montant_quebec',D('Infinity')),('montant_361_cedant',D('4000')),('choix_conjoint_confirme',False),('choix_conjoint_confirme',1),('annee',2024)])
def test_choix_refuse(champ,v):
    with pytest.raises(ValueError):calculer_fractionnement_2025(replace(choix(),**{champ:v}))


def test_identite_et_limites():
    p=choix()
    with pytest.raises(ValueError,match='distincts'):calculer_fractionnement_2025(replace(p,beneficiaire=replace(p.beneficiaire,identifiant=p.cedant.identifiant)))
    with pytest.raises(ValueError,match='34990'):calculer_fractionnement_2025(replace(p,montant_federal=D('25000')))
    p=replace(p,cedant=replace(p.cedant,t4a_016=D('60000'),rl2_a=D('60000')),montant_federal=D('30000'),montant_quebec=D('30000'))
    with pytest.raises(ValueError,match='34990'):calculer_fractionnement_2025(p)


def test_stockage_pdf_trace(tmp_path):
    p=choix();r=calculer_fractionnement_2025(p)
    fichier=sauvegarder_fractionnement_2025(p,tmp_path/'couple.json')
    assert charger_fractionnement_2025(fichier)==p
    assert calculer_fractionnement_2025(charger_fractionnement_2025(fichier))==r
    trace=construire_trace_fractionnement_2025(r)
    assert any('21000' in x and '11600' in x for x in trace)
    pdf=exporter_fractionnement_pdf_2025(r,tmp_path/'couple.pdf')
    with fitz.open(pdf) as doc:
        texte=''.join(page.get_text() for page in doc)
        assert 'CEDANT-FICTIF' in texte and 'BENEFICIAIRE-FICTIF' in texte and '451.3' in texte
        for page in doc:
            for x0,y0,x1,y1,*_ in page.get_text('blocks'):
                assert 0<=x0<x1<=page.rect.width and 0<=y0<y1<=page.rect.height


@pytest.mark.parametrize('modification',[{'schema_fractionnement':2},{'schema_fractionnement':True},{'profil':{}},{'profil':None},{'profil':True}])
def test_json_corrompu(tmp_path,modification):
    p=sauvegarder_fractionnement_2025(choix(),tmp_path/'c.json')
    contenu=json.loads(p.read_text(encoding='utf-8'));contenu.update(modification);p.write_text(json.dumps(contenu),encoding='utf-8')
    with pytest.raises(ValueError):charger_fractionnement_2025(p)


def test_brouillon_sans_resultat(tmp_path):
    p=ChoixFractionnement2025();f=sauvegarder_fractionnement_2025(p,tmp_path/'b.json')
    assert charger_fractionnement_2025(f)==p
    with pytest.raises(ValueError):calculer_fractionnement_2025(charger_fractionnement_2025(f))


@pytest.mark.parametrize('montant',['0.01','1234.56','9999.99','17374.99'])
def test_arrondis_retenues_conservent_les_totaux(montant):
    p=choix();p=replace(p,montant_federal=D(montant),montant_quebec=D(montant),
        cedant=replace(p.cedant,t4a_022=D('4321.09'),rl2_j=D('5432.10')))
    r=calculer_fractionnement_2025(p)
    assert r.cedant.retenue_43700+r.beneficiaire.retenue_43700==D('7321.09')
    assert r.cedant.retenue_quebec+r.beneficiaire.retenue_quebec==D('7432.10')
    assert r.cedant.revenu_net_federal+r.beneficiaire.revenu_net_federal==80000
    assert r.cedant.revenu_net_quebec+r.beneficiaire.revenu_net_quebec==80000


def test_repartition_annexe_b_unique_deux_ages():
    p=choix();p=replace(p,beneficiaire=replace(p.beneficiaire,age=65))
    r=calculer_fractionnement_2025(p)
    # 2 x 3906 + 2 x 3470 - (80000 - 42090) x 18,75 %, arrondi.
    assert r.montant_361_couple==D('7643.87')
    assert r.cedant.montant_361+r.beneficiaire.montant_361==D('7643.87')
    assert r.beneficiaire.montant_30100==9028
