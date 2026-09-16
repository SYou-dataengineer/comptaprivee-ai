"""Bloc 2C : références ARC 11400/11410 et Québec 119, annexe F 2025."""
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
import json
import fitz
import pytest
from src.comptaprivee.tax_cpp_qpp_benefits_2025 import consolider_prestations_rrq_rpc_2025
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025, formater_estimation_fiscale_2025
from src.comptaprivee.tax_document_classifier import classifier_document_fiscal
from src.comptaprivee.tax_field_extractor import extraire_cases_fiscales
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from tests.test_tax_estimation_2025 import _dossier_52000, _validee
from tests.test_tax_rpp_2025 import profil_rpa
from tests.test_tax_union_dues_integration_2025 import _reer_5000, _cotisations_600
from tests.test_tax_age_retirement_integration_2025 import _profil_age_retraite
from tests.test_tax_federal_age_pension_integration_2025 import _profil_age_federal, _profil_pension_federal


def dossier_rrq_rpc(brut='20000', case='14', emploi=True, rl2=True):
    d = _dossier_52000()
    if not emploi:
        d = replace(d, documents=(), donnees_validees=())
    cases = [('T4A(P)', case, brut), ('T4A(P)', '20', brut), ('T4A(P)', '22', '1800')]
    if rl2:
        cases += [('RL-2', 'C', brut), ('RL-2', 'J', '2200')]
    return replace(d, documents=d.documents+(Path('T4A(P).pdf'),)+((Path('RL-2.pdf'),) if rl2 else ()),
        donnees_validees=d.donnees_validees+tuple(_validee(Path(t+'.pdf'),t,c,v) for t,c,v in cases))


def modifier(d,t,c,v):
    return replace(d, donnees_validees=tuple(x for x in d.donnees_validees if (x.type_document,x.case)!=(t,c))+(_validee(Path(t+'.pdf'),t,c,v),))


def calcul(d=None, **kwargs):
    return calculer_estimation_fiscale_2025(d or dossier_rrq_rpc(), rrq_rpc_confirme=True, **kwargs)


@pytest.mark.parametrize('nom,type_doc', [('T4A(P).pdf','T4A(P)'),('T4AP_2025.pdf','T4A(P)'),('releve 2.pdf','RL-2'),('RL-2.pdf','RL-2')])
def test_classification(nom,type_doc):
    assert classifier_document_fiscal(nom).type_document == type_doc
    assert classifier_document_fiscal('scan.pdf',type_doc).type_document == type_doc


def test_classification_ambigue():
    assert classifier_document_fiscal('scan.pdf','T4A(P) RL-2').type_document == 'À vérifier'
    assert classifier_document_fiscal('T4.pdf','T4A(P)').type_document == 'À vérifier'


@pytest.mark.parametrize('t,texte,case,attendu', [
 ('T4A(P)','Box 20 Taxable benefits 20,000.00','20','20000'),
 ('T4A(P)','Case 16 Invalidité 5 000,00','16','5000'),
 ('T4A(P)','Case 18 Décès 2 500,00','18','2500'),
 ('T4A(P)','Box 21 Number of months 12','21','12'),
 ('T4A(P)','Box 23 Retirement months 6','23','6'),
 ('T4A(P)','Case 22 -10.00','22','-10'),
 ('RL-2','Case C Prestations 20000.00','C','20000'),
 ('RL-2','Case J Impôt 2200.00','J','2200'),
 ('RL-2','Case J -10.00','J','-10'),
 ('RL-2','Case J-10.00','J','-10'),
 ('RL-2','Case C -1 000,00','C','-1000'),
 ('RL-2','Code C-7 100.00','C-7','100'),
])
def test_extraction(t,texte,case,attendu):
    valeurs=extraire_cases_fiscales(t,texte,'scan.pdf')
    assert len(valeurs)==1
    assert (valeurs[0].case,valeurs[0].valeur)==(case,Decimal(attendu))


