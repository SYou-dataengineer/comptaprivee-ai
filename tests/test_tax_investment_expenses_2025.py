"""3E : annexe N, FSS, preuves, non-double-compte et persistance."""
from dataclasses import replace
from decimal import Decimal as D
import json
import fitz
import pytest
from src.comptaprivee.tax_investment_expenses_2025 import *
from src.comptaprivee.tax_interest_income_2025 import ProfilInterets2025
from src.comptaprivee.tax_dividend_income_2025 import ProfilDividendes2025
from src.comptaprivee.tax_capital_gains_2025 import ProfilCapital2025
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025, formater_estimation_fiscale_2025
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from tests.test_tax_interest_income_2025 import dossier_interets, profil_interets
from tests.test_tax_dividend_income_2025 import dossier_dividendes, profil_dividendes
from tests.test_tax_capital_gains_2025 import dossier_capital, profil_capital


def profil_frais(dossier=None, profils=None, **kw):
    dossier = dossier or dossier_interets()
    profils = profils or (profil_interets(), ProfilDividendes2025(), ProfilCapital2025())
    p = ProfilFraisPlacement2025(gestion='500', interets='1000', source='Facture synthétique F-2025-1, compte unique',
        paiement='Paiements 2025 vérifiés, frais ventilés', utilisation='Emprunt simple affecté directement au CPG déclaré',
        confirme=True, report_confirme=True)
    p = replace(p, **kw)
    return replace(p, empreinte=empreinte_frais_placement_2025(p, dossier, *profils))


def calcul(dossier=None, p=None, **kw):
    dossier = dossier or dossier_interets()
    return calculer_estimation_fiscale_2025(dossier, profil_interets=profil_interets(),
        profil_frais_placement=p or profil_frais(dossier), **kw)


@pytest.mark.parametrize('emploi', [False, True])
def test_deductions_revenu_total_retenues_fss(emploi):
    d = dossier_interets(emploi=emploi)
    base = calculer_estimation_fiscale_2025(d, profil_interets=profil_interets())
    e = calcul(d)
    assert e.revenu.revenu_total_federal == base.revenu.revenu_total_federal
    assert e.revenu.revenu_total_quebec == base.revenu.revenu_total_quebec
    for juridiction in ('federal', 'quebec'):
        for niveau in ('net', 'imposable'):
            assert getattr(e.revenu, f'revenu_{niveau}_{juridiction}') == getattr(base.revenu, f'revenu_{niveau}_{juridiction}')-1500
    assert e.frais_placement.ligne_22100 == e.frais_placement.ligne_231 == 1500
    assert e.frais_placement.ligne_260 == 0
    assert e.interets.cotisation_fss == e.frais_placement.cotisation_fss == D('3.70')
    assert e.rapprochement.retenues_totales == base.rapprochement.retenues_totales
    assert e.rapprochement.impot_total_preliminaire == e.rapprochement.impot_federal_apres_abattement + e.quebec.impot_quebec_preliminaire + D('3.70')


@pytest.mark.parametrize('revenus,frais,ajustement,net_qc', [('1000','1500','500','50095'),('1500','1500','0','50095'),('2000','1500','0','50595')])
def test_annexe_n_excedent_contre_salaire(revenus, frais, ajustement, net_qc):
    d=dossier_interets(revenus, True);e=calcul(d, profil_frais(d, gestion=frais, interets='0'))
    assert e.revenu.revenu_net_federal == D('51515')+D(revenus)-D(frais)
    assert e.revenu.revenu_net_quebec == D(net_qc)
    assert e.frais_placement.ligne_260 == e.frais_placement.solde_cloture == D(ajustement)
    assert e.frais_placement.ligne_276 == 0


@pytest.mark.parametrize('solde,demande,cloture', [('0','0','0'),('1000','1000','0'),('2000','700','1300'),('30000','18500','11500')])
def test_reports_soldes_separes_et_fss_inchange(solde, demande, cloture):
    p=profil_frais(solde_quebec=solde, demande_252=demande, source_report='Annexes N depuis 2004 et toutes utilisations vérifiées')
    e=calcul(p=p);r=e.frais_placement
    assert r.solde_ouverture==D(solde) and r.solde_cloture==D(cloture)
    assert e.revenu.revenu_net_federal==18500
    assert e.revenu.revenu_net_quebec==18500-D(demande)
    assert r.cotisation_fss==D('3.70') and r.assiette_fss==18500
    assert calcul(p=p)==e  # Aucun solde d'ouverture muté ni consommation répétée.


@pytest.mark.parametrize('solde,demande',[('100','101'),('30000','18501'),('0','1')])
def test_report_hors_plafond_refuse(solde,demande):
    with pytest.raises(ValueError,match='Report 252'):
        calcul(p=profil_frais(solde_quebec=solde,demande_252=demande,source_report='Historique vérifié'))


