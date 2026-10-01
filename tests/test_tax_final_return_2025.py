"""7H : données fictives exclusivement, aucun prorata fiscal supposé."""
from dataclasses import replace, FrozenInstanceError
from datetime import date
from decimal import Decimal as D
import json
import fitz
import pytest
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_interest_income_2025 import dossier_interets, profil_interets
from tests.test_tax_self_employment_contributions_2025 import dossier_7c
from tests.test_tax_multiple_jurisdictions_2025 import dossier_7g
from src.comptaprivee.tax_final_return_2025 import *
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calcul, formater_estimation_fiscale_2025
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025, formater_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025, exporter_preparation_deces_pdf_2025


def profil(**kw):
    p=Deces2025(date_deces='2025-12-15',reference_representant='REF-FICTIVE',source='Preuve et ventilation fictives',
        rrq_standard_18_64=True,**{n:True for n in CONFIRMATIONS_7H})
    return replace(p,**kw)


def dossier(p=None):
    return replace(_dossier_52000(),deces=p or profil())


@pytest.mark.parametrize('jour,limite', [('2025-01-01','2026-04-30'),('2025-10-31','2026-04-30'),
    ('2025-11-01','2026-05-01'),('2025-11-30','2026-05-30'),('2025-12-01','2026-06-01'),('2025-12-31','2026-06-30')])
def test_echeances_nominales_periode(jour,limite):
    p=profil(date_deces=jour)
    assert echeance_deces_2025(p)==date.fromisoformat(limite)
    texte='\n'.join(lignes_deces_2025(dossier(p)))
    assert f'2025-01-01 au {jour} inclusivement' in texte
    assert 'aucun report automatique' in texte


@pytest.mark.parametrize('champ',EXCLUSIONS_7H)
def test_exclusions(champ):
    with pytest.raises(ValueError,match='Déclaration finale complexe'):
        calcul(dossier(profil(**{champ:True})))


@pytest.mark.parametrize('champ',CONFIRMATIONS_7H)
def test_confirmations_obligatoires(champ):
    with pytest.raises(ValueError,match='confirmations'):
        valider_deces_2025(profil(**{champ:False}))


@pytest.mark.parametrize('kw',[{'date_deces':'2024-12-31'},{'date_deces':'2025-02-29'},
    {'date_deces':'20251215'},{'date_deces':None},{'province':'ON'}, {'source':''},
    {'reference_representant':''},{'revenus_confirmes':1},{'entreprise_active':0},{'declaration_finale':False}])
def test_validation_stricte(kw):
    with pytest.raises(ValueError):valider_deces_2025(profil(**kw))


@pytest.mark.parametrize('mois',range(1,12))
def test_rrq_bloque_avant_tout_calcul(mois,monkeypatch):
    from src.comptaprivee import tax_estimation_2025 as module
    monkeypatch.setattr(module,'calculer_impot_federal_preliminaire_2025',lambda *a,**k:pytest.fail('Calcul interdit'))
    with pytest.raises(ValueError) as exc:calcul(dossier(profil(date_deces=f'2025-{mois:02d}-15')))
    assert str(exc.value)==MESSAGE_RRQ


def test_decembre_standard_accepte_sans_modifier_les_montants():
    avant=calcul(_dossier_52000());apres=calcul(dossier())
    assert apres.revenu==avant.revenu
    assert apres.federal==avant.federal and apres.quebec==avant.quebec
    assert apres.rapprochement==avant.rapprochement
    assert 'Impôt minimum 2025 : non appliqué' in formater_estimation_fiscale_2025(apres)
    assert '2025-12-15' in formater_trace_calcul_fiscal_2025(construire_trace_calcul_fiscal_2025(apres))


@pytest.mark.parametrize('mois',[1,10,11,12])
def test_interets_sans_rrq_acceptes(mois):
    d=replace(dossier_interets(),deces=profil(date_deces=f'2025-{mois:02d}-15'))
    e=calcul(d,profil_interets=profil_interets())
    assert e.revenu.revenu_total_federal==D('20000')
    assert e.rapprochement.remboursement_rrq_excedentaire==0
    assert 'Impôt minimum 2025 : non appliqué' in formater_estimation_fiscale_2025(e)


@pytest.mark.parametrize('montant',['3104.01','3103.99','4000'])
def test_rrq_non_standard_decembre_refuse(montant):
    d=dossier();d=replace(d,donnees_validees=tuple(replace(v,valeur_validee=D(montant))
        if (v.type_document,v.case) in {('T4','17'),('RL-1','B.A')} else v for v in d.donnees_validees))
    with pytest.raises(ValueError,match='ligne 452 requis'):calcul(d)


