"""Messages GUI pour montants non finis et résultats historiques."""
import inspect
from tkinter import ttk
import pytest
from tests.test_gui_block2 import application, racine, ouvrir_dossier_test, derniere_fenetre, descendants, bouton
from src.comptaprivee import gui


@pytest.mark.parametrize('valeur',['NaN','nan','Infinity','inf','-Infinity'])
def test_correction_gui_non_finie(application,monkeypatch,valeur):
    fiscal=ouvrir_dossier_test(application)
    extraire=application.callbacks_test['extraire_cases_documents_fiscaux']
    inspect.getclosurevars(extraire).nonlocals['afficher_donnees_fiscales_extraites']()
    fenetre=derniere_fenetre(fiscal)
    table=next(w for w in descendants(fenetre) if isinstance(w,ttk.Treeview))
    table.selection_set(table.get_children()[0])
    monkeypatch.setattr(gui.simpledialog,'askstring',lambda *a,**k:valeur)
    bouton(fenetre,'Corriger et valider').invoke()
    assert any('fini' in str(m) for m in application.messages_test)
    assert not application.erreurs_test


def test_historique_gui_recalcul_requis(application):
    import json
    from tests.test_tax_case_storage import _dossier
    from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
    d=_dossier();p=sauvegarder_dossier_fiscal(d,estimation=calculer_estimation_fiscale_2025(d))
    c=json.loads(p.read_text(encoding='utf-8'));c['derniere_estimation']['montant']='999999'
    p.write_text(json.dumps(c),encoding='utf-8')
    application.ouvrir_agent_fiscal();fiscal=derniere_fenetre(application)
    bouton(fiscal,'Dossiers enregistrés').invoke();liste=derniere_fenetre(fiscal)
    table=next(w for w in descendants(liste) if isinstance(w,ttk.Treeview))
    ident=table.get_children()[0]
    assert 'Recalcul requis' in table.set(ident,'resultat')
    table.selection_set(ident);bouton(liste,'Ouvrir le dossier').invoke()
    assert any('historique non verifie' in str(m) for m in application.messages_test)
    bouton(fiscal,"Calculer l'estimation fiscale 2025").invoke()
    assert not application.erreurs_test
