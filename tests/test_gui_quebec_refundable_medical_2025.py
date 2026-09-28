from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from tests.test_gui_caregiver_child_combination_2025 import cocher
from src.comptaprivee.tax_quebec_refundable_medical_2025 import CONFIRMATIONS_6E


def test_naissance_reouverture_et_revocation(application):
    application.ouvrir_agent_fiscal(); fiscal = derniere_fenetre(application)
    bouton(fiscal, "Crédit médical remboursable Québec 2025 (6E)").invoke(); d = derniere_fenetre(fiscal)
    champ(d, "reclamer_6e").invoke()
    _remplir(champ(d, "naissance_6e"), "2007-12-31")
    _remplir(champ(d, "source_6e"), "Date et emploi fictifs vérifiés")
    for nom in CONFIRMATIONS_6E: cocher(champ(d, nom+"_6e"))
    bouton(d, "Appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    bouton(fiscal, "Crédit médical remboursable Québec 2025 (6E)").invoke(); d = derniere_fenetre(fiscal)
    assert champ(d, "naissance_6e").get() == "2007-12-31"
    _remplir(champ(d, "naissance_6e"), "2008-01-01")
    for nom in CONFIRMATIONS_6E: assert not d.getvar(champ(d, nom+"_6e").cget("variable"))
    for nom in CONFIRMATIONS_6E: cocher(champ(d, nom+"_6e"))
    bouton(d, "Appliquer").invoke(); assert d.winfo_exists()
    assert "18 ans" in application.messages_test[-1][1]
    bouton(d, "Effacer").invoke(); bouton(d, "Appliquer").invoke()
    assert not d.winfo_exists()
    fiscal.destroy()
