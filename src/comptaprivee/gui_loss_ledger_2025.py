"""Saisie de soldes documentés 7F; aucune reconstitution de perte annuelle."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from dataclasses import replace
from decimal import Decimal, InvalidOperation
from .gui_layout import FormulaireDefilant, dimensionner_fenetre
from .tax_loss_ledger_2025 import (
    RegistrePertes2025, PerteNonCapital2025, PerteNetteCapital2025,
    DemandePerte2025, CapaciteReport2025, valider_registre_pertes_2025,
    preparer_pertes_2025, lignes_preparation_pertes_2025, EXCLUSIONS_7F,
)


def ouvrir_pertes_2025(parent, registre, appliquer):
    d = tk.Toplevel(parent)
    d.title('Pertes et reports 2025 - 7F')
    dimensionner_fenetre(d, 1100, 880)
    d.transient(parent); d.grab_set()
    f = FormulaireDefilant(d); c = f.corps; c.columnconfigure(1, weight=1)
    courant = registre
    ttk.Label(c, text='Soldes documentés ARC / Québec - pertes et reports', font=('Segoe UI', 14, 'bold')).grid(row=0,columnspan=2,sticky='w')
    ttk.Label(c, text='Une fiche par nature, juridiction et année. Les montants sont des pertes fiscales disponibles, '
        'après toutes utilisations antérieures. Un reste non demandé est conservé pour le futur. '
        'Aucun remboursement historique calculé. La perte non-capital 2025 externe permet seulement une préparation séparée.',
        wraplength=980,justify='left').grid(row=1,columnspan=2,sticky='w',pady=8)
    liste = ttk.Combobox(c, name='fiches_7f', state='readonly')
    liste.grid(row=2,columnspan=2,sticky='ew',pady=5)
    variables = {}
    labels = {'nature':'Nature : non_capital ou net_capital', 'juridiction':'Juridiction : federal ou quebec',
        'annee_origine':'Année d’origine', 'disponible':'Solde fiscal disponible', 'source':'Source exhaustive du solde et des utilisations',
        'courant':'Demande 2025 (pertes antérieures)',
        'arriere_2022':'Demande 2022 (perte 2025)', 'arriere_2023':'Demande 2023 (perte 2025)', 'arriere_2024':'Demande 2024 (perte 2025)'}
    for y in (2022,2023,2024):
        labels['revenu_'+str(y)] = f'{y} : revenu imposable encore disponible après autres pertes'
        labels['gains_'+str(y)] = f'{y} : gains imposables encore disponibles'
        labels['source_'+str(y)] = f'{y} : source et rapprochement historique'
    for row,(n,label) in enumerate(labels.items(),3):
        valeur = 'non_capital' if n=='nature' else 'federal' if n=='juridiction' else '2024' if n=='annee_origine' else '' if n.startswith('source') else '0'
        v=tk.StringVar(value=valeur);variables[n]=v
        ttk.Label(c,text=label,wraplength=550).grid(row=row,column=0,sticky='w')
        if n in ('nature','juridiction'):
            w=ttk.Combobox(c,name=n+'_7f',textvariable=v,state='readonly',values=('non_capital','net_capital') if n=='nature' else ('federal','quebec'))
        else:
            w=ttk.Entry(c,name=n+'_7f',textvariable=v)
        w.grid(row=row,column=1,sticky='ew',pady=3)
    confirme=tk.BooleanVar(value=False)
    tk.Checkbutton(c,name='confirmation_7f',variable=confirme,wraplength=980,justify='left',anchor='w',
        text='Je confirme les soldes fiscaux et leur historique exhaustif; montants ARC/RQ indépendants; '
        'capital déjà net à 50 %; capacités après pertes antérieures, aucun rajustement annexe N nécessaire; '
        'aucun cas exclu : '+', '.join(EXCLUSIONS_7F)+'.').grid(row=len(labels)+3,columnspan=2,sticky='w',pady=10)
    for v in variables.values():
        v.trace_add('write',lambda *_: confirme.set(False))
    def toutes():
        return [('non_capital',p) for p in courant.pertes_non_capital]+[('net_capital',p) for p in courant.pertes_net_capital]
    def rafraichir():
        liste['values']=[f'{n} / {p.juridiction} / {p.annee_origine}' for n,p in toutes()]
    def charger(_=None):
        if liste.current()<0:return
        n,p=toutes()[liste.current()]
        for nom in variables:
            variables[nom].set('' if nom.startswith('source') else '0')
        for nom,val in {'nature':n,'juridiction':p.juridiction,'annee_origine':p.annee_origine,'disponible':p.disponible,'source':p.source}.items():
            variables[nom].set(str(val))
        for demande in p.demandes:
            variables['courant' if demande.sens=='courant' else 'arriere_'+str(demande.annee_visee)].set(str(demande.montant))
        for cap in courant.capacites:
            if cap.juridiction==p.juridiction and cap.annee_visee in (2022,2023,2024):
                for nom,val in (('revenu',cap.revenu_imposable_disponible),('gains',cap.gains_imposables_disponibles),('source',cap.source)):
                    variables[nom+'_'+str(cap.annee_visee)].set(str(val))
        confirme.set(True)
    liste.bind('<<ComboboxSelected>>',charger)
    def sauver_fiche():
        nonlocal courant
        try:
            if not confirme.get():raise ValueError('Confirmez les faits et exclusions de la fiche.')
            v={n:x.get().strip() for n,x in variables.items()}
            nature=v['nature'];j=v['juridiction'];annee=int(v['annee_origine'])
            demandes=[]
            for nom,sens,y in [('courant','courant',2025)]+[('arriere_'+str(y),'arriere',y) for y in (2022,2023,2024)]:
                montant=Decimal(v[nom].replace(',','.'))
                if montant: demandes.append(DemandePerte2025(sens,y,montant))
            classe=PerteNonCapital2025 if nature=='non_capital' else PerteNetteCapital2025
            p=classe(j,annee,Decimal(v['disponible'].replace(',','.')),v['source'],tuple(demandes),True,True,True)
            nom='pertes_non_capital' if nature=='non_capital' else 'pertes_net_capital'
            pertes=tuple(x for x in getattr(courant,nom) if (x.juridiction,x.annee_origine)!=(j,annee))+(p,)
            caps=list(courant.capacites)
            for y in (2022,2023,2024):
                if v['source_'+str(y)]:
                    cap=CapaciteReport2025(j,y,Decimal(v['revenu_'+str(y)].replace(',','.')),
                        Decimal(v['gains_'+str(y)].replace(',','.')),v['source_'+str(y)],True,True,True,True)
                    caps=[x for x in caps if (x.juridiction,x.annee_visee)!=(j,y)]+[cap]
            nouveau=replace(courant,**{nom:pertes},capacites=tuple(caps))
            valider_registre_pertes_2025(nouveau)
            # Les capacités 2025 proviennent exclusivement de l'estimation annuelle.
            sans_courant=replace(nouveau,
                pertes_non_capital=tuple(replace(x,demandes=tuple(a for a in x.demandes if a.sens!='courant')) for x in nouveau.pertes_non_capital),
                pertes_net_capital=tuple(replace(x,demandes=tuple(a for a in x.demandes if a.sens!='courant')) for x in nouveau.pertes_net_capital))
            preparer_pertes_2025(sans_courant)
            courant=nouveau;rafraichir()
            messagebox.showinfo('Fiche 7F préparée','Fiche conservée dans cette fenêtre. Appliquez le registre pour la conserver au dossier.',parent=d)
        except (ValueError,InvalidOperation) as exc:messagebox.showerror('Pertes 7F invalides',str(exc),parent=d)
    def sauver():
        try:appliquer(courant)
        except ValueError as exc:messagebox.showerror('Pertes 7F invalides',str(exc),parent=d);return
        d.destroy()
    def vider():
        nonlocal courant
        courant=RegistrePertes2025();rafraichir();confirme.set(False)
    def pdf():
        try:
            lignes_preparation_pertes_2025(courant)
            chemin=filedialog.asksaveasfilename(parent=d,defaultextension='.pdf',filetypes=[('PDF','*.pdf')])
            if chemin:
                from .tax_report_pdf_2025 import exporter_preparation_pertes_pdf_2025
                exporter_preparation_pertes_pdf_2025(courant,chemin)
        except ValueError as exc:messagebox.showerror('Préparation 7F',str(exc)+' Pour une demande courante, utilisez l’estimation annuelle et son PDF.',parent=d)
    for texte,commande in (('Préparer la fiche',sauver_fiche),('Appliquer le registre',sauver),('Désactiver les reports',vider),('PDF préparation séparée',pdf),('Fermer',d.destroy)):
        ttk.Button(f.actions,text=texte,command=commande).pack(side='left',padx=4)
    rafraichir()
