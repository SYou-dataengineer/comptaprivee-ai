"""3A : appariement, revenu imposable, FSS et garde-fous de bout en bout."""
from dataclasses import replace
from decimal import Decimal as D
from pathlib import Path
import json
import fitz
import pytest
from src.comptaprivee.tax_interest_income_2025 import *
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025, formater_estimation_fiscale_2025
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
from src.comptaprivee.tax_document_classifier import classifier_document_fiscal
from src.comptaprivee.tax_field_extractor import extraire_cases_fiscales
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from tests.test_tax_estimation_2025 import _dossier_52000, _validee
from tests.test_tax_pension_income_2025 import modifier


def profil_interets():
    return ProfilInterets2025(source='Paire synthétique complète, CAD et exclusions vérifiés',confirme=True)


def dossier_interets(montant='20000',emploi=False):
    d=_dossier_52000()
    if not emploi:d=replace(d,documents=(),donnees_validees=())
    return replace(d,documents=d.documents+(Path('T5.pdf'),Path('RL-3.pdf')),
        donnees_validees=d.donnees_validees+tuple(_validee(Path(t+'.pdf'),t,c,montant) for t,c in [('T5','13'),('RL-3','D')]))


def calcul(dossier=None,**kw):
    return calculer_estimation_fiscale_2025(dossier or dossier_interets(),profil_interets=profil_interets(),**kw)


@pytest.mark.parametrize('emploi',[False,True])
def test_revenus_retenues_fss_et_impot(emploi):
    e=calcul(dossier_interets(emploi=emploi))
    assert e.interets.ligne_12100==e.interets.ligne_130==20000
    assert e.revenu.revenu_total_federal==e.revenu.revenu_total_quebec==(72000 if emploi else 20000)
    assert e.revenu.revenu_net_federal==e.revenu.revenu_imposable_federal==(71515 if emploi else 20000)
    assert e.revenu.revenu_net_quebec==e.revenu.revenu_imposable_quebec==(70095 if emploi else 20000)
    assert e.interets.cotisation_fss==D('18.70')
    assert e.rapprochement.retenues_totales==(13700 if emploi else 0)
    assert e.rapprochement.impot_total_preliminaire==e.rapprochement.impot_federal_apres_abattement+e.quebec.impot_quebec_preliminaire+D('18.70')
    if not emploi:
        # Crédit personnel arrondi : 16 129 * 14,5 % = 2 338,71.
        assert e.federal.impot_federal_de_base==D('561.29')
        assert e.quebec.impot_quebec_preliminaire==D('200.06')
        assert e.rapprochement.impot_total_preliminaire==D('687.44')


@pytest.mark.parametrize('montant,fss',[('0','0'),('18130','0'),('18131','.01'),('33130','150'),('63060','150'),('63061','150.01'),('148060','1000'),('200000','1000')])
def test_frontieres_fss(montant,fss):
    dossier=dossier_interets(montant)
    assert consolider_interets_2025(dossier,profil_interets()).cotisation_fss==D(fss)
    if D(montant)>129590:
        # Le garde-fou historique des crédits à haut revenu est conservé.
        with pytest.raises(ValueError,match='hors profil'):calcul(dossier)
    else:
        e=calcul(dossier)
        assert e.interets.cotisation_fss==D(fss)
        assert e.revenu.revenu_net_federal==D(montant)


@pytest.mark.parametrize('ty,c',[('T5','13'),('T5','23')]+[('RL-3',c) for c in ('A1','A2','B','C','D','E','F','G','I','J','K')])
@pytest.mark.parametrize('v',['123.45','-123.45'])
def test_extraction(ty,c,v):
    assert [(x.case,x.valeur) for x in extraire_cases_fiscales(ty,f'Case {c} {v}','scan.pdf')]==[(c,D(v))]


def test_codes_administratifs_non_monetaires():
    texte='Case 13 123.45\nCase 21 O\nCase 22 000000000\nCase 23 1\nCase 27 CAD\nCase 28 99999\nCase 29 99999'
    assert {x.case for x in extraire_cases_fiscales('T5',texte,'scan.pdf')}=={'13','23'}
    assert calcul(modifier(dossier_interets(),'T5','23','1')).interets.ligne_12100==20000
    for code in ('0','2','3','4','5'):
        with pytest.raises(ValueError,match='titulaire unique'):calcul(modifier(dossier_interets(),'T5','23',code))


