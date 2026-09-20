"""Éditeur local du dossier conjoint 2G; aucune mutation d'un dossier individuel."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from decimal import Decimal, InvalidOperation
from .gui_layout import FormulaireDefilant, dimensionner_fenetre, organiser_boutons
from .tax_pension_splitting_2025 import (ConjointPension2025, ChoixFractionnement2025,
    calculer_fractionnement_2025, lignes_fractionnement_2025)
from .tax_pension_splitting_storage import sauvegarder_fractionnement_2025, charger_fractionnement_2025
from .tax_report_pdf_2025 import exporter_fractionnement_pdf_2025


def ouvrir_fractionnement_2025(parent):
    dialogue=tk.Toplevel(parent)
    dialogue.title('Fractionnement de pension 2025 - couple')
    dimensionner_fenetre(dialogue,900,700)
    dialogue.transient(parent)
    formulaire=FormulaireDefilant(dialogue);cadre=formulaire.corps
    cadre.columnconfigure(0,weight=1)
    texte=("Dossier de couple distinct : saisissez les deux pensions RPA viagères T4A 016 / RL-2 A après validation des pièces. "
        "Une paire par conjoint; les retenues portent uniquement sur cette pension. Identifiants locaux distincts, sans NAS requis. "
        "Canada/Québec et union toute l'année 2025, sans séparation ni décès, assurance médicaments privée complète. "
        "Aucun salaire, autre revenu (dont PSV/RRQ), déduction, transfert de crédit ni crédit particulier. "
        "Nets de chaque conjoint limités à 30 000–57 375 $ dans les deux juridictions. FERR, rentes autres que RPA, changements conjugaux et RAMQ publique exclus. "
        "Le choix fédéral est indépendant du choix Québec (cédant de 65 ans requis pour ce dernier). Répartissez le montant 361 commun après réduction unique. "
        "Une modification révoque toutes les confirmations et le résultat/PDF. Ce rapport ne remplace pas les formulaires signés.")
    ttk.Label(cadre,text=texte,wraplength=650,justify='left').grid(row=0,column=0,sticky='w',pady=10)
    variables={};row=1
    champs=[('identifiant','Identifiant local'),('age','Âge au 31 décembre'),('t4a_016','T4A 016'),('rl2_a','RL-2 A'),('t4a_022','T4A 022'),('rl2_j','RL-2 J'),('source','Pièces et source âge')]
    for role in ('cedant','beneficiaire'):
        ttk.Label(cadre,text=role.upper()).grid(row=row,column=0,sticky='w',pady=8);row+=1
        for cle,label in champs:
            nom=role+'_'+cle;v=tk.StringVar(value='0' if cle in {'t4a_016','rl2_a','t4a_022','rl2_j'} else '')
            variables[nom]=v
            ttk.Label(cadre,text=label).grid(row=row,column=0,sticky='w');row+=1
            ttk.Entry(cadre,name=nom,textvariable=v).grid(row=row,column=0,sticky='ew',pady=3);row+=1
    for nom,label in [('montant_federal','Montant choisi T1032 (maximum 50 %)'),('montant_quebec','Montant choisi annexe Q (maximum 50 %)'),('montant_361_cedant','Montant 361 attribué au cédant; solde au bénéficiaire')]:
        v=tk.StringVar(value='0');variables[nom]=v
        ttk.Label(cadre,text=label).grid(row=row,column=0,sticky='w');row+=1
        ttk.Entry(cadre,name=nom,textvariable=v).grid(row=row,column=0,sticky='ew',pady=3);row+=1
    confirmations={}
    for nom,label in [('cedant_confirme','Je confirme les données et exclusions du cédant.'),('beneficiaire_confirme','Je confirme les données et exclusions du bénéficiaire.'),('choix_conjoint_confirme','Les deux conjoints confirment le choix T1032/annexe Q, les conditions ci-dessus et la répartition 361.')]:
        v=tk.BooleanVar(value=False);confirmations[nom]=v
        tk.Checkbutton(cadre,name=nom,variable=v,text=label,wraplength=650,justify='left').grid(row=row,column=0,sticky='w',pady=8);row+=1
    etat={'resultat':None,'revision':0,'chargement':False}
    def invalider(*_):
        if etat['chargement']:return
        etat['revision']+=1;etat['resultat']=None
        for v in confirmations.values():v.set(False)
    for v in variables.values():v.trace_add('write',invalider)
    def invalider_confirmation(*_):
        if not etat['chargement']:
            etat['revision']+=1;etat['resultat']=None
    for v in confirmations.values():v.trace_add('write',invalider_confirmation)
    def profil():
        personnes={}
        for role in ('cedant','beneficiaire'):
            valeurs={cle:variables[role+'_'+cle].get().strip() for cle,_ in champs}
            valeurs['age']=int(valeurs['age']) if valeurs['age'] else None
            for cle in ('t4a_016','rl2_a','t4a_022','rl2_j'):valeurs[cle]=Decimal(valeurs[cle].replace(',','.'))
            personnes[role]=ConjointPension2025(**valeurs,confirme=confirmations[role+'_confirme'].get())
        return ChoixFractionnement2025(**personnes,**{k:Decimal(variables[k].get().replace(',','.')) for k in ('montant_federal','montant_quebec','montant_361_cedant')},choix_conjoint_confirme=confirmations['choix_conjoint_confirme'].get())
    def erreur(e):messagebox.showerror('Fractionnement invalide',str(e),parent=dialogue)
    def calculer():
        try:r=calculer_fractionnement_2025(profil())
        except (ValueError,InvalidOperation) as e:erreur(e);return
        etat['resultat']=r;revision=etat['revision']
        resultat=tk.Toplevel(dialogue);resultat.title('Résultat conjoint 2025');dimensionner_fenetre(resultat,850,650)
        text=tk.Text(resultat,wrap='word');text.pack(fill='both',expand=True);text.insert('1.0','\n'.join(lignes_fractionnement_2025(r)))
        text.configure(state='disabled')
        def exporter():
            if revision!=etat['revision'] or etat['resultat'] is not r:
                messagebox.showerror('Estimation périmée','Revalidez et recalculez le couple.',parent=resultat);return
            chemin=filedialog.asksaveasfilename(parent=resultat,defaultextension='.pdf',filetypes=[('PDF','*.pdf')])
            if chemin:exporter_fractionnement_pdf_2025(r,chemin)
        ttk.Button(resultat,text='Exporter le PDF conjoint',command=exporter).pack(fill='x')
    def sauver():
        try:
            p=profil()
            chemin=filedialog.asksaveasfilename(parent=dialogue,defaultextension='.json',filetypes=[('Dossier de couple','*.json')])
            if chemin:sauvegarder_fractionnement_2025(p,chemin)
        except (ValueError,InvalidOperation,OSError) as e:erreur(e)
    def ouvrir():
        chemin=filedialog.askopenfilename(parent=dialogue,filetypes=[('Dossier de couple','*.json')])
        if not chemin:return
        try:p=charger_fractionnement_2025(chemin)
        except (ValueError,OSError) as e:erreur(e);return
        invalider();etat['chargement']=True
        try:
            for role in ('cedant','beneficiaire'):
                personne=getattr(p,role)
                for cle,_ in champs:variables[role+'_'+cle].set('' if getattr(personne,cle) is None else str(getattr(personne,cle)))
                confirmations[role+'_confirme'].set(personne.confirme)
            for k in ('montant_federal','montant_quebec','montant_361_cedant'):variables[k].set(str(getattr(p,k)))
            confirmations['choix_conjoint_confirme'].set(p.choix_conjoint_confirme)
        finally:etat['chargement']=False
    for label,cmd in [('Fermer',dialogue.destroy),('Ouvrir le couple',ouvrir),('Sauvegarder le couple',sauver),('Calculer les deux déclarations',calculer)]:
        ttk.Button(formulaire.actions,text=label,command=cmd).pack(side='left')
    organiser_boutons(formulaire.actions)
    return dialogue
