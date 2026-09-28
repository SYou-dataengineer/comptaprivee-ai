import tkinter as tk
from tkinter import ttk
import pytest
from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre, descendants
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from src.comptaprivee.tax_training_credit_2025 import CONFIRMATIONS_FORMATION


def ouvrir(app):
    app.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(app)
    bouton(fiscal, "Frais de scolarité 2025").invoke()
    return fiscal, derniere_fenetre(fiscal)


def remplir(d):
    entries = [w for w in descendants(d) if isinstance(w, ttk.Entry)]
    for widget, valeur in zip(entries[:4], ("3000", "T2202", "3000", "Reçu Québec")):
        _remplir(widget, valeur)
    for nom, valeur in (("frais_canadiens", "3000"), ("plafond_avis_2025", "750"), ("age_fin_2025", "35"), ("source", "Avis ARC et T2202")):
        _remplir(champ(d, nom + "_5c"), valeur)
    champ(d, "reclamer_maximum_5c").invoke()
    for w in descendants(d):
        if isinstance(w, tk.Checkbutton) and w.cget("text") != "Crédit canadien pour la formation non réclamé":
            w.select()
    for nom in CONFIRMATIONS_FORMATION:
        champ(d, nom + "_5c").invoke()


def test_gui_formation_sauvegarde_et_reouverture(application):
    fiscal, d = ouvrir(application)
    remplir(d)
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    bouton(fiscal, "Frais de scolarité 2025").invoke()
    d = derniere_fenetre(fiscal)
    assert champ(d, "plafond_avis_2025_5c").get() == "750"
    assert d.getvar(champ(d, "reclamer_maximum_5c").cget("variable")) == 1
    bouton(d, "Effacer").invoke()
    assert champ(d, "source_5c").get() == ""
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists()
    fiscal.destroy()


@pytest.mark.parametrize("nom", ["frais_canadiens", "plafond_avis_2025", "age_fin_2025", "source"])
def test_gui_modification_revoque_confirmations(application, nom):
    fiscal, d = ouvrir(application)
    remplir(d)
    _remplir(champ(d, nom + "_5c"), "99")
    for confirmation in CONFIRMATIONS_FORMATION:
        assert d.getvar(champ(d, confirmation + "_5c").cget("variable")) == 0
    for w in descendants(d):
        if isinstance(w, tk.Checkbutton):
            assert d.getvar(w.cget("variable")) == 0
    bouton(d, "Fermer").invoke()
    fiscal.destroy()


def test_gui_age_inadmissible_refuse(application):
    fiscal, d = ouvrir(application)
    remplir(d)
    _remplir(champ(d, "age_fin_2025_5c"), "25")
    for w in descendants(d):
        if isinstance(w, tk.Checkbutton) and w.cget("text") != "Crédit canadien pour la formation non réclamé":
            w.select()
    for nom in CONFIRMATIONS_FORMATION:
        champ(d, nom + "_5c").invoke()
    bouton(d, "Valider et appliquer").invoke()
    assert d.winfo_exists()
    assert "26 à 65" in application.messages_test[-1][1]
    bouton(d, "Fermer").invoke()
    fiscal.destroy()
