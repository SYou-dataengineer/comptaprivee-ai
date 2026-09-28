"""Confirmation du profil salarié de prolongation de carrière, Québec 2025."""
import tkinter as tk
from tkinter import ttk, messagebox
from .gui_layout import FormulaireDefilant, dimensionner_fenetre
from .tax_quebec_career_extension_2025 import ProlongationCarriereQuebec2025, CONFIRMATIONS_6D, valider_carriere_quebec_2025


def ouvrir_carriere_quebec_2025(parent, profil, appliquer):
    d = tk.Toplevel(parent); d.title("Prolongation de carrière Québec — ligne 391")
    dimensionner_fenetre(d, 1020, 820); d.transient(parent); d.grab_set()
    f = FormulaireDefilant(d); c = f.corps; c.columnconfigure(1, weight=1)
    ttk.Label(c, text="Prolongation de carrière Québec 2025 — salarié", font=("Segoe UI", 16, "bold")).grid(row=0, columnspan=2, sticky="w")
    ttk.Label(c, text="65 ans ou plus au 31 décembre 2025. Salaire et revenu net calculés depuis le dossier. "
        "Le crédit est de 14 % du salaire admissible excédant 7 500 $, sur au plus 12 500 $. "
        "Réduction de 7 % du revenu net au-delà de 56 500 $, puis plafond d'impôt TP-752.PC. "
        "Crédit non remboursable; aucun montant à saisir. Les autres profils de travail restent hors périmètre.",
        wraplength=900, justify="left").grid(row=1, columnspan=2, sticky="w", pady=8)
    actif = tk.BooleanVar(value=profil.reclamer)
    ttk.Checkbutton(c, name="reclamer_6d", text="Demander le crédit Québec 391", variable=actif).grid(row=2, columnspan=2, sticky="w")
    naissance = tk.StringVar(value=profil.naissance); source = tk.StringVar(value=profil.source)
    for row, nom, label, var in ((3, "naissance_6d", "Naissance (AAAA-MM-JJ)", naissance),
                               (4, "source_6d", "Source de l'âge et des vérifications d'emploi", source)):
        ttk.Label(c, text=label).grid(row=row, column=0, sticky="w")
        ttk.Entry(c, name=nom, textvariable=var).grid(row=row, column=1, sticky="ew", pady=4)
    confirmations = {}
    for row, (nom, label) in enumerate(CONFIRMATIONS_6D.items(), 5):
        confirmations[nom] = tk.BooleanVar(value=getattr(profil, nom))
        tk.Checkbutton(c, name=nom+"_6d", text=label, variable=confirmations[nom], wraplength=920,
            anchor="w", justify="left").grid(row=row, columnspan=2, sticky="w", pady=3)

    def revoquer(*_):
        for v in confirmations.values(): v.set(False)

    def valider():
        try:
            p = valider_carriere_quebec_2025(ProlongationCarriereQuebec2025(reclamer=actif.get(),
                naissance=naissance.get().strip(), source=source.get().strip(),
                **{nom: v.get() for nom, v in confirmations.items()}))
        except ValueError as erreur:
            messagebox.showerror("Carrière Québec invalide", str(erreur), parent=d); return
        appliquer(p); d.destroy()

    def effacer():
        actif.set(False); naissance.set(""); source.set("")

    for v in (actif, naissance, source): v.trace_add("write", revoquer)
    ttk.Button(f.actions, text="Effacer", command=effacer).pack(side="left")
    ttk.Button(f.actions, text="Appliquer", command=valider).pack(side="right")
    ttk.Button(f.actions, text="Fermer", command=d.destroy).pack(side="right")
