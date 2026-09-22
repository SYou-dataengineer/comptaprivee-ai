"""Formulaire 3F : confirmations, calcul, JSON et PDF périmés."""
import tkinter as tk
from dataclasses import replace
import pytest
from src.comptaprivee import gui, tax_case_storage
from src.comptaprivee.gui_layout import FormulaireDefilant
from tests.test_gui_block2 import application, racine, bouton, descendants, derniere_fenetre
from tests.test_gui_pension_income_2025 import champ
from tests.test_tax_capital_loss_carryovers_2025 import dossier_capital, profil_capital, profil_pertes, CHAMPS_REPORTS_PERTES


def ouvrir(app,confirme=True):
    tax_case_storage.sauvegarder_dossier_fiscal(dossier_capital(),profil_capital=profil_capital(),
        profil_reports_pertes=replace(profil_pertes(),confirme=confirme))
    app.ouvrir_agent_fiscal();fiscal=derniere_fenetre(app)
    bouton(fiscal,'Dossiers enregistrés').invoke();bouton(derniere_fenetre(fiscal),'Ouvrir le dossier').invoke()
    bouton(fiscal,'Reports de pertes en capital 2025 (3F)').invoke()
    return fiscal,derniere_fenetre(fiscal)


@pytest.mark.parametrize('echelle',[96/72,144/72,192/72])
def test_actions_visibles(application,echelle):
    app=application;app.tk.call('tk','scaling',echelle)
    _,dialogue=ouvrir(app)
    for taille in ('600x400','1000x700'):
        dialogue.geometry(taille);app.update()
        form=next(w for w in dialogue.winfo_children() if isinstance(w,FormulaireDefilant))
        for action in form.actions.winfo_children():
            assert action.winfo_ismapped() and action.winfo_width()>=action.winfo_reqwidth()
            assert action.winfo_rooty()+action.winfo_height()<=dialogue.winfo_rooty()+dialogue.winfo_height()
        form.canvas.yview_moveto(1);app.update();assert form.canvas.yview()[1]==pytest.approx(1)


@pytest.mark.parametrize('nom',[n for n,_ in CHAMPS_REPORTS_PERTES])
def test_champs_revoquent_confirmations(application,nom):
    _,dialogue=ouvrir(application)
    champ(dialogue,nom+'_reports_pertes').insert(0,'9')
    for nom_check in ('confirmation_historique_pertes','confirmation_reports_pertes'):
        check=champ(dialogue,nom_check);assert dialogue.getvar(check.cget('variable'))==0
    bouton(dialogue,'Valider et appliquer').invoke();assert dialogue.winfo_exists()


def test_calcul_sauvegarde_pdf_invalidation_rechargement(application,monkeypatch,tmp_path):
    app=application;fiscal,dialogue=ouvrir(app,False)
    bouton(dialogue,'Valider et appliquer').invoke();assert dialogue.winfo_exists()
    champ(dialogue,'confirmation_reports_pertes').invoke();bouton(dialogue,'Valider et appliquer').invoke()
    assert not dialogue.winfo_exists(),app.messages_test
    bouton(fiscal,"Calculer l'estimation fiscale 2025").invoke();ancien=derniere_fenetre(fiscal)
    texte=next(w for w in descendants(ancien) if isinstance(w,tk.Text)).get('1.0','end')
    assert 'REPORTS DE PERTES' in texte and '1 200,00' in texte and '2018' in texte
    pdf=tmp_path/'ancien.pdf';monkeypatch.setattr(gui.filedialog,'asksaveasfilename',lambda **kw:str(pdf))
    bouton(ancien,'Exporter le rapport fiscal en PDF').invoke();assert pdf.exists()
    app.callbacks_test['sauvegarder_dossier_fiscal_local']()
    chemin=next((tmp_path/'dossiers').glob('*.json'))
    assert tax_case_storage.charger_dossier_fiscal(chemin).profil_reports_pertes.confirme
    bouton(fiscal,'Reports de pertes en capital 2025 (3F)').invoke();dialogue=derniere_fenetre(fiscal)
    entree=champ(dialogue,'demande_federale_reports_pertes');entree.delete(0,'end');entree.insert(0,'500')
    champ(dialogue,'confirmation_historique_pertes').invoke();champ(dialogue,'confirmation_reports_pertes').invoke()
    bouton(dialogue,'Valider et appliquer').invoke();assert not dialogue.winfo_exists(),app.messages_test
    bouton(ancien,'Exporter le rapport fiscal en PDF').invoke();assert app.messages_test[-1][0]=='Estimation périmée'
    app.callbacks_test['sauvegarder_dossier_fiscal_local']();charge=tax_case_storage.charger_dossier_fiscal(chemin)
    assert charge.rapport_pdf is None and charge.profil_reports_pertes.demande_federale=='500'
    bouton(fiscal,"Recalculer l'estimation fiscale 2025").invoke();nouveau=derniere_fenetre(fiscal)
    texte=next(w for w in descendants(nouveau) if isinstance(w,tk.Text)).get('1.0','end')
    assert '720,00' in texte
    fiscal.destroy();app.ouvrir_agent_fiscal();fiscal=derniere_fenetre(app)
    bouton(fiscal,'Dossiers enregistrés').invoke();bouton(derniere_fenetre(fiscal),'Ouvrir le dossier').invoke()
    bouton(fiscal,'Reports de pertes en capital 2025 (3F)').invoke();dialogue=derniere_fenetre(fiscal)
    assert champ(dialogue,'demande_federale_reports_pertes').get()=='500'


def test_dossier_perime(application):
    app=application;_,dialogue=ouvrir(app)
    app.dossier_fiscal_valide_courant=replace(app.dossier_fiscal_valide_courant,client='Autre dossier synthétique')
    bouton(dialogue,'Valider et appliquer').invoke()
    assert dialogue.winfo_exists() and 'changé' in app.messages_test[-1][1]


def test_reextraction_revoque_pertes(application):
    app=application;fiscal,dialogue=ouvrir(app);bouton(dialogue,'Fermer').invoke()
    app.callbacks_test['extraire_cases_documents_fiscaux']()
    bouton(fiscal,'Reports de pertes en capital 2025 (3F)').invoke();dialogue=derniere_fenetre(fiscal)
    assert dialogue.getvar(champ(dialogue,'confirmation_reports_pertes').cget('variable'))==0


def test_confirmation_historique_revoque_confirmation_generale(application):
    _,dialogue=ouvrir(application)
    champ(dialogue,'confirmation_historique_pertes').invoke()
    assert dialogue.getvar(champ(dialogue,'confirmation_reports_pertes').cget('variable'))==0
    bouton(dialogue,'Valider et appliquer').invoke();assert dialogue.winfo_exists()


def test_modification_vente_revoque_reports(application):
    app=application;fiscal,dialogue=ouvrir(app);bouton(dialogue,'Fermer').invoke()
    bouton(fiscal,'Gains et pertes en capital 2025').invoke();capital=derniere_fenetre(fiscal)
    entree=champ(capital,'pbr_capital');entree.delete(0,'end');entree.insert(0,'4001')
    champ(capital,'confirmation_pbr_capital').invoke();champ(capital,'confirmation_capital').invoke()
    bouton(capital,'Valider et appliquer').invoke();assert not capital.winfo_exists()
    bouton(fiscal,'Reports de pertes en capital 2025 (3F)').invoke();dialogue=derniere_fenetre(fiscal)
    assert dialogue.getvar(champ(dialogue,'confirmation_reports_pertes').cget('variable'))==0
