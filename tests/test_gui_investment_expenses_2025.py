"""Formulaire réel 3E : extraction locale, confirmations, PDF et persistance."""
import tkinter as tk
from dataclasses import replace
import pytest
from src.comptaprivee import gui, gui_investment_expenses_2025 as formulaire_frais, tax_case_storage
from src.comptaprivee.gui_layout import FormulaireDefilant
from tests.test_gui_block2 import application, racine, bouton, descendants, derniere_fenetre
from tests.test_gui_pension_income_2025 import champ
from tests.test_tax_investment_expenses_2025 import dossier_interets, profil_interets, profil_frais, CHAMPS_FRAIS_PLACEMENT


def ouvrir(app, confirme=True):
    tax_case_storage.sauvegarder_dossier_fiscal(dossier_interets(), profil_interets=profil_interets(),
        profil_frais_placement=replace(profil_frais(),confirme=confirme))
    app.ouvrir_agent_fiscal();fiscal=derniere_fenetre(app)
    bouton(fiscal,'Dossiers enregistrés').invoke();bouton(derniere_fenetre(fiscal),'Ouvrir le dossier').invoke()
    bouton(fiscal,'Frais de placement 2025 (3E)').invoke()
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


@pytest.mark.parametrize('nom',[n for n,_ in CHAMPS_FRAIS_PLACEMENT])
def test_tous_champs_revoquent_confirmations(application,nom):
    app=application;_,dialogue=ouvrir(app)
    champ(dialogue,nom+'_frais_placement').insert(0,'9')
    for nom_check in ('confirmation_report_frais','confirmation_frais_placement'):
        check=champ(dialogue,nom_check);assert dialogue.getvar(check.cget('variable'))==0
    bouton(dialogue,'Valider et appliquer').invoke();assert dialogue.winfo_exists()


def test_calcul_sauvegarde_pdf_invalidation_rechargement(application,monkeypatch,tmp_path):
    app=application;fiscal,dialogue=ouvrir(app,False)
    bouton(dialogue,'Valider et appliquer').invoke();assert dialogue.winfo_exists()
    champ(dialogue,'confirmation_frais_placement').invoke();bouton(dialogue,'Valider et appliquer').invoke()
    assert not dialogue.winfo_exists(),app.messages_test
    bouton(fiscal,"Calculer l'estimation fiscale 2025").invoke();ancien=derniere_fenetre(fiscal)
    texte=next(w for w in descendants(ancien) if isinstance(w,tk.Text)).get('1.0','end')
    assert 'FRAIS DE PLACEMENT' in texte and '18 500,00' in texte and '3,70' in texte
    pdf=tmp_path/'ancien.pdf';monkeypatch.setattr(gui.filedialog,'asksaveasfilename',lambda **kw:str(pdf))
    bouton(ancien,'Exporter le rapport fiscal en PDF').invoke();assert pdf.exists()
    app.callbacks_test['sauvegarder_dossier_fiscal_local']()
    chemin=next((tmp_path/'dossiers').glob('*.json'))
    assert tax_case_storage.charger_dossier_fiscal(chemin).profil_frais_placement.confirme
    bouton(fiscal,'Frais de placement 2025 (3E)').invoke();dialogue=derniere_fenetre(fiscal)
    entree=champ(dialogue,'gestion_frais_placement');entree.delete(0,'end');entree.insert(0,'1000')
    champ(dialogue,'confirmation_report_frais').invoke();champ(dialogue,'confirmation_frais_placement').invoke()
    bouton(dialogue,'Valider et appliquer').invoke();assert not dialogue.winfo_exists(),app.messages_test
    bouton(ancien,'Exporter le rapport fiscal en PDF').invoke();assert app.messages_test[-1][0]=='Estimation périmée'
    app.callbacks_test['sauvegarder_dossier_fiscal_local']();charge=tax_case_storage.charger_dossier_fiscal(chemin)
    assert charge.rapport_pdf is None and charge.profil_frais_placement.gestion=='1000'
    bouton(fiscal,"Recalculer l'estimation fiscale 2025").invoke();nouveau=derniere_fenetre(fiscal)
    texte=next(w for w in descendants(nouveau) if isinstance(w,tk.Text)).get('1.0','end')
    assert '18 000,00' in texte
    fiscal.destroy();app.ouvrir_agent_fiscal();fiscal=derniere_fenetre(app)
    bouton(fiscal,'Dossiers enregistrés').invoke();bouton(derniere_fenetre(fiscal),'Ouvrir le dossier').invoke()
    bouton(fiscal,'Frais de placement 2025 (3E)').invoke();dialogue=derniere_fenetre(fiscal)
    assert champ(dialogue,'gestion_frais_placement').get()=='1000'


def test_import_remplace_sans_cumul_et_revoque(application,monkeypatch):
    _,dialogue=ouvrir(application)
    monkeypatch.setattr(formulaire_frais.filedialog,'askopenfilename',lambda **kw:'frais-synthetiques.pdf')
    # La fonction d'extraction est capturée à l'ouverture : patch avant une nouvelle ouverture.
    fiscal=dialogue.master;bouton(dialogue,'Fermer').invoke()
    monkeypatch.setattr(gui,'extraire_texte_document',lambda p:'2025\nFrais de gestion : 234.56 CAD')
    bouton(fiscal,'Frais de placement 2025 (3E)').invoke();dialogue=derniere_fenetre(fiscal)
    for _ in range(2):bouton(dialogue,'Importer une pièce').invoke()
    assert champ(dialogue,'gestion_frais_placement').get()=='234.56'
    assert champ(dialogue,'interets_frais_placement').get()=='0'
    assert dialogue.getvar(champ(dialogue,'confirmation_frais_placement').cget('variable'))==0


def test_dossier_perime(application):
    app=application;_,dialogue=ouvrir(app)
    app.dossier_fiscal_valide_courant=replace(app.dossier_fiscal_valide_courant,client='Autre client synthétique')
    bouton(dialogue,'Valider et appliquer').invoke()
    assert dialogue.winfo_exists() and 'changé' in app.messages_test[-1][1]


def test_modification_placement_revoque_frais(application):
    app=application;fiscal,dialogue=ouvrir(app);bouton(dialogue,'Fermer').invoke()
    app.callbacks_test['extraire_cases_documents_fiscaux']()
    bouton(fiscal,'Frais de placement 2025 (3E)').invoke();dialogue=derniere_fenetre(fiscal)
    assert dialogue.getvar(champ(dialogue,'confirmation_frais_placement').cget('variable'))==0


def test_report_non_confirme_revoque_confirmation_generale(application):
    _,dialogue=ouvrir(application)
    champ(dialogue,'confirmation_report_frais').invoke()
    assert dialogue.getvar(champ(dialogue,'confirmation_frais_placement').cget('variable'))==0
    bouton(dialogue,'Valider et appliquer').invoke();assert dialogue.winfo_exists()
