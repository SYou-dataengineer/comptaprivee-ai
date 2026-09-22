"""Reports 3F : conservation des soldes, ordre, plafonds, annexe N et persistance."""
from dataclasses import replace
from decimal import Decimal as D
import json
import fitz
import pytest
from src.comptaprivee.tax_capital_loss_carryovers_2025 import *
from src.comptaprivee.tax_investment_expenses_2025 import ProfilFraisPlacement2025
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025, formater_estimation_fiscale_2025
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from tests.test_tax_capital_gains_2025 import dossier_capital, profil_capital


def profil_pertes(dossier=None, capital=None, frais=None, **kw):
    dossier=dossier or dossier_capital();capital=capital or profil_capital();frais=frais or ProfilFraisPlacement2025()
    p=ProfilReportsPertes2025(historique='2024;500;600 | 2018;1000;800',
        source_federale='Avis ARC et registre synthétique complet',source_quebec='Avis RQ, TP-729 et registre synthétique complet',
        demande_federale='1200',demande_quebec='1000',historique_confirme=True,confirme=True)
    p=replace(p,**kw)
    return replace(p,empreinte=empreinte_reports_pertes_2025(p,dossier,capital,frais))


def calcul(dossier=None,p=None,frais=None,**kw):
    dossier=dossier or dossier_capital();frais=frais or ProfilFraisPlacement2025()
    return calculer_estimation_fiscale_2025(dossier,profil_capital=profil_capital(),profil_frais_placement=frais,
        profil_reports_pertes=p or profil_pertes(dossier,frais=frais),**kw)


@pytest.mark.parametrize('emploi',[False,True])
def test_imposable_seulement_soldes_distincts_fifo(emploi):
    d=dossier_capital(emploi=emploi);e=calcul(d)
    base=calculer_estimation_fiscale_2025(d,profil_capital=profil_capital())
    for j in ('federal','quebec'):
        for n in ('total','net'):
            assert getattr(e.revenu,f'revenu_{n}_{j}')==getattr(base.revenu,f'revenu_{n}_{j}')
    assert e.revenu.revenu_imposable_federal==base.revenu.revenu_imposable_federal-1200
    assert e.revenu.revenu_imposable_quebec==base.revenu.revenu_imposable_quebec-1000
    assert e.capital==base.capital and e.rapprochement.retenues_totales==base.rapprochement.retenues_totales
    a,b=e.reports_pertes.soldes
    assert (a.annee,a.utilise_federal,a.utilise_quebec,a.cloture_federale,a.cloture_quebec)==(2018,1000,800,0,0)
    assert (b.annee,b.utilise_federal,b.utilise_quebec,b.cloture_federale,b.cloture_quebec)==(2024,200,200,300,400)
    assert calcul(d)==e


@pytest.mark.parametrize('fed,qc',[('0','0'),('1220','1220'),('100','0'),('0','500'),('1000.01','800.01')])
def test_plafonds_valides_et_conservation(fed,qc):
    e=calcul(p=profil_pertes(demande_federale=fed,demande_quebec=qc))
    for ligne in e.reports_pertes.soldes:
        assert ligne.ouverture_federale==ligne.utilise_federal+ligne.cloture_federale
        assert ligne.ouverture_quebec==ligne.utilise_quebec+ligne.cloture_quebec
    assert sum(s.utilise_federal for s in e.reports_pertes.soldes)==D(fed)
    assert sum(s.utilise_quebec for s in e.reports_pertes.soldes)==D(qc)
    assert e.revenu.revenu_net_federal==e.revenu.revenu_net_quebec==1220


@pytest.mark.parametrize('kw',[{'demande_federale':'1220.01'},{'demande_quebec':'1220.01'},
    {'historique':'2020;100;200','demande_federale':'101','demande_quebec':'0'},
    {'historique':'2020;200;100','demande_federale':'0','demande_quebec':'101'}])
def test_plafond_gain_ou_solde_refuse(kw):
    with pytest.raises(ValueError,match='dépasse'):calcul(p=profil_pertes(**kw))


@pytest.mark.parametrize('produit,perte',[('3000','530'),('4060','0')])
@pytest.mark.parametrize('emploi',[False,True])
def test_perte_2025_sans_deduction_courante(produit,perte,emploi):
    d=dossier_capital(produit,emploi=emploi)
    p=profil_pertes(d,demande_federale='0',demande_quebec='0')
    e=calcul(d,p);base=calculer_estimation_fiscale_2025(d,profil_capital=profil_capital())
    assert e.revenu==base.revenu and e.reports_pertes.perte_2025==D(perte)
    assert sum(s.cloture_federale for s in e.reports_pertes.soldes)==1500+D(perte)
    assert sum(s.cloture_quebec for s in e.reports_pertes.soldes)==1400+D(perte)
    assert sum(s.annee==2025 for s in e.reports_pertes.soldes)==bool(D(perte))
    assert calcul(d,p)==e
    with pytest.raises(ValueError):calcul(d,profil_pertes(d,demande_federale='1',demande_quebec='0'))


