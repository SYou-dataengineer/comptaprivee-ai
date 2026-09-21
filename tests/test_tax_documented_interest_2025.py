"""3B : intérêts sourcés, périodes, ventilation T3 et refus de doubles comptes."""
from dataclasses import replace
from decimal import Decimal as D
from pathlib import Path
import json
import fitz
import pytest
from src.comptaprivee.tax_interest_income_2025 import ProfilInterets2025, valider_profil_interets_2025
from src.comptaprivee.tax_documented_interest_2025 import NATURES_INTERETS_DOCUMENTES
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025, formater_estimation_fiscale_2025
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
from src.comptaprivee.tax_document_classifier import classifier_document_fiscal
from src.comptaprivee.tax_field_extractor import extraire_cases_fiscales
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from tests.test_tax_estimation_2025 import _dossier_52000, _validee
from tests.test_tax_interest_income_2025 import dossier_interets


def profil_documente(nature='BANQUE'):
    return ProfilInterets2025(source='Pièces synthétiques complètes et exclusions vérifiées',confirme=True,
        nature=nature,identifiant_source='SOURCE-SYNTHETIQUE-1',date_debut='2025-01-01',date_fin='2025-12-31',
        echeancier_confirme=nature=='CPG_ANNUEL',ventilation_confirmee=nature=='T3_INTERETS')


def dossier_documente(nature='BANQUE',montant='20000',emploi=False):
    d=_dossier_52000()
    if not emploi:d=replace(d,documents=(),donnees_validees=())
    cases=[('T3','26','T3.pdf'),('RL-16','G','RL-16.pdf')] if nature=='T3_INTERETS' else [('INTERETS',nature,'Etat interets 2025.pdf')]
    return replace(d,documents=d.documents+tuple(Path(p) for _,_,p in cases),
        donnees_validees=d.donnees_validees+tuple(_validee(Path(p),t,c,montant) for t,c,p in cases))


def calcul(nature='BANQUE',dossier=None,**kw):
    return calculer_estimation_fiscale_2025(dossier or dossier_documente(nature),profil_interets=profil_documente(nature),**kw)


@pytest.mark.parametrize('nature',NATURES_INTERETS_DOCUMENTES)
@pytest.mark.parametrize('emploi',[False,True])
def test_lignes_et_impots_sans_double_compte(nature,emploi):
    e=calcul(nature,dossier_documente(nature,emploi=emploi));t3=nature=='T3_INTERETS'
    assert e.interets.ligne_12100==(0 if t3 else 20000)
    assert e.interets.ligne_13000==(20000 if t3 else 0)
    assert e.interets.ligne_130==20000
    assert e.revenu.revenu_net_federal==e.revenu.revenu_imposable_federal==(71515 if emploi else 20000)
    assert e.revenu.revenu_net_quebec==e.revenu.revenu_imposable_quebec==(70095 if emploi else 20000)
    assert e.interets.cotisation_fss==D('18.70')
    assert e.rapprochement.retenues_totales==(13700 if emploi else 0)
    assert e.rapprochement.impot_total_preliminaire==D('14879.56' if emploi else '687.44')
    assert not e.pensions.present and not e.credits_federaux_age_pension.reclamer_montant_pension


@pytest.mark.parametrize('montant,fss',[('0','0'),('49.99','0'),('18130','0'),('18131','.01'),('33130','150'),('63060','150'),('63061','150.01')])
def test_petits_montants_et_fss(montant,fss):
    e=calcul(dossier=dossier_documente(montant=montant))
    assert e.interets.ligne_12100==D(montant) and e.interets.cotisation_fss==D(fss)


@pytest.mark.parametrize('libelle,case',[
    ('Intérêts bancaires 2025','BANQUE'),('Intérêts crédités 2025','BANQUE'),
    ("Intérêts sur remboursement d'impôt 2025",'REMBOURSEMENT_IMPOT'),
    ('Intérêts courus CPG 2025','CPG_ANNUEL'),('Intérêts déjà déclarés','DEJA_DECLARES')])
@pytest.mark.parametrize('v',['123.45','-123.45'])
def test_extraction_libelle_montant_meme_ligne(libelle,case,v):
    donnees=extraire_cases_fiscales('INTERETS',f'{libelle} : {v} $','Etat interets 2025.pdf')
    assert [(x.case,x.valeur) for x in donnees]==[(case,D(v))]


@pytest.mark.parametrize('texte',['Solde : 9000.00','Remboursement impôt : 9000.00','Capital CPG : 9000.00',
    'Intérêts bancaires 2025 :\nSolde : 9000.00','Intérêts bancaires 2025 :\n9000.00','Intérêts bancaires 2024 : 9000.00'])
