"""Acceptation du vrai bouton Tk avec verrou simulé sur une seule destination."""
import errno
from pathlib import Path
from tkinter import ttk
import zipfile

from src.comptaprivee import app_paths, backup_manager as bm, gui, tax_case_storage
from test_tax_case_storage import _dossier


def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


def test_gui_refus_preserve_donnees_puis_nouveau_nom_et_reessai(tmp_path, monkeypatch):
    saved = tax_case_storage.sauvegarder_dossier_fiscal(_dossier())
    fiscal_before = saved.read_bytes()
    previous = bm.creer_sauvegarde(tmp_path / 'prototype.zip')
    previous_bytes = previous.read_bytes()
    new = tmp_path / 'prototype-2 été.zip'
    original_replace = bm.os.replace
    refus = True
    attempts = []

    def locked(source, destination):
        if Path(destination) == previous and refus:
            attempts.append(destination)
            raise PermissionError(errno.EACCES, 'DETAIL TECHNIQUE PRIVE', str(destination))
        return original_replace(source, destination)

    monkeypatch.setattr(bm.os, 'replace', locked)
    monkeypatch.setattr(bm.time, 'sleep', lambda delay: None)
    destinations = iter((previous, new, previous))
    monkeypatch.setattr(gui.filedialog, 'asksaveasfilename', lambda **kw: str(next(destinations)))
    errors, successes, callbacks = [], [], []
    monkeypatch.setattr(gui.messagebox, 'showerror', lambda *a, **kw: errors.append(a))
    monkeypatch.setattr(gui.messagebox, 'showinfo', lambda *a, **kw: successes.append(a))
    app = gui.ApplicationComptaPrivee()
    app.withdraw()
    app.report_callback_exception = lambda *args: callbacks.append(args)
    try:
        app.ouvrir_parametres()
        app.update()
        button = next(w for w in descendants(app)
                      if isinstance(w, ttk.Button) and w.cget('text') == 'Créer une sauvegarde...')
        button.invoke()
        app.update()
        assert len(attempts) == 4
        assert len(errors) == 1 and not successes and not callbacks
        message = errors[0][1]
        assert 'conservée' in message and 'réessayez' in message and 'autre nom' in message
        assert 'PermissionError' not in message and 'DETAIL TECHNIQUE' not in message
        assert str(tmp_path) not in message and 'Traceback' not in message
        assert 'non confirmée' in app.statut.get()
        assert previous.read_bytes() == previous_bytes
        assert saved.read_bytes() == fiscal_before
        assert not list(tmp_path.glob('.backup-*'))

        # Le même bouton fonctionne immédiatement sur un autre nom, verrou maintenu.
        button.invoke()
        app.update()
        assert len(successes) == 1 and len(errors) == 1
        assert new.name in app.statut.get()
        with zipfile.ZipFile(new) as archive:
            assert archive.testzip() is None
            assert archive.read('data/dossiers_fiscaux/' + saved.name) == fiscal_before
        assert previous.read_bytes() == previous_bytes

        # Une tentative ultérieure sur le nom d'origine fonctionne après libération.
        refus = False
        button.invoke()
        app.update()
        assert len(successes) == 2 and not callbacks
        assert app.winfo_exists()
        with zipfile.ZipFile(previous) as archive:
            assert archive.testzip() is None
        assert saved.read_bytes() == fiscal_before
        assert not list(tmp_path.glob('.backup-*'))
    finally:
        app.destroy()
