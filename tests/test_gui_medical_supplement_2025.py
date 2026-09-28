import tkinter as tk
from tkinter import ttk
import pytest
from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre, descendants
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from src.comptaprivee.tax_medical_supplement_2025 import CONFIRMATIONS_SUPPLEMENT


def ouvrir(app):
    app.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(app)
    bouton(fiscal, "Frais médicaux 2025").invoke()
    return fiscal, derniere_fenetre(fiscal)


def confirmer(d):
    for w in descendants(d):
        if isinstance(w, tk.Checkbutton):
            w.select()
    for nom in CONFIRMATIONS_SUPPLEMENT:
        champ(d, nom + "_5d").invoke()


def remplir(d):
    entries = [w for w in descendants(d) if isinstance(w, ttk.Entry)]
    for widget, valeur in zip(entries[:4], ("10000", "Reçus fédéraux", "10000", "Reçus Québec")):
        _remplir(widget, valeur)
    _remplir(champ(d, "age_fin_2025_5d"), "35")
    _remplir(champ(d, "source_5d"), "Validation comptable fictive")
    champ(d, "reclamer_5d").invoke()
    confirmer(d)


def test_gui_supplement_reouverture_effacer(application):
    fiscal, d = ouvrir(application)
    remplir(d)
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    bouton(fiscal, "Frais médicaux 2025").invoke()
    d = derniere_fenetre(fiscal)
    assert champ(d, "age_fin_2025_5d").get() == "35"
    assert d.getvar(champ(d, "reclamer_5d").cget("variable")) == 1
    bouton(d, "Effacer").invoke()
    assert champ(d, "source_5d").get() == ""
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists()
    fiscal.destroy()


@pytest.mark.parametrize("nom", ["age_fin_2025", "source", "frais_bruts", "reclamer"])
def test_gui_revoque_confirmations(application, nom):
    fiscal, d = ouvrir(application)
    remplir(d)
    if nom == "frais_bruts":
        _remplir(next(w for w in descendants(d) if isinstance(w, ttk.Entry)), "5000")
    elif nom == "reclamer":
        champ(d, "reclamer_5d").invoke()
    else:
        _remplir(champ(d, nom + "_5d"), "99")
    for confirmation in CONFIRMATIONS_SUPPLEMENT:
        assert d.getvar(champ(d, confirmation + "_5d").cget("variable")) == 0
    for w in descendants(d):
        if isinstance(w, tk.Checkbutton):
            assert d.getvar(w.cget("variable")) == 0
    bouton(d, "Fermer").invoke()
    fiscal.destroy()


def test_gui_age_inadmissible(application):
    fiscal, d = ouvrir(application)
    remplir(d)
    _remplir(champ(d, "age_fin_2025_5d"), "17")
    confirmer(d)
    bouton(d, "Valider et appliquer").invoke()
    assert d.winfo_exists()
    assert "18 ans" in application.messages_test[-1][1]
    bouton(d, "Fermer").invoke()
    fiscal.destroy()
