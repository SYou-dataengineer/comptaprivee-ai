"""7D : montants exclusivement fictifs et limites logicielles explicites."""
from dataclasses import replace, FrozenInstanceError
from decimal import Decimal as D
import json
import fitz
import pytest

from src.comptaprivee.tax_rental_income_2025 import (
    BienLocatif2025, CONFIRMATIONS_7D, EXCLUSIONS_7D, MONTANTS_7D,
    calculer_location_2025, locations_depuis_json, locations_vers_json,
)
from src.comptaprivee.tax_validated_case import DossierFiscalValide
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025, formater_estimation_fiscale_2025
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025, formater_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from tests.test_tax_case_storage import _dossier
from tests.test_tax_multiple_employers_2025 import dossier_multiple, profil_multiple


def bien(**kw):
    return replace(BienLocatif2025(reference='Bien fictif', adresse='10 rue Fictive, Québec',
        source='Bail et pièces fictifs', loyers=D(24000), **{n:True for n in CONFIRMATIONS_7D}), **kw)


def dossier_location(**kw):
    return DossierFiscalValide(client='Location fictive 7D',annee_fiscale=2025,province='Québec',
        documents=(),donnees_validees=(),biens_locatifs=(bien(**kw),))


@pytest.mark.parametrize('loyers,autres,depenses,net', [
    ('24000','0','0','24000'), ('12000','100','250','11850'),
    ('500','0','500','0'), ('0','0','0','0')])
def test_net_et_immutabilite(loyers, autres, depenses, net):
    b=bien(loyers=D(loyers),autres_revenus=D(autres),assurance=D(depenses))
    r=calculer_location_2025((b,))
    assert r.ligne_12600==r.ligne_136==D(net)
    assert r.ligne_12599==r.ligne_168==D(loyers)+D(autres)
    with pytest.raises(FrozenInstanceError): b.loyers=D(10)


def test_plusieurs_depenses_et_perte_refusee():
    b=bien(publicite=D(100),assurance=D(800),gestion=D(200),comptabilite=D(300),
           taxes_foncieres=D(2000),services_publics=D(600))
    r=calculer_location_2025((b,))
    assert r.depenses==D(4000) and r.ligne_136==D(20000)
    for perte in (D('.01'),D(10000)):
        with pytest.raises(ValueError,match='perte locative'):
            calculer_location_2025((bien(assurance=D(24000)+perte),))


@pytest.mark.parametrize('nom', MONTANTS_7D)
@pytest.mark.parametrize('v', [D('NaN'),D('sNaN'),D('Infinity'),D('-1'),D('.001'),D('1E40'),1.1,'10'])
def test_montant_invalide(nom,v):
    with pytest.raises(ValueError): calculer_location_2025((bien(**{nom:v}),))


@pytest.mark.parametrize('nom',EXCLUSIONS_7D)
def test_exclusions_explicites(nom):
    for v in (True,1,'oui'):
        with pytest.raises(ValueError,match='hors périmètre'): calculer_location_2025((bien(**{nom:v}),))


@pytest.mark.parametrize('nom',CONFIRMATIONS_7D)
def test_confirmations_strictes(nom):
    for v in (False,1,'oui'):
        with pytest.raises(ValueError): calculer_location_2025((bien(**{nom:v}),))


@pytest.mark.parametrize('kw',[{'debut':'2025-02-01'},{'fin':'2025-12-30'},{'adresse':' '},{'source':None}])
def test_faits_invalides(kw):
    with pytest.raises(ValueError): calculer_location_2025((bien(**kw),))


def test_doublon_et_plusieurs_biens_refuses():
    for biens in ((bien(),bien()),(bien(),bien(reference='Autre')), [bien()]):
        with pytest.raises(ValueError): calculer_location_2025(biens)


def test_annuel_location_pure_pas_de_cotisations_emploi():
    e=calculer_estimation_fiscale_2025(dossier_location())
    assert e.revenu.revenu_total_federal==e.revenu.revenu_net_federal==D(24000)
    assert e.revenu.revenu_total_quebec==e.revenu.revenu_net_quebec==D(24000)
    assert e.revenu.deduction_travailleur_quebec==0
    assert e.federal.cotisation_base_rrq==0
    assert e.cotisations_autonomes is None
    assert e.location.cotisation_fss==D('58.70')
    x=e.rapprochement
    assert x.solde_estime==x.impot_federal_apres_abattement+e.quebec.impot_quebec_preliminaire+D('58.70')
    assert x.rrq_autonome_445==x.rqap_autonome_439==0


