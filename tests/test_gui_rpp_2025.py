"""Parcours Tkinter RPA sur données fictives et stockage isolé."""
import tkinter as tk
from tkinter import ttk
from decimal import Decimal

import pytest

from src.comptaprivee import gui, tax_case_storage
from src.comptaprivee.gui_layout import FormulaireDefilant
from tests.test_gui_block2 import application, racine, bouton, descendants, derniere_fenetre
from tests.test_tax_rpp_2025 import dossier_rpa, profil_rpa
from tests.test_tax_estimation_2025 import _dossier_52000


def ouvrir(app):
    tax_case_storage.sauvegarder_dossier_fiscal(dossier_rpa(), cotisations_rpa=profil_rpa())
    app.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(app)
    bouton(fiscal, "Dossiers enregistrés").invoke()
    bouton(derniere_fenetre(fiscal), "Ouvrir le dossier").invoke()
    bouton(fiscal, "Cotisations RPA 2025").invoke()
    return fiscal, derniere_fenetre(fiscal)


@pytest.mark.parametrize("echelle", [96 / 72, 144 / 72, 192 / 72])
def test_rpa_actions_visibles_redimensionnement(application, echelle):
    app = application
    app.tk.call("tk", "scaling", echelle)
    fiscal, dialogue = ouvrir(app)
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


def test_rpa_erreur_annulation_effacer_et_rechargement(application):
    app = application
    fiscal, dialogue = ouvrir(app)
    champs = [w for w in descendants(dialogue) if isinstance(w, ttk.Entry)]
    assert champs[0].get() == "3000"
    champs[0].delete(0, "end")
    champs[0].insert(0, "NaN")
    bouton(dialogue, "Valider et appliquer").invoke()
    assert dialogue.winfo_exists() and app.messages_test
    bouton(dialogue, "Fermer").invoke()
    bouton(fiscal, "Cotisations RPA 2025").invoke()
    dialogue = derniere_fenetre(fiscal)
    assert next(w for w in descendants(dialogue) if isinstance(w, ttk.Entry)).get() == "3000"
    bouton(dialogue, "Effacer").invoke()
    assert all(w.get() == "" for w in descendants(dialogue) if isinstance(w, ttk.Entry))
    bouton(dialogue, "Valider et appliquer").invoke()
    # Des cases RPA validées interdisent de les omettre silencieusement.
    assert dialogue.winfo_exists()
    bouton(dialogue, "Fermer").invoke()


def test_rpa_calcul_sauvegarde_export_et_estimation_perimee(application, monkeypatch, tmp_path):
    app = application
    fiscal, dialogue = ouvrir(app)
    bouton(dialogue, "Valider et appliquer").invoke()
    bouton(fiscal, "Calculer l'estimation fiscale 2025").invoke()
    resultat = derniere_fenetre(fiscal)
    texte = next(w for w in descendants(resultat) if isinstance(w, tk.Text)).get("1.0", "end")
    assert "20700" in texte and "6\u00a0394,28" in texte
    pdf = tmp_path / "data" / "exports" / "Estimation_Fiscale_2025_Client_Test.pdf"
    monkeypatch.setattr(gui.filedialog, "asksaveasfilename", lambda **kw: str(pdf))
    bouton(resultat, "Exporter le rapport fiscal en PDF").invoke()
    assert pdf.exists()
    app.callbacks_test["sauvegarder_dossier_fiscal_local"]()
    charge = tax_case_storage.charger_dossier_fiscal(next((tmp_path / "dossiers").glob("*.json")))
    assert charge.cotisations_rpa == profil_rpa()
    assert charge.rapport_pdf.resolve() == pdf
    # Même une confirmation du profil invalide l'ancienne estimation et son PDF.
    bouton(fiscal, "Cotisations RPA 2025").invoke()
    dialogue = derniere_fenetre(fiscal)
    bouton(dialogue, "Valider et appliquer").invoke()
    messages_avant = len(app.messages_test)
    bouton(resultat, "Exporter le rapport fiscal en PDF").invoke()
    assert len(app.messages_test) == messages_avant + 1
    assert app.messages_test[-1][0] == "Estimation périmée"
    app.callbacks_test["sauvegarder_dossier_fiscal_local"]()
    charge = tax_case_storage.charger_dossier_fiscal(next((tmp_path / "dossiers").glob("*.json")))
    assert charge.rapport_pdf is None
    assert charge.estimation.montant == Decimal("6394.28")
    fiscal.destroy()
    app.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(app)
    bouton(fiscal, "Dossiers enregistrés").invoke()
    bouton(derniere_fenetre(fiscal), "Ouvrir le dossier").invoke()
    bouton(fiscal, "Cotisations RPA 2025").invoke()
    dialogue = derniere_fenetre(fiscal)
    assert next(w for w in descendants(dialogue) if isinstance(w, ttk.Entry)).get() == "3000"
    bouton(dialogue, "Fermer").invoke()
    app.callbacks_test["sauvegarder_dossier_fiscal_local"]()
    charge = tax_case_storage.charger_dossier_fiscal(next((tmp_path / "dossiers").glob("*.json")))
    assert charge.rapport_pdf is None


def test_rpa_saisie_manuelle_depuis_profil_vide(application, tmp_path):
    app = application
    tax_case_storage.sauvegarder_dossier_fiscal(_dossier_52000())
    app.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(app)
    bouton(fiscal, "Dossiers enregistrés").invoke()
    bouton(derniere_fenetre(fiscal), "Ouvrir le dossier").invoke()
    bouton(fiscal, "Cotisations RPA 2025").invoke()
    dialogue = derniere_fenetre(fiscal)
    champs = [w for w in descendants(dialogue) if isinstance(w, ttk.Entry)]
    assert all(w.get() == "" for w in champs)
    for champ, valeur in zip(champs, ("3 000,00", "3 000,00", "Reçu RPA fédéral 2025", "Reçu RPA Québec 2025")):
        champ.insert(0, valeur)
    bouton(dialogue, "Valider et appliquer").invoke()
    assert dialogue.winfo_exists()  # confirmations requises
    for case in (w for w in descendants(dialogue) if isinstance(w, tk.Checkbutton)):
        case.invoke()
    bouton(dialogue, "Valider et appliquer").invoke()
    assert not dialogue.winfo_exists()
    app.callbacks_test["sauvegarder_dossier_fiscal_local"]()
    charge = tax_case_storage.charger_dossier_fiscal(next((tmp_path / "dossiers").glob("*.json")))
    assert charge.cotisations_rpa.montant_federal == Decimal("3000")
    assert charge.cotisations_rpa.source_federale == "Reçu RPA fédéral 2025"
    assert charge.estimation.montant == Decimal("6394.28")
