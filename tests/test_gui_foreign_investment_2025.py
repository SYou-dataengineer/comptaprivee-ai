"""Tests GUI unitaires du formulaire 3G, avant intégration à gui.py."""
from decimal import Decimal as D
import tkinter as tk

import pytest

from src.comptaprivee.gui_foreign_investment_2025 import (
    _decimal_champ,
    ouvrir_placement_etranger_2025,
)
from src.comptaprivee.tax_foreign_investment_2025 import (
    ProfilCreditImpotEtranger2025,
    ProfilPlacementEtranger2025,
)
from tests.test_gui_block2 import descendants, bouton, racine, application, derniere_fenetre
from tests.test_gui_pension_income_2025 import champ
from tests.test_tax_foreign_investment_2025 import dossier


@pytest.mark.parametrize(
    "texte,attendu",
    [
        ("", D("0")),
        ("100", D("100")),
        ("100,25", D("100.25")),
        ("1 000.25", D("1000.25")),
    ],
)
def test_decimal_champ_3g(texte, attendu):
    assert _decimal_champ(texte, "Montant") == attendu


@pytest.mark.parametrize("texte", ["-1", "NaN", "Infinity", "1.001", "abc"])
def test_decimal_champ_3g_refuse(texte):
    with pytest.raises(ValueError):
        _decimal_champ(texte, "Montant")


def profil_placement():
    return ProfilPlacementEtranger2025(
        source="T5/RL-3 vérifiés",
        confirme=True,
        pays="États-Unis",
        devise="CAD",
        obligations_biens_etrangers_verifiees=True,
    )


def profil_credit():
    return ProfilCreditImpotEtranger2025(
        credit_federal_40500=D("100"),
        credit_quebec_409=D("50"),
        source_t2209="T2209 vérifié",
        source_tp772="TP-772 vérifié",
        confirme=True,
    )


def test_formulaire_3g_charge_valeurs(racine):
    dialogue = ouvrir_placement_etranger_2025(
        racine, profil_placement(), profil_credit(), dossier(), lambda *_: None
    )
    racine.update()
    assert champ(dialogue, "pays_placement_etranger").get() == "États-Unis"
    assert champ(dialogue, "devise_placement_etranger").get() == "CAD"
    assert champ(dialogue, "credit_federal_40500_etranger").get() == "100"
    dialogue.destroy()


def test_modification_revoque_confirmations(racine):
    dialogue = ouvrir_placement_etranger_2025(
        racine, profil_placement(), profil_credit(), dossier(), lambda *_: None
    )
    racine.update()
    entree = champ(dialogue, "pays_placement_etranger")
    entree.insert("end", "X")
    racine.update()
    for nom in (
        "confirmation_placement_etranger",
        "confirmation_credit_etranger",
    ):
        check = champ(dialogue, nom)
        assert dialogue.getvar(check.cget("variable")) == 0
    dialogue.destroy()


def test_validation_transmet_deux_profils(racine):
    recus = []
    dialogue = ouvrir_placement_etranger_2025(
        racine,
        profil_placement(),
        profil_credit(),
        dossier(),
        lambda p, c: recus.append((p, c)),
    )
    racine.update()
    bouton(dialogue, "Valider et appliquer").invoke()
    racine.update()
    assert len(recus) == 1
    assert recus[0][0].pays == "États-Unis"
    assert recus[0][1].credit_federal_40500 == D("100")
    assert not dialogue.winfo_exists()


@pytest.mark.parametrize("echelle", [96 / 72, 144 / 72, 192 / 72])
def test_actions_visibles_3g(racine, echelle):
    from src.comptaprivee.gui_layout import FormulaireDefilant

    racine.tk.call("tk", "scaling", echelle)
    dialogue = ouvrir_placement_etranger_2025(
        racine, profil_placement(), profil_credit(), dossier(), lambda *_: None
    )
    for taille in ("600x400", "1000x700"):
        dialogue.geometry(taille)
        racine.update()
        formulaire = next(
            w for w in dialogue.winfo_children()
            if isinstance(w, FormulaireDefilant)
        )
        for action in formulaire.actions.winfo_children():
            assert action.winfo_ismapped()
            assert action.winfo_width() >= action.winfo_reqwidth()
            assert (
                action.winfo_rooty() + action.winfo_height()
                <= dialogue.winfo_rooty() + dialogue.winfo_height()
            )
        formulaire.canvas.yview_moveto(1)
        racine.update()
        assert formulaire.canvas.yview()[1] == pytest.approx(1)
    dialogue.destroy()


