"""Régressions FINAL-B1, exclusivement données fictives."""
import hashlib
import json
import os
import stat
import zipfile
from dataclasses import replace
from pathlib import Path

import pytest
from src.comptaprivee import backup_manager as backup
from tests.storage_helpers import restaurer_dans_profil
from src.comptaprivee import tax_case_storage as storage
from src.comptaprivee.tax_case import creer_dossier_fiscal
from src.comptaprivee.tax_validated_case import construire_dossier_fiscal_valide
from test_tax_case_storage import _dossier


def archive(tmp_path, fichiers, modifier=None, lien=None):
    entrees = [dict(chemin=n, categorie=backup.FIXES.get(n, 'donnees_fiscales'), taille=len(v), sha256=hashlib.sha256(v).hexdigest()) for n,v in fichiers.items()]
    manifeste = dict(version=1, application='ComptaPrivée AI', cree_le='2025-01-01', fichiers=entrees)
    if modifier:
        modifier(manifeste)
    chemin = tmp_path / 'backup.zip'
    with zipfile.ZipFile(chemin, 'w') as z:
        z.writestr('manifest.json', json.dumps(manifeste))
        for nom, contenu in fichiers.items():
            info = zipfile.ZipInfo(nom)
            if nom == lien:
                info.create_system = 3
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
            z.writestr(info, contenu)
    return chemin


@pytest.mark.parametrize('nom', ['src/comptaprivee/gui.py', '.git/config', '../evil', '/evil', 'C:/evil', 'data/../evil', 'data\\parametres.json', 'tests/a.py', 'requirements.txt', 'data/inconnu.json', 'data/dossiers_fiscaux/CON.json', 'data/dossiers_fiscaux/a.json:stream', 'data/dossiers_fiscaux/a.tmp'])
def test_destination_interdite(tmp_path, nom):
    p = archive(tmp_path, {nom: b'{}'})
    cible = tmp_path/'cible'
    with pytest.raises(ValueError): restaurer_dans_profil(p, racine=cible)
    assert not cible.exists()


@pytest.mark.parametrize('modifier', [
    lambda m:m.update(version=2), lambda m:m.update(version=True),
    lambda m:m.update(application='autre'), lambda m:m.update(fichiers='faux'),
    lambda m:m.update(inconnu='src/code.py'), lambda m:m['fichiers'][0].update(taille=99),
    lambda m:m['fichiers'][0].update(sha256='0'*64),
    lambda m:m['fichiers'][0].update(categorie='code'),
    lambda m:m['fichiers'][0].update(chemin='src/a.py'),
    lambda m:m.update(fichiers=[]),
])
def test_manifeste_invalide(tmp_path, modifier):
    p = archive(tmp_path, {'data/parametres.json':b'{}'}, modifier)
    with pytest.raises(ValueError): restaurer_dans_profil(p, racine=tmp_path/'cible')
    assert not (tmp_path/'cible').exists()


def test_refus_symlink_archive(tmp_path):
    p = archive(tmp_path, {'data/parametres.json':b'{}'}, lien='data/parametres.json')
    with pytest.raises(ValueError): restaurer_dans_profil(p, racine=tmp_path/'cible')


def test_refus_parent_lie(tmp_path, monkeypatch):
    p = archive(tmp_path, {'data/parametres.json':b'{}'})
    original = Path.is_symlink
    monkeypatch.setattr(Path, 'is_symlink', lambda self:self.name == 'data' or original(self))
    with pytest.raises(ValueError): restaurer_dans_profil(p, racine=tmp_path/'cible')


def test_validation_integrale_avant_ecriture(tmp_path):
    p = archive(tmp_path, {'data/parametres.json':b'{}', 'data/profil_comptable.json':b'invalide'})
    cible = tmp_path/'cible'; (cible/'data').mkdir(parents=True)
    ancien = cible/'data/parametres.json'; ancien.write_bytes(b'{"avant":true}')
    with pytest.raises(ValueError): restaurer_dans_profil(p, racine=cible)
    assert ancien.read_bytes() == b'{"avant":true}'


