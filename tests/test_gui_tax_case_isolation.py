"""Un nouveau client ne doit hériter ni de faits ni d'approbations fiscales."""
from tkinter import ttk
import pytest
from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre, descendants
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from tests.test_gui_caregiver_child_combination_2025 import cocher
from src.comptaprivee.tax_quebec_career_extension_2025 import CONFIRMATIONS_6D


@pytest.mark.parametrize("nouveau_client", ["Client B fictif", ""])
def test_nouveau_client_efface_naissance_source_et_confirmations(application, nouveau_client):
    application.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(application)
    client = next(w for w in descendants(fiscal) if type(w) is ttk.Entry)
    _remplir(client, "Client A fictif")
    bouton(fiscal, "Initialiser le dossier fiscal").invoke()
    bouton(fiscal, "Prolongation carrière Québec 2025 (6D)").invoke()
    d = derniere_fenetre(fiscal)
    champ(d, "reclamer_6d").invoke()
    _remplir(champ(d, "naissance_6d"), "1960-12-31")
    _remplir(champ(d, "source_6d"), "Pièces fictives propres au client A")
    for nom in CONFIRMATIONS_6D:
        cocher(champ(d, nom + "_6d"))
    bouton(d, "Appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    _remplir(client, nouveau_client)
    bouton(fiscal, "Initialiser le dossier fiscal").invoke()
    assert application.dossier_fiscal_courant.client == (nouveau_client or "Client A fictif")
    bouton(fiscal, "Prolongation carrière Québec 2025 (6D)").invoke()
    d = derniere_fenetre(fiscal)
    # Une initialisation refusée doit laisser intact le dossier précédent.
    assert champ(d, "naissance_6d").get() == ("" if nouveau_client else "1960-12-31")
    assert champ(d, "source_6d").get() == ("" if nouveau_client else "Pièces fictives propres au client A")
    for nom in ("reclamer", *CONFIRMATIONS_6D):
        assert bool(d.getvar(champ(d, nom + "_6d").cget("variable"))) == (not nouveau_client)


def test_nouveau_client_ne_recupere_pas_le_report_etudiant(application):
    from tests.test_gui_other_deductions_2025 import _cocher
    from src.comptaprivee.tax_quebec_student_interest_2025 import CONFIRMATIONS_6B
    application.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(application)
    client = next(w for w in descendants(fiscal) if type(w) is ttk.Entry)
    _remplir(client, "Client A fictif")
    bouton(fiscal, "Initialiser le dossier fiscal").invoke()
    bouton(fiscal, "Intérêts étudiants Québec 2025 (6B)").invoke()
    d = derniere_fenetre(fiscal)
    _remplir(champ(d, "solde_inutilise_1998_2024_6b"), "2000")
    _remplir(champ(d, "source_6b"), "Report fictif propre au client A")
    for nom in CONFIRMATIONS_6B:
        _cocher(d, nom + "_6b")
    bouton(d, "Appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    _remplir(client, "Client B fictif")
    bouton(fiscal, "Initialiser le dossier fiscal").invoke()
    bouton(fiscal, "Intérêts étudiants Québec 2025 (6B)").invoke()
    d = derniere_fenetre(fiscal)
    assert champ(d, "solde_inutilise_1998_2024_6b").get() in ("", "0")
    assert champ(d, "source_6b").get() == ""
    for nom in CONFIRMATIONS_6B:
        assert not d.getvar(champ(d, nom + "_6b").cget("variable"))
