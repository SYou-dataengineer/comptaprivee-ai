"""Fiche unique de location simple 7D, confirmations révoquées après modification."""
import tkinter as tk
from tkinter import ttk, messagebox
from decimal import Decimal, InvalidOperation
from .gui_layout import FormulaireDefilant, dimensionner_fenetre
from .tax_rental_income_2025 import (
    BienLocatif2025, DEPENSES_7D, MONTANTS_7D, CONFIRMATIONS_7D,
    EXCLUSIONS_7D, calculer_location_2025,
)


def ouvrir_location_2025(parent, biens, appliquer):
    d = tk.Toplevel(parent)
    d.title('Location résidentielle simple 2025 - 7D')
    dimensionner_fenetre(d, 1100, 850)
    d.transient(parent); d.grab_set()
    f = FormulaireDefilant(d); c = f.corps; c.columnconfigure(1, weight=1)
    ttk.Label(c, text='Un immeuble résidentiel entièrement locatif, toute l’année 2025.',
              font=('Segoe UI', 14, 'bold')).grid(row=0, columnspan=2, sticky='w')
    ttk.Label(c, text='Sans DPA, pertes, intérêts ni travaux. Location seule ou avec salaire ordinaire. '
        'Les exclusions sont des limites du logiciel. Aucun calcul ne peut être validé avec un cas exclu.',
        wraplength=930, justify='left').grid(row=1, columnspan=2, sticky='w', pady=7)
    b = biens[0] if biens else BienLocatif2025()
    variables = {}
    labels = {'reference':'Référence du bien', 'adresse':'Adresse du bien au Québec',
              'debut':'Début de location (2025-01-01)', 'fin':'Fin de location (2025-12-31)',
              'source':'Sources : baux et pièces', 'loyers':'Loyers bruts de 2025',
              'autres_revenus':'Primes de bail acquises en 2025, hors dépôts remboursables', **DEPENSES_7D}
    row = 2
    for nom, label in labels.items():
        v = tk.StringVar(value=str(getattr(b, nom))); variables[nom] = v
        ttk.Label(c, text=label, wraplength=540).grid(row=row, column=0, sticky='w')
        ttk.Entry(c, name=nom+'_7d', textvariable=v).grid(row=row, column=1, sticky='ew', pady=3)
        row += 1
    exclusions = {}
    ttk.Label(c, text='Cas exclus : cochez tout cas présent (le calcul sera refusé)').grid(row=row,columnspan=2,sticky='w',pady=8)
    row += 1
    for nom, label in EXCLUSIONS_7D.items():
        v = tk.BooleanVar(value=getattr(b, nom)); exclusions[nom] = v
        tk.Checkbutton(c, name=nom+'_7d', text=label, variable=v, anchor='w', justify='left',
                       wraplength=930).grid(row=row,columnspan=2,sticky='w');row += 1
    confirmations = {}
    ttk.Label(c, text='Confirmations obligatoires').grid(row=row,columnspan=2,sticky='w',pady=8);row += 1
    for nom, label in CONFIRMATIONS_7D.items():
        v = tk.BooleanVar(value=getattr(b, nom)); confirmations[nom] = v
        tk.Checkbutton(c, name=nom+'_7d', text=label, variable=v, anchor='w', justify='left',
                       wraplength=930).grid(row=row,columnspan=2,sticky='w',pady=2);row += 1
    def revoquer(*_):
        for v in confirmations.values(): v.set(False)
    for v in (*variables.values(), *exclusions.values()): v.trace_add('write', revoquer)
    def enregistrer():
        try:
            valeurs = {n:v.get().strip() for n,v in variables.items()}
            for n in MONTANTS_7D: valeurs[n] = Decimal(valeurs[n].replace(',', '.'))
            valeurs.update({n:v.get() for n,v in (*exclusions.items(), *confirmations.items())})
            faits = (BienLocatif2025(**valeurs),)
            calculer_location_2025(faits); appliquer(faits)
        except (ValueError, InvalidOperation) as exc:
            messagebox.showerror('Location 7D invalide', str(exc), parent=d); return
        d.destroy()
    def effacer():
        try: appliquer(())
        except ValueError as exc:
            messagebox.showerror('Location 7D invalide', str(exc), parent=d); return
        d.destroy()
    for texte, commande in (('Appliquer', enregistrer), ('Supprimer le bien', effacer), ('Fermer', d.destroy)):
        ttk.Button(f.actions, text=texte, command=commande).pack(side='left', padx=5)
