from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from tests.test_gui_caregiver_child_combination_2025 import cocher
from src.comptaprivee.tax_quebec_career_extension_2025 import CONFIRMATIONS_6D


def test_naissance_reouverture_et_revocation(application):
    application.ouvrir_agent_fiscal(); fiscal = derniere_fenetre(application)
    bouton(fiscal, "Prolongation carrière Québec 2025 (6D)").invoke(); d = derniere_fenetre(fiscal)
    champ(d, "reclamer_6d").invoke()
    _remplir(champ(d, "naissance_6d"), "1960-12-31")
    _remplir(champ(d, "source_6d"), "Date et emploi fictifs vérifiés")
    for nom in CONFIRMATIONS_6D: cocher(champ(d, nom+"_6d"))
    bouton(d, "Appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    bouton(fiscal, "Prolongation carrière Québec 2025 (6D)").invoke(); d = derniere_fenetre(fiscal)
    assert champ(d, "naissance_6d").get() == "1960-12-31"
    _remplir(champ(d, "naissance_6d"), "1961-01-01")
    for nom in CONFIRMATIONS_6D: assert not d.getvar(champ(d, nom+"_6d").cget("variable"))
    for nom in CONFIRMATIONS_6D: cocher(champ(d, nom+"_6d"))
    bouton(d, "Appliquer").invoke(); assert d.winfo_exists()
    assert "65 ans" in application.messages_test[-1][1]
    bouton(d, "Effacer").invoke(); bouton(d, "Appliquer").invoke()
    assert not d.winfo_exists()
    fiscal.destroy()
