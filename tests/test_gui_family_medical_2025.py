from dataclasses import fields
import pytest
from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from tests.test_tax_family_medical_2025 import personne, depense
from src.comptaprivee.gui_family_medical_2025 import ouvrir_medical_familial_2025
from src.comptaprivee.tax_family_medical_2025 import FraisMedicauxFamilleFederaux2025, CONFIRMATIONS_MEDICALES_FAMILLE


def ouvrir(app, recus, profil=None):
    ouvrir_medical_familial_2025(app, profil or FraisMedicauxFamilleFederaux2025(), "Client", recus.append)
    return derniere_fenetre(app)


def remplir(d, objet):
    for f in fields(objet):
        w = champ(d, f.name + "_5s")
        v = getattr(objet, f.name)
        if f.type is bool:
            if bool(d.getvar(w.cget("variable"))) != v:
                w.invoke()
        elif f.name == "lien":
            w.set(v)
        else:
            _remplir(w, str(v))


def confirmer(d):
    for nom in CONFIRMATIONS_MEDICALES_FAMILLE:
        w = champ(d, nom + "_5s")
        if not d.getvar(w.cget("variable")):
            w.invoke()


def ajouter(d):
    for nom, valeur in (("debut_periode", "2024-07-01"), ("fin_periode", "2025-06-30")):
        _remplir(champ(d, nom + "_5s"), valeur)
    for nom, objet in (("Personnes", personne()), ("Reçus", depense())):
        bouton(d, "Ajouter — " + nom).invoke()
        enfant = derniere_fenetre(d)
        remplir(enfant, objet)
        bouton(enfant, "Enregistrer").invoke()
        assert not enfant.winfo_exists()
    confirmer(d)


def test_saisie_reouverture_revocation_effacement(application):
    recus = []
    d = ouvrir(application, recus)
    ajouter(d)
    bouton(d, "Appliquer les frais familiaux").invoke()
    assert not d.winfo_exists(), application.messages_test
    d = ouvrir(application, recus, recus[-1])
    assert champ(d, "personnes_5s").get_children() == ("0",)
    _remplir(champ(d, "fin_periode_5s"), "2025-07-01")
    assert all(not d.getvar(champ(d, n + "_5s").cget("variable")) for n in CONFIRMATIONS_MEDICALES_FAMILLE)
    bouton(d, "Appliquer les frais familiaux").invoke()
    assert d.winfo_exists()
    confirmer(d)
    champ(d, "reçus_5s").selection_set("0")
    bouton(d, "Modifier — Reçus").invoke()
    enfant = derniere_fenetre(d)
    _remplir(champ(enfant, "montant_paye_5s"), "3000")
    bouton(enfant, "Enregistrer").invoke()
    assert all(not d.getvar(champ(d, n + "_5s").cget("variable")) for n in CONFIRMATIONS_MEDICALES_FAMILLE)
    bouton(d, "Effacer les frais familiaux").invoke()
    assert recus[-1] == FraisMedicauxFamilleFederaux2025()


@pytest.mark.parametrize("montant", ["NaN", "Infinity", "-1", "0.001", "texte"])
def test_montant_refuse_dans_editeur(application, montant):
    d = ouvrir(application, [])
    bouton(d, "Ajouter — Reçus").invoke()
    enfant = derniere_fenetre(d)
    remplir(enfant, depense())
    _remplir(champ(enfant, "montant_paye_5s"), montant)
    bouton(enfant, "Enregistrer").invoke()
    assert enfant.winfo_exists() and application.messages_test
    enfant.destroy()
    d.destroy()


def test_bouton_agent_fiscal(application):
    application.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(application)
    bouton(fiscal, "Frais médicaux familiaux 2025 (5S)").invoke()
    d = derniere_fenetre(fiscal)
    bouton(d, "Effacer les frais familiaux").invoke()
    assert "Frais médicaux familiaux" in application.statut.get()
    fiscal.destroy()