@pytest.mark.parametrize('texte',['2003;100;100','1985;100;100','2000;100;100','2025;100;100','2026;100;100',
    '2020;100','2020;100;100;50','2020;-100;100','2020;NaN;100','2020;1e3;100','2020;1.001;100',
    '2020;100;100|2020;200;200','2020;100;100|','année;100;100',None,[],True])
def test_historique_hors_perimetre(texte):
    with pytest.raises(ValueError):valider_profil_reports_pertes_2025(replace(ProfilReportsPertes2025(),historique=texte))


@pytest.mark.parametrize('nom',['demande_federale','demande_quebec'])
@pytest.mark.parametrize('valeur',['','-1','NaN','0.001','1000000000',100,None])
def test_montants_stricts(nom,valeur):
    with pytest.raises(ValueError):valider_profil_reports_pertes_2025(replace(ProfilReportsPertes2025(),**{nom:valeur}))


@pytest.mark.parametrize('nom',['confirme','historique_confirme','retrospectif','cas_exclu'])
@pytest.mark.parametrize('valeur',[1,'true',None])
def test_confirmations_strictes(nom,valeur):
    with pytest.raises(ValueError):valider_profil_reports_pertes_2025(replace(ProfilReportsPertes2025(),**{nom:valeur}))


@pytest.mark.parametrize('kw',[{'confirme':False},{'historique_confirme':False},{'source_federale':''},{'source_quebec':''},{'retrospectif':True},{'cas_exclu':True}])
def test_preuves_et_exclusions(kw):
    with pytest.raises(ValueError):calcul(p=profil_pertes(**kw))


def frais_capital(d,**kw):
    from tests.test_tax_investment_expenses_2025 import profil_frais,ProfilInterets2025,ProfilDividendes2025
    return profil_frais(d,(ProfilInterets2025(),ProfilDividendes2025(),profil_capital()),interets='0',**kw)


@pytest.mark.parametrize('gestion,qc,rajustement',[('500','1000','280'),('1500','1000','1000'),('500','720','0')])
def test_annexe_n_276_et_solde_frais_separe(gestion,qc,rajustement):
    d=dossier_capital(emploi=True);frais=frais_capital(d,gestion=gestion)
    base=calculer_estimation_fiscale_2025(d,profil_capital=profil_capital(),profil_frais_placement=frais)
    e=calcul(d,profil_pertes(d,frais=frais,demande_quebec=qc),frais)
    assert e.reports_pertes.ligne_276==e.frais_placement.ligne_276==D(rajustement)
    assert e.revenu.revenu_net_quebec==base.revenu.revenu_net_quebec
    assert e.revenu.revenu_imposable_quebec==base.revenu.revenu_imposable_quebec-D(qc)+D(rajustement)
    assert e.frais_placement.solde_cloture==base.frais_placement.solde_cloture+D(rajustement)
    assert sum(s.cloture_quebec for s in e.reports_pertes.soldes)==1400-D(qc)
    assert e.capital.cotisation_fss==base.capital.cotisation_fss


def test_report_252_ne_consomme_pas_le_meme_gain():
    d=dossier_capital(emploi=True);frais=frais_capital(d,gestion='500',solde_quebec='2000',demande_252='500',source_report='Historique frais distinct')
    with pytest.raises(ValueError,match='252 excessif'):calcul(d,profil_pertes(d,frais=frais,demande_quebec='500'),frais)
    e=calcul(d,profil_pertes(d,frais=frais,demande_quebec='220'),frais)
    assert e.frais_placement.ligne_252==500 and e.reports_pertes.ligne_290==220


def test_fss_positif_non_reduit_par_pertes():
    d=dossier_capital('44060');p=profil_pertes(d,historique='2019;20000;20000',demande_federale='20000',demande_quebec='20000')
    e=calcul(d,p)
    assert e.revenu.revenu_net_federal==e.revenu.revenu_net_quebec==20000
    assert e.revenu.revenu_imposable_federal==e.revenu.revenu_imposable_quebec==0
    assert e.capital.cotisation_fss==D('18.70')
    assert e.rapprochement.impot_total_preliminaire==D('18.70')


@pytest.mark.parametrize('nom',[n for n,_ in CHAMPS_REPORTS_PERTES])
def test_confirmation_perimee(nom):
    valeur='1' if nom.startswith('demande') else ('2020;100;100' if nom=='historique' else 'Autre preuve')
    with pytest.raises(ValueError,match='périmée'):calcul(p=replace(profil_pertes(),**{nom:valeur}))


