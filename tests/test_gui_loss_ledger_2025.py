import tkinter as tk
from tkinter import ttk
from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre, descendants
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from tests.test_gui_caregiver_child_combination_2025 import cocher
from tests.test_gui_rental_income_2025 import ouvrir
from src.comptaprivee.tax_loss_ledger_2025 import RegistrePertes2025

TITRE = 'Pertes et reports 2025 (7F)'


def fiche(fiscal):
    bouton(fiscal,TITRE).invoke();d=derniere_fenetre(fiscal)
    for n,v in (('annee_origine','2024'),('disponible','1000'),('source','Avis et rapprochement fictifs'),('courant','400')):
        _remplir(champ(d,n+'_7f'),v)
    cocher(champ(d,'confirmation_7f'))
    bouton(d,'Préparer la fiche').invoke()
    return d


def test_gui_annuel_pdf_sauvegarde_reset(application,monkeypatch,tmp_path):
    from src.comptaprivee import gui
    fiscal=ouvrir(application)
    d=fiche(fiscal);bouton(d,'Appliquer le registre').invoke()
    assert not d.winfo_exists(),application.messages_test
    assert application.dossier_fiscal_valide_courant.registre_pertes.pertes_non_capital[0].disponible==1000
    bouton(fiscal,"Calculer l'estimation fiscale 2025").invoke();resultat=derniere_fenetre(fiscal)
    texte=next(w for w in descendants(resultat) if isinstance(w,tk.Text)).get('1.0','end')
    assert '25200' in texte and '400.00' in texte
    pdf=tmp_path/'pertes_fictives.pdf';monkeypatch.setattr(gui.filedialog,'asksaveasfilename',lambda **kw:str(pdf))
    bouton(resultat,'Exporter le rapport fiscal en PDF').invoke();assert pdf.exists()
    bouton(fiscal,'Enregistrer dossier').invoke();fiscal.destroy()
    application.ouvrir_agent_fiscal();fiscal=derniere_fenetre(application)
    bouton(fiscal,'Dossiers enregistrés').invoke();bouton(derniere_fenetre(fiscal),'Ouvrir le dossier').invoke()
    assert application.dossier_fiscal_valide_courant.registre_pertes.pertes_non_capital[0].disponible==1000
    client=next(w for w in descendants(fiscal) if type(w) is ttk.Entry)
    _remplir(client,'Nouveau fictif');bouton(fiscal,'Initialiser le dossier fiscal').invoke()
    assert application.dossier_fiscal_valide_courant is None
    bouton(fiscal,TITRE).invoke()
    assert application.messages_test[-1][0]=='Pertes 7F indisponibles'


def test_gui_modification_confirmation_et_invalidation_pdf(application):
    fiscal=ouvrir(application);d=fiche(fiscal)
    _remplir(champ(d,'disponible_7f'),'300')
    assert not d.getvar(champ(d,'confirmation_7f').cget('variable'))
    cocher(champ(d,'confirmation_7f'));bouton(d,'Préparer la fiche').invoke()
    assert 'solde disponible' in application.messages_test[-1][1]
    bouton(d,'Appliquer le registre').invoke()
    assert application.dossier_fiscal_valide_courant.registre_pertes.pertes_non_capital[0].disponible==1000
    bouton(fiscal,"Calculer l'estimation fiscale 2025").invoke();resultat=derniere_fenetre(fiscal)
    bouton(fiscal,TITRE).invoke();d=derniere_fenetre(fiscal)
    bouton(d,'Désactiver les reports').invoke();bouton(d,'Appliquer le registre').invoke()
    assert application.dossier_fiscal_valide_courant.registre_pertes==RegistrePertes2025()
    bouton(resultat,'Exporter le rapport fiscal en PDF').invoke()
    assert application.messages_test[-1][0]=='Estimation périmée'


def test_gui_report_non_capital_separe(application,monkeypatch,tmp_path):
    from src.comptaprivee import gui_loss_ledger_2025 as module
    fiscal=ouvrir(application);bouton(fiscal,TITRE).invoke();d=derniere_fenetre(fiscal)
    for n,v in (('annee_origine','2025'),('disponible','1000'),('source','T1A fictif perte fiscale nette confirmée'),
                ('arriere_2024','300'),('revenu_2024','5000'),('source_2024','Avis et utilisations fictifs 2024')):
        _remplir(champ(d,n+'_7f'),v)
    cocher(champ(d,'confirmation_7f'));bouton(d,'Préparer la fiche').invoke()
    pdf=tmp_path/'demande_fictive.pdf';monkeypatch.setattr(module.filedialog,'asksaveasfilename',lambda **kw:str(pdf))
    bouton(d,'PDF préparation séparée').invoke();assert pdf.exists(),application.messages_test
    bouton(d,'Appliquer le registre').invoke()
    bouton(fiscal,"Calculer l'estimation fiscale 2025").invoke()
    assert 'préparation séparée' in application.messages_test[-1][1]
