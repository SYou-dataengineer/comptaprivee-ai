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
    dossier_3h_c,
    profil_dividendes,
    profil_interets,
    profil_frais_3h_b,
    profil_frais_3h_d,
)
from tests.test_tax_capital_gains_2025 import profil_capital
from tests.test_tax_capital_loss_carryovers_2025 import profil_pertes


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

def ouvrir_integration_3h_b(app):
    d = dossier_combine()
    frais = profil_frais_3h_b(d)
    chemin = tax_case_storage.sauvegarder_dossier_fiscal(
        d,
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
        profil_frais_placement=frais,
    )
    charge = tax_case_storage.charger_dossier_fiscal(chemin)
    assert charge.profil_interets.confirme
    assert charge.profil_dividendes.confirme
    assert charge.profil_frais_placement.confirme

    app.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(app)
    bouton(fiscal, "Dossiers enregistrés").invoke()
    liste = derniere_fenetre(fiscal)
    bouton(liste, "Ouvrir le dossier").invoke()
    return fiscal, frais


def test_gui_3h_b_charge_frais_et_calcule_resume(application):
    app = application
    fiscal, frais = ouvrir_integration_3h_b(app)

    bouton(fiscal, "Frais de placement 2025 (3E)").invoke()
    dialogue = derniere_fenetre(fiscal)
    assert champ(dialogue, "gestion_frais_placement").get() == frais.gestion
    assert champ(dialogue, "interets_frais_placement").get() == frais.interets
    assert dialogue.getvar(champ(dialogue, "confirmation_frais_placement").cget("variable")) == 1
    bouton(dialogue, "Fermer").invoke()

    bouton(fiscal, "Calculer l'estimation fiscale 2025").invoke()
    resultat = derniere_fenetre(fiscal)
    texte = next(w for w in descendants(resultat) if isinstance(w, tk.Text)).get("1.0", "end")
    assert "BLOC 3H-B" in texte
    assert "18500.00 $" in texte
    assert "3.70 $" in texte
    fiscal.destroy()


def test_gui_3h_b_pdf_persistance_et_invalidation(application, monkeypatch, tmp_path):
    app = application
    fiscal, _ = ouvrir_integration_3h_b(app)

    bouton(fiscal, "Calculer l'estimation fiscale 2025").invoke()
    resultat = derniere_fenetre(fiscal)
    destination = tmp_path / "rapport_3h_b_gui.pdf"
    monkeypatch.setattr(gui.filedialog, "asksaveasfilename", lambda **kw: str(destination))
    bouton(resultat, "Exporter le rapport fiscal en PDF").invoke()
    assert destination.exists()

    app.callbacks_test["sauvegarder_dossier_fiscal_local"]()
    charge = tax_case_storage.charger_dossier_fiscal(
        next((tmp_path / "dossiers").glob("*.json"))
    )
    assert charge.profil_interets.confirme
    assert charge.profil_dividendes.confirme
    assert charge.profil_frais_placement.confirme

    bouton(fiscal, "Frais de placement 2025 (3E)").invoke()
    dialogue = derniere_fenetre(fiscal)
    entree = champ(dialogue, "gestion_frais_placement")
    entree.delete(0, "end")
    entree.insert(0, "600")
    champ(dialogue, "confirmation_report_frais").invoke()
    champ(dialogue, "confirmation_frais_placement").invoke()
    bouton(dialogue, "Valider et appliquer").invoke()
    assert not dialogue.winfo_exists(), app.messages_test

    bouton(resultat, "Exporter le rapport fiscal en PDF").invoke()
    assert app.messages_test[-1][0] == "Estimation périmée"
    fiscal.destroy()

def ouvrir_integration_3h_c(app):
    chemin = tax_case_storage.sauvegarder_dossier_fiscal(
        dossier_3h_c(),
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
        profil_capital=profil_capital(),
    )
    charge = tax_case_storage.charger_dossier_fiscal(chemin)
    assert charge.profil_interets.confirme
    assert charge.profil_dividendes.confirme
    assert charge.profil_capital.confirme

    app.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(app)
    bouton(fiscal, "Dossiers enregistrés").invoke()
    liste = derniere_fenetre(fiscal)
    bouton(liste, "Ouvrir le dossier").invoke()

    bouton(fiscal, "Gains et pertes en capital 2025").invoke()
    dialogue = derniere_fenetre(fiscal)
    return fiscal, dialogue


