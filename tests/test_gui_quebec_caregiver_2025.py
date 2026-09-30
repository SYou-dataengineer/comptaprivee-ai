from tkinter import ttk
from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre, descendants
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from tests.test_gui_caregiver_child_combination_2025 import cocher
from src.comptaprivee.tax_quebec_caregiver_2025 import CONFIRMATIONS_6G


def saisir(application):
    application.ouvrir_agent_fiscal(); fiscal = derniere_fenetre(application)
    bouton(fiscal, "Personne aidante Québec 2025 (6G)").invoke(); d = derniere_fenetre(fiscal)
    champ(d, "reclamer_6g").invoke()
    _remplir(champ(d, "source_6g"), "Famille et avances fictives vérifiées")
    _remplir(champ(d, "avances_rl19_h_6g"), "8000")
    bouton(d, "Ajouter").invoke(); e = derniere_fenetre(d)
    for nom, valeur in (("reference", "personne-a"), ("nom", "Enfant A fictif"), ("naissance", "1950-01-01"),
                        ("debut", "2025-01-01"), ("fin", "2025-12-31"), ("adresse", "Adresse fictive Québec"),
                        ("revenu_net", "30000"), ("source", "Période, naissance et attestation Québec fictives")):
        _remplir(champ(e, nom+"_personne_6g"), valeur)
    bouton(e, "Enregistrer la personne").invoke()
    assert not e.winfo_exists(), application.messages_test
    for nom in CONFIRMATIONS_6G: cocher(champ(d, nom+"_6g"))
    bouton(d, "Appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    return fiscal


def test_personne_reouverture_modification_et_effacement(application):
    fiscal = saisir(application)
    bouton(fiscal, "Personne aidante Québec 2025 (6G)").invoke(); d = derniere_fenetre(fiscal)
    table = champ(d, "personnes_6g")
    assert len(table.get_children()) == 1
    assert champ(d, "avances_rl19_h_6g").get() == "8000"
    table.selection_set("0"); bouton(d, "Modifier").invoke(); e = derniere_fenetre(d)
    assert champ(e, "revenu_net_personne_6g").get() == "30000"
    _remplir(champ(e, "revenu_net_personne_6g"), "31000")
    bouton(e, "Enregistrer la personne").invoke()
    for nom in CONFIRMATIONS_6G:
        assert not d.getvar(champ(d, nom+"_6g").cget("variable"))
    bouton(d, "Appliquer").invoke(); assert d.winfo_exists()
    bouton(d, "Effacer").invoke(); bouton(d, "Appliquer").invoke()
    assert not d.winfo_exists()
    bouton(fiscal, "Personne aidante Québec 2025 (6G)").invoke(); d = derniere_fenetre(fiscal)
    assert not champ(d, "personnes_6g").get_children()
    assert champ(d, "avances_rl19_h_6g").get() == "0"


def test_nouveau_dossier_efface_personnes_et_avances(application):
    fiscal = saisir(application)
    client = next(w for w in descendants(fiscal) if type(w) is ttk.Entry)
    _remplir(client, "Nouveau client fictif")
    bouton(fiscal, "Initialiser le dossier fiscal").invoke()
    bouton(fiscal, "Personne aidante Québec 2025 (6G)").invoke(); d = derniere_fenetre(fiscal)
    assert not champ(d, "personnes_6g").get_children()
    assert champ(d, "source_6g").get() == ""
    assert champ(d, "avances_rl19_h_6g").get() == "0"
    for nom in ("reclamer", *CONFIRMATIONS_6G):
        assert not d.getvar(champ(d, nom+"_6g").cget("variable"))


def test_sauvegarde_et_rechargement_gui_du_profil(application):
    from tests.test_tax_estimation_2025 import _dossier_52000

    fiscal = saisir(application)
    application.dossier_fiscal_valide_courant = _dossier_52000()
    bouton(fiscal, "Enregistrer dossier").invoke()
    assert not application.erreurs_test, application.messages_test
    fiscal.destroy()

    application.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(application)
    bouton(fiscal, "Dossiers enregistrés").invoke()
    liste = derniere_fenetre(fiscal)
    bouton(liste, "Ouvrir le dossier").invoke()
    bouton(fiscal, "Personne aidante Québec 2025 (6G)").invoke()
    d = derniere_fenetre(fiscal)
    table = champ(d, "personnes_6g")
    assert len(table.get_children()) == 1
    assert "Enfant A fictif" in table.item(table.get_children()[0], "values")[0]
    assert champ(d, "avances_rl19_h_6g").get() == "8000"
    assert champ(d, "source_6g").get() == "Famille et avances fictives vérifiées"
    for nom in ("reclamer", *CONFIRMATIONS_6G):
        assert d.getvar(champ(d, nom+"_6g").cget("variable"))
