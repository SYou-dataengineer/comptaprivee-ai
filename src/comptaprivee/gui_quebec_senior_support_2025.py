"""Soutien aux aînés individuel, ligne 463."""
import tkinter as tk
from tkinter import ttk, messagebox

from .gui_layout import FormulaireDefilant, dimensionner_fenetre
from .tax_quebec_senior_support_2025 import (
    CONFIRMATIONS_6J, SoutienAinesQuebec2025, valider_soutien_aines_quebec_2025,
)


def ouvrir_soutien_aines_quebec_2025(parent, profil, appliquer):
    d = tk.Toplevel(parent)
    d.title("Soutien aux aînés Québec 2025")
    dimensionner_fenetre(d, 1080, 880)
    d.transient(parent)
    d.grab_set()
    f = FormulaireDefilant(d)
    c = f.corps
    c.columnconfigure(1, weight=1)
    ttk.Label(c, text="Soutien aux aînés - ligne 463", font=("Segoe UI", 16, "bold")).grid(
        row=0, columnspan=2, sticky="w")
    ttk.Label(c, text="Profil individuel : 70 ans ou plus fin 2025, citoyen canadien résident toute l'année, "
        "sans conjoint ni personne à charge. Aucun décès, exonération, détention ou cas particulier. "
        "Revenu familial : ligne Québec 275 recalculée. Maximum 2 000 $, réduction de 5,40 % "
        "au-delà de 27 835 $. Crédit remboursable 463 calculé automatiquement; aucun montant manuel.",
        wraplength=950, justify="left").grid(row=1, columnspan=2, sticky="w", pady=8)
    actif = tk.BooleanVar(value=profil.activer)
    ttk.Checkbutton(c, name="activer_6j", text="Activer le soutien aux aînés", variable=actif).grid(
        row=2, columnspan=2, sticky="w")
    variables = {}
    for row, (nom, libelle) in enumerate((("naissance", "Naissance AAAA-MM-JJ"),
            ("source", "Sources des faits et admissibilité 463")), 3):
        v = tk.StringVar(value=getattr(profil, nom))
        variables[nom] = v
        ttk.Label(c, text=libelle, wraplength=450).grid(row=row, column=0, sticky="w", pady=6)
        ttk.Entry(c, name=nom+"_6j", textvariable=v).grid(row=row, column=1, sticky="ew", pady=6)
    confirmations = {}
    for row, (nom, libelle) in enumerate(CONFIRMATIONS_6J.items(), 5):
        v = tk.BooleanVar(value=getattr(profil, nom))
        confirmations[nom] = v
        tk.Checkbutton(c, name=nom+"_6j", variable=v, text=libelle, wraplength=950,
            anchor="w", justify="left").grid(row=row, columnspan=2, sticky="w", pady=3)

    def revoquer(*_):
        for v in confirmations.values():
            v.set(False)

    def sauver():
        try:
            p = valider_soutien_aines_quebec_2025(SoutienAinesQuebec2025(
                activer=actif.get(),
                **{nom: v.get().strip() for nom, v in variables.items()},
                **{nom: v.get() for nom, v in confirmations.items()}))
        except ValueError as erreur:
            messagebox.showerror("Soutien aux aînés invalide", str(erreur), parent=d)
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
