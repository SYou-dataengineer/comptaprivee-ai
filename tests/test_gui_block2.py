"""Écrans réels du bloc 2, exclusivement avec des données fictives isolées."""

import inspect
import tkinter as tk
from tkinter import ttk
from decimal import Decimal

import pytest

from src.comptaprivee import gui, tax_case_storage
from src.comptaprivee.gui_layout import EcranResponsive
from src.comptaprivee.database import enregistrer_facture
from src.comptaprivee.facture_parser import DonneesFacture
from test_tax_case_storage import _dossier


def descendants(widget):
    for enfant in widget.winfo_children():
        yield enfant
        yield from descendants(enfant)


def bouton(widget, texte):
    return next(w for w in descendants(widget)
                if isinstance(w, ttk.Button) and w.cget("text") == texte)


def derniere_fenetre(parent):
    return [w for w in parent.winfo_children() if isinstance(w, tk.Toplevel)][-1]


@pytest.fixture(scope="module")
def racine():
    app = gui.ApplicationComptaPrivee()
    try:
        yield app
    finally:
        app.destroy()


@pytest.fixture
def application(tmp_path, monkeypatch, racine):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(tax_case_storage, "DOSSIERS_FISCAUX_DIR", tmp_path / "dossiers")
    monkeypatch.setattr(tax_case_storage, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(gui, "lister_dossiers_fiscaux",
                        lambda: tax_case_storage.lister_dossiers_fiscaux(tmp_path / "dossiers"))
    messages = []
    for nom in ("showinfo", "showwarning", "showerror"):
        monkeypatch.setattr(gui.messagebox, nom, lambda *a, **k: messages.append(a))
    monkeypatch.setattr(gui.messagebox, "askyesno", lambda *a, **k: False)
    enregistrer_facture(DonneesFacture(
        numero="DEMO-001", date="2025-01-15", fournisseur="Fournisseur fictif",
        client="Démonstration", sous_total=Decimal("100"), tps=Decimal("5"),
        tvq=Decimal("9.975"), total=Decimal("114.975")))
    callbacks = {}
    original = tk.Misc._register

    def enregistrer(widget, fonction, *args, **kwargs):
        callbacks[getattr(fonction, "__name__", "")] = fonction
        return original(widget, fonction, *args, **kwargs)

    monkeypatch.setattr(tk.Misc, "_register", enregistrer)
    app = racine
    app.dossier_fiscal_courant = None
    app.dossier_fiscal_valide_courant = None
    app.erreurs_test = []
    app.messages_test = messages
    app.callbacks_test = callbacks
    app.report_callback_exception = lambda *args: app.erreurs_test.append(args)
    try:
        yield app
        assert not app.erreurs_test
    finally:
        for enfant in list(app.winfo_children()):
            if isinstance(enfant, tk.Toplevel):
                enfant.destroy()
        app.update()


def verifier_ecran(app, fenetre):
    ecran = next(w for w in fenetre.winfo_children() if isinstance(w, EcranResponsive))
    for taille in ("600x400", "1000x700"):
        fenetre.geometry(taille)
        app.update()
        assert not app.erreurs_test
        actions = [w for w in ecran.actions.winfo_children() if isinstance(w, ttk.Button)]
        assert actions
        for action in actions:
            assert action.winfo_ismapped()
            assert action.winfo_width() >= action.winfo_reqwidth()
            assert action.winfo_height() >= action.winfo_reqheight()
            assert action.winfo_rootx() >= fenetre.winfo_rootx()
            assert action.winfo_rootx() + action.winfo_width() <= fenetre.winfo_rootx() + fenetre.winfo_width()
            assert action.winfo_rooty() + action.winfo_height() <= fenetre.winfo_rooty() + fenetre.winfo_height()
        for table in (w for w in descendants(ecran.corps) if isinstance(w, ttk.Treeview)):
            assert table.cget("xscrollcommand")
            assert table.cget("yscrollcommand")
            for colonne in table.cget("columns"):
                assert table.column(colonne, "width") >= table.column(colonne, "minwidth")
                assert not table.column(colonne, "stretch")
            table.xview_moveto(1)
            app.update()
            assert table.xview()[1] == pytest.approx(1)
        ecran.canvas.yview_moveto(1)
        app.update()
        assert ecran.canvas.yview()[1] == pytest.approx(1)
    return ecran


@pytest.mark.parametrize("methode", [
    None, "ouvrir_parametres", "configurer_societe_comptable", "ouvrir_historique",
    "ouvrir_historique_exports", "ouvrir_corbeille", "ouvrir_journal_audit",
    "ouvrir_a_verifier", "ouvrir_tableau_bord",
])
@pytest.mark.parametrize("echelle", [96 / 72, 144 / 72, 192 / 72])
def test_ecrans_petites_fenetres(application, methode, echelle):
    app = application
    app.tk.call("tk", "scaling", echelle)
    if methode:
        getattr(app, methode)()
    fenetre = derniere_fenetre(app) if methode else app
    verifier_ecran(app, fenetre)
    if methode == "ouvrir_parametres":
        onglets = next(w for w in descendants(fenetre) if isinstance(w, ttk.Notebook))
        for onglet in onglets.tabs():
            onglets.select(onglet)
            verifier_ecran(app, fenetre)


def ouvrir_dossier_test(app):
    dossier = _dossier()
    tax_case_storage.sauvegarder_dossier_fiscal(dossier)
    app.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(app)
    bouton(fiscal, "Dossiers enregistrés").invoke()
    liste = derniere_fenetre(fiscal)
    verifier_ecran(app, liste)
    bouton(liste, "Ouvrir le dossier").invoke()
    assert app.dossier_fiscal_valide_courant.client == dossier.client
    assert [v.valeur_validee for v in app.dossier_fiscal_valide_courant.donnees_validees] == [
        v.valeur_validee for v in dossier.donnees_validees]
    return fiscal


def test_dossier_recharge_validation_resultat_trace(application):
    app = application
    fiscal = ouvrir_dossier_test(app)
    extraire = app.callbacks_test["extraire_cases_documents_fiscaux"]
    afficher = inspect.getclosurevars(extraire).nonlocals["afficher_donnees_fiscales_extraites"]
    afficher()
    validation = derniere_fenetre(fiscal)
    verifier_ecran(app, validation)
    table = next(w for w in descendants(validation) if isinstance(w, ttk.Treeview))
    assert len(table.get_children()) == 15
    bouton(validation, "Fermer").invoke()
    bouton(fiscal, "Calculer l'estimation fiscale 2025").invoke()
    resultat = derniere_fenetre(fiscal)
    verifier_ecran(app, resultat)
    texte = next(w for w in descendants(resultat) if isinstance(w, tk.Text)).get("1.0", "end")
    assert "5\u00a0611,05" in texte
    bouton(resultat, "Voir le détail du calcul").invoke()
    trace = derniere_fenetre(resultat)
    verifier_ecran(app, trace)
    assert next(w for w in descendants(trace) if isinstance(w, tk.Text)).get("1.0", "end").strip()


def test_parametres_enregistrer_et_recharger(application):
    app = application
    app.ouvrir_parametres()
    fenetre = derniere_fenetre(app)
    combo = next(w for w in descendants(fenetre) if isinstance(w, ttk.Combobox)
                 and "USD" in w.cget("values"))
    combo.set("USD")
    bouton(fenetre, "Enregistrer").invoke()
    assert not fenetre.winfo_exists()
    app.ouvrir_parametres()
    fenetre = derniere_fenetre(app)
    combo = next(w for w in descendants(fenetre) if isinstance(w, ttk.Combobox)
                 and "USD" in w.cget("values"))
    assert combo.get() == "USD"


@pytest.mark.parametrize("libelle", ["Voir le graphique", "Évolution mensuelle",
    "TPS / TVQ mensuelles", "Contrôle anomalies", "Résumé comptable"])
def test_sous_fenetres_tableau_bord(application, libelle):
    app = application
    app.ouvrir_tableau_bord()
    tableau_bord = derniere_fenetre(app)
    bouton(tableau_bord, libelle).invoke()
    graphique = derniere_fenetre(tableau_bord)
    ecran = verifier_ecran(app, graphique)
    for toile in (w for w in ecran.corps.winfo_children() if isinstance(w, tk.Canvas)):
        assert toile.cget("xscrollcommand")
        assert toile.find_all()
        toile.xview_moveto(1)
        app.update()
        assert toile.xview()[1] == pytest.approx(1)


def test_historique_detail(application):
    app = application
    app.ouvrir_historique()
    historique = derniere_fenetre(app)
    table = next(w for w in descendants(historique) if isinstance(w, ttk.Treeview))
    table.selection_set(table.get_children()[0])
    bouton(historique, "Voir le détail").invoke()
    verifier_ecran(app, derniere_fenetre(historique))


def test_profil_invalide_puis_enregistrement_et_rechargement(application):
    app = application
    app.configurer_societe_comptable()
    profil = derniere_fenetre(app)
    bouton(profil, "Enregistrer").invoke()
    assert profil.winfo_exists()
    assert app.messages_test
    nom = next(w for w in descendants(profil) if isinstance(w, ttk.Entry))
    nom.insert(0, "Cabinet fictif pour tests")
    bouton(profil, "Enregistrer").invoke()
    assert not profil.winfo_exists()
    app.configurer_societe_comptable()
    profil = derniere_fenetre(app)
    assert next(w for w in descendants(profil) if isinstance(w, ttk.Entry)).get() == "Cabinet fictif pour tests"


def test_parametres_couleur_invalide_ne_sauvegarde_pas(application):
    app = application
    app.ouvrir_parametres()
    fenetre = derniere_fenetre(app)
    couleur = next(w for w in descendants(fenetre) if type(w) is ttk.Entry)
    couleur.delete(0, "end")
    couleur.insert(0, "invalide")
    bouton(fenetre, "Enregistrer").invoke()
    assert fenetre.winfo_exists()
    assert app.messages_test
    assert gui.lire_parametres().couleur_pdf == "#1A408C"


def test_corbeille_restauration_persistante(application, monkeypatch):
    from src.comptaprivee.database import lister_factures, mettre_facture_corbeille, lister_factures_corbeille
    app = application
    facture = lister_factures()[0]
    mettre_facture_corbeille(facture.identifiant)
    app.ouvrir_corbeille()
    fenetre = derniere_fenetre(app)
    table = next(w for w in descendants(fenetre) if isinstance(w, ttk.Treeview))
    table.selection_set(table.get_children()[0])
    monkeypatch.setattr(gui.messagebox, "askyesno", lambda *a, **k: True)
    bouton(fenetre, "Restaurer").invoke()
    assert not lister_factures_corbeille()
    assert lister_factures()[0].numero == "DEMO-001"