def test_gui_3h_c_capital_preserve_interets_dividendes_et_calcule(application):
    app = application
    fiscal, dialogue = ouvrir_integration_3h_c(app)

    assert champ(dialogue, "source_capital").get() == profil_capital().source
    assert dialogue.getvar(
        champ(dialogue, "confirmation_pbr_capital").cget("variable")
    ) == 1
    assert dialogue.getvar(
        champ(dialogue, "confirmation_capital").cget("variable")
    ) == 1

    bouton(dialogue, "Valider et appliquer").invoke()
    assert not dialogue.winfo_exists(), app.messages_test

    bouton(fiscal, "Calculer l'estimation fiscale 2025").invoke()
    resultat = derniere_fenetre(fiscal)
    texte = next(
        w for w in descendants(resultat) if isinstance(w, tk.Text)
    ).get("1.0", "end")

    assert "BLOC 3H-C" in texte
    assert "21220.00 $" in texte
    assert "30.90 $" in texte
    fiscal.destroy()


def test_gui_3h_c_persistance_pdf_et_invalidation(application, monkeypatch, tmp_path):
    app = application
    fiscal, dialogue = ouvrir_integration_3h_c(app)

    bouton(dialogue, "Valider et appliquer").invoke()
    assert not dialogue.winfo_exists(), app.messages_test

    bouton(fiscal, "Calculer l'estimation fiscale 2025").invoke()
    resultat = derniere_fenetre(fiscal)

    destination = tmp_path / "rapport_3h_c_gui.pdf"
    monkeypatch.setattr(
        gui.filedialog,
        "asksaveasfilename",
        lambda **kw: str(destination),
    )
    bouton(resultat, "Exporter le rapport fiscal en PDF").invoke()
    assert destination.exists()

    app.callbacks_test["sauvegarder_dossier_fiscal_local"]()
    charge = tax_case_storage.charger_dossier_fiscal(
        next((tmp_path / "dossiers").glob("*.json"))
    )
    assert charge.profil_interets.confirme
    assert charge.profil_dividendes.confirme
    assert charge.profil_capital.confirme

    bouton(fiscal, "Gains et pertes en capital 2025").invoke()
    dialogue = derniere_fenetre(fiscal)
    source = champ(dialogue, "source_capital")
    source.insert(0, "Revu : ")
    app.update()

    pbr = champ(dialogue, "confirmation_pbr_capital")
    capital = champ(dialogue, "confirmation_capital")
    if dialogue.getvar(pbr.cget("variable")) == 0:
        pbr.invoke()
    if dialogue.getvar(capital.cget("variable")) == 0:
        capital.invoke()

    bouton(dialogue, "Valider et appliquer").invoke()
    assert not dialogue.winfo_exists(), app.messages_test

    bouton(resultat, "Exporter le rapport fiscal en PDF").invoke()
    assert app.messages_test[-1][0] == "Estimation périmée"
    fiscal.destroy()

def ouvrir_integration_3h_d(app):
    d = dossier_3h_c()
    frais = profil_frais_3h_d(d)
    chemin = tax_case_storage.sauvegarder_dossier_fiscal(
        d,
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
        profil_capital=profil_capital(),
        profil_frais_placement=frais,
    )
    charge = tax_case_storage.charger_dossier_fiscal(chemin)
    assert charge.profil_interets.confirme
    assert charge.profil_dividendes.confirme
    assert charge.profil_capital.confirme
    assert charge.profil_frais_placement.confirme

    app.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(app)
    bouton(fiscal, "Dossiers enregistrés").invoke()
    liste = derniere_fenetre(fiscal)
    bouton(liste, "Ouvrir le dossier").invoke()
    return fiscal, frais


def test_gui_3h_d_charge_frais_et_calcule_resume(application):
    app = application
    fiscal, frais = ouvrir_integration_3h_d(app)

    bouton(fiscal, "Frais de placement 2025 (3E)").invoke()
    dialogue = derniere_fenetre(fiscal)
    assert "3H-D" in dialogue.title()
    assert champ(dialogue, "gestion_frais_placement").get() == frais.gestion
    assert champ(dialogue, "interets_frais_placement").get() == frais.interets
    assert dialogue.getvar(
        champ(dialogue, "confirmation_frais_placement").cget("variable")
    ) == 1
    bouton(dialogue, "Fermer").invoke()

    bouton(fiscal, "Calculer l'estimation fiscale 2025").invoke()
    resultat = derniere_fenetre(fiscal)
    texte = next(
        w for w in descendants(resultat) if isinstance(w, tk.Text)
    ).get("1.0", "end")

    assert "BLOC 3H-D" in texte
    assert "19720.00 $" in texte
    assert "15.90 $" in texte
    fiscal.destroy()


