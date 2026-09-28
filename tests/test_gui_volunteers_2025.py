import pytest
from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from src.comptaprivee.tax_volunteers_2025 import CONFIRMATIONS_BENEVOLES


def ouvrir(app):
    app.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(app)
    bouton(fiscal, "Services bénévoles 2025 (5L)").invoke()
    return fiscal, derniere_fenetre(fiscal)


def remplir(d, heures="200", organisme="Service fictif"):
    champ(d, "choix_5l").set("pompiers")
    _remplir(champ(d, "source_5l"), "Choix fictif")
    for nom, valeur in (("organisme", organisme), ("heures", heures), ("source", "Certificat fictif")):
        _remplir(champ(d, nom + "_activite_5l"), valeur)
    champ(d, "nature_activite_5l").set("pompiers")
    champ(d, "admissible_5l").invoke()


def confirmer(d):
    for nom in CONFIRMATIONS_BENEVOLES:
        champ(d, nom + "_5l").invoke()


def test_ajouter_modifier_reouvrir_et_effacer(application):
    fiscal, d = ouvrir(application)
    remplir(d)
    bouton(d, "Enregistrer l'activité").invoke()
    confirmer(d)
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    bouton(fiscal, "Services bénévoles 2025 (5L)").invoke()
    d = derniere_fenetre(fiscal)
    tableau = champ(d, "activites_5l")
    assert len(tableau.get_children()) == 1
    tableau.selection_set("0")
    bouton(d, "Modifier la sélection").invoke()
    assert champ(d, "heures_activite_5l").get() == "200"
    _remplir(champ(d, "heures_activite_5l"), "220")
    bouton(d, "Enregistrer l'activité").invoke()
    confirmer(d)
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    bouton(fiscal, "Services bénévoles 2025 (5L)").invoke()
    d = derniere_fenetre(fiscal)
    bouton(d, "Effacer le profil").invoke()
    bouton(fiscal, "Services bénévoles 2025 (5L)").invoke()
    d = derniere_fenetre(fiscal)
    assert not champ(d, "activites_5l").get_children()
    assert champ(d, "choix_5l").get() == ""
    bouton(d, "Fermer").invoke()
    fiscal.destroy()


@pytest.mark.parametrize("nom", ["source", "choix"])
def test_choix_ou_source_revoque(application, nom):
    fiscal, d = ouvrir(application)
    remplir(d)
    bouton(d, "Enregistrer l'activité").invoke()
    confirmer(d)
    if nom == "choix":
        champ(d, "choix_5l").set("exoneration")
    else:
        _remplir(champ(d, "source_5l"), "Autre source")
    for n in CONFIRMATIONS_BENEVOLES:
        assert d.getvar(champ(d, n + "_5l").cget("variable")) == 0
    bouton(d, "Valider et appliquer").invoke()
    assert d.winfo_exists()
    bouton(d, "Fermer").invoke()
    fiscal.destroy()


@pytest.mark.parametrize("heures", ["NaN", "Infinity", "-1", "0", "1.001", "texte"])
def test_heures_invalides(application, heures):
    fiscal, d = ouvrir(application)
    remplir(d, heures)
    bouton(d, "Enregistrer l'activité").invoke()
    assert not champ(d, "activites_5l").get_children()
    assert application.messages_test[-1][0] == "Activité bénévole invalide"
    bouton(d, "Fermer").invoke()
    fiscal.destroy()


def test_seuil_et_exoneration_sans_heures(application):
    fiscal, d = ouvrir(application)
    remplir(d, "199.99")
    bouton(d, "Enregistrer l'activité").invoke()
    confirmer(d)
    bouton(d, "Valider et appliquer").invoke()
    assert d.winfo_exists()
    assert "200 heures" in application.messages_test[-1][1]
    champ(d, "choix_5l").set("exoneration")
    confirmer(d)
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    fiscal.destroy()
