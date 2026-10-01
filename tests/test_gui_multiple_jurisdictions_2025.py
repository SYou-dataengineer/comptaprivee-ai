import tkinter as tk
from tkinter import ttk
from dataclasses import replace
from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre, descendants
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from tests.test_gui_caregiver_child_combination_2025 import cocher
from tests.test_gui_self_employment_2025 import ouvrir, TITRE as TITRE_7B
from tests.test_gui_self_employment_contributions_2025 import activer
from src.comptaprivee.tax_multiple_jurisdictions_2025 import CONFIRMATIONS_7G

TITRE='Administrations multiples 2025 (7G)'


def saisir(fiscal):
    bouton(fiscal,TITRE).invoke();d=derniere_fenetre(fiscal)
    cocher(champ(d,'presence_7g'))
    champ(d,'province_7g').set('ON')
    for n,v in (('revenu_quebec','7000'),('revenu_hors_quebec','3000'),
                ('methode','Ventilation nette documentée fictive'),('source','Analyse et pièces fictives')):
        _remplir(champ(d,n+'_7g'),v)
    for n in CONFIRMATIONS_7G:cocher(champ(d,n+'_7g'))
    return d


def test_gui_detection_trace_pdf_sauvegarde_recharge_reset(application,monkeypatch,tmp_path):
    from src.comptaprivee import gui_multiple_jurisdictions_2025 as module
    fiscal=ouvrir(application);d=saisir(fiscal)
    bouton(d,'Vérifier et afficher la trace').invoke()
    texte=champ(d,'trace_7g').get('1.0','end')
    assert 'Ontario' in texte and 'T2203 requis : oui' in texte and 'TP-22 requis : oui' in texte
    assert 'CALCUL ANNUEL SUSPENDU' in texte
    pdf=tmp_path/'interprovincial_fictif.pdf'
    monkeypatch.setattr(module.filedialog,'asksaveasfilename',lambda **kw:str(pdf))
    bouton(d,'Exporter la préparation PDF').invoke();assert pdf.exists(),application.messages_test
    bouton(d,'Appliquer les faits').invoke();assert not d.winfo_exists(),application.messages_test
    e=application.dossier_fiscal_valide_courant.entreprises[0]
    assert not e.services_quebec and e.administrations.province=='ON'
    bouton(fiscal,"Calculer l'estimation fiscale 2025").invoke()
    assert application.messages_test[-1][0]=='Calcul annuel suspendu - 7G'
    assert 'T2203 / TP-22 requis' in application.messages_test[-1][1]
    bouton(fiscal,'Enregistrer dossier').invoke();fiscal.destroy()
    application.ouvrir_agent_fiscal();fiscal=derniere_fenetre(application)
    bouton(fiscal,'Dossiers enregistrés').invoke();bouton(derniere_fenetre(fiscal),'Ouvrir le dossier').invoke()
    assert application.dossier_fiscal_valide_courant.entreprises[0].administrations.revenu_hors_quebec==3000
    bouton(fiscal,TITRE).invoke();d=derniere_fenetre(fiscal)
    assert champ(d,'province_7g').get()=='ON'
    bouton(d,'Fermer').invoke()
    client=next(w for w in descendants(fiscal) if type(w) is ttk.Entry)
    _remplir(client,'Nouveau fictif');bouton(fiscal,'Initialiser le dossier fiscal').invoke()
    assert application.dossier_fiscal_valide_courant is None
    bouton(fiscal,TITRE).invoke()
    assert application.messages_test[-1][0]=='Préparation 7G indisponible'


def test_gui_montants_incoherents_confirmation_revoquee(application):
    fiscal=ouvrir(application);d=saisir(fiscal)
    _remplir(champ(d,'revenu_hors_quebec_7g'),'3001')
    for n in CONFIRMATIONS_7G:
        assert not d.getvar(champ(d,n+'_7g').cget('variable'))
        cocher(champ(d,n+'_7g'))
    bouton(d,'Appliquer les faits').invoke()
    assert d.winfo_exists() and 'ventilation différente' in application.messages_test[-1][1]
    assert application.dossier_fiscal_valide_courant.entreprises[0].administrations is None


def test_gui_revoque_7c_et_pdf_annuel_precedent(application):
    fiscal=ouvrir(application);activer(application,fiscal)
    bouton(fiscal,"Calculer l'estimation fiscale 2025").invoke();annuel=derniere_fenetre(fiscal)
    d=saisir(fiscal);bouton(d,'Appliquer les faits').invoke()
    assert not application.dossier_fiscal_valide_courant.profil_cotisations_autonomes.activer
    bouton(annuel,'Exporter le rapport fiscal en PDF').invoke()
    assert application.messages_test[-1][0]=='Estimation périmée'


def test_gui_preparation_perimee_refuse_export_et_application(application,monkeypatch,tmp_path):
    from src.comptaprivee import gui_multiple_jurisdictions_2025 as module
    fiscal=ouvrir(application);d=saisir(fiscal)
    actuel=application.dossier_fiscal_valide_courant
    application.dossier_fiscal_valide_courant=replace(actuel,client='Dossier fictif modifié')
    pdf=tmp_path/'interdit.pdf';monkeypatch.setattr(module.filedialog,'asksaveasfilename',lambda **kw:str(pdf))
    bouton(d,'Exporter la préparation PDF').invoke()
    assert not pdf.exists() and 'Dossier modifié' in application.messages_test[-1][1]
    bouton(d,'Appliquer les faits').invoke();assert d.winfo_exists()


def test_gui_7b_ne_supprime_pas_silencieusement_presence_hors_quebec(application):
    fiscal=ouvrir(application);d=saisir(fiscal);bouton(d,'Appliquer les faits').invoke()
    bouton(fiscal,TITRE_7B).invoke();d=derniere_fenetre(fiscal)
    application.update()
    liste=champ(d,'liste_7b');liste.selection_set(0);liste.event_generate('<<ListboxSelect>>');application.update()
    assert champ(d,'reference_7b').get() == application.dossier_fiscal_valide_courant.entreprises[0].reference
    # L'ancien formulaire ne peut pas convertir le profil hors Québec en Québec seul.
    cocher(champ(d,'services_quebec_7b'))
    bouton(d,'Ajouter / remplacer').invoke()
    assert 'incompatible' in application.messages_test[-1][1]
    assert application.dossier_fiscal_valide_courant.entreprises[0].administrations.etablissement_hors_quebec


def test_gui_quebec_seulement_preserve_le_parcours_7c(application):
    fiscal=ouvrir(application);activer(application,fiscal)
    ancien=application.dossier_fiscal_valide_courant.profil_cotisations_autonomes
    bouton(fiscal,TITRE).invoke();d=derniere_fenetre(fiscal)
    _remplir(champ(d,'methode_7g'),'Activité intégralement Québec, analyse fictive')
    _remplir(champ(d,'source_7g'),'Pièces fictives Québec seulement')
    for n in CONFIRMATIONS_7G:cocher(champ(d,n+'_7g'))
    bouton(d,'Appliquer les faits').invoke();assert not d.winfo_exists(),application.messages_test
    assert application.dossier_fiscal_valide_courant.profil_cotisations_autonomes==ancien
    bouton(fiscal,"Calculer l'estimation fiscale 2025").invoke();resultat=derniere_fenetre(fiscal)
    texte=next(w for w in descendants(resultat) if isinstance(w,tk.Text)).get('1.0','end')
    assert '445' in texte and '8880.60' in texte
