"""3D : PBR indépendant, appariement brut/net, pertes et chaîne complète."""
from dataclasses import replace
from decimal import Decimal as D
from pathlib import Path
import json
import fitz
import pytest
from src.comptaprivee.tax_capital_gains_2025 import *
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025, formater_estimation_fiscale_2025
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
from src.comptaprivee.tax_document_classifier import classifier_document_fiscal
from src.comptaprivee.tax_field_extractor import extraire_cases_fiscales
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from tests.test_tax_estimation_2025 import _dossier_52000, _validee
from tests.test_tax_pension_income_2025 import modifier


def profil_capital(**kw):
    p=ProfilCapital2025(source='Vente synthétique appariée et exclusions vérifiées',titre='XYZ Canada actions ordinaires SHS',
        date_acquisition='2023-03-01',date_cession='2025-03-13',pbr='4000',source_pbr='Achat unique et frais vérifiés sur registre synthétique',
        frais_courtage='60',frais_autres='0',source_frais='Avis de vente synthétique, frais ventilés',confirme=True,pbr_confirme=True)
    return replace(p,**kw)


def dossier_capital(produit='6500',courtage='60',emploi=False):
    d=_dossier_52000()
    if not emploi:d=replace(d,documents=(),donnees_validees=())
    return replace(d,documents=d.documents+(Path('T5008.pdf'),Path('RL-18.pdf')),
        donnees_validees=d.donnees_validees+(_validee('T5008.pdf','T5008','21',produit),_validee('RL-18.pdf','RL-18','21',str(D(produit)-D(courtage)))))


def calcul(dossier=None,profil=None,**kw):
    return calculer_estimation_fiscale_2025(dossier or dossier_capital(),profil_capital=profil or profil_capital(),**kw)


@pytest.mark.parametrize('emploi',[False,True])
@pytest.mark.parametrize('produit,gain,imposable,perte',[('6500','2440','1220','0'),('4060','0','0','0'),('3000','-1060','0','530')])
def test_gain_perte_revenu_et_retenues(emploi,produit,gain,imposable,perte):
    e=calcul(dossier_capital(produit,emploi=emploi));r=e.capital
    assert r.gain_perte==D(gain) and r.ligne_12700==r.ligne_139==D(imposable)
    assert r.perte_nette_2025==D(perte)
    assert e.revenu.revenu_total_federal==e.revenu.revenu_total_quebec==D(imposable)+(52000 if emploi else 0)
    assert e.revenu.revenu_net_federal==e.revenu.revenu_imposable_federal==D(imposable)+(51515 if emploi else 0)
    assert e.revenu.revenu_net_quebec==e.revenu.revenu_imposable_quebec==D(imposable)+(50095 if emploi else 0)
    assert e.rapprochement.retenues_totales==(13700 if emploi else 0)
    assert not e.dividendes.present and not e.interets.present and not e.pensions.present
    from tests.test_tax_interest_income_2025 import dossier_interets,calcul as calcul_interets
    reference=calcul_interets(dossier_interets(imposable,emploi))
    assert e.federal==reference.federal and e.quebec==reference.quebec
    assert e.rapprochement.impot_total_preliminaire==reference.rapprochement.impot_total_preliminaire


def test_exemple_officiel_et_frais_autres_non_doubles():
    e=calcul(profil=profil_capital(frais_autres='20'))
    assert e.capital.produit==6500 and e.capital.produit_rl18==6440
    assert e.capital.gain_perte==2420 and e.capital.ligne_12700==1210
    assert e.capital.gain_perte==e.capital.produit_rl18-e.capital.pbr-e.capital.frais_autres


@pytest.mark.parametrize('cout',['0','4000','9999'])
def test_case20_ne_determine_jamais_pbr(cout):
    d=modifier(modifier(dossier_capital(),'T5008','20',cout),'RL-18','20','1234')
    assert calcul(d).capital.pbr==4000 and calcul(d).capital.gain_perte==2440


def test_aucun_pbr_implicite_meme_case20_complete():
    d=modifier(modifier(dossier_capital(),'T5008','20','4000'),'RL-18','20','4000')
    for p in (profil_capital(pbr=''),profil_capital(pbr_confirme=False),profil_capital(source_pbr='')):
        with pytest.raises(ValueError,match='PBR'):calcul(d,p)


@pytest.mark.parametrize('imposable,fss',[('0','0'),('18130','0'),('18131','.01'),('33130','150'),('63060','150'),('63061','150.01')])
def test_fss_gain_imposable_et_non_produit(imposable,fss):
    produit=str(2*D(imposable)+D('4060'))
    e=calcul(dossier_capital(produit))
    assert e.capital.cotisation_fss==D(fss)
    assert e.rapprochement.impot_total_preliminaire==e.rapprochement.impot_federal_apres_abattement+e.quebec.impot_quebec_preliminaire+D(fss)


