"""7J : données fictives, obligations déclaratives, aucun calcul fiscal étranger."""
from dataclasses import replace, FrozenInstanceError
from decimal import Decimal as D
import json
import fitz
import pytest
from tests.test_tax_interest_income_2025 import dossier_interets, profil_interets
from tests.test_tax_final_return_2025 import profil as deces
from src.comptaprivee.tax_foreign_property_2025 import *
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calcul, formater_estimation_fiscale_2025
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025, formater_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025, exporter_preparation_biens_etrangers_pdf_2025


def bien(montant='100000.01', **kw):
    v=D(montant)
    return replace(BienEtranger2025('Compte fictif','compte','USA',v,v,v,D('40'),D('-2'),
        'Relevés fictifs CAD vérifiés',(CoutEtranger2025(DEBUT,v),CoutEtranger2025(FIN,v)),True),**kw)


def profil(biens=None, **kw):
    return replace(InventaireEtranger2025((bien(),) if biens is None else biens,
        'Contrôle fictif exhaustif',True,True,True),**kw)


def dossier(p=None):
    return replace(dossier_interets(),biens_etrangers=p or profil())


@pytest.mark.parametrize('montant,requis,methode',[
    ('99999.99',False,'aucune'),('100000',False,'aucune'),('100000.01',True,'partie A possible'),
    ('249999.99',True,'partie A possible'),('250000',True,'partie B requise'),('250000.01',True,'partie B requise')])
def test_seuils_cout_et_obligations(montant,requis,methode):
    r=preparer_biens_etrangers_2025(dossier(profil((bien(montant),))))
    assert r.cout_total_maximal==D(montant)
    assert r.t1135_requis is requis and r.tp1079_requis is requis and r.ligne_25 is requis
    assert r.methode_federale==methode


def test_vente_en_cours_annee_ne_supprime_pas_obligation():
    b=bien('0',cout_maximal=D('250000'),couts=(CoutEtranger2025(DEBUT,D(0)),
        CoutEtranger2025('2025-06-01T10:00:00',D('250000')),
        CoutEtranger2025('2025-06-01T11:00:00',D(0)),CoutEtranger2025(FIN,D(0))))
    r=preparer_biens_etrangers_2025(dossier(profil((b,))))
    assert r.t1135_requis and r.methode_federale=='partie B requise'
    assert r.moment_maximal=='2025-06-01T10:00:00'


@pytest.mark.parametrize('simultane',[False,True])
def test_maximum_agrege_pas_somme_maxima(simultane):
    moment='2025-07-01T12:00:00'
    a=bien('60000',cout_fin=D(0),couts=(CoutEtranger2025(DEBUT,D(60000)),CoutEtranger2025(moment,D(0)),CoutEtranger2025(FIN,D(0))))
    debut='2025-07-01T11:59:59' if simultane else moment
    b=bien('0',reference='Autre',cout_maximal=D(60000),cout_fin=D(60000),couts=(CoutEtranger2025(DEBUT,D(0)),CoutEtranger2025(debut,D(60000)),CoutEtranger2025(FIN,D(60000))))
    r=preparer_biens_etrangers_2025(dossier(profil((a,b))))
    assert r.cout_total_maximal==D(120000 if simultane else 60000)
    assert r.t1135_requis is simultane


@pytest.mark.parametrize('nature',TYPES_7J)
def test_types_documentes(nature):
    r=preparer_biens_etrangers_2025(dossier(profil((bien(nature=nature),))))
    assert r.t1135_requis


@pytest.mark.parametrize('exclusion',['personnel','REER','RRIF','TFSA','RPP','PRPP','entreprise_active','affiliee','fiducie_complexe','societe_personnes','crypto'])
def test_exclus_refuses(exclusion):
    with pytest.raises(ValueError,match='exclu'):
        valider_inventaire_etranger_2025(profil((bien(exclusion=exclusion),)))


@pytest.mark.parametrize('champ',['cout_debut','cout_maximal','cout_fin','revenu_brut_connu','gain_perte_connu'])
@pytest.mark.parametrize('valeur',['NaN','Infinity','0.001','1000000000'])
def test_montants_invalides(champ,valeur):
    with pytest.raises(ValueError):valider_inventaire_etranger_2025(profil((bien(**{champ:D(valeur)}),)))


