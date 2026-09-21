"""3C : montants réels/imposables/crédits, FSS, persistance et exclusions."""
from dataclasses import replace
from decimal import Decimal as D
from pathlib import Path
import json
import fitz
import pytest

from src.comptaprivee.tax_dividend_income_2025 import *
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025, formater_estimation_fiscale_2025
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
from src.comptaprivee.tax_field_extractor import extraire_cases_fiscales
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from tests.test_tax_estimation_2025 import _dossier_52000, _validee
from tests.test_tax_pension_income_2025 import modifier


def profil_dividendes():
    return ProfilDividendes2025(source='Paire synthétique complète 2025, identité et exclusions vérifiées', confirme=True)


def dossier_dividendes(a='10000', o='10000', emploi=False):
    d=_dossier_52000()
    if not emploi: d=replace(d,documents=(),donnees_validees=())
    a,o=D(a),D(o)
    ta,to=arrondir_cent(a*D('1.38')),arrondir_cent(o*D('1.15'))
    valeurs={'T5':{'24':a,'25':ta,'26':arrondir_cent(ta*D('.150198')),'10':o,'11':to,'12':arrondir_cent(to*D('.090301'))},
             'RL-3':{'A1':a,'A2':o,'B':ta+to,'C':arrondir_cent(a*D('.161460')+o*D('.039330'))}}
    return replace(d,documents=d.documents+(Path('T5.pdf'),Path('RL-3.pdf')),
        donnees_validees=d.donnees_validees+tuple(_validee(Path(t+'.pdf'),t,c,str(v)) for t,cs in valeurs.items() for c,v in cs.items()))


def calcul(dossier=None,**kw):
    return calculer_estimation_fiscale_2025(dossier or dossier_dividendes(),profil_dividendes=profil_dividendes(),**kw)


@pytest.mark.parametrize('emploi',[False,True])
@pytest.mark.parametrize('a,o,imposable,credit_f,credit_q',[('10000','0','13800','2072.73','1614.60'),('0','10000','11500','1038.46','393.30'),('10000','10000','25300','3111.19','2007.90')])
def test_inclusion_unique_et_credits(emploi,a,o,imposable,credit_f,credit_q):
    e=calcul(dossier_dividendes(a,o,emploi));r=e.dividendes
    assert r.ligne_12000==r.ligne_128==D(imposable)
    assert r.ligne_12010==D(o)*D('1.15')
    assert r.ligne_40425==D(credit_f) and r.ligne_415==D(credit_q)
    assert e.revenu.revenu_total_federal==e.revenu.revenu_total_quebec==D(imposable)+(52000 if emploi else 0)
    assert e.revenu.revenu_net_federal==e.revenu.revenu_imposable_federal==D(imposable)+(51515 if emploi else 0)
    assert e.revenu.revenu_net_quebec==e.revenu.revenu_imposable_quebec==D(imposable)+(50095 if emploi else 0)
    assert not e.interets.present and not e.pensions.present
    assert e.rapprochement.retenues_totales==(13700 if emploi else 0)
    assert e.rapprochement.abattement_quebec==arrondir_cent(e.federal.impot_federal_de_base*D('.165'))
    assert e.rapprochement.impot_total_preliminaire==e.rapprochement.impot_federal_apres_abattement+e.quebec.impot_quebec_preliminaire+r.cotisation_fss
    # Contrefactuel : les mêmes revenus majorés sans crédit dividendes.
    from tests.test_tax_interest_income_2025 import dossier_interets, calcul as calcul_interets
    sans_credit=calcul_interets(dossier_interets(imposable,emploi))
    assert e.federal.impot_federal_de_base==max(D(0),sans_credit.federal.impot_federal_de_base-D(credit_f))
    assert e.quebec.impot_quebec_preliminaire==max(D(0),sans_credit.quebec.impot_quebec_preliminaire-D(credit_q))
    assert e.federal.credits_non_remboursables==sans_credit.federal.credits_non_remboursables
    assert e.federal.top_up_credit==sans_credit.federal.top_up_credit


def test_credits_inutilises_ne_remboursent_pas_et_fss_reel():
    e=calcul()
    assert e.federal.impot_federal_de_base==e.quebec.impot_quebec_preliminaire==0
    assert e.dividendes.cotisation_fss==e.rapprochement.impot_total_preliminaire==D('18.70')


