"""Édition des faits 7B; aucune estimation fiscale annuelle partielle."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from decimal import Decimal, InvalidOperation

from .gui_layout import FormulaireDefilant, dimensionner_fenetre
from .tax_self_employment_2025 import (Entreprise2025, CONFIRMATIONS_7B,
    calculer_entreprises_2025, preparer_revenus_autonomes_2025, lignes_preparation_autonome_2025)


def ouvrir_entreprises_2025(parent, entreprises, appliquer):
    d = tk.Toplevel(parent)
    d.title("Entreprises 2025 - préparation 7B")
    dimensionner_fenetre(d, 1050, 850)
    d.transient(parent)
    d.grab_set()
    f = FormulaireDefilant(d)
    c = f.corps
    c.columnconfigure(1, weight=1)
    ttk.Label(c, text="Revenus autonomes simples - préparation avant cotisations", font=("Segoe UI", 15, "bold")).grid(row=0,columnspan=2,sticky="w")
    ttk.Label(c, text="Services, propriétaire unique, exercice au 31 décembre 2025. Deux dépenses seulement : "
        "petits articles de bureau et tenue comptable courante, sans part personnelle. "
        "Pertes et cas complexes exclus. Aucun solde fiscal avant traitement RRQ/RQAP (7C).",
        wraplength=900,justify="left").grid(row=1,columnspan=2,sticky="w",pady=8)
    liste = tk.Listbox(c,name="liste_7b",height=4,exportselection=False)
    liste.grid(row=2,columnspan=2,sticky="ew")
    courantes = list(entreprises)
    selection = [None]
    variables = {}
    libelles = (("reference","Référence / nom de l'entreprise"),("nature","Nature : entreprise ou profession"),
        ("debut","Début AAAA-MM-JJ"),("fin","Fin AAAA-MM-JJ"),("revenu_brut","Revenus bruts acquis"),
        ("frais_bureau","Petits articles de bureau courants"),("frais_comptables","Tenue comptable courante"),
        ("source","Sources et pièces justificatives"))
    for row,(nom,texte) in enumerate(libelles,3):
        v=tk.StringVar(value=str(getattr(Entreprise2025(),nom)))
        variables[nom]=v
        ttk.Label(c,text=texte).grid(row=row,column=0,sticky="w",pady=4)
        if nom == "nature":
            ttk.Combobox(c,name=nom+"_7b",textvariable=v,values=("entreprise","profession"),state="readonly").grid(row=row,column=1,sticky="ew")
        else:
            ttk.Entry(c,name=nom+"_7b",textvariable=v).grid(row=row,column=1,sticky="ew")
    confirmations={}
    for row,(nom,texte) in enumerate(CONFIRMATIONS_7B.items(),11):
        v=tk.BooleanVar(value=False)
        confirmations[nom]=v
        tk.Checkbutton(c,name=nom+"_7b",text=texte,variable=v,wraplength=900,anchor="w",justify="left").grid(row=row,columnspan=2,sticky="w")

    def revoquer(*_):
        for v in confirmations.values(): v.set(False)
    for v in variables.values(): v.trace_add("write",revoquer)

    def rafraichir():
        liste.delete(0,"end")
        for e in courantes: liste.insert("end",e.reference)

    def nouveau():
        selection[0]=None
        liste.selection_clear(0,"end")
        for nom,v in variables.items(): v.set(str(getattr(Entreprise2025(),nom)))

    def charger(_=None):
        if not liste.curselection(): return
        selection[0]=liste.curselection()[0]
        e=courantes[selection[0]]
        for nom,v in variables.items(): v.set(str(getattr(e,nom)))
        for nom,v in confirmations.items(): v.set(getattr(e,nom))

    def retenir():
        try:
            valeurs={nom:v.get().strip() for nom,v in variables.items()}
            for nom in ("revenu_brut","frais_bureau","frais_comptables"):
                valeurs[nom]=Decimal(valeurs[nom].replace(" ","").replace(",","."))
            e=Entreprise2025(**valeurs,**{nom:v.get() for nom,v in confirmations.items()})
            essais=list(courantes)
            if selection[0] is None: essais.append(e)
            else: essais[selection[0]]=e
            calculer_entreprises_2025(tuple(essais))
        except (ValueError,InvalidOperation) as exc:
            messagebox.showerror("Entreprise invalide",str(exc),parent=d)
            return
        courantes[:]=essais
        rafraichir()
        nouveau()

    def supprimer():
        indices = liste.curselection()
        if indices:
            del courantes[indices[0]]
            rafraichir()
            nouveau()

    def sauver():
        # Ne pas perdre silencieusement une saisie non retenue dans la liste.
        if variables["reference"].get().strip():
            messagebox.showerror("Saisie en cours","Retenez la fiche avec Ajouter / remplacer, ou cliquez Nouvelle fiche pour abandonner sa saisie.",parent=d)
            return
        try:
            appliquer(tuple(courantes))
        except ValueError as exc:
            messagebox.showerror("Entreprises non enregistrées",str(exc),parent=d)
            return
        d.destroy()

    liste.bind("<<ListboxSelect>>",charger)
    for texte,commande in (("Nouvelle fiche",nouveau),("Ajouter / remplacer",retenir),("Supprimer",supprimer),
                           ("Appliquer au dossier",sauver),("Fermer",d.destroy)):
        ttk.Button(f.actions,text=texte,command=commande).pack(side="left",padx=4)
    rafraichir()


def afficher_preparation_autonome_2025(parent,dossier,dossier_actuel):
    try:
        p=preparer_revenus_autonomes_2025(dossier,dossier.entreprises)
    except ValueError as exc:
        messagebox.showerror("Préparation 7B indisponible",str(exc),parent=parent)
        return
    d=tk.Toplevel(parent)
    d.title("Préparation 7B - estimation annuelle bloquée")
    dimensionner_fenetre(d,1050,800)
    texte=tk.Text(d,wrap="word")
    texte.pack(fill="both",expand=True)
    texte.insert("1.0","\n".join(lignes_preparation_autonome_2025(p)))
    texte.configure(state="disabled")

    def exporter():
        if dossier_actuel() is not dossier:
            messagebox.showerror("Préparation périmée","Rouvrez la préparation après modification du dossier.",parent=d)
            return
        chemin=filedialog.asksaveasfilename(parent=d,defaultextension=".pdf",filetypes=[("PDF","*.pdf")])
        if not chemin: return
        try:
            from .tax_report_pdf_2025 import exporter_preparation_autonome_pdf_2025
            exporter_preparation_autonome_pdf_2025(p,chemin)
        except (OSError,ValueError) as exc:
            messagebox.showerror("Export 7B impossible",str(exc),parent=d)
    ttk.Button(d,text="Exporter la préparation PDF",command=exporter).pack(side="right",padx=8,pady=8)
