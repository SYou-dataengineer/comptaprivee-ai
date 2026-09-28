import tkinter as tk
from tkinter import ttk
from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre, descendants
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from tests.test_gui_caregiver_child_combination_2025 import cocher


def case(d, texte):
    return next(w for w in descendants(d) if isinstance(w, tk.Checkbutton) and w.cget("text") == texte)


def test_combinaison_deux_profils_reouverture_et_revocation(application):
    application.ouvrir_agent_fiscal()
    f = derniere_fenetre(application)
    bouton(f, "Personne vivant seule 2025").invoke()
    d = derniere_fenetre(f)
    _remplir(champ(d, "revenu_var_6a"), "50095")
    _remplir(champ(d, "source_var_6a"), "Bail fictif vérifié")
    for w in descendants(d):
        if isinstance(w, tk.Checkbutton) and w.winfo_name() not in (
            "additionnel_var_6a", "enfant_etudes_var_6a", "sans_allocation_dec_var_6a",
            "sans_age_retraite_var_6a", "validation_var_6a", "combinaison_6a"):
            cocher(w)
    cocher(champ(d, "combinaison_6a"))
    cocher(champ(d, "validation_var_6a"))
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    bouton(f, "Âge / retraite 2025").invoke()
    d = derniere_fenetre(f)
    _remplir(champ(d, "source_age_var_6a"), "Naissance fictive 1950 confirmée")
    # Le revenu net est la dernière entrée numérique de la grille âge/retraite.
    revenu = next(w for w in descendants(d) if isinstance(w, ttk.Entry) and w.grid_info().get("row") == 15)
    _remplir(revenu, "50095")
    for texte in ("Réclamer le montant en raison de l'âge", "Né avant le 1er janvier 1961",
                  "Aucun conjoint au 31 décembre 2025", "Résident du Québec et du Canada toute l'année 2025"):
        cocher(case(d, texte))
    cocher(champ(d, "combinaison_6a"))
    cocher(case(d, "Situation validée par le comptable"))
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    for titre, source in (("Âge / retraite 2025", "source_age_var_6a"), ("Personne vivant seule 2025", "source_var_6a")):
        bouton(f, titre).invoke()
        d = derniere_fenetre(f)
        assert d.getvar(champ(d, "combinaison_6a").cget("variable"))
        assert d.getvar(case(d, "Situation validée par le comptable").cget("variable"))
        _remplir(champ(d, source), "Justificatif changé")
        assert not d.getvar(champ(d, "combinaison_6a").cget("variable"))
        assert not d.getvar(case(d, "Situation validée par le comptable").cget("variable"))
        bouton(d, "Valider et appliquer").invoke()
        assert d.winfo_exists()
        bouton(d, "Fermer").invoke()
    f.destroy()
