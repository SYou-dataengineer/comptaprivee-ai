"""7G : formulaire de préparation, sans estimation interprovinciale."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from dataclasses import replace
from decimal import Decimal, InvalidOperation
from .gui_layout import FormulaireDefilant, dimensionner_fenetre
from .tax_multiple_jurisdictions_2025 import (
    Administrations2025, CONFIRMATIONS_7G, PROVINCES_7G,
    preparer_administrations_2025, lignes_preparation_administrations_2025,
)


def ouvrir_administrations_2025(parent, dossier, dossier_actuel, appliquer):
    if len(dossier.entreprises) != 1:
        raise ValueError('7G : une seule fiche entreprise requise.')
    e = dossier.entreprises[0]
    p = e.administrations or Administrations2025(reference_entreprise=e.reference,
        revenu_quebec=e.revenu_brut-e.frais_bureau-e.frais_comptables)
    d=tk.Toplevel(parent);d.title('Administrations multiples 2025 - 7G')
    dimensionner_fenetre(d,1100,900);d.transient(parent);d.grab_set()
    f=FormulaireDefilant(d);c=f.corps;c.columnconfigure(1,weight=1)
    ttk.Label(c,text='Préparation interprovinciale - aucun impôt estimé',font=('Segoe UI',14,'bold')).grid(row=0,columnspan=2,sticky='w')
    ttk.Label(c,text=f'Entreprise : {e.reference}. Revenu net : {e.revenu_brut-e.frais_bureau-e.frais_comptables:.2f} $. '
        'Un établissement principal au Québec et au plus un établissement stable ailleurs au Canada. '
        'La présence hors Québec suspend le calcul annuel; T2203 et TP-22 restent à préparer hors du moteur.',
        wraplength=970,justify='left').grid(row=1,columnspan=2,sticky='w',pady=8)
    presence=tk.BooleanVar(value=p.etablissement_hors_quebec)
    tk.Checkbutton(c,name='presence_7g',text='Établissement stable hors Québec présent',variable=presence).grid(row=2,columnspan=2,sticky='w')
    variables={}
    labels={'province':'Province/territoire hors Québec (code)', 'revenu_quebec':'Revenu net attribué au Québec',
        'revenu_hors_quebec':'Revenu net attribué hors Québec', 'methode':'Méthode documentée de ventilation',
        'source':'Pièces justificatives et source de la répartition'}
    for row,(n,label) in enumerate(labels.items(),3):
        v=tk.StringVar(value=str(getattr(p,n)));variables[n]=v
        ttk.Label(c,text=label,wraplength=510).grid(row=row,column=0,sticky='w')
        if n=='province':
            w=ttk.Combobox(c,name=n+'_7g',textvariable=v,values=('',*PROVINCES_7G),state='readonly')
        else:w=ttk.Entry(c,name=n+'_7g',textvariable=v)
        w.grid(row=row,column=1,sticky='ew',pady=5)
    confirmations={}
    for row,(n,label) in enumerate(CONFIRMATIONS_7G.items(),8):
        v=tk.BooleanVar(value=getattr(p,n));confirmations[n]=v
        tk.Checkbutton(c,name=n+'_7g',text=label,variable=v,wraplength=970,justify='left',anchor='w').grid(row=row,columnspan=2,sticky='w',pady=4)
    apercu=tk.Text(c,name='trace_7g',height=12,wrap='word',state='disabled')
    apercu.grid(row=14,columnspan=2,sticky='ew',pady=10)
    def afficher(texte):
        apercu.configure(state='normal');apercu.delete('1.0','end');apercu.insert('1.0',texte);apercu.configure(state='disabled')
    def revoquer(*_):
        for v in confirmations.values():v.set(False)
        afficher('Faits modifiés : reconfirmez et vérifiez la préparation.')
    for v in variables.values():v.trace_add('write',revoquer)
    presence.trace_add('write',revoquer)
    def verifier():
        try:
            if dossier_actuel() is not dossier:
                raise ValueError('Dossier modifié : rouvrez la préparation 7G.')
            valeurs={n:v.get().strip() for n,v in variables.items()}
            for n in ('revenu_quebec','revenu_hors_quebec'):
                valeurs[n]=Decimal(valeurs[n].replace(' ','').replace(',','.'))
            profil=Administrations2025(reference_entreprise=e.reference,etablissement_hors_quebec=presence.get(),
                **valeurs,**{n:v.get() for n,v in confirmations.items()})
            faits=replace(e,administrations=profil,services_quebec=not profil.etablissement_hors_quebec)
            prepare=replace(dossier,entreprises=(faits,))
            resultat=preparer_administrations_2025(prepare)
            afficher('\n'.join(lignes_preparation_administrations_2025(resultat)))
            return profil,prepare
        except (ValueError,InvalidOperation) as exc:
            messagebox.showerror('Préparation 7G invalide',str(exc),parent=d)
            return None
    def sauver():
        resultat=verifier()
        if resultat is None:return
        try:appliquer(resultat[0])
        except ValueError as exc:messagebox.showerror('Préparation 7G invalide',str(exc),parent=d);return
        d.destroy()
    def exporter():
        resultat=verifier()
        if resultat is None:return
        chemin=filedialog.asksaveasfilename(parent=d,defaultextension='.pdf',filetypes=[('PDF','*.pdf')])
        if not chemin:return
        try:
            from .tax_report_pdf_2025 import exporter_preparation_administrations_pdf_2025
            exporter_preparation_administrations_pdf_2025(resultat[1],chemin)
        except (OSError,ValueError) as exc:messagebox.showerror('Export 7G impossible',str(exc),parent=d)
    for texte,commande in (('Vérifier et afficher la trace',verifier),('Appliquer les faits',sauver),('Exporter la préparation PDF',exporter),('Fermer',d.destroy)):
        ttk.Button(f.actions,text=texte,command=commande).pack(side='left',padx=5)