@pytest.mark.parametrize('champ', ['gestion','interets','solde_quebec','demande_252'])
@pytest.mark.parametrize('valeur', ['', '-1', 'NaN', 'Infinity', '1e3', '0.001', '1 000', '1000000000', 1, None])
def test_montants_stricts(champ,valeur):
    with pytest.raises(ValueError):valider_profil_frais_placement_2025(replace(ProfilFraisPlacement2025(),**{champ:valeur}))


@pytest.mark.parametrize('champ',['confirme','report_confirme','cas_exclu'])
@pytest.mark.parametrize('valeur',[1,'true',None])
def test_booleens_stricts(champ,valeur):
    with pytest.raises(ValueError):valider_profil_frais_placement_2025(replace(ProfilFraisPlacement2025(),**{champ:valeur}))


@pytest.mark.parametrize('changement',[{'confirme':False},{'report_confirme':False},{'source':''},{'paiement':''},{'utilisation':''},{'devise':'USD'},{'cas_exclu':True},{'solde_quebec':'100','source_report':''}])
def test_preuves_et_exclusions(changement):
    with pytest.raises(ValueError):calcul(p=profil_frais(**changement))


def test_dividendes_majores_pour_n_reels_pour_fss():
    d=dossier_dividendes();profils=(ProfilInterets2025(),profil_dividendes(),ProfilCapital2025())
    p=profil_frais(d,profils,gestion='500',interets='1000',utilisation='Actions productrices de dividendes')
    e=calculer_estimation_fiscale_2025(d,profil_dividendes=profils[1],profil_frais_placement=p)
    assert e.frais_placement.revenus_n36==25300
    assert e.revenu.revenu_total_federal==25300 and e.revenu.revenu_net_federal==23800
    assert e.frais_placement.assiette_fss==18500
    assert e.dividendes.ligne_40425==D('3111.19') and e.dividendes.ligne_415==D('2007.90')


def test_capital_frais_gestion_distincts_du_courtage():
    d=dossier_capital();profils=(ProfilInterets2025(),ProfilDividendes2025(),profil_capital())
    p=profil_frais(d,profils,interets='0')
    e=calculer_estimation_fiscale_2025(d,profil_capital=profils[2],profil_frais_placement=p)
    assert e.capital.gain_perte==2440 and e.capital.ligne_139==1220
    assert e.frais_placement.ligne_231==500 and e.revenu.revenu_net_quebec==720
    with pytest.raises(ValueError,match='après vente'):
        calculer_estimation_fiscale_2025(d,profil_capital=profils[2],profil_frais_placement=profil_frais(d,profils))


@pytest.mark.parametrize('revenus,frais,fss',[('18130','0','0'),('18131','1','0'),('20000','1870','0'),('20000','1869','.01'),('64060','1000','150'),('64061','1000','150.01')])
def test_frontieres_fss(revenus,frais,fss):
    d=dossier_interets(revenus);e=calcul(d,profil_frais(d,gestion=frais,interets='0'))
    assert e.frais_placement.cotisation_fss==D(fss)


def test_deficit_et_imr_refuses():
    d=dossier_interets('100')
    with pytest.raises(ValueError,match='déficit'):calcul(d)
    d=dossier_interets('180000')
    with pytest.raises(ValueError,match='minimum'):calcul(d,profil_frais(d,gestion='60000',interets='0'))


@pytest.mark.parametrize('texte,attendu', [('2025\nFrais de gestion : 123,45 CAD',{'gestion':'123.45'}),('2025\nIntérêts payés : 456.78 $',{'interets':'456.78'}),('2025\nFrais de garde : 12\nIntérêts sur emprunt : 15',{'gestion':'12','interets':'15'})])
def test_extraction_propositions(texte,attendu):
    assert extraire_frais_placement_2025(texte)==attendu


@pytest.mark.parametrize('texte',['2024\nFrais de gestion : 123','2025 2024\nFrais de gestion : 123','2025\nFrais de gestion : -123','2025\nFrais de gestion : 1.234','2025\nFrais de gestion : 123\nFrais de gestion : 123','2025\nTotal : 123','2025\nFrais de gestion :\n123'])
def test_extraction_ambigue_refusee(texte):
    with pytest.raises(ValueError):extraire_frais_placement_2025(texte)


@pytest.mark.parametrize('nom', [n for n,_ in CHAMPS_FRAIS_PLACEMENT])
def test_confirmation_liee_aux_frais(nom):
    p=profil_frais();valeur='1' if nom in ('gestion','interets','solde_quebec','demande_252') else 'Autre preuve'
    with pytest.raises(ValueError,match='périmée|Historique'):calcul(p=replace(p,**{nom:valeur}))


def test_confirmation_liee_aux_revenus():
    with pytest.raises(ValueError,match='périmée'):calcul(dossier_interets('25000'),profil_frais())


