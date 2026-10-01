"""POST-V1-B : toutes les données sont fictives et hors du programme."""
import json
import os
import sqlite3
import zipfile
from pathlib import Path

import pytest
from src.comptaprivee import app_paths as paths, tax_case_storage as storage
from src.comptaprivee.backup_manager import creer_sauvegarde, restaurer_sauvegarde, _nom_archive
from src.comptaprivee.data_migration import migrer_ancien_data
from src.comptaprivee.database import initialiser_base
from src.comptaprivee.settings import enregistrer_parametres, lire_parametres, ParametresApplication
from src.comptaprivee.company_profile import enregistrer_profil_societe, lire_profil_societe, ProfilSociete
from tests.test_tax_case_storage import _dossier


@pytest.fixture
def profil(tmp_path, monkeypatch):
    programme = tmp_path / 'Program Files fictif'
    programme.mkdir()
    utilisateur = tmp_path / 'Utilisateur Élodie' / 'ComptaPriveeAI'
    monkeypatch.setattr(paths, 'PROGRAM_DIR', programme)
    monkeypatch.setattr(paths, 'RESOURCE_DIR', programme)
    monkeypatch.setattr(paths, 'USER_DATA_DIR', utilisateur)
    monkeypatch.setattr(storage, 'DOSSIERS_FISCAUX_DIR', paths.tax_cases_dir())
    monkeypatch.chdir(programme)
    return programme, utilisateur


def test_parcours_sans_ecriture_programme(profil, monkeypatch):
    programme, root = profil
    original = Path.mkdir
    def interdire(self, *args, **kw):
        if self.resolve().is_relative_to(programme): raise PermissionError('programme non inscriptible')
        return original(self, *args, **kw)
    monkeypatch.setattr(Path, 'mkdir', interdire)
    assert initialiser_base() == paths.database_path()
    enregistrer_parametres(ParametresApplication())
    enregistrer_profil_societe(ProfilSociete(nom_societe='Cabinet fictif'))
    dossier = _dossier(); fichier = storage.sauvegarder_dossier_fiscal(dossier)
    assert storage.charger_dossier_fiscal(fichier).dossier.case_id == dossier.case_id
    assert lire_parametres().devise == 'CAD'
    assert lire_profil_societe().nom_societe == 'Cabinet fictif'
    from src.comptaprivee.document_converter import _preparer_destination
    sortie = _preparer_destination(programme / 'fictif.docx', None, '.pdf')
    assert sortie == paths.exports_dir() / 'fictif.pdf'
    from src.comptaprivee.ocr_review_queue import _enregistrer, _charger
    _enregistrer([], None); assert _charger(None) == []
    paths.temp_dir().joinpath('fictif.tmp').write_text('temporaire fictif')
    z = creer_sauvegarde(root.parent / 'copie.zip')
    with zipfile.ZipFile(z) as archive:
        assert set(archive.namelist()) == {'manifest.json','data/comptaprivee.db',
            'data/parametres.json','data/profil_comptable.json','data/dossiers_fiscaux/'+fichier.name}
    restaurer_sauvegarde(z)
    assert list(programme.iterdir()) == []


def test_racine_windows(monkeypatch, tmp_path):
    monkeypatch.setattr(paths.sys, 'platform', 'win32')
    monkeypatch.setenv('LOCALAPPDATA', str(tmp_path / 'Été local'))
    assert paths._user_root() == tmp_path / 'Été local/ComptaPriveeAI'


def test_ressources_independantes_cwd(profil, monkeypatch):
    programme, root = profil
    root.mkdir(parents=True); monkeypatch.chdir(root)
    assert paths.resource_path('icone.ico') == programme / 'icone.ico'
    with pytest.raises(ValueError): paths.resource_path('../fuite')


def test_refus_donnees_dans_programme(profil, monkeypatch):
    monkeypatch.setattr(paths, 'USER_DATA_DIR', profil[0] / 'data')
    with pytest.raises(ValueError): paths.user_data_dir()


