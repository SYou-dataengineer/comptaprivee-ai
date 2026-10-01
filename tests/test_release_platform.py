"""Contrat release : millésime, métadonnées et chemins utilisateur fictifs."""
import csv
import json
from pathlib import Path
import tomllib
from dataclasses import replace
from decimal import Decimal

import pytest
from tests.test_tax_case_storage import _dossier
from src.comptaprivee import tax_case_storage as storage
from src.comptaprivee.backup_manager import creer_sauvegarde, restaurer_sauvegarde
from src.comptaprivee.csv_exporter import exporter_facture_csv
from src.comptaprivee.facture_parser import DonneesFacture
from src.comptaprivee.tax_case import annee_fiscale_par_defaut, annees_fiscales_disponibles
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025


def test_metadonnees_et_collecte():
    racine=Path(__file__).resolve().parents[1]
    config=tomllib.loads((racine/'pyproject.toml').read_text(encoding='utf-8'))
    version = config['project']['version']
    assert version in ('1.0.0rc1', '1.0.0')
    for document in ('README.md', 'CHANGELOG.md', 'docs/release_v1_checklist.md'):
        assert version in (racine / document).read_text(encoding='utf-8')
    assert config['project']['requires-python']=='>=3.12,<3.13'
    assert config['tool']['pytest']['ini_options']['testpaths']==['tests']


@pytest.mark.parametrize('horloge',[2025,2026,2027,2040])
def test_horloge_ne_selectionne_pas_un_moteur(horloge):
    assert annee_fiscale_par_defaut(horloge)==2025
    assert annees_fiscales_disponibles(horloge)==(2025,)


def test_moteur_2026_refuse():
    with pytest.raises(ValueError):
        calculer_estimation_fiscale_2025(replace(_dossier(),annee_fiscale=2026))


def test_chemin_utilisateur_unicode_espaces_json_csv_backup(tmp_path,monkeypatch):
    racine=tmp_path/'Utilisateur Élodie fictive'/'Mes dossiers privés'
    racine.mkdir(parents=True)
    monkeypatch.chdir(racine)
    fiscaux=racine/'data/dossiers_fiscaux'
    monkeypatch.setattr(storage,'DOSSIERS_FISCAUX_DIR',fiscaux)
    monkeypatch.setattr(storage,'PROJECT_ROOT',racine)
    d=replace(_dossier(),client='Élodie fictive')
    p=storage.sauvegarder_dossier_fiscal(d)
    assert storage.charger_dossier_fiscal(p).dossier.case_id==d.case_id
    export=exporter_facture_csv(DonneesFacture('FICTIF-1',None,'Fournisseur été',None,Decimal('12.50'),None,None,Decimal('12.50')),racine/'exports privés'/'été.csv')
    with export.open(encoding='utf-8-sig',newline='') as f:
        assert next(csv.DictReader(f,delimiter=';'))['fournisseur']=='Fournisseur été'
    archive=creer_sauvegarde(racine/'Sauvegardes privées'/'copie été.zip')
    cible=tmp_path/'Autre utilisateur fictif'/'Restauration été'
    restaurer_sauvegarde(archive,racine=cible)
    restaure=cible/'data/dossiers_fiscaux'/p.name
    assert restaure.read_bytes()==p.read_bytes()
    assert storage.charger_dossier_fiscal(restaure).dossier.case_id==d.case_id


def test_police_csv_excel_conserve_style(tmp_path):
    from openpyxl import load_workbook
    from src.comptaprivee.document_converter import csv_vers_excel
    entree=tmp_path/'entree.csv';entree.write_text('Colonne;Autre\n1;2',encoding='utf-8')
    sortie=tmp_path/'sortie.xlsx'
    csv_vers_excel(entree,sortie)
    classeur=load_workbook(sortie)
    try:
        assert classeur.active['A1'].font.bold is True
        assert classeur.active['A2'].font.bold is False
        assert classeur.active['A1'].font.name==classeur.active['A2'].font.name
    finally:classeur.close()
