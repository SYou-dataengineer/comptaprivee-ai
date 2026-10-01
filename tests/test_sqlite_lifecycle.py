"""Connexions fermées avant restauration, indépendamment du ramasse-miettes."""
from contextlib import closing
import sqlite3
import subprocess
import sys

import pytest

from src.comptaprivee import app_paths, audit_log, database
from src.comptaprivee.backup_manager import creer_sauvegarde, restaurer_sauvegarde
from src.comptaprivee.facture_parser import DonneesFacture


def test_operations_liberent_connexions_et_restauration(monkeypatch, tmp_path):
    connexions = []
    original = database.ouvrir_connexion

    def retenir(*args, **kwargs):
        connexion = original(*args, **kwargs)
        connexions.append(connexion)  # Interdit toute fermeture par GC.
        return connexion

    monkeypatch.setattr(database, 'ouvrir_connexion', retenir)
    monkeypatch.setattr(audit_log, 'ouvrir_connexion', retenir)
    facture = DonneesFacture('FICTIF-C2', None, 'Fictif', None, None, None, None, None)
    try:
        for _ in range(3):
            item = database.enregistrer_facture(facture)
            with pytest.raises(ValueError, match='existe déjà'):
                database.enregistrer_facture(facture)
            assert database.rechercher_factures('FICTIF-C2')
            assert database.lister_factures()
            assert database.mettre_facture_corbeille(item.identifiant)
            assert database.lister_factures_corbeille()
            assert database.restaurer_facture(item.identifiant)
            restored = database.lister_factures()[0]
            assert database.mettre_facture_corbeille(restored.identifiant)
            assert database.supprimer_facture_corbeille(restored.identifiant)
            archive = creer_sauvegarde(tmp_path / 'fictif.zip')
            restaurer_sauvegarde(archive)
        assert connexions
        for connexion in connexions:
            with pytest.raises(sqlite3.ProgrammingError, match='closed'):
                connexion.execute('SELECT 1')
        assert not list(tmp_path.glob('.restore-*'))
        assert not list(tmp_path.glob('.backup-*'))
        assert not list(app_paths.temp_dir().iterdir())
    finally:
        for connexion in connexions:
            connexion.close()


@pytest.mark.parametrize('mode', ['DELETE', 'WAL'])
def test_reouverture_apres_sortie_brutale_sans_effacer_db(tmp_path, mode):
    path = tmp_path / 'base fictive été.db'
    script = '''
import os,sqlite3,sys
c=sqlite3.connect(sys.argv[1])
c.execute('PRAGMA journal_mode='+sys.argv[2])
c.execute('CREATE TABLE fictif (n INTEGER)')
c.execute('INSERT INTO fictif VALUES (1)'); c.commit()
c.execute('INSERT INTO fictif VALUES (2)')
os._exit(17)
'''
    result = subprocess.run([sys.executable, '-c', script, str(path), mode], timeout=20)
    assert result.returncode == 17
    assert path.exists()
    with closing(sqlite3.connect(path)) as c:
        assert c.execute('PRAGMA integrity_check').fetchone() == ('ok',)
        assert c.execute('SELECT n FROM fictif').fetchall() == [(1,)]
        with c:
            c.execute('INSERT INTO fictif VALUES (3)')
    with closing(sqlite3.connect(path)) as c:
        assert c.execute('SELECT n FROM fictif ORDER BY n').fetchall() == [(1,), (3,)]
