"""Saisie des projets, dépenses et partages de l'annexe 12 de 2025."""
from dataclasses import fields
from decimal import Decimal, InvalidOperation
import tkinter as tk
from tkinter import ttk, messagebox

from .gui_layout import FormulaireDefilant, dimensionner_fenetre
from .tax_multigenerational_renovation_2025 import (
    CONFIRMATIONS_RENOVATION, LIENS_PROCHE, ROLES_DEMANDEUR,
    DepenseRenovation2025, PartAutreDemandeur2025,
    RenovationMultigenerationnelle2025, RenovationsMultigenerationnelles2025,
    calculer_multigenerationnel_2025, calculer_renovation_multigenerationnelle_2025,
    montant_multigenerationnel_2025,
)

LIBELLES = {
    "logement": "Adresse du logement au Canada",
    "unite": "Identification du logement secondaire créé",
    "particulier": "Nom ou référence du particulier déterminé",
    "naissance_particulier": "Naissance du particulier déterminé (AAAA-MM-JJ)",
    "ciph_admissible": "Particulier déterminé admissible au CIPH en 2025",
    "source_ciph": "Référence du CIPH, si applicable",
    "proche": "Nom ou référence du proche occupant",
    "naissance_proche": "Naissance du proche occupant (AAAA-MM-JJ)",
    "lien_proche": "Lien familial du proche occupant",
    "lien_avec_conjoint": "Ce lien familial est avec le conjoint du particulier déterminé",
    "role_demandeur": "Rôle du contribuable qui fait cette demande",
    "source_role": "Pièces établissant son rôle, son lien familial et son âge si proche",
    "date_fin": "Date d'achèvement des travaux (AAAA-MM-JJ)",
    "source": "Référence des pièces justificatives",
    "attribution_fiducie": "Dépenses attribuées au contribuable par une fiducie",
    "source_attribution": "Notification de la fiducie et ventilation de la quote-part",
    "date_piece": "Date de facture ou du contrat (AAAA-MM-JJ)",
    "date_bien_service": "Date d'acquisition des biens ou services (AAAA-MM-JJ)",
    "date_paiement": "Date du paiement effectué (AAAA-MM-JJ)",
    "fournisseur": "Fournisseur ou entrepreneur et adresse",
    "description": "Description de la dépense admissible",
    "montant": "Montant personnel payé, taxes comprises ($)",
    "aide": "Aides et remboursements reçus ou à recevoir ($)",
    "fournisseur_lie": "Fournisseur ayant un lien de dépendance avec le contribuable",
    "numero_tps": "Numéro ou référence d'inscription TPS/TVH, obligatoire si lié",
    "personne": "Nom ou référence de l'autre demandeur admissible",
    "base_reclamee": "Dépenses qu'il réclame pour cette rénovation ($), avant crédit",
    "resident_annee_complete": "Le contribuable résidait au Canada toute l'année 2025",
    "profil_ordinaire": "Déclaration ordinaire, sans faillite ni décès dans ce projet",
    "rapprochement_medical_accessibilite": "Pièce de rapprochement avec les frais médicaux fédéraux / l'accessibilité",
    **CONFIRMATIONS_RENOVATION,
}


def _fenetre(parent, titre):
    d = tk.Toplevel(parent)
    d.title(titre)
    dimensionner_fenetre(d, 1080, 840)
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


