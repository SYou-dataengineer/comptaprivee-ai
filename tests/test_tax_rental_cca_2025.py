"""7E : catégorie existante, données fictives, aucun calcul d'addition 2025."""
from dataclasses import replace, FrozenInstanceError
from decimal import Decimal as D
import json
import fitz
import pytest

from src.comptaprivee.tax_rental_cca_2025 import (
    DpaLocation2025, CONFIRMATIONS_7E, MONTANTS_7E, calculer_dpa_location_2025,
    dpa_location_depuis_json, dpa_location_vers_json,
)
from src.comptaprivee.tax_rental_income_2025 import calculer_location_2025
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025, formater_estimation_fiscale_2025
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025, formater_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from tests.test_tax_rental_income_2025 import dossier_location, bien
from tests.test_tax_case_storage import _dossier


def profil(**kw):
    return replace(DpaLocation2025(fnacc_federale=D(100000),pnacc_quebec=D(100000),
        acquisition='2010-01-01',mise_service='2010-01-01',source='Registres et choix fictifs',
        **{n:True for n in CONFIRMATIONS_7E}),**kw)


def dossier_dpa(**kw):
    return dossier_location(amortissement=profil(**kw))


@pytest.mark.parametrize('choix,fin,net',[('0','100000','10000'),('1500','98500','8500'),('4000','96000','6000')])
def test_maximum_choix_et_solde(choix,fin,net):
    p=profil(dpa_federale=D(choix),dpa_quebec=D(choix))
    r=calculer_dpa_location_2025(p,D(10000))
    for x in (r.federal,r.quebec):
        assert x.maximum_theorique==x.maximum_admissible==D(4000)
        assert x.choisie==D(choix) and x.fermeture==D(fin) and x.revenu_apres==D(net)
    with pytest.raises(FrozenInstanceError): p.taux=D('.10')


def test_revenu_faible_limite_et_refus_sans_ecretement_silencieux():
    p=profil(dpa_federale=D(100),dpa_quebec=D(100))
    r=calculer_dpa_location_2025(p,D(100))
    assert r.federal.maximum_theorique==4000 and r.federal.maximum_admissible==100
    assert r.federal.revenu_apres==0 and r.federal.fermeture==99900
    for nom in ('dpa_federale','dpa_quebec'):
        with pytest.raises(ValueError,match='perte'): calculer_dpa_location_2025(profil(**{nom:D('100.01')}),D(100))
        with pytest.raises(ValueError,match='maximum'): calculer_dpa_location_2025(profil(**{nom:D('4000.01')}),D(10000))
    r=calculer_dpa_location_2025(profil(),D(0))
    assert r.federal.maximum_admissible==r.quebec.maximum_admissible==0


def test_soldes_et_choix_independants():
    r=calculer_dpa_location_2025(profil(pnacc_quebec=D(80000),dpa_federale=D(4000),dpa_quebec=D(2500)),D(24000))
    assert r.federal.maximum_theorique==4000 and r.quebec.maximum_theorique==3200
    assert r.federal.fermeture==96000 and r.quebec.fermeture==77500
    assert r.federal.revenu_apres==20000 and r.quebec.revenu_apres==21500


def test_fraction_cent_convention_logicielle():
    r=calculer_dpa_location_2025(profil(fnacc_federale=D('100000.13'),dpa_federale=D('4000.01')),D(10000))
    assert r.federal.maximum_theorique==D('4000.01')
    assert r.federal.fermeture==D('96000.12')


@pytest.mark.parametrize('nom',MONTANTS_7E)
@pytest.mark.parametrize('v',[D('NaN'),D('sNaN'),D('Infinity'),D('-1'),D('.001'),D('1E40'),1.5,'4'])
def test_decimal_invalide(nom,v):
    with pytest.raises(ValueError): calculer_dpa_location_2025(profil(**{nom:v}),D(10000))


@pytest.mark.parametrize('nom',CONFIRMATIONS_7E)
def test_confirmations_strictes(nom):
    for v in (False,1,'oui'):
        with pytest.raises(ValueError): calculer_dpa_location_2025(profil(**{nom:v}),D(10000))


@pytest.mark.parametrize('kw',[
    {'categorie':'3'},{'categorie':['1','3']},{'taux':D('.10')},{'additions_2025':D(1)},
    {'acquisition':'2025-01-01'},{'mise_service':'2025-01-01'},{'mise_service':'2009-01-01'},
    {'acquisition':'invalide'},{'mise_service':None},{'source':' '},
    {'source_federale':'autre'},{'source_quebec':'autre'},
    {'disposition':True},{'recuperation':True},{'perte_finale':True},{'accelere':True},
])
def test_exclusions(kw):
    with pytest.raises(ValueError): calculer_dpa_location_2025(profil(**kw),D(10000))


