import tkinter as tk
from tkinter import ttk
from dataclasses import replace
from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre, descendants, ouvrir_dossier_test
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir, _cocher
from src.comptaprivee.tax_final_return_2025 import CONFIRMATIONS_7H

TITRE='Déclaration finale 2025 (7H)'


def saisir(fiscal,jour='2025-12-15'):
    bouton(fiscal,TITRE).invoke();d=derniere_fenetre(fiscal)
    for n,v in (('date_deces',jour),('reference_representant','REF-FICTIVE'),('source','Preuve fictive 2025')):
        _remplir(champ(d,n+'_7h'),v)
    for n in (*CONFIRMATIONS_7H,'rrq_standard_18_64'):_cocher(d,n+'_7h')
    return d


def test_gui_estimation_trace_pdf_recharge_reset(application,monkeypatch,tmp_path):
    from src.comptaprivee import gui_final_return_2025 as module
    fiscal=ouvrir_dossier_test(application);d=saisir(fiscal)
    bouton(d,'Vérifier et afficher la trace').invoke()
    assert '2026-06-15' in champ(d,'trace_7h').get('1.0','end')
    pdf=tmp_path/'preparation_deces_fictive.pdf'
    monkeypatch.setattr(module.filedialog,'asksaveasfilename',lambda **kw:str(pdf))
    bouton(d,'Exporter la préparation PDF').invoke();assert pdf.exists(),application.messages_test
    bouton(d,'Appliquer les faits').invoke();assert not d.winfo_exists(),application.messages_test
    assert application.dossier_fiscal_valide_courant.deces.date_deces=='2025-12-15'
    bouton(fiscal,"Calculer l'estimation fiscale 2025").invoke();resultat=derniere_fenetre(fiscal)
    texte=next(w for w in descendants(resultat) if isinstance(w,tk.Text)).get('1.0','end')
    assert 'DÉCLARATION FINALE' in texte and 'Impôt minimum 2025 : non appliqué' in texte
    bouton(fiscal,'Enregistrer dossier').invoke();fiscal.destroy()
    application.ouvrir_agent_fiscal();fiscal=derniere_fenetre(application)
    bouton(fiscal,'Dossiers enregistrés').invoke();bouton(derniere_fenetre(fiscal),'Ouvrir le dossier').invoke()
    bouton(fiscal,TITRE).invoke();d=derniere_fenetre(fiscal)
    assert champ(d,'date_deces_7h').get()=='2025-12-15'
    bouton(d,'Fermer').invoke()
    client=next(w for w in descendants(fiscal) if type(w) is ttk.Entry)
    _remplir(client,'Nouveau fictif');bouton(fiscal,'Initialiser le dossier fiscal').invoke()
    assert application.dossier_fiscal_valide_courant is None
    bouton(fiscal,TITRE).invoke();assert application.messages_test[-1][0]=='Profil décès indisponible'


def test_gui_blocage_rrq_et_invalidation_ancien_pdf(application):
    fiscal=ouvrir_dossier_test(application)
    bouton(fiscal,"Calculer l'estimation fiscale 2025").invoke();ancien=derniere_fenetre(fiscal)
    d=saisir(fiscal,'2025-01-15');bouton(d,'Vérifier et afficher la trace').invoke()
    assert 'CALCUL ANNUEL SUSPENDU' in champ(d,'trace_7h').get('1.0','end')
    bouton(d,'Appliquer les faits').invoke()
    bouton(ancien,'Exporter le rapport fiscal en PDF').invoke()
    assert application.messages_test[-1][0]=='Estimation périmée'
    bouton(fiscal,"Recalculer l'estimation fiscale 2025").invoke()
    assert application.messages_test[-1][0]=='Calcul annuel suspendu - 7H'
    assert 'ligne 452 requis' in application.messages_test[-1][1]


def test_gui_modification_revoque_et_refuse_post_deces(application):
    fiscal=ouvrir_dossier_test(application);d=saisir(fiscal)
    _remplir(champ(d,'date_deces_7h'),'2025-12-20')
    assert all(not d.getvar(champ(d,n+'_7h').cget('variable')) for n in CONFIRMATIONS_7H)
    _cocher(d,'revenus_post_deces_7h')
    for n in CONFIRMATIONS_7H:_cocher(d,n+'_7h')
    bouton(d,'Appliquer les faits').invoke()
    assert d.winfo_exists() and 'Déclaration finale complexe' in application.messages_test[-1][1]
    assert application.dossier_fiscal_valide_courant.deces is None


def test_gui_fenetre_perimee(application,monkeypatch,tmp_path):
    from src.comptaprivee import gui_final_return_2025 as module
    fiscal=ouvrir_dossier_test(application);d=saisir(fiscal)
    application.dossier_fiscal_valide_courant=replace(application.dossier_fiscal_valide_courant,client='Autre fictif')
    pdf=tmp_path/'interdit.pdf';monkeypatch.setattr(module.filedialog,'asksaveasfilename',lambda **kw:str(pdf))
    bouton(d,'Exporter la préparation PDF').invoke()
    assert not pdf.exists() and 'Dossier modifié' in application.messages_test[-1][1]
