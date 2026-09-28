"""Personnes, reçus et période des frais médicaux familiaux fédéraux."""
from dataclasses import fields
from decimal import Decimal, InvalidOperation
import tkinter as tk
from tkinter import ttk, messagebox

from .gui_layout import FormulaireDefilant, dimensionner_fenetre
from .tax_family_medical_2025 import (
    FraisMedicauxFamilleFederaux2025, PersonneFraisMedicaux2025,
    DepenseMedicaleFamiliale2025, LIENS_MEDICAUX, CONFIRMATIONS_MEDICALES_FAMILLE,
    montant_medical_familial, calculer_medical_familial_2025,
)

LIBELLES = {
    "reference": "Référence unique (sans NAS)", "nom": "Nom de la personne",
    "naissance": "Naissance (AAAA-MM-JJ)", "lien": "Lien avec le demandeur",
    "lien_avec_conjoint": "Le lien familial indiqué est avec le conjoint du demandeur",
    "resident_canada_dans_annee": "Résidence au Canada à un moment de 2025 confirmée",
    "revenu_net_23600": "Revenu net 23600 de cette personne (33199 seulement)",
    "source_revenu": "Source du revenu net 23600 (33199 seulement)",
    "source_lien_dependance": "Pièces établissant le lien et la dépendance, selon le cas",
    "personne": "Référence de la personne bénéficiaire du reçu",
    "date_paiement": "Date de paiement (AAAA-MM-JJ)", "description": "Description des frais admissibles",
    "montant_paye": "Montant payé par le demandeur ou son conjoint ($)",
    "remboursements": "Remboursements reçus ou à recevoir ($)",
    "remboursements_imposables_non_deduits": "Dont remboursements inclus dans un revenu et non déduits ($)",
    "part_reclamee_ailleurs": "Part du reçu déjà attribuée à une autre demande ($)",
    "source": "Référence du reçu et des pièces justificatives",
}


def _fenetre(parent, titre):
    d = tk.Toplevel(parent)
    d.title(titre)
    dimensionner_fenetre(d, 1080, 850)
    d.transient(parent)
    d.grab_set()
    f = FormulaireDefilant(d)
    f.corps.columnconfigure(1, weight=1)
    def fermer():
        d.destroy()
        if isinstance(parent, tk.Toplevel) and parent.winfo_exists():
            parent.grab_set()
    d.protocol("WM_DELETE_WINDOW", fermer)
    return d, f, fermer


def _editer(parent, objet, appliquer, classe):
    d, f, fermer = _fenetre(parent, "Personne — frais médicaux" if classe is PersonneFraisMedicaux2025 else "Reçu médical")
    objet = objet or classe()
    variables = {}
    for rang, champ in enumerate(fields(objet)):
        nom = champ.name
        v = tk.BooleanVar(value=getattr(objet, nom)) if champ.type is bool else tk.StringVar(value=str(getattr(objet, nom)))
        variables[nom] = v
        if champ.type is bool:
            ttk.Checkbutton(f.corps, name=nom + "_5s", variable=v).grid(row=rang, column=0, sticky="w")
            ttk.Label(f.corps, text=LIBELLES[nom], wraplength=650).grid(row=rang, column=1, sticky="w")
        else:
            ttk.Label(f.corps, text=LIBELLES[nom], wraplength=360).grid(row=rang, column=0, sticky="w", pady=5)
            w = (ttk.Combobox(f.corps, name=nom + "_5s", textvariable=v, values=LIENS_MEDICAUX, state="readonly")
                 if nom == "lien" else ttk.Entry(f.corps, name=nom + "_5s", textvariable=v))
            w.grid(row=rang, column=1, sticky="ew", pady=5)
    def sauver():
        try:
            valeurs = {}
            for champ in fields(objet):
                x = variables[champ.name].get()
                if champ.type is Decimal:
                    x = montant_medical_familial(Decimal(x.strip().replace(",", ".")), LIBELLES[champ.name], signe=champ.name == "revenu_net_23600")
                elif isinstance(x, str):
                    x = x.strip()
                valeurs[champ.name] = x
            if not valeurs["reference"]:
                raise ValueError("Référence obligatoire.")
            nouveau = classe(**valeurs)
        except (InvalidOperation, ValueError) as erreur:
            messagebox.showerror("Saisie invalide", str(erreur), parent=d)
            return
        appliquer(nouveau)
        fermer()
    ttk.Label(f.corps, text="Les liens, dates, justificatifs et rapprochements sont contrôlés lors de l'application du profil.", wraplength=950).grid(row=30, column=0, columnspan=2, sticky="w", pady=10)
    ttk.Button(f.actions, text="Enregistrer", command=sauver).pack(side="right")
    ttk.Button(f.actions, text="Annuler", command=fermer).pack(side="right")