@pytest.mark.parametrize('montant,fss',[('0','0'),('18130','0'),('18131','.01'),('33130','150'),('63060','150'),('63061','150.01'),('148060','1000')])
def test_assiette_fss_reelle(montant,fss):
    r=consolider_dividendes_2025(dossier_dividendes(montant,'0'),profil_dividendes())
    assert r.cotisation_fss==D(fss)


@pytest.mark.parametrize('ty,case',[('T5',c) for c in ('10','11','12','24','25','26')]+[('RL-3',c) for c in ('A1','A2','B','C','207','208')])
def test_extraction_cases_distinctes(ty,case):
    assert [(x.case,x.valeur) for x in extraire_cases_fiscales(ty,f'Case {case} 123.45','scan.pdf')]==[(case,D('123.45'))]


def test_extraction_sans_confondre_vide_et_case_suivante():
    texte='Case A1\nCase A2 20.00\nCase B 23.00\nCase C 0.79'
    assert {x.case:x.valeur for x in extraire_cases_fiscales('RL-3',texte,'scan.pdf')}=={'A2':D(20),'B':D(23),'C':D('.79')}


@pytest.mark.parametrize('ty,case',[('T5',c) for c in ('10','11','12','24','25','26')]+[('RL-3',c) for c in ('A1','A2','B','C')])
def test_cases_obligatoires_meme_nulles(ty,case):
    d=dossier_dividendes('0','0')
    d=replace(d,donnees_validees=tuple(x for x in d.donnees_validees if (x.type_document,x.case)!=(ty,case)))
    with pytest.raises(ValueError,match='obligatoires'):calcul(d)


@pytest.mark.parametrize('ty,case',[('T5',c) for c in ('10','11','12','24','25','26')]+[('RL-3',c) for c in ('A1','A2','B','C')])
def test_ecart_un_cent_refuse(ty,case):
    d=dossier_dividendes();v=next(x.valeur_validee for x in d.donnees_validees if (x.type_document,x.case)==(ty,case))
    with pytest.raises(ValueError,match='incohérents'):calcul(modifier(d,ty,case,str(v+D('.01'))))


@pytest.mark.parametrize('ty,c',[('T5',c) for c in ('13','14','15','16','17','18','19','30')]+[('RL-3',c) for c in ('D','E','F','G','H','I','J','K','E-1','E-2','H-2','K-1','207','208')])
def test_autres_cases_refusees(ty,c):
    with pytest.raises(ValueError,match='hors périmètre'):calcul(modifier(dossier_dividendes(),ty,c,'1'))


@pytest.mark.parametrize('v',['-1','NaN','Infinity','0.001','1000000000'])
def test_montants_invalides(v):
    with pytest.raises(ValueError):calcul(modifier(dossier_dividendes(),'T5','24',v))


@pytest.mark.parametrize('champ,v',[('confirme',1),('confirme','true'),('source',None),('source',''),('devise','USD'),('compte_conjoint',True),('frais_placement',True),('cas_complexe',True),('cas_complexe',1)])
def test_profil_invalide(champ,v):
    with pytest.raises(ValueError):valider_profil_dividendes_2025(replace(profil_dividendes(),**{champ:v}))


@pytest.mark.parametrize('code',['0','2','3','4','5'])
def test_beneficiaire_non_particulier_unique_refuse(code):
    with pytest.raises(ValueError,match='titulaire unique'):calcul(modifier(dossier_dividendes(),'T5','23',code))


def test_code_un_et_zero_dividendes():
    assert calcul(modifier(dossier_dividendes('0','0'),'T5','23','1')).dividendes.ligne_12000==0


def test_doublon_piece_non_validee_et_paire_incomplete():
    d=dossier_dividendes()
    for invalide in (replace(d,donnees_validees=d.donnees_validees+(d.donnees_validees[0],)),
                    replace(d,documents=d.documents+(Path('autre.pdf'),)),
                    replace(d,documents=(Path('T5.pdf'),),donnees_validees=tuple(x for x in d.donnees_validees if x.type_document=='T5'))):
        with pytest.raises(ValueError):calcul(invalide)


