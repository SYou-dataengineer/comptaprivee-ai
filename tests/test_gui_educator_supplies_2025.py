import pytest
from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from src.comptaprivee.tax_educator_supplies_2025 import CONFIRMATIONS_EDUCATEUR


def ouvrir(app):
    app.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(app)
    bouton(fiscal, "Fournitures éducateur 2025 (5P)").invoke()
    return fiscal, derniere_fenetre(fiscal)


def remplir(d, montant="1000"):
    for nom, valeur in dict(employeur="École fictive", source="Validation fictive", source_qualification="Brevet fictif").items():
        _remplir(champ(d, nom + "_5p"), valeur)
    champ(d, "province_emploi_5p").set("QC")
    for nom, valeur in dict(date_paiement="2025-09-01", description="Livres fictifs", montant=montant, source="Facture fictive").items():
        _remplir(champ(d, nom + "_depense_5p"), valeur)
    champ(d, "categorie_depense_5p").set("livres")


def confirmer(d):
    for nom in CONFIRMATIONS_EDUCATEUR:
        champ(d, nom + "_5p").invoke()


def test_ajouter_modifier_reouvrir_effacer(application):
    fiscal, d = ouvrir(application)
    remplir(d)
    bouton(d, "Enregistrer la dépense").invoke()
    confirmer(d)
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    bouton(fiscal, "Fournitures éducateur 2025 (5P)").invoke()
    d = derniere_fenetre(fiscal)
    assert all(d.getvar(champ(d, n + "_5p").cget("variable")) for n in CONFIRMATIONS_EDUCATEUR)
    champ(d, "depenses_5p").selection_set("0")
    bouton(d, "Modifier la dépense").invoke()
    _remplir(champ(d, "montant_depense_5p"), "900")
    bouton(d, "Valider et appliquer").invoke()
    assert d.winfo_exists()
    bouton(d, "Enregistrer la dépense").invoke()
    confirmer(d)
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    bouton(fiscal, "Fournitures éducateur 2025 (5P)").invoke()
    d = derniere_fenetre(fiscal)
    bouton(d, "Effacer le profil").invoke()
    bouton(fiscal, "Fournitures éducateur 2025 (5P)").invoke()
    d = derniere_fenetre(fiscal)
    assert not champ(d, "depenses_5p").get_children()
    assert champ(d, "employeur_5p").get() == ""
    bouton(d, "Fermer").invoke()
    fiscal.destroy()


@pytest.mark.parametrize("montant", ["NaN", "Infinity", "-1", "0", "1.001", "texte"])
def test_montants_invalides(application, montant):
    fiscal, d = ouvrir(application)
    remplir(d, montant)
    bouton(d, "Enregistrer la dépense").invoke()
    assert not champ(d, "depenses_5p").get_children()
    assert application.messages_test[-1][0] == "Dépense d'éducateur invalide"
    bouton(d, "Fermer").invoke()
    fiscal.destroy()


@pytest.mark.parametrize("nom", ["source", "employeur", "source_qualification"])
def test_modification_revoque_confirmations(application, nom):
    fiscal, d = ouvrir(application)
    remplir(d)
    bouton(d, "Enregistrer la dépense").invoke()
    confirmer(d)
    _remplir(champ(d, nom + "_5p"), "Modification")
    assert all(not d.getvar(champ(d, n + "_5p").cget("variable")) for n in CONFIRMATIONS_EDUCATEUR)
    bouton(d, "Valider et appliquer").invoke()
    assert d.winfo_exists()
    bouton(d, "Fermer").invoke()
    fiscal.destroy()


def test_attestation_et_ordinateur_fourni(application):
    fiscal, d = ouvrir(application)
    remplir(d)
    champ(d, "categorie_depense_5p").set("ordinateurs et tablettes")
    bouton(d, "Enregistrer la dépense").invoke()
    champ(d, "ordinateur_employeur_disponible_5p").invoke()
    confirmer(d)
    bouton(d, "Valider et appliquer").invoke()
    assert d.winfo_exists()
    champ(d, "ordinateur_employeur_disponible_5p").invoke()
    champ(d, "attestation_demandee_5p").invoke()
    champ(d, "attestation_fournie_5p").invoke()
    confirmer(d)
    bouton(d, "Valider et appliquer").invoke()
    assert d.winfo_exists()
    _remplir(champ(d, "source_attestation_5p"), "Attestation fictive")
    confirmer(d)
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    fiscal.destroy()
