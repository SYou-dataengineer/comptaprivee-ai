"""Parcours RQAP Tkinter avec données fictives et stockage temporaire."""
import tkinter as tk

import pytest

from src.comptaprivee import gui, tax_case_storage
from src.comptaprivee.gui_layout import FormulaireDefilant
from tests.test_gui_block2 import application, racine, bouton, descendants, derniere_fenetre
from tests.test_tax_parental_benefits_2025 import dossier_rqap


def ouvrir(app, confirme=False):
    tax_case_storage.sauvegarder_dossier_fiscal(dossier_rqap(), rqap_confirme=confirme)
    app.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(app)
    bouton(fiscal, "Dossiers enregistrés").invoke()
    bouton(derniere_fenetre(fiscal), "Ouvrir le dossier").invoke()
    bouton(fiscal, "Prestations RQAP 2025").invoke()
    return fiscal, derniere_fenetre(fiscal)


@pytest.mark.parametrize("echelle", [96/72, 144/72, 192/72])
def test_rqap_actions_visibles(application, echelle):
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


def test_rqap_confirmation_calcul_pdf_sauvegarde_rechargement(application, monkeypatch, tmp_path):
    app = application
    fiscal, dialogue = ouvrir(app)
    bouton(dialogue, "Valider et appliquer").invoke()
    assert dialogue.winfo_exists() and app.messages_test[-1][0] == "Prestations RQAP invalides"
    next(w for w in descendants(dialogue) if isinstance(w, tk.Checkbutton)).invoke()
    bouton(dialogue, "Valider et appliquer").invoke()
    bouton(fiscal, "Calculer l'estimation fiscale 2025").invoke()
    resultat = derniere_fenetre(fiscal)
    texte = next(w for w in descendants(resultat) if isinstance(w, tk.Text)).get("1.0", "end")
    assert "11905" in texte and "446" in texte and "70\u00a0515,00" in texte
    pdf = tmp_path / "rqap.pdf"
    monkeypatch.setattr(gui.filedialog, "asksaveasfilename", lambda **kw: str(pdf))
    bouton(resultat, "Exporter le rapport fiscal en PDF").invoke()
    assert pdf.exists()
    app.callbacks_test["sauvegarder_dossier_fiscal_local"]()
    chemin = next((tmp_path / "dossiers").glob("*.json"))
    charge = tax_case_storage.charger_dossier_fiscal(chemin)
    assert charge.rqap_confirme and charge.rapport_pdf.resolve() == pdf
    bouton(fiscal, "Prestations RQAP 2025").invoke()
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
    bouton(fiscal, "Prestations RQAP 2025").invoke()
    dialogue = derniere_fenetre(fiscal)
    case = next(w for w in descendants(dialogue) if isinstance(w, tk.Checkbutton))
    assert dialogue.getvar(case.cget("variable")) == 1
    bouton(dialogue, "Fermer").invoke()
    # Une nouvelle extraction retire la confirmation liée aux anciennes cases.
    app.callbacks_test["extraire_cases_documents_fiscaux"]()
    bouton(fiscal, "Prestations RQAP 2025").invoke()
    dialogue = derniere_fenetre(fiscal)
    case = next(w for w in descendants(dialogue) if isinstance(w, tk.Checkbutton))
    assert dialogue.getvar(case.cget("variable")) == 0


def test_rqap_sans_dossier_et_annulation(application):
    app = application
    app.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(app)
    bouton(fiscal, "Prestations RQAP 2025").invoke()
    dialogue = derniere_fenetre(fiscal)
    bouton(dialogue, "Valider et appliquer").invoke()
    assert dialogue.winfo_exists() and app.messages_test
    bouton(dialogue, "Fermer").invoke()
    assert not dialogue.winfo_exists()


@pytest.mark.parametrize("feuillet_vide", [None, "T4E", "RL-6", "illisible"])
def test_reconnaissance_extraction_et_refus_feuillet_vide(application, monkeypatch, feuillet_vide):
    app = application
    fiscal, dialogue = ouvrir(app)
    bouton(dialogue, "Fermer").invoke()
    dossier = dossier_rqap()

    def texte_document(chemin):
        type_doc = chemin.stem
        if feuillet_vide == "illisible" and type_doc == "T4E":
            raise ValueError("Lecture impossible")
        if type_doc == feuillet_vide:
            return type_doc  # reconnu, mais aucune case exploitable
        return type_doc + "\n" + "\n".join(
            f"Case {d.case} {d.valeur_validee:.2f}"
            for d in dossier.donnees_validees if d.document.name == chemin.name
        )

    monkeypatch.setattr(gui, "extraire_texte_document", texte_document)
    app.callbacks_test["reconnaitre_documents_fiscaux"]()
    message = app.messages_test[-1][1]
    assert "RL-6 : 1" in message
    if feuillet_vide == "illisible":
        assert "T4E : 0" in message and "À vérifier / non reconnus : 1" in message
    else:
        assert "T4E : 1" in message and "À vérifier / non reconnus : 0" in message
    app.callbacks_test["extraire_cases_documents_fiscaux"]()
    validation = derniere_fenetre(fiscal)
    bouton(validation, "Valider tout").invoke()
    bouton(validation, "Fermer").invoke()
    app.callbacks_test["preparer_dossier_fiscal_valide"]()
    if feuillet_vide:
        assert app.dossier_fiscal_valide_courant is None
        assert app.messages_test[-1][0] == "Dossier fiscal non prêt"
        assert "ne peut pas être omis" in app.messages_test[-1][1]
    else:
        assert app.dossier_fiscal_valide_courant is not None
        assert {d.type_document for d in app.dossier_fiscal_valide_courant.donnees_validees} == {"T4", "RL-1", "T4E", "RL-6"}
        bouton(fiscal, "Prestations RQAP 2025").invoke()
        dialogue = derniere_fenetre(fiscal)
        next(w for w in descendants(dialogue) if isinstance(w, tk.Checkbutton)).invoke()
        bouton(dialogue, "Valider et appliquer").invoke()
        assert not dialogue.winfo_exists()