def test_salaire_et_location_ajout_net_une_fois():
    d=_dossier();ancien=calculer_estimation_fiscale_2025(d)
    e=calculer_estimation_fiscale_2025(replace(d,biens_locatifs=(bien(assurance=D(4000)),)))
    for jur in ('federal','quebec'):
        for niveau in ('total','net','imposable'):
            n=f'revenu_{niveau}_{jur}'
            assert getattr(e.revenu,n)==getattr(ancien.revenu,n)+D(20000)
    assert e.base==ancien.base
    assert e.revenu.deduction_travailleur_quebec==ancien.revenu.deduction_travailleur_quebec
    assert e.revenu.deduction_rrq_amelioree_federale==ancien.revenu.deduction_rrq_amelioree_federale
    assert e.federal.cotisation_base_rrq==ancien.federal.cotisation_base_rrq
    assert e.rapprochement.retenues_totales==ancien.rapprochement.retenues_totales
    assert e.location.cotisation_fss==D('18.70')


def test_multi_employeurs_7a_inchange():
    d=dossier_multiple(); p=profil_multiple(d)
    e=calculer_estimation_fiscale_2025(replace(d,biens_locatifs=(bien(),)),cotisations_excedentaires=p)
    assert e.federal.cotisation_base_rrq==D(2430)
    assert e.revenu.deduction_rrq_amelioree_federale==D(450)
    assert e.revenu.revenu_total_federal==D(76000)
    assert 'EMPLOYEURS MULTIPLES' in formater_estimation_fiscale_2025(e)


@pytest.mark.parametrize('net,fss', [('18130','0'),('18131','.01'),('20000','18.70'),
                                   ('40000','150'),('63060','150'),('63061','150.01'),('200000','1000')])
def test_fss_sur_net_et_limites(net,fss):
    e=calculer_estimation_fiscale_2025(dossier_location(loyers=D(net)))
    assert e.location.cotisation_fss==D(fss)
    assert e.rapprochement.fss_location_446==D(fss)


def test_7c_et_credit_supplementaire_refuses():
    from tests.test_tax_self_employment_contributions_2025 import dossier_7c
    from src.comptaprivee.tax_self_employment_contributions_2025 import calculer_cotisations_autonomes_2025
    d=replace(dossier_7c(),biens_locatifs=(bien(),))
    with pytest.raises(ValueError,match='7D'): calculer_estimation_fiscale_2025(d)
    with pytest.raises(ValueError,match='7D'): calculer_cotisations_autonomes_2025(d,d.profil_cotisations_autonomes)
    from tests.test_tax_quebec_work_premium_2025 import profil
    with pytest.raises(ValueError,match='prime_travail_quebec'):
        calculer_estimation_fiscale_2025(dossier_location(),prime_travail_quebec=profil())


def test_json_ancien_nouveau_strict_et_estimation(tmp_path):
    d=dossier_location(); e=calculer_estimation_fiscale_2025(d)
    p=sauvegarder_dossier_fiscal(d,estimation=e,destination=tmp_path/'location.json')
    assert charger_dossier_fiscal(p).dossier==d
    assert calculer_estimation_fiscale_2025(charger_dossier_fiscal(p).dossier)==e
    assert locations_depuis_json(None)==()
    assert locations_depuis_json(locations_vers_json(d.biens_locatifs))==d.biens_locatifs
    for mauvais in ({'dpa_montant':'100'},{'loyers':100},{'loyers':'NaN'},{'dpa':True}):
        data=locations_vers_json(d.biens_locatifs);data[0].update(mauvais)
        with pytest.raises(ValueError): locations_depuis_json(data)
    ancien=sauvegarder_dossier_fiscal(_dossier(),destination=tmp_path/'ancien.json')
    brut=json.loads(ancien.read_text(encoding='utf-8'));brut.pop('biens_locatifs')
    ancien.write_text(json.dumps(brut),encoding='utf-8')
    assert charger_dossier_fiscal(ancien).dossier.biens_locatifs==()
    with pytest.raises(ValueError,match='différente'):
        sauvegarder_dossier_fiscal(dossier_location(loyers=D(25000)),estimation=e,destination=p)


def test_trace_et_pdf(tmp_path):
    e=calculer_estimation_fiscale_2025(dossier_location())
    trace=formater_trace_calcul_fiscal_2025(construire_trace_calcul_fiscal_2025(e))
    for code in ('12599','12600','136','168','275','446'): assert code in trace
    assert 'Le brut est informatif; seul le NET' in formater_estimation_fiscale_2025(e)
    p=exporter_rapport_fiscal_pdf_2025(e,tmp_path/'location.pdf')
    with fitz.open(p) as pdf:
        texte=''.join(page.get_text() for page in pdf)
        assert '24000.00' in texte and '58.70' in texte and '12600' in texte
        for page in pdf:
            for b in page.get_text('blocks'): assert b[2]<page.rect.width-35
