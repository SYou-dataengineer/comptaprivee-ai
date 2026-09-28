from tkinter import ttk
from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre, descendants
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from tests.test_gui_caregiver_child_combination_2025 import cocher
from src.comptaprivee.tax_quebec_childcare_2025 import CONFIRMATIONS_6F


def saisir(application):
    application.ouvrir_agent_fiscal(); fiscal = derniere_fenetre(application)
    bouton(fiscal, "Frais de garde Québec 2025 (6F)").invoke(); d = derniere_fenetre(fiscal)
    champ(d, "reclamer_6f").invoke()
    _remplir(champ(d, "source_6f"), "Famille et avances fictives vérifiées")
    _remplir(champ(d, "avances_rl19_c_6f"), "8000")
    bouton(d, "Ajouter").invoke(); e = derniere_fenetre(d)
    for nom, valeur in (("reference", "enfant-a"), ("nom", "Enfant A fictif"), ("naissance", "2020-01-01"),
                        ("frais_rl24_e", "10000"), ("source", "RL-24 et naissance fictifs")):
        _remplir(champ(e, nom+"_enfant_6f"), valeur)
    bouton(e, "Enregistrer l'enfant").invoke()
    assert not e.winfo_exists(), application.messages_test
    for nom in CONFIRMATIONS_6F: cocher(champ(d, nom+"_6f"))
    bouton(d, "Appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    return fiscal


def test_enfant_reouverture_modification_et_effacement(application):
    fiscal = saisir(application)
    bouton(fiscal, "Frais de garde Québec 2025 (6F)").invoke(); d = derniere_fenetre(fiscal)
    table = champ(d, "enfants_6f")
    assert len(table.get_children()) == 1
    assert champ(d, "avances_rl19_c_6f").get() == "8000"
    table.selection_set("0"); bouton(d, "Modifier").invoke(); e = derniere_fenetre(d)
    assert champ(e, "frais_rl24_e_enfant_6f").get() == "10000"
    _remplir(champ(e, "frais_rl24_e_enfant_6f"), "11000")
    bouton(e, "Enregistrer l'enfant").invoke()
    for nom in CONFIRMATIONS_6F:
        assert not d.getvar(champ(d, nom+"_6f").cget("variable"))
    bouton(d, "Appliquer").invoke(); assert d.winfo_exists()
    bouton(d, "Effacer").invoke(); bouton(d, "Appliquer").invoke()
    assert not d.winfo_exists()
    bouton(fiscal, "Frais de garde Québec 2025 (6F)").invoke(); d = derniere_fenetre(fiscal)
    assert not champ(d, "enfants_6f").get_children()
    assert champ(d, "avances_rl19_c_6f").get() == "0"


def test_nouveau_dossier_efface_enfants_et_avances(application):
    fiscal = saisir(application)
    client = next(w for w in descendants(fiscal) if type(w) is ttk.Entry)
    _remplir(client, "Nouveau client fictif")
    bouton(fiscal, "Initialiser le dossier fiscal").invoke()
    bouton(fiscal, "Frais de garde Québec 2025 (6F)").invoke(); d = derniere_fenetre(fiscal)
    assert not champ(d, "enfants_6f").get_children()
    assert champ(d, "source_6f").get() == ""
    assert champ(d, "avances_rl19_c_6f").get() == "0"
    for nom in ("reclamer", *CONFIRMATIONS_6F):
        assert not d.getvar(champ(d, nom+"_6f").cget("variable"))
