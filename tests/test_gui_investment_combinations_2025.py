"""Tests GUI d'intégration du parcours combiné 3H-A."""
import tkinter as tk

from src.comptaprivee import gui, tax_case_storage
from tests.test_gui_block2 import (
    application,
    racine,
    bouton,
    descendants,
    derniere_fenetre,
)
from tests.test_gui_pension_income_2025 import champ
from tests.test_tax_investment_combinations_2025 import (
    dossier_combine,
    profil_dividendes,
    profil_interets,
)


def ouvrir_integration_3h_a(app):
    chemin = tax_case_storage.sauvegarder_dossier_fiscal(
        dossier_combine(),
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
    )
    charge = tax_case_storage.charger_dossier_fiscal(chemin)
    assert charge.profil_interets.confirme
    assert charge.profil_dividendes.confirme

    app.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(app)

    bouton(fiscal, "Dossiers enregistrés").invoke()
    liste = derniere_fenetre(fiscal)
    bouton(liste, "Ouvrir le dossier").invoke()

    bouton(fiscal, "Intérêts + dividendes 2025 (3H-A)").invoke()
    dialogue = derniere_fenetre(fiscal)
    return fiscal, dialogue


def test_gui_3h_a_charge_deux_profils(application):
    app = application
    fiscal, dialogue = ouvrir_integration_3h_a(app)

    assert champ(dialogue, "source_interets_3h").get() == profil_interets().source
    assert champ(dialogue, "source_dividendes_3h").get() == profil_dividendes().source

    c_i = champ(dialogue, "confirmation_interets_3h")
    c_d = champ(dialogue, "confirmation_dividendes_3h")
    assert dialogue.getvar(c_i.cget("variable")) == 1
    assert dialogue.getvar(c_d.cget("variable")) == 1

    bouton(dialogue, "Fermer").invoke()
    fiscal.destroy()


def test_gui_3h_a_calcul_resume_pdf_et_invalidation(application, monkeypatch, tmp_path):
    app = application
    fiscal, dialogue = ouvrir_integration_3h_a(app)

    bouton(dialogue, "Valider et appliquer").invoke()
    assert not dialogue.winfo_exists(), app.messages_test

    bouton(fiscal, "Calculer l'estimation fiscale 2025").invoke()
    resultat = derniere_fenetre(fiscal)
    texte = next(
        w for w in descendants(resultat) if isinstance(w, tk.Text)
    ).get("1.0", "end")

    assert "COMBINAISON CONTRÔLÉE 2025" in texte
    assert "BLOC 3H-A" in texte
    assert "Assiette FSS globale 446" in texte
    assert "18.70 $" in texte

    destination = tmp_path / "rapport_3h_a_gui.pdf"
    monkeypatch.setattr(
        gui.filedialog,
        "asksaveasfilename",
        lambda **kw: str(destination),
    )
    bouton(resultat, "Exporter le rapport fiscal en PDF").invoke()
    assert destination.exists()

    bouton(fiscal, "Intérêts + dividendes 2025 (3H-A)").invoke()
    dialogue = derniere_fenetre(fiscal)

    source = champ(dialogue, "source_interets_3h")
    variable_source = source.cget("textvariable")
    dialogue.setvar(
        variable_source,
        "Revu : " + source.get(),
    )
    app.update()

    c_i = champ(dialogue, "confirmation_interets_3h")
    c_d = champ(dialogue, "confirmation_dividendes_3h")
    assert dialogue.getvar(c_i.cget("variable")) == 0
    assert dialogue.getvar(c_d.cget("variable")) == 0

    c_i.invoke()
    c_d.invoke()
    bouton(dialogue, "Valider et appliquer").invoke()
    assert not dialogue.winfo_exists(), app.messages_test

    bouton(resultat, "Exporter le rapport fiscal en PDF").invoke()
    assert app.messages_test[-1][0] == "Estimation périmée"

    fiscal.destroy()


def test_gui_3h_a_rechargement_persiste_les_deux_profils(application):
    app = application
    fiscal, dialogue = ouvrir_integration_3h_a(app)

    champ(dialogue, "source_interets_3h").insert(0, "Rechargé : ")
    app.update()

    c_i = champ(dialogue, "confirmation_interets_3h")
    c_d = champ(dialogue, "confirmation_dividendes_3h")
    if dialogue.getvar(c_i.cget("variable")) == 0:
        c_i.invoke()
    if dialogue.getvar(c_d.cget("variable")) == 0:
        c_d.invoke()

    bouton(dialogue, "Valider et appliquer").invoke()
    assert not dialogue.winfo_exists(), app.messages_test

    app.callbacks_test["sauvegarder_dossier_fiscal_local"]()

    fiscal.destroy()
    app.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(app)

    bouton(fiscal, "Dossiers enregistrés").invoke()
    liste = derniere_fenetre(fiscal)
    bouton(liste, "Ouvrir le dossier").invoke()

    bouton(fiscal, "Intérêts + dividendes 2025 (3H-A)").invoke()
    dialogue = derniere_fenetre(fiscal)

    assert champ(dialogue, "source_interets_3h").get().startswith("Rechargé : ")
    assert champ(dialogue, "source_dividendes_3h").get() == profil_dividendes().source

    bouton(dialogue, "Fermer").invoke()
    fiscal.destroy()
