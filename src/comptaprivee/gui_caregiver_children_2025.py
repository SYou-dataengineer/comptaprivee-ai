"""Fiches individuelles des enfants — ligne fédérale 30500."""
from dataclasses import fields
from decimal import Decimal, InvalidOperation
import tkinter as tk
from tkinter import ttk, messagebox
from .gui_layout import FormulaireDefilant, dimensionner_fenetre
from .tax_federal_caregiver_child_2025 import (
    AidantNaturelEnfantMoins18Federal2025 as Profil, EnfantAidant30500,
    valider_aidant_naturel_enfant_moins18_federal_2025)

LIBELLES = {
    "enfant_biologique_ou_adopte": "Enfant biologique ou adopté du demandeur ou de son conjoint",
    "enfant_moins_18_fin_2025": "Enfant de moins de 18 ans au 31 décembre 2025",
    "infirmite_physique_ou_mentale": "Infirmité physique ou mentale confirmée",
    "dependance_longue_continue_duree_indeterminee": "Dépendance pour une longue période continue de durée indéterminée",
    "besoin_aide_beaucoup_plus_que_meme_age": "Besoin de beaucoup plus d'aide que les enfants du même âge",
    "enfant_avec_deux_parents_toute_annee": "Enfant vivant avec ses deux parents toute l'année",
    "aucune_garde_partagee": "Aucune garde partagée",
    "aucune_pension_alimentaire": "Aucune pension alimentaire",
    "aucun_autre_reclamant_30500": "Aucun autre réclamant 30500 pour cet enfant",
    "aucun_transfert_conjoint_32600": "Aucun transfert au conjoint de ce montant 30500",
    "preuve_medicale_ou_t2201_confirmee": "Preuve médicale ou T2201 approuvé confirmé",
    "valide_par_comptable": "Fiche individuelle validée par le comptable",
    "source_enfant": "Source des pièces, de l'attribution et de la preuve médicale",
}


def fenetre(parent, titre):
    d = tk.Toplevel(parent)
    d.title(titre)
    dimensionner_fenetre(d, 1080, 850)
    d.transient(parent)
    d.grab_set()
    f = FormulaireDefilant(d)
    f.corps.columnconfigure(1, weight=1)
    def fermer():
        d.destroy()
        if isinstance(parent, tk.Toplevel) and parent.winfo_exists():
            parent.grab_set()
    d.protocol("WM_DELETE_WINDOW", fermer)
    return d, f, fermer


def editer_enfant(parent, enfant, appliquer):
    d, f, fermer = fenetre(parent, "Fiche enfant — 30500")
    identite = {}
    for rang, (nom, texte) in enumerate((("reference", "Référence unique locale (sans NAS)"),
            ("nom", "Nom complet de l’enfant"), ("naissance", "Date de naissance (AAAA-MM-JJ)"))):
        v = tk.StringVar(value=getattr(enfant, nom))
        identite[nom] = v
        ttk.Label(f.corps, text=texte).grid(row=rang, column=0, sticky="w")
        ttk.Entry(f.corps, name=nom + "_5y", textvariable=v).grid(row=rang, column=1, sticky="ew", pady=4)
    variables = {}
    for rang, (nom, texte) in enumerate(LIBELLES.items(), start=3):
        valeur = getattr(enfant.profil, nom)
        v = tk.BooleanVar(value=valeur) if type(valeur) is bool else tk.StringVar(value=str(valeur))
        variables[nom] = v
        if type(valeur) is bool:
            ttk.Checkbutton(f.corps, name=nom + "_5y", text=texte, variable=v).grid(
                row=rang, column=0, columnspan=2, sticky="w", pady=4)
        else:
            ttk.Label(f.corps, text=texte, wraplength=460).grid(row=rang, column=0, sticky="w", pady=4)
            w = ttk.Entry(f.corps, name=nom + "_5y", textvariable=v)
            w.grid(row=rang, column=1, sticky="ew", pady=4)
    def revoquer(*_):
        for nom in ("valide_par_comptable", "preuve_medicale_ou_t2201_confirmee"):
            variables[nom].set(False)
    for v in identite.values():
        v.trace_add("write", revoquer)
    for nom, v in variables.items():
        if nom not in ("valide_par_comptable", "preuve_medicale_ou_t2201_confirmee"):
            v.trace_add("write", revoquer)
    for nom in ("preuve_medicale_ou_t2201_confirmee",):
        variables[nom].trace_add("write", lambda *_: variables["valide_par_comptable"].set(False))
    def sauver():
        try:
            valeurs = {nom: v.get() for nom, v in variables.items()}
            for champ in fields(Profil):
                if champ.name in valeurs and isinstance(champ.default, Decimal):
                    valeurs[champ.name] = Decimal(valeurs[champ.name].strip().replace(" ", "").replace(",", ".") or "0")
            ident = {nom: v.get().strip() for nom, v in identite.items()}
            nouveau = EnfantAidant30500(**ident, profil=Profil(reclamer_montant=True, **valeurs))
            valider_aidant_naturel_enfant_moins18_federal_2025(Profil(reclamer_montant=True, valide_par_comptable=True,
                identites_distinctes_confirmees=True, enfants_detailles=(nouveau,)))
        except (ValueError, InvalidOperation) as erreur:
            messagebox.showerror("Fiche 30500 invalide", str(erreur), parent=d)
            return
        appliquer(nouveau)
        fermer()
    ttk.Button(f.actions, text="Enregistrer l’enfant", command=sauver).pack(side="right")
    ttk.Button(f.actions, text="Annuler", command=fermer).pack(side="right")


