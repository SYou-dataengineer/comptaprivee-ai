"""Section DPA 7E distincte de la fiche de revenus et dépenses 7D."""
import tkinter as tk
from tkinter import ttk, messagebox
from decimal import Decimal, InvalidOperation
from .gui_layout import FormulaireDefilant, dimensionner_fenetre
from .tax_rental_cca_2025 import DpaLocation2025, CONFIRMATIONS_7E, calculer_dpa_location_2025


def ouvrir_dpa_location_2025(parent, profil, revenu_avant, appliquer):
    d = tk.Toplevel(parent)
    d.title('DPA location 2025 - 7E')
    dimensionner_fenetre(d, 1050, 850)
    d.transient(parent); d.grab_set()
    f = FormulaireDefilant(d); c = f.corps; c.columnconfigure(1, weight=1)
    ttk.Label(c, text='Catégorie 1 régulière - taux 4 % - immeuble déjà détenu avant 2025',
        font=('Segoe UI',14,'bold')).grid(row=0,columnspan=2,sticky='w')
    ttk.Label(c, text=f'Revenu locatif avant DPA : {revenu_avant:.2f} $. Soldes et choix fédéral/Québec indépendants. '
        'Aucune addition/acquisition, disposition ou règle de première année. Terrain exclu. '
        'T776 F (25) section A; TPW-130.G applicable à 2025, sections 4.2 et 5.1.',
        wraplength=900,justify='left').grid(row=1,columnspan=2,sticky='w',pady=8)
    p = profil if profil is not None else DpaLocation2025()
    labels = {'acquisition':'Acquisition AAAA-MM-JJ (avant 2025)',
        'mise_service':'Disponibilité pour utilisation AAAA-MM-JJ (avant 2025)',
        'fnacc_federale':'FNACC fédérale au 1er janvier 2025',
        'pnacc_quebec':'PNACC Québec au 1er janvier 2025',
        'dpa_federale':'DPA choisie fédérale', 'dpa_quebec':'DPA choisie Québec',
        'source':'Sources des soldes et choix, explication des écarts éventuels'}
    variables = {}
    row = 2
    for n,label in labels.items():
        v=tk.StringVar(value=str(getattr(p,n))); variables[n]=v
        ttk.Label(c,text=label,wraplength=470).grid(row=row,column=0,sticky='w')
        ttk.Entry(c,name=n+'_7e',textvariable=v).grid(row=row,column=1,sticky='ew',pady=5)
        row += 1
    confirmations = {}
    for n,label in CONFIRMATIONS_7E.items():
        v=tk.BooleanVar(value=getattr(p,n));confirmations[n]=v
        tk.Checkbutton(c,name=n+'_7e',text=label,variable=v,wraplength=900,justify='left',anchor='w').grid(row=row,columnspan=2,sticky='w',pady=4)
        row += 1
    apercu=tk.StringVar(value='')
    ttk.Label(c,name='apercu_7e',textvariable=apercu,wraplength=900,justify='left').grid(row=row,columnspan=2,sticky='w',pady=10)
    def revoquer(*_):
        for v in confirmations.values(): v.set(False)
        apercu.set('Choix modifiés : reconfirmez et vérifiez les plafonds.')
    for v in variables.values(): v.trace_add('write',revoquer)
    def lire():
        valeurs={n:v.get().strip() for n,v in variables.items()}
        for n in ('fnacc_federale','pnacc_quebec','dpa_federale','dpa_quebec'):
            valeurs[n]=Decimal(valeurs[n].replace(',','.'))
        return DpaLocation2025(**valeurs,**{n:v.get() for n,v in confirmations.items()})
    def verifier():
        try:
            profil=lire(); r=calculer_dpa_location_2025(profil,revenu_avant)
            apercu.set(f'Plafond fédéral : {r.federal.maximum_admissible:.2f} $; FNACC finale : {r.federal.fermeture:.2f} $. '
                f'Plafond Québec : {r.quebec.maximum_admissible:.2f} $; PNACC finale : {r.quebec.fermeture:.2f} $.')
            return profil
        except (ValueError,InvalidOperation) as exc:
            messagebox.showerror('DPA 7E invalide',str(exc),parent=d)
            return None
    def sauver():
        profil=verifier()
        if profil is None: return
        try: appliquer(profil)
        except ValueError as exc:
            messagebox.showerror('DPA 7E invalide',str(exc),parent=d); return
        d.destroy()
    def desactiver():
        try: appliquer(None)
        except ValueError as exc:
            messagebox.showerror('DPA 7E invalide',str(exc),parent=d); return
        d.destroy()
    for texte,commande in (('Vérifier les plafonds',verifier),('Appliquer',sauver),('Désactiver la DPA',desactiver),('Fermer',d.destroy)):
        ttk.Button(f.actions,text=texte,command=commande).pack(side='left',padx=5)
