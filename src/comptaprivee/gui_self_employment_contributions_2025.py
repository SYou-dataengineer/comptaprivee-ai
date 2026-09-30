"""Confirmation du périmètre annuel autonome pur 7C."""
import tkinter as tk
from tkinter import ttk, messagebox
from .gui_layout import FormulaireDefilant, dimensionner_fenetre
from .tax_self_employment_contributions_2025 import (
    ProfilCotisationsAutonomes2025, CONFIRMATIONS_7C, valider_profil_7c,
)


def ouvrir_cotisations_autonomes_2025(parent, profil, appliquer):
    d=tk.Toplevel(parent)
    d.title('Cotisations autonomes 2025 - 7C')
    dimensionner_fenetre(d,1000,820)
    d.transient(parent);d.grab_set()
    f=FormulaireDefilant(d);c=f.corps;c.columnconfigure(1,weight=1)
    ttk.Label(c,text='Estimation annuelle : autonome pur seulement',font=('Segoe UI',15,'bold')).grid(row=0,columnspan=2,sticky='w')
    ttk.Label(c,text='18 ans acquis avant 2025, moins de 65 ans fin 2025. RRQ/RQAP, déductions et FSS inclus. '
        'Emploi combiné, crédits supplémentaires, acomptes et RAMQ publique exclus. '
        'Sans activation, seule la préparation 7B reste disponible.',wraplength=850,justify='left').grid(row=1,columnspan=2,sticky='w',pady=8)
    actif=tk.BooleanVar(value=profil.activer)
    tk.Checkbutton(c,name='activer_7c',text='Activer le profil annuel 7C',variable=actif).grid(row=2,columnspan=2,sticky='w')
    variables={}
    for row,(nom,label) in enumerate((('naissance','Naissance AAAA-MM-JJ'),('source','Sources et validations comptables')),3):
        v=tk.StringVar(value=getattr(profil,nom));variables[nom]=v
        ttk.Label(c,text=label).grid(row=row,column=0,sticky='w')
        ttk.Entry(c,name=nom+'_7c',textvariable=v).grid(row=row,column=1,sticky='ew',pady=5)
    confirmations={}
    for row,(nom,label) in enumerate(CONFIRMATIONS_7C.items(),5):
        v=tk.BooleanVar(value=getattr(profil,nom));confirmations[nom]=v
        tk.Checkbutton(c,name=nom+'_7c',text=label,variable=v,wraplength=850,justify='left',anchor='w').grid(row=row,columnspan=2,sticky='w',pady=3)
    def revoquer(*_):
        for v in confirmations.values(): v.set(False)
    for v in variables.values(): v.trace_add('write',revoquer)
    actif.trace_add('write',revoquer)
    def effacer():
        actif.set(False)
        for v in variables.values(): v.set('')
    def sauver():
        try:
            p=ProfilCotisationsAutonomes2025(activer=actif.get(),**{n:v.get().strip() for n,v in variables.items()},
                **{n:v.get() for n,v in confirmations.items()})
            valider_profil_7c(p);appliquer(p)
        except ValueError as exc:
            messagebox.showerror('Profil 7C invalide',str(exc),parent=d);return
        d.destroy()
    for texte,commande in (('Appliquer',sauver),('Effacer',effacer),('Fermer',d.destroy)):
        ttk.Button(f.actions,text=texte,command=commande).pack(side='left',padx=5)
