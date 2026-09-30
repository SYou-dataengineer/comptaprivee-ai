"""7B : données fictives; préparation seulement avant les cotisations 7C."""
from dataclasses import replace, FrozenInstanceError
from decimal import Decimal
import json
import fitz
import pytest

from src.comptaprivee.tax_self_employment_2025 import (
    Entreprise2025, CONFIRMATIONS_7B, calculer_entreprises_2025,
    entreprises_depuis_json, entreprises_vers_json,
    preparer_revenus_autonomes_2025, lignes_preparation_autonome_2025,
)
from src.comptaprivee.tax_validated_case import DossierFiscalValide
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
from src.comptaprivee.tax_report_pdf_2025 import exporter_preparation_autonome_pdf_2025
from test_tax_case_storage import _dossier


def entreprise(**kw):
    return replace(Entreprise2025(reference="Services fictifs", source="Journal fictif 2025",
        revenu_brut=Decimal("10000"), **{n: True for n in CONFIRMATIONS_7B}), **kw)


def dossier():
    return DossierFiscalValide(client="Démonstration 7B", annee_fiscale=2025,
        province="Québec", documents=(), donnees_validees=(), entreprises=(entreprise(),))


@pytest.mark.parametrize("brut,bureau,comptable,net", [
    ("10000", "0", "0", "10000"), ("10000.01", "100.01", "400", "9500.00"),
    ("0", "0", "0", "0"), ("100", "25", "75", "0")])
def test_net_exact(brut,bureau,comptable,net):
    e=entreprise(revenu_brut=Decimal(brut),frais_bureau=Decimal(bureau),frais_comptables=Decimal(comptable))
    assert calculer_entreprises_2025((e,))[0].revenu_net == Decimal(net)
    with pytest.raises(FrozenInstanceError): e.reference="autre"


@pytest.mark.parametrize("champ", ["revenu_brut", "frais_bureau", "frais_comptables"])
@pytest.mark.parametrize("valeur", [Decimal("NaN"),Decimal("sNaN"),Decimal("Infinity"),Decimal("-1"),Decimal("0.001"),Decimal("1E40"),1.2,"10"])
def test_montants_invalides(champ,valeur):
    with pytest.raises(ValueError): calculer_entreprises_2025((entreprise(**{champ:valeur}),))


@pytest.mark.parametrize("champ", list(CONFIRMATIONS_7B))
def test_confirmations_obligatoires(champ):
    for valeur in (False,1,"oui"):
        with pytest.raises(ValueError): calculer_entreprises_2025((entreprise(**{champ:valeur}),))


@pytest.mark.parametrize("kw", [{"fin":"2025-06-30"},{"debut":"2024-01-01"},{"debut":"invalide"},
    {"nature":"agriculture"},{"source":" "},{"reference":""},{"frais_bureau":Decimal("10001")}])
def test_exclusions(kw):
    with pytest.raises(ValueError): calculer_entreprises_2025((entreprise(**kw),))


def test_doublons_et_liste():
    with pytest.raises(ValueError,match="doublon"):
        calculer_entreprises_2025((entreprise(),entreprise(reference="  SERVICES   FICTIFS ")))
    r=calculer_entreprises_2025((entreprise(),entreprise(reference="Profession fictive",nature="profession")))
    assert sum(x.revenu_net for x in r)==Decimal("20000")


def test_json_faits_et_ancien():
    assert entreprises_depuis_json(None)==()
    assert entreprises_depuis_json(entreprises_vers_json((entreprise(),)))==(entreprise(),)
    for valeur in ({},[{}],[{"inconnu":True}],[{"revenu_brut":2.1}]):
        with pytest.raises(ValueError): entreprises_depuis_json(valeur)


@pytest.mark.parametrize("salaire",[False,True])
def test_preparation_et_blocage_annuel(salaire):
    d=replace(_dossier(),entreprises=(entreprise(),)) if salaire else dossier()
    p=preparer_revenus_autonomes_2025(d,d.entreprises)
    assert p.revenu_total_federal == Decimal("62000" if salaire else "10000")
    assert p.revenu_total_quebec == p.revenu_total_federal
    assert p.revenu_275_avant_7c == Decimal("60580" if salaire else "9400")
    with pytest.raises(ValueError,match="7C"): calculer_estimation_fiscale_2025(d)
    trace="\n".join(lignes_preparation_autonome_2025(p))
    assert "13500" in trace and "ligne 164" in trace and "AVANT" in trace
    assert "ACT : non calculés" in trace


@pytest.mark.parametrize("salaire",[False,True])
def test_sauvegarde_recharge_et_resume_interdit(tmp_path,salaire):
    d=replace(_dossier(),entreprises=(entreprise(),)) if salaire else dossier()
    chemin=sauvegarder_dossier_fiscal(d,destination=tmp_path/'d.json')
    assert charger_dossier_fiscal(chemin).dossier == d
    with pytest.raises(ValueError,match="7C"):
        sauvegarder_dossier_fiscal(d,destination=chemin,rapport_pdf="ancien.pdf")
    brut=json.loads(chemin.read_text(encoding='utf-8'))
    brut['derniere_estimation']={}
    chemin.write_text(json.dumps(brut),encoding='utf-8')
    with pytest.raises(ValueError,match="7C"): charger_dossier_fiscal(chemin)


def test_ancien_json_salaire(tmp_path):
    chemin=sauvegarder_dossier_fiscal(_dossier(),destination=tmp_path/'d.json')
    brut=json.loads(chemin.read_text(encoding='utf-8'));brut.pop('entreprises')
    chemin.write_text(json.dumps(brut),encoding='utf-8')
    ancien=charger_dossier_fiscal(chemin).dossier
    assert ancien.entreprises==()
    assert calculer_estimation_fiscale_2025(ancien)==calculer_estimation_fiscale_2025(_dossier())


def test_pdf(tmp_path):
    d=dossier();p=preparer_revenus_autonomes_2025(d,d.entreprises)
    chemin=exporter_preparation_autonome_pdf_2025(p,tmp_path/'preparation.pdf')
    with fitz.open(chemin) as pdf:
        texte=''.join(page.get_text() for page in pdf)
        assert "10000.00" in texte and "9400.00" in texte
        assert "estimation finale bloquée" in texte
        assert "AVANT cotisations" in texte
        for page in pdf:
            for bloc in page.get_text('blocks'):
                assert bloc[0]>=40 and bloc[2]<page.rect.width-40


def test_mixte_multi_et_exclusions():
    from test_tax_multiple_employers_2025 import dossier_multiple
    d=replace(dossier_multiple(),entreprises=(entreprise(),))
    p=preparer_revenus_autonomes_2025(d,d.entreprises)
    assert p.revenu_total_federal==Decimal('62000')
    with pytest.raises(ValueError,match='7C'): calculer_estimation_fiscale_2025(d)
    with pytest.raises(ValueError,match='correspondre'):
        preparer_revenus_autonomes_2025(d,())
    d=replace(d,donnees_validees=(replace(d.donnees_validees[0],type_document='T5'),))
    with pytest.raises(ValueError,match='autres que salaire'):
        preparer_revenus_autonomes_2025(d,d.entreprises)


def test_credits_non_etendus_silencieusement():
    from src.comptaprivee.tax_quebec_work_premium_2025 import PrimeTravailQuebec2025
    with pytest.raises(ValueError,match='7C'):
        calculer_estimation_fiscale_2025(dossier(),prime_travail_quebec=PrimeTravailQuebec2025())