def test_integration_distincte_federal_quebec_et_fss():
    e=calculer_estimation_fiscale_2025(dossier_dpa(pnacc_quebec=D(80000),dpa_federale=D(4000),dpa_quebec=D(2500)))
    assert e.location.ligne_12599==e.location.ligne_168==24000
    assert e.location.ligne_12600==e.revenu.revenu_net_federal==20000
    assert e.location.ligne_136==e.revenu.revenu_net_quebec==21500
    assert e.location.cotisation_fss==D('33.70')
    x=e.rapprochement
    assert x.solde_estime==x.impot_federal_apres_abattement+e.quebec.impot_quebec_preliminaire+D('33.70')
    assert x.fss_location_446==D('33.70')


def test_salaire_inchange_et_dpa_zero_ne_change_pas_impots():
    d=replace(_dossier(),biens_locatifs=(bien(),))
    avant=calculer_estimation_fiscale_2025(d)
    zero=calculer_estimation_fiscale_2025(replace(d,biens_locatifs=(bien(amortissement=profil()),)))
    assert zero.federal==avant.federal and zero.quebec==avant.quebec and zero.rapprochement==avant.rapprochement
    apres=calculer_estimation_fiscale_2025(replace(d,biens_locatifs=(bien(amortissement=profil(dpa_federale=D(4000),dpa_quebec=D(3000))),)))
    assert apres.base==avant.base
    assert apres.revenu.revenu_net_federal==avant.revenu.revenu_net_federal-4000
    assert apres.revenu.revenu_net_quebec==avant.revenu.revenu_net_quebec-3000
    assert apres.revenu.deduction_travailleur_quebec==avant.revenu.deduction_travailleur_quebec


def test_json_ancien_nouveau_strict_et_persistance(tmp_path):
    d=dossier_dpa(dpa_federale=D(4000),dpa_quebec=D(3000))
    e=calculer_estimation_fiscale_2025(d)
    p=sauvegarder_dossier_fiscal(d,estimation=e,destination=tmp_path/'7e.json')
    assert charger_dossier_fiscal(p).dossier==d
    assert calculer_estimation_fiscale_2025(charger_dossier_fiscal(p).dossier)==e
    brut=json.loads(p.read_text(encoding='utf-8'))
    assert brut['biens_locatifs'][0]['amortissement']['taux']=='0.04'
    assert 'source_quebec' in brut['biens_locatifs'][0]['amortissement']
    ancien=sauvegarder_dossier_fiscal(dossier_location(),destination=tmp_path/'7d.json')
    data=json.loads(ancien.read_text(encoding='utf-8'));data['biens_locatifs'][0].pop('amortissement')
    ancien.write_text(json.dumps(data),encoding='utf-8')
    charge=charger_dossier_fiscal(ancien).dossier
    assert charge.biens_locatifs[0].amortissement is None
    assert calculer_estimation_fiscale_2025(charge)==calculer_estimation_fiscale_2025(dossier_location())
    for valeur in ([],{'inconnu':1},{'fnacc_federale':100000},{'taux':'NaN'}):
        with pytest.raises(ValueError): dpa_location_depuis_json(valeur)


def test_trace_et_pdf(tmp_path):
    e=calculer_estimation_fiscale_2025(dossier_dpa(dpa_federale=D(4000),dpa_quebec=D(3000)))
    structure=construire_trace_calcul_fiscal_2025(e)
    assert next(l.montant for l in structure.lignes if l.libelle=='Fédéral solde final')==D(96000)
    assert next(l.montant for l in structure.lignes if l.libelle=='Québec DPA choisie')==D(3000)
    trace=formater_trace_calcul_fiscal_2025(structure)
    for t in ('FNACC','PNACC','4000.00','3000.00','96000.00','97000.00','sans objet'):
        assert t in trace
    assert 'DPA / récupération / perte finale / part personnelle : 0.00' not in trace
    assert 'fédéral 12600 : 20000.00' in trace and 'Québec 136 : 21000.00' in trace
    p=exporter_rapport_fiscal_pdf_2025(e,tmp_path/'dpa.pdf')
    with fitz.open(p) as pdf:
        texte=''.join(page.get_text() for page in pdf)
        assert '96000.00' in texte and '97000.00' in texte
        for page in pdf:
            for b in page.get_text('blocks'): assert b[2]<page.rect.width-35