@pytest.mark.parametrize('emploi',[False,True])
def test_seuil_imr_gain_integral_avant_deductions(emploi):
    produit=str(D('177882')-(52000 if emploi else 0)+D('4060'))
    assert calcul(dossier_capital(produit,emploi=emploi)).capital.present
    from src.comptaprivee.tax_adjustments_2025 import AjustementReer2025
    with pytest.raises(ValueError,match='Impôt minimum'):
        calcul(dossier_capital(str(D(produit)+1),emploi=emploi),ajustement_reer=AjustementReer2025(D('10000'),D('10000'),'Avis synthétique',True))


@pytest.mark.parametrize('champ,valeur',[('confirme',1),('pbr_confirme','true'),('devise','USD'),('compte_conjoint',True),('cas_complexe',True),('reports_pertes',True),('perte_apparente',True),('source',None),('titre',''),('source_frais',''),('date_cession','2024-12-31'),('date_cession','2026-01-01'),('date_cession','2025-02-30'),('date_cession','20250313'),('date_acquisition','1999-12-31'),('date_acquisition','2025-03-01'),('date_acquisition','2025-04-01'),('pbr','-1'),('pbr','NaN'),('pbr','1e3'),('pbr','1000000000'),('frais_courtage',''),('frais_autres','0.001'),('pbr',4000)])
def test_profils_hors_perimetre(champ,valeur):
    with pytest.raises(ValueError):calcul(profil=profil_capital(**{champ:valeur}))


def test_periode_perte_apparente_frontiere_30_jours():
    # 13 mars - 11 février = 30 jours; 10 février = 31 jours.
    with pytest.raises(ValueError,match='30 jours'):calcul(profil=profil_capital(date_acquisition='2025-02-11'))
    assert calcul(profil=profil_capital(date_acquisition='2025-02-10')).capital.present


@pytest.mark.parametrize('type_doc',['T5008','RL-18'])
@pytest.mark.parametrize('case',['19','20','21','23'])
@pytest.mark.parametrize('montant',['123.45','-123.45'])
def test_extraction_capital(type_doc,case,montant):
    assert [(x.case,x.valeur) for x in extraire_cases_fiscales(type_doc,f'Case {case} {montant}','scan.pdf')]==[(case,D(montant))]


@pytest.mark.parametrize('nom,type_doc',[('T5008','T5008'),('RL-18','RL-18'),('Relevé 18','RL-18')])
def test_classification(nom,type_doc):
    assert classifier_document_fiscal(nom+'.pdf').type_document==type_doc


def test_consolide_mixte_et_codes_non_monetaires():
    assert classifier_document_fiscal('T5008_RL-18.pdf').type_document not in {'T5008','RL-18'}
    texte='Case 11 1\nCase 12 000000000\nCase 13 CAD\nCase 14 0313\nCase 15 SHS\nCase 16 100\nCase 17 XYZ\nCase 18 999999\nCase 20\nCase 21 6500.00'
    assert [(x.case,x.valeur) for x in extraire_cases_fiscales('T5008',texte,'scan.pdf')]==[('21',D(6500))]


@pytest.mark.parametrize('type_doc',['T5008','RL-18'])
def test_produits_incoherents_et_manquants(type_doc):
    with pytest.raises(ValueError,match='Appariement'):calcul(modifier(dossier_capital(),type_doc,'21','6501'))
    d=dossier_capital();d=replace(d,donnees_validees=tuple(x for x in d.donnees_validees if x.type_document!=type_doc))
    with pytest.raises(ValueError):calcul(d)


@pytest.mark.parametrize('montant',['-1','NaN','Infinity','0.001','1000000000'])
def test_montants_feuillets_invalides(montant):
    with pytest.raises(ValueError):calcul(modifier(dossier_capital(),'T5008','21',montant))


@pytest.mark.parametrize('ty,case',[('T5008','19'),('T5008','23'),('RL-18','19'),('RL-18','23')])
def test_titres_complexes_refuses(ty,case):
    with pytest.raises(ValueError,match='hors périmètre'):calcul(modifier(dossier_capital(),ty,case,'1'))


def test_doublons_et_sources_non_validees():
    d=dossier_capital()
    for invalide in (replace(d,donnees_validees=d.donnees_validees+(d.donnees_validees[0],)),
                    replace(d,documents=d.documents+(Path('autre.pdf'),)),
                    replace(d,donnees_validees=(replace(d.donnees_validees[0],statut='À vérifier'),d.donnees_validees[1])),
                    replace(d,documents=(Path('commun.pdf'),),donnees_validees=tuple(replace(x,document=Path('commun.pdf')) for x in d.donnees_validees))):
        with pytest.raises(ValueError):calcul(invalide)