def _liste(parent, cadre, rang, nom, valeurs, classe, changement):
    table = ttk.Treeview(cadre, name=nom.lower() + "_5s", columns=("detail",), show="headings", height=4)
    table.heading("detail", text=nom)
    table.column("detail", width=900)
    table.grid(row=rang, column=0, columnspan=2, sticky="ew", pady=8)
    def rafraichir():
        table.delete(*table.get_children())
        for i, v in enumerate(valeurs):
            texte = f"{v.reference} — {v.nom} — {v.lien}" if classe is PersonneFraisMedicaux2025 else f"{v.reference} — {v.personne} — {v.date_paiement} — {v.montant_paye:.2f} $"
            table.insert("", "end", iid=str(i), values=(texte,))
    def ouvrir(nouveau):
        if not nouveau and not table.selection():
            return
        i = None if nouveau else int(table.selection()[0])
        def sauver(v):
            if i is None:
                valeurs.append(v)
            else:
                valeurs[i] = v
            changement()
            rafraichir()
        _editer(parent, None if i is None else valeurs[i], sauver, classe)
    def retirer():
        if table.selection():
            del valeurs[int(table.selection()[0])]
            changement()
            rafraichir()
    actions = ttk.Frame(cadre)
    actions.grid(row=rang + 1, column=0, columnspan=2, sticky="w")
    for texte, commande in (("Ajouter", lambda: ouvrir(True)), ("Modifier", lambda: ouvrir(False)), ("Retirer", retirer)):
        ttk.Button(actions, text=texte + " — " + nom, command=commande).pack(side="left", padx=3)
    rafraichir()


def ouvrir_medical_familial_2025(parent, profil, demandeur, appliquer):
    d, f, fermer = _fenetre(parent, "Frais médicaux familiaux fédéraux — 33099 / 33199")
    ttk.Label(f.corps, text="Saisissez les personnes et les reçus admissibles déjà vérifiés. "
        "Le calcul sépare le groupe 33099 et chaque autre personne à charge 33199. "
        "Même période de douze mois pour tous; aucune optimisation automatique entre conjoints. "
        "Le Québec familial, l'ACT familial et le supplément médical familial seront traités séparément.",
        wraplength=980).grid(row=0, column=0, columnspan=2, sticky="w", pady=8)
    ttk.Label(f.corps, text="Demandeur : " + demandeur).grid(row=1, column=0, columnspan=2, sticky="w")
    dates = {}
    for rang, (nom, libelle) in enumerate((("debut_periode", "Début de période (AAAA-MM-JJ)"), ("fin_periode", "Fin de période en 2025 (AAAA-MM-JJ)")), 2):
        dates[nom] = tk.StringVar(value=getattr(profil, nom))
        ttk.Label(f.corps, text=libelle).grid(row=rang, column=0, sticky="w")
        ttk.Entry(f.corps, name=nom + "_5s", textvariable=dates[nom]).grid(row=rang, column=1, sticky="ew")
    confirmations = {}
    for rang, (nom, libelle) in enumerate(CONFIRMATIONS_MEDICALES_FAMILLE.items(), 10):
        v = tk.BooleanVar(value=getattr(profil, nom) if profil.demandeur == demandeur else False)
        confirmations[nom] = v
        ttk.Checkbutton(f.corps, name=nom + "_5s", variable=v).grid(row=rang, column=0, sticky="w")
        ttk.Label(f.corps, text=libelle, wraplength=650).grid(row=rang, column=1, sticky="w", pady=4)
    def revoquer(*_):
        for v in confirmations.values():
            v.set(False)
    for v in dates.values():
        v.trace_add("write", revoquer)
    personnes, depenses = list(profil.personnes), list(profil.depenses)
    _liste(d, f.corps, 4, "Personnes", personnes, PersonneFraisMedicaux2025, revoquer)
    _liste(d, f.corps, 7, "Reçus", depenses, DepenseMedicaleFamiliale2025, revoquer)
    def sauver():
        try:
            p = FraisMedicauxFamilleFederaux2025(demandeur=demandeur,
                personnes=tuple(personnes), depenses=tuple(depenses),
                **{n: v.get().strip() for n, v in dates.items()}, **{n: v.get() for n, v in confirmations.items()})
            calculer_medical_familial_2025(p, demandeur=demandeur, revenu_net=Decimal(0))
        except ValueError as erreur:
            messagebox.showerror("Profil médical invalide", str(erreur), parent=d)
            return
        appliquer(p)
        fermer()
    ttk.Button(f.actions, text="Appliquer les frais familiaux", command=sauver).pack(side="right")
    ttk.Button(f.actions, text="Effacer les frais familiaux", command=lambda: (appliquer(FraisMedicauxFamilleFederaux2025()), fermer())).pack(side="left")
    ttk.Button(f.actions, text="Annuler", command=fermer).pack(side="right")
