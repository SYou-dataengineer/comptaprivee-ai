from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from tests.test_gui_caregiver_child_combination_2025 import cocher
from src.comptaprivee.tax_quebec_home_buyers_2025 import CONFIRMATIONS_6C


def test_saisie_reouverture_et_revocation(application):
    application.ouvrir_agent_fiscal(); fiscal = derniere_fenetre(application)
    bouton(fiscal, "Achat habitation Québec 2025 (6C)").invoke(); d = derniere_fenetre(fiscal)
    champ(d, "reclamer_6c").invoke()
    for nom, texte in (("date_acquisition", "2025-06-15"), ("reference_habitation", "Habitation fictive lot A"),
                       ("credit_demande_autres", "400"), ("source", "Acte et entente fictifs vérifiés")):
        _remplir(champ(d, nom+"_6c"), texte)
    for nom in CONFIRMATIONS_6C: cocher(champ(d, nom+"_6c"))
    bouton(d, "Appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    bouton(fiscal, "Achat habitation Québec 2025 (6C)").invoke(); d = derniere_fenetre(fiscal)
    assert champ(d, "credit_demande_autres_6c").get() == "400"
    _remplir(champ(d, "date_acquisition_6c"), "2025-07-01")
    for nom in CONFIRMATIONS_6C: assert not d.getvar(champ(d, nom+"_6c").cget("variable"))
    bouton(d, "Appliquer").invoke(); assert d.winfo_exists()
    bouton(d, "Effacer").invoke(); bouton(d, "Appliquer").invoke()
    assert not d.winfo_exists()
    fiscal.destroy()