@pytest.mark.parametrize('type_doc',['T3','RL-16','T4A','T5008','INTERETS'])
def test_autres_sources_refusees(type_doc):
    d=dossier_dividendes();p=Path(type_doc+'.pdf')
    d=replace(d,documents=d.documents+(p,),donnees_validees=d.donnees_validees+(_validee(p,type_doc,'26','1'),))
    with pytest.raises(ValueError,match='hors périmètre'):calcul(d)


@pytest.mark.parametrize('nom',['ae_confirme','rqap_confirme','rrq_rpc_confirme','psv_confirme'])
def test_concurrence_prestations(nom):
    with pytest.raises(ValueError):calcul(**{nom:True})


@pytest.mark.parametrize('emploi',[False,True])
def test_stockage_resume_trace_pdf(tmp_path,emploi):
    e=calcul(dossier_dividendes(emploi=emploi))
    p=sauvegarder_dossier_fiscal(e.dossier,estimation=e,destination=tmp_path/'d.json')
    charge=charger_dossier_fiscal(p)
    assert calculer_estimation_fiscale_2025(charge.dossier,profil_dividendes=charge.profil_dividendes)==e
    assert 'DIVIDENDES CANADIENS 2025' in formater_estimation_fiscale_2025(e)
    trace=construire_trace_calcul_fiscal_2025(e)
    assert next(x.montant for x in trace.lignes if x.libelle=='Dividendes 12000')==25300
    assert next(x.montant for x in trace.lignes if x.libelle=='FSS dividendes 446')==D('18.70')
    pdf=exporter_rapport_fiscal_pdf_2025(e,tmp_path/'r.pdf')
    with fitz.open(pdf) as doc:
        texte=''.join(page.get_text() for page in doc)
        assert 'DIVIDENDES CANADIENS 2025' in texte and '12010' in texte and '40425' in texte and '415' in texte
        for page in doc:
            for x0,y0,x1,y1,*_ in page.get_text('blocks'):
                assert 0<=x0<x1<=page.rect.width and 0<=y0<y1<=page.rect.height
    raw=json.loads(p.read_text(encoding='utf-8'));del raw['profil_dividendes'];p.write_text(json.dumps(raw),encoding='utf-8')
    ancien=charger_dossier_fiscal(p)
    assert not ancien.profil_dividendes.confirme
    with pytest.raises(ValueError,match='Confirmez'):calculer_estimation_fiscale_2025(ancien.dossier)


@pytest.mark.parametrize('raw',[None,[],True,{'confirme':1},{'devise':'USD'},{'source':3},{'inconnu':True}])
def test_json_invalide(tmp_path,raw):
    p=sauvegarder_dossier_fiscal(dossier_dividendes(),destination=tmp_path/'d.json')
    contenu=json.loads(p.read_text(encoding='utf-8'));contenu['profil_dividendes']=raw;p.write_text(json.dumps(contenu),encoding='utf-8')
    with pytest.raises(ValueError):charger_dossier_fiscal(p)


def test_estimation_profil_perime_refuse(tmp_path):
    e=calcul()
    with pytest.raises(ValueError):sauvegarder_dossier_fiscal(e.dossier,estimation=e,profil_dividendes=ProfilDividendes2025(),destination=tmp_path/'d.json')


def test_reer_net_et_fss_independants():
    from src.comptaprivee.tax_adjustments_2025 import AjustementReer2025
    e=calcul(dossier_dividendes(emploi=True),ajustement_reer=AjustementReer2025(D('10000'),D('10000'),'Avis ARC synthétique',True))
    assert e.revenu.revenu_net_federal==66815 and e.revenu.revenu_net_quebec==65395
    assert e.dividendes.cotisation_fss==D('18.70')


def test_credit_age_utilise_net_majore_et_refuse_net_reel():
    from src.comptaprivee.tax_federal_age_pension_2025 import CreditsFederauxAgePension2025
    p=CreditsFederauxAgePension2025(reclamer_montant_age=True,age_65_plus_31_decembre_2025=True,
        revenu_net_ligne_23600=D('20000'),resident_canada_toute_annee=True,aucune_regle_deces=True,
        aucun_fractionnement_pension=True,aucun_transfert_conjoint=True,valide_par_comptable=True,source_age='Âge synthétique')
    with pytest.raises(ValueError,match='doit correspondre'):calcul(credits_federaux_age_pension=p)
    assert calcul(credits_federaux_age_pension=replace(p,revenu_net_ligne_23600=D('25300'))).federal.impot_federal_de_base==0
