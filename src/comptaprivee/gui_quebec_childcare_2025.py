"""Saisie des faits RL-24 et RL-19 pour l'annexe C Québec 2025."""
import tkinter as tk
from tkinter import ttk, messagebox
from .gui_layout import FormulaireDefilant, dimensionner_fenetre
from .tax_quebec_childcare_2025 import (FraisGardeQuebec2025, EnfantGardeQuebec2025,
    CONFIRMATIONS_6F, CATEGORIES_GARDE_QUEBEC, montant_garde_depuis_champ,
    valider_garde_quebec_2025, valider_enfant_garde_quebec_2025)


def _fenetre(parent, titre):
    d = tk.Toplevel(parent); d.title(titre)
    dimensionner_fenetre(d, 1080, 880); d.transient(parent); d.grab_set()
    f = FormulaireDefilant(d); f.corps.columnconfigure(1, weight=1)
    def fermer():
        d.destroy()
        if isinstance(parent, tk.Toplevel) and parent.winfo_exists():
            parent.grab_set()
    d.protocol("WM_DELETE_WINDOW", fermer)
    return d, f, fermer


def _editer_enfant(parent, enfant, appliquer):
    d, f, fermer = _fenetre(parent, "Enfant — frais de garde Québec")
    variables = {}
    for row, (nom, libelle) in enumerate((("reference", "Référence locale unique (sans NAS)"),
            ("nom", "Nom complet de l'enfant"), ("naissance", "Naissance AAAA-MM-JJ"),
            ("categorie", "Condition vérifiée au Québec"), ("frais_rl24_e", "Total des cases E RL-24 de cet enfant"),
            ("source", "Références des RL-24, naissance et preuve médicale si applicable"))):
        v = tk.StringVar(value=str(getattr(enfant, nom))); variables[nom] = v
        ttk.Label(f.corps, text=libelle, wraplength=480).grid(row=row, column=0, sticky="w", pady=6)
        w = (ttk.Combobox(f.corps, name=nom+"_enfant_6f", textvariable=v,
                values=CATEGORIES_GARDE_QUEBEC, state="readonly") if nom == "categorie" else
             ttk.Entry(f.corps, name=nom+"_enfant_6f", textvariable=v))
        w.grid(row=row, column=1, sticky="ew", pady=6)
    def sauver():
        try:
            valeurs = {nom: v.get().strip() for nom, v in variables.items()}
            valeurs["frais_rl24_e"] = montant_garde_depuis_champ(valeurs["frais_rl24_e"])
            enfant_valide = valider_enfant_garde_quebec_2025(EnfantGardeQuebec2025(**valeurs))
        except ValueError as erreur:
            messagebox.showerror("Enfant garde Québec invalide", str(erreur), parent=d); return
        appliquer(enfant_valide); fermer()
    ttk.Button(f.actions, text="Enregistrer l'enfant", command=sauver).pack(side="right")
    ttk.Button(f.actions, text="Annuler", command=fermer).pack(side="right")


