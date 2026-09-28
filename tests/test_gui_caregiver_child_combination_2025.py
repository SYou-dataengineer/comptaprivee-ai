import tkinter as tk
from tkinter import ttk
from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre, descendants
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir


def cocher(w):
    if not w.getvar(w.cget("variable")):
        w.invoke()


def test_deux_dialogues_reouverture_et_revocation(application):
    application.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(application)
    bouton(fiscal, "Personne à charge fédérale 2025").invoke()
    d = derniere_fenetre(fiscal)
    entries = [w for w in descendants(d) if isinstance(w, ttk.Entry)]
    _remplir(entries[0], "51515")
    _remplir(entries[1], "4000")
    _remplir(champ(d, "reference_30400_5v"), "Enfant fictif A")
    _remplir(entries[-1], "Sources fictives 30400 et preuve médicale")
    cocher(champ(d, "infirmite_30400_5v"))
    for w in descendants(d):
        if isinstance(w, tk.Checkbutton) and w.cget("text") not in (
            "Aucune déficience physique ou mentale de l'enfant", "Validation comptable confirmée"):
            cocher(w)
    validation = next(w for w in descendants(d) if isinstance(w, tk.Checkbutton) and w.cget("text") == "Validation comptable confirmée")
    cocher(validation)
    bouton(d, "Appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    bouton(fiscal, "Personne à charge fédérale 2025").invoke()
    d = derniere_fenetre(fiscal)
    assert champ(d, "reference_30400_5v").get() == "Enfant fictif A"
    _remplir(champ(d, "reference_30400_5v"), "Enfant B")
    assert not d.getvar(champ(d, "preuve_30400_5v").cget("variable"))
    bouton(d, "Annuler").invoke()
    bouton(fiscal, "Aidant enfant fédéral 2025").invoke()
    d = derniere_fenetre(fiscal)
    entries = [w for w in descendants(d) if isinstance(w, ttk.Entry)]
    _remplir(entries[0], "Sources fictives 30500")
    _remplir(champ(d, "reference_30500_5v"), "Enfant fictif A")
    for w in descendants(d):
        if isinstance(w, tk.Checkbutton) and w.cget("text") not in (
            "Enfant avec ses deux parents pendant toute l'année 2025", "Validation comptable confirmée"):
            cocher(w)
    cocher(champ(d, "valide_par_comptable_5v"))
    bouton(d, "Appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    bouton(fiscal, "Aidant enfant fédéral 2025").invoke()
    d = derniere_fenetre(fiscal)
    assert champ(d, "reference_30500_5v").get() == "Enfant fictif A"
    _remplir(champ(d, "reference_30500_5v"), "Enfant B")
    assert not d.getvar(champ(d, "valide_par_comptable_5v").cget("variable"))
    assert not d.getvar(champ(d, "preuve_medicale_ou_t2201_confirmee_5v").cget("variable"))
    bouton(d, "Annuler").invoke()
    fiscal.destroy()