def test_gui_3h_d_pdf_persistance_et_invalidation(application, monkeypatch, tmp_path):
    app = application
    fiscal, _ = ouvrir_integration_3h_d(app)

    bouton(fiscal, "Calculer l'estimation fiscale 2025").invoke()
    resultat = derniere_fenetre(fiscal)

    destination = tmp_path / "rapport_3h_d_gui.pdf"
    monkeypatch.setattr(
        gui.filedialog,
        "asksaveasfilename",
        lambda **kw: str(destination),
    )
    bouton(resultat, "Exporter le rapport fiscal en PDF").invoke()
    assert destination.exists()

    app.callbacks_test["sauvegarder_dossier_fiscal_local"]()
    charge = tax_case_storage.charger_dossier_fiscal(
        next((tmp_path / "dossiers").glob("*.json"))
    )
    assert charge.profil_interets.confirme
    assert charge.profil_dividendes.confirme
    assert charge.profil_capital.confirme
    assert charge.profil_frais_placement.confirme

    bouton(fiscal, "Frais de placement 2025 (3E)").invoke()
    dialogue = derniere_fenetre(fiscal)
    entree = champ(dialogue, "gestion_frais_placement")
    entree.delete(0, "end")
    entree.insert(0, "1400")
    champ(dialogue, "confirmation_report_frais").invoke()
    champ(dialogue, "confirmation_frais_placement").invoke()
    bouton(dialogue, "Valider et appliquer").invoke()
    assert not dialogue.winfo_exists(), app.messages_test

    bouton(resultat, "Exporter le rapport fiscal en PDF").invoke()
    assert app.messages_test[-1][0] == "Estimation périmée"
    fiscal.destroy()

def ouvrir_integration_3h_e(app):
    d = dossier_3h_c()
    pertes = profil_pertes(
        d,
        demande_federale="1000",
        demande_quebec="800",
    )
    chemin = tax_case_storage.sauvegarder_dossier_fiscal(
        d,
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
        profil_capital=profil_capital(),
        profil_reports_pertes=pertes,
    )
    charge = tax_case_storage.charger_dossier_fiscal(chemin)
    assert charge.profil_interets.confirme
    assert charge.profil_dividendes.confirme
    assert charge.profil_capital.confirme
    assert charge.profil_reports_pertes.confirme

    app.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(app)
    bouton(fiscal, "Dossiers enregistrés").invoke()
    liste = derniere_fenetre(fiscal)
    bouton(liste, "Ouvrir le dossier").invoke()
    return fiscal, pertes


def test_gui_3h_e_charge_reports_et_calcule_resume(application):
    app = application
    fiscal, pertes = ouvrir_integration_3h_e(app)

    bouton(fiscal, "Reports de pertes en capital 2025 (3F)").invoke()
    dialogue = derniere_fenetre(fiscal)
    assert "3H-E" in dialogue.title()
    assert champ(dialogue, "demande_federale_reports_pertes").get() == pertes.demande_federale
    assert champ(dialogue, "demande_quebec_reports_pertes").get() == pertes.demande_quebec
    assert dialogue.getvar(
        champ(dialogue, "confirmation_reports_pertes").cget("variable")
    ) == 1
    bouton(dialogue, "Fermer").invoke()

    bouton(fiscal, "Calculer l'estimation fiscale 2025").invoke()
    resultat = derniere_fenetre(fiscal)
    texte = next(
        w for w in descendants(resultat) if isinstance(w, tk.Text)
    ).get("1.0", "end")

    assert "BLOC 3H-E" in texte
    assert "30.90 $" in texte
    fiscal.destroy()


def test_gui_3h_e_pdf_persistance_et_invalidation(application, monkeypatch, tmp_path):
    app = application
    fiscal, _ = ouvrir_integration_3h_e(app)

    bouton(fiscal, "Calculer l'estimation fiscale 2025").invoke()
    resultat = derniere_fenetre(fiscal)

    destination = tmp_path / "rapport_3h_e_gui.pdf"
    monkeypatch.setattr(
        gui.filedialog,
        "asksaveasfilename",
        lambda **kw: str(destination),
    )
    bouton(resultat, "Exporter le rapport fiscal en PDF").invoke()
    assert destination.exists()

    app.callbacks_test["sauvegarder_dossier_fiscal_local"]()
    charge = tax_case_storage.charger_dossier_fiscal(
        next((tmp_path / "dossiers").glob("*.json"))
    )
    assert charge.profil_interets.confirme
    assert charge.profil_dividendes.confirme
    assert charge.profil_capital.confirme
    assert charge.profil_reports_pertes.confirme

    bouton(fiscal, "Reports de pertes en capital 2025 (3F)").invoke()
    dialogue = derniere_fenetre(fiscal)
    entree = champ(dialogue, "demande_federale_reports_pertes")
    entree.delete(0, "end")
    entree.insert(0, "900")

    historique = champ(dialogue, "confirmation_historique_pertes")
    confirmation = champ(dialogue, "confirmation_reports_pertes")
    if dialogue.getvar(historique.cget("variable")) == 0:
        historique.invoke()
    if dialogue.getvar(confirmation.cget("variable")) == 0:
        confirmation.invoke()

    bouton(dialogue, "Valider et appliquer").invoke()
    assert not dialogue.winfo_exists(), app.messages_test

    bouton(resultat, "Exporter le rapport fiscal en PDF").invoke()
    assert app.messages_test[-1][0] == "Estimation périmée"
    fiscal.destroy()