def _champs(cadre, objet, exclus=(), confirmations=()):
    variables = {}
    types = {}
    ligne = 0
    for champ in fields(objet):
        nom = champ.name
        if nom in exclus:
            continue
        types[nom] = champ.type
        valeur = getattr(objet, nom)
        v = tk.BooleanVar(value=valeur) if champ.type is bool else tk.StringVar(value=str(valeur))
        variables[nom] = v
        if champ.type is bool:
            w = tk.Checkbutton(cadre, name=nom + "_5q", text=LIBELLES[nom], variable=v,
                               wraplength=780, justify="left", anchor="w")
            w.grid(row=ligne, column=0, columnspan=2, sticky="w", pady=3)
        else:
            ttk.Label(cadre, text=LIBELLES[nom], wraplength=420).grid(row=ligne, column=0, sticky="w")
            choix = LIENS_PROCHE if nom == "lien_proche" else ROLES_DEMANDEUR if nom == "role_demandeur" else None
            w = (ttk.Combobox(cadre, name=nom + "_5q", textvariable=v, values=choix, state="readonly")
                 if choix else ttk.Entry(cadre, name=nom + "_5q", textvariable=v))
            w.grid(row=ligne, column=1, sticky="ew", pady=3)
        ligne += 1
    def revoquer(*_):
        for nom in confirmations:
            variables[nom].set(False)
    for nom, variable in variables.items():
        if nom not in confirmations:
            variable.trace_add("write", revoquer)
    def lire():
        valeurs = {}
        for nom, v in variables.items():
            x = v.get()
            if types[nom] is Decimal:
                try:
                    x = montant_multigenerationnel_2025(Decimal(x.strip().replace(",", ".")), LIBELLES[nom])
                except (InvalidOperation, ValueError) as erreur:
                    raise ValueError("Montant invalide : " + LIBELLES[nom]) from erreur
            elif isinstance(x, str):
                x = x.strip()
            valeurs[nom] = x
        return valeurs
    return lire, revoquer, ligne


def _liste(parent, cadre, ligne, nom, titre, valeurs, editer, changement):
    ttk.Label(cadre, text=titre).grid(row=ligne, column=0, columnspan=2, sticky="w", pady=(12, 2))
    table = ttk.Treeview(cadre, name=nom + "_5q", columns=("detail",), show="headings", height=5)
    table.heading("detail", text=titre)
    table.column("detail", width=850)
    table.grid(row=ligne + 1, column=0, columnspan=2, sticky="ew")
    def rafraichir():
        table.delete(*table.get_children())
        for i, v in enumerate(valeurs):
            if isinstance(v, RenovationMultigenerationnelle2025):
                texte = f"{v.logement} — {v.unite} — {v.particulier}"
            elif isinstance(v, DepenseRenovation2025):
                texte = f"{v.description} : {v.montant:.2f} $; aide {v.aide:.2f} $; {v.source}"
            else:
                texte = f"{v.personne} : {v.base_reclamee:.2f} $; {v.source}"
            table.insert("", "end", iid=str(i), values=(texte,))
    def ouvrir(nouveau):
        selection = table.selection()
        if not nouveau and not selection:
            return
        index = None if nouveau else int(selection[0])
        def enregistrer(v):
            if index is None:
                valeurs.append(v)
            else:
                valeurs[index] = v
            changement()
            rafraichir()
        editer(parent, None if index is None else valeurs[index], enregistrer)
    def retirer():
        if table.selection():
            del valeurs[int(table.selection()[0])]
            changement()
            rafraichir()
    actions = ttk.Frame(cadre)
    actions.grid(row=ligne + 2, column=0, columnspan=2, sticky="w")
    for texte, commande in (("Ajouter", lambda: ouvrir(True)), ("Modifier", lambda: ouvrir(False)), ("Retirer", retirer)):
        ttk.Button(actions, text=texte + " — " + titre, command=commande).pack(side="left", padx=3)
    rafraichir()
    return ligne + 3


def _editer_piece(parent, objet, appliquer, classe):
    d, f, fermer = _fenetre(parent, "Dépense de rénovation" if classe is DepenseRenovation2025 else "Partage de rénovation")
    lire, _, _ = _champs(f.corps, objet or classe())
    def sauver():
        try:
            v = classe(**lire())
            if not v.source or (isinstance(v, DepenseRenovation2025) and (v.montant <= 0 or v.aide > v.montant)):
                raise ValueError("Source requise; dépense positive et aides limitées au montant payé.")
        except ValueError as erreur:
            messagebox.showerror("Saisie invalide", str(erreur), parent=d)
            return
        appliquer(v)
        fermer()
    ttk.Label(f.corps, text="Les dates et l'admissibilité seront contrôlées lors de l'enregistrement du projet.").grid(row=30, column=0, columnspan=2)
    ttk.Button(f.actions, text="Enregistrer", command=sauver).pack(side="right")
    ttk.Button(f.actions, text="Annuler", command=fermer).pack(side="right")


