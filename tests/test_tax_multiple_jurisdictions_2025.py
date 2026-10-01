"""7G : préparation seulement, montants fictifs; aucun impôt interprovincial."""
from dataclasses import replace, FrozenInstanceError
from decimal import Decimal as D
import json
import fitz
import pytest
from tests.test_tax_self_employment_contributions_2025 import dossier_7c
from src.comptaprivee.tax_multiple_jurisdictions_2025 import (
    Administrations2025, CONFIRMATIONS_7G, MESSAGE_7G, PROVINCES_7G,
    preparer_administrations_2025, administrations_depuis_json, administrations_vers_json,
    lignes_preparation_administrations_2025,
)
from src.comptaprivee.tax_self_employment_2025 import calculer_entreprises_2025, preparer_revenus_autonomes_2025
from src.comptaprivee.tax_self_employment_contributions_2025 import calculer_cotisations_autonomes_2025
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calcul, formater_estimation_fiscale_2025
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_administrations_2025, construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_preparation_administrations_pdf_2025, exporter_rapport_fiscal_pdf_2025


def profil(**kw):
    p=Administrations2025(reference_entreprise=dossier_7c().entreprises[0].reference,
        etablissement_hors_quebec=True,province='ON',revenu_quebec=D('7000'),revenu_hors_quebec=D('3000'),
        methode='Répartition confirmée par le comptable sur pièces fictives',source='Journal et analyse fictifs 2025',
        **{n:True for n in CONFIRMATIONS_7G})
    return replace(p,**kw)


def dossier_7g(p=None):
    d=dossier_7c();p=p or profil()
    return replace(d,entreprises=(replace(d.entreprises[0],administrations=p,services_quebec=not p.etablissement_hors_quebec),))


@pytest.mark.parametrize('province',list(PROVINCES_7G))
def test_juridiction_70_30_formulaires_sans_impot(province):
    d=dossier_7g(profil(province=province))
    r=preparer_administrations_2025(d)
    assert r.revenu_total==D('10000')
    assert r.pourcentage_quebec==70 and r.pourcentage_hors_quebec==30
    assert r.t2203_requis and r.tp22_requis and r.estimation_suspendue
    assert set(vars(r))=={'client','faits','revenu_total','pourcentage_quebec','pourcentage_hors_quebec','t2203_requis','tp22_requis','estimation_suspendue'}
    assert calculer_entreprises_2025(d.entreprises)[0].revenu_net==10000
    with pytest.raises(FrozenInstanceError):r.faits.revenu_quebec=D('0')


def test_quebec_seulement_historique_inchange():
    base=dossier_7c();avant=calcul(base)
    p=profil(etablissement_hors_quebec=False,province='',revenu_quebec=D('10000'),revenu_hors_quebec=D('0'))
    d=dossier_7g(p);r=preparer_administrations_2025(d);apres=calcul(d)
    assert not r.t2203_requis and not r.tp22_requis and not r.estimation_suspendue
    assert apres.revenu==avant.revenu and apres.federal==avant.federal and apres.quebec==avant.quebec
    assert apres.rapprochement==avant.rapprochement
    assert apres.cotisations_autonomes==avant.cotisations_autonomes


def test_bloque_avant_calcul_federal_abattement_fss(monkeypatch):
    from src.comptaprivee import tax_estimation_2025 as module
    def interdit(*a,**kw):pytest.fail('Un calcul monétaire annuel ne doit pas être appelé.')
    monkeypatch.setattr(module,'calculer_impot_federal_preliminaire_2025',interdit)
    monkeypatch.setattr(module,'calculer_cotisations_autonomes_2025',interdit)
    with pytest.raises(ValueError) as exc:calcul(dossier_7g())
    assert str(exc.value)==MESSAGE_7G
    d=dossier_7g()
    for f in (lambda:calculer_cotisations_autonomes_2025(d,d.profil_cotisations_autonomes),
              lambda:preparer_revenus_autonomes_2025(d,d.entreprises)):
        with pytest.raises(ValueError,match='T2203 / TP-22'):f()


@pytest.mark.parametrize('kw',[
    {'province':'QC'},{'province':'US'},{'province':'ON,AB'},{'province':''},
    {'revenu_quebec':D('6999.99')},{'revenu_hors_quebec':D('3000.01')},
    {'reference_entreprise':'Autre'},{'source':''},{'methode':' '},
    {'etablissement_hors_quebec':False},{'etablissement_hors_quebec':1},
])
def test_faits_incoherents_refuses(kw):
    with pytest.raises(ValueError):preparer_administrations_2025(dossier_7g(profil(**kw)))


@pytest.mark.parametrize('champ',list(CONFIRMATIONS_7G))
@pytest.mark.parametrize('valeur',[False,1,'oui'])
def test_confirmations_strictes(champ,valeur):
    with pytest.raises(ValueError):preparer_administrations_2025(dossier_7g(profil(**{champ:valeur})))


@pytest.mark.parametrize('champ',['revenu_quebec','revenu_hors_quebec'])
@pytest.mark.parametrize('valeur',[D('NaN'),D('sNaN'),D('Infinity'),D('-1'),D('.001'),D('1E40'),7000.0,'7000',True])
def test_decimal_strict(champ,valeur):
    with pytest.raises(ValueError):preparer_administrations_2025(dossier_7g(profil(**{champ:valeur})))


def test_pas_de_pourcentage_invente_sur_revenu_nul():
    d=dossier_7g(profil(revenu_quebec=D('0'),revenu_hors_quebec=D('0')))
    d=replace(d,entreprises=(replace(d.entreprises[0],revenu_brut=D('0')),))
    r=preparer_administrations_2025(d)
    assert r.pourcentage_quebec is None and r.pourcentage_hors_quebec is None
    assert r.estimation_suspendue


