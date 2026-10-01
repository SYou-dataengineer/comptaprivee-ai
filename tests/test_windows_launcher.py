import sys
from pathlib import Path
import pytest
from scripts import windows_launcher as launcher
from src.comptaprivee import app_paths


def test_lanceur_appelle_gui_existante(monkeypatch):
    from src.comptaprivee import gui
    appels=[]
    monkeypatch.setattr(sys,'argv',['ComptaPriveeAI.exe'])
    monkeypatch.setattr(gui,'lancer_interface',lambda:appels.append(True))
    assert launcher.main()==0
    assert appels==[True]


def test_erreur_demarrage_code_et_journal_sans_donnee(monkeypatch):
    from src.comptaprivee import gui
    from tkinter import messagebox
    monkeypatch.setattr(sys,'argv',['ComptaPriveeAI.exe'])
    monkeypatch.setattr(sys,'platform','linux')
    def erreur(): raise RuntimeError('contenu confidentiel interdit au journal')
    messages=[]
    monkeypatch.setattr(gui,'lancer_interface',erreur)
    monkeypatch.setattr(messagebox,'showerror',lambda *a:messages.append(a))
    assert launcher.main()==1
    journal=(app_paths.logs_dir()/'startup.log').read_text(encoding='utf-8')
    assert 'RuntimeError' in journal
    assert 'confidentiel' not in journal
    assert messages


def test_diagnostic_refuse_profil_non_autorise(monkeypatch):
    from scripts.prototype_check import run
    monkeypatch.delenv('COMPTAPRIVEE_PROTOTYPE_CHECK',raising=False)
    with pytest.raises(RuntimeError,match='isolé'): run()


def test_diagnostic_refuse_donnees_existantes(monkeypatch):
    from scripts.prototype_check import run
    monkeypatch.setenv('COMPTAPRIVEE_PROTOTYPE_CHECK','1')
    root=app_paths.user_data_dir();root.mkdir(parents=True,exist_ok=True)
    (root/'inconnu').write_text('ne pas toucher')
    with pytest.raises(RuntimeError,match='préserver'): run()
    assert (root/'inconnu').read_text()=='ne pas toucher'


@pytest.mark.parametrize('produit', ['Word','Excel'])
def test_office_absent_message_clair(monkeypatch,tmp_path,produit):
    from src.comptaprivee import document_converter as convert
    monkeypatch.setattr(sys,'platform','win32')
    # Module synthétique : ce test reste exécutable sans Office et sous Linux.
    import types
    client=types.ModuleType('win32com.client')
    def absent(*a,**kw): raise RuntimeError('absent fictif')
    client.DispatchEx=absent
    parent=types.ModuleType('win32com');parent.client=client
    monkeypatch.setitem(sys.modules,'win32com',parent)
    monkeypatch.setitem(sys.modules,'win32com.client',client)
    source=tmp_path/('fictif.docx' if produit=='Word' else 'fictif.xlsx')
    source.write_bytes(b'fictif')
    fonction=convert.word_vers_pdf if produit=='Word' else convert.excel_vers_pdf
    with pytest.raises(convert.ErreurConversion,match='Microsoft '+produit+' installé'):
        fonction(source,tmp_path/'sortie.pdf')