def test_mois_absent_ne_capture_pas_case_suivante():
    assert not any(d.case=='21' for d in extraire_cases_fiscales('T4A(P)','Case 21\nCase 22 1800.00','scan.pdf'))


@pytest.mark.parametrize('v',['NaN','sNaN','Infinity','-1','0.001','1000000000'])
def test_montants_invalides(v):
    with pytest.raises(ValueError,match='Montant'):
        calcul(modifier(dossier_rrq_rpc(),'T4A(P)','20',v))


@pytest.mark.parametrize('confirme',[False,None,1,'true'])
def test_confirmation(confirme):
    with pytest.raises(ValueError):
        calculer_estimation_fiscale_2025(dossier_rrq_rpc(),rrq_rpc_confirme=confirme)


@pytest.mark.parametrize('t,c',[('T4A(P)','18'),('T4A(P)','99'),('RL-2','A'),('RL-2','B'),('RL-2','D'),('RL-2','C-7')])
def test_hors_perimetre(t,c):
    with pytest.raises(ValueError,match='hors périmètre'):
        calcul(modifier(dossier_rrq_rpc(),t,c,'100'))


@pytest.mark.parametrize('c,v',[('21','13'),('23','1.5'),('23','13')])
def test_mois_invalides(c,v):
    with pytest.raises(ValueError,match='mois'):
        calcul(modifier(dossier_rrq_rpc(), 'T4A(P)',c,v))


def test_sources_incoherences_et_manquants():
    d=dossier_rrq_rpc()
    invalides=[replace(d,documents=d.documents[:-1]),
        replace(d,donnees_validees=d.donnees_validees+(d.donnees_validees[-1],)),
        replace(d,annee_fiscale=2024),replace(d,province='Ontario'),
        modifier(d,'RL-2','C','20000.01'),modifier(d,'T4A(P)','14','20001'),
        replace(d,donnees_validees=d.donnees_validees+(_validee(Path('second.pdf'),'T4A(P)','20','100'),)),
        replace(d,donnees_validees=d.donnees_validees[:-1]+(replace(d.donnees_validees[-1],statut='À valider'),))]
    for t,c in [('T4A(P)','20'),('RL-2','C')]:
        invalides.append(replace(d,donnees_validees=tuple(x for x in d.donnees_validees if (x.type_document,x.case)!=(t,c))))
    for invalide in invalides:
        with pytest.raises(ValueError):
            calcul(invalide)
    with pytest.raises(ValueError,match='T4A'):
        calcul(_dossier_52000())


@pytest.mark.parametrize('case',['14','15','16','17','19'])
@pytest.mark.parametrize('rl2',[True,False])
def test_prestations_sans_emploi(case,rl2):
    e=calcul(dossier_rrq_rpc(case=case,emploi=False,rl2=rl2))
    assert e.base.nombre_t4==e.base.nombre_rl1==0
    assert e.revenu.revenu_total_federal==e.revenu.revenu_total_quebec==20000
    assert e.revenu.revenu_net_federal==e.revenu.revenu_net_quebec==20000
    assert e.revenu.deduction_travailleur_quebec==0
    assert e.prestations_rrq_rpc.invalidite == (20000 if case=='16' else 0)
    assert e.prestations_rrq_rpc.enfant == (20000 if case=='17' else 0)
    assert e.rapprochement.retenue_federale==1800
    assert e.rapprochement.retenue_quebec==(2200 if rl2 else 0)
    assert e.prestations_rrq_rpc.cotisation_fss==Decimal('18.70')
    assert not e.montants_age_retraite.reclamer_revenus_retraite
    assert not e.credits_federaux_age_pension.reclamer_montant_pension


@pytest.mark.parametrize('case',['16','17'])
def test_cotisations_particulieres_refusees(case):
    with pytest.raises(ValueError,match='avec salaire'):
        calcul(dossier_rrq_rpc(case=case))


