"""Inventaire déclaratif 7J : coûts CAD documentés, aucun calcul de revenu."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from dataclasses import replace
from decimal import Decimal, InvalidOperation
from .gui_layout import FormulaireDefilant, dimensionner_fenetre
from .tax_foreign_property_2025 import (
    InventaireEtranger2025, BienEtranger2025, CoutEtranger2025,
    TYPES_7J, PAYS_7J, AVERTISSEMENT, lignes_biens_etrangers_2025,
)


def ouvrir_biens_etrangers_2025(parent, dossier, dossier_actuel, appliquer):
    p = dossier.biens_etrangers or InventaireEtranger2025()
    d = tk.Toplevel(parent)
    d.title('Biens étrangers 2025 - 7J')
    dimensionner_fenetre(d, 1150, 900)
    d.transient(parent); d.grab_set()
    f = FormulaireDefilant(d); c = f.corps; c.columnconfigure(0, weight=1)
    ttk.Label(c, text='Inventaire étranger et obligations déclaratives', font=('Segoe UI', 14, 'bold')).grid(row=0, sticky='w')
    ttk.Label(c, text=AVERTISSEMENT+' Aucun montant ajouté aux revenus. Coûts fiscaux CAD déjà établis, pas la JVM.',
        wraplength=1020, justify='left').grid(row=1, sticky='w', pady=6)
    source = tk.StringVar(value=p.source)
    ttk.Label(c, text='Source du contrôle comptable').grid(row=2, sticky='w')
    ttk.Entry(c, name='source_7j', textvariable=source).grid(row=3, sticky='ew')
    zones = {}
    textes = (
        ('biens', 'Un bien par ligne : référence | type | pays | coût début | coût maximal | coût fin | revenu brut connu | gain/perte connu | source',
         '\n'.join(f'{b.reference} | {b.nature} | {b.pays} | {b.cout_debut} | {b.cout_maximal} | {b.cout_fin} | {b.revenu_brut_connu} | {b.gain_perte_connu} | {b.source}' for b in p.biens)),
        ('couts', 'Chaque changement de coût : référence | instant AAAA-MM-JJTHH:MM:SS | coût CAD. Début 2025-01-01T00:00:00 et fin 2025-12-31T23:59:59 obligatoires, zéro si absent.',
         '\n'.join(f'{b.reference} | {v.moment} | {v.cout}' for b in p.biens for v in b.couts)),
    )
    for i, (nom, label, texte) in enumerate(textes):
        ttk.Label(c, text=label, wraplength=1020, justify='left').grid(row=4+i*2, sticky='w', pady=5)
        z=tk.Text(c, name=nom+'_7j', height=4, wrap='word')
        z.insert('1.0',texte); z.grid(row=5+i*2,sticky='ew'); zones[nom]=z
    ttk.Label(c, text='Types : '+ '; '.join(TYPES_7J)+'. Pays ISO : '+', '.join(PAYS_7J)+
        '. Exclus : usage personnel, régimes enregistrés, entreprise active exclusive, affiliée, structures complexes, crypto ambiguë. '
        'Le pays est celui du débiteur/émetteur/fiducie pour les titres, celui de situation pour les autres biens.',
        wraplength=1020, justify='left').grid(row=8, sticky='w', pady=5)
    bools={}
    for row,(nom,label) in enumerate((
        ('particulier_quebec','Particulier résident Québec/Canada toute l’année, ou première arrivée explicitement signalée ci-dessous'),
        ('premiere_residence_2025','Première résidence au Canada en 2025 : dispense TP-1079.8.BE; ligne 25 à valider manuellement'),
        ('chronologie_complete','Tous les changements et pics sont documentés, dans la même référence horaire; aucune séquence intraseconde non représentée'),
        ('confirme','Qualification fiscale dans les deux juridictions et coûts CAD vérifiés; inventaire exhaustif, exclusions absentes; sources et revenus/gains connus confirmés')),
        9):
        v=tk.BooleanVar(value=getattr(p,nom));bools[nom]=v
        tk.Checkbutton(c,name=nom+'_7j',text=label,variable=v,wraplength=1020,anchor='w',justify='left').grid(row=row,sticky='w')
    apercu=tk.Text(c,name='trace_7j',height=10,wrap='word',state='disabled')
    apercu.grid(row=13,sticky='ew',pady=8)
    def afficher(texte):
        apercu.configure(state='normal');apercu.delete('1.0','end');apercu.insert('1.0',texte);apercu.configure(state='disabled')
    def revoquer(*_):
        bools['confirme'].set(False);afficher('Faits modifiés : reconfirmez le contrôle comptable.')
    source.trace_add('write',revoquer)
    for n,v in bools.items():
        if n != 'confirme':v.trace_add('write',revoquer)
    for z in zones.values():
        z.edit_modified(False)
        def modifie(event):
            if event.widget.edit_modified():revoquer();event.widget.edit_modified(False)
        z.bind('<<Modified>>',modifie)
    def verifier():
        try:
            if dossier_actuel() is not dossier:raise ValueError('Dossier modifié : rouvrez l’inventaire étranger.')
            couts={}
            for ligne in zones['couts'].get('1.0','end').splitlines():
                if not ligne.strip():continue
                parts=[x.strip() for x in ligne.split('|')]
                if len(parts)!=3:raise ValueError('Chronologie : référence | instant ISO | coût CAD requis.')
                ref,moment,montant=parts
                couts.setdefault(ref,[]).append(CoutEtranger2025(moment,Decimal(montant.replace(',','.'))))
            biens=[]
            for ligne in zones['biens'].get('1.0','end').splitlines():
                if not ligne.strip():continue
                parts=[x.strip() for x in ligne.split('|',8)]
                if len(parts)!=9:raise ValueError('Fiche : les neuf colonnes sont obligatoires; zéro connu doit être explicite.')
                ref,nature,pays,*reste=parts
                montants=[Decimal(x.replace(',','.')) for x in reste[:5]]
                biens.append(BienEtranger2025(ref,nature,pays,*montants,reste[5],tuple(couts.pop(ref,())),bools['confirme'].get()))
            if couts:raise ValueError('Chronologie sans fiche de bien correspondante.')
            profil=InventaireEtranger2025(tuple(biens),source.get().strip(),**{n:v.get() for n,v in bools.items()})
            nouveau=replace(dossier,biens_etrangers=profil)
            afficher('\n'.join(lignes_biens_etrangers_2025(nouveau)))
            return profil,nouveau
        except (ValueError,InvalidOperation) as exc:
            messagebox.showerror('Inventaire étranger invalide',str(exc),parent=d)
    def sauver():
        r=verifier()
        if r is None:return
        try:appliquer(r[0])
        except ValueError as exc:messagebox.showerror('Inventaire étranger invalide',str(exc),parent=d);return
        d.destroy()
    def exporter():
        r=verifier()
        if r is None:return
        chemin=filedialog.asksaveasfilename(parent=d,defaultextension='.pdf',filetypes=[('PDF','*.pdf')])
        if not chemin:return
        try:
            from .tax_report_pdf_2025 import exporter_preparation_biens_etrangers_pdf_2025
            exporter_preparation_biens_etrangers_pdf_2025(r[1],chemin)
        except (ValueError,OSError) as exc:messagebox.showerror('Export impossible',str(exc),parent=d)
    for texte,commande in (('Vérifier et afficher la trace',verifier),('Appliquer les faits',sauver),('Exporter la préparation PDF',exporter),('Fermer',d.destroy)):
        ttk.Button(f.actions,text=texte,command=commande).pack(side='left',padx=5)
