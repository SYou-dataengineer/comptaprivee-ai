import tkinter as tk
from tkinter import ttk
from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre, descendants
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from tests.test_gui_caregiver_child_combination_2025 import cocher


def test_partage_reouverture_et_revocation(application):
    application.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(application)
    bouton(fiscal, "Aidant 30450 fédéral 2025").invoke()
    d = derniere_fenetre(fiscal)
    entries = [w for w in descendants(d) if isinstance(w, ttk.Entry) and not isinstance(w, ttk.Combobox)]
    _remplir(entries[0], "25000")
    _remplir(entries[1], "Revenu et preuve médicale fictifs")
    _remplir(champ(d, "reference_30450"), "Parent fictif A")
    _remplir(champ(d, "autres_30450"), "1500")
    _remplir(champ(d, "source_partage_30450"), "Entente fictive des soutiens")
    for w in descendants(d):
        if isinstance(w, tk.Checkbutton) and w.cget("text") not in (
            "Aucun partage de la réclamation 30450", "Validation comptable confirmée",
            "Entente de partage confirmée entre tous les soutiens"):
            cocher(w)
    cocher(champ(d, "entente_30450"))
    cocher(champ(d, "confirmation_30450_16"))
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    bouton(fiscal, "Aidant 30450 fédéral 2025").invoke()
    d = derniere_fenetre(fiscal)
    assert champ(d, "autres_30450").get() == "1500"
    _remplir(champ(d, "autres_30450"), "2000")
    for nom in ("entente_30450", "confirmation_30450_16", "confirmation_30450_15"):
        assert not d.getvar(champ(d, nom).cget("variable"))
    bouton(d, "Fermer").invoke()
    fiscal.destroy()
