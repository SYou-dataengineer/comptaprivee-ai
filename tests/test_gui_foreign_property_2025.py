from tkinter import ttk
from dataclasses import replace
import pytest
from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre, descendants, ouvrir_dossier_test
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir, _cocher

TITRE='Biens étrangers 2025 (7J)'


def saisir(fiscal,montant='250000'):
    bouton(fiscal,TITRE).invoke();d=derniere_fenetre(fiscal)
    _remplir(champ(d,'source_7j'),'Contrôle étranger fictif')
    champ(d,'biens_7j').insert('1.0',f'Compte fictif | compte | USA | {montant} | {montant} | 0 | 300 | 0 | Relevé fictif')
    champ(d,'couts_7j').insert('1.0',f'Compte fictif | 2025-01-01T00:00:00 | {montant}\nCompte fictif | 2025-06-01T12:00:00 | 0\nCompte fictif | 2025-12-31T23:59:59 | 0')
    d.update()
    for n in ('particulier_quebec','chronologie_complete','confirme'):_cocher(d,n+'_7j')
    return d


def test_gui_trace_pdf_sauvegarde_recharge_reset(application,monkeypatch,tmp_path):
    from src.comptaprivee import gui_foreign_property_2025 as m
    fiscal=ouvrir_dossier_test(application);d=saisir(fiscal)
    bouton(d,'Vérifier et afficher la trace').invoke()
    texte=champ(d,'trace_7j').get('1.0','end')
    assert 'T1135 requis : oui' in texte and 'partie B requise' in texte,application.messages_test
    pdf=tmp_path/'etranger_fictif.pdf';monkeypatch.setattr(m.filedialog,'asksaveasfilename',lambda **kw:str(pdf))
    bouton(d,'Exporter la préparation PDF').invoke();assert pdf.exists(),application.messages_test
    bouton(d,'Appliquer les faits').invoke();assert not d.winfo_exists(),application.messages_test
    p=application.dossier_fiscal_valide_courant.biens_etrangers
    assert p.biens[0].cout_fin==0
    bouton(fiscal,'Enregistrer dossier').invoke();fiscal.destroy()
    application.ouvrir_agent_fiscal();fiscal=derniere_fenetre(application)
    bouton(fiscal,'Dossiers enregistrés').invoke();bouton(derniere_fenetre(fiscal),'Ouvrir le dossier').invoke()
    assert application.dossier_fiscal_valide_courant.biens_etrangers==p
    bouton(fiscal,TITRE).invoke();d=derniere_fenetre(fiscal)
    assert 'Relevé fictif' in champ(d,'biens_7j').get('1.0','end')
    bouton(d,'Fermer').invoke()
    client=next(w for w in descendants(fiscal) if type(w) is ttk.Entry)
    _remplir(client,'Nouveau fictif');bouton(fiscal,'Initialiser le dossier fiscal').invoke()
    assert application.dossier_fiscal_valide_courant is None


def test_gui_estimation_perimee(application):
    fiscal=ouvrir_dossier_test(application)
    bouton(fiscal,"Calculer l'estimation fiscale 2025").invoke();ancien=derniere_fenetre(fiscal)
    d=saisir(fiscal);bouton(d,'Appliquer les faits').invoke()
    bouton(ancien,'Exporter le rapport fiscal en PDF').invoke()
    assert application.messages_test[-1][0]=='Estimation périmée'


def test_gui_modification_revoque_confirmation(application):
    fiscal=ouvrir_dossier_test(application);d=saisir(fiscal)
    champ(d,'biens_7j').insert('end',' ');d.update()
    assert not d.getvar(champ(d,'confirme_7j').cget('variable'))
    bouton(d,'Appliquer les faits').invoke()
    assert d.winfo_exists() and application.dossier_fiscal_valide_courant.biens_etrangers is None


def test_gui_fenetre_perimee(application,monkeypatch,tmp_path):
    from src.comptaprivee import gui_foreign_property_2025 as m
    fiscal=ouvrir_dossier_test(application);d=saisir(fiscal)
    application.dossier_fiscal_valide_courant=replace(application.dossier_fiscal_valide_courant,client='Autre fictif')
    pdf=tmp_path/'interdit.pdf';monkeypatch.setattr(m.filedialog,'asksaveasfilename',lambda **kw:str(pdf))
    bouton(d,'Exporter la préparation PDF').invoke()
    assert not pdf.exists() and 'Dossier modifié' in application.messages_test[-1][1]


@pytest.mark.parametrize('montant',['99999.99','250000'])
def test_gui_arrivee_preparation_sans_blocage_du_dossier(application,monkeypatch,tmp_path,montant):
    from src.comptaprivee import gui_foreign_property_2025 as m
    from src.comptaprivee.tax_foreign_property_2025 import AVERTISSEMENT_ARRIVEE
    fiscal=ouvrir_dossier_test(application);d=saisir(fiscal,montant)
    _cocher(d,'premiere_residence_2025_7j');_cocher(d,'confirme_7j')
    bouton(d,'Vérifier et afficher la trace').invoke()
    texte=champ(d,'trace_7j').get('1.0','end')
    assert AVERTISSEMENT_ARRIVEE in texte,application.messages_test
    assert 'Ligne 25 Québec : à valider manuellement' in texte
    assert 'TP-1079.8.BE requis : non' in texte
    pdf=tmp_path/'arrivee.pdf';monkeypatch.setattr(m.filedialog,'asksaveasfilename',lambda **kw:str(pdf))
    bouton(d,'Exporter la préparation PDF').invoke();assert pdf.exists()
    bouton(d,'Appliquer les faits').invoke();assert not d.winfo_exists(),application.messages_test
    p=application.dossier_fiscal_valide_courant.biens_etrangers
    assert p.premiere_residence_2025
    bouton(fiscal,'Enregistrer dossier').invoke();fiscal.destroy()
    application.ouvrir_agent_fiscal();fiscal=derniere_fenetre(application)
    bouton(fiscal,'Dossiers enregistrés').invoke();bouton(derniere_fenetre(fiscal),'Ouvrir le dossier').invoke()
    assert application.dossier_fiscal_valide_courant.biens_etrangers==p
    bouton(fiscal,"Calculer l'estimation fiscale 2025").invoke()
    assert 'résidence partielle' in application.messages_test[-1][1]