def ouvrir_garde_quebec_2025(parent, profil, appliquer):
    d, f, fermer = _fenetre(parent, "Frais de garde Québec — annexe C")
    c = f.corps
    ttk.Label(c, text="Frais de garde Québec 2025 — lignes 455 et 441", font=("Segoe UI", 16, "bold")).grid(row=0, columnspan=2, sticky="w")
    ttk.Label(c, text="Une fiche par enfant du demandeur ou du conjoint. RL-24 et preuves vérifiés par le comptable. "
        "Le plafond est familial; le taux est calculé depuis les revenus nets Québec. La part du conjoint est celle convenue ensemble. "
        "Bouclier fiscal 460 non calculé : faits 2024 nécessaires et examen séparé requis. "
        "Les avances personnelles RL-19 case C restent à déclarer même si elles dépassent le crédit. "
        "Hors de ce profil : garde partagée, hébergement, aides/remboursements, résidence partielle et changements d'union.",
        wraplength=950, justify="left").grid(row=1, columnspan=2, sticky="w", pady=8)
    actif = tk.BooleanVar(value=profil.reclamer)
    ttk.Checkbutton(c, name="reclamer_6f", text="Activer l'annexe C / les avances RL-19", variable=actif).grid(row=2, columnspan=2, sticky="w")
    enfants = list(profil.enfants)
    table = ttk.Treeview(c, name="enfants_6f", columns=("enfant",), show="headings", height=5)
    table.heading("enfant", text="Référence — nom — naissance — catégorie — frais RL-24")
    table.column("enfant", width=920); table.grid(row=3, columnspan=2, sticky="ew")
    variables = {}
    for row, (nom, libelle) in enumerate((("conjoint_nom", "Conjoint au 31 décembre (vide si aucun)"),
            ("revenu_net_conjoint", "Revenu net Québec 275 du conjoint, selon sa déclaration"),
            ("credit_demande_conjoint", "Part du crédit 455 convenue pour le conjoint"),
            ("source_conjoint", "Source du revenu et de la part du conjoint"),
            ("avances_rl19_c", "Avances personnelles RL-19 case C"),
            ("source", "Source du dossier familial et du contrôle RL-19")), 5):
        v = tk.StringVar(value=str(getattr(profil, nom))); variables[nom] = v
        ttk.Label(c, text=libelle, wraplength=480).grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(c, name=nom+"_6f", textvariable=v).grid(row=row, column=1, sticky="ew", pady=4)
    confirmations = {}
    for row, (nom, libelle) in enumerate(CONFIRMATIONS_6F.items(), 11):
        v = tk.BooleanVar(value=getattr(profil, nom)); confirmations[nom] = v
        tk.Checkbutton(c, name=nom+"_6f", variable=v, text=libelle, wraplength=950,
            anchor="w", justify="left").grid(row=row, columnspan=2, sticky="w", pady=3)
    def revoquer(*_):
        for v in confirmations.values(): v.set(False)
    def rafraichir():
        table.delete(*table.get_children())
        for i, e in enumerate(enfants):
            table.insert("", "end", iid=str(i), values=(f"{e.reference} — {e.nom} — {e.naissance} — {e.categorie} — {e.frais_rl24_e:.2f} $",))
    def editer(nouveau):
        if not nouveau and not table.selection(): return
        i = None if nouveau else int(table.selection()[0])
        def sauver(e):
            if i is None: enfants.append(e)
            else: enfants[i] = e
            revoquer(); rafraichir()
        _editer_enfant(d, EnfantGardeQuebec2025() if nouveau else enfants[i], sauver)
    def retirer():
        if table.selection():
            del enfants[int(table.selection()[0])]
            revoquer(); rafraichir()
    actions = ttk.Frame(c); actions.grid(row=4, columnspan=2, sticky="w", pady=6)
    for texte, callback in (("Ajouter", lambda: editer(True)), ("Modifier", lambda: editer(False)), ("Retirer", retirer)):
        ttk.Button(actions, text=texte, command=callback).pack(side="left", padx=4)
    def sauver():
        try:
            valeurs = {nom: v.get().strip() for nom, v in variables.items()}
            for nom in ("revenu_net_conjoint", "credit_demande_conjoint", "avances_rl19_c"):
                valeurs[nom] = montant_garde_depuis_champ(valeurs[nom])
            p = valider_garde_quebec_2025(FraisGardeQuebec2025(reclamer=actif.get(), enfants=tuple(enfants),
                **valeurs, **{nom: v.get() for nom, v in confirmations.items()}))
        except ValueError as erreur:
            messagebox.showerror("Garde Québec invalide", str(erreur), parent=d); return
        appliquer(p); fermer()
    def effacer():
        enfants.clear(); actif.set(False)
        for v in variables.values(): v.set("")
        revoquer(); rafraichir()
    for v in (actif, *variables.values()): v.trace_add("write", revoquer)
    ttk.Button(f.actions, text="Effacer", command=effacer).pack(side="left")
    ttk.Button(f.actions, text="Appliquer", command=sauver).pack(side="right")
    ttk.Button(f.actions, text="Fermer", command=fermer).pack(side="right")
    rafraichir()