@pytest.mark.parametrize('existant', [True, False])
def test_rollback_apres_premier_remplacement(tmp_path, monkeypatch, existant):
    p = archive(tmp_path, {'data/parametres.json':b'{}', 'data/profil_comptable.json':b'{}'})
    cible=tmp_path/'cible'; (cible/'data').mkdir(parents=True)
    ancien=cible/'data/parametres.json'
    if existant: ancien.write_bytes(b'{"avant":true}')
    original=os.replace
    def interrompre(src,dst):
        if Path(src).name == 'nouveau-1': raise OSError('interruption fictive')
        return original(src,dst)
    monkeypatch.setattr(backup.os,'replace',interrompre)
    with pytest.raises(OSError): restaurer_dans_profil(p,racine=cible)
    assert ancien.read_bytes() == b'{"avant":true}' if existant else not ancien.exists()
    assert not (cible/'data/profil_comptable.json').exists()
    assert not list(cible.glob('.restore-*'))


def test_backup_roundtrip_fiscal(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fiscaux=tmp_path/'data/dossiers_fiscaux'
    monkeypatch.setattr(storage,'DOSSIERS_FISCAUX_DIR',fiscaux)
    p=storage.sauvegarder_dossier_fiscal(_dossier())
    (fiscaux/'ignore.tmp').write_text('temp')
    (tmp_path/'src').mkdir(); (tmp_path/'src/code.py').write_text('code')
    z=backup.creer_sauvegarde(tmp_path/'backup.zip')
    with zipfile.ZipFile(z) as a:
        assert set(a.namelist()) == {'manifest.json','data/dossiers_fiscaux/'+p.name}
        m=json.loads(a.read('manifest.json'))
        assert m['fichiers'][0]['categorie']=='donnees_fiscales'
    destination=tmp_path/'restaure'
    restaurer_dans_profil(z,racine=destination)
    r=destination/'data/dossiers_fiscaux'/p.name
    assert p.read_bytes()==r.read_bytes()
    assert storage.charger_dossier_fiscal(r).dossier.case_id == storage.charger_dossier_fiscal(p).dossier.case_id


@pytest.mark.parametrize('noms', [('Audit / A','Audit : A'),('Homonyme','Homonyme')])
def test_identites_distinctes(tmp_path, monkeypatch,noms):
    monkeypatch.setattr(storage,'DOSSIERS_FISCAUX_DIR',tmp_path)
    a,b=[replace(_dossier(),client=n) for n in noms]
    pa,pb=[storage.sauvegarder_dossier_fiscal(d) for d in (a,b)]
    assert pa!=pb and a.case_id!=b.case_id
    assert storage.charger_dossier_fiscal(pa).dossier.case_id==a.case_id
    assert storage.charger_dossier_fiscal(pb).dossier.case_id==b.case_id


def test_renommage_et_refus_autre_identite(tmp_path,monkeypatch):
    monkeypatch.setattr(storage,'DOSSIERS_FISCAUX_DIR',tmp_path)
    d=_dossier(); p=storage.sauvegarder_dossier_fiscal(d)
    assert storage.sauvegarder_dossier_fiscal(replace(d,client='Renommé'))==p
    avant=p.read_bytes()
    with pytest.raises(ValueError,match='case_id'): storage.sauvegarder_dossier_fiscal(_dossier(),destination=p)
    assert p.read_bytes()==avant


def test_migration_sans_ecriture_puis_persistance(tmp_path):
    p=storage.sauvegarder_dossier_fiscal(_dossier(),destination=tmp_path/'ancien.json')
    contenu=json.loads(p.read_text(encoding='utf-8'));del contenu['case_id']
    p.write_text(json.dumps(contenu),encoding='utf-8');avant=p.read_bytes()
    a=storage.charger_dossier_fiscal(p).dossier
    b=storage.charger_dossier_fiscal(p).dossier
    assert a.case_id==b.case_id and p.read_bytes()==avant
    storage.sauvegarder_dossier_fiscal(a,destination=p)
    assert json.loads(p.read_text(encoding='utf-8'))['case_id']==a.case_id


def test_draft_identite_validation():
    from src.comptaprivee.tax_field_extractor import DonneeFiscaleExtraite
    from src.comptaprivee.tax_field_validation import valider_donnee_fiscale,cle_donnee_fiscale
    from decimal import Decimal
    brut=creer_dossier_fiscal(client='Fictif',annee_fiscale=2025)
    d=DonneeFiscaleExtraite(Path('test.pdf'),'T4','14','Salaire',Decimal('1'),'1')
    valide=construire_dossier_fiscal_valide(brut,[d],{cle_donnee_fiscale(d):valider_donnee_fiscale(d)})
    assert valide.case_id==brut.case_id
    assert creer_dossier_fiscal(client='Fictif',annee_fiscale=2025).case_id!=brut.case_id


def test_migration_default_conserve_chemin(tmp_path,monkeypatch):
    monkeypatch.setattr(storage,'DOSSIERS_FISCAUX_DIR',tmp_path)
    p=storage.sauvegarder_dossier_fiscal(_dossier(),destination=tmp_path/'ancien.json')
    contenu=json.loads(p.read_text(encoding='utf-8'));del contenu['case_id']
    p.write_text(json.dumps(contenu),encoding='utf-8')
    d=storage.charger_dossier_fiscal(p).dossier
    assert storage.sauvegarder_dossier_fiscal(d)==p
    assert len(list(tmp_path.glob('*.json')))==1


def test_restore_case_id_autre_dossier_refuse(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(storage,'DOSSIERS_FISCAUX_DIR',tmp_path/'data/dossiers_fiscaux')
    d=_dossier();p=storage.sauvegarder_dossier_fiscal(d)
    z=backup.creer_sauvegarde(tmp_path/'backup.zip')
    cible=tmp_path/'cible'
    autre=storage.sauvegarder_dossier_fiscal(_dossier(),destination=cible/'data/dossiers_fiscaux'/p.name)
    avant=autre.read_bytes()
    with pytest.raises(ValueError,match='case_id'):restaurer_dans_profil(z,racine=cible)
    assert autre.read_bytes()==avant


def test_entree_non_declaree(tmp_path):
    z=archive(tmp_path,{'data/parametres.json':b'{}'})
    with zipfile.ZipFile(z,'a') as a:a.writestr('data/profil_comptable.json',b'{}')
    with pytest.raises(ValueError):restaurer_dans_profil(z,racine=tmp_path/'cible')


def test_zip_invalide(tmp_path):
    p=tmp_path/'faux.zip';p.write_bytes(b'pas un zip')
    with pytest.raises(ValueError):restaurer_dans_profil(p,racine=tmp_path/'cible')


def test_rollback_impossible_conserve_secours(tmp_path,monkeypatch):
    z=archive(tmp_path,{'data/parametres.json':b'{}','data/profil_comptable.json':b'{}'})
    cible=tmp_path/'cible';(cible/'data').mkdir(parents=True)
    (cible/'data/parametres.json').write_bytes(b'{"ancien":true}')
    original=os.replace
    def panne(src,dst):
        if Path(src).name in {'nouveau-1','ancien-0'}:raise OSError('panne simulee')
        return original(src,dst)
    monkeypatch.setattr(backup.os,'replace',panne)
    with pytest.raises(RuntimeError,match='copies de secours'):restaurer_dans_profil(z,racine=cible)
    secours=list(cible.glob('.restore-*/ancien-0'))
    assert len(secours)==1 and secours[0].read_bytes()==b'{"ancien":true}'


def test_roundtrip_base_sqlite_et_parametres(tmp_path,monkeypatch):
    import sqlite3
    from contextlib import closing
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(storage,'DOSSIERS_FISCAUX_DIR',tmp_path/'data/dossiers_fiscaux')
    (tmp_path/'data').mkdir()
    with closing(sqlite3.connect('data/comptaprivee.db')) as db:
        db.execute('create table fictif (id integer)');db.execute('insert into fictif values (1)');db.commit()
    Path('data/parametres.json').write_bytes(b'{"langue":"fr"}')
    z=backup.creer_sauvegarde(tmp_path/'backup.zip')
    cible=tmp_path/'cible';restaurer_dans_profil(z,racine=cible)
    with zipfile.ZipFile(z) as a:
        for nom in ['data/comptaprivee.db','data/parametres.json']:
            assert (cible/nom).read_bytes()==a.read(nom)


@pytest.mark.parametrize('valeur',[None,'../autre','pas-un-uuid'])
def test_case_id_invalide(tmp_path,valeur):
    p=storage.sauvegarder_dossier_fiscal(_dossier(),destination=tmp_path/'d.json')
    contenu=json.loads(p.read_text(encoding='utf-8'));contenu['case_id']=valeur
    with pytest.raises(ValueError,match='Identifiant'):storage.dossier_fiscal_depuis_contenu(contenu,verifier_documents=False)
