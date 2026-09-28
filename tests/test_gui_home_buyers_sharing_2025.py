import tkinter as tk
from tkinter import ttk
from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre, descendants
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from tests.test_gui_caregiver_child_combination_2025 import cocher


def test_partage_calcul_automatique_reouverture_revocation(application):
    application.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(application)
    bouton(fiscal, "Achat habitation 31270").invoke()
    d = derniere_fenetre(fiscal)
    entrees = [w for w in descendants(d) if isinstance(w, ttk.Entry)]
    _remplir(entrees[1], "Acte fictif et critères vérifiés")
    _remplir(champ(d, "reference_31270"), "Habitation fictive A")
    _remplir(champ(d, "autres_31270"), "4000")
    _remplir(champ(d, "source_partage_31270"), "Entente fictive A/B")
    for w in descendants(d):
        if isinstance(w, tk.Checkbutton) and w.winfo_name() not in (
            "aucun_partage_du_montant_5z", "valide_par_comptable_5z", "admissibles_31270", "entente_31270"):
            cocher(w)
    assert str(champ(d, "montant_31270").cget("state")) == "readonly"
    assert champ(d, "montant_31270").get() == "6000"
    cocher(champ(d, "admissibles_31270"))
    cocher(champ(d, "entente_31270"))
    cocher(champ(d, "valide_par_comptable_5z"))
    bouton(d, "Appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    bouton(fiscal, "Achat habitation 31270").invoke()
    d = derniere_fenetre(fiscal)
    assert champ(d, "montant_31270").get() == "6000"
    _remplir(champ(d, "autres_31270"), "3500")
    assert champ(d, "montant_31270").get() == "6500"
    for nom in ("admissibles_31270", "entente_31270", "valide_par_comptable_5z"):
        assert not d.getvar(champ(d, nom).cget("variable"))
    bouton(d, "Annuler").invoke()
    fiscal.destroy()
