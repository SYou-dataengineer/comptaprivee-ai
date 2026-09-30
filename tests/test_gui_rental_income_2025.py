import tkinter as tk
from tkinter import ttk

from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre, descendants
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from tests.test_gui_caregiver_child_combination_2025 import cocher
from src.comptaprivee.tax_rental_income_2025 import CONFIRMATIONS_7D
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal
from tests.test_tax_rental_income_2025 import dossier_location

TITRE = 'Location résidentielle 2025 (7D)'


def ouvrir(application):
    sauvegarder_dossier_fiscal(dossier_location())
    application.ouvrir_agent_fiscal(); fiscal=derniere_fenetre(application)
    bouton(fiscal,'Dossiers enregistrés').invoke()
    bouton(derniere_fenetre(fiscal),'Ouvrir le dossier').invoke()
    assert application.dossier_fiscal_valide_courant.biens_locatifs
    return fiscal


def test_gui_annuel_pdf_perime_recharge_reset(application,monkeypatch,tmp_path):
    from src.comptaprivee import gui
    fiscal=ouvrir(application)
    bouton(fiscal,"Calculer l'estimation fiscale 2025").invoke()
    resultat=derniere_fenetre(fiscal)
    texte=next(w for w in descendants(resultat) if isinstance(w,tk.Text)).get('1.0','end')
    assert '12600' in texte and '24000.00' in texte and '58.70' in texte
    pdf=tmp_path/'location.pdf'
    monkeypatch.setattr(gui.filedialog,'asksaveasfilename',lambda **kw:str(pdf))
    bouton(resultat,'Exporter le rapport fiscal en PDF').invoke()
    assert pdf.exists(),application.messages_test
    bouton(fiscal,TITRE).invoke(); d=derniere_fenetre(fiscal)
    _remplir(champ(d,'assurance_7d'),'1000')
    for nom in CONFIRMATIONS_7D:
        assert not d.getvar(champ(d,nom+'_7d').cget('variable'))
        cocher(champ(d,nom+'_7d'))
    bouton(d,'Appliquer').invoke()
    assert not d.winfo_exists(),application.messages_test
    bouton(resultat,'Exporter le rapport fiscal en PDF').invoke()
    assert application.messages_test[-1][0]=='Estimation périmée'
    bouton(fiscal,'Enregistrer dossier').invoke()
    fiscal.destroy();application.ouvrir_agent_fiscal();fiscal=derniere_fenetre(application)
    bouton(fiscal,'Dossiers enregistrés').invoke()
    bouton(derniere_fenetre(fiscal),'Ouvrir le dossier').invoke()
    assert application.dossier_fiscal_valide_courant.biens_locatifs[0].assurance==1000
    client=next(w for w in descendants(fiscal) if type(w) is ttk.Entry)
    _remplir(client,'Nouveau dossier fictif');bouton(fiscal,'Initialiser le dossier fiscal').invoke()
    assert application.dossier_fiscal_valide_courant is None
    bouton(fiscal,TITRE).invoke();d=derniere_fenetre(fiscal)
    assert champ(d,'reference_7d').get()==''
    assert champ(d,'loyers_7d').get()=='0'


def test_gui_creation_refus_dpa_et_suppression(application):
    application.ouvrir_agent_fiscal();fiscal=derniere_fenetre(application)
    client=next(w for w in descendants(fiscal) if type(w) is ttk.Entry)
    _remplir(client,'Location fictive');bouton(fiscal,'Initialiser le dossier fiscal').invoke()
    bouton(fiscal,TITRE).invoke();d=derniere_fenetre(fiscal)
    for n,v in [('reference','Bien fictif'),('adresse','10 rue Fictive, Québec'),('source','Bail fictif'),('loyers','10000')]:
        _remplir(champ(d,n+'_7d'),v)
    cocher(champ(d,'dpa_7d'))
    for n in CONFIRMATIONS_7D: cocher(champ(d,n+'_7d'))
    bouton(d,'Appliquer').invoke()
    assert d.winfo_exists() and 'DPA' in application.messages_test[-1][1]
    champ(d,'dpa_7d').invoke()
    for n in CONFIRMATIONS_7D: cocher(champ(d,n+'_7d'))
    bouton(d,'Appliquer').invoke()
    assert not d.winfo_exists(),application.messages_test
    assert application.dossier_fiscal_valide_courant.biens_locatifs[0].loyers==10000
    bouton(fiscal,TITRE).invoke();d=derniere_fenetre(fiscal)
    bouton(d,'Supprimer le bien').invoke()
    assert application.dossier_fiscal_valide_courant.biens_locatifs==()
