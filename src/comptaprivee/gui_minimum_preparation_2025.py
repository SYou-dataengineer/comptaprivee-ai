"""Préparation IMR 7I : faits seulement, aucun champ d'impôt calculé."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from dataclasses import replace
from decimal import Decimal, InvalidOperation
from .gui_layout import FormulaireDefilant, dimensionner_fenetre
from .tax_minimum_preparation_2025 import (
    ProfilImr2025, ElementImr2025, SoldeImr2025, ELEMENTS_7I, lignes_imr_2025,
)


def ouvrir_imr_2025(parent, dossier, dossier_actuel, appliquer):
    p = dossier.imr or ProfilImr2025()
    d = tk.Toplevel(parent)
    d.title('Préparation IMR 2025 - 7I')
    dimensionner_fenetre(d, 1100, 900)
    d.transient(parent); d.grab_set()
    f = FormulaireDefilant(d); c = f.corps; c.columnconfigure(1, weight=1)
    ttk.Label(c, text='IMR : détection, faits et préparation externe', font=('Segoe UI', 14, 'bold')).grid(row=0, columnspan=2, sticky='w')
    ttk.Label(c, text='Aucun calcul T691 / TP-776.42. Aucun montant IMR écrit à 41700/40427/432. '
        'Un élément connu ou un solde positif suspend l’estimation annuelle. '
        'Le repère 177 882 $ ne décide pas de l’obligation fiscale.',
        wraplength=970, justify='left').grid(row=1, columnspan=2, sticky='w', pady=8)
    source = tk.StringVar(value=p.source)
    ttk.Label(c, text='Source du contrôle comptable').grid(row=2, column=0, sticky='w')
    ttk.Entry(c, name='source_7i', textvariable=source).grid(row=2, column=1, sticky='ew')
    zones = {}
    for row, (nom, label, texte) in enumerate((
        ('elements', 'Éléments : code | montant CAD | source (une ligne par code)',
         '\n'.join(f'{e.nature} | {e.montant} | {e.source}' for e in p.elements)),
        ('soldes_federaux', 'Soldes ARC confirmés : année | montant CAD | référence de l’avis',
         '\n'.join(f'{s.annee} | {s.montant_confirme} | {s.source}' for s in p.soldes_federaux)),
        ('soldes_quebec', 'Soldes RQ confirmés : année | montant CAD | référence de l’avis',
         '\n'.join(f'{s.annee} | {s.montant_confirme} | {s.source}' for s in p.soldes_quebec))), 3):
        ttk.Label(c, text=label, wraplength=460).grid(row=row, column=0, sticky='w')
        z = tk.Text(c, name=nom+'_7i', height=3, width=55, wrap='word')
        z.insert('1.0', texte); z.grid(row=row, column=1, sticky='ew', pady=5); zones[nom] = z
    ttk.Label(c, text='Codes : '+ '; '.join(f'{k} : {v}' for k, v in ELEMENTS_7I.items()),
        wraplength=970, justify='left').grid(row=6, columnspan=2, sticky='w', pady=8)
    bools = {}
    for row, (nom, label) in enumerate((
        ('residence_quebec_annee', 'Résidence Québec/Canada toute l’année confirmée (hors décès 7H)'),
        ('t691_signale', 'T691 requis signalé par le comptable, indépendamment du repère'),
        ('tp77642_signale', 'TP-776.42 requis signalé par le comptable, indépendamment du repère'),
        ('confirme', 'Éléments exhaustifs vérifiés; soldes distincts confirmés par avis, sources documentées')), 7):
        v = tk.BooleanVar(value=getattr(p, nom)); bools[nom] = v
        tk.Checkbutton(c, name=nom+'_7i', text=label, variable=v, wraplength=970, anchor='w',
            justify='left').grid(row=row, columnspan=2, sticky='w')
    apercu = tk.Text(c, name='trace_7i', height=12, wrap='word', state='disabled')
    apercu.grid(row=11, columnspan=2, sticky='ew', pady=8)
    def afficher(texte):
        apercu.configure(state='normal'); apercu.delete('1.0', 'end'); apercu.insert('1.0', texte); apercu.configure(state='disabled')
    def revoquer(*_):
        bools['confirme'].set(False)
        afficher('Faits modifiés : reconfirmez l’exhaustivité et les sources.')
    source.trace_add('write', revoquer)
    for n, v in bools.items():
        if n != 'confirme': v.trace_add('write', revoquer)
    for z in zones.values():
        z.edit_modified(False)
        def modifie(event):
            if event.widget.edit_modified():
                revoquer(); event.widget.edit_modified(False)
        z.bind('<<Modified>>', modifie)
    def verifier():
        try:
            if dossier_actuel() is not dossier:
                raise ValueError('Dossier modifié : rouvrez la préparation IMR.')
            listes = {}
            for nom, z in zones.items():
                objets = []
                for ligne in z.get('1.0', 'end').splitlines():
                    if not ligne.strip(): continue
                    parties = [x.strip() for x in ligne.split('|', 2)]
                    if len(parties) != 3: raise ValueError('Format requis : code/année | montant | source.')
                    a, montant, src = parties
                    objets.append(ElementImr2025(a, Decimal(montant.replace(',', '.')), src) if nom == 'elements'
                        else SoldeImr2025(int(a), Decimal(montant.replace(',', '.')), src))
                listes[nom] = tuple(objets)
            profil = ProfilImr2025(source=source.get().strip(), **{n:v.get() for n,v in bools.items()}, **listes)
            nouveau = replace(dossier, imr=profil)
            afficher('\n'.join(lignes_imr_2025(nouveau)))
            return profil, nouveau
        except (ValueError, InvalidOperation) as exc:
            messagebox.showerror('Préparation IMR invalide', str(exc), parent=d)
    def sauver():
        r = verifier()
        if r is None: return
        try: appliquer(r[0])
        except ValueError as exc:
            messagebox.showerror('Préparation IMR invalide', str(exc), parent=d); return
        d.destroy()
    def exporter():
        r = verifier()
        if r is None: return
        chemin = filedialog.asksaveasfilename(parent=d, defaultextension='.pdf', filetypes=[('PDF','*.pdf')])
        if not chemin: return
        try:
            from .tax_report_pdf_2025 import exporter_preparation_imr_pdf_2025
            exporter_preparation_imr_pdf_2025(r[1], chemin)
        except (ValueError, OSError) as exc:
            messagebox.showerror('Export IMR impossible', str(exc), parent=d)
    for texte, commande in (('Vérifier et afficher la trace', verifier), ('Appliquer les faits', sauver),
            ('Exporter la préparation PDF', exporter), ('Fermer', d.destroy)):
        ttk.Button(f.actions, text=texte, command=commande).pack(side='left', padx=5)
