import tkinter as tk
import pytest
from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from tests.test_gui_medical_supplement_2025 import ouvrir
from src.comptaprivee.tax_medical_supplement_2025 import CONFIRMATIONS_SUPPLEMENT


def confirmer(d):
    for n in CONFIRMATIONS_SUPPLEMENT:
        if n != "sans_conjoint_ni_personne_charge":
            w = champ(d, n+"_5d")
            if not d.getvar(w.cget("variable")):
                w.invoke()
    w = champ(d, "donnees_familiales_verifiees_5t")
    if not d.getvar(w.cget("variable")):
        w.invoke()


def remplir(d):
    _remplir(champ(d, "age_fin_2025_5d"), "35")
    _remplir(champ(d, "source_5d"), "Dossier synthétique validé")
    champ(d, "reclamer_5d").invoke()
    champ(d, "mode_familial_5t").invoke()
    champ(d, "situation_conjugale_5t").set("conjoint")
    _remplir(champ(d, "nom_conjoint_5t"), "Conjoint fictif")
    _remplir(champ(d, "revenu_net_conjoint_5t"), "-100,00")
    _remplir(champ(d, "source_conjoint_5t"), "Déclaration synthétique et état civil")
    confirmer(d)


def test_saisie_reouverture_et_effacement(application):
    fiscal, d = ouvrir(application)
    remplir(d)
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    bouton(fiscal, "Frais médicaux 2025").invoke()
    d = derniere_fenetre(fiscal)
    assert champ(d, "nom_conjoint_5t").get() == "Conjoint fictif"
    assert champ(d, "revenu_net_conjoint_5t").get() == "-100.00"
    assert champ(d, "situation_conjugale_5t").get() == "conjoint"
    bouton(d, "Effacer").invoke()
    assert champ(d, "nom_conjoint_5t").get() == ""
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    fiscal.destroy()


@pytest.mark.parametrize("nom", ["nom_conjoint", "revenu_net_conjoint", "source_conjoint", "situation_conjugale", "mode_familial"])
def test_modification_revoque_confirmations(application, nom):
    fiscal, d = ouvrir(application)
    remplir(d)
    w = champ(d, nom+"_5t")
    if nom == "mode_familial":
        w.invoke()
    elif nom == "situation_conjugale":
        w.set("conjoint décédé")
    else:
        _remplir(w, "123")
    for n in CONFIRMATIONS_SUPPLEMENT:
        assert d.getvar(champ(d, n+"_5d").cget("variable")) == 0
    assert d.getvar(champ(d, "donnees_familiales_verifiees_5t").cget("variable")) == 0
    bouton(d, "Fermer").invoke()
    fiscal.destroy()


@pytest.mark.parametrize("revenu", ["NaN", "Infinity", "0.001", "invalide"])
def test_montant_invalide_non_applique(application, revenu):
    fiscal, d = ouvrir(application)
    remplir(d)
    _remplir(champ(d, "revenu_net_conjoint_5t"), revenu)
    confirmer(d)
    bouton(d, "Valider et appliquer").invoke()
    assert d.winfo_exists() and application.messages_test
    bouton(d, "Fermer").invoke()
    fiscal.destroy()
