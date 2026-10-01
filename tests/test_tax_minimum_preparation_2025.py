"""7I : données fictives; aucun test ne valide un calcul monétaire IMR."""
from dataclasses import replace, FrozenInstanceError
from decimal import Decimal as D
import json
import fitz
import pytest
from tests.test_tax_interest_income_2025 import dossier_interets, profil_interets
from tests.test_tax_estimation_2025 import _dossier_52000, _validee
from tests.test_tax_final_return_2025 import profil as deces
from tests.test_tax_multiple_jurisdictions_2025 import dossier_7g
from src.comptaprivee.tax_minimum_preparation_2025 import *
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calcul, formater_estimation_fiscale_2025
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025, formater_trace_calcul_fiscal_2025, construire_trace_imr_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025, exporter_preparation_imr_pdf_2025


def profil(**kw):
    return replace(ProfilImr2025(source='Audit fictif exhaustif', confirme=True, residence_quebec_annee=True), **kw)


def dossier(**kw):
    return replace(dossier_interets(), imr=profil(**kw))


def test_sans_element_aucune_ecriture_et_parcours_ordinaire():
    avant = calcul(dossier_interets(), profil_interets=profil_interets())
    apres = calcul(dossier(), profil_interets=profil_interets())
    assert apres.federal == avant.federal and apres.quebec == avant.quebec
    assert apres.revenu == avant.revenu and apres.rapprochement == avant.rapprochement
    r = preparer_imr_2025(dossier())
    assert not r.t691_requis and not r.tp77642_requis and not r.estimation_suspendue
    assert not hasattr(r, 'montant_imr')
    assert 'Aucun montant écrit automatiquement' in formater_estimation_fiscale_2025(apres)


@pytest.mark.parametrize('montant,position', [('177881.99','sous'), ('177882','égal'), ('177882.01','au-dessus')])
def test_repere_ne_decide_pas_exemption(montant, position):
    r = preparer_imr_2025(dossier(elements=(ElementImr2025('gain_capital',D(montant),'Pièce fictive'),)))
    assert r.position_repere == position
    assert r.t691_requis and r.tp77642_requis and r.estimation_suspendue


@pytest.mark.parametrize('nature', ELEMENTS_7I)
def test_elements_positifs_bloquent_meme_sous_repere(nature, monkeypatch):
    from src.comptaprivee import tax_estimation_2025 as m
    monkeypatch.setattr(m, 'calculer_impot_federal_preliminaire_2025', lambda *a,**k:pytest.fail('Calcul interdit'))
    with pytest.raises(ValueError, match='IMR potentiel'):
        calcul(dossier(elements=(ElementImr2025(nature,D('.01'),'Pièce fictive'),)), profil_interets=profil_interets())


@pytest.mark.parametrize('nom', ['t691_signale', 'tp77642_signale'])
def test_signal_independant_du_total(nom):
    r = preparer_imr_2025(dossier(**{nom:True}))
    assert r.total_elements_declares == 0 and r.estimation_suspendue
    assert r.t691_requis == (nom == 't691_signale')
    assert r.tp77642_requis == (nom == 'tp77642_signale')


@pytest.mark.parametrize('registre,annee', [(n,a) for n in ('soldes_federaux','soldes_quebec') for a in (2016,2018,2024)])
def test_soldes_separes_sans_expiration_ni_utilisation_inventee(registre, annee):
    d = dossier(**{registre:(SoldeImr2025(annee,D('100'),'Avis fictif confirmé'),)})
    r = preparer_imr_2025(d)
    assert r.t691_requis == (registre == 'soldes_federaux')
    assert r.tp77642_requis == (registre == 'soldes_quebec')
    assert r.estimation_suspendue
    assert 'expiration, utilisation et reliquat non calculés' in '\n'.join(lignes_imr_2025(d))
    assert getattr(d.imr,registre)[0].montant_confirme == D('100')


def test_memes_annees_autorisees_dans_juridictions_distinctes():
    s = SoldeImr2025(2024,D('50'),'Avis fictif')
    valider_imr_2025(profil(soldes_federaux=(s,),soldes_quebec=(s,)))
    with pytest.raises(ValueError, match='doublon'):
        valider_imr_2025(profil(soldes_federaux=(s,s)))


@pytest.mark.parametrize('v', ['NaN','Infinity','-1','.001','1000000000'])
def test_decimaux_invalides(v):
    with pytest.raises(ValueError): valider_imr_2025(profil(elements=(ElementImr2025('garde',D(v),'Source'),)))
    with pytest.raises(ValueError): valider_imr_2025(profil(soldes_federaux=(SoldeImr2025(2024,D(v),'Source'),)))


@pytest.mark.parametrize('kw', [{'confirme':1}, {'confirme':False}, {'source':''}, {'elements':[]},
    {'soldes_quebec':[]}, {'soldes_federaux':(SoldeImr2025(2025,D('1'),'Source'),)},
    {'elements':(ElementImr2025('impot_final',D('1'),'Source'),)},
    {'elements':(ElementImr2025('garde',D('1'),''),)}])
def test_validation_stricte(kw):
    with pytest.raises(ValueError): valider_imr_2025(profil(**kw))


