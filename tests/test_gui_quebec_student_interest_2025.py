from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir, _cocher
from src.comptaprivee.tax_quebec_student_interest_2025 import CONFIRMATIONS_6B


def test_saisie_reouverture_calcul_et_revocation(application):
    application.ouvrir_agent_fiscal(); fiscal = derniere_fenetre(application)
    bouton(fiscal, "Intérêts étudiants Québec 2025 (6B)").invoke(); d = derniere_fenetre(fiscal)
    for nom, texte in (("interets_payes_2025", "1000"), ("solde_inutilise_1998_2024", "2000"),
                       ("reclamation_385", "1200"), ("source", "Avis Québec fictif et relevé 2025")):
        _remplir(champ(d, nom+"_6b"), texte)
    assert str(champ(d, "calcul_6b").cget("state")) == "readonly"
    assert "240.00" in champ(d, "calcul_6b").get() and "1800.00" in champ(d, "calcul_6b").get()
    for nom in CONFIRMATIONS_6B: _cocher(d, nom+"_6b")
    bouton(d, "Appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    bouton(fiscal, "Intérêts étudiants Québec 2025 (6B)").invoke(); d = derniere_fenetre(fiscal)
    assert champ(d, "reclamation_385_6b").get() == "1200"
    _remplir(champ(d, "reclamation_385_6b"), "0")
    assert "3000.00" in champ(d, "calcul_6b").get()
    for nom in CONFIRMATIONS_6B:
        assert not d.getvar(champ(d, nom+"_6b").cget("variable"))
    bouton(d, "Appliquer").invoke(); assert d.winfo_exists()
    bouton(d, "Effacer").invoke(); bouton(d, "Appliquer").invoke()
    assert not d.winfo_exists()
    fiscal.destroy()