def test_restore_hors_profil_refuse(profil):
    with pytest.raises(ValueError, match='USER_DATA_DIR'):
        restaurer_sauvegarde('absent.zip', racine=profil[0])


def test_nom_archive_absolu_par_categorie(profil):
    assert _nom_archive(paths.database_path()) == 'data/comptaprivee.db'
    assert _nom_archive(paths.settings_path()) == 'data/parametres.json'
    assert _nom_archive(paths.accounting_profile_path()) == 'data/profil_comptable.json'
    with pytest.raises(ValueError): _nom_archive(profil[0] / 'code.py')
    with pytest.raises(ValueError): _nom_archive(paths.exports_dir() / 'rapport.pdf')


def historique(tmp_path):
    ancien = tmp_path / 'Ancien dépôt'
    (ancien / 'data/dossiers_fiscaux').mkdir(parents=True)
    (ancien / 'data/documents').mkdir()
    (ancien / 'data/documents/original.pdf').write_bytes(b'fictif')
    (ancien / 'data/exports').mkdir()
    (ancien / 'data/exports/rapport.csv').write_text('fictif')
    (ancien / 'data/parametres.json').write_text('{"devise":"CAD"}')
    with sqlite3.connect(ancien / 'data/comptaprivee.db') as db:
        db.execute('CREATE TABLE fictif (id INTEGER)')
        db.execute('INSERT INTO fictif VALUES (42)')
    fichier = storage.sauvegarder_dossier_fiscal(_dossier(), destination=ancien / 'data/dossiers_fiscaux/ancien.json')
    return ancien, fichier


@pytest.mark.parametrize('sans_id', [False, True])
def test_migration_idempotente_identite_et_sources(profil, tmp_path, sans_id):
    ancien, fichier = historique(tmp_path)
    if sans_id:
        brut=json.loads(fichier.read_text(encoding='utf-8'));brut.pop('case_id')
        fichier.write_text(json.dumps(brut),encoding='utf-8')
    avant=fichier.read_bytes(); ident=storage.charger_dossier_fiscal(fichier).dossier.case_id
    assert migrer_ancien_data(ancien) == 4
    assert migrer_ancien_data(ancien) == 0
    assert fichier.read_bytes() == avant
    copie=storage.charger_dossier_fiscal(paths.tax_cases_dir() / fichier.name)
    assert copie.dossier.case_id == ident
    assert all(p.is_absolute() for p in copie.dossier.documents)
    assert (ancien / 'data/documents/original.pdf').exists()
    assert not (profil[1] / 'data/documents').exists()
    assert (paths.exports_dir() / 'rapport.csv').read_text() == 'fictif'
    assert 'Client' not in (paths.logs_dir() / 'migration.log').read_text()
    with sqlite3.connect(paths.database_path()) as db:
        assert db.execute('SELECT id FROM fictif').fetchone() == (42,)


def test_conflit_avant_copie(profil, tmp_path):
    ancien, _ = historique(tmp_path)
    paths.settings_path().parent.mkdir(parents=True)
    paths.settings_path().write_text('{"autre":true}')
    with pytest.raises(ValueError, match='Conflit'): migrer_ancien_data(ancien)
    assert not paths.database_path().exists()
    assert paths.settings_path().read_text() == '{"autre":true}'


def test_migration_refuse_liens(profil, tmp_path, monkeypatch):
    ancien, _ = historique(tmp_path)
    original=Path.is_symlink
    monkeypatch.setattr(Path, 'is_symlink', lambda p:p.name=='parametres.json' or original(p))
    with pytest.raises(ValueError, match='lien'): migrer_ancien_data(ancien)
    assert not paths.database_path().exists()


def test_temporaire_nettoye(profil):
    import tempfile
    with tempfile.TemporaryDirectory(dir=paths.temp_dir()) as td:
        p=Path(td);(p/'fictif').write_text('fictif')
    assert not p.exists()
