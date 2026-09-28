import pytest
from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from src.comptaprivee.tax_workers_benefit_2025 import CONFIRMATIONS_ACT


def ouvrir(app):
    app.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(app)
    bouton(fiscal, "Allocation travailleurs 2025 (5E)").invoke()
    return fiscal, derniere_fenetre(fiscal)


def confirmer(d):
    for nom in CONFIRMATIONS_ACT:
        champ(d, nom + "_5e").invoke()


def remplir(d):
    for nom, valeur in (("age_fin_2025", "35"), ("source", "RC210 fictif et validation"), ("avances_rc210_case10", "1000")):
        _remplir(champ(d, nom + "_5e"), valeur)
    champ(d, "reclamer_base_5e").invoke()
    confirmer(d)


def test_gui_reouverture_effacer(application):
    fiscal, d = ouvrir(application)
    remplir(d)
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    bouton(fiscal, "Allocation travailleurs 2025 (5E)").invoke()
    d = derniere_fenetre(fiscal)
    assert champ(d, "avances_rc210_case10_5e").get() == "1000"
    assert d.getvar(champ(d, "reclamer_base_5e").cget("variable")) == 1
    bouton(d, "Effacer").invoke()
    assert champ(d, "source_5e").get() == ""
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists()
    fiscal.destroy()


@pytest.mark.parametrize("nom", ["age_fin_2025", "source", "avances_rc210_case10", "avances_rc210_case11", "reclamer_base", "reclamer_supplement"])
def test_gui_revoque_confirmations(application, nom):
    fiscal, d = ouvrir(application)
    remplir(d)
    if nom.startswith("reclamer"):
        champ(d, nom + "_5e").invoke()
    else:
        _remplir(champ(d, nom + "_5e"), "99")
    for confirmation in (*CONFIRMATIONS_ACT, "admissibilite_ciph_confirmee"):
        assert d.getvar(champ(d, confirmation + "_5e").cget("variable")) == 0
    bouton(d, "Fermer").invoke()
    fiscal.destroy()


def test_gui_supplement_sans_ciph_refuse(application):
    fiscal, d = ouvrir(application)
    remplir(d)
    champ(d, "reclamer_supplement_5e").invoke()
    confirmer(d)
    bouton(d, "Valider et appliquer").invoke()
    assert d.winfo_exists()
    assert "CIPH" in application.messages_test[-1][1]
    champ(d, "admissibilite_ciph_confirmee_5e").invoke()
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists()
    fiscal.destroy()


@pytest.mark.parametrize("valeur", ["NaN", "Infinity", "-1", "texte"])
def test_gui_rc210_invalide(application, valeur):
    fiscal, d = ouvrir(application)
    remplir(d)
    _remplir(champ(d, "avances_rc210_case10_5e"), valeur)
    confirmer(d)
    bouton(d, "Valider et appliquer").invoke()
    assert d.winfo_exists()
    assert application.messages_test[-1][0] == "ACT invalide"
    bouton(d, "Fermer").invoke()
    fiscal.destroy()