def _editer_projet(parent, objet, appliquer):
    objet = objet or RenovationMultigenerationnelle2025()
    d, f, fermer = _fenetre(parent, "Projet de rénovation multigénérationnelle — 2025")
    lire, revoquer, ligne = _champs(f.corps, objet, ("depenses", "autres_demandes"), CONFIRMATIONS_RENOVATION)
    depenses, autres = list(objet.depenses), list(objet.autres_demandes)
    ligne = _liste(d, f.corps, ligne, "depenses", "Dépenses", depenses,
        lambda parent, valeur, cb: _editer_piece(parent, valeur, cb, DepenseRenovation2025), revoquer)
    _liste(d, f.corps, ligne, "autres_demandes", "Autres demandeurs", autres,
        lambda parent, valeur, cb: _editer_piece(parent, valeur, cb, PartAutreDemandeur2025), revoquer)
    def sauver():
        if any(isinstance(w, tk.Toplevel) for w in d.winfo_children()):
            return
        try:
            p = RenovationMultigenerationnelle2025(**lire(), depenses=tuple(depenses), autres_demandes=tuple(autres))
            calculer_renovation_multigenerationnelle_2025(p)
        except ValueError as erreur:
            messagebox.showerror("Projet invalide", str(erreur), parent=d)
            return
        appliquer(p)
        fermer()
    ttk.Button(f.actions, text="Enregistrer le projet", command=sauver).pack(side="right")
    ttk.Button(f.actions, text="Annuler", command=fermer).pack(side="right")


def ouvrir_multigenerationnel_2025(parent, profil, appliquer):
    d, f, fermer = _fenetre(parent, "Rénovations multigénérationnelles — 45354 / 45355")
    lire, revoquer, ligne = _champs(f.corps, profil, ("renovations",), ("resident_annee_complete", "profil_ordinaire"))
    projets = list(profil.renovations)
    ligne = _liste(d, f.corps, ligne, "renovations", "Projets", projets, _editer_projet, revoquer)
    ttk.Label(f.corps, text="Crédit remboursable de 14,5 %. Plafond partagé de 50 000 $ par rénovation terminée en 2025. "
        "Dépenses propres au contribuable uniquement, nettes des aides. Exclure entretien courant, appareils ménagers, "
        "divertissement, financement, travail personnel et autres dépenses non admissibles. Les mêmes dépenses ne peuvent "
        "servir aux frais médicaux fédéraux ni à l'accessibilité domiciliaire. L'admissibilité et l'accord de partage "
        "exigent des pièces vérifiées par le comptable.", wraplength=960).grid(row=ligne, column=0, columnspan=2, pady=10)
    def sauver(effacer=False):
        if any(isinstance(w, tk.Toplevel) for w in d.winfo_children()):
            return
        try:
            p = RenovationsMultigenerationnelles2025() if effacer else RenovationsMultigenerationnelles2025(renovations=tuple(projets), **lire())
            calculer_multigenerationnel_2025(p)
        except ValueError as erreur:
            messagebox.showerror("Rénovations invalides", str(erreur), parent=d)
            return
        appliquer(p)
        fermer()
    ttk.Button(f.actions, text="Valider et appliquer", command=sauver).pack(side="right")
    ttk.Button(f.actions, text="Effacer le profil", command=lambda: sauver(True)).pack(side="right", padx=8)
    ttk.Button(f.actions, text="Fermer", command=fermer).pack(side="right", padx=8)
    return d