def test_beneficiaires_mixtes_refuses():
    d=modifier(dossier_rrq_rpc(emploi=False,case='17'),'T4A(P)','14','1')
    d=modifier(d,'T4A(P)','20','20001'); d=modifier(d,'RL-2','C','20001')
    with pytest.raises(ValueError,match='mixtes'):
        calcul(d)


@pytest.mark.parametrize('t',['T4E','RL-6','T4A(OAS)','T4A','T4RIF'])
def test_profils_mixtes_refuses(t):
    d=dossier_rrq_rpc()
    d=replace(d,donnees_validees=d.donnees_validees+(_validee(Path('autre.pdf'),t,'14','100'),))
    with pytest.raises(ValueError,match='hors périmètre'):
        calcul(d)


def test_emploi_total_retenues_fss_deductions():
    e=calcul()
    base=calculer_estimation_fiscale_2025(_dossier_52000())
    assert e.base==base.base
    assert e.revenu.revenu_total_federal==e.revenu.revenu_total_quebec==72000
    assert e.revenu.revenu_net_federal==Decimal('71515')
    assert e.revenu.revenu_net_quebec==Decimal('70095')
    r=e.rapprochement
    assert r.retenues_totales==17700
    assert r.impot_total_preliminaire==r.impot_federal_apres_abattement+r.impot_quebec_preliminaire+Decimal('18.70')
    autre=calcul(cotisations_rpa=profil_rpa(),ajustement_reer=_reer_5000(),cotisations_syndicales=_cotisations_600())
    assert autre.revenu.revenu_net_federal==62915
    assert autre.revenu.revenu_net_quebec==62095
    assert autre.prestations_rrq_rpc.cotisation_fss==Decimal('18.70')


@pytest.mark.parametrize('brut,fss',[('0','0'),('18130','0'),('18131','0.01'),('33130','150'),('63060','150'),('63061','150.01'),('148060','1000')])
def test_fss(brut,fss):
    assert consolider_prestations_rrq_rpc_2025(dossier_rrq_rpc(brut=brut,emploi=False),True).cotisation_fss==Decimal(fss)


def test_credits_age_revenus_actualises_et_pension_exclue():
    d=dossier_rrq_rpc(brut='40000',emploi=False)
    e=calcul(d,credits_federaux_age_pension=_profil_age_federal(revenu_net_ligne_23600=Decimal('40000')),
        montants_age_retraite=_profil_age_retraite(reclamer_revenus_retraite=False,revenu_ligne_122=Decimal('0'),revenu_familial_net=Decimal('40000')))
    assert e.revenu.revenu_net_federal==40000
    with pytest.raises(ValueError,match='revenu net'):
        calcul(d,credits_federaux_age_pension=_profil_age_federal())
    with pytest.raises(ValueError,match='361'):
        calcul(d,montants_age_retraite=_profil_age_retraite(revenu_familial_net=Decimal('40000')))
    with pytest.raises(ValueError,match='31400'):
        calcul(d,credits_federaux_age_pension=replace(_profil_pension_federal(),revenu_net_ligne_23600=Decimal('40000')))


def test_stockage_recalcul_et_ancien_json(tmp_path):
    d=dossier_rrq_rpc(); e=calcul(d)
    p=sauvegarder_dossier_fiscal(d,estimation=e,destination=tmp_path/'d.json')
    charge=charger_dossier_fiscal(p)
    assert charge.rrq_rpc_confirme and not charge.ae_confirme and not charge.rqap_confirme
    assert calcul(charge.dossier)==e
    with pytest.raises(ValueError,match='diffère'):
        sauvegarder_dossier_fiscal(d,estimation=e,rrq_rpc_confirme=False,destination=p)
    contenu=json.loads(p.read_text(encoding='utf-8')); del contenu['rrq_rpc_confirme']
    p.write_text(json.dumps(contenu),encoding='utf-8')
    charge=charger_dossier_fiscal(p)
    assert not charge.rrq_rpc_confirme
    with pytest.raises(ValueError,match='Confirmez'):
        calculer_estimation_fiscale_2025(charge.dossier)


