"""Saisie locale des donneurs et des accords de transfert handicap 31800."""
from dataclasses import fields
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from .gui_layout import FormulaireDefilant, dimensionner_fenetre
from .tax_disability_transfer_2025 import (
    TransfertsHandicap2025, TransfertHandicapDependant2025, PartHandicapAutreSoutien2025,
    CONFIRMATIONS_HANDICAP_TRANSFERE, LIENS_HANDICAP, CONDITIONS_HANDICAP,
    SITUATIONS_PENSION_HANDICAP, instantane_donneur_handicap_2025,
    calculer_transferts_handicap_2025,
)

LIBELLES = {
    "reference": "Référence locale du donneur (sans NAS)",
    "nom_donneur": "Nom du donneur, identique à son dossier",
    "naissance": "Naissance du donneur (AAAA-MM-JJ)",
    "lien": "Lien familial du donneur",
    "lien_avec_conjoint": "Ce lien familial est avec le conjoint du contribuable",
    "condition": "Condition 30400 / 30450 établie par le comptable",
    "source": "Référence du CIPH, des pièces et de l'autorisation",
    "rapprochement_30400_30450": "Justification des conditions et rapprochement des dossiers",
    "conjoint_donneur_reclame": "Le conjoint du donneur réclame un crédit personnel ou un transfert pour lui (exclusion)",
    "autre_personne_reclame_30400": "Une autre personne réclame 30400 pour ce donneur (exclusion)",
    "situation_pension": "Situation des obligations alimentaires",
    "source_pension": "Pièces de l'exception alimentaire et accord, si applicable",
    "limiter_demande": "Limiter volontairement la part de base demandée selon l'accord",
    "part_demandee": "Part de base désignée ($), seulement si limitation activée",
    "personne": "Nom de l'autre soutien",
    "montant_base": "Part de base qu'il réclame ($), selon l'accord",
    **CONFIRMATIONS_HANDICAP_TRANSFERE,
}


def _fenetre(parent, titre):
    d = tk.Toplevel(parent)
    d.title(titre)
    dimensionner_fenetre(d, 1120, 880)
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


def _champs(cadre, objet, exclus=()):
    variables, types = {}, {}
    choix = {"lien": LIENS_HANDICAP, "condition": CONDITIONS_HANDICAP,
             "situation_pension": SITUATIONS_PENSION_HANDICAP}
    rang = 0
    for champ in fields(objet):
        nom = champ.name
        if nom in exclus:
            continue
        types[nom] = champ.type
        v = tk.BooleanVar(value=getattr(objet, nom)) if champ.type is bool else tk.StringVar(value=str(getattr(objet, nom)))
        variables[nom] = v
        if champ.type is bool:
            # Un libellé séparé conserve les longues confirmations lisibles.
            ttk.Checkbutton(cadre, name=nom + "_5r", variable=v).grid(row=rang, column=0, sticky="w")
            ttk.Label(cadre, text=LIBELLES[nom], wraplength=730).grid(row=rang, column=1, sticky="w", pady=4)
        else:
            ttk.Label(cadre, text=LIBELLES[nom], wraplength=320).grid(row=rang, column=0, sticky="w")
            w = (ttk.Combobox(cadre, name=nom + "_5r", textvariable=v, values=choix[nom], state="readonly")
                 if nom in choix else ttk.Entry(cadre, name=nom + "_5r", textvariable=v))
            w.grid(row=rang, column=1, sticky="ew", pady=4)
        rang += 1
    def revoquer(*_):
        for nom in CONFIRMATIONS_HANDICAP_TRANSFERE:
            if nom in variables:
                variables[nom].set(False)
    for nom, v in variables.items():
        if nom not in CONFIRMATIONS_HANDICAP_TRANSFERE:
            v.trace_add("write", revoquer)
    def lire():
        resultat = {}
        for nom, v in variables.items():
            x = v.get()
            if types[nom] is Decimal:
                try:
                    x = Decimal(x.strip().replace(",", "."))
                    if not x.is_finite() or x < 0 or x != x.quantize(Decimal("0.01")):
                        raise ValueError()
                except (InvalidOperation, ValueError) as erreur:
                    raise ValueError("Montant invalide : " + LIBELLES[nom]) from erreur
            elif isinstance(x, str):
                x = x.strip()
            resultat[nom] = x
        return resultat
    return lire, revoquer, rang


def _liste(parent, cadre, rang, nom, valeurs, editer, changement):
    table = ttk.Treeview(cadre, name=nom + "_5r", columns=("detail",), show="headings", height=4)
    table.heading("detail", text="Donneurs" if nom == "donneurs" else "Parts des autres soutiens")
    table.column("detail", width=850)
    table.grid(row=rang, column=0, columnspan=2, sticky="ew", pady=8)
    def rafraichir():
        table.delete(*table.get_children())
        for i, v in enumerate(valeurs):
            texte = v.nom_donneur if isinstance(v, TransfertHandicapDependant2025) else f"{v.personne} : {v.montant_base:.2f} $; {v.source}"
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
        editer(parent, None if i is None else valeurs[i], sauver)
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