@pytest.mark.parametrize('kw',[{'cout_maximal':D('-1')},{'cout_fin':D('1')},{'couts':()},
    {'pays':'ZZZ'},{'pays':'CAN'},{'pays':[]},{'nature':[]},{'nature':'inconnu'},{'source':''},{'qualification_confirmee':False},
    {'couts':(CoutEtranger2025(DEBUT,D('NaN')),CoutEtranger2025(FIN,D(1)))}])
def test_faits_invalides(kw):
    with pytest.raises(ValueError):valider_inventaire_etranger_2025(profil((bien(**kw),)))


@pytest.mark.parametrize('moment',['2024-12-31T23:59:59','2025-06-01','2025-06-01T12:00:00+00:00',DEBUT])
def test_chronologie_invalide(moment):
    b=bien(couts=(CoutEtranger2025(DEBUT,D('100000.01')),CoutEtranger2025(moment,D('100000.01')),CoutEtranger2025(FIN,D('100000.01'))))
    with pytest.raises(ValueError):valider_inventaire_etranger_2025(profil((b,)))


def test_immuable_doublon_et_confirmation():
    p=profil()
    with pytest.raises(FrozenInstanceError):p.confirme=False
    with pytest.raises(ValueError,match='doublon'):valider_inventaire_etranger_2025(profil((bien(),bien(reference=' compte FICTIF '))))
    for n in ('confirme','chronologie_complete','particulier_quebec'):
        with pytest.raises(ValueError):valider_inventaire_etranger_2025(replace(p,**{n:False}))


def test_ancien_nouveau_json_et_aucune_ecriture_monetaire(tmp_path):
    d=dossier();avant=calcul(dossier_interets(),profil_interets=profil_interets())
    apres=calcul(d,profil_interets=profil_interets())
    assert apres.federal==avant.federal and apres.quebec==avant.quebec
    assert apres.revenu==avant.revenu and apres.rapprochement==avant.rapprochement
    f=tmp_path/'fictif.json'
    sauvegarder_dossier_fiscal(d,destination=f,estimation=apres)
    charge=charger_dossier_fiscal(f)
    assert charge.dossier==d
    contenu=json.loads(f.read_text(encoding='utf-8'))
    assert contenu['biens_etrangers']['biens'][0]['cout_maximal']=='100000.01'
    del contenu['biens_etrangers'];f.write_text(json.dumps(contenu),encoding='utf-8')
    assert charger_dossier_fiscal(f).dossier.biens_etrangers is None


@pytest.mark.parametrize('champ',['revenu_imposable','credit_impot_etranger','gain_calcule','t1135_requis','ligne_25'])
def test_json_aucun_calcul_force(champ):
    with pytest.raises(ValueError,match='champ JSON inconnu'):
        inventaire_etranger_depuis_json({**inventaire_etranger_vers_json(profil()),champ:'100'})


def test_sous_seuil_avertissement_et_pdf(tmp_path):
    d=dossier(profil((bien('10'),)));e=calcul(d,profil_interets=profil_interets())
    trace=formater_trace_calcul_fiscal_2025(construire_trace_calcul_fiscal_2025(e))
    assert 'T1135 requis : non' in trace and AVERTISSEMENT in trace
    assert 'BIENS ÉTRANGERS' in formater_estimation_fiscale_2025(e)
    for nom,export,obj in (('preparation',exporter_preparation_biens_etrangers_pdf_2025,d),('annuel',exporter_rapport_fiscal_pdf_2025,e)):
        pdf=export(obj,tmp_path/(nom+'.pdf'))
        with fitz.open(pdf) as doc:texte=''.join(p.get_text() for p in doc)
        assert 'T1135 requis : non' in texte and 'TP-1079.8.BE requis : non' in texte
        assert 'Ligne 25 Québec : non' in texte and 'déclaration du revenu étranger' in texte


