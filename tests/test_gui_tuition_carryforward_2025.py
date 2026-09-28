import tkinter as tk
from tkinter import ttk
import pytest
from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre, descendants
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from tests.test_gui_training_credit_2025 import ouvrir
from src.comptaprivee.tax_tuition_carryforward_2025 import CONFIRMATIONS_REPORTS_SCOLARITE


def remplir(d):
    entries = [w for w in descendants(d) if isinstance(w, ttk.Entry)]
    for w, v in zip(entries[:4], ("3000", "T2202 fictif", "0", "")):
        _remplir(w, v)
    _remplir(champ(d, "report_avis_2024_5f"), "1000")
    _remplir(champ(d, "source_5f"), "Avis ARC fictif")
    champ(d, "activer_5f").invoke()
    for w in descendants(d):
        if isinstance(w, tk.Checkbutton) and w.cget("text") != "Aucun report antérieur":
            w.select()
    for nom in CONFIRMATIONS_REPORTS_SCOLARITE:
        champ(d, nom + "_5f").invoke()


def test_gui_report_reouverture_effacer(application):
    fiscal, d = ouvrir(application)
    remplir(d)
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    bouton(fiscal, "Frais de scolarité 2025").invoke()
    d = derniere_fenetre(fiscal)
    assert champ(d, "report_avis_2024_5f").get() == "1000"
    bouton(d, "Effacer").invoke()
    assert champ(d, "source_5f").get() == ""
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists()
    fiscal.destroy()


@pytest.mark.parametrize("nom", ["report_avis_2024", "source", "activer"])
def test_gui_modification_revoque(application, nom):
    fiscal, d = ouvrir(application)
    remplir(d)
    if nom == "activer":
        champ(d, "activer_5f").invoke()
    else:
        _remplir(champ(d, nom + "_5f"), "99")
    for confirmation in CONFIRMATIONS_REPORTS_SCOLARITE:
        assert d.getvar(champ(d, confirmation + "_5f").cget("variable")) == 0
    for w in descendants(d):
        if isinstance(w, tk.Checkbutton):
            assert d.getvar(w.cget("variable")) == 0
    bouton(d, "Fermer").invoke()
    fiscal.destroy()