def _editer_part(parent, objet, appliquer):
    d, f, fermer = _fenetre(parent, "Part d'un autre soutien — handicap")
    lire, _, _ = _champs(f.corps, objet or PartHandicapAutreSoutien2025())
    def sauver():
        try:
            p = PartHandicapAutreSoutien2025(**lire())
            if not p.personne or not p.source:
                raise ValueError("Nom et source de l'accord obligatoires.")
        except ValueError as erreur:
            messagebox.showerror("Part invalide", str(erreur), parent=d)
            return
        appliquer(p)
        fermer()
    ttk.Button(f.actions, text="Enregistrer", command=sauver).pack(side="right")
    ttk.Button(f.actions, text="Annuler", command=fermer).pack(side="right")


def _editer_donneur(parent, objet, appliquer, beneficiaire):
    p = objet or TransfertHandicapDependant2025()
    d, f, fermer = _fenetre(parent, "Donneur du transfert handicap — 31800")
    lire, revoquer, rang = _champs(f.corps, p, ("dossier_donneur_json", "autres_parts"))
    instantane = p.dossier_donneur_json
    statut = tk.StringVar(value="Dossier brut incorporé" if instantane else "Importer le dossier fiscal du donneur")
    def importer():
        nonlocal instantane
        chemin = filedialog.askopenfilename(parent=d, title="Dossier fiscal personnel du donneur", filetypes=[("Dossier JSON", "*.json")])
        if not chemin:
            return
        try:
            nouveau = instantane_donneur_handicap_2025(json.loads(Path(chemin).read_text(encoding="utf-8")))
        except (OSError, ValueError) as erreur:
            messagebox.showerror("Import invalide", str(erreur), parent=d)
            return
        instantane = nouveau
        revoquer()
        statut.set("Dossier brut incorporé; vérifier l'identité et refaire les confirmations")
    ttk.Button(f.corps, text="Importer le dossier du donneur", command=importer).grid(row=rang, column=0, sticky="w")
    ttk.Label(f.corps, textvariable=statut, wraplength=650).grid(row=rang, column=1, sticky="w")
    parts = list(p.autres_parts)
    _liste(d, f.corps, rang + 1, "autres soutiens", parts, _editer_part, revoquer)
    def sauver():
        try:
            nouveau = TransfertHandicapDependant2025(**lire(), dossier_donneur_json=instantane, autres_parts=tuple(parts))
            calculer_transferts_handicap_2025(TransfertsHandicap2025(beneficiaire, (nouveau,)), beneficiaire=beneficiaire)
        except ValueError as erreur:
            messagebox.showerror("Transfert invalide", str(erreur), parent=d)
            return
        appliquer(nouveau)
        fermer()
    ttk.Button(f.actions, text="Enregistrer le donneur", command=sauver).pack(side="right")
    ttk.Button(f.actions, text="Annuler", command=fermer).pack(side="right")


def ouvrir_transferts_handicap_2025(parent, profil, beneficiaire, appliquer):
    d, f, fermer = _fenetre(parent, "Transferts handicap de personnes à charge — 31800")
    ttk.Label(f.corps, text="Les donneurs doivent avoir un dossier fiscal 2025 validé avec CIPH approuvé. "
        "Import local des entrées brutes, sans transmission. Le conjoint relève du formulaire 32600. "
        "Les conditions 30400/30450 et alimentaires sont également contrôlées lors du calcul du bénéficiaire.",
        wraplength=1000).grid(row=0, column=0, columnspan=2, sticky="w", pady=8)
    ttk.Label(f.corps, text="Bénéficiaire : " + beneficiaire).grid(row=1, column=0, columnspan=2, sticky="w")
    valeurs = list(profil.transferts)
    def editer(parent, objet, sauver):
        _editer_donneur(parent, objet, sauver, beneficiaire)
    _liste(d, f.corps, 2, "donneurs", valeurs, editer, lambda: None)
    def sauver():
        try:
            p = TransfertsHandicap2025(beneficiaire if valeurs else "", tuple(valeurs))
            if valeurs and profil.beneficiaire and profil.beneficiaire != beneficiaire:
                raise ValueError("Bénéficiaire modifié : retirer les anciennes désignations et les refaire.")
            calculer_transferts_handicap_2025(p, beneficiaire=beneficiaire)
        except ValueError as erreur:
            messagebox.showerror("Transferts invalides", str(erreur), parent=d)
            return
        appliquer(p)
        fermer()
    ttk.Button(f.actions, text="Appliquer les transferts", command=sauver).pack(side="right")
    ttk.Button(f.actions, text="Effacer les transferts", command=lambda: (appliquer(TransfertsHandicap2025()), fermer())).pack(side="left")
    ttk.Button(f.actions, text="Annuler", command=fermer).pack(side="right")
