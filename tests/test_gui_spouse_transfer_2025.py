from tkinter import ttk

from src.comptaprivee import gui
from src.comptaprivee.tax_spouse_transfer_2025 import CONFIRMATIONS_TRANSFERT_CONJOINT
from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre, descendants
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from tests.test_tax_spouse_transfer_2025 import profil


def ouvrir(app):
    app.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(app)
    client = next(w for w in descendants(fiscal) if isinstance(w, ttk.Entry) and str(w.cget("width")) == "42")
    _remplir(client, "Client Test")
    bouton(fiscal, "Transfert conjoint 2025 (5K)").invoke()
    return fiscal, derniere_fenetre(fiscal)


def confirmer(d):
    for nom in CONFIRMATIONS_TRANSFERT_CONJOINT:
        champ(d, nom + "_5k").invoke()


def test_import_apercu_application_reouverture_et_retrait(application, tmp_path, monkeypatch):
    profil(tmp_path)
    monkeypatch.setattr(gui.filedialog, "askopenfilename", lambda **kw: str(tmp_path / "conjoint.json"))
    fiscal, d = ouvrir(application)
    bouton(d, "Importer le dossier du conjoint").invoke()
    confirmer(d)
    bouton(d, "Calculer l'annexe 2").invoke()
    assert "9028.00" in d.getvar(champ(d, "apercu_5k").cget("textvariable")), application.messages_test
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    bouton(fiscal, "Transfert conjoint 2025 (5K)").invoke()
    d = derniere_fenetre(fiscal)
    assert champ(d, "source_5k").get() == "conjoint.json"
    bouton(d, "Retirer le transfert").invoke()
    bouton(fiscal, "Transfert conjoint 2025 (5K)").invoke()
    d = derniere_fenetre(fiscal)
    assert champ(d, "source_5k").get() == ""
    bouton(d, "Fermer").invoke()
    fiscal.destroy()


def test_modification_source_revoque_confirmations(application, tmp_path, monkeypatch):
    profil(tmp_path)
    monkeypatch.setattr(gui.filedialog, "askopenfilename", lambda **kw: str(tmp_path / "conjoint.json"))
    fiscal, d = ouvrir(application)
    bouton(d, "Importer le dossier du conjoint").invoke()
    confirmer(d)
    _remplir(champ(d, "source_5k"), "Source corrigée")
    for nom in CONFIRMATIONS_TRANSFERT_CONJOINT:
        assert d.getvar(champ(d, nom + "_5k").cget("variable")) == 0
    bouton(d, "Valider et appliquer").invoke()
    assert d.winfo_exists()
    assert application.messages_test[-1][0] == "Transfert du conjoint invalide"
    bouton(d, "Fermer").invoke()
    fiscal.destroy()


def test_import_invalide_sans_remplacement_silencieux(application, tmp_path, monkeypatch):
    f = tmp_path / "invalide.json"
    f.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(gui.filedialog, "askopenfilename", lambda **kw: str(f))
    fiscal, d = ouvrir(application)
    bouton(d, "Importer le dossier du conjoint").invoke()
    assert application.messages_test[-1][0] == "Dossier du conjoint invalide"
    assert champ(d, "source_5k").get() == ""
    bouton(d, "Fermer").invoke()
    fiscal.destroy()