@pytest.mark.parametrize('type_doc',['T3','RL-16','T5','RL-3','T4A','INTERETS'])
def test_distributions_et_autres_sources_refusees(type_doc):
    d=dossier_capital();p=Path(type_doc+'.pdf')
    d=replace(d,documents=d.documents+(p,),donnees_validees=d.donnees_validees+(_validee(p,type_doc,'21','1'),))
    with pytest.raises(ValueError,match='hors périmètre'):calcul(d)


@pytest.mark.parametrize('nom',['ae_confirme','rqap_confirme','rrq_rpc_confirme','psv_confirme'])
def test_concurrence_prestations(nom):
    with pytest.raises(ValueError,match='hors périmètre'):calcul(**{nom:True})


@pytest.mark.parametrize('produit',['3000','6500','44060'])
def test_stockage_resume_trace_pdf(tmp_path,produit):
    e=calcul(dossier_capital(produit,emploi=True))
    p=sauvegarder_dossier_fiscal(e.dossier,estimation=e,destination=tmp_path/'d.json')
    charge=charger_dossier_fiscal(p)
    assert calculer_estimation_fiscale_2025(charge.dossier,profil_capital=charge.profil_capital)==e
    assert 'GAINS ET PERTES EN CAPITAL 2025' in formater_estimation_fiscale_2025(e)
    trace=construire_trace_calcul_fiscal_2025(e)
    assert next(x.montant for x in trace.lignes if x.libelle=='PBR indépendant')==4000
    assert next(x.montant for x in trace.lignes if x.libelle=='Gain/perte 13200 / G 10')==D(produit)-4060
    pdf=exporter_rapport_fiscal_pdf_2025(e,tmp_path/'r.pdf')
    with fitz.open(pdf) as doc:
        texte=''.join(page.get_text() for page in doc)
        assert 'GAINS ET PERTES EN CAPITAL 2025' in texte and '12700' in texte and 'PBR' in texte
        for page in doc:
            for x0,y0,x1,y1,*_ in page.get_text('blocks'):
                assert 0<=x0<x1<=page.rect.width and 0<=y0<y1<=page.rect.height
    raw=json.loads(p.read_text(encoding='utf-8'));del raw['profil_capital'];p.write_text(json.dumps(raw),encoding='utf-8')
    ancien=charger_dossier_fiscal(p)
    assert not ancien.profil_capital.confirme
    with pytest.raises(ValueError,match='Confirmez'):calculer_estimation_fiscale_2025(ancien.dossier)


@pytest.mark.parametrize('raw',[None,[],True,{'confirme':1},{'devise':'USD'},{'pbr':4000},{'inconnu':True}])
def test_json_invalide(tmp_path,raw):
    p=sauvegarder_dossier_fiscal(dossier_capital(),destination=tmp_path/'d.json')
    contenu=json.loads(p.read_text(encoding='utf-8'));contenu['profil_capital']=raw;p.write_text(json.dumps(contenu),encoding='utf-8')
    with pytest.raises(ValueError):charger_dossier_fiscal(p)


def test_profil_et_dossier_perimes_refuses(tmp_path):
    e=calcul()
    with pytest.raises(ValueError):sauvegarder_dossier_fiscal(e.dossier,estimation=e,profil_capital=profil_capital(pbr='4001'),destination=tmp_path/'d.json')
    with pytest.raises(ValueError):sauvegarder_dossier_fiscal(dossier_capital('7000'),estimation=e,destination=tmp_path/'d.json')


def test_reer_ne_reduit_pas_fss():
    from src.comptaprivee.tax_adjustments_2025 import AjustementReer2025
    e=calcul(dossier_capital('44060',emploi=True),ajustement_reer=AjustementReer2025(D('10000'),D('10000'),'Avis synthétique',True))
    assert e.revenu.revenu_net_federal==61515 and e.capital.cotisation_fss==D('18.70')


def test_credit_age_net_perime_refuse():
    from src.comptaprivee.tax_federal_age_pension_2025 import CreditsFederauxAgePension2025
    p=CreditsFederauxAgePension2025(reclamer_montant_age=True,age_65_plus_31_decembre_2025=True,
        revenu_net_ligne_23600=D('40000'),resident_canada_toute_annee=True,aucune_regle_deces=True,
        aucun_fractionnement_pension=True,aucun_transfert_conjoint=True,valide_par_comptable=True,source_age='Âge synthétique')
    with pytest.raises(ValueError,match='doit correspondre'):calcul(dossier_capital('44060'),credits_federaux_age_pension=p)
    assert calcul(dossier_capital('44060'),credits_federaux_age_pension=replace(p,revenu_net_ligne_23600=D('20000'))).federal.impot_federal_de_base==0
