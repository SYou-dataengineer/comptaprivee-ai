import pytest
from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from src.comptaprivee.tax_adoption_2025 import CONFIRMATIONS_ADOPTION


def ouvrir(app):
    app.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(app)
    bouton(fiscal, "Frais d'adoption 2025 (5M)").invoke()
    return fiscal, derniere_fenetre(fiscal)


def remplir_enfant(e):
    for n, v in dict(nom="Enfant fictif", naissance="2015-01-01", inscription="2024-01-01",
        ordonnance="2025-01-01", residence_permanente="2025-02-01", source="Pièces fictives").items():
        _remplir(champ(e, n + "_enfant_5m"), v)


def remplir_depense(e, montant="10000"):
    for n, v in dict(date_engagement="2024-12-01", montant=montant, source="Facture fictive").items():
        _remplir(champ(e, n + "_depense_5m"), v)
    champ(e, "categorie_depense_5m").set("agence")


def confirmer(d):
    for n in CONFIRMATIONS_ADOPTION:
        champ(d, n + "_5m").invoke()


def test_ajout_modification_reouverture_effacement(application):
    fiscal, d = ouvrir(application)
    bouton(d, "Ajouter un enfant").invoke()
    e = derniere_fenetre(d)
    remplir_enfant(e)
    remplir_depense(e)
    bouton(e, "Enregistrer la dépense").invoke()
    assert len(champ(e, "depenses_5m").get_children()) == 1, application.messages_test
    bouton(e, "Enregistrer l'enfant").invoke()
    assert not e.winfo_exists(), application.messages_test
    confirmer(d)
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    bouton(fiscal, "Frais d'adoption 2025 (5M)").invoke()
    d = derniere_fenetre(fiscal)
    t = champ(d, "enfants_5m")
    t.selection_set("0")
    bouton(d, "Modifier l'enfant").invoke()
    e = derniere_fenetre(d)
    assert champ(e, "nom_enfant_5m").get() == "Enfant fictif"
    _remplir(champ(e, "part_pourcentage_enfant_5m"), "40")
    assert all(d.getvar(champ(d, n + "_5m").cget("variable")) == 0 for n in CONFIRMATIONS_ADOPTION)
    frais = champ(e, "depenses_5m")
    frais.selection_set("0")
    bouton(e, "Modifier la dépense").invoke()
    _remplir(champ(e, "montant_depense_5m"), "12000")
    bouton(e, "Enregistrer l'enfant").invoke()
    assert e.winfo_exists()  # Une édition de dépense non enregistrée ne doit pas disparaître.
    bouton(e, "Enregistrer la dépense").invoke()
    bouton(e, "Enregistrer l'enfant").invoke()
    confirmer(d)
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    bouton(fiscal, "Frais d'adoption 2025 (5M)").invoke()
    d = derniere_fenetre(fiscal)
    assert champ(d, "enfants_5m").item("0", "values")[1] == "40"
    bouton(d, "Effacer le profil").invoke()
    bouton(fiscal, "Frais d'adoption 2025 (5M)").invoke()
    d = derniere_fenetre(fiscal)
    assert not champ(d, "enfants_5m").get_children()
    bouton(d, "Fermer").invoke()
    fiscal.destroy()


@pytest.mark.parametrize("montant", ["NaN", "Infinity", "-1", "0", "1.001", "texte"])
def test_frais_invalides(application, montant):
    fiscal, d = ouvrir(application)
    bouton(d, "Ajouter un enfant").invoke()
    e = derniere_fenetre(d)
    remplir_enfant(e)
    remplir_depense(e, montant)
    bouton(e, "Enregistrer la dépense").invoke()
    assert not champ(e, "depenses_5m").get_children()
    assert application.messages_test[-1][0] == "Dépense d'adoption invalide"
    bouton(e, "Annuler").invoke()
    bouton(d, "Fermer").invoke()
    fiscal.destroy()


def test_retirer_depense_enfant_et_confirmation_obligatoire(application):
    fiscal, d = ouvrir(application)
    bouton(d, "Ajouter un enfant").invoke()
    e = derniere_fenetre(d)
    remplir_enfant(e)
    remplir_depense(e)
    bouton(e, "Enregistrer la dépense").invoke()
    champ(e, "depenses_5m").selection_set("0")
    bouton(e, "Retirer la dépense").invoke()
    bouton(e, "Enregistrer l'enfant").invoke()
    assert e.winfo_exists()
    remplir_depense(e)
    bouton(e, "Enregistrer la dépense").invoke()
    bouton(e, "Enregistrer l'enfant").invoke()
    bouton(d, "Valider et appliquer").invoke()
    assert d.winfo_exists()
    champ(d, "enfants_5m").selection_set("0")
    bouton(d, "Retirer l'enfant").invoke()
    assert not champ(d, "enfants_5m").get_children()
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists()
    fiscal.destroy()
