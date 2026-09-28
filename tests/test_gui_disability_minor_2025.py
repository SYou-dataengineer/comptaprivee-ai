import tkinter as tk
import pytest
from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre, descendants
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir


def case(d, prefixe):
    return next(w for w in descendants(d) if isinstance(w, tk.Checkbutton) and str(w.cget("text")).startswith(prefixe))


def ouvrir(app):
    app.ouvrir_agent_fiscal()
    f = derniere_fenetre(app)
    bouton(f, "Handicap / déficience 2025").invoke()
    return f, derniere_fenetre(f)


def remplir(d, soins="0"):
    case(d, "Réclamer le montant fédéral").invoke()
    # Les deux sources historiques n'ont pas de nom de widget.
    entrees = [w for w in descendants(d) if w.winfo_class() == "TEntry"]
    _remplir(entrees[0], "T2201 synthétique approuvé")
    _remplir(champ(d, "naissance_federale_5r"), "2010-02-03")
    _remplir(champ(d, "soins_reclames_federaux_5r"), soins)
    _remplir(champ(d, "source_soins_federaux_5r"), "Rapprochement synthétique des soins")
    for texte in ("Admissibilité validée", "Déficience d'au moins", "Crédit réclamé pour soi-même",
                  "CIPH / T2201", "Aucun conflit", "Aucun transfert"):
        case(d, texte).invoke()
    champ(d, "soins_federaux_valides_5r").invoke()


def test_mineur_reouverture_revocation(application):
    f, d = ouvrir(application)
    remplir(d)
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    bouton(f, "Handicap / déficience 2025").invoke()
    d = derniere_fenetre(f)
    assert champ(d, "naissance_federale_5r").get() == "2010-02-03"
    _remplir(champ(d, "soins_reclames_federaux_5r"), "4000")
    assert not d.getvar(case(d, "Admissibilité validée").cget("variable"))
    assert not d.getvar(champ(d, "soins_federaux_valides_5r").cget("variable"))
    bouton(d, "Valider et appliquer").invoke()
    assert d.winfo_exists()
    bouton(d, "Effacer").invoke()
    assert champ(d, "naissance_federale_5r").get() == ""
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists()
    f.destroy()


@pytest.mark.parametrize("soins", ["NaN", "-1", "1.001", "texte"])
def test_soins_invalides(application, soins):
    f, d = ouvrir(application)
    remplir(d, soins)
    bouton(d, "Valider et appliquer").invoke()
    assert d.winfo_exists()
    assert application.messages_test[-1][0] == "Crédit handicap / déficience invalide"
    bouton(d, "Fermer").invoke()
    f.destroy()
