"""Prime au travail individuelle, annexe P 2025."""
import tkinter as tk
from tkinter import ttk, messagebox

from .gui_layout import FormulaireDefilant, dimensionner_fenetre
from .tax_quebec_work_premium_2025 import (
    CONFIRMATIONS_6I, PrimeTravailQuebec2025, valider_prime_travail_quebec_2025, montant_prime_depuis_champ,
)


def ouvrir_prime_travail_quebec_2025(parent, profil, appliquer):
    d = tk.Toplevel(parent)
    d.title("Prime au travail Québec 2025")
    dimensionner_fenetre(d, 1080, 880)
    d.transient(parent)
    d.grab_set()
    f = FormulaireDefilant(d)
    c = f.corps
    c.columnconfigure(1, weight=1)
    ttk.Label(c, text="Prime au travail individuelle - annexe P", font=("Segoe UI", 16, "bold")).grid(
        row=0, columnspan=2, sticky="w")
    ttk.Label(c, text="Prime ordinaire et comparaison adaptée si admissible. Adulte sans conjoint ni enfant; "
        "revenu de travail limité à la ligne 101 moins la case 211. Revenu familial : ligne 275 recalculée. "
        "Crédit à la ligne 456; avances RL-19 A intégrales à la ligne 441. "
        "Supplément de transition et bouclier fiscal exclus : examen séparé requis. "
        "Produits exacts conservés; représentation au cent selon la convention générale du moteur, "
        "sans règle d'arrondi particulière de l'annexe P présumée.",
        wraplength=950, justify="left").grid(row=1, columnspan=2, sticky="w", pady=8)
    actif = tk.BooleanVar(value=profil.activer)
    ttk.Checkbutton(c, name="activer_6i", text="Activer la prime au travail", variable=actif).grid(
        row=2, columnspan=2, sticky="w")
    variables = {}
    for row, (nom, libelle) in enumerate((("naissance", "Naissance AAAA-MM-JJ"),
            ("source", "Sources des faits et examen de l'annexe P"),
            ("avances_rl19_a", "Avances RL-19 A ($), zéro si aucune")), 3):
        v = tk.StringVar(value=str(getattr(profil, nom)))
        variables[nom] = v
        ttk.Label(c, text=libelle, wraplength=450).grid(row=row, column=0, sticky="w", pady=6)
        ttk.Entry(c, name=nom+"_6i", textvariable=v).grid(row=row, column=1, sticky="ew", pady=6)
    adaptee = {}
    for row, (nom, libelle) in enumerate((
        ("droit_376_confirme", "Droit au montant de la ligne 376 confirmé pour 2025"),
        ("prestations_contraintes_2020_2025_confirmees", "Prestations pour contraintes sévères admissibles reçues en 2020-2025")), 6):
        v = tk.BooleanVar(value=getattr(profil, nom))
        adaptee[nom] = v
        ttk.Checkbutton(c, name=nom+"_6i", variable=v, text=libelle).grid(
            row=row, columnspan=2, sticky="w", pady=6)
    confirmations = {}
    for row, (nom, libelle) in enumerate(CONFIRMATIONS_6I.items(), 8):
        v = tk.BooleanVar(value=getattr(profil, nom))
        confirmations[nom] = v
        tk.Checkbutton(c, name=nom+"_6i", variable=v, text=libelle, wraplength=950,
            anchor="w", justify="left").grid(row=row, columnspan=2, sticky="w", pady=3)

    def revoquer(*_):
        for v in confirmations.values():
            v.set(False)

    def sauver():
        try:
            p = valider_prime_travail_quebec_2025(PrimeTravailQuebec2025(
                activer=actif.get(),
                **{nom: v.get() for nom, v in adaptee.items()},
                **{nom: montant_prime_depuis_champ(v.get()) if nom == "avances_rl19_a"
                    else v.get().strip() for nom, v in variables.items()},
                **{nom: v.get() for nom, v in confirmations.items()}))
        except ValueError as erreur:
            messagebox.showerror("Prime au travail invalide", str(erreur), parent=d)
            return
        appliquer(p)
        d.destroy()

    def effacer():
        actif.set(False)
        for v in adaptee.values():
            v.set(False)
        for v in variables.values():
            v.set("")
        revoquer()

    for v in (actif, *adaptee.values(), *variables.values()):
        v.trace_add("write", revoquer)
    ttk.Button(f.actions, text="Effacer", command=effacer).pack(side="left")
    ttk.Button(f.actions, text="Appliquer", command=sauver).pack(side="right")
    ttk.Button(f.actions, text="Fermer", command=d.destroy).pack(side="right")
