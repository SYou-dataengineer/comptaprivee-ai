"""Volontaires Québec individuel, ligne 390."""
import tkinter as tk
from tkinter import ttk, messagebox

from .gui_layout import FormulaireDefilant, dimensionner_fenetre
from .tax_quebec_volunteers_2025 import (
    CONFIRMATIONS_390, VolontairesQuebec2025, valider_volontaires_quebec_2025,
)


def ouvrir_volontaires_quebec_2025(parent, profil, appliquer):
    d = tk.Toplevel(parent)
    d.title("Volontaires Québec 2025")
    dimensionner_fenetre(d, 1080, 880)
    d.transient(parent)
    d.grab_set()
    f = FormulaireDefilant(d)
    c = f.corps
    c.columnconfigure(1, weight=1)
    ttk.Label(c, text="Volontaires Québec - ligne 390", font=("Segoe UI", 16, "bold")).grid(
        row=0, columnspan=2, sticky="w")
    ttk.Label(c, text="Préparez les activités dans Services bénévoles 5L : pompiers OU sauvetage, au moins 200 heures "
        "de la même activité, sans rémunération. L'admissibilité et les certificats Québec sont confirmés séparément ici. "
        "Crédit non remboursable 390 : 756,56 $. Rémunérations RL-1 L-2 / T4 87, activité mixte et cas particuliers exclus.",
        wraplength=950, justify="left").grid(row=1, columnspan=2, sticky="w", pady=8)
    actif = tk.BooleanVar(value=profil.activer)
    ttk.Checkbutton(c, name="activer_390", text="Activer le crédit volontaires Québec", variable=actif).grid(
        row=2, columnspan=2, sticky="w")
    variables = {}
    for row, (nom, libelle) in enumerate((("source", "Sources des faits et admissibilité Québec 390"),), 3):
        v = tk.StringVar(value=getattr(profil, nom))
        variables[nom] = v
        ttk.Label(c, text=libelle, wraplength=450).grid(row=row, column=0, sticky="w", pady=6)
        ttk.Entry(c, name=nom+"_390", textvariable=v).grid(row=row, column=1, sticky="ew", pady=6)
    confirmations = {}
    for row, (nom, libelle) in enumerate(CONFIRMATIONS_390.items(), 4):
        v = tk.BooleanVar(value=getattr(profil, nom))
        confirmations[nom] = v
        tk.Checkbutton(c, name=nom+"_390", variable=v, text=libelle, wraplength=950,
            anchor="w", justify="left").grid(row=row, columnspan=2, sticky="w", pady=3)

    def revoquer(*_):
        for v in confirmations.values():
            v.set(False)

    def sauver():
        try:
            p = valider_volontaires_quebec_2025(VolontairesQuebec2025(
                activer=actif.get(),
                **{nom: v.get().strip() for nom, v in variables.items()},
                **{nom: v.get() for nom, v in confirmations.items()}))
        except ValueError as erreur:
            messagebox.showerror("Volontaires Québec invalide", str(erreur), parent=d)
            return
        appliquer(p)
        d.destroy()

    def effacer():
        actif.set(False)
        for v in variables.values():
            v.set("")
        revoquer()

    for v in (actif, *variables.values()):
        v.trace_add("write", revoquer)
    ttk.Button(f.actions, text="Effacer", command=effacer).pack(side="left")
    ttk.Button(f.actions, text="Appliquer", command=sauver).pack(side="right")
    ttk.Button(f.actions, text="Fermer", command=d.destroy).pack(side="right")
