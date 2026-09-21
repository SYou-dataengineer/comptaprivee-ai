"""Formulaire 3B réel, invalidation et rechargement."""
import tkinter as tk
from dataclasses import replace
import pytest
from src.comptaprivee import gui, tax_case_storage
from src.comptaprivee.gui_layout import FormulaireDefilant
from tests.test_gui_block2 import application, racine, bouton, descendants, derniere_fenetre
from tests.test_gui_pension_income_2025 import champ
from tests.test_tax_documented_interest_2025 import dossier_documente, profil_documente, NATURES_INTERETS_DOCUMENTES


def ouvrir(app,confirme=True,nature='BANQUE'):
    tax_case_storage.sauvegarder_dossier_fiscal(dossier_documente(nature),profil_interets=replace(profil_documente(nature),confirme=confirme))
    app.ouvrir_agent_fiscal();fiscal=derniere_fenetre(app)
    bouton(fiscal,'Dossiers enregistrés').invoke();bouton(derniere_fenetre(fiscal),'Ouvrir le dossier').invoke()
    bouton(fiscal,'Intérêts documentés 2025 (3B)').invoke()
    return fiscal,derniere_fenetre(fiscal)


@pytest.mark.parametrize('echelle',[96/72,144/72,192/72])
def test_actions_visibles(application,echelle):
    app=application;app.tk.call('tk','scaling',echelle)
    fiscal,dialogue=ouvrir(app)
    for taille in ('600x400','1000x700'):
        dialogue.geometry(taille);app.update()
        form=next(w for w in dialogue.winfo_children() if isinstance(w,FormulaireDefilant))
        for action in form.actions.winfo_children():
            assert action.winfo_ismapped() and action.winfo_width()>=action.winfo_reqwidth()
            assert action.winfo_rooty()+action.winfo_height()<=dialogue.winfo_rooty()+dialogue.winfo_height()
        form.canvas.yview_moveto(1);app.update();assert form.canvas.yview()[1]==pytest.approx(1)


@pytest.mark.parametrize('nature',NATURES_INTERETS_DOCUMENTES)
def test_confirmation_export_stockage_invalidation(application,monkeypatch,tmp_path,nature):
    app=application;fiscal,dialogue=ouvrir(app,False,nature)
    bouton(dialogue,'Valider et appliquer').invoke();assert dialogue.winfo_exists()
    champ(dialogue,'confirmation_interets_documentes').invoke();bouton(dialogue,'Valider et appliquer').invoke()
    bouton(fiscal,"Calculer l'estimation fiscale 2025").invoke();resultat=derniere_fenetre(fiscal)
    texte=next(w for w in descendants(resultat) if isinstance(w,tk.Text)).get('1.0','end')
    assert 'INTÉRÊTS DOCUMENTÉS' in texte and '12100' in texte and '446' in texte
    pdf=tmp_path/'rapport.pdf';monkeypatch.setattr(gui.filedialog,'asksaveasfilename',lambda **kw:str(pdf))
    bouton(resultat,'Exporter le rapport fiscal en PDF').invoke();assert pdf.exists()
    app.callbacks_test['sauvegarder_dossier_fiscal_local']()
    chemin=next((tmp_path/'dossiers').glob('*.json'))
    assert tax_case_storage.charger_dossier_fiscal(chemin).profil_interets.confirme
    bouton(fiscal,'Intérêts documentés 2025 (3B)').invoke();dialogue=derniere_fenetre(fiscal)
    champ(dialogue,'source_interets_documentes').insert(0,'Revu : ')
    check=champ(dialogue,'confirmation_interets_documentes');assert dialogue.getvar(check.cget('variable'))==0
    check.invoke();bouton(dialogue,'Valider et appliquer').invoke()
    bouton(resultat,'Exporter le rapport fiscal en PDF').invoke();assert app.messages_test[-1][0]=='Estimation périmée'
    app.callbacks_test['sauvegarder_dossier_fiscal_local']();assert tax_case_storage.charger_dossier_fiscal(chemin).rapport_pdf is None
    fiscal.destroy();app.ouvrir_agent_fiscal();fiscal=derniere_fenetre(app)
    bouton(fiscal,'Dossiers enregistrés').invoke();bouton(derniere_fenetre(fiscal),'Ouvrir le dossier').invoke()
    bouton(fiscal,'Intérêts documentés 2025 (3B)').invoke();dialogue=derniere_fenetre(fiscal)
    assert champ(dialogue,'source_interets_documentes').get().startswith('Revu : ')
    bouton(dialogue,'Fermer').invoke();app.callbacks_test['extraire_cases_documents_fiscaux']()
    bouton(fiscal,'Intérêts documentés 2025 (3B)').invoke();dialogue=derniere_fenetre(fiscal)
    check=champ(dialogue,'confirmation_interets_documentes');assert dialogue.getvar(check.cget('variable'))==0


@pytest.mark.parametrize('vide',[False,True])
def test_import_preparation(application,monkeypatch,vide):
    app=application;fiscal,dialogue=ouvrir(app);bouton(dialogue,'Fermer').invoke()
    d=dossier_documente()
    def texte(p):
        return p.stem if vide else p.stem+'\nIntérêts bancaires 2025 : 20000.00'
    monkeypatch.setattr(gui,'extraire_texte_document',texte)
    app.callbacks_test['reconnaitre_documents_fiscaux']()
    assert 'INTERETS : 1' in app.messages_test[-1][1]
    app.callbacks_test['extraire_cases_documents_fiscaux']();validation=derniere_fenetre(fiscal)
    bouton(validation,'Valider tout').invoke();bouton(validation,'Fermer').invoke()
    app.callbacks_test['preparer_dossier_fiscal_valide']()
    assert (app.dossier_fiscal_valide_courant is None)==vide


def test_formulaire_ancien_dossier_refuse(application):
    app=application;fiscal,dialogue=ouvrir(app)
    app.dossier_fiscal_valide_courant=replace(app.dossier_fiscal_valide_courant,client='Autre dossier synthétique')
    bouton(dialogue,'Valider et appliquer').invoke()
    assert dialogue.winfo_exists() and 'dossier a changé' in app.messages_test[-1][1]


@pytest.mark.parametrize('nom',['identifiant','debut','fin','echeancier','ventilation','nature'])
def test_changement_revoque_confirmation(application,nom):
    app=application;_,dialogue=ouvrir(app)
    w=champ(dialogue,nom+'_interets_documentes')
    if nom in {'echeancier','ventilation'}:w.invoke()
    elif nom=='nature':w.set('CPG_ANNUEL')
    else:w.insert(0,'modifié')
    confirmation=champ(dialogue,'confirmation_interets_documentes')
    assert dialogue.getvar(confirmation.cget('variable'))==0