def ouvrir_enfants_30500_2025(parent, profil, appliquer):
    if profil.enfant_reclame_30400:
        raise ValueError("La combinaison 30400/30500 reste dans le dialogue individuel.")
    d, f, fermer = fenetre(parent, "Enfants — 30500 / 30499")
    enfants = list(profil.enfants_detailles)
    if not enfants and profil.reclamer_montant:
        enfants.append(EnfantAidant30500(reference=profil.reference_enfant or "enfant-1", profil=profil))
    ttk.Label(f.corps, text="Une fiche par enfant admissible vivant avec ses deux parents toute l'année. "
        "Le montant 30500 est calculé à 2687 $ par enfant; une seule attribution par enfant. "
        "Garde partagée, pensions et combinaison avec 30400 hors de ce mode. "
        "Complétez l'identité des anciennes fiches à partir des pièces.",
        wraplength=950).grid(row=0, column=0, columnspan=2, sticky="w", pady=10)
    table = ttk.Treeview(f.corps, name="enfants_5y", columns=("enfant",), show="headings", height=8)
    table.heading("enfant", text="Référence — nom — naissance")
    table.column("enfant", width=950)
    table.grid(row=1, column=0, columnspan=2, sticky="ew")
    identites = tk.BooleanVar(value=profil.identites_distinctes_confirmees)
    valide = tk.BooleanVar(value=bool(profil.enfants_detailles) and profil.valide_par_comptable)
    def rafraichir():
        table.delete(*table.get_children())
        for i, p in enumerate(enfants):
            table.insert("", "end", iid=str(i), values=(f"{p.reference} — {p.nom} — {p.naissance}",))
    def changement():
        identites.set(False)
        valide.set(False)
        rafraichir()
    def editer(nouveau):
        if not nouveau and not table.selection():
            return
        i = None if nouveau else int(table.selection()[0])
        def sauver(p):
            if i is None:
                enfants.append(p)
            else:
                enfants[i] = p
            changement()
        editer_enfant(d, EnfantAidant30500() if nouveau else enfants[i], sauver)
    def retirer():
        if table.selection():
            del enfants[int(table.selection()[0])]
            changement()
    actions = ttk.Frame(f.corps)
    actions.grid(row=2, column=0, columnspan=2, sticky="w", pady=8)
    for texte, commande in (("Ajouter", lambda: editer(True)), ("Modifier", lambda: editer(False)), ("Retirer", retirer)):
        ttk.Button(actions, text=texte, command=commande).pack(side="left", padx=4)
    ttk.Checkbutton(f.corps, name="identites_5y", text="Enfants distincts et références rapprochées des pièces",
        variable=identites).grid(row=3, column=0, columnspan=2, sticky="w")
    ttk.Checkbutton(f.corps, name="valide_5y", text="Ensemble des fiches validé par le comptable",
        variable=valide).grid(row=4, column=0, columnspan=2, sticky="w")
    identites.trace_add("write", lambda *_: valide.set(False))
    def sauver():
        try:
            nouveau = (Profil(reclamer_montant=True, valide_par_comptable=valide.get(),
                identites_distinctes_confirmees=identites.get(), enfants_detailles=tuple(enfants))
                if enfants else Profil())
            valider_aidant_naturel_enfant_moins18_federal_2025(nouveau)
        except ValueError as erreur:
            messagebox.showerror("Enfants 30500 invalides", str(erreur), parent=d)
            return
        appliquer(nouveau)
        fermer()
    ttk.Button(f.actions, text="Appliquer les enfants", command=sauver).pack(side="right")
    ttk.Button(f.actions, text="Annuler", command=fermer).pack(side="right")
    rafraichir()
