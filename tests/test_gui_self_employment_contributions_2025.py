import tkinter as tk
from tkinter import ttk

from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre, descendants
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from tests.test_gui_caregiver_child_combination_2025 import cocher
from tests.test_gui_self_employment_2025 import ouvrir, TITRE as TITRE_7B
from src.comptaprivee.tax_self_employment_contributions_2025 import CONFIRMATIONS_7C
from src.comptaprivee.tax_self_employment_2025 import CONFIRMATIONS_7B

TITRE = 'Cotisations autonomes / annuel 2025 (7C)'


def activer(application, fiscal):
    bouton(fiscal, TITRE).invoke()
    d = derniere_fenetre(fiscal)
    cocher(champ(d, 'activer_7c'))
    _remplir(champ(d, 'naissance_7c'), '1980-01-01')
    _remplir(champ(d, 'source_7c'), 'Audit fictif')
    for nom in CONFIRMATIONS_7C:
        cocher(champ(d, nom + '_7c'))
    bouton(d, 'Appliquer').invoke()
    assert not d.winfo_exists(), application.messages_test
    assert application.dossier_fiscal_valide_courant.profil_cotisations_autonomes.activer


def test_gui_annuel_pdf_persistance_reset(application, monkeypatch, tmp_path):
    from src.comptaprivee import gui
    fiscal = ouvrir(application)
    activer(application, fiscal)
    bouton(fiscal, "Calculer l'estimation fiscale 2025").invoke()
    resultat = derniere_fenetre(fiscal)
    texte = next(w for w in descendants(resultat) if isinstance(w, tk.Text)).get('1.0', 'end')
    assert '445' in texte and '22300' in texte and '8880.60' in texte
    pdf = tmp_path / 'annuel.pdf'
    monkeypatch.setattr(gui.filedialog, 'asksaveasfilename', lambda **kw: str(pdf))
    bouton(resultat, 'Exporter le rapport fiscal en PDF').invoke()
    assert pdf.exists(), application.messages_test
    bouton(fiscal, 'Enregistrer dossier').invoke()
    fiscal.destroy()
    application.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(application)
    bouton(fiscal, 'Dossiers enregistrés').invoke()
    bouton(derniere_fenetre(fiscal), 'Ouvrir le dossier').invoke()
    assert application.dossier_fiscal_valide_courant.profil_cotisations_autonomes.activer
    bouton(fiscal, TITRE).invoke()
    d = derniere_fenetre(fiscal)
    _remplir(champ(d, 'source_7c'), 'Nouvel audit fictif')
    for nom in CONFIRMATIONS_7C:
        assert not d.getvar(champ(d, nom + '_7c').cget('variable'))
    bouton(d, 'Appliquer').invoke()
    assert d.winfo_exists()
    assert application.messages_test[-1][0] == 'Profil 7C invalide'
    bouton(d, 'Fermer').invoke()
    client = next(w for w in descendants(fiscal) if type(w) is ttk.Entry)
    _remplir(client, 'Nouveau fictif')
    bouton(fiscal, 'Initialiser le dossier fiscal').invoke()
    assert application.dossier_fiscal_valide_courant is None


def test_modification_entreprise_revoque_annuel(application):
    fiscal = ouvrir(application)
    activer(application, fiscal)
    bouton(fiscal, TITRE_7B).invoke()
    d = derniere_fenetre(fiscal)
    liste = champ(d, 'liste_7b')
    liste.selection_set(0)
    liste.event_generate('<<ListboxSelect>>')
    application.update()
    _remplir(champ(d, 'revenu_brut_7b'), '12000')
    for nom in CONFIRMATIONS_7B:
        cocher(champ(d, nom + '_7b'))
    bouton(d, 'Ajouter / remplacer').invoke()
    bouton(d, 'Appliquer au dossier').invoke()
    assert not application.dossier_fiscal_valide_courant.profil_cotisations_autonomes.activer
    bouton(fiscal, "Calculer l'estimation fiscale 2025").invoke()
    texte = next(w for w in descendants(derniere_fenetre(fiscal)) if isinstance(w, tk.Text)).get('1.0', 'end')
    assert 'estimation finale bloquée' in texte