@pytest.mark.parametrize('v',[None,1,'true',[],{}])
def test_confirmation_json_invalide(tmp_path,v):
    p=sauvegarder_dossier_fiscal(dossier_rrq_rpc(),rrq_rpc_confirme=True,destination=tmp_path/'d.json')
    contenu=json.loads(p.read_text(encoding='utf-8')); contenu['rrq_rpc_confirme']=v
    p.write_text(json.dumps(contenu),encoding='utf-8')
    with pytest.raises(ValueError,match='booléen'):
        charger_dossier_fiscal(p)


@pytest.mark.parametrize('emploi,rl2',[(True,True),(False,False)])
def test_resume_trace_pdf(tmp_path,emploi,rl2):
    e=calcul(dossier_rrq_rpc(emploi=emploi,rl2=rl2))
    texte=formater_estimation_fiscale_2025(e)
    for mot in ('11400','11410','119','43700','451','446','rétroactivité'):
        assert mot in texte
    trace=construire_trace_calcul_fiscal_2025(e)
    assert [l.ordre for l in trace.lignes]==list(range(1,len(trace.lignes)+1))
    assert next(l for l in trace.lignes if l.libelle=='RRQ/RPC 11400').montant==20000
    assert next(l for l in trace.lignes if l.libelle=='FSS RRQ/RPC 446').montant==Decimal('18.70')
    p=exporter_rapport_fiscal_pdf_2025(e,tmp_path/'rrq.pdf')
    with fitz.open(p) as pdf:
        texte='\n'.join(page.get_text() for page in pdf)
        for mot in ('11410','T4A(P)','FSS Québec 446','Sans rétroactivité'):
            assert mot in texte
        for page in pdf:
            for x0,y0,x1,y1,*_ in page.get_text('blocks'):
                assert 0<=x0<x1<=page.rect.width
                assert 0<=y0<y1<=page.rect.height

@pytest.mark.parametrize('emploi',[True,False])
def test_total_sans_detail_sous_cases(emploi):
    d=dossier_rrq_rpc(emploi=emploi)
    d=replace(d,donnees_validees=tuple(x for x in d.donnees_validees if (x.type_document,x.case)!=('T4A(P)','14')))
    assert calcul(d).prestations_rrq_rpc.prestations==20000


def test_limites_existantes_credits_et_hauts_revenus_preservees():
    with pytest.raises(ValueError,match='34990'):
        calcul(credits_federaux_age_pension=_profil_age_federal(revenu_net_ligne_23600=Decimal('71515')))
    with pytest.raises(ValueError,match='hors profil'):
        calcul(dossier_rrq_rpc(brut='148060',emploi=False))


@pytest.mark.parametrize('autre',['ae_confirme','rqap_confirme'])
def test_confirmations_concurrentes_refusees(tmp_path,autre):
    d=dossier_rrq_rpc()
    with pytest.raises(ValueError,match='hors périmètre'):
        calcul(d,**{autre:True})
    with pytest.raises(ValueError,match='hors périmètre'):
        sauvegarder_dossier_fiscal(d,rrq_rpc_confirme=True,destination=tmp_path/'a.json',**{autre:True})


def test_retraite_survivant_sans_double_compte():
    d=modifier(dossier_rrq_rpc(),'T4A(P)','14','15000')
    d=modifier(d,'T4A(P)','15','4500'); d=modifier(d,'T4A(P)','19','500')
    p=calcul(d).prestations_rrq_rpc
    assert p.prestations==20000 and p.survivant==4500 and p.apres_retraite==500


def test_sans_emploi_ne_cree_pas_de_credits_salariaux():
    e=calcul(dossier_rrq_rpc(emploi=False,case='16'))
    assert e.federal.montant_canadien_emploi==0
    assert e.federal.cotisation_base_rrq==e.federal.assurance_emploi_admissible==e.federal.rqap_admissible==0
    assert e.revenu.deduction_rrq_amelioree_federale==e.revenu.deduction_rrq_quebec==0