def ouvrir_integration_3g(app):
    from src.comptaprivee import tax_case_storage
    from tests.test_gui_block2 import derniere_fenetre

    chemin_3g = tax_case_storage.sauvegarder_dossier_fiscal(
        dossier("10000.00", "1500.00"),
        profil_placement_etranger=profil_placement(),
        profil_credit_impot_etranger=profil_credit(),
    )
    charge_direct = tax_case_storage.charger_dossier_fiscal(chemin_3g)
    assert charge_direct.profil_placement_etranger.pays == "États-Unis"
    assert charge_direct.profil_placement_etranger.source == "T5/RL-3 vérifiés"
    assert charge_direct.profil_credit_impot_etranger.credit_federal_40500 == D("100")
    assert charge_direct.profil_credit_impot_etranger.credit_quebec_409 == D("50")
    app.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(app)
    bouton(fiscal, "Dossiers enregistrés").invoke()
    bouton(derniere_fenetre(fiscal), "Ouvrir le dossier").invoke()
    import inspect
    callback_3g = app.callbacks_test["ouvrir_etranger_2025"]
    etat_3g = inspect.getclosurevars(callback_3g).nonlocals
    assert etat_3g["placement_etranger_profil_courant"].pays == "États-Unis"
    assert etat_3g["placement_etranger_profil_courant"].source == "T5/RL-3 vérifiés"
    assert etat_3g["credit_etranger_profil_courant"].credit_federal_40500 == D("100")
    bouton(fiscal, "Placements et impôts étrangers 2025 (3G)").invoke()
    return fiscal, derniere_fenetre(fiscal)


def test_integration_gui_3g_calcul_pdf_stockage_invalidation_rechargement(
    application, monkeypatch, tmp_path
):
    from src.comptaprivee import gui, tax_case_storage
    from tests.test_gui_block2 import derniere_fenetre

    app = application
    fiscal, dialogue = ouvrir_integration_3g(app)

    assert champ(dialogue, "pays_placement_etranger").get() == "États-Unis"
    assert champ(dialogue, "credit_federal_40500_etranger").get() == "100"
    assert champ(dialogue, "credit_quebec_409_etranger").get() == "50"
    bouton(dialogue, "Fermer").invoke()

    bouton(fiscal, "Calculer l'estimation fiscale 2025").invoke()
    ancien = derniere_fenetre(fiscal)
    texte = next(
        w for w in descendants(ancien) if isinstance(w, tk.Text)
    ).get("1.0", "end")
    assert "PLACEMENT ÉTRANGER 2025" in texte
    assert "CRÉDITS POUR IMPÔT ÉTRANGER 2025" in texte
    assert "12100" in texte
    assert "40500" in texte
    assert "409" in texte
    assert "FSS Québec 446" in texte

    pdf = tmp_path / "rapport_3g_gui.pdf"
    monkeypatch.setattr(
        gui.filedialog,
        "asksaveasfilename",
        lambda **kw: str(pdf),
    )
    bouton(ancien, "Exporter le rapport fiscal en PDF").invoke()
    assert pdf.exists()

    app.callbacks_test["sauvegarder_dossier_fiscal_local"]()
    chemin = next((tmp_path / "dossiers").glob("*.json"))
    charge = tax_case_storage.charger_dossier_fiscal(chemin)
    assert charge.profil_placement_etranger.confirme
    assert charge.profil_credit_impot_etranger.confirme
    assert charge.rapport_pdf is not None

    bouton(fiscal, "Placements et impôts étrangers 2025 (3G)").invoke()
    dialogue = derniere_fenetre(fiscal)
    source = champ(dialogue, "source_placement_etranger")
    source.insert(0, "Revu : ")
    app.update()

    for nom in (
        "confirmation_placement_etranger",
        "confirmation_credit_etranger",
    ):
        check = champ(dialogue, nom)
        assert dialogue.getvar(check.cget("variable")) == 0
        check.invoke()

    bouton(dialogue, "Valider et appliquer").invoke()
    assert not dialogue.winfo_exists(), app.messages_test

    bouton(ancien, "Exporter le rapport fiscal en PDF").invoke()
    assert app.messages_test[-1][0] == "Estimation périmée"

    app.callbacks_test["sauvegarder_dossier_fiscal_local"]()
    charge = tax_case_storage.charger_dossier_fiscal(chemin)
    assert charge.rapport_pdf is None
    assert charge.profil_placement_etranger.source.startswith("Revu : ")

    bouton(fiscal, "Recalculer l'estimation fiscale 2025").invoke()
    nouveau = derniere_fenetre(fiscal)
    texte = next(
        w for w in descendants(nouveau) if isinstance(w, tk.Text)
    ).get("1.0", "end")
    assert "Revu :" in texte
    assert "CRÉDITS POUR IMPÔT ÉTRANGER 2025" in texte

    fiscal.destroy()
    app.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(app)
    bouton(fiscal, "Dossiers enregistrés").invoke()
    bouton(derniere_fenetre(fiscal), "Ouvrir le dossier").invoke()
    bouton(fiscal, "Placements et impôts étrangers 2025 (3G)").invoke()
    dialogue = derniere_fenetre(fiscal)
    assert champ(dialogue, "source_placement_etranger").get().startswith("Revu : ")
    assert champ(dialogue, "credit_federal_40500_etranger").get() == "100"


def test_integration_gui_3g_dossier_change_refuse(application):
    from dataclasses import replace

    app = application
    _, dialogue = ouvrir_integration_3g(app)
    app.dossier_fiscal_valide_courant = replace(
        app.dossier_fiscal_valide_courant,
        client="Autre dossier synthétique",
    )
    bouton(dialogue, "Valider et appliquer").invoke()
    assert dialogue.winfo_exists()
    assert "changé" in app.messages_test[-1][1]