@pytest.mark.parametrize('montant',['0','99999.99','100000','100000.01','250000'])
def test_nouvel_arrivant_dispense_et_ligne25_manuelle_sans_perte_faits(tmp_path,montant):
    d=dossier(profil((bien(montant),),premiere_residence_2025=True))
    f=tmp_path/'arrivee.json';sauvegarder_dossier_fiscal(d,destination=f)
    assert charger_dossier_fiscal(f).dossier==d
    r=preparer_biens_etrangers_2025(d)
    assert not r.tp1079_requis and r.ligne_25 is None and r.exception_nouvel_arrivant
    assert r.cout_total_maximal==D(montant)
    # Source ARC spécifique, aucune transposition de la dispense Québec.
    assert not r.t1135_requis and r.methode_federale=='aucune'
    texte='\n'.join(lignes_biens_etrangers_2025(d))
    assert AVERTISSEMENT_ARRIVEE in texte and 'article 233.7' in texte
    assert 'Ligne 25 Québec : à valider manuellement' in texte
    assert 'Ligne 25 Québec : oui' not in texte and 'Ligne 25 Québec : non' not in texte
    pdf=exporter_preparation_biens_etrangers_pdf_2025(d,tmp_path/'arrivee.pdf')
    with fitz.open(pdf) as doc:texte=' '.join(' '.join(p.get_text().split()) for p in doc)
    assert 'TP-1079.8.BE requis : non' in texte
    assert 'Ligne 25 Québec : à valider manuellement' in texte
    assert 'doit être validée lors de la préparation de la déclaration' in texte
    with pytest.raises(ValueError,match='résidence partielle'):calcul(d,profil_interets=profil_interets())


def test_deces_biens_etrangers_non_ouverts():
    with pytest.raises(ValueError):calcul(replace(dossier(),deces=deces()),profil_interets=profil_interets())


def test_estimation_perimee_refusee(tmp_path):
    e=calcul(dossier_interets(),profil_interets=profil_interets())
    with pytest.raises(ValueError):sauvegarder_dossier_fiscal(dossier(),estimation=e,destination=tmp_path/'perime.json')
    avec=calcul(dossier(),profil_interets=profil_interets())
    with pytest.raises(ValueError,match='7J'):
        sauvegarder_dossier_fiscal(dossier_interets(),estimation=avec,destination=tmp_path/'retire.json')


def test_profil_absent_et_inventaire_vide():
    assert preparer_biens_etrangers_2025(dossier_interets()) is None
    r=preparer_biens_etrangers_2025(dossier(profil(())))
    assert r.cout_total_maximal==0 and not r.t1135_requis


@pytest.mark.parametrize('parcours',['emploi','location','autonome'])
def test_parcours_annuels_revenus_inchanges_et_audit_complet(parcours,tmp_path):
    from tests.test_tax_rental_income_2025 import dossier_location
    from tests.test_tax_self_employment_contributions_2025 import dossier_7c
    from tests.test_tax_estimation_2025 import _dossier_52000
    initial={'emploi':_dossier_52000,'location':dossier_location,'autonome':dossier_7c}[parcours]()
    avant=calcul(initial);apres=calcul(replace(initial,biens_etrangers=profil()))
    assert apres.revenu==avant.revenu and apres.federal==avant.federal and apres.quebec==avant.quebec
    assert apres.rapprochement==avant.rapprochement
    assert 'T1135 requis : oui' in formater_estimation_fiscale_2025(apres)
    assert 'Ligne 25 Québec : oui' in formater_trace_calcul_fiscal_2025(construire_trace_calcul_fiscal_2025(apres))
    pdf=exporter_rapport_fiscal_pdf_2025(apres,tmp_path/(parcours+'.pdf'))
    with fitz.open(pdf) as doc:texte=''.join(p.get_text() for p in doc)
    assert 'TP-1079.8.BE requis : oui' in texte


def test_cache_annuel_ne_contourne_pas_garde_fou_arrivee(tmp_path):
    e=calcul(dossier(),profil_interets=profil_interets())
    d=replace(e.dossier,biens_etrangers=profil(premiere_residence_2025=True))
    faux=replace(e,dossier=d)
    for action in (lambda:construire_trace_calcul_fiscal_2025(faux),
        lambda:exporter_rapport_fiscal_pdf_2025(faux,tmp_path/'interdit.pdf'),
        lambda:sauvegarder_dossier_fiscal(d,estimation=faux,destination=tmp_path/'interdit.json')):
        with pytest.raises(ValueError,match='résidence partielle'):action()
    f=tmp_path/'cache.json';sauvegarder_dossier_fiscal(e.dossier,estimation=e,destination=f)
    contenu=json.loads(f.read_text(encoding='utf-8'))
    contenu['biens_etrangers']['premiere_residence_2025']=True
    f.write_text(json.dumps(contenu),encoding='utf-8')
    with pytest.raises(ValueError,match='résidence partielle'):charger_dossier_fiscal(f)
    assert not (tmp_path/'interdit.pdf').exists()
