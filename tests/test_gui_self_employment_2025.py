import tkinter as tk
from tkinter import ttk
from dataclasses import replace

from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre, descendants
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from tests.test_gui_caregiver_child_combination_2025 import cocher
from tests.test_tax_self_employment_2025 import dossier
from src.comptaprivee.tax_self_employment_2025 import CONFIRMATIONS_7B
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal

TITRE="Entreprises 2025 / préparation (7B)"


def ouvrir(application):
    sauvegarder_dossier_fiscal(dossier())
    application.ouvrir_agent_fiscal()
    fiscal=derniere_fenetre(application)
    bouton(fiscal,"Dossiers enregistrés").invoke()
    bouton(derniere_fenetre(fiscal),"Ouvrir le dossier").invoke()
    assert application.dossier_fiscal_valide_courant.entreprises
    return fiscal


def test_gui_trace_pdf_perime_reset(application,monkeypatch,tmp_path):
    from src.comptaprivee import gui
    fiscal=ouvrir(application)
    bouton(fiscal,"Calculer l'estimation fiscale 2025").invoke()
    resultat=derniere_fenetre(fiscal)
    texte=next(w for w in descendants(resultat) if isinstance(w,tk.Text)).get("1.0","end")
    assert "estimation finale bloquée" in texte and "9400.00" in texte
    pdf=tmp_path/'7b.pdf'
    monkeypatch.setattr(gui.filedialog,"asksaveasfilename",lambda **kw:str(pdf))
    bouton(resultat,"Exporter la préparation PDF").invoke()
    assert pdf.exists(),application.messages_test
    bouton(fiscal,TITRE).invoke()
    d=derniere_fenetre(fiscal)
    liste=champ(d,'liste_7b');liste.selection_set(0);liste.event_generate('<<ListboxSelect>>')
    application.update()
    _remplir(champ(d,'revenu_brut_7b'),'12000')
    for nom in CONFIRMATIONS_7B:
        assert not d.getvar(champ(d,nom+'_7b').cget('variable'))
        cocher(champ(d,nom+'_7b'))
    bouton(d,'Ajouter / remplacer').invoke()
    bouton(d,'Appliquer au dossier').invoke()
    assert not d.winfo_exists(),application.messages_test
    bouton(resultat,"Exporter la préparation PDF").invoke()
    assert application.messages_test[-1][0]=='Préparation périmée'
    bouton(fiscal,'Enregistrer dossier').invoke()
    assert not application.erreurs_test
    client=next(w for w in descendants(fiscal) if type(w) is ttk.Entry)
    _remplir(client,'Nouveau fictif')
    bouton(fiscal,'Initialiser le dossier fiscal').invoke()
    bouton(fiscal,TITRE).invoke()
    assert champ(derniere_fenetre(fiscal),'liste_7b').size()==0


def test_gui_creation_pure_sauvegarde_recharge(application):
    application.ouvrir_agent_fiscal();fiscal=derniere_fenetre(application)
    client=next(w for w in descendants(fiscal) if type(w) is ttk.Entry)
    _remplir(client,'Autonome fictif')
    bouton(fiscal,'Initialiser le dossier fiscal').invoke()
    bouton(fiscal,TITRE).invoke();d=derniere_fenetre(fiscal)
    for nom,valeur in [('reference','Conseil fictif'),('source','Journal fictif'),('revenu_brut','5000')]:
        _remplir(champ(d,nom+'_7b'),valeur)
    for nom in CONFIRMATIONS_7B: cocher(champ(d,nom+'_7b'))
    bouton(d,'Ajouter / remplacer').invoke();bouton(d,'Appliquer au dossier').invoke()
    assert not d.winfo_exists(),application.messages_test
    assert application.dossier_fiscal_valide_courant.entreprises[0].reference=='Conseil fictif'
    bouton(fiscal,'Enregistrer dossier').invoke()
    fiscal.destroy();application.ouvrir_agent_fiscal();fiscal=derniere_fenetre(application)
    bouton(fiscal,'Dossiers enregistrés').invoke()
    bouton(derniere_fenetre(fiscal),'Ouvrir le dossier').invoke()
    bouton(fiscal,TITRE).invoke();d=derniere_fenetre(fiscal)
    assert champ(d,'liste_7b').size()==1
    liste=champ(d,'liste_7b');liste.selection_set(0);liste.event_generate('<<ListboxSelect>>')
    application.update()
    bouton(d,'Supprimer').invoke();bouton(d,'Appliquer au dossier').invoke()
    assert application.dossier_fiscal_valide_courant.entreprises==()
