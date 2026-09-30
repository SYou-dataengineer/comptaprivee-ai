import tkinter as tk
from tkinter import ttk

from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre, descendants
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from tests.test_gui_caregiver_child_combination_2025 import cocher
from tests.test_gui_rental_income_2025 import ouvrir, TITRE as TITRE_7D
from src.comptaprivee.tax_rental_cca_2025 import CONFIRMATIONS_7E
from src.comptaprivee.tax_rental_income_2025 import CONFIRMATIONS_7D

TITRE = 'DPA location 2025 (7E)'


def activer(application,fiscal):
    bouton(fiscal,TITRE).invoke();d=derniere_fenetre(fiscal)
    for n,v in [('acquisition','2010-01-01'),('mise_service','2010-01-01'),('source','Registres fictifs'),
                ('fnacc_federale','100000'),('pnacc_quebec','80000'),('dpa_federale','4000'),('dpa_quebec','3000')]:
        _remplir(champ(d,n+'_7e'),v)
    for n in CONFIRMATIONS_7E: cocher(champ(d,n+'_7e'))
    bouton(d,'Vérifier les plafonds').invoke()
    assert '3200.00' in d.getvar(champ(d,'apercu_7e').cget('textvariable'))
    bouton(d,'Appliquer').invoke()
    assert not d.winfo_exists(),application.messages_test


def test_gui_dpa_annuel_pdf_recharge_reset(application,monkeypatch,tmp_path):
    from src.comptaprivee import gui
    fiscal=ouvrir(application);activer(application,fiscal)
    bouton(fiscal,"Calculer l'estimation fiscale 2025").invoke();resultat=derniere_fenetre(fiscal)
    texte=next(w for w in descendants(resultat) if isinstance(w,tk.Text)).get('1.0','end')
    assert '20000.00' in texte and '21000.00' in texte and '96000.00' in texte and '77000.00' in texte
    p=tmp_path/'7e.pdf';monkeypatch.setattr(gui.filedialog,'asksaveasfilename',lambda **kw:str(p))
    bouton(resultat,'Exporter le rapport fiscal en PDF').invoke();assert p.exists()
    bouton(fiscal,'Enregistrer dossier').invoke();fiscal.destroy()
    application.ouvrir_agent_fiscal();fiscal=derniere_fenetre(application)
    bouton(fiscal,'Dossiers enregistrés').invoke();bouton(derniere_fenetre(fiscal),'Ouvrir le dossier').invoke()
    assert application.dossier_fiscal_valide_courant.biens_locatifs[0].amortissement.dpa_quebec==3000
    bouton(fiscal,TITRE).invoke();d=derniere_fenetre(fiscal)
    assert champ(d,'fnacc_federale_7e').get()=='100000'
    bouton(d,'Fermer').invoke()
    client=next(w for w in descendants(fiscal) if type(w) is ttk.Entry)
    _remplir(client,'Nouveau fictif');bouton(fiscal,'Initialiser le dossier fiscal').invoke()
    assert application.dossier_fiscal_valide_courant is None
    bouton(fiscal,TITRE).invoke()
    assert application.messages_test[-1][0]=='DPA 7E indisponible'


def test_modification_revoque_confirmations_refus_et_export_perime(application):
    fiscal=ouvrir(application);activer(application,fiscal)
    bouton(fiscal,"Calculer l'estimation fiscale 2025").invoke();resultat=derniere_fenetre(fiscal)
    bouton(fiscal,TITRE).invoke();d=derniere_fenetre(fiscal)
    _remplir(champ(d,'dpa_federale_7e'),'4001')
    for n in CONFIRMATIONS_7E:
        assert not d.getvar(champ(d,n+'_7e').cget('variable'))
        cocher(champ(d,n+'_7e'))
    bouton(d,'Appliquer').invoke()
    assert d.winfo_exists() and 'maximum' in application.messages_test[-1][1]
    assert application.dossier_fiscal_valide_courant.biens_locatifs[0].amortissement.dpa_federale==4000
    bouton(d,'Désactiver la DPA').invoke()
    assert application.dossier_fiscal_valide_courant.biens_locatifs[0].amortissement is None
    bouton(resultat,'Exporter le rapport fiscal en PDF').invoke()
    assert application.messages_test[-1][0]=='Estimation périmée'


def test_modifier_7d_revoque_7e(application):
    fiscal=ouvrir(application);activer(application,fiscal)
    bouton(fiscal,TITRE_7D).invoke();d=derniere_fenetre(fiscal)
    _remplir(champ(d,'loyers_7d'),'1000')
    for n in CONFIRMATIONS_7D: cocher(champ(d,n+'_7d'))
    bouton(d,'Appliquer').invoke()
    assert not d.winfo_exists(),application.messages_test
    b=application.dossier_fiscal_valide_courant.biens_locatifs[0]
    assert b.loyers==1000 and b.amortissement is None
