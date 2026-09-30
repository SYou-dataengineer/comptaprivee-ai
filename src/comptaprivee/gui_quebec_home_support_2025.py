"""Maintien à domicile individuel, ligne 458."""
import tkinter as tk
from tkinter import ttk, messagebox

from .gui_layout import FormulaireDefilant, dimensionner_fenetre
from .tax_quebec_home_support_2025 import (
    CONFIRMATIONS_6K, MaintienDomicileQuebec2025, valider_maintien_domicile_quebec_2025, MOIS_2025, montant_maintien_depuis_champ,
)


def ouvrir_maintien_domicile_quebec_2025(parent, profil, appliquer):
    d = tk.Toplevel(parent)
    d.title("Maintien à domicile Québec 2025")
    dimensionner_fenetre(d, 1080, 880)
    d.transient(parent)
    d.grab_set()
    f = FormulaireDefilant(d)
    c = f.corps
    c.columnconfigure(1, weight=1)
    ttk.Label(c, text="Maintien à domicile - ligne 458", font=("Segoe UI", 16, "bold")).grid(
        row=0, columnspan=2, sticky="w")
    ttk.Label(c, text="Logement locatif ordinaire uniquement; personne autonome, 70 ans dès le 1er janvier 2025, "
        "seule dans le même logement toute l'année. Douze loyers payés; revenu familial 275 au plus 71 010 $. "
        "Autres logements, services supplémentaires, avances et cumul de frais médicaux exclus. "
        "5 % des loyers retenus entre 600 et 1 200 $, puis crédit 39 %. Maximum de ce sous-profil : 280,80 $.",
        wraplength=950, justify="left").grid(row=1, columnspan=2, sticky="w", pady=8)
    actif = tk.BooleanVar(value=profil.activer)
    ttk.Checkbutton(c, name="activer_6k", text="Activer le maintien à domicile", variable=actif).grid(
        row=2, columnspan=2, sticky="w")
    variables = {}
    for row, (nom, libelle) in enumerate((("naissance", "Naissance AAAA-MM-JJ"),
            ("source", "Sources des faits et admissibilité 458")), 3):
        v = tk.StringVar(value=getattr(profil, nom))
        variables[nom] = v
        ttk.Label(c, text=libelle, wraplength=450).grid(row=row, column=0, sticky="w", pady=6)
        ttk.Entry(c, name=nom+"_6k", textvariable=v).grid(row=row, column=1, sticky="ew", pady=6)
    loyers = []
    for i, mois in enumerate(MOIS_2025):
        v = tk.StringVar(value=str(profil.loyers_mensuels[i]) if profil.loyers_mensuels else "")
        loyers.append(v)
        ttk.Label(c, text="Loyer payé - " + mois + " ($)").grid(row=5+i, column=0, sticky="w", pady=4)
        ttk.Entry(c, name="loyer_"+str(i+1)+"_6k", textvariable=v).grid(row=5+i, column=1, sticky="ew", pady=4)
    confirmations = {}
    for row, (nom, libelle) in enumerate(CONFIRMATIONS_6K.items(), 17):
        v = tk.BooleanVar(value=getattr(profil, nom))
        confirmations[nom] = v
        tk.Checkbutton(c, name=nom+"_6k", variable=v, text=libelle, wraplength=950,
            anchor="w", justify="left").grid(row=row, columnspan=2, sticky="w", pady=3)

    def revoquer(*_):
        for v in confirmations.values():
            v.set(False)

    def sauver():
        try:
            montants = tuple(montant_maintien_depuis_champ(v.get()) for v in loyers)
            p = valider_maintien_domicile_quebec_2025(MaintienDomicileQuebec2025(
                activer=actif.get(), loyers_mensuels=montants if any(montants) else (),
                **{nom: v.get().strip() for nom, v in variables.items()},
                **{nom: v.get() for nom, v in confirmations.items()}))
        except ValueError as erreur:
            messagebox.showerror("Maintien à domicile invalide", str(erreur), parent=d)
            return
        appliquer(p)
        d.destroy()

    def effacer():
        actif.set(False)
        for v in (*variables.values(), *loyers):
            v.set("")
        revoquer()

    for v in (actif, *variables.values(), *loyers):
        v.trace_add("write", revoquer)
    ttk.Button(f.actions, text="Effacer", command=effacer).pack(side="left")
    ttk.Button(f.actions, text="Appliquer", command=sauver).pack(side="right")
    ttk.Button(f.actions, text="Fermer", command=d.destroy).pack(side="right")
