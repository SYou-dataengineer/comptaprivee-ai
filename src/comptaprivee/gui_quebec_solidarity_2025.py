"""Préparation des faits annexe D, sans montant ni transmission."""
import tkinter as tk
from tkinter import ttk, messagebox

from .gui_layout import FormulaireDefilant, dimensionner_fenetre
from .tax_quebec_solidarity_2025 import (
    CONFIRMATIONS_6H, SolidariteQuebec2025, valider_solidarite_quebec_2025,
)


def ouvrir_solidarite_quebec_2025(parent, profil, appliquer):
    d = tk.Toplevel(parent)
    d.title("Solidarité Québec - préparation annexe D 2025")
    dimensionner_fenetre(d, 1080, 880)
    d.transient(parent)
    d.grab_set()
    f = FormulaireDefilant(d)
    c = f.corps
    c.columnconfigure(1, weight=1)
    ttk.Label(c, text="Préparation annexe D - TVQ individuelle", font=("Segoe UI", 16, "bold")).grid(
        row=0, columnspan=2, sticky="w")
    ttk.Label(c, text="Faits 2025 pour juillet 2026 à juin 2027. Aucun montant calculé par ComptaPrivée AI; "
        "montant final déterminé séparément par Revenu Québec, sans effet sur le remboursement/solde TP-1 2025. "
        "Revenu familial : ligne Québec 275 recalculée lors de l'estimation. "
        "Profil limité aux adultes citoyens canadiens, résidents toute l'année, sans conjoint ni enfant. "
        "Logement, villages nordiques et cas particuliers exclus. Aucune annexe officielle produite ou transmise.",
        wraplength=950, justify="left").grid(row=1, columnspan=2, sticky="w", pady=8)
    actif = tk.BooleanVar(value=profil.activer)
    seul = tk.BooleanVar(value=profil.vit_seul_toute_annee)
    ttk.Checkbutton(c, name="activer_6h", text="Activer la préparation de l'admissibilité TVQ", variable=actif).grid(
        row=2, columnspan=2, sticky="w")
    variables = {}
    for row, (nom, libelle) in enumerate((("naissance", "Naissance AAAA-MM-JJ"),
            ("source", "Sources des faits et examen de l'annexe D")), 3):
        v = tk.StringVar(value=getattr(profil, nom))
        variables[nom] = v
        ttk.Label(c, text=libelle, wraplength=450).grid(row=row, column=0, sticky="w", pady=6)
        ttk.Entry(c, name=nom+"_6h", textvariable=v).grid(row=row, column=1, sticky="ew", pady=6)
    ttk.Checkbutton(c, name="vit_seul_toute_annee_6h", variable=seul,
        text="A vécu seul dans une habitation pendant toute l'année 2025 (annexe D, ligne 12)").grid(
        row=5, columnspan=2, sticky="w", pady=6)
    confirmations = {}
    for row, (nom, libelle) in enumerate(CONFIRMATIONS_6H.items(), 6):
        v = tk.BooleanVar(value=getattr(profil, nom))
        confirmations[nom] = v
        tk.Checkbutton(c, name=nom+"_6h", variable=v, text=libelle, wraplength=950,
            anchor="w", justify="left").grid(row=row, columnspan=2, sticky="w", pady=3)

    def revoquer(*_):
        for v in confirmations.values():
            v.set(False)

    def sauver():
        try:
            p = valider_solidarite_quebec_2025(SolidariteQuebec2025(
                activer=actif.get(), vit_seul_toute_annee=seul.get(),
                **{nom: v.get().strip() for nom, v in variables.items()},
                **{nom: v.get() for nom, v in confirmations.items()}))
        except ValueError as erreur:
            messagebox.showerror("Préparation solidarité invalide", str(erreur), parent=d)
            return
        appliquer(p)
        d.destroy()

    def effacer():
        actif.set(False)
        seul.set(False)
        for v in variables.values():
            v.set("")
        revoquer()

    for v in (actif, seul, *variables.values()):
        v.trace_add("write", revoquer)
    ttk.Button(f.actions, text="Effacer", command=effacer).pack(side="left")
    ttk.Button(f.actions, text="Appliquer", command=sauver).pack(side="right")
    ttk.Button(f.actions, text="Fermer", command=d.destroy).pack(side="right")
