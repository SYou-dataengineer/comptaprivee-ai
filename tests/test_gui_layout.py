"""Validation réelle de Tkinter, sous Windows ou Xvfb sur Linux."""

from types import SimpleNamespace
import tkinter as tk
from tkinter import ttk

import pytest

from src.comptaprivee.gui_layout import FormulaireDefilant, dimensions_fenetre


@pytest.mark.parametrize("screen, expected", [
    ((1920, 1080), (780, 650)),
    ((800, 600), (752, 500)),
    ((3840, 2160), (780, 650)),
    ((40, 80), (1, 1)),
])
def test_dimensions_normales_et_limites(screen, expected):
    assert dimensions_fenetre(780, 650, *screen) == expected


@pytest.mark.parametrize("dimensions", [(0, 650, 800, 600),
    (780, -1, 800, 600), (780, 650, 0, 600), (780, 650, 800, -1)])
def test_dimensions_invalides(dimensions):
    with pytest.raises(ValueError):
        dimensions_fenetre(*dimensions)


@pytest.mark.parametrize("scale", [1.0, 1.5, 2.0])
def test_formulaire_defile_actions_visibles_et_focus(scale):
    root = tk.Tk()
    try:
        root.tk.call("tk", "scaling", scale)
        root.geometry("480x320")
        form = FormulaireDefilant(root)
        form.corps.columnconfigure(0, weight=1)
        label = ttk.Label(form.corps, text="Texte fiscal long. " * 20, wraplength=680)
        label.grid(sticky="ew")
        entries = []
        for _ in range(30):
            entry = ttk.Entry(form.corps)
            entry.grid(sticky="ew", pady=4)
            entries.append(entry)
        button = ttk.Button(form.actions, text="Valider et appliquer")
        button.pack(side="right")
        root.update()
        assert form.canvas.yview()[1] < 1
        assert button.winfo_rooty() + button.winfo_height() <= root.winfo_rooty() + 320
        assert button.winfo_width() >= button.winfo_reqwidth()
        assert int(label.cget("wraplength")) < 480
        form._defiler(SimpleNamespace(delta=-120))
        assert form.canvas.yview()[0] > 0
        form._montrer_focus(SimpleNamespace(widget=entries[-1]))
        root.update()
        assert entries[-1].winfo_rooty() >= form.canvas.winfo_rooty()
        assert entries[-1].winfo_rooty() + entries[-1].winfo_height() <= (
            form.canvas.winfo_rooty() + form.canvas.winfo_height()
        )
        root.geometry("780x650")
        root.update()
        assert form.corps.winfo_width() == form.canvas.winfo_width()
        form.destroy()
        assert not root.bind("<MouseWheel>")
        assert not root.bind("<FocusIn>")
    finally:
        root.destroy()


def _descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from _descendants(child)


@pytest.mark.parametrize("size", ["480x320", "780x650"])
def test_dialogue_medical_reel_erreur_effacer_et_fermer(size, monkeypatch):
    from src.comptaprivee.gui import ApplicationComptaPrivee
    from src.comptaprivee import gui

    erreurs = []
    monkeypatch.setattr(gui.messagebox, "showerror", lambda *a, **k: erreurs.append(a))
    app = ApplicationComptaPrivee()
    try:
        app.ouvrir_agent_fiscal()
        fiscal = next(w for w in app.winfo_children() if isinstance(w, tk.Toplevel))
        next(w for w in _descendants(fiscal) if isinstance(w, ttk.Button)
             and w.cget("text") == "Frais médicaux 2025").invoke()
        dialog = next(w for w in fiscal.winfo_children() if isinstance(w, tk.Toplevel))
        dialog.geometry(size)
        app.update()
        form = next(w for w in dialog.winfo_children() if isinstance(w, FormulaireDefilant))
        buttons = {w.cget("text"): w for w in form.actions.winfo_children()}
        for button in buttons.values():
            assert button.winfo_ismapped()
            assert button.winfo_rooty() + button.winfo_height() <= (
                dialog.winfo_rooty() + dialog.winfo_height())
            assert button.winfo_rootx() + button.winfo_width() <= (
                dialog.winfo_rootx() + dialog.winfo_width())
        entry = next(w for w in form.corps.winfo_children() if isinstance(w, ttk.Entry))
        entry.insert(0, "invalide")
        buttons["Valider et appliquer"].invoke()
        assert erreurs
        assert dialog.winfo_exists()
        buttons["Effacer"].invoke()
        assert entry.get() == ""
        buttons["Fermer"].invoke()
        assert not dialog.winfo_exists()
    finally:
        app.destroy()


@pytest.mark.parametrize("label", [
    "Frais de scolarité 2025", "Handicap / déficience 2025",
    "Assurance médicaments 2025", "Cotisations excédentaires 2025",
    "Personne vivant seule 2025", "Âge / retraite 2025",
    "Âge / pension fédéral 2025", "Accessibilité domicile 31285",
    "Achat habitation 31270", "Aidant 30450 fédéral 2025",
    "Aidant 30425 fédéral 2025", "Aidant enfant fédéral 2025",
    "Personne à charge fédérale 2025", "Conjoint fédéral 2025",
    "Ajustements fiscaux",
])
def test_formulaires_fiscaux_actions_accessibles(label):
    from src.comptaprivee.gui import ApplicationComptaPrivee

    app = ApplicationComptaPrivee()
    erreurs = []
    app.report_callback_exception = lambda *args: erreurs.append(args)
    try:
        app.ouvrir_agent_fiscal()
        fiscal = next(w for w in app.winfo_children() if isinstance(w, tk.Toplevel))
        button = next(w for w in _descendants(fiscal) if isinstance(w, ttk.Button)
                      and w.cget("text") == label)
        # Les ajustements sont normalement verrouillés avant validation du dossier.
        # Ici, on ne teste que leur présentation, sans lancer de calcul.
        button.configure(state="normal")
        button.invoke()
        assert not erreurs
        dialog = next(w for w in fiscal.winfo_children() if isinstance(w, tk.Toplevel))
        form = next(w for w in dialog.winfo_children() if isinstance(w, FormulaireDefilant))
        for size in ["600x400", "1000x700"]:
            dialog.geometry(size)
            app.update()
            assert not erreurs
            buttons = form.actions.winfo_children()
            assert len(buttons) >= 2
            for action in buttons:
                assert action.winfo_ismapped()
                assert action.winfo_width() >= action.winfo_reqwidth()
                assert action.winfo_rooty() + action.winfo_height() <= (
                    dialog.winfo_rooty() + dialog.winfo_height())
                assert action.winfo_rootx() + action.winfo_width() <= (
                    dialog.winfo_rootx() + dialog.winfo_width())
            form.canvas.yview_moveto(1)
            app.update()
            assert form.canvas.yview()[1] == pytest.approx(1)
    finally:
        app.destroy()
