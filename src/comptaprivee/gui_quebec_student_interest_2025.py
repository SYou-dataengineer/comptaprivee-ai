"""Saisie des intérêts et du choix de report Québec, annexe M 2025."""
from decimal import Decimal, InvalidOperation
import tkinter as tk
from tkinter import ttk, messagebox
from .gui_layout import FormulaireDefilant, dimensionner_fenetre
from .tax_quebec_student_interest_2025 import InteretsEtudiantsQuebec2025, CONFIRMATIONS_6B, calculer_interets_quebec_2025


def ouvrir_interets_quebec_2025(parent, profil, appliquer):
    d = tk.Toplevel(parent)
    d.title("Intérêts étudiants Québec — annexe M 2025")
    dimensionner_fenetre(d, 980, 850)
    d.transient(parent); d.grab_set()
    f = FormulaireDefilant(d); cadre = f.corps
    cadre.columnconfigure(1, weight=1)
    ttk.Label(cadre, text="Québec — ligne 385 / annexe M", font=("Segoe UI", 16, "bold")).grid(row=0, columnspan=2, sticky="w")
    ttk.Label(cadre, text="Prêt sous la Loi sur l'aide financière aux études, les lois fédérales sur les prêts étudiants, "
        "l'aide financière aux étudiants ou les prêts aux apprentis, ou une loi provinciale admissible. "
        "Les reports Québec depuis 1998 sont distincts du fédéral. Choisissez la part à réclamer : "
        "0 conserve tout le disponible. Le crédit est calculé à 20 % et n'est pas remboursable. "
        "Une part réclamée sans économie d'impôt reste consommée. Aucun suivi automatique des avis RQ.",
        wraplength=860, justify="left").grid(row=1, columnspan=2, sticky="w", pady=8)
    variables = {}
    for row, (nom, label) in enumerate((
        ("interets_payes_2025", "Intérêts admissibles payés en 2025 — ligne 48"),
        ("solde_inutilise_1998_2024", "Solde Québec inutilisé 1998–2024 — ligne 46"),
        ("reclamation_385", "Part choisie à réclamer — ligne 385 (0 pour reporter tout)"),
        ("source", "Source des paiements et du solde : annexe M / avis / historique")), 2):
        variables[nom] = tk.StringVar(value=str(getattr(profil, nom)))
        ttk.Label(cadre, text=label).grid(row=row, column=0, sticky="w")
        ttk.Entry(cadre, name=nom+"_6b", textvariable=variables[nom]).grid(row=row, column=1, sticky="ew", pady=4)
    confirmations = {}
    for row, (nom, label) in enumerate(CONFIRMATIONS_6B.items(), 6):
        confirmations[nom] = tk.BooleanVar(value=getattr(profil, nom))
        ttk.Checkbutton(cadre, name=nom+"_6b", text=label, variable=confirmations[nom]).grid(row=row, columnspan=2, sticky="w", pady=3)
    apercu = tk.StringVar()
    ttk.Entry(cadre, name="calcul_6b", textvariable=apercu, state="readonly", width=105).grid(row=14, columnspan=2, sticky="ew", pady=10)

    def construire(confirme=True):
        valeurs = {nom: v.get().strip() for nom, v in variables.items()}
        try:
            for nom in ("interets_payes_2025", "solde_inutilise_1998_2024", "reclamation_385"):
                valeurs[nom] = Decimal(valeurs[nom].replace(" ", "").replace(",", ".") or "0")
        except InvalidOperation as erreur:
            raise ValueError("Montant Québec 385 invalide.") from erreur
        valeurs.update({nom: v.get() if confirme else True for nom, v in confirmations.items()})
        if not confirme: valeurs["source"] = "Aperçu non validé"
        return InteretsEtudiantsQuebec2025(**valeurs)

    def actualiser(*_):
        for v in confirmations.values(): v.set(False)
        afficher()

    def afficher():
        try:
            r = calculer_interets_quebec_2025(construire(False))
            apercu.set(f"Disponible : {r.disponible_ligne_52:.2f} $; crédit sur 385 : {r.credit_385:.2f} $; report : {r.report_ligne_62:.2f} $")
        except ValueError:
            apercu.set("Montants à vérifier")

    def valider():
        try:
            p = construire(); calculer_interets_quebec_2025(p)
        except ValueError as erreur:
            messagebox.showerror("Intérêts Québec invalides", str(erreur), parent=d); return
        appliquer(p); d.destroy()

    def effacer():
        for nom, v in variables.items(): v.set("" if nom == "source" else "0")

    for v in variables.values(): v.trace_add("write", actualiser)
    afficher()
    ttk.Button(f.actions, text="Effacer", command=effacer).pack(side="left")
    ttk.Button(f.actions, text="Appliquer", command=valider).pack(side="right")
    ttk.Button(f.actions, text="Fermer", command=d.destroy).pack(side="right")
