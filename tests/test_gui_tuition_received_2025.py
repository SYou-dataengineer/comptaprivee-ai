import pytest
from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from src.comptaprivee.tax_tuition_received_2025 import CONFIRMATIONS_SCOLARITE_RECUE


def ouvrir(app):
    app.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(app)
    bouton(fiscal, "Scolarité reçue 2025 (5H)").invoke()
    return fiscal, derniere_fenetre(fiscal)


def confirmer(d):
    for nom in CONFIRMATIONS_SCOLARITE_RECUE:
        champ(d, nom + "_5h").invoke()


def remplir(d, reference="E1"):
    for nom, valeur in (("reference_etudiant", reference), ("nom_etudiant", "Étudiant fictif"),
            ("montant_certificat", "3000"), ("source", "Certificat fictif")):
        _remplir(champ(d, nom + "_5h"), valeur)
    champ(d, "relation_5h").set("parent")
    confirmer(d)


def test_gui_plusieurs_reouverture_modifier_retirer(application):
    fiscal, d = ouvrir(application)
    remplir(d)
    bouton(d, "Enregistrer la désignation").invoke()
    remplir(d, "E2")
    bouton(d, "Enregistrer la désignation").invoke()
    assert len(champ(d, "designations_5h").get_children()) == 2
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    bouton(fiscal, "Scolarité reçue 2025 (5H)").invoke()
    d = derniere_fenetre(fiscal)
    tableau = champ(d, "designations_5h")
    assert len(tableau.get_children()) == 2
    tableau.selection_set("0")
    bouton(d, "Modifier la sélection").invoke()
    assert champ(d, "reference_etudiant_5h").get() == "E1"
    _remplir(champ(d, "montant_certificat_5h"), "2000")
    confirmer(d)
    bouton(d, "Enregistrer la désignation").invoke()
    assert tableau.item("0", "values")[1] == "2000"
    for _ in range(2):
        tableau.selection_set("0")
        bouton(d, "Retirer la sélection").invoke()
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists()
    fiscal.destroy()


@pytest.mark.parametrize("nom", ["reference_etudiant", "nom_etudiant", "montant_certificat", "source", "relation"])
def test_modification_revoque_et_saisie_non_enregistree_refuse(application, nom):
    fiscal, d = ouvrir(application)
    remplir(d)
    if nom == "relation":
        champ(d, nom + "_5h").set("grand_parent")
    else:
        _remplir(champ(d, nom + "_5h"), "99")
    for confirmation in CONFIRMATIONS_SCOLARITE_RECUE:
        assert d.getvar(champ(d, confirmation + "_5h").cget("variable")) == 0
    bouton(d, "Valider et appliquer").invoke()
    assert d.winfo_exists()
    assert application.messages_test[-1][0] == "Désignation non enregistrée"
    bouton(d, "Fermer").invoke()
    fiscal.destroy()


@pytest.mark.parametrize("valeur", ["NaN", "Infinity", "-1", "5000.01", "texte"])
def test_saisie_invalide(application, valeur):
    fiscal, d = ouvrir(application)
    remplir(d)
    _remplir(champ(d, "montant_certificat_5h"), valeur)
    confirmer(d)
    bouton(d, "Enregistrer la désignation").invoke()
    assert not champ(d, "designations_5h").get_children()
    assert application.messages_test[-1][0] == "Désignation invalide"
    bouton(d, "Fermer").invoke()
    fiscal.destroy()
