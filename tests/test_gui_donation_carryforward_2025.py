import pytest
from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from src.comptaprivee.tax_donation_carryforward_2025 import CONFIRMATIONS_REPORTS_DONS


def ouvrir(app):
    app.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(app)
    bouton(fiscal, "Ajustements fiscaux").invoke()
    return fiscal, derniere_fenetre(fiscal)


def confirmer(d):
    for nom in CONFIRMATIONS_REPORTS_DONS:
        champ(d, nom + "_5i").invoke()


def remplir(d):
    for nom, valeur in (("montant_reclame", "500"), ("source", "Choix fictif"),
                        ("solde_2020", "1000"), ("source_2020", "Reçus fictifs")):
        _remplir(champ(d, nom + "_5i"), valeur)
    champ(d, "activer_5i").invoke()
    confirmer(d)


def test_report_seul_reouverture_effacer(application):
    fiscal, d = ouvrir(application)
    remplir(d)
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    bouton(fiscal, "Ajustements fiscaux").invoke()
    d = derniere_fenetre(fiscal)
    assert champ(d, "solde_2020_5i").get() == "1000"
    assert champ(d, "montant_reclame_5i").get() == "500"
    bouton(d, "Effacer").invoke()
    assert champ(d, "solde_2020_5i").get() == ""
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists()
    fiscal.destroy()


@pytest.mark.parametrize("nom", ["montant_reclame", "source", "solde_2020", "source_2020", "activer"])
def test_modification_revoque(application, nom):
    fiscal, d = ouvrir(application)
    remplir(d)
    if nom == "activer":
        champ(d, "activer_5i").invoke()
    else:
        _remplir(champ(d, nom + "_5i"), "99")
    for confirmation in CONFIRMATIONS_REPORTS_DONS:
        assert d.getvar(champ(d, confirmation + "_5i").cget("variable")) == 0
    bouton(d, "Fermer").invoke()
    fiscal.destroy()


@pytest.mark.parametrize("valeur", ["NaN", "-1", "Infinity", "1001", "texte"])
def test_choix_invalide_refuse(application, valeur):
    fiscal, d = ouvrir(application)
    remplir(d)
    _remplir(champ(d, "montant_reclame_5i"), valeur)
    confirmer(d)
    bouton(d, "Valider et appliquer").invoke()
    assert d.winfo_exists()
    assert application.messages_test[-1][0] == "Ajustements fiscaux invalides"
    bouton(d, "Fermer").invoke()
    fiscal.destroy()


def test_modification_don_courant_revoque_reports(application):
    from tkinter import ttk
    from tests.test_gui_block2 import descendants
    fiscal, d = ouvrir(application)
    remplir(d)
    entree = next(w for w in descendants(d) if isinstance(w, ttk.Entry) and w.grid_info().get("row") == 18)
    _remplir(entree, "1000")
    for confirmation in CONFIRMATIONS_REPORTS_DONS:
        assert d.getvar(champ(d, confirmation + "_5i").cget("variable")) == 0
    bouton(d, "Valider et appliquer").invoke()
    assert d.winfo_exists()
    bouton(d, "Fermer").invoke()
    fiscal.destroy()
