"""Parcours RRQ/RPC avec feuillets RRQ/RPC fictifs et stockage temporaire."""
import tkinter as tk

import pytest

from src.comptaprivee import gui, tax_case_storage
from src.comptaprivee.gui_layout import FormulaireDefilant
from tests.test_gui_block2 import application, racine, bouton, descendants, derniere_fenetre
from tests.test_tax_cpp_qpp_benefits_2025 import dossier_rrq_rpc


def ouvrir(app, confirme=False):
    tax_case_storage.sauvegarder_dossier_fiscal(dossier_rrq_rpc(), rrq_rpc_confirme=confirme)
    app.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(app)
    bouton(fiscal, "Dossiers enregistrés").invoke()
    bouton(derniere_fenetre(fiscal), "Ouvrir le dossier").invoke()
    bouton(fiscal, "RRQ/RPC 2025").invoke()
    return fiscal, derniere_fenetre(fiscal)


@pytest.mark.parametrize("echelle", [96/72, 144/72, 192/72])
def test_rrq_rpc_actions_visibles(application, echelle):
    app = application
    app.tk.call("tk", "scaling", echelle)
    fiscal, dialogue = ouvrir(app, True)
    for taille in ("600x400", "1000x700"):
        dialogue.geometry(taille)
        app.update()
        form = next(w for w in dialogue.winfo_children() if isinstance(w, FormulaireDefilant))
        for action in form.actions.winfo_children():
            assert action.winfo_ismapped()
            assert action.winfo_width() >= action.winfo_reqwidth()
            assert action.winfo_rooty() + action.winfo_height() <= dialogue.winfo_rooty() + dialogue.winfo_height()
            assert action.winfo_rootx() + action.winfo_width() <= dialogue.winfo_rootx() + dialogue.winfo_width()
        form.canvas.yview_moveto(1)
        app.update()
        assert form.canvas.yview()[1] == pytest.approx(1)
    bouton(dialogue, "Valider et appliquer").invoke()
    assert not dialogue.winfo_exists()


def test_rrq_rpc_confirmation_calcul_export_et_rechargement(application, monkeypatch, tmp_path):
    app = application
    fiscal, dialogue = ouvrir(app)
    bouton(dialogue, "Valider et appliquer").invoke()
    assert dialogue.winfo_exists() and app.messages_test[-1][0] == "RRQ/RPC invalide"
    next(w for w in descendants(dialogue) if isinstance(w, tk.Checkbutton)).invoke()
    bouton(dialogue, "Valider et appliquer").invoke()
    bouton(fiscal, "Calculer l'estimation fiscale 2025").invoke()
    resultat = derniere_fenetre(fiscal)
    texte = next(w for w in descendants(resultat) if isinstance(w, tk.Text)).get("1.0", "end")
    assert "11400" in texte and "71\u00a0515,00" in texte
    pdf = tmp_path / "rrq_rpc.pdf"
    monkeypatch.setattr(gui.filedialog, "asksaveasfilename", lambda **kw: str(pdf))
    bouton(resultat, "Exporter le rapport fiscal en PDF").invoke()
    assert pdf.exists()
    app.callbacks_test["sauvegarder_dossier_fiscal_local"]()
    chemin = next((tmp_path / "dossiers").glob("*.json"))
    charge = tax_case_storage.charger_dossier_fiscal(chemin)
    assert charge.rrq_rpc_confirme and not charge.rqap_confirme
    assert charge.rapport_pdf.resolve() == pdf
    bouton(fiscal, "RRQ/RPC 2025").invoke()
    bouton(derniere_fenetre(fiscal), "Valider et appliquer").invoke()
    bouton(resultat, "Exporter le rapport fiscal en PDF").invoke()
    assert app.messages_test[-1][0] == "Estimation périmée"
    app.callbacks_test["sauvegarder_dossier_fiscal_local"]()
    assert tax_case_storage.charger_dossier_fiscal(chemin).rapport_pdf is None
    fiscal.destroy()
    app.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(app)
    bouton(fiscal, "Dossiers enregistrés").invoke()
    bouton(derniere_fenetre(fiscal), "Ouvrir le dossier").invoke()
    bouton(fiscal, "RRQ/RPC 2025").invoke()
    dialogue = derniere_fenetre(fiscal)
    case = next(w for w in descendants(dialogue) if isinstance(w, tk.Checkbutton))
    assert dialogue.getvar(case.cget("variable")) == 1
    bouton(dialogue, "Fermer").invoke()
    app.callbacks_test["extraire_cases_documents_fiscaux"]()
    bouton(fiscal, "RRQ/RPC 2025").invoke()
    dialogue = derniere_fenetre(fiscal)
    case = next(w for w in descendants(dialogue) if isinstance(w, tk.Checkbutton))
    assert dialogue.getvar(case.cget("variable")) == 0


