import tkinter as tk
from tkinter import ttk

from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre, descendants
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from tests.test_gui_caregiver_child_combination_2025 import cocher
from src.comptaprivee.tax_quebec_volunteers_2025 import CONFIRMATIONS_390


TITRE = "Volontaires Québec 2025 / 390 (6L)"


def saisir(application):
    application.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(application)
    bouton(fiscal, TITRE).invoke()
    d = derniere_fenetre(fiscal)
    champ(d, "activer_390").invoke()
    _remplir(champ(d, "source_390"), "Faits 390 fictifs vérifiés")
    for nom in CONFIRMATIONS_390:
        cocher(champ(d, nom+"_390"))
    bouton(d, "Appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    return fiscal


def test_reouverture_modification_revoque_confirmations_et_effacement(application):
    fiscal = saisir(application)
    bouton(fiscal, TITRE).invoke()
    d = derniere_fenetre(fiscal)
    champ(d, "activer_390").invoke()
    for nom in CONFIRMATIONS_390:
        assert not d.getvar(champ(d, nom+"_390").cget("variable"))
    bouton(d, "Appliquer").invoke()
    assert d.winfo_exists()
    bouton(d, "Effacer").invoke()
    bouton(d, "Appliquer").invoke()
    assert not d.winfo_exists()
    bouton(fiscal, TITRE).invoke()
    d = derniere_fenetre(fiscal)
    assert champ(d, "source_390").get() == ""
    assert not d.getvar(champ(d, "activer_390").cget("variable"))


def test_nouveau_dossier_efface_tous_les_faits(application):
    fiscal = saisir(application)
    client = next(w for w in descendants(fiscal) if type(w) is ttk.Entry)
    _remplir(client, "Nouveau dossier fictif")
    bouton(fiscal, "Initialiser le dossier fiscal").invoke()
    bouton(fiscal, TITRE).invoke()
    d = derniere_fenetre(fiscal)
    assert champ(d, "source_390").get() == ""
    for nom in ("activer", *CONFIRMATIONS_390):
        assert not d.getvar(champ(d, nom+"_390").cget("variable"))


def test_sauvegarde_rechargement_gui(application):
    from tests.test_tax_estimation_2025 import _dossier_52000
    fiscal = saisir(application)
    application.dossier_fiscal_valide_courant = _dossier_52000()
    bouton(fiscal, "Enregistrer dossier").invoke()
    assert not application.erreurs_test, application.messages_test
    fiscal.destroy()
    application.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(application)
    bouton(fiscal, "Dossiers enregistrés").invoke()
    bouton(derniere_fenetre(fiscal), "Ouvrir le dossier").invoke()
    bouton(fiscal, TITRE).invoke()
    d = derniere_fenetre(fiscal)
    assert champ(d, "source_390").get() == "Faits 390 fictifs vérifiés"
    for nom in ("activer", *CONFIRMATIONS_390):
        assert d.getvar(champ(d, nom+"_390").cget("variable"))


def test_estimation_trace_export_et_invalidation(application, monkeypatch, tmp_path):
    from src.comptaprivee import gui, tax_case_storage
    from tests.test_tax_estimation_2025 import _dossier_52000
    from tests.test_tax_quebec_volunteers_2025 import profil
    from tests.test_tax_volunteers_2025 import profil as federal
    tax_case_storage.sauvegarder_dossier_fiscal(_dossier_52000(), benevoles=federal(), volontaires_quebec=profil())
    application.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(application)
    bouton(fiscal, "Dossiers enregistrés").invoke()
    bouton(derniere_fenetre(fiscal), "Ouvrir le dossier").invoke()
    bouton(fiscal, "Calculer l'estimation fiscale 2025").invoke()
    resultat = derniere_fenetre(fiscal)
    texte = next(w for w in descendants(resultat) if isinstance(w, tk.Text)).get("1.0", "end")
    assert "VOLONTAIRES QUÉBEC" in texte
    bouton(resultat, "Voir le détail du calcul").invoke()
    trace = derniere_fenetre(resultat)
    texte = next(w for w in descendants(trace) if isinstance(w, tk.Text)).get("1.0", "end")
    assert "Ligne 390" in texte
    trace.destroy()
    pdf = tmp_path / "390_gui.pdf"
    monkeypatch.setattr(gui.filedialog, "asksaveasfilename", lambda **kw: str(pdf))
    bouton(resultat, "Exporter le rapport fiscal en PDF").invoke()
    assert pdf.exists(), application.messages_test
    bouton(fiscal, TITRE).invoke()
    d = derniere_fenetre(fiscal)
    _remplir(champ(d, "source_390"), "Pièces fictives revues")
    for nom in CONFIRMATIONS_390:
        cocher(champ(d, nom+"_390"))
    bouton(d, "Appliquer").invoke()
    bouton(resultat, "Exporter le rapport fiscal en PDF").invoke()
    assert application.messages_test[-1][0] == "Estimation périmée"
