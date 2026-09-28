"""Première habitation au Québec, TP-752.HA 2025."""
from decimal import Decimal, InvalidOperation
import tkinter as tk
from tkinter import ttk, messagebox
from .gui_layout import FormulaireDefilant, dimensionner_fenetre
from .tax_quebec_home_buyers_2025 import AchatHabitationQuebec2025, CONFIRMATIONS_6C, valider_achat_quebec_2025


def ouvrir_achat_quebec_2025(parent, profil, appliquer):
    d = tk.Toplevel(parent); d.title("Achat habitation Québec — ligne 396")
    dimensionner_fenetre(d, 1040, 860); d.transient(parent); d.grab_set()
    f = FormulaireDefilant(d); c = f.corps; c.columnconfigure(1, weight=1)
    ttk.Label(c, text="Première habitation Québec — TP-752.HA", font=("Segoe UI", 16, "bold")).grid(row=0, columnspan=2, sticky="w")
    ttk.Label(c, text="Crédit non remboursable : maximum commun de 1 400 $, moins les parts demandées ailleurs. "
        "L'estimation calcule aussi le plafond d'impôt selon TP-752.HA. "
        "Habitation au Québec uniquement. Le crédit fédéral reste un profil distinct. "
        "Exception handicap, décès et résidence partielle non pris en charge dans ce profil.",
        wraplength=910, justify="left").grid(row=1, columnspan=2, sticky="w", pady=8)
    actif = tk.BooleanVar(value=profil.reclamer)
    ttk.Checkbutton(c, name="reclamer_6c", text="Demander le crédit Québec 396", variable=actif).grid(row=2, columnspan=2, sticky="w")
    variables = {}
    for row, (nom, label) in enumerate((
        ("date_acquisition", "Date d'acquisition (AAAA-MM-JJ)"),
        ("reference_habitation", "Référence de l'habitation / adresse / lot"),
        ("credit_demande_autres", "Crédits 396 demandés par les autres personnes ($)"),
        ("source", "Source de l'acte, des critères et du partage")), 3):
        variables[nom] = tk.StringVar(value=str(getattr(profil, nom)))
        ttk.Label(c, text=label).grid(row=row, column=0, sticky="w")
        ttk.Entry(c, name=nom+"_6c", textvariable=variables[nom]).grid(row=row, column=1, sticky="ew", pady=4)
    confirmations = {}
    for row, (nom, label) in enumerate(CONFIRMATIONS_6C.items(), 7):
        confirmations[nom] = tk.BooleanVar(value=getattr(profil, nom))
        tk.Checkbutton(c, name=nom+"_6c", text=label, variable=confirmations[nom], wraplength=930,
            anchor="w", justify="left").grid(row=row, columnspan=2, sticky="w", pady=3)

    def revoquer(*_):
        for v in confirmations.values(): v.set(False)

    def valider():
        try:
            valeurs = {nom: v.get().strip() for nom, v in variables.items()}
            valeurs["credit_demande_autres"] = Decimal(valeurs["credit_demande_autres"].replace(" ", "").replace(",", ".") or "0")
            p = valider_achat_quebec_2025(AchatHabitationQuebec2025(reclamer=actif.get(), **valeurs,
                **{nom: v.get() for nom, v in confirmations.items()}))
        except (ValueError, InvalidOperation) as erreur:
            messagebox.showerror("Achat Québec invalide", str(erreur), parent=d); return
        appliquer(p); d.destroy()

    def effacer():
        actif.set(False)
        for nom, v in variables.items(): v.set("0" if nom == "credit_demande_autres" else "")

    actif.trace_add("write", revoquer)
    for v in variables.values(): v.trace_add("write", revoquer)
    ttk.Button(f.actions, text="Effacer", command=effacer).pack(side="left")
    ttk.Button(f.actions, text="Appliquer", command=valider).pack(side="right")
    ttk.Button(f.actions, text="Fermer", command=d.destroy).pack(side="right")