@pytest.mark.parametrize("vide", [None, "T4A(P)", "RL-2"])
def test_rrq_rpc_import_validation_et_preparation(application, monkeypatch, vide):
    app = application
    fiscal, dialogue = ouvrir(app)
    bouton(dialogue, "Fermer").invoke()
    dossier = dossier_rrq_rpc()

    def texte(chemin):
        if chemin.stem == vide:
            return chemin.stem
        return chemin.stem + "\n" + "\n".join(
            f"Case {d.case} {d.valeur_validee:.2f}"
            for d in dossier.donnees_validees if d.document.name == chemin.name)

    monkeypatch.setattr(gui, "extraire_texte_document", texte)
    app.callbacks_test["reconnaitre_documents_fiscaux"]()
    assert "T4A(P) : 1" in app.messages_test[-1][1]
    assert "RL-2 : 1" in app.messages_test[-1][1]
    assert "À vérifier / non reconnus : 0" in app.messages_test[-1][1]
    app.callbacks_test["extraire_cases_documents_fiscaux"]()
    validation = derniere_fenetre(fiscal)
    bouton(validation, "Valider tout").invoke()
    bouton(validation, "Fermer").invoke()
    app.callbacks_test["preparer_dossier_fiscal_valide"]()
    if vide:
        assert app.dossier_fiscal_valide_courant is None
        assert "ne peut pas être omis" in app.messages_test[-1][1]
    else:
        assert app.dossier_fiscal_valide_courant is not None
        bouton(fiscal, "RRQ/RPC 2025").invoke()
        dialogue = derniere_fenetre(fiscal)
        next(w for w in descendants(dialogue) if isinstance(w, tk.Checkbutton)).invoke()
        bouton(dialogue, "Valider et appliquer").invoke()
        assert not dialogue.winfo_exists()


def test_rrq_rpc_sans_dossier(application):
    application.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(application)
    bouton(fiscal, "RRQ/RPC 2025").invoke()
    dialogue = derniere_fenetre(fiscal)
    bouton(dialogue, "Valider et appliquer").invoke()
    assert dialogue.winfo_exists() and application.messages_test
    bouton(dialogue, "Fermer").invoke()

@pytest.mark.parametrize('case', ['14', '16', '17'])
def test_rrq_rpc_gui_sans_emploi(application, monkeypatch, tmp_path, case):
    app=application
    tax_case_storage.sauvegarder_dossier_fiscal(dossier_rrq_rpc(emploi=False,case=case,rl2=False),rrq_rpc_confirme=True)
    app.ouvrir_agent_fiscal()
    fiscal=derniere_fenetre(app)
    bouton(fiscal,'Dossiers enregistrés').invoke()
    bouton(derniere_fenetre(fiscal),'Ouvrir le dossier').invoke()
    bouton(fiscal,'Calculer l\'estimation fiscale 2025').invoke()
    resultat=derniere_fenetre(fiscal)
    texte=next(w for w in descendants(resultat) if isinstance(w,tk.Text)).get('1.0','end')
    assert '11400' in texte and 'aucun RL-2 reçu' in texte
    p=tmp_path/'sans-emploi.pdf'
    monkeypatch.setattr(gui.filedialog,'asksaveasfilename',lambda **kw: str(p))
    bouton(resultat,'Exporter le rapport fiscal en PDF').invoke()
    assert p.exists()