def test_aucun_solde_ou_principal_extrait(texte):
    assert extraire_cases_fiscales('INTERETS',texte,'scan.pdf')==()


@pytest.mark.parametrize('nom',['Etat interets 2025','Relevé intérêts 2025','Avis intérêts 2025'])
def test_classification_et_ambiguite(nom):
    assert classifier_document_fiscal(nom+'.pdf').type_document=='INTERETS'
    assert classifier_document_fiscal('scan.pdf',nom).type_document=='INTERETS'
    assert classifier_document_fiscal('scan.pdf',nom+' T5').type_document=='À vérifier'


@pytest.mark.parametrize('nom,v',[
    ('identifiant_source',''),('date_debut','2024-01-01'),('date_fin','2026-01-01'),
    ('date_debut','2025-12-32'),('date_debut','20250101'),('date_fin',''),('date_fin',None),
    ('nature','DIVIDENDE'),('devise','USD'),('compte_conjoint',True),('deja_declares',True),
    ('frais_placement',True),('ventilation_confirmee',True),('echeancier_confirme',True),
    ('echeancier_confirme',1),('ventilation_confirmee','true')])
def test_profil_hors_perimetre(nom,v):
    with pytest.raises(ValueError):valider_profil_interets_2025(replace(profil_documente(),**{nom:v}))


@pytest.mark.parametrize('nom,v',[('date_debut','2025-02-01'),('date_fin','2025-11-30'),('echeancier_confirme',False)])
def test_cpg_anniversaire_et_echeancier_requis(nom,v):
    with pytest.raises(ValueError,match='CPG'):valider_profil_interets_2025(replace(profil_documente('CPG_ANNUEL'),**{nom:v}))


def test_t3_ventilation_et_appariement_obligatoires():
    d=dossier_documente('T3_INTERETS')
    with pytest.raises(ValueError,match='ventilation'):
        calculer_estimation_fiscale_2025(d,profil_interets=replace(profil_documente('T3_INTERETS'),ventilation_confirmee=False))
    with pytest.raises(ValueError,match='égaux'):
        calcul('T3_INTERETS',replace(d,donnees_validees=(d.donnees_validees[0],replace(d.donnees_validees[1],valeur_validee=D('100')))))


@pytest.mark.parametrize('type_doc,case',[('T3','31'),('T3','25'),('T3','21'),('T3','35'),('T3','42'),('RL-16','D'),('RL-16','F'),('RL-16','C')])
def test_t3_autres_cases_refusees(type_doc,case):
    d=dossier_documente('T3_INTERETS')
    with pytest.raises(ValueError,match='hors périmètre'):
        calcul('T3_INTERETS',replace(d,donnees_validees=d.donnees_validees+(_validee(Path(type_doc+'.pdf'),type_doc,case,'1'),)))


@pytest.mark.parametrize('v',['-1','NaN','Infinity','0.001','1000000000'])
def test_montants_invalides(v):
    d=dossier_documente()
    with pytest.raises(ValueError):calcul(dossier=replace(d,donnees_validees=(replace(d.donnees_validees[0],valeur_validee=D(v)),)))


def test_doublons_sources_et_cumul_3a_refuses():
    d=dossier_documente();a=dossier_interets()
    faux=[replace(d,donnees_validees=d.donnees_validees*2),
        replace(d,documents=d.documents+a.documents,donnees_validees=d.donnees_validees+a.donnees_validees),
        replace(d,documents=d.documents+(Path('inconnu.pdf'),)),replace(d,documents=()),
        replace(d,donnees_validees=(replace(d.donnees_validees[0],statut='À vérifier'),)),
        replace(d,donnees_validees=d.donnees_validees+(_validee(d.documents[0],'INTERETS','DEJA_DECLARES','1'),)),
        replace(d,annee_fiscale=2024),replace(d,province='Ontario')]
    for dossier in faux:
        with pytest.raises(ValueError):calcul(dossier=dossier)
    with pytest.raises(ValueError,match='Confirmez'):calculer_estimation_fiscale_2025(d)


