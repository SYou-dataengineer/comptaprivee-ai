"""Parcours GUI pensions : saisie, confirmation, recalcul, PDF et stockage."""
import tkinter as tk
import pytest
from src.comptaprivee import gui, tax_case_storage
from src.comptaprivee.gui_layout import FormulaireDefilant
from tests.test_gui_block2 import application, racine, bouton, descendants, derniere_fenetre
from tests.test_tax_pension_income_2025 import dossier_pensions, profil_pensions
from dataclasses import replace


def champ(dialogue,nom):return next(w for w in descendants(dialogue) if w.winfo_name()==nom)


def ouvrir(app,confirme=False,nature='RPA',age=64):
    tax_case_storage.sauvegarder_dossier_fiscal(dossier_pensions(nature),profil_pensions=replace(profil_pensions(nature,age),confirme=confirme))
    app.ouvrir_agent_fiscal();fiscal=derniere_fenetre(app)
    bouton(fiscal,'Dossiers enregistrés').invoke();bouton(derniere_fenetre(fiscal),'Ouvrir le dossier').invoke()
    bouton(fiscal,'Pensions, FERR et rentes 2025').invoke()
    return fiscal,derniere_fenetre(fiscal)


@pytest.mark.parametrize('echelle',[96/72,144/72,192/72])
def test_actions_visibles(application,echelle):
    app=application;app.tk.call('tk','scaling',echelle)
    fiscal,dialogue=ouvrir(app,True)
    for taille in ('600x400','1000x700'):
        dialogue.geometry(taille);app.update()
        form=next(w for w in dialogue.winfo_children() if isinstance(w,FormulaireDefilant))
        for action in form.actions.winfo_children():
            assert action.winfo_ismapped() and action.winfo_width()>=action.winfo_reqwidth()
            assert action.winfo_rooty()+action.winfo_height()<=dialogue.winfo_rooty()+dialogue.winfo_height()
            assert action.winfo_rootx()+action.winfo_width()<=dialogue.winfo_rootx()+dialogue.winfo_width()
        form.canvas.yview_moveto(1);app.update();assert form.canvas.yview()[1]==pytest.approx(1)
    bouton(dialogue,'Valider et appliquer').invoke();assert not dialogue.winfo_exists()


def test_confirmation_calcul_export_stockage_et_invalidation(application,monkeypatch,tmp_path):
    app=application;fiscal,dialogue=ouvrir(app)
    bouton(dialogue,'Valider et appliquer').invoke()
    assert dialogue.winfo_exists() and app.messages_test[-1][0]=='Pensions invalides'
    champ(dialogue,'confirmation_pensions').invoke();bouton(dialogue,'Valider et appliquer').invoke()
    bouton(fiscal,"Calculer l'estimation fiscale 2025").invoke();resultat=derniere_fenetre(fiscal)
    texte=next(w for w in descendants(resultat) if isinstance(w,tk.Text)).get('1.0','end')
    assert 'PENSIONS, FERR' in texte and '31400' in texte and '361' in texte
    pdf=tmp_path/'pensions.pdf';monkeypatch.setattr(gui.filedialog,'asksaveasfilename',lambda **kw:str(pdf))
    bouton(resultat,'Exporter le rapport fiscal en PDF').invoke();assert pdf.exists()
    app.callbacks_test['sauvegarder_dossier_fiscal_local']()
    chemin=next((tmp_path/'dossiers').glob('*.json'));charge=tax_case_storage.charger_dossier_fiscal(chemin)
    assert charge.profil_pensions.confirme and charge.profil_pensions.age_31_decembre==64
    assert charge.rapport_pdf.resolve()==pdf
    bouton(fiscal,'Pensions, FERR et rentes 2025').invoke();bouton(derniere_fenetre(fiscal),'Valider et appliquer').invoke()
    bouton(resultat,'Exporter le rapport fiscal en PDF').invoke();assert app.messages_test[-1][0]=='Estimation périmée'
    app.callbacks_test['sauvegarder_dossier_fiscal_local']();assert tax_case_storage.charger_dossier_fiscal(chemin).rapport_pdf is None
    fiscal.destroy();app.ouvrir_agent_fiscal();fiscal=derniere_fenetre(app)
    bouton(fiscal,'Dossiers enregistrés').invoke();bouton(derniere_fenetre(fiscal),'Ouvrir le dossier').invoke()
    bouton(fiscal,'Pensions, FERR et rentes 2025').invoke();dialogue=derniere_fenetre(fiscal)
    assert champ(dialogue,'age_pensions').get()=='64' and champ(dialogue,'nature_pensions').get()=='RPA'
    check=champ(dialogue,'confirmation_pensions');assert dialogue.getvar(check.cget('variable'))==1
    bouton(dialogue,'Fermer').invoke();app.callbacks_test['extraire_cases_documents_fiscaux']()
    bouton(fiscal,'Pensions, FERR et rentes 2025').invoke();dialogue=derniere_fenetre(fiscal)
    check=champ(dialogue,'confirmation_pensions');assert dialogue.getvar(check.cget('variable'))==0