def test_sauvegarde_rechargement_ancien_json_et_resume_pdf(tmp_path):
    e=calcul();chemin=sauvegarder_dossier_fiscal(e.dossier,destination=tmp_path/'cas.json',estimation=e)
    charge=charger_dossier_fiscal(chemin)
    assert charge.profil_frais_placement==e.profil_frais_placement
    assert calcul(charge.dossier,charge.profil_frais_placement)==e
    assert 'FRAIS DE PLACEMENT' in formater_estimation_fiscale_2025(e)
    assert 'Report 252' in str(construire_trace_calcul_fiscal_2025(e))
    pdf=exporter_rapport_fiscal_pdf_2025(e,tmp_path/'rapport.pdf')
    with fitz.open(pdf) as doc:
        texte=''.join(page.get_text() for page in doc)
    assert '22100' in texte and 'N80' in texte and '3,70' in texte
    contenu=json.loads(chemin.read_text(encoding='utf-8'));contenu.pop('profil_frais_placement')
    chemin.write_text(json.dumps(contenu),encoding='utf-8')
    assert charger_dossier_fiscal(chemin).profil_frais_placement==ProfilFraisPlacement2025()


def test_sauvegarde_estimation_perimee_et_json_altere(tmp_path):
    e=calcul()
    with pytest.raises(ValueError,match='diffère'):
        sauvegarder_dossier_fiscal(e.dossier,destination=tmp_path/'bad.json',estimation=e,profil_frais_placement=replace(e.profil_frais_placement,gestion='999'))
    chemin=sauvegarder_dossier_fiscal(e.dossier,destination=tmp_path/'cas.json',estimation=e)
    contenu=json.loads(chemin.read_text(encoding='utf-8'));contenu['profil_frais_placement']['gestion']='999'
    chemin.write_text(json.dumps(contenu),encoding='utf-8')
    with pytest.raises(ValueError,match='périmée'):charger_dossier_fiscal(chemin)


@pytest.mark.parametrize('nature',['BANQUE','CPG_ANNUEL','T3_INTERETS','REMBOURSEMENT_IMPOT'])
def test_parcours_3b_et_report_seul(nature):
    from tests.test_tax_documented_interest_2025 import dossier_documente,profil_documente
    d=dossier_documente(nature);profils=(profil_documente(nature),ProfilDividendes2025(),ProfilCapital2025())
    p=profil_frais(d,profils,gestion='0',interets='0',solde_quebec='1000',demande_252='1000',source_report='Historique complet vérifié')
    e=calculer_estimation_fiscale_2025(d,profil_interets=profils[0],profil_frais_placement=p)
    assert e.revenu.revenu_net_federal==20000 and e.revenu.revenu_net_quebec==19000
    assert e.frais_placement.cotisation_fss==D('18.70')
    p=profil_frais(d,profils)
    if nature=='REMBOURSEMENT_IMPOT':
        with pytest.raises(ValueError,match='remboursement fiscal'):
            calculer_estimation_fiscale_2025(d,profil_interets=profils[0],profil_frais_placement=p)
    else:
        assert calculer_estimation_fiscale_2025(d,profil_interets=profils[0],profil_frais_placement=p).revenu.revenu_net_federal==18500


def test_credit_age_exige_revenu_apres_frais():
    from src.comptaprivee.tax_federal_age_pension_2025 import CreditsFederauxAgePension2025
    p=CreditsFederauxAgePension2025(reclamer_montant_age=True,age_65_plus_31_decembre_2025=True,
        revenu_net_ligne_23600=D('20000'),resident_canada_toute_annee=True,aucune_regle_deces=True,
        aucun_fractionnement_pension=True,aucun_transfert_conjoint=True,valide_par_comptable=True,source_age='Âge synthétique')
    with pytest.raises(ValueError,match='doit correspondre'):calcul(credits_federaux_age_pension=p)
    assert calcul(credits_federaux_age_pension=replace(p,revenu_net_ligne_23600=D('18500'))).federal.impot_federal_de_base==0


def test_reer_ne_reduit_pas_assiette_fss_3e():
    from src.comptaprivee.tax_adjustments_2025 import AjustementReer2025
    e=calcul(dossier_interets(emploi=True),ajustement_reer=AjustementReer2025(D('10000'),D('10000'),'Avis synthétique',True))
    assert e.revenu.revenu_net_federal==60015 and e.frais_placement.cotisation_fss==D('3.70')


@pytest.mark.parametrize('raw',[None,[],True,{'confirme':1},{'devise':'USD'},{'gestion':10},{'inconnu':True}])
def test_json_invalide(tmp_path,raw):
    p=sauvegarder_dossier_fiscal(dossier_interets(),destination=tmp_path/'d.json')
    contenu=json.loads(p.read_text(encoding='utf-8'));contenu['profil_frais_placement']=raw
    p.write_text(json.dumps(contenu),encoding='utf-8')
    with pytest.raises(ValueError):charger_dossier_fiscal(p)


def test_frais_sans_placement_refuses():
    from tests.test_tax_estimation_2025 import _dossier_52000
    d=_dossier_52000();profils=(ProfilInterets2025(),ProfilDividendes2025(),ProfilCapital2025())
    with pytest.raises(ValueError,match='parcours de placement'):
        calculer_estimation_fiscale_2025(d,profil_frais_placement=profil_frais(d,profils))
