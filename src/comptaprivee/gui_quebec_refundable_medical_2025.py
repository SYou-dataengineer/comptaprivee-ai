"""Confirmation du crédit médical remboursable Québec 2025."""
import tkinter as tk
from tkinter import ttk, messagebox
from .gui_layout import FormulaireDefilant, dimensionner_fenetre
from .tax_quebec_refundable_medical_2025 import MedicalRemboursableQuebec2025, CONFIRMATIONS_6E, valider_medical_remboursable_quebec_2025


def ouvrir_medical_remboursable_quebec_2025(parent, profil, appliquer):
    d = tk.Toplevel(parent); d.title("Crédit médical remboursable Québec — ligne 462")
    dimensionner_fenetre(d, 1020, 820); d.transient(parent); d.grab_set()
    f = FormulaireDefilant(d); c = f.corps; c.columnconfigure(1, weight=1)
    ttk.Label(c, text="Crédit médical remboursable Québec 2025", font=("Segoe UI", 16, "bold")).grid(row=0, columnspan=2, sticky="w")
    ttk.Label(c, text="18 ans ou plus au 31 décembre 2025. Profil individuel sans conjoint ni personne à charge. "
        "Revenu de travail minimal : 3 750 $, après déductions 205/207 et avantages case 211. "
        "Le crédit remboursable dépend de la ligne 381 et du revenu net Québec, recalculés depuis le dossier. "
        "Frais médicaux à documenter dans leur écran; aucun montant calculé à saisir ici.",
        wraplength=900, justify="left").grid(row=1, columnspan=2, sticky="w", pady=8)
    actif = tk.BooleanVar(value=profil.reclamer)
    ttk.Checkbutton(c, name="reclamer_6e", text="Demander le crédit médical Québec 462", variable=actif).grid(row=2, columnspan=2, sticky="w")
    naissance = tk.StringVar(value=profil.naissance); source = tk.StringVar(value=profil.source)
    for row, nom, label, var in ((3, "naissance_6e", "Naissance (AAAA-MM-JJ)", naissance),
                               (4, "source_6e", "Source de l'âge, des frais et du périmètre", source)):
        ttk.Label(c, text=label).grid(row=row, column=0, sticky="w")
        ttk.Entry(c, name=nom, textvariable=var).grid(row=row, column=1, sticky="ew", pady=4)
    confirmations = {}
    for row, (nom, label) in enumerate(CONFIRMATIONS_6E.items(), 5):
        confirmations[nom] = tk.BooleanVar(value=getattr(profil, nom))
        tk.Checkbutton(c, name=nom+"_6e", text=label, variable=confirmations[nom], wraplength=920,
            anchor="w", justify="left").grid(row=row, columnspan=2, sticky="w", pady=3)

    def revoquer(*_):
        for v in confirmations.values(): v.set(False)

    def valider():
        try:
            p = valider_medical_remboursable_quebec_2025(MedicalRemboursableQuebec2025(reclamer=actif.get(),
                naissance=naissance.get().strip(), source=source.get().strip(),
                **{nom: v.get() for nom, v in confirmations.items()}))
        except ValueError as erreur:
            messagebox.showerror("Crédit médical Québec invalide", str(erreur), parent=d); return
        appliquer(p); d.destroy()

    def effacer():
        actif.set(False); naissance.set(""); source.set("")

    for v in (actif, naissance, source): v.trace_add("write", revoquer)
    ttk.Button(f.actions, text="Effacer", command=effacer).pack(side="left")
    ttk.Button(f.actions, text="Appliquer", command=valider).pack(side="right")
    ttk.Button(f.actions, text="Fermer", command=d.destroy).pack(side="right")