@pytest.mark.parametrize('texte,case',[('Case D\nCase A1 100.00','A1'),('Case E\nCase E-1 100.00','E-1')])
def test_case_vide_ne_capture_pas_sous_case_rl3(texte,case):
    assert [(x.case,x.valeur) for x in extraire_cases_fiscales('RL-3',texte,'scan.pdf')]==[(case,D('100'))]


@pytest.mark.parametrize('nom',['RL-3','RL3','Relevé 3'])
def test_classification(nom):
    assert classifier_document_fiscal(nom+'.pdf').type_document=='RL-3'
    assert classifier_document_fiscal('scan.pdf',nom).type_document=='RL-3'
    assert classifier_document_fiscal('scan.pdf',nom+' T4').type_document=='À vérifier'


@pytest.mark.parametrize('ty,c',[('T5',str(c)) for c in (10,11,12,14,15,16,17,18,19,24,25,26,30)]+[('RL-3',c) for c in ('A1','A2','B','C','E','F','G','I','J','K')])
def test_autres_montants_refuses(ty,c):
    with pytest.raises(ValueError,match='hors périmètre'):calcul(modifier(dossier_interets(),ty,c,'1'))


@pytest.mark.parametrize('v',['-1','NaN','Infinity','0.001','1000000000'])
def test_montants_invalides(v):
    with pytest.raises(ValueError):calcul(modifier(dossier_interets(),'T5','13',v))


def test_sources_validation_appariement_et_confirmation():
    d=dossier_interets()
    for faux in [replace(d,documents=d.documents[:-1]),replace(d,donnees_validees=d.donnees_validees*2),
        modifier(d,'RL-3','D','1'),replace(d,donnees_validees=d.donnees_validees[:1]),
        replace(d,donnees_validees=tuple(replace(x,statut='À vérifier') for x in d.donnees_validees)),
        replace(d,annee_fiscale=2024),replace(d,province='Ontario'),
        modifier(d,'T3','26','100'),modifier(d,'T5008','21','100')]:
        with pytest.raises(ValueError):calcul(faux)
    with pytest.raises(ValueError,match='Confirmez'):calculer_estimation_fiscale_2025(d)


@pytest.mark.parametrize('nom',['ae_confirme','rqap_confirme','rrq_rpc_confirme','psv_confirme'])
def test_concurrence(nom):
    with pytest.raises(ValueError):calcul(**{nom:True})


@pytest.mark.parametrize('champ,v',[('confirme',1),('confirme','true'),('source',None),('devise','USD'),('compte_conjoint',True),('frais_placement',True),('deja_declares',True),('compte_conjoint',1)])
def test_profil_invalide(champ,v):
    with pytest.raises(ValueError):valider_profil_interets_2025(replace(profil_interets(),**{champ:v}))


@pytest.mark.parametrize('emploi',[False,True])
def test_stockage_resume_trace_pdf(tmp_path,emploi):
    e=calcul(dossier_interets(emploi=emploi))
    p=sauvegarder_dossier_fiscal(e.dossier,estimation=e,destination=tmp_path/'d.json')
    charge=charger_dossier_fiscal(p)
    assert calculer_estimation_fiscale_2025(charge.dossier,profil_interets=charge.profil_interets)==e
    assert 'INTÉRÊTS CANADIENS 2025' in formater_estimation_fiscale_2025(e)
    trace=construire_trace_calcul_fiscal_2025(e)
    assert next(x.montant for x in trace.lignes if x.libelle=='Intérêts 12100')==20000
    assert next(x.montant for x in trace.lignes if x.libelle=='FSS intérêts 446')==D('18.70')
    pdf=exporter_rapport_fiscal_pdf_2025(e,tmp_path/'r.pdf')
    with fitz.open(pdf) as doc:
        texte=''.join(page.get_text() for page in doc)
        assert 'INTÉRÊTS CANADIENS 2025' in texte and '12100' in texte and 'FSS 446' in texte
        for page in doc:
            for x0,y0,x1,y1,*_ in page.get_text('blocks'):
                assert 0<=x0<x1<=page.rect.width and 0<=y0<y1<=page.rect.height
    raw=json.loads(p.read_text(encoding='utf-8'));del raw['profil_interets'];p.write_text(json.dumps(raw),encoding='utf-8')
    ancien=charger_dossier_fiscal(p)
    assert not ancien.profil_interets.confirme
    with pytest.raises(ValueError,match='Confirmez'):calculer_estimation_fiscale_2025(ancien.dossier)


