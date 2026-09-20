import tkinter as tk
import pytest
from src.comptaprivee import gui_pension_splitting_2025 as module
from src.comptaprivee.gui_layout import FormulaireDefilant
from tests.test_gui_block2 import application, racine, bouton, descendants, derniere_fenetre
from tests.test_gui_pension_income_2025 import champ
from tests.test_tax_pension_splitting_2025 import choix, sauvegarder_fractionnement_2025


def ouvrir(app,mp,tmp_path):
    chemin=sauvegarder_fractionnement_2025(choix(),tmp_path/'couple.json')
    mp.setattr(module.filedialog,'askopenfilename',lambda **kw:str(chemin))
    dialogue=module.ouvrir_fractionnement_2025(app)
    bouton(dialogue,'Ouvrir le couple').invoke()
    return dialogue,chemin


@pytest.mark.parametrize('echelle',[96/72,144/72,192/72])
def test_actions_visibles(application,monkeypatch,tmp_path,echelle):
    app=application;app.tk.call('tk','scaling',echelle)
    dialogue,_=ouvrir(app,monkeypatch,tmp_path)
    for taille in ('600x400','1000x700'):
        dialogue.geometry(taille);app.update()
        form=next(w for w in dialogue.winfo_children() if isinstance(w,FormulaireDefilant))
        for action in form.actions.winfo_children():
            assert action.winfo_ismapped() and action.winfo_width()>=action.winfo_reqwidth()
            assert action.winfo_rooty()+action.winfo_height()<=dialogue.winfo_rooty()+dialogue.winfo_height()
        form.canvas.yview_moveto(1);app.update();assert form.canvas.yview()[1]==pytest.approx(1)


def test_calcul_modification_export_et_rechargement(application,monkeypatch,tmp_path):
    app=application;dialogue,json_path=ouvrir(app,monkeypatch,tmp_path)
    bouton(dialogue,'Calculer les deux déclarations').invoke();resultat=derniere_fenetre(dialogue)
    texte=next(w for w in descendants(resultat) if isinstance(w,tk.Text)).get('1.0','end')
    assert 'CEDANT-FICTIF' in texte and 'BENEFICIAIRE-FICTIF' in texte
    pdf=tmp_path/'couple.pdf';monkeypatch.setattr(module.filedialog,'asksaveasfilename',lambda **kw:str(pdf))
    bouton(resultat,'Exporter le PDF conjoint').invoke();assert pdf.exists()
    champ(dialogue,'cedant_source').insert(0,'Revu : ')
    for nom in ('cedant_confirme','beneficiaire_confirme','choix_conjoint_confirme'):
        check=champ(dialogue,nom);assert dialogue.getvar(check.cget('variable'))==0
    bouton(resultat,'Exporter le PDF conjoint').invoke();assert app.messages_test[-1][0]=='Estimation périmée'
    bouton(dialogue,'Calculer les deux déclarations').invoke();assert app.messages_test[-1][0]=='Fractionnement invalide'
    monkeypatch.setattr(module.filedialog,'asksaveasfilename',lambda **kw:str(json_path))
    bouton(dialogue,'Sauvegarder le couple').invoke();bouton(dialogue,'Ouvrir le couple').invoke()
    for nom in ('cedant_confirme','beneficiaire_confirme','choix_conjoint_confirme'):champ(dialogue,nom).invoke()
    bouton(dialogue,'Calculer les deux déclarations').invoke();assert derniere_fenetre(dialogue) is not resultat
    bouton(dialogue,'Sauvegarder le couple').invoke();bouton(dialogue,'Ouvrir le couple').invoke()
    check=champ(dialogue,'choix_conjoint_confirme');assert dialogue.getvar(check.cget('variable'))==1
    bouton(resultat,'Exporter le PDF conjoint').invoke();assert app.messages_test[-1][0]=='Estimation périmée'
