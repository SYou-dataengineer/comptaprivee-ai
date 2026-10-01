"""Entrées non finies, typage, historique et CSV : données fictives."""
import csv
import io
import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
import pytest
from tests.test_tax_case_storage import _dossier
from tests.test_tax_field_validation import _donnee
from src.comptaprivee.tax_field_validation import corriger_et_valider_donnee_fiscale, valider_donnee_fiscale
from src.comptaprivee.tax_field_extractor import convertir_montant_fiscal, extraire_cases_fiscales
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal, dossier_fiscal_depuis_contenu
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
from src.comptaprivee.tax_engine_input_2025 import consolider_base_fiscale_emploi_2025
from src.comptaprivee.csv_exporter import exporter_facture_csv, RedacteurCsvSur, neutraliser_texte_csv
from src.comptaprivee.facture_parser import DonneesFacture


@pytest.mark.parametrize('valeur',['NaN','nan','sNaN','Infinity','inf','-Infinity'])
def test_non_fini_tous_chemins(valeur):
    with pytest.raises(ValueError): convertir_montant_fiscal(valeur)
    with pytest.raises(ValueError): corriger_et_valider_donnee_fiscale(_donnee(),valeur)
    with pytest.raises(ValueError): corriger_et_valider_donnee_fiscale(_donnee(),Decimal(valeur))
    with pytest.raises(ValueError): valider_donnee_fiscale(replace(_donnee(),valeur=Decimal(valeur)))
    with pytest.raises(ValueError): replace(valider_donnee_fiscale(_donnee()),valeur_validee=Decimal(valeur))


def contenu(tmp_path):
    d=_dossier();e=calculer_estimation_fiscale_2025(d)
    p=sauvegarder_dossier_fiscal(d,estimation=e,destination=tmp_path/'d.json')
    return json.loads(p.read_text(encoding='utf-8'))


@pytest.mark.parametrize('valeur',['NaN','Infinity','-Infinity',float('nan'),float('inf'),True,[],{},'1_000',' 5 '])
def test_montant_json_refuse(tmp_path,valeur):
    c=contenu(tmp_path);c['donnees_validees'][0]['valeur_validee']=valeur
    with pytest.raises(ValueError):dossier_fiscal_depuis_contenu(c,verifier_documents=False)


@pytest.mark.parametrize('valeur',[2025.9,2025.0,True,'2025',None])
def test_annee_json_stricte(tmp_path,valeur):
    c=contenu(tmp_path);c['annee_fiscale']=valeur
    with pytest.raises(ValueError):dossier_fiscal_depuis_contenu(c,verifier_documents=False)


@pytest.mark.parametrize('valeur',['false','true',0,1,[],None])
def test_booleen_json_strict(tmp_path,valeur):
    c=contenu(tmp_path);c['donnees_validees'][0]['corrigee']=valeur
    with pytest.raises(ValueError):dossier_fiscal_depuis_contenu(c,verifier_documents=False)
    c['donnees_validees'][0]['corrigee']=False
    c['deduction_celiapp']['valide_par_comptable']=valeur
    with pytest.raises(ValueError):dossier_fiscal_depuis_contenu(c,verifier_documents=False)


@pytest.mark.parametrize('champ',[None,'montant','impot_total_preliminaire','retenues_totales'])
def test_historique_non_verifie_et_recalcul(tmp_path,champ):
    c=contenu(tmp_path)
    if champ:c['derniere_estimation'][champ]='999999'
    charge=dossier_fiscal_depuis_contenu(c,verifier_documents=False)
    assert not charge.estimation.verifie
    assert 'recalcul requis' in charge.estimation.statut_verification
    nouveau=calculer_estimation_fiscale_2025(charge.dossier)
    assert nouveau.rapprochement.remboursement_estime==Decimal('5611.05')


def test_ancien_et_tronque(tmp_path):
    c=contenu(tmp_path);c.pop('case_id');c.pop('derniere_estimation')
    assert dossier_fiscal_depuis_contenu(c,verifier_documents=False).estimation is None
    del c['donnees_validees'][0]['valeur_validee']
    with pytest.raises(ValueError):dossier_fiscal_depuis_contenu(c,verifier_documents=False)


def test_t4_16a_coexistence_et_refus_rpc():
    texte='Case 16 : 100,00\nCase 16A : 25,00\nCase 17 : 200,00\nCase 17A : 30,00\nCase 26 : 52000,00'
    donnees=extraire_cases_fiscales('T4',texte,'T4.pdf')
    assert {d.case:d.valeur for d in donnees}=={'16':Decimal(100),'16A':Decimal(25),'17':Decimal(200),'17A':Decimal(30),'26':Decimal(52000)}
    d16a=next(d for d in donnees if d.case=='16A')
    dossier=_dossier();dossier=replace(dossier,donnees_validees=dossier.donnees_validees+(valider_donnee_fiscale(d16a),))
    with pytest.raises(ValueError,match='RPC'):consolider_base_fiscale_emploi_2025(dossier)


def test_case16a_incomplete_ne_prend_pas_17():
    ds=extraire_cases_fiscales('T4','Case 16A : illisible\nCase 17 : 250,00','t.pdf')
    assert not any(d.case=='16A' for d in ds)


@pytest.mark.parametrize('texte',['=1+1','+CMD','-1+1','@SUM(A1)','\t=1+1','  =1+1','\n@SUM(A1)'])
def test_csv_formules_et_numeriques(tmp_path,texte):
    f=DonneesFacture(texte,None,texte,texte,Decimal('-12.50'),None,None,Decimal('1'))
    p=exporter_facture_csv(f,tmp_path/'f.csv')
    with p.open(encoding='utf-8-sig',newline='') as stream:r=next(csv.DictReader(stream,delimiter=';'))
    assert r['numero']=="'"+texte and r['sous_total']=='-12.50'
    stream=io.StringIO();RedacteurCsvSur(stream).writerow([texte,-12.5,'Été fictif'])
    assert next(csv.reader(io.StringIO(stream.getvalue())))==["'"+texte,'-12.5','Été fictif']


@pytest.mark.parametrize('texte',['Ordinaire','Été fictif','123',"'=1+1"])
def test_csv_texte_ordinaire(texte):
    assert neutraliser_texte_csv(texte)==texte


@pytest.mark.parametrize('seconde',['25,00','26,00'])
def test_case16a_dupliquee_refusee(seconde):
    with pytest.raises(ValueError,match='16A'):
        extraire_cases_fiscales('T4','Case 16A : 25,00\nBox 16A : '+seconde,'t.pdf')


def test_roundtrip_json_recalcul_sans_modifier_faits(tmp_path):
    c=contenu(tmp_path)
    charge=dossier_fiscal_depuis_contenu(c,verifier_documents=False)
    e=calculer_estimation_fiscale_2025(charge.dossier)
    p=sauvegarder_dossier_fiscal(charge.dossier,estimation=e,destination=tmp_path/'recalcule.json')
    nouveau=charger_dossier_fiscal(p)
    assert nouveau.dossier.case_id==charge.dossier.case_id
    assert nouveau.dossier.donnees_validees==charge.dossier.donnees_validees
    assert nouveau.estimation.montant==Decimal('5611.05')
    assert not nouveau.estimation.verifie
