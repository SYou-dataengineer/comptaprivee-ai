"""Tests GUI du bloc CELIAPP 4A."""
import tkinter as tk

from src.comptaprivee import gui
from tests.test_gui_block2 import (
    application,
    racine,
    bouton,
    derniere_fenetre,
)
from tests.test_gui_pension_income_2025 import champ


def ouvrir_dialogue(app):
    app.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(app)
    bouton(fiscal, "Ajustements fiscaux").invoke()
    dialogue = derniere_fenetre(fiscal)
    return fiscal, dialogue


def _cocher(dialogue, nom):
    case = champ(dialogue, nom)
    if dialogue.getvar(case.cget("variable")) == 0:
        case.invoke()


def _remplir(entree, valeur):
    entree.delete(0, "end")
    entree.insert(0, valeur)


def test_gui_celiapp_4a_affiche_champs(application):
    fiscal, dialogue = ouvrir_dialogue(application)

    assert champ(dialogue, "deduction_celiapp").get() == ""
    assert champ(dialogue, "cotisations_celiapp_2025").get() == ""
    assert champ(dialogue, "droits_celiapp_confirmes").get() == ""
    assert champ(dialogue, "source_celiapp").get() == ""

    bouton(dialogue, "Fermer").invoke()
    fiscal.destroy()


def test_gui_celiapp_4a_modification_revoque_confirmations(application):
    app = application
    fiscal, dialogue = ouvrir_dialogue(app)

    for nom in (
        "confirmation_celiapp_comptable",
        "confirmation_celiapp_titulaire",
        "confirmation_celiapp_residence",
    ):
        _cocher(dialogue, nom)

    source = champ(dialogue, "source_celiapp")
    source.insert(0, "Annexe 15")
    app.update()

    for nom in (
        "confirmation_celiapp_comptable",
        "confirmation_celiapp_titulaire",
        "confirmation_celiapp_residence",
    ):
        case = champ(dialogue, nom)
        assert dialogue.getvar(case.cget("variable")) == 0

    bouton(dialogue, "Fermer").invoke()
    fiscal.destroy()


def test_gui_celiapp_4a_valide_et_resume_bouton(application):
    app = application
    fiscal, dialogue = ouvrir_dialogue(app)

    _remplir(champ(dialogue, "deduction_celiapp"), "5000")
    _remplir(champ(dialogue, "cotisations_celiapp_2025"), "6000")
    _remplir(champ(dialogue, "droits_celiapp_confirmes"), "8000")
    _remplir(
        champ(dialogue, "source_celiapp"),
        "Annexe 15 / relevé CELIAPP 2025",
    )

    for nom in (
        "confirmation_celiapp_comptable",
        "confirmation_celiapp_titulaire",
        "confirmation_celiapp_residence",
    ):
        _cocher(dialogue, nom)

    bouton(dialogue, "Valider et appliquer").invoke()
    assert not dialogue.winfo_exists(), app.messages_test

    ajustements = next(
        w for w in fiscal.winfo_children()
        if False
    ) if False else None
    del ajustements

    textes = []
    def parcourir(widget):
        for enfant in widget.winfo_children():
            if hasattr(enfant, "cget"):
                try:
                    texte = enfant.cget("text")
                except tk.TclError:
                    texte = ""
                if isinstance(texte, str):
                    textes.append(texte)
            parcourir(enfant)

    parcourir(fiscal)
    assert any(
        texte.startswith("Ajustements fiscaux —")
        and "CELIAPP" in texte
        for texte in textes
    )

    fiscal.destroy()
