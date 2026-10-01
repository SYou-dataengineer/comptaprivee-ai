import tkinter as tk
from tkinter import ttk
from dataclasses import replace
from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre, descendants, ouvrir_dossier_test
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir, _cocher

TITRE = 'Préparation IMR 2025 (7I)'


def saisir(fiscal):
    bouton(fiscal,TITRE).invoke();d=derniere_fenetre(fiscal)
    _remplir(champ(d,'source_7i'),'Audit IMR fictif')
    champ(d,'soldes_federaux_7i').insert('1.0','2024 | 123.45 | Avis ARC fictif')
    champ(d,'soldes_quebec_7i').insert('1.0','2023 | 67.89 | Avis RQ fictif')
    d.update()
    _cocher(d,'residence_quebec_annee_7i');_cocher(d,'confirme_7i')
    return d


def test_gui_trace_pdf_sauvegarde_recharge_reset(application,monkeypatch,tmp_path):
    from src.comptaprivee import gui_minimum_preparation_2025 as m
    fiscal=ouvrir_dossier_test(application);d=saisir(fiscal)
    bouton(d,'Vérifier et afficher la trace').invoke()
    texte=champ(d,'trace_7i').get('1.0','end')
    assert 'T691 requis : oui' in texte and 'TP-776.42 requis : oui' in texte,application.messages_test
    pdf=tmp_path/'imr_fictif.pdf'
    monkeypatch.setattr(m.filedialog,'asksaveasfilename',lambda **kw:str(pdf))
    bouton(d,'Exporter la préparation PDF').invoke();assert pdf.exists(),application.messages_test
    bouton(d,'Appliquer les faits').invoke();assert not d.winfo_exists(),application.messages_test
    p=application.dossier_fiscal_valide_courant.imr
    assert str(p.soldes_federaux[0].montant_confirme)=='123.45'
    bouton(fiscal,"Calculer l'estimation fiscale 2025").invoke()
    assert application.messages_test[-1][0]=='Calcul annuel suspendu - 7I'
    bouton(fiscal,'Enregistrer dossier').invoke();fiscal.destroy()
    application.ouvrir_agent_fiscal();fiscal=derniere_fenetre(application)
    bouton(fiscal,'Dossiers enregistrés').invoke();bouton(derniere_fenetre(fiscal),'Ouvrir le dossier').invoke()
    assert application.dossier_fiscal_valide_courant.imr==p
    bouton(fiscal,TITRE).invoke();d=derniere_fenetre(fiscal)
    assert 'Avis ARC fictif' in champ(d,'soldes_federaux_7i').get('1.0','end')
    bouton(d,'Fermer').invoke()
    client=next(w for w in descendants(fiscal) if type(w) is ttk.Entry)
    _remplir(client,'Nouveau fictif');bouton(fiscal,'Initialiser le dossier fiscal').invoke()
    assert application.dossier_fiscal_valide_courant is None
    bouton(fiscal,TITRE).invoke();assert application.messages_test[-1][0]=='Profil IMR indisponible'


def test_gui_estimation_perimee(application):
    fiscal=ouvrir_dossier_test(application)
    bouton(fiscal,"Calculer l'estimation fiscale 2025").invoke();ancien=derniere_fenetre(fiscal)
    d=saisir(fiscal);bouton(d,'Appliquer les faits').invoke()
    bouton(ancien,'Exporter le rapport fiscal en PDF').invoke()
    assert application.messages_test[-1][0]=='Estimation périmée'


def test_gui_modification_revoque_confirmation(application):
    fiscal=ouvrir_dossier_test(application);d=saisir(fiscal)
    champ(d,'elements_7i').insert('1.0','gain_capital | 1.00 | Fictif');d.update()
    assert not d.getvar(champ(d,'confirme_7i').cget('variable'))
    bouton(d,'Appliquer les faits').invoke()
    assert d.winfo_exists() and application.dossier_fiscal_valide_courant.imr is None
    assert 'exhaustivité' in application.messages_test[-1][1]


def test_gui_fenetre_perimee(application,monkeypatch,tmp_path):
    from src.comptaprivee import gui_minimum_preparation_2025 as m
    fiscal=ouvrir_dossier_test(application);d=saisir(fiscal)
    application.dossier_fiscal_valide_courant=replace(application.dossier_fiscal_valide_courant,client='Autre fictif')
    pdf=tmp_path/'interdit.pdf';monkeypatch.setattr(m.filedialog,'asksaveasfilename',lambda **kw:str(pdf))
    bouton(d,'Exporter la préparation PDF').invoke()
    assert not pdf.exists() and 'Dossier modifié' in application.messages_test[-1][1]