@pytest.mark.parametrize('raw',[None,[],True,{'confirme':1},{'devise':'USD'},{'source':3},{'inconnu':True}])
def test_json_invalide(tmp_path,raw):
    p=sauvegarder_dossier_fiscal(dossier_interets(),destination=tmp_path/'d.json')
    contenu=json.loads(p.read_text(encoding='utf-8'));contenu['profil_interets']=raw;p.write_text(json.dumps(contenu),encoding='utf-8')
    with pytest.raises(ValueError):charger_dossier_fiscal(p)


def test_stockage_refuse_estimation_profil_different(tmp_path):
    e=calcul()
    with pytest.raises(ValueError):sauvegarder_dossier_fiscal(e.dossier,estimation=e,profil_interets=ProfilInterets2025(),destination=tmp_path/'d.json')


def test_document_sans_donnees_refuse():
    d=dossier_interets()
    with pytest.raises(ValueError,match='Chaque pièce'):calcul(replace(d,documents=d.documents+(Path('autre.pdf'),)))


def test_reer_ne_reduit_pas_assiette_fss():
    from src.comptaprivee.tax_adjustments_2025 import AjustementReer2025
    e=calcul(dossier_interets(emploi=True),ajustement_reer=AjustementReer2025(D('10000'),D('10000'),'Avis ARC synthétique',True))
    assert e.revenu.revenu_net_federal==61515
    assert e.revenu.revenu_net_quebec==60095
    assert e.interets.cotisation_fss==D('18.70')


def test_credit_age_revenu_perime_refuse_et_revalide():
    from src.comptaprivee.tax_federal_age_pension_2025 import CreditsFederauxAgePension2025
    p=CreditsFederauxAgePension2025(reclamer_montant_age=True,age_65_plus_31_decembre_2025=True,
        revenu_net_ligne_23600=D('20000'),resident_canada_toute_annee=True,aucune_regle_deces=True,
        aucun_fractionnement_pension=True,aucun_transfert_conjoint=True,valide_par_comptable=True,source_age='Âge synthétique')
    assert calcul(credits_federaux_age_pension=p).federal.impot_federal_de_base==0
    with pytest.raises(ValueError,match='doit correspondre'):
        calcul(dossier_interets('30000'),credits_federaux_age_pension=p)
    assert calcul(dossier_interets('30000'),credits_federaux_age_pension=replace(p,revenu_net_ligne_23600=D('30000'))).interets.ligne_12100==30000


def test_aucun_credit_pension_sur_interets():
    from src.comptaprivee.tax_federal_age_pension_2025 import CreditsFederauxAgePension2025
    p=CreditsFederauxAgePension2025(reclamer_montant_pension=True,revenu_pension_admissible=D('20000'),
        revenu_net_ligne_23600=D('20000'),resident_canada_toute_annee=True,aucune_regle_deces=True,
        aucun_fractionnement_pension=True,aucun_transfert_conjoint=True,valide_par_comptable=True,
        revenu_pension_admissible_confirme=True,source_pension='T5 intérêts')
    with pytest.raises(ValueError,match='31400'):calcul(credits_federaux_age_pension=p)


@pytest.mark.parametrize('age',[64,65])
def test_t5_rente_code_beneficiaire_preserve_bloc_2e(age):
    from tests.test_tax_pension_income_2025 import dossier_pensions, profil_pensions
    d=dossier_pensions('T5_RENTE')
    reference=calculer_estimation_fiscale_2025(d,profil_pensions=profil_pensions('T5_RENTE',age))
    avec_code=calculer_estimation_fiscale_2025(modifier(d,'T5','23','1'),profil_pensions=profil_pensions('T5_RENTE',age))
    assert avec_code.pensions==reference.pensions
    assert avec_code.rapprochement==reference.rapprochement
    assert not avec_code.interets.present
    with pytest.raises(ValueError,match='hors périmètre'):
        calculer_estimation_fiscale_2025(modifier(d,'T5','23','2'),profil_pensions=profil_pensions('T5_RENTE',age))
