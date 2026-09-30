import tkinter as tk
from tkinter import ttk

from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre, descendants
from tests.test_gui_other_deductions_2025 import _remplir
from tests.test_tax_multiple_employers_2025 import dossier_multiple, profil_multiple
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal


def ouvrir(application):
    sauvegarder_dossier_fiscal(dossier_multiple(),cotisations_excedentaires=profil_multiple())
    application.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(application)
    bouton(fiscal,"Dossiers enregistrés").invoke()
    bouton(derniere_fenetre(fiscal),"Ouvrir le dossier").invoke()
    assert not application.erreurs_test, application.messages_test
    return fiscal


def confirmation(dialogue):
    return next(w for w in descendants(dialogue) if isinstance(w,tk.Checkbutton) and str(w.cget("text")).startswith("7A :"))


def test_gui_multi_calcul_trace_pdf_et_invalidation(application,monkeypatch,tmp_path):
    from src.comptaprivee import gui
    fiscal = ouvrir(application)
    bouton(fiscal,"Calculer l'estimation fiscale 2025").invoke()
    resultat = derniere_fenetre(fiscal)
    texte = next(w for w in descendants(resultat) if isinstance(w,tk.Text)).get("1.0","end")
    assert "2430.00" in texte and "22215" in texte, application.messages_test
    bouton(resultat,"Voir le détail du calcul").invoke()
    trace = derniere_fenetre(resultat)
    texte = next(w for w in descendants(trace) if isinstance(w,tk.Text)).get("1.0","end")
    assert "Employeur2_T4.pdf" in texte
    trace.destroy()
    pdf = tmp_path/"7a_gui.pdf"
    monkeypatch.setattr(gui.filedialog,"asksaveasfilename",lambda **kw: str(pdf))
    bouton(resultat,"Exporter le rapport fiscal en PDF").invoke()
    assert pdf.exists(), application.messages_test
    bouton(fiscal,"Cotisations excédentaires 2025").invoke()
    d = derniere_fenetre(fiscal)
    c = confirmation(d)
    assert d.getvar(c.cget("variable"))
    source = [w for w in descendants(d) if isinstance(w,ttk.Entry)][-1]
    _remplir(source,"Employeur1 et Employeur2 : originaux revérifiés")
    assert not d.getvar(c.cget("variable"))
    c.invoke()
    bouton(d,"Valider et appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    bouton(resultat,"Exporter le rapport fiscal en PDF").invoke()
    assert application.messages_test[-1][0] == "Estimation périmée"
    bouton(fiscal,"Enregistrer dossier").invoke()
    assert not application.erreurs_test, application.messages_test


def test_gui_multi_nouveau_dossier_et_effacement(application):
    fiscal = ouvrir(application)
    client = next(w for w in descendants(fiscal) if type(w) is ttk.Entry)
    _remplir(client,"Autre dossier fictif")
    bouton(fiscal,"Initialiser le dossier fiscal").invoke()
    bouton(fiscal,"Cotisations excédentaires 2025").invoke()
    d = derniere_fenetre(fiscal)
    assert not d.getvar(confirmation(d).cget("variable"))
    confirmation(d).invoke()
    bouton(d,"Effacer").invoke()
    assert not d.getvar(confirmation(d).cget("variable"))
