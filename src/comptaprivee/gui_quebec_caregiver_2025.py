"""Saisie des faits annexe H et RL-19 Québec 2025."""
import tkinter as tk
from tkinter import ttk, messagebox
from .gui_layout import FormulaireDefilant, dimensionner_fenetre
from .tax_quebec_caregiver_2025 import (PersonneAidanteQuebec2025, PersonneAideeQuebec2025,
    CONFIRMATIONS_6G, MODES_AIDANTE, LIENS_AIDANTE, montant_aidante_depuis_champ,
    valider_aidante_quebec_2025, valider_personne_aidee_quebec_2025)


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


def _editer_personne(parent, personne, appliquer):
    d, f, fermer = _fenetre(parent, "Personne aidée — annexe H Québec")
    variables = {}
    for row, (nom, libelle) in enumerate((("reference", "Référence locale unique (sans NAS)"),
            ("nom", "Nom complet de la personne aidée"), ("naissance", "Naissance AAAA-MM-JJ"),
            ("mode", "Situation de la personne aidée"), ("lien", "Lien avec vous ou votre conjoint"),
            ("debut", "Début retenu de l'aide/cohabitation continue (2024 ou 2025)"),
            ("fin", "Fin de cette période déjà accomplie (AAAA-MM-JJ)"),
            ("adresse", "Adresse de cohabitation (vide si sans cohabitation)"),
            ("revenu_net", "Revenu net Québec 275 de la personne aidée"),
            ("credit_autres", "Crédit convenu demandé par les autres aidants"),
            ("source", "Sources : identité, lien, périodes, revenu, attestations et partage"))):
        v = tk.StringVar(value=str(getattr(personne, nom))); variables[nom] = v
        ttk.Label(f.corps, text=libelle, wraplength=480).grid(row=row, column=0, sticky="w", pady=6)
        w = (ttk.Combobox(f.corps, name=nom+"_personne_6g", textvariable=v,
                values=MODES_AIDANTE if nom == "mode" else LIENS_AIDANTE, state="readonly") if nom in ("mode", "lien") else
             ttk.Entry(f.corps, name=nom+"_personne_6g", textvariable=v))
        w.grid(row=row, column=1, sticky="ew", pady=6)
    def sauver():
        try:
            valeurs = {nom: v.get().strip() for nom, v in variables.items()}
            for nom in ("revenu_net", "credit_autres"):
                valeurs[nom] = montant_aidante_depuis_champ(valeurs[nom])
            personne_valide = valider_personne_aidee_quebec_2025(PersonneAideeQuebec2025(**valeurs))
        except ValueError as erreur:
            messagebox.showerror("Personne aidée invalide", str(erreur), parent=d); return
        appliquer(personne_valide); fermer()
    ttk.Button(f.actions, text="Enregistrer la personne", command=sauver).pack(side="right")
    ttk.Button(f.actions, text="Annuler", command=fermer).pack(side="right")


def ouvrir_aidante_quebec_2025(parent, profil, appliquer):
    d, f, fermer = _fenetre(parent, "Personne aidante Québec — annexe H")
    c = f.corps
    ttk.Label(c, text="Personne aidante Québec 2025 — lignes 462 et 441", font=("Segoe UI", 16, "bold")).grid(row=0, columnspan=2, sticky="w")
    ttk.Label(c, text="Une fiche par personne aidée. Conditions et attestations Québec vérifiées par le comptable. "
        "Période personnelle continue de 365 jours dont 183 en 2025, déjà accomplie. "
        "Le crédit est calculé selon l'âge, le revenu et la cohabitation, puis réduit des parts convenues des autres aidants. "
        "Avances RL-19 H à déclarer intégralement. Rotations, décès, relève et rajustements d'assistance sociale hors de ce profil.",
        wraplength=950, justify="left").grid(row=1, columnspan=2, sticky="w", pady=8)
    actif = tk.BooleanVar(value=profil.reclamer)
    ttk.Checkbutton(c, name="reclamer_6g", text="Activer l'annexe H / les avances RL-19", variable=actif).grid(row=2, columnspan=2, sticky="w")
    personnes = list(profil.personnes)
    table = ttk.Treeview(c, name="personnes_6g", columns=("personne",), show="headings", height=5)
    table.heading("personne", text="Référence — nom — naissance — situation — revenu net")
    table.column("personne", width=920); table.grid(row=3, columnspan=2, sticky="ew")
    variables = {}
    for row, (nom, libelle) in enumerate((("avances_rl19_h", "Avances personnelles RL-19 case H"),
            ("source", "Source du dossier et du contrôle des avances RL-19")), 5):
        v = tk.StringVar(value=str(getattr(profil, nom))); variables[nom] = v
        ttk.Label(c, text=libelle, wraplength=480).grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(c, name=nom+"_6g", textvariable=v).grid(row=row, column=1, sticky="ew", pady=4)
    confirmations = {}
    for row, (nom, libelle) in enumerate(CONFIRMATIONS_6G.items(), 7):
        v = tk.BooleanVar(value=getattr(profil, nom)); confirmations[nom] = v
        tk.Checkbutton(c, name=nom+"_6g", variable=v, text=libelle, wraplength=950,
            anchor="w", justify="left").grid(row=row, columnspan=2, sticky="w", pady=3)
    def revoquer(*_):
        for v in confirmations.values(): v.set(False)
    def rafraichir():
        table.delete(*table.get_children())
        for i, e in enumerate(personnes):
            table.insert("", "end", iid=str(i), values=(f"{e.reference} — {e.nom} — {e.naissance} — {e.mode} — {e.revenu_net:.2f} $",))
    def editer(nouveau):
        if not nouveau and not table.selection(): return
        i = None if nouveau else int(table.selection()[0])
        def sauver(e):
            if i is None: personnes.append(e)
            else: personnes[i] = e
            revoquer(); rafraichir()
        _editer_personne(d, PersonneAideeQuebec2025() if nouveau else personnes[i], sauver)
    def retirer():
        if table.selection():
            del personnes[int(table.selection()[0])]
            revoquer(); rafraichir()
    actions = ttk.Frame(c); actions.grid(row=4, columnspan=2, sticky="w", pady=6)
    for texte, callback in (("Ajouter", lambda: editer(True)), ("Modifier", lambda: editer(False)), ("Retirer", retirer)):
        ttk.Button(actions, text=texte, command=callback).pack(side="left", padx=4)
    def sauver():
        try:
            valeurs = {nom: v.get().strip() for nom, v in variables.items()}
            for nom in ("avances_rl19_h",):
                valeurs[nom] = montant_aidante_depuis_champ(valeurs[nom])
            p = valider_aidante_quebec_2025(PersonneAidanteQuebec2025(reclamer=actif.get(), personnes=tuple(personnes),
                **valeurs, **{nom: v.get() for nom, v in confirmations.items()}))
        except ValueError as erreur:
            messagebox.showerror("Personne aidante Québec invalide", str(erreur), parent=d); return
        appliquer(p); fermer()
    def effacer():
        personnes.clear(); actif.set(False)
        for v in variables.values(): v.set("")
        revoquer(); rafraichir()
    for v in (actif, *variables.values()): v.trace_add("write", revoquer)
    ttk.Button(f.actions, text="Effacer", command=effacer).pack(side="left")
    ttk.Button(f.actions, text="Appliquer", command=sauver).pack(side="right")
    ttk.Button(f.actions, text="Fermer", command=fermer).pack(side="right")
    rafraichir()
