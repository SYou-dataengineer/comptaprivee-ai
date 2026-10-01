"""Remplacement ZIP borné, sans supprimer la sauvegarde précédente."""
import errno
import zipfile

import pytest

from src.comptaprivee import app_paths, backup_manager as bm


@pytest.fixture
def settings():
    path = app_paths.settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"devise":"CAD"}', encoding='utf-8')
    return path


def assert_lisible(destination, devise):
    with zipfile.ZipFile(destination) as archive:
        assert archive.testzip() is None
        assert devise in archive.read('data/parametres.json').decode('utf-8')


@pytest.mark.parametrize('directory', ['normal', 'avec espaces', 'été Québec'])
def test_creation_puis_remplacements(tmp_path, settings, directory):
    destination = tmp_path / directory / 'prototype.zip'
    for devise in ('CAD', 'USD', 'EUR'):
        settings.write_text('{"devise":"' + devise + '"}', encoding='utf-8')
        assert bm.creer_sauvegarde(destination) == destination
        assert_lisible(destination, devise)
        assert not list(destination.parent.glob('.backup-*'))


def test_refus_transitoire_reessaie_seulement_replace(tmp_path, settings, monkeypatch):
    destination = bm.creer_sauvegarde(tmp_path / 'prototype.zip')
    ancien = destination.read_bytes()
    settings.write_text('{"devise":"USD"}', encoding='utf-8')
    original = bm.os.replace
    appels, delais = [], []

    def transient(source, target):
        appels.append((source, target, source.read_bytes()))
        if len(appels) <= 2:
            assert destination.read_bytes() == ancien
            raise PermissionError(errno.EACCES, 'Refus fictif', str(target))
        original(source, target)

    monkeypatch.setattr(bm.os, 'replace', transient)
    monkeypatch.setattr(bm.time, 'sleep', delais.append)
    bm.creer_sauvegarde(destination)
    assert len(appels) == 3 and appels[0] == appels[1] == appels[2]
    assert delais == [0.05, 0.10]
    assert_lisible(destination, 'USD')


def test_refus_permanent_preserve_archive_et_erreur(tmp_path, settings, monkeypatch):
    destination = bm.creer_sauvegarde(tmp_path / 'prototype.zip')
    ancien = destination.read_bytes()
    erreur = PermissionError(errno.EACCES, 'Refus permanent fictif', str(destination))
    appels, delais = [], []

    def refuse(*args):
        appels.append(args)
        raise erreur

    monkeypatch.setattr(bm.os, 'replace', refuse)
    monkeypatch.setattr(bm.time, 'sleep', delais.append)
    with pytest.raises(PermissionError) as raised:
        bm.creer_sauvegarde(destination)
    assert raised.value is erreur
    assert len(appels) == 4 and delais == [0.05, 0.10, 0.20]
    assert destination.read_bytes() == ancien
    assert_lisible(destination, 'CAD')
    assert not list(tmp_path.glob('.backup-*'))


def test_autre_erreur_non_reessayee(tmp_path, settings, monkeypatch):
    appels, delais = [], []

    def refuse(*args):
        appels.append(args)
        raise OSError(errno.ENOSPC, 'Disque plein fictif')

    monkeypatch.setattr(bm.os, 'replace', refuse)
    monkeypatch.setattr(bm.time, 'sleep', delais.append)
    with pytest.raises(OSError) as raised:
        bm.creer_sauvegarde(tmp_path / 'prototype.zip')
    assert raised.value.errno == errno.ENOSPC
    assert len(appels) == 1 and not delais


def test_zip_applicatifs_fermes_avant_remplacement(tmp_path, settings, monkeypatch):
    archives = []
    original_zip = zipfile.ZipFile
    original_replace = bm.os.replace

    class ZipObserve(original_zip):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            archives.append(self)  # Pas de fermeture accidentelle par GC.

    def replace(source, destination):
        assert archives and all(archive.fp is None for archive in archives)
        # Sur Windows, renommer la source exige aussi la libération du handle.
        original_replace(source, destination)

    monkeypatch.setattr(bm.zipfile, 'ZipFile', ZipObserve)
    monkeypatch.setattr(bm.os, 'replace', replace)
    destination = tmp_path / 'prototype.zip'
    for _ in range(3):
        bm.creer_sauvegarde(destination)
        assert_lisible(destination, 'CAD')
    assert all(archive.fp is None for archive in archives)