@pytest.mark.parametrize('nature',NATURES_INTERETS_DOCUMENTES)
def test_stockage_resume_trace_pdf(tmp_path,nature):
    e=calcul(nature);p=sauvegarder_dossier_fiscal(e.dossier,estimation=e,destination=tmp_path/'d.json')
    c=charger_dossier_fiscal(p)
    assert calculer_estimation_fiscale_2025(c.dossier,profil_interets=c.profil_interets)==e
    assert 'BLOC 3B' in formater_estimation_fiscale_2025(e)
    trace=construire_trace_calcul_fiscal_2025(e)
    assert next(x.montant for x in trace.lignes if x.libelle=='Intérêts T3 13000')==(20000 if nature=='T3_INTERETS' else 0)
    pdf=exporter_rapport_fiscal_pdf_2025(e,tmp_path/'r.pdf')
    with fitz.open(pdf) as doc:
        assert 'BLOC 3B' in ''.join(page.get_text() for page in doc)
        for page in doc:
            for x0,y0,x1,y1,*_ in page.get_text('blocks'):
                assert 0<=x0<x1<=page.rect.width and 0<=y0<y1<=page.rect.height
    raw=json.loads(p.read_text(encoding='utf-8'));raw['profil_interets']['date_fin']='2024-12-31';p.write_text(json.dumps(raw),encoding='utf-8')
    with pytest.raises(ValueError,match='2025'):charger_dossier_fiscal(p)


def test_ancien_json_3a_compatible(tmp_path):
    from tests.test_tax_interest_income_2025 import calcul as calcul_3a
    e=calcul_3a();p=sauvegarder_dossier_fiscal(e.dossier,estimation=e,destination=tmp_path/'d.json')
    raw=json.loads(p.read_text(encoding='utf-8'))
    for nom in ('nature','identifiant_source','date_debut','date_fin','echeancier_confirme','ventilation_confirmee'):raw['profil_interets'].pop(nom)
    p.write_text(json.dumps(raw),encoding='utf-8');c=charger_dossier_fiscal(p)
    assert calculer_estimation_fiscale_2025(c.dossier,profil_interets=c.profil_interets)==e


@pytest.mark.parametrize('libelle,case',[('Dividendes 2025','DIVIDENDES'),('Frais de placement 2025','FRAIS'),('Impôt étranger 2025','IMPOT_ETRANGER')])
def test_autre_montant_detecte_et_refuse(libelle,case):
    d=dossier_documente()
    extrait=extraire_cases_fiscales('INTERETS',libelle+' : 12.00',d.documents[0])
    assert [(x.case,x.valeur) for x in extrait]==[(case,D('12'))]
    with pytest.raises(ValueError,match='hors périmètre'):
        calcul(dossier=replace(d,donnees_validees=d.donnees_validees+(_validee(d.documents[0],'INTERETS',case,'12'),)))


@pytest.mark.parametrize('nom',['rqap_confirme','ae_confirme','rrq_rpc_confirme','psv_confirme'])
def test_autres_prestations_refusees(nom):
    with pytest.raises(ValueError,match='hors périmètre'):calcul(**{nom:True})


def test_reer_et_credit_age_revalide():
    from tests.test_tax_union_dues_integration_2025 import _reer_5000
    from src.comptaprivee.tax_federal_age_pension_2025 import CreditsFederauxAgePension2025
    e=calcul(ajustement_reer=_reer_5000())
    assert e.revenu.revenu_net_federal==15000 and e.revenu.revenu_net_quebec==15000
    assert e.interets.cotisation_fss==D('18.70')
    p=CreditsFederauxAgePension2025(reclamer_montant_age=True,age_65_plus_31_decembre_2025=True,
        revenu_net_ligne_23600=D('20000'),resident_canada_toute_annee=True,aucune_regle_deces=True,
        aucun_fractionnement_pension=True,aucun_transfert_conjoint=True,valide_par_comptable=True,source_age='Âge synthétique')
    assert calcul(credits_federaux_age_pension=p).federal.impot_federal_de_base==0
    with pytest.raises(ValueError,match='doit correspondre'):
        calcul(dossier=dossier_documente(montant='30000'),credits_federaux_age_pension=p)


def test_etat_windows_crlf_et_doublons_preserves():
    extrait=extraire_cases_fiscales('INTERETS','Intérêts bancaires 2025 : 12,34\r\nIntérêts bancaires 2025 : 56,78\r\n','scan.pdf')
    assert [x.valeur for x in extrait]==[D('12.34'),D('56.78')]


def test_consolidateur_3b_refuse_profil_3a():
    from src.comptaprivee.tax_documented_interest_2025 import consolider_interets_documentes_2025
    from tests.test_tax_interest_income_2025 import profil_interets
    with pytest.raises(ValueError,match='nature du Bloc 3B'):
        consolider_interets_documentes_2025(dossier_documente(),profil_interets())