@pytest.mark.parametrize('nature',['RPA','FERR','T3_RPA','T5_RENTE'])
@pytest.mark.parametrize('vide',[False,True])
def test_import_preparation(application,monkeypatch,nature,vide):
    app=application;fiscal,dialogue=ouvrir(app,nature=nature);bouton(dialogue,'Fermer').invoke()
    dossier=dossier_pensions(nature);t=dossier.donnees_validees[0].type_document
    def texte(chemin):
        if vide and chemin.stem==t:return t
        return chemin.stem+'\n'+'\n'.join(f'Case {d.case} {d.valeur_validee:.2f}' for d in dossier.donnees_validees if d.document.name==chemin.name)
    monkeypatch.setattr(gui,'extraire_texte_document',texte)
    app.callbacks_test['reconnaitre_documents_fiscaux']()
    assert f'{t} : 1' in app.messages_test[-1][1] and 'À vérifier / non reconnus : 0' in app.messages_test[-1][1]
    app.callbacks_test['extraire_cases_documents_fiscaux']();validation=derniere_fenetre(fiscal)
    bouton(validation,'Valider tout').invoke();bouton(validation,'Fermer').invoke();app.callbacks_test['preparer_dossier_fiscal_valide']()
    if vide:
        assert app.dossier_fiscal_valide_courant is None and 'ne peut pas être omis' in app.messages_test[-1][1]
    else:
        assert app.dossier_fiscal_valide_courant is not None
        bouton(fiscal,'Pensions, FERR et rentes 2025').invoke();dialogue=derniere_fenetre(fiscal)
        champ(dialogue,'nature_pensions').set(nature);champ(dialogue,'age_pensions').insert(0,'65');champ(dialogue,'source_pensions').insert(0,'Acte validé')
        champ(dialogue,'confirmation_pensions').invoke();bouton(dialogue,'Valider et appliquer').invoke()
        assert not dialogue.winfo_exists()
        bouton(fiscal,"Calculer l'estimation fiscale 2025").invoke()
        resultat=derniere_fenetre(fiscal);assert any(isinstance(w,tk.Text) for w in descendants(resultat))


@pytest.mark.parametrize('texte',['Revenu reçu en raison','Revenu étranger'])
def test_deces_et_etranger_refuses(application,texte):
    app=application;fiscal,dialogue=ouvrir(app,True)
    next(w for w in descendants(dialogue) if isinstance(w,tk.Checkbutton) and w.cget('text').startswith(texte)).invoke()
    bouton(dialogue,'Valider et appliquer').invoke()
    assert dialogue.winfo_exists() and 'hors périmètre' in app.messages_test[-1][1]


def test_age_invalide_et_dossier_modifie(application):
    app=application;fiscal,dialogue=ouvrir(app,True)
    age=champ(dialogue,'age_pensions');age.delete(0,'end');age.insert(0,'64.5')
    bouton(dialogue,'Valider et appliquer').invoke();assert dialogue.winfo_exists()
    age.delete(0,'end');age.insert(0,'65');app.dossier_fiscal_valide_courant=dossier_pensions()
    bouton(dialogue,'Valider et appliquer').invoke();assert dialogue.winfo_exists() and 'changé' in app.messages_test[-1][1]

@pytest.mark.parametrize('nom,valeur', [('age_pensions','65'), ('source_pensions','Acte revu'), ('nature_pensions','VIAGERE_VARIABLE')])
def test_modification_retire_confirmation(application, nom, valeur):
    app = application
    fiscal, dialogue = ouvrir(app, True)
    widget = champ(dialogue, nom)
    if nom == 'nature_pensions':
        widget.set(valeur)
    else:
        widget.delete(0, 'end')
        widget.insert(0, valeur)
    check = champ(dialogue, 'confirmation_pensions')
    assert dialogue.getvar(check.cget('variable')) == 0
    bouton(dialogue, 'Valider et appliquer').invoke()
    assert dialogue.winfo_exists()
    if nom == 'nature_pensions':
        widget.set('RPA')
    check.invoke()
    bouton(dialogue, 'Valider et appliquer').invoke()
    assert not dialogue.winfo_exists()
    app.callbacks_test['sauvegarder_dossier_fiscal_local']()
    bouton(fiscal, 'Pensions, FERR et rentes 2025').invoke()
    dialogue = derniere_fenetre(fiscal)
    check = champ(dialogue, 'confirmation_pensions')
    assert dialogue.getvar(check.cget('variable')) == 1
