"""7C autonome pur : montants fictifs et convention monétaire du moteur."""
from dataclasses import replace
from decimal import Decimal as D
import json
import fitz
import pytest
from tests.test_tax_self_employment_2025 import dossier, entreprise
from tests.test_tax_case_storage import _dossier
from src.comptaprivee.tax_self_employment_contributions_2025 import (
    ProfilCotisationsAutonomes2025, CONFIRMATIONS_7C, calculer_cotisations_autonomes_2025,
    valider_profil_7c, profil_7c_depuis_json,
)
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025, formater_estimation_fiscale_2025
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025, formater_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025


def profil(**kw):
    return replace(ProfilCotisationsAutonomes2025(activer=True,naissance='1980-01-01',source='Audit fictif 7C',
        **{n:True for n in CONFIRMATIONS_7C}),**kw)


def dossier_7c(net='10000'):
    return replace(dossier(),entreprises=(entreprise(revenu_brut=D(net)),),profil_cotisations_autonomes=profil())


@pytest.mark.parametrize('net,payable',[('3500.04','0'),('3500.05','0'),('3500.06','0'),('3500.08','.01')])
def test_u99_arrondis_et_voisins(net,payable):
    c=calculer_cotisations_autonomes_2025(dossier_7c(net),profil())
    assert c.rrq_445==D(payable)
    for _,v in (*c.lignes_u,*c.lignes_s8,*c.lignes_r): assert v==v.quantize(D('.01'))
    u=dict(c.lignes_u)
    assert u['98']==u['97']*2
    assert u['99']==min(u['94'],u['98'])


@pytest.mark.parametrize('net,rrq,ded',[
    ('0','0','0'),('3500','0','0'),('10000','832','481'),
    ('71299','8678.27','5017.13'),('71300','8678.40','5017.20'),
    ('71301','8678.48','5017.28'),('81200','9470.40','5809.20'),('100000','9470.40','5809.20')])
def test_rrq_bases_plafonds_et_tranche_2(net,rrq,ded):
    c=calculer_cotisations_autonomes_2025(dossier_7c(net),profil())
    assert c.rrq_445==D(rrq)
    assert c.rrq_deduction_248==D(ded)
    assert c.deduction_22200==D(ded)
    assert c.base_31000<=D('3661.20')


@pytest.mark.parametrize('net,rqap,ded,credit',[
    ('0','0','0','0'),('1999.99','0','0','0'),('2000','17.56','7.68','9.88'),
    ('2000.01','17.56','7.68','9.88'),('98000','860.44','376.32','484.12'),('100000','860.44','376.32','484.12')])
def test_rqap_seuil_2000_et_ligne97_zero(net,rqap,ded,credit):
    c=calculer_cotisations_autonomes_2025(dossier_7c(net),profil())
    assert (c.rqap_439,c.rqap_deduction_248,c.deduction_22300,c.base_31215)==(D(rqap),D(ded),D(ded),D(credit))
    assert c.deduction_22300+c.base_31215==c.rqap_439


@pytest.mark.parametrize('naissance',['1960-12-31','2007-01-01','2008-01-01','invalide'])
def test_age_et_proratas_exclus(naissance):
    with pytest.raises(ValueError): valider_profil_7c(profil(naissance=naissance))


@pytest.mark.parametrize('nom',list(CONFIRMATIONS_7C))
def test_confirmations_et_types(nom):
    for valeur in (False,'oui',1):
        with pytest.raises(ValueError): valider_profil_7c(profil(**{nom:valeur}))


@pytest.mark.parametrize('case',['16','16A','96','96.1','96.2'])
def test_rpc_et_le35_refuses(case):
    salaire=_dossier()
    donnee=replace(salaire.donnees_validees[0],case=case,valeur_validee=D(100))
    d=replace(dossier_7c(),donnees_validees=(donnee,))
    with pytest.raises(ValueError,match='LE-35'): calculer_estimation_fiscale_2025(d)


def test_salaire_mixte_et_6i_refuses():
    d=replace(_dossier(),entreprises=dossier_7c().entreprises,profil_cotisations_autonomes=profil())
    with pytest.raises(ValueError,match='autonome pur'): calculer_estimation_fiscale_2025(d)
    from tests.test_tax_quebec_work_premium_2025 import profil as profil_prime
    with pytest.raises(ValueError,match='prime_travail_quebec'):
        calculer_estimation_fiscale_2025(dossier_7c(),prime_travail_quebec=profil_prime())


def test_annuel_deductions_credits_et_cotisations_une_fois():
    e=calculer_estimation_fiscale_2025(dossier_7c())
    assert e.revenu.revenu_total_federal==D(10000)
    assert e.revenu.revenu_net_federal==D('9480.60')
    assert e.revenu.revenu_net_quebec==D('8880.60')
    assert e.revenu.deduction_rrq_amelioree_federale==0
    assert e.federal.cotisation_base_rrq==0
    credits=dict(e.federal.credits_federaux_complets.montants_par_ligne)
    assert credits['30800']==0 and credits['31000']==D(351) and credits['31215']==D('49.40')
    assert e.rapprochement.solde_estime==D('919.80')
    assert e.rapprochement.rrq_autonome_445==D(832)
    assert e.rapprochement.rqap_autonome_439==D('87.80')


def test_fss_et_rapprochement_haut_revenu():
    e=calculer_estimation_fiscale_2025(dossier_7c('98000'))
    c=e.cotisations_autonomes;x=e.rapprochement
    assert c.fss_446==D('437.54')
    assert x.solde_estime==x.impot_federal_apres_abattement+e.quebec.impot_quebec_preliminaire+c.rrq_445+c.rqap_439+c.fss_446


def test_json_annuel_et_ancien(tmp_path):
    d=dossier_7c();e=calculer_estimation_fiscale_2025(d)
    chemin=sauvegarder_dossier_fiscal(d,estimation=e,destination=tmp_path/'7c.json')
    charge=charger_dossier_fiscal(chemin)
    assert charge.dossier==d
    assert calculer_estimation_fiscale_2025(charge.dossier)==e
    brut=json.loads(chemin.read_text(encoding='utf-8'))
    assert brut['profil_cotisations_autonomes']['activer'] is True
    assert profil_7c_depuis_json(None)==ProfilCotisationsAutonomes2025()
    for invalide in ({'activer':1},{'intrus':True}):
        with pytest.raises(ValueError): profil_7c_depuis_json(invalide)
    brut.pop('profil_cotisations_autonomes')
    chemin.write_text(json.dumps(brut),encoding='utf-8')
    with pytest.raises(ValueError,match='7C'): charger_dossier_fiscal(chemin)


def test_trace_resume_et_pdf(tmp_path):
    e=calculer_estimation_fiscale_2025(dossier_7c())
    trace=formater_trace_calcul_fiscal_2025(construire_trace_calcul_fiscal_2025(e))
    resume=formater_estimation_fiscale_2025(e)
    assert 'U C ligne 99 : 832.00' in trace and 'S8 partie 3 ligne 15 : 481.00' in trace
    for code in ('22200','22300','31000','31215','445','439','446','275'): assert code in resume
    chemin=exporter_rapport_fiscal_pdf_2025(e,tmp_path/'7c.pdf')
    with fitz.open(chemin) as pdf:
        texte=''.join(p.get_text() for p in pdf)
        assert '919.80' in texte and '8880.60' in texte
        assert 'bloquée' not in texte
        for p in pdf:
            for b in p.get_text('blocks'): assert b[2]<p.rect.width-35