def test_changement_dossier_perime():
    with pytest.raises(ValueError,match='périmée'):calcul(dossier_capital('7000'),profil_pertes())


def test_persistance_resume_trace_pdf_et_recalcul(tmp_path):
    e=calcul();chemin=sauvegarder_dossier_fiscal(e.dossier,destination=tmp_path/'cas.json',estimation=e)
    charge=charger_dossier_fiscal(chemin)
    assert charge.profil_reports_pertes==e.profil_reports_pertes
    assert calcul(charge.dossier,charge.profil_reports_pertes)==e
    assert 'REPORTS DE PERTES' in formater_estimation_fiscale_2025(e)
    assert '2018' in str(construire_trace_calcul_fiscal_2025(e)) and '25300' in str(construire_trace_calcul_fiscal_2025(e))
    pdf=exporter_rapport_fiscal_pdf_2025(e,tmp_path/'rapport.pdf')
    with fitz.open(pdf) as doc:texte=''.join(page.get_text() for page in doc)
    assert '25300' in texte and '1 200,00' in texte and '2018' in texte
    assert 'aucun report de perte' not in texte
    contenu=json.loads(chemin.read_text(encoding='utf-8'));contenu.pop('profil_reports_pertes')
    chemin.write_text(json.dumps(contenu),encoding='utf-8')
    assert charger_dossier_fiscal(chemin).profil_reports_pertes==ProfilReportsPertes2025()


@pytest.mark.parametrize('raw',[None,[],True,{'confirme':1},{'retrospectif':True},{'historique':123},{'inconnu':True}])
def test_json_invalide(tmp_path,raw):
    p=sauvegarder_dossier_fiscal(dossier_capital(),destination=tmp_path/'d.json')
    contenu=json.loads(p.read_text(encoding='utf-8'));contenu['profil_reports_pertes']=raw;p.write_text(json.dumps(contenu),encoding='utf-8')
    with pytest.raises(ValueError):charger_dossier_fiscal(p)


def test_credit_age_base_sur_net_et_non_imposable():
    from src.comptaprivee.tax_federal_age_pension_2025 import CreditsFederauxAgePension2025
    d=dossier_capital('44060');p=profil_pertes(d,historique='2020;20000;20000',demande_federale='20000',demande_quebec='20000')
    age=CreditsFederauxAgePension2025(reclamer_montant_age=True,age_65_plus_31_decembre_2025=True,
        revenu_net_ligne_23600=D('0'),resident_canada_toute_annee=True,aucune_regle_deces=True,
        aucun_fractionnement_pension=True,aucun_transfert_conjoint=True,valide_par_comptable=True,source_age='Âge synthétique')
    with pytest.raises(ValueError,match='doit correspondre'):calcul(d,p,credits_federaux_age_pension=age)
    assert calcul(d,p,credits_federaux_age_pension=replace(age,revenu_net_ligne_23600=D('20000'))).revenu.revenu_imposable_federal==0


def test_imposable_negatif_refuse_apres_frais():
    d=dossier_capital();frais=frais_capital(d,gestion='500')
    with pytest.raises(ValueError,match='Imposable négatif'):calcul(d,profil_pertes(d,frais=frais),frais)


def test_perte_2025_rechargee_une_seule_fois(tmp_path):
    d=dossier_capital('3000');p=profil_pertes(d,historique='',demande_federale='0',demande_quebec='0')
    e=calcul(d,p);chemin=sauvegarder_dossier_fiscal(d,destination=tmp_path/'d.json',estimation=e)
    charge=charger_dossier_fiscal(chemin);nouveau=calcul(charge.dossier,charge.profil_reports_pertes)
    assert nouveau.reports_pertes.soldes==e.reports_pertes.soldes
    assert len(nouveau.reports_pertes.soldes)==1 and nouveau.reports_pertes.soldes[0].cloture_federale==530


def test_sauvegarde_et_rechargement_refusent_confirmation_perimee(tmp_path):
    e=calcul()
    with pytest.raises(ValueError,match='diffère'):
        sauvegarder_dossier_fiscal(e.dossier,destination=tmp_path/'bad.json',estimation=e,
            profil_reports_pertes=replace(e.profil_reports_pertes,demande_quebec='999'))
    p=sauvegarder_dossier_fiscal(e.dossier,destination=tmp_path/'d.json',estimation=e)
    contenu=json.loads(p.read_text(encoding='utf-8'));contenu['profil_reports_pertes']['historique']='2018;9000;8000'
    p.write_text(json.dumps(contenu),encoding='utf-8')
    with pytest.raises(ValueError,match='périmée'):charger_dossier_fiscal(p)
