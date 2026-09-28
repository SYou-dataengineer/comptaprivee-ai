import pytest
from tkinter import ttk
from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre, descendants
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from tests.test_gui_caregiver_child_combination_2025 import cocher
from tests.test_tax_caregiver_children_2025 import profil
from tests.test_tax_federal_caregiver_child_integration_2025 import _profil_aidant_enfant
from src.comptaprivee.gui_caregiver_children_2025 import ouvrir_enfants_30500_2025


def test_modification_et_revocation(application):
    resultats = []
    ouvrir_enfants_30500_2025(application, profil(), resultats.append)
    d = derniere_fenetre(application)
    table = champ(d, "enfants_5y")
    assert len(table.get_children()) == 2
    table.selection_set("0")
    bouton(d, "Modifier").invoke()
    ed = derniere_fenetre(d)
    _remplir(champ(ed, "source_enfant_5y"), "Nouvelle pièce fictive")
    assert not ed.getvar(champ(ed, "valide_par_comptable_5y").cget("variable"))
    assert not ed.getvar(champ(ed, "preuve_medicale_ou_t2201_confirmee_5y").cget("variable"))
    cocher(champ(ed, "preuve_medicale_ou_t2201_confirmee_5y"))
    cocher(champ(ed, "valide_par_comptable_5y"))
    bouton(ed, "Enregistrer l’enfant").invoke()
    assert not ed.winfo_exists(), application.messages_test
    assert not d.getvar(champ(d, "identites_5y").cget("variable"))
    cocher(champ(d, "identites_5y"))
    cocher(champ(d, "valide_5y"))
    bouton(d, "Appliquer les enfants").invoke()
    assert resultats[0].enfants_detailles[0].profil.source_enfant == "Nouvelle pièce fictive"
    assert resultats[0].enfants_detailles[1] == profil().enfants_detailles[1]


def test_integration_bouton_et_reouverture(application):
    application.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(application)
    bouton(fiscal, "Aidant enfant fédéral 2025").invoke()
    ancien = derniere_fenetre(fiscal)
    bouton(ancien, "Plusieurs enfants — profil enregistré").invoke()
    d = derniere_fenetre(fiscal)
    bouton(d, "Ajouter").invoke()
    ed = derniere_fenetre(d)
    for nom, valeur in (("reference", "enfant-x"), ("nom", "Enfant fictif X"), ("naissance", "2015-01-01"),
        ("source_enfant", "Pièces fictives et preuve médicale")):
        _remplir(champ(ed, nom + "_5y"), valeur)
    for w in descendants(ed):
        if isinstance(w, ttk.Checkbutton) and w.winfo_name() not in ("valide_par_comptable_5y", "preuve_medicale_ou_t2201_confirmee_5y"):
            cocher(w)
    cocher(champ(ed, "preuve_medicale_ou_t2201_confirmee_5y"))
    cocher(champ(ed, "valide_par_comptable_5y"))
    bouton(ed, "Enregistrer l’enfant").invoke()
    assert not ed.winfo_exists(), application.messages_test
    cocher(champ(d, "identites_5y"))
    cocher(champ(d, "valide_5y"))
    bouton(d, "Appliquer les enfants").invoke()
    assert not d.winfo_exists(), application.messages_test
    bouton(fiscal, "Aidant enfant fédéral 2025").invoke()
    d = derniere_fenetre(fiscal)
    assert len(champ(d, "enfants_5y").get_children()) == 1
    bouton(d, "Annuler").invoke()
    fiscal.destroy()


def test_conversion_historique_et_refus_conversion_5v(application):
    resultats = []
    p = _profil_aidant_enfant()
    ouvrir_enfants_30500_2025(application, p, resultats.append)
    d = derniere_fenetre(application)
    champ(d, "enfants_5y").selection_set("0")
    bouton(d, "Modifier").invoke()
    ed = derniere_fenetre(d)
    assert champ(ed, "source_enfant_5y").get() == p.source_enfant
    _remplir(champ(ed, "nom_5y"), "Enfant fictif historique")
    _remplir(champ(ed, "naissance_5y"), "2015-01-01")
    cocher(champ(ed, "preuve_medicale_ou_t2201_confirmee_5y"))
    cocher(champ(ed, "valide_par_comptable_5y"))
    bouton(ed, "Enregistrer l’enfant").invoke()
    assert not ed.winfo_exists(), application.messages_test
    cocher(champ(d, "identites_5y"))
    cocher(champ(d, "valide_5y"))
    bouton(d, "Appliquer les enfants").invoke()
    assert resultats[0].enfants_detailles[0].profil == p
    p5v = _profil_aidant_enfant(enfant_reclame_30400=True, reference_enfant="enfant-a", enfant_avec_deux_parents_toute_annee=False)
    with pytest.raises(ValueError, match="reste dans le dialogue individuel"):
        ouvrir_enfants_30500_2025(application, p5v, resultats.append)
