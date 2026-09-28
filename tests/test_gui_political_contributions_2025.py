import pytest
from tkinter import ttk
from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre, descendants
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from src.comptaprivee.tax_political_contributions_2025 import CONFIRMATIONS_POLITIQUES


def ouvrir(app):
    app.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(app)
    client = next(w for w in descendants(fiscal) if isinstance(w, ttk.Entry) and str(w.cget("width")) == "42")
    _remplir(client, "Client Test")
    bouton(fiscal, "Contributions politiques 2025 (5N)").invoke()
    return fiscal, derniere_fenetre(fiscal)


def remplir(d, montant="1400"):
    _remplir(champ(d, "source_5n"), "Validation fictive")
    for n, v in dict(date_paiement="2025-05-01", nom_donateur="Client Test", beneficiaire="Parti fictif",
        montant=montant, avantage="100", source="Reçu fictif").items():
        _remplir(champ(d, n + "_recu_5n"), v)
    champ(d, "donateur_recu_5n").set("contribuable")
    champ(d, "type_beneficiaire_recu_5n").set("parti")


def confirmer(d):
    for n in CONFIRMATIONS_POLITIQUES:
        champ(d, n + "_5n").invoke()


def test_ajouter_modifier_reouvrir_effacer(application):
    fiscal, d = ouvrir(application)
    remplir(d)
    bouton(d, "Enregistrer le reçu").invoke()
    confirmer(d)
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    bouton(fiscal, "Contributions politiques 2025 (5N)").invoke()
    d = derniere_fenetre(fiscal)
    assert all(d.getvar(champ(d, n + "_5n").cget("variable")) for n in CONFIRMATIONS_POLITIQUES)
    t = champ(d, "recus_5n")
    t.selection_set("0")
    bouton(d, "Modifier le reçu").invoke()
    assert champ(d, "montant_recu_5n").get() == "1400"
    _remplir(champ(d, "montant_recu_5n"), "1500")
    bouton(d, "Valider et appliquer").invoke()
    assert d.winfo_exists()
    bouton(d, "Enregistrer le reçu").invoke()
    confirmer(d)
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    bouton(fiscal, "Contributions politiques 2025 (5N)").invoke()
    d = derniere_fenetre(fiscal)
    bouton(d, "Effacer le profil").invoke()
    bouton(fiscal, "Contributions politiques 2025 (5N)").invoke()
    d = derniere_fenetre(fiscal)
    assert not champ(d, "recus_5n").get_children()
    bouton(d, "Fermer").invoke()
    fiscal.destroy()


@pytest.mark.parametrize("montant", ["NaN", "Infinity", "-1", "0", "1.001", "texte"])
def test_montant_invalide(application, montant):
    fiscal, d = ouvrir(application)
    remplir(d, montant)
    bouton(d, "Enregistrer le reçu").invoke()
    assert not champ(d, "recus_5n").get_children()
    assert application.messages_test[-1][0] == "Reçu politique invalide"
    bouton(d, "Fermer").invoke()
    fiscal.destroy()


@pytest.mark.parametrize("champ_modifie", ["source", "nom_conjoint"])
def test_revoquer_confirmations(application, champ_modifie):
    fiscal, d = ouvrir(application)
    remplir(d)
    bouton(d, "Enregistrer le reçu").invoke()
    confirmer(d)
    _remplir(champ(d, champ_modifie + "_5n"), "Modification")
    assert all(not d.getvar(champ(d, n + "_5n").cget("variable")) for n in CONFIRMATIONS_POLITIQUES)
    bouton(d, "Valider et appliquer").invoke()
    assert d.winfo_exists()
    bouton(d, "Fermer").invoke()
    fiscal.destroy()


def test_recu_conjoint_et_retrait(application):
    fiscal, d = ouvrir(application)
    remplir(d)
    champ(d, "donateur_recu_5n").set("conjoint")
    _remplir(champ(d, "nom_donateur_recu_5n"), "Conjoint fictif")
    bouton(d, "Enregistrer le reçu").invoke()
    confirmer(d)
    bouton(d, "Valider et appliquer").invoke()
    assert d.winfo_exists()  # Identité du conjoint obligatoire.
    _remplir(champ(d, "nom_conjoint_5n"), "Conjoint fictif")
    confirmer(d)
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    bouton(fiscal, "Contributions politiques 2025 (5N)").invoke()
    d = derniere_fenetre(fiscal)
    champ(d, "recus_5n").selection_set("0")
    bouton(d, "Retirer le reçu").invoke()
    assert not champ(d, "recus_5n").get_children()
    assert all(not d.getvar(champ(d, n + "_5n").cget("variable")) for n in CONFIRMATIONS_POLITIQUES)
    bouton(d, "Effacer le profil").invoke()
    fiscal.destroy()
