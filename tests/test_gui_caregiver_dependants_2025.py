from tkinter import ttk
from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre, descendants
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from tests.test_gui_caregiver_child_combination_2025 import cocher
from tests.test_tax_caregiver_dependants_2025 import profil
from src.comptaprivee.gui_caregiver_dependants_2025 import ouvrir_personnes_30450_2025


def test_modification_revoque_et_persiste_fiches(application):
    resultats = []
    ouvrir_personnes_30450_2025(application, profil(), resultats.append)
    d = derniere_fenetre(application)
    table = champ(d, "personnes_5x")
    assert len(table.get_children()) == 2
    table.selection_set("0")
    bouton(d, "Modifier").invoke()
    ed = derniere_fenetre(d)
    _remplir(champ(ed, "revenu_net_personne_ligne_23600_5x"), "1000")
    for nom in ("valide_par_comptable", "preuve_medicale_ou_t2201_confirmee", "partage_30450_confirme"):
        assert not ed.getvar(champ(ed, nom + "_5x").cget("variable"))
    cocher(champ(ed, "preuve_medicale_ou_t2201_confirmee_5x"))
    cocher(champ(ed, "valide_par_comptable_5x"))
    bouton(ed, "Enregistrer la personne").invoke()
    assert not ed.winfo_exists(), application.messages_test
    assert not d.getvar(champ(d, "identites_5x").cget("variable"))
    assert not d.getvar(champ(d, "valide_5x").cget("variable"))
    cocher(champ(d, "identites_5x"))
    cocher(champ(d, "valide_5x"))
    bouton(d, "Appliquer les personnes").invoke()
    assert not d.winfo_exists(), application.messages_test
    assert resultats[0].personnes_detaillees[0].profil.revenu_net_personne_ligne_23600 == 1000
    assert resultats[0].personnes_detaillees[1] == profil().personnes_detaillees[1]


def test_bouton_fiscal_et_reouverture(application):
    application.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(application)
    bouton(fiscal, "Aidant 30450 fédéral 2025").invoke()
    ancien = derniere_fenetre(fiscal)
    bouton(ancien, "Plusieurs personnes — profil enregistré").invoke()
    d = derniere_fenetre(fiscal)
    bouton(d, "Ajouter").invoke()
    ed = derniere_fenetre(d)
    for nom, valeur in (("reference", "parent-x"), ("nom", "Parent fictif X"), ("naissance", "1950-01-02"),
        ("revenu_net_personne_ligne_23600", "10000"), ("source_personne", "Pièces fictives parent et revenu et preuve")):
        _remplir(champ(ed, nom + "_5x"), valeur)
    champ(ed, "lien_personne_5x").set("parent")
    for w in descendants(ed):
        if isinstance(w, ttk.Checkbutton) and w.winfo_name() not in (
            "valide_par_comptable_5x", "preuve_medicale_ou_t2201_confirmee_5x", "partage_30450_confirme_5x"):
            cocher(w)
    cocher(champ(ed, "preuve_medicale_ou_t2201_confirmee_5x"))
    cocher(champ(ed, "valide_par_comptable_5x"))
    bouton(ed, "Enregistrer la personne").invoke()
    assert not ed.winfo_exists(), application.messages_test
    cocher(champ(d, "identites_5x"))
    cocher(champ(d, "valide_5x"))
    bouton(d, "Appliquer les personnes").invoke()
    assert not d.winfo_exists(), application.messages_test
    bouton(fiscal, "Aidant 30450 fédéral 2025").invoke()
    d = derniere_fenetre(fiscal)
    assert len(champ(d, "personnes_5x").get_children()) == 1
    bouton(d, "Annuler").invoke()
    fiscal.destroy()


def test_conversion_profil_historique_preserve_les_faits(application):
    from tests.test_tax_federal_caregiver_other_dependant_2025 import _profil
    resultats = []
    ouvrir_personnes_30450_2025(application, _profil(), resultats.append)
    d = derniere_fenetre(application)
    table = champ(d, "personnes_5x")
    table.selection_set("0")
    bouton(d, "Modifier").invoke()
    ed = derniere_fenetre(d)
    assert champ(ed, "revenu_net_personne_ligne_23600_5x").get() == "25000"
    _remplir(champ(ed, "nom_5x"), "Parent fictif historique")
    _remplir(champ(ed, "naissance_5x"), "1950-01-01")
    cocher(champ(ed, "preuve_medicale_ou_t2201_confirmee_5x"))
    cocher(champ(ed, "valide_par_comptable_5x"))
    bouton(ed, "Enregistrer la personne").invoke()
    assert not ed.winfo_exists(), application.messages_test
    cocher(champ(d, "identites_5x"))
    cocher(champ(d, "valide_5x"))
    bouton(d, "Appliquer les personnes").invoke()
    assert resultats[0].personnes_detaillees[0].profil == _profil()
