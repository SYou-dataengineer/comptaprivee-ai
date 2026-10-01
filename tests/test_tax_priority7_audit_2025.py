"""7K : contrôles transversaux sur faits fictifs, sans nouveau profil fiscal."""
from dataclasses import replace
from decimal import Decimal as D
import json
import pytest
from tests.test_tax_self_employment_contributions_2025 import dossier_7c
from tests.test_tax_rental_income_2025 import dossier_location
from tests.test_tax_rental_cca_2025 import dossier_dpa
from tests.test_tax_loss_integration_2025 import pertes
from tests.test_tax_multiple_employers_2025 import dossier_multiple, profil_multiple
from tests.test_tax_foreign_property_2025 import profil as inventaire
from tests.test_tax_foreign_investment_2025 import dossier as dossier_etranger, profil as profil_etranger, profil_credit
from src.comptaprivee.tax_self_employment_2025 import entreprises_vers_json, entreprises_depuis_json
from src.comptaprivee.tax_rental_income_2025 import locations_vers_json, locations_depuis_json, MONTANTS_7D
from src.comptaprivee.tax_rental_cca_2025 import dpa_location_vers_json, dpa_location_depuis_json, MONTANTS_7E
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calcul
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal


@pytest.mark.parametrize('champ',['revenu_brut','frais_bureau','frais_comptables'])
def test_7b_json_montant_manquant_ne_devient_pas_zero(champ):
    brut=entreprises_vers_json(dossier_7c().entreprises)
    del brut[0][champ]
    with pytest.raises(ValueError,match='obligatoire manquant.*'+champ):entreprises_depuis_json(brut)


@pytest.mark.parametrize('champ',MONTANTS_7D)
def test_7d_json_montant_manquant_ne_devient_pas_zero(champ):
    brut=locations_vers_json(dossier_location().biens_locatifs)
    del brut[0][champ]
    with pytest.raises(ValueError,match='obligatoire manquant.*'+champ):locations_depuis_json(brut)


@pytest.mark.parametrize('champ',MONTANTS_7E)
def test_7e_json_montant_manquant_ne_devient_pas_zero(champ):
    brut=dpa_location_vers_json(dossier_dpa().biens_locatifs[0].amortissement)
    del brut[champ]
    with pytest.raises(ValueError,match='obligatoire manquant.*'+champ):dpa_location_depuis_json(brut)


@pytest.mark.parametrize('bloc',['7B','7D','7E'])
def test_chargement_fiche_confirmee_corrompue_refuse(bloc,tmp_path):
    d={'7B':dossier_7c,'7D':dossier_location,'7E':dossier_dpa}[bloc]()
    f=sauvegarder_dossier_fiscal(d,destination=tmp_path/'fictif.json',estimation=calcul(d))
    contenu=json.loads(f.read_text(encoding='utf-8'))
    if bloc=='7B':del contenu['entreprises'][0]['revenu_brut']
    elif bloc=='7D':del contenu['biens_locatifs'][0]['loyers']
    else:del contenu['biens_locatifs'][0]['amortissement']['dpa_federale']
    f.write_text(json.dumps(contenu),encoding='utf-8')
    with pytest.raises(ValueError,match='obligatoire manquant'):charger_dossier_fiscal(f)


def test_anciens_profils_absents_et_extensions_facultatives_restent_compatibles():
    assert entreprises_depuis_json(None)==() and locations_depuis_json(None)==()
    assert dpa_location_depuis_json(None) is None
    brut=entreprises_vers_json(dossier_7c().entreprises)
    del brut[0]['administrations']
    assert entreprises_depuis_json(brut)==dossier_7c().entreprises
    brut=locations_vers_json(dossier_location().biens_locatifs)
    del brut[0]['amortissement']
    assert locations_depuis_json(brut)==dossier_location().biens_locatifs


@pytest.mark.parametrize('dpa',[False,True])
def test_7a_7d_7e_7f_ordre_sans_double_deduction(dpa):
    loc=dossier_dpa(dpa_federale=D(1000),dpa_quebec=D(500)) if dpa else dossier_location()
    d=replace(dossier_multiple(),biens_locatifs=loc.biens_locatifs)
    base=calcul(d,cotisations_excedentaires=profil_multiple())
    e=calcul(replace(d,registre_pertes=pertes()),cotisations_excedentaires=profil_multiple())
    salaire=calcul(dossier_multiple(),cotisations_excedentaires=profil_multiple())
    assert e.revenu.deduction_rrq_amelioree_federale==salaire.revenu.deduction_rrq_amelioree_federale
    assert e.revenu.revenu_net_federal==salaire.revenu.revenu_net_federal+e.location.ligne_12600
    assert e.revenu.revenu_net_quebec==salaire.revenu.revenu_net_quebec+e.location.ligne_136
    assert e.cotisations_autonomes is None
    for j in ('federal','quebec'):
        assert getattr(e.revenu,'revenu_net_'+j)==getattr(base.revenu,'revenu_net_'+j)
        assert getattr(e.revenu,'revenu_imposable_'+j)==getattr(base.revenu,'revenu_imposable_'+j)-400


def test_7j_ne_recalcule_pas_credit_etranger_3g():
    d=dossier_etranger('10000','1500',emploi=True)
    kw=dict(profil_placement_etranger=profil_etranger(),profil_credit_impot_etranger=profil_credit('100','50'))
    avant=calcul(d,**kw);apres=calcul(replace(d,biens_etrangers=inventaire()),**kw)
    assert avant.revenu==apres.revenu and avant.credit_impot_etranger==apres.credit_impot_etranger
    assert avant.federal==apres.federal and avant.quebec==apres.quebec and avant.rapprochement==apres.rapprochement


@pytest.mark.parametrize('fabrique',[dossier_7c,dossier_dpa])
def test_plusieurs_profils_aller_retour_et_incoherence_estimation(fabrique,tmp_path):
    d=replace(fabrique(),registre_pertes=pertes(),biens_etrangers=inventaire())
    e=calcul(d);f=sauvegarder_dossier_fiscal(d,destination=tmp_path/'complet.json',estimation=e)
    recharge=charger_dossier_fiscal(f)
    assert recharge.dossier==d and calcul(recharge.dossier)==e
    with pytest.raises(ValueError):
        sauvegarder_dossier_fiscal(replace(d,registre_pertes=type(d.registre_pertes)()),estimation=e,destination=tmp_path/'divergent.json')