def test_immuable_et_doublon_element():
    p=profil()
    with pytest.raises(FrozenInstanceError): p.confirme=False
    e=ElementImr2025('garde',D('1'),'Source')
    with pytest.raises(ValueError): valider_imr_2025(profil(elements=(e,e)))


def test_detection_feuillets_sans_inventer_deduction():
    d=replace(_dossier_52000(),imr=profil())
    r=preparer_imr_2025(d)
    assert r.estimation_suspendue and r.total_elements_declares == 0
    assert any('T4 case 17' in m for m in r.motifs)


def test_deces_prioritaire_et_reports_refuses():
    d=replace(_dossier_52000(),deces=deces(),imr=profil(t691_signale=True,tp77642_signale=True))
    r=preparer_imr_2025(d)
    assert r.deces and not r.t691_requis and not r.tp77642_requis
    assert calcul(d).rapprochement == calcul(replace(d,imr=None)).rapprochement
    assert 'IMR courant non appliqué' in '\n'.join(lignes_imr_2025(d))
    d=replace(d,imr=profil(soldes_federaux=(SoldeImr2025(2024,D('10'),'Avis'),)))
    with pytest.raises(ValueError,match='7H.*reports IMR'): calcul(d)


def test_interprovincial_reste_bloque():
    with pytest.raises(ValueError,match='interprovincial'):
        calcul(replace(dossier_7g(),imr=profil()))


def test_residence_non_confirmee_bloque():
    with pytest.raises(ValueError,match='résidence annuelle'):
        calcul(dossier(residence_quebec_annee=False),profil_interets=profil_interets())


def test_json_ancien_nouveau_et_pas_de_resultat_fiscal(tmp_path):
    p=profil(elements=(ElementImr2025('garde',D('12.34'),'Reçu fictif'),),
        soldes_federaux=(SoldeImr2025(2024,D('50.01'),'Avis ARC fictif'),),
        soldes_quebec=(SoldeImr2025(2023,D('30.02'),'Avis RQ fictif'),))
    assert imr_depuis_json(imr_vers_json(p)) == p
    assert imr_depuis_json(None) is None
    chemin=sauvegarder_dossier_fiscal(replace(dossier_interets(),imr=p),destination=tmp_path/'faits.json')
    assert charger_dossier_fiscal(chemin).dossier.imr == p
    contenu=json.loads(chemin.read_text(encoding='utf-8'))
    del contenu['imr'];chemin.write_text(json.dumps(contenu),encoding='utf-8')
    assert charger_dossier_fiscal(chemin).dossier.imr is None
    contenu['imr']=imr_vers_json(p);contenu['rapport_pdf']='ancien.pdf'
    chemin.write_text(json.dumps(contenu),encoding='utf-8')
    with pytest.raises(ValueError,match='IMR potentiel'):charger_dossier_fiscal(chemin)


@pytest.mark.parametrize('nom',['ligne_41700','ligne_40427','ligne_432','montant_imr'])
def test_json_impot_final_refuse(nom):
    with pytest.raises(ValueError,match='impôt final'):
        imr_depuis_json({**imr_vers_json(profil()),nom:'10'})


def test_ancien_resume_et_export_ne_contournent_pas_blocage(tmp_path):
    e=calcul(dossier_interets(),profil_interets=profil_interets())
    d=dossier(t691_signale=True)
    faux=replace(e,dossier=d)
    for action in (lambda:construire_trace_calcul_fiscal_2025(faux),
            lambda:exporter_rapport_fiscal_pdf_2025(faux,tmp_path/'interdit.pdf'),
            lambda:sauvegarder_dossier_fiscal(d,estimation=e,destination=tmp_path/'interdit.json')):
        with pytest.raises(ValueError,match='IMR potentiel'): action()
    assert not (tmp_path/'interdit.pdf').exists()


def test_traces_et_pdf_preparation_et_annuel(tmp_path):
    d=dossier(t691_signale=True)
    texte='\n'.join(construire_trace_imr_2025(d))
    assert 'T691 requis : oui' in texte and 'Montant non calculé' in texte
    pdf=exporter_preparation_imr_pdf_2025(d,tmp_path/'preparation.pdf')
    with fitz.open(pdf) as doc:
        texte=''.join(p.get_text() for p in doc)
    assert '41700/40427/432' in texte and 'CALCUL ANNUEL SUSPENDU' in texte
    e=calcul(dossier(),profil_interets=profil_interets())
    trace=formater_trace_calcul_fiscal_2025(construire_trace_calcul_fiscal_2025(e))
    assert 'IMR 2025' in trace
    pdf=exporter_rapport_fiscal_pdf_2025(e,tmp_path/'annuel.pdf')
    with fitz.open(pdf) as doc:texte=''.join(p.get_text() for p in doc)
    assert '41700/40427/432' in texte


def test_options_connues_bloquent_meme_sans_faits_saisis():
    from src.comptaprivee.tax_capital_gains_2025 import ProfilCapital2025
    with pytest.raises(ValueError,match='IMR potentiel'):
        calcul(dossier(),profil_interets=profil_interets(),profil_capital=ProfilCapital2025(source='Fait fictif'))
