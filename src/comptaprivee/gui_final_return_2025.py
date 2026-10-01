"""Saisie des faits décès 7H et contrôle avant estimation."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from dataclasses import replace
from .gui_layout import FormulaireDefilant, dimensionner_fenetre
from .tax_final_return_2025 import Deces2025, CONFIRMATIONS_7H, EXCLUSIONS_7H, lignes_deces_2025


def ouvrir_deces_2025(parent, dossier, dossier_actuel, appliquer):
    p = dossier.deces or Deces2025()
    d = tk.Toplevel(parent)
    d.title('Déclaration finale 2025 - 7H')
    dimensionner_fenetre(d, 1100, 900)
    d.transient(parent); d.grab_set()
    f = FormulaireDefilant(d); c = f.corps; c.columnconfigure(1, weight=1)
    ttk.Label(c, text='Décès 2025 - déclaration principale uniquement', font=('Segoe UI', 14, 'bold')).grid(row=0, columnspan=2, sticky='w')
    ttk.Label(c, text='Emploi ordinaire ou intérêts canadiens T5/RL-3 seulement. '
        'Aucun crédit facultatif. Les cas RRQ nécessitant une proratisation ou un excédent spécifique bloquent le calcul annuel.',
        wraplength=970, justify='left').grid(row=1, columnspan=2, sticky='w', pady=8)
    variables = {}
    for row, (n, label) in enumerate((('date_deces','Date du décès (YYYY-MM-DD)'),
            ('province','Province au décès (QC)'), ('reference_representant','Référence du représentant (sans identité sensible)'),
            ('source','Référence de la preuve et contrôle des revenus')), 2):
        v = tk.StringVar(value=getattr(p,n)); variables[n]=v
        ttk.Label(c,text=label,wraplength=490).grid(row=row,column=0,sticky='w')
        ttk.Entry(c,name=n+'_7h',textvariable=v).grid(row=row,column=1,sticky='ew',pady=4)
    bools={}
    labels = {'declaration_finale':'Déclaration finale principale seulement',
        **CONFIRMATIONS_7H,
        'rrq_standard_18_64':'Si emploi : âgé de 18 à 64 ans sur toute la période, sans invalidité RRQ ni choix de cessation.'}
    for row,(n,label) in enumerate(labels.items(),6):
        v=tk.BooleanVar(value=getattr(p,n));bools[n]=v
        tk.Checkbutton(c,name=n+'_7h',text=label,variable=v,wraplength=970,justify='left',anchor='w').grid(row=row,columnspan=2,sticky='w',pady=3)
    exclusions = {'revenus_post_deces':'Revenu reçu ou gagné après le décès présent',
        'actifs_complexes':'Actifs/dispositions, REER/FERR ou roulement présents',
        'entreprise_active':'Travail autonome / entreprise active présent',
        'conjoint_entreprise':'Conjoint exploitant une entreprise',
        'declaration_distincte':'Déclaration distincte requise', 'succession':'Succession T3/TP-646 requise',
        'fiducie':'Fiducie', 'faillite':'Faillite', 'non_resident':'Non-résidence / immigration / émigration',
        'interprovincial':'Profil interprovincial', 'cotisations_facultatives':'Cotisations facultatives',
        'report_imr':'Report antérieur IMR'}
    for row,n in enumerate(EXCLUSIONS_7H,16):
        v=tk.BooleanVar(value=getattr(p,n));bools[n]=v
        tk.Checkbutton(c,name=n+'_7h',text=exclusions[n]+' — hors périmètre',variable=v,
            wraplength=970,anchor='w').grid(row=row,columnspan=2,sticky='w')
    apercu=tk.Text(c,name='trace_7h',height=13,wrap='word',state='disabled')
    apercu.grid(row=29,columnspan=2,sticky='ew',pady=8)
    def afficher(texte):
        apercu.configure(state='normal');apercu.delete('1.0','end');apercu.insert('1.0',texte);apercu.configure(state='disabled')
    def revoquer(*_):
        for n in CONFIRMATIONS_7H:bools[n].set(False)
        afficher('Faits modifiés : reconfirmez les contrôles.')
    for v in variables.values():v.trace_add('write',revoquer)
    for n in EXCLUSIONS_7H:bools[n].trace_add('write',revoquer)
    def verifier():
        try:
            if dossier_actuel() is not dossier:
                raise ValueError('Dossier modifié : rouvrez le profil décès.')
            profil=Deces2025(**{n:v.get().strip() for n,v in variables.items()},**{n:v.get() for n,v in bools.items()})
            nouveau=replace(dossier,deces=profil)
            afficher('\n'.join(lignes_deces_2025(nouveau)))
            return profil,nouveau
        except ValueError as exc:
            messagebox.showerror('Profil décès invalide',str(exc),parent=d)
    def sauver():
        r=verifier()
        if r is None:return
        try:appliquer(r[0])
        except ValueError as exc:messagebox.showerror('Profil décès invalide',str(exc),parent=d);return
        d.destroy()
    def exporter():
        r=verifier()
        if r is None:return
        chemin=filedialog.asksaveasfilename(parent=d,defaultextension='.pdf',filetypes=[('PDF','*.pdf')])
        if not chemin:return
        try:
            from .tax_report_pdf_2025 import exporter_preparation_deces_pdf_2025
            exporter_preparation_deces_pdf_2025(r[1],chemin)
        except (ValueError,OSError) as exc:messagebox.showerror('Export décès impossible',str(exc),parent=d)
    for texte,commande in (('Vérifier et afficher la trace',verifier),('Appliquer les faits',sauver),
            ('Exporter la préparation PDF',exporter),('Fermer',d.destroy)):
        ttk.Button(f.actions,text=texte,command=commande).pack(side='left',padx=5)
