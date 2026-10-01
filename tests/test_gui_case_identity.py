"""Identité persistante à travers la navigation GUI et le nouveau dossier."""
from tkinter import ttk
from dataclasses import replace
from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre, descendants
from tests.test_gui_other_deductions_2025 import _remplir
from tests.test_tax_case_storage import _dossier
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal


def test_chargement_a_b_et_nouveau_dossier(application):
    a=replace(_dossier(),client='Client A fictif')
    b=replace(_dossier(),client='Client B fictif')
    sauvegarder_dossier_fiscal(a); sauvegarder_dossier_fiscal(b)
    application.ouvrir_agent_fiscal(); fiscal=derniere_fenetre(application)
    for d in (a,b,a):
        bouton(fiscal,'Dossiers enregistrés').invoke(); liste=derniere_fenetre(fiscal)
        table=next(w for w in descendants(liste) if isinstance(w,ttk.Treeview))
        ident=next(i for i in table.get_children() if table.set(i,'client')==d.client)
        table.selection_set(ident); bouton(liste,'Ouvrir le dossier').invoke()
        assert application.dossier_fiscal_courant.case_id==d.case_id
        assert application.dossier_fiscal_valide_courant.case_id==d.case_id
    client=next(w for w in descendants(fiscal) if type(w) is ttk.Entry)
    _remplir(client,a.client)  # un homonyme est aussi un nouveau dossier
    bouton(fiscal,'Initialiser le dossier fiscal').invoke()
    assert application.dossier_fiscal_courant.case_id not in {a.case_id,b.case_id}
    assert application.dossier_fiscal_valide_courant is None
