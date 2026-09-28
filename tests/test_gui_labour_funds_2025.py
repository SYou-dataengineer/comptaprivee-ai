import pytest
from tkinter import ttk

from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre, descendants
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from src.comptaprivee.tax_labour_funds_2025 import CONFIRMATIONS_FONDS


def ouvrir(app):
    app.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(app)
    client = next(w for w in descendants(fiscal) if isinstance(w, ttk.Entry) and str(w.cget("width")) == "42")
    _remplir(client, "Client Test")
    bouton(fiscal, "Fonds de travailleurs 2025 (5O)").invoke()
    return fiscal, derniere_fenetre(fiscal)


def remplir(d, montant="5000"):
    for nom, valeur in dict(source="Validation fictive", contribuable_nom="Client Test",
            contribuable_naissance="1980-01-01", contribuable_revenu_emploi_entreprise="52000").items():
        _remplir(champ(d, nom + "_5o"), valeur)
    for nom, valeur in dict(date_acquisition="2025-05-01", montant=montant, source="RL-10 fictif").items():
        _remplir(champ(d, nom + "_acquisition_5o"), valeur)
    champ(d, "fonds_acquisition_5o").set("FTQ A")


def confirmer(d):
    for nom in CONFIRMATIONS_FONDS:
        champ(d, nom + "_5o").invoke()


def test_ajouter_modifier_reouvrir_effacer(application):
    fiscal, d = ouvrir(application)
    remplir(d)
    bouton(d, "Enregistrer l'acquisition").invoke()
    confirmer(d)
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    bouton(fiscal, "Fonds de travailleurs 2025 (5O)").invoke()
    d = derniere_fenetre(fiscal)
    assert all(d.getvar(champ(d, n + "_5o").cget("variable")) for n in CONFIRMATIONS_FONDS)
    assert champ(d, "contribuable_naissance_5o").get() == "1980-01-01"
    champ(d, "acquisitions_5o").selection_set("0")
    bouton(d, "Modifier l'acquisition").invoke()
    assert champ(d, "montant_acquisition_5o").get() == "5000"
    _remplir(champ(d, "montant_acquisition_5o"), "4000")
    bouton(d, "Valider et appliquer").invoke()
    assert d.winfo_exists()
    bouton(d, "Enregistrer l'acquisition").invoke()
    confirmer(d)
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    bouton(fiscal, "Fonds de travailleurs 2025 (5O)").invoke()
    d = derniere_fenetre(fiscal)
    bouton(d, "Effacer le profil").invoke()
    bouton(fiscal, "Fonds de travailleurs 2025 (5O)").invoke()
    d = derniere_fenetre(fiscal)
    assert not champ(d, "acquisitions_5o").get_children()
    assert champ(d, "contribuable_nom_5o").get() == ""
    bouton(d, "Fermer").invoke()
    fiscal.destroy()


@pytest.mark.parametrize("montant", ["NaN", "Infinity", "-1", "0", "1.001", "texte"])
def test_montant_invalide(application, montant):
    fiscal, d = ouvrir(application)
    remplir(d, montant)
    bouton(d, "Enregistrer l'acquisition").invoke()
    assert not champ(d, "acquisitions_5o").get_children()
    assert application.messages_test[-1][0] == "Acquisition invalide"
    bouton(d, "Fermer").invoke()
    fiscal.destroy()


@pytest.mark.parametrize("nom", ["source", "contribuable_naissance", "contribuable_revenu_emploi_entreprise"])
def test_revoquer_confirmations(application, nom):
    fiscal, d = ouvrir(application)
    remplir(d)
    bouton(d, "Enregistrer l'acquisition").invoke()
    confirmer(d)
    _remplir(champ(d, nom + "_5o"), "Modification")
    assert all(not d.getvar(champ(d, n + "_5o").cget("variable")) for n in CONFIRMATIONS_FONDS)
    bouton(d, "Valider et appliquer").invoke()
    assert d.winfo_exists()
    bouton(d, "Fermer").invoke()
    fiscal.destroy()


def test_situation_retraite_refusee_et_confirmation_revoquee(application):
    fiscal, d = ouvrir(application)
    remplir(d)
    _remplir(champ(d, "contribuable_revenu_emploi_entreprise_5o"), "3500")
    bouton(d, "Enregistrer l'acquisition").invoke()
    confirmer(d)
    champ(d, "contribuable_rente_retraite_5o").invoke()
    assert all(not d.getvar(champ(d, n + "_5o").cget("variable")) for n in CONFIRMATIONS_FONDS)
    confirmer(d)
    bouton(d, "Valider et appliquer").invoke()
    assert d.winfo_exists()
    assert "provincial" in str(application.messages_test[-1])
    bouton(d, "Fermer").invoke()
    fiscal.destroy()


def test_historique_2024_et_reservation_2026(application):
    fiscal, d = ouvrir(application)
    remplir(d)
    _remplir(champ(d, "date_acquisition_acquisition_5o"), "2025-03-01")
    _remplir(champ(d, "credit_utilise_2024_acquisition_5o"), "100")
    bouton(d, "Enregistrer l'acquisition").invoke()
    assert not champ(d, "acquisitions_5o").get_children()
    _remplir(champ(d, "source_2024_acquisition_5o"), "Déclaration 2024 cotisée")
    bouton(d, "Enregistrer l'acquisition").invoke()
    assert len(champ(d, "acquisitions_5o").get_children()) == 1
    remplir(d, "2000")
    _remplir(champ(d, "source_acquisition_5o"), "Second relevé fictif")
    _remplir(champ(d, "date_acquisition_acquisition_5o"), "2026-03-02")
    _remplir(champ(d, "cout_reserve_2026_acquisition_5o"), "1000")
    bouton(d, "Enregistrer l'acquisition").invoke()
    assert len(champ(d, "acquisitions_5o").get_children()) == 2
    confirmer(d)
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    fiscal.destroy()
