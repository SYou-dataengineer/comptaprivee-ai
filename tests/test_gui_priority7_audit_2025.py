"""7K : isolation des profils entre deux dossiers fictifs et après reset."""
from dataclasses import replace
import inspect
from tkinter import ttk
import pytest
from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre, descendants
from tests.test_gui_other_deductions_2025 import _remplir
from tests.test_tax_case_storage import _dossier
from tests.test_tax_self_employment_contributions_2025 import dossier_7c
from tests.test_tax_rental_cca_2025 import dossier_dpa
from tests.test_tax_multiple_jurisdictions_2025 import dossier_7g
from tests.test_tax_loss_integration_2025 import pertes
from tests.test_tax_minimum_preparation_2025 import profil as imr
from tests.test_tax_foreign_property_2025 import profil as inventaire
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal
from src.comptaprivee.tax_loss_ledger_2025 import RegistrePertes2025


@pytest.mark.parametrize('fabrique',[dossier_7c,dossier_dpa,dossier_7g])
def test_chargements_successifs_et_reset_isolent_profils(application,fabrique):
    premier=replace(fabrique(),client='Premier fictif',registre_pertes=pertes(),imr=imr(),biens_etrangers=inventaire())
    second=replace(_dossier(),client='Second fictif')
    sauvegarder_dossier_fiscal(premier);sauvegarder_dossier_fiscal(second)
    application.ouvrir_agent_fiscal();fiscal=derniere_fenetre(application)
    def ouvrir(client):
        bouton(fiscal,'Dossiers enregistrés').invoke();liste=derniere_fenetre(fiscal)
        table=next(w for w in descendants(liste) if isinstance(w,ttk.Treeview))
        ident=next(i for i in table.get_children() if table.set(i,'client')==client)
        table.selection_set(ident);bouton(liste,'Ouvrir le dossier').invoke()
    def memoire_vide():
        valeurs=inspect.getclosurevars(application.callbacks_test['initialiser_dossier_fiscal']).nonlocals
        for cle,attendu in [('entreprises_courantes',()),('locations_courantes',()),
                ('pertes_courantes',RegistrePertes2025()),('deces_courant',None),
                ('imr_courant',None),('biens_etrangers_courants',None)]:
            assert valeurs[cle]==attendu,cle
    ouvrir(premier.client)
    assert application.dossier_fiscal_valide_courant==premier
    ouvrir(second.client)
    assert application.dossier_fiscal_valide_courant==second
    memoire_vide()
    bouton(fiscal,"Calculer l'estimation fiscale 2025").invoke()
    resultat=derniere_fenetre(fiscal)
    assert resultat is not fiscal,application.messages_test
    resultat.destroy()
    ouvrir(premier.client)
    client=next(w for w in descendants(fiscal) if type(w) is ttk.Entry)
    _remplir(client,'Nouveau fictif');bouton(fiscal,'Initialiser le dossier fiscal').invoke()
    assert application.dossier_fiscal_valide_courant is None
    memoire_vide()
