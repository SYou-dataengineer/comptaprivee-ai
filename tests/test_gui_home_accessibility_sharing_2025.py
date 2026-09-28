import tkinter as tk
from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre, descendants
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from tests.test_gui_caregiver_child_combination_2025 import cocher


def test_partage_plafond_reouverture_revocation(application):
    application.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(application)
    bouton(fiscal, "Accessibilité domicile 31285").invoke()
    d = derniere_fenetre(fiscal)
    for nom, texte in (("depenses_31285", "25000"), ("source_31285", "Factures fictives vérifiées"),
        ("reference_31285", "Logement fictif A"), ("autres_31285", "4000"),
        ("source_partage_31285", "Entente fictive A/B admissibles")):
        _remplir(champ(d, nom), texte)
    for w in descendants(d):
        if isinstance(w, tk.Checkbutton) and w.winfo_name() not in (
            "aucun_partage_de_la_demande_5aa", "admissible_ciph_5aa", "valide_par_comptable_5aa",
            "admissibles_31285", "unique_31285", "entente_31285"):
            cocher(w)
    assert str(champ(d, "resultat_31285").cget("state")) == "readonly"
    assert champ(d, "resultat_31285").get() == "16000"
    for nom in ("admissibles_31285", "unique_31285", "entente_31285", "valide_par_comptable_5aa"):
        cocher(champ(d, nom))
    bouton(d, "Appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    bouton(fiscal, "Accessibilité domicile 31285").invoke()
    d = derniere_fenetre(fiscal)
    assert champ(d, "resultat_31285").get() == "16000"
    _remplir(champ(d, "depenses_31285"), "12000")
    assert champ(d, "resultat_31285").get() == "8000"
    for nom in ("admissibles_31285", "unique_31285", "entente_31285", "valide_par_comptable_5aa"):
        assert not d.getvar(champ(d, nom).cget("variable"))
    bouton(d, "Annuler").invoke()
    fiscal.destroy()
