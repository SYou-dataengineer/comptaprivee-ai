from decimal import Decimal as D
import pytest

from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir, _cocher
from src.comptaprivee.tax_student_loan_interest_2025 import CONFIRMATIONS_5B


def ouvrir(app):
    app.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(app)
    bouton(fiscal, "Intérêts prêts étudiants 2025 (5B)").invoke()
    return fiscal, derniere_fenetre(fiscal)


def confirmer(dialogue):
    for nom in CONFIRMATIONS_5B:
        _cocher(dialogue, nom + "_5b")


def test_gui_champs_et_profil_vide(application):
    fiscal, dialogue = ouvrir(application)
    for nom in ["interets_payes_2025", "montant_reclame_31900", "source"] + [f"report_{a}" for a in range(2020, 2025)]:
        assert champ(dialogue, nom + "_5b").get() == ""
    bouton(dialogue, "Valider et appliquer").invoke()
    assert not dialogue.winfo_exists(), application.messages_test
    fiscal.destroy()


@pytest.mark.parametrize("nom", ["interets_payes_2025", "report_2020", "report_2024", "source", "montant_reclame_31900"])
def test_gui_modification_revoque_toutes_confirmations(application, nom):
    fiscal, dialogue = ouvrir(application)
    confirmer(dialogue)
    _remplir(champ(dialogue, nom + "_5b"), "100")
    for confirmation in CONFIRMATIONS_5B:
        case = champ(dialogue, confirmation + "_5b")
        assert dialogue.getvar(case.cget("variable")) == 0
    bouton(dialogue, "Fermer").invoke()
    fiscal.destroy()


def test_gui_validation_et_reouverture(application):
    fiscal, dialogue = ouvrir(application)
    _remplir(champ(dialogue, "interets_payes_2025_5b"), "1000")
    _remplir(champ(dialogue, "report_2020_5b"), "200")
    _remplir(champ(dialogue, "montant_reclame_31900_5b"), "500")
    _remplir(champ(dialogue, "source_5b"), "Paiements du parent apparenté, prêt au nom du contribuable")
    confirmer(dialogue)
    bouton(dialogue, "Valider et appliquer").invoke()
    assert not dialogue.winfo_exists(), application.messages_test
    bouton(fiscal, "Intérêts prêts étudiants 2025 (5B)").invoke()
    dialogue = derniere_fenetre(fiscal)
    assert D(champ(dialogue, "report_2020_5b").get()) == D(200)
    assert D(champ(dialogue, "montant_reclame_31900_5b").get()) == D(500)
    bouton(dialogue, "Effacer").invoke()
    assert champ(dialogue, "source_5b").get() == ""
    bouton(dialogue, "Valider et appliquer").invoke()
    assert not dialogue.winfo_exists()
    fiscal.destroy()


@pytest.mark.parametrize("montant", ["NaN", "Infinity", "-1", "texte"])
def test_gui_montant_invalide_garde_dialogue(application, montant):
    fiscal, dialogue = ouvrir(application)
    _remplir(champ(dialogue, "interets_payes_2025_5b"), montant)
    bouton(dialogue, "Valider et appliquer").invoke()
    assert dialogue.winfo_exists()
    assert application.messages_test[-1][0] == "Intérêts étudiants invalides"
    bouton(dialogue, "Fermer").invoke()
    fiscal.destroy()


def test_gui_tiers_non_apparente_refuse(application):
    fiscal, dialogue = ouvrir(application)
    _remplir(champ(dialogue, "interets_payes_2025_5b"), "100")
    _remplir(champ(dialogue, "source_5b"), "Pièce")
    confirmer(dialogue)
    champ(dialogue, "aucun_tiers_non_apparente_confirme_5b").invoke()
    bouton(dialogue, "Valider et appliquer").invoke()
    assert dialogue.winfo_exists()
    assert "tiers non apparenté" in application.messages_test[-1][1]
    bouton(dialogue, "Fermer").invoke()
    fiscal.destroy()