def test_rpc_refuse():
    from tests.test_tax_estimation_2025 import _validee
    d=dossier();d=replace(d,donnees_validees=d.donnees_validees+(_validee('T4.pdf','T4','16','1'),))
    with pytest.raises(ValueError,match='RPC exclu'):calcul(d)


@pytest.mark.parametrize('fabrique',[dossier_7c,dossier_7g])
def test_autonome_et_interprovincial_refuses(fabrique):
    with pytest.raises(ValueError,match='Déclaration finale complexe'):calcul(replace(fabrique(),deces=profil()))


def test_credit_non_verifie_refuse():
    from src.comptaprivee.tax_living_alone_2025 import PersonneVivantSeule2025
    with pytest.raises(ValueError,match='Crédit/déduction non ouvert'):
        calcul(dossier(),personne_vivant_seule=PersonneVivantSeule2025(source='Demande fictive'))


def test_json_ancien_nouveau_et_blocage_conserve(tmp_path):
    ancien=sauvegarder_dossier_fiscal(_dossier_52000(),destination=tmp_path/'dossier.json')
    brut=json.loads(ancien.read_text(encoding='utf-8'));brut.pop('deces')
    ancien.write_text(json.dumps(brut),encoding='utf-8')
    assert charger_dossier_fiscal(ancien).dossier.deces is None
    d=dossier(profil(date_deces='2025-01-15'))
    chemin=sauvegarder_dossier_fiscal(d,destination=tmp_path/'dossier.json')
    charge=charger_dossier_fiscal(chemin).dossier
    assert charge.deces==d.deces
    with pytest.raises(ValueError,match='ligne 452 requis'):calcul(charge)
    with pytest.raises(ValueError,match='ligne 452 requis'):
        sauvegarder_dossier_fiscal(d,estimation=calcul(_dossier_52000()),destination=tmp_path/'dossier.json')
    brut=json.loads(chemin.read_text(encoding='utf-8'));brut['rapport_pdf']='rapport.pdf'
    chemin.write_text(json.dumps(brut),encoding='utf-8')
    with pytest.raises(ValueError,match='ligne 452 requis'):charger_dossier_fiscal(chemin)


def test_immutable_json_inconnu():
    p=profil()
    with pytest.raises(FrozenInstanceError):p.date_deces='2025-01-01'
    assert deces_depuis_json(deces_vers_json(p))==p
    with pytest.raises(ValueError):deces_depuis_json({**deces_vers_json(p),'remboursement_452':'0'})


def test_pdf_annuel_et_preparation_bloquee(tmp_path):
    annuel=exporter_rapport_fiscal_pdf_2025(calcul(dossier()),tmp_path/'finale.pdf')
    with fitz.open(annuel) as pdf:texte='\n'.join(p.get_text() for p in pdf)
    assert '2025-12-15' in texte and 'Impôt minimum 2025' in texte and '2026-06-15' in texte
    bloque=dossier(profil(date_deces='2025-01-15'))
    preparation=exporter_preparation_deces_pdf_2025(bloque,tmp_path/'preparation.pdf')
    with fitz.open(preparation) as pdf:texte='\n'.join(p.get_text() for p in pdf)
    assert 'CALCUL ANNUEL SUSPENDU' in texte and 'ligne 452 requis' in texte
    with pytest.raises(ValueError,match='ligne 452 requis'):
        exporter_rapport_fiscal_pdf_2025(replace(calcul(dossier()),dossier=bloque),tmp_path/'interdit.pdf')


def test_json_annuel_et_credit_perime_refuse(tmp_path):
    from src.comptaprivee.tax_living_alone_2025 import PersonneVivantSeule2025
    e=calcul(dossier())
    chemin=sauvegarder_dossier_fiscal(e.dossier,estimation=e,destination=tmp_path/'finale.json')
    assert charger_dossier_fiscal(chemin).estimation is not None
    faux=replace(e,personne_vivant_seule=PersonneVivantSeule2025(source='Ancienne demande fictive'))
    with pytest.raises(ValueError,match='Crédit/déduction non ouvert'):formater_estimation_fiscale_2025(faux)
    with pytest.raises(ValueError,match='Crédit/déduction non ouvert'):
        sauvegarder_dossier_fiscal(faux.dossier,estimation=faux,destination=tmp_path/'interdit.json')


@pytest.mark.parametrize('montant',['NaN','Infinity','-1'])
def test_montants_invalides_refuses(montant):
    d=dossier();v=replace(d.donnees_validees[0],valeur_validee=D(montant))
    with pytest.raises(ValueError,match='Decimal fini'):
        calcul(replace(d,donnees_validees=(v,*d.donnees_validees[1:])))


def test_rrq_age_non_confirme_refuse():
    with pytest.raises(ValueError,match='ligne 452 requis'):calcul(dossier(profil(rrq_standard_18_64=False)))