def test_profil_absent_services_false_reste_bloque():
    d=dossier_7c();d=replace(d,entreprises=(replace(d.entreprises[0],services_quebec=False),))
    with pytest.raises(ValueError,match='confirmation obligatoire'):calcul(d)
    with pytest.raises(ValueError,match='profil de répartition absent'):preparer_administrations_2025(dossier_7c())


def test_contradiction_7b_et_plusieurs_entreprises_refusees():
    d=dossier_7g()
    with pytest.raises(ValueError,match='incompatible'):
        preparer_administrations_2025(replace(d,entreprises=(replace(d.entreprises[0],services_quebec=True),)))
    with pytest.raises(ValueError,match='seule entreprise'):
        preparer_administrations_2025(replace(d,entreprises=d.entreprises+d.entreprises))
    with pytest.raises(ValueError,match='Québec 2025'):
        preparer_administrations_2025(replace(d,province='Ontario'))


@pytest.mark.parametrize('champ',['abattement_44000','impot','pourcentage_tp22','fss_446','etablissements'])
def test_aucune_saisie_monetaire_fiscale_ni_structure_complexe(champ):
    v=administrations_vers_json(profil());v[champ]='100'
    with pytest.raises(ValueError,match='champs JSON inconnus'):administrations_depuis_json(v)


def test_json_dossier_ancien_nouveau_et_recalcul_bloque(tmp_path):
    assert administrations_depuis_json(None) is None
    d=dossier_7g()
    path=sauvegarder_dossier_fiscal(d,destination=tmp_path/'fictif.json')
    recharge=charger_dossier_fiscal(path)
    assert recharge.dossier==d and recharge.estimation is None
    assert preparer_administrations_2025(recharge.dossier)==preparer_administrations_2025(d)
    with pytest.raises(ValueError,match='T2203 / TP-22'):calcul(recharge.dossier)
    ancien=sauvegarder_dossier_fiscal(dossier_7c(),destination=tmp_path/'ancien.json')
    brut=json.loads(ancien.read_text(encoding='utf-8'));brut['entreprises'][0].pop('administrations')
    ancien.write_text(json.dumps(brut),encoding='utf-8')
    assert calcul(charger_dossier_fiscal(ancien).dossier)==calcul(dossier_7c())


def test_estimation_et_pdf_perimes_ne_peuvent_pas_etre_associes(tmp_path):
    d=dossier_7g();ancien=calcul(dossier_7c())
    for kw in ({'estimation':ancien},{'rapport_pdf':tmp_path/'ancien.pdf'}):
        with pytest.raises(ValueError,match='T2203 / TP-22'):
            sauvegarder_dossier_fiscal(d,destination=tmp_path/'interdit.json',**kw)
    falsifie=replace(ancien,dossier=d)
    with pytest.raises(ValueError,match='T2203 / TP-22'):formater_estimation_fiscale_2025(falsifie)
    with pytest.raises(ValueError,match='T2203 / TP-22'):exporter_rapport_fiscal_pdf_2025(falsifie,tmp_path/'interdit.pdf')
    with pytest.raises(ValueError,match='T2203 / TP-22'):construire_trace_calcul_fiscal_2025(falsifie)
    path=sauvegarder_dossier_fiscal(d,destination=tmp_path/'fictif.json')
    v=json.loads(path.read_text(encoding='utf-8'));v['derniere_estimation']={'resultat':'faux'}
    path.write_text(json.dumps(v),encoding='utf-8')
    with pytest.raises(ValueError,match='T2203 / TP-22'):charger_dossier_fiscal(path)


def test_trace_pdf_independants_sans_montant_fiscal(tmp_path):
    d=dossier_7g()
    lignes=construire_trace_administrations_2025(d)
    assert lignes==lignes_preparation_administrations_2025(preparer_administrations_2025(d))
    texte='\n'.join(lignes)
    for attendu in ('Ontario','7000.00','3000.00','T2203 requis : oui','TP-22 requis : oui',
                    'CALCUL ANNUEL SUSPENDU','aucun abattement calculé','FSS 446 : montant non calculé'):
        assert attendu in texte
    path=exporter_preparation_administrations_pdf_2025(d,tmp_path/'preparation.pdf')
    with fitz.open(path) as pdf:
        texte='\n'.join(page.get_text() for page in pdf)
    for attendu in ('Ontario','7000.00','3000.00','CALCUL ANNUEL SUSPENDU','TP-22 requis : oui'):
        assert attendu in texte


@pytest.mark.parametrize('v',[[],True,{'province':['ON']},{'revenu_quebec':7000,'revenu_hors_quebec':'3000'}])
def test_json_invalide_refuse(v):
    with pytest.raises(ValueError):administrations_depuis_json(v)


def test_ventilation_stale_apres_modification_entreprise_refusee(tmp_path):
    d=dossier_7g()
    d=replace(d,entreprises=(replace(d.entreprises[0],revenu_brut=D('10001')),))
    with pytest.raises(ValueError,match='ventilation différente'):preparer_administrations_2025(d)
    with pytest.raises(ValueError,match='ventilation différente'):
        sauvegarder_dossier_fiscal(d,destination=tmp_path/'interdit.json')


def test_emploi_et_location_exclus_de_la_preparation():
    from tests.test_tax_case_storage import _dossier
    emploi=_dossier();d=dossier_7g()
    with pytest.raises(ValueError,match='autonome seule'):
        preparer_administrations_2025(replace(d,documents=emploi.documents,donnees_validees=emploi.donnees_validees))


@pytest.mark.parametrize('entreprises',[[],(object(),)])
def test_types_invalides_refuses_avant_estimation(entreprises):
    with pytest.raises(ValueError):calcul(replace(dossier_7c(),entreprises=entreprises))
