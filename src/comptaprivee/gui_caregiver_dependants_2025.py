"""Fiches individuelles de personnes à charge — ligne fédérale 30450."""
from dataclasses import fields
from decimal import Decimal, InvalidOperation
import tkinter as tk
from tkinter import ttk, messagebox
from .gui_layout import FormulaireDefilant, dimensionner_fenetre
from .tax_federal_caregiver_other_dependant_2025 import (
    AidantNaturelAutrePersonneChargeFederal2025 as Profil, PersonneAidant30450,
    LIENS_AUTORISES, valider_aidant_naturel_30450_2025)

LIBELLES = {
    "lien_personne": "Lien familial avec le demandeur ou son conjoint",
    "revenu_net_personne_ligne_23600": "Revenu net de cette personne — ligne 23600 ($)",
    "age_18_ans_ou_plus": "Âge de 18 ans ou plus au cours de 2025 confirmé",
    "personne_soutenue_en_2025": "Personne soutenue par le demandeur en 2025",
    "infirmite_physique_ou_mentale": "Infirmité physique ou mentale confirmée",
    "dependance_due_uniquement_a_infirmite": "Dépendance due à l'infirmité",
    "dependance_periode_considerable": "Dépendance pendant une période considérable",
    "resident_canada_au_moins_un_moment_2025": "Résidence au Canada dans l'année (sauf enfant/petit-enfant)",
    "aucune_reclamation_ligne_30300_30400_pour_personne": "Aucun montant 30300/30400 pour cette personne",
    "aucun_paiement_pension_alimentaire_pour_personne": "Aucune pension alimentaire pour cette personne",
    "aucun_partage_reclamation_30450": "Aucun partage de la réclamation 30450",
    "preuve_medicale_ou_t2201_confirmee": "Preuve médicale ou T2201 approuvé confirmé",
    "valide_par_comptable": "Fiche individuelle validée par le comptable",
    "source_personne": "Source du lien, du revenu, de la dépendance et de la preuve",
    "partage_30450_confirme": "Entente de partage confirmée entre tous les soutiens",
    "montant_attribue_autres_soutiens": "Somme attribuée aux autres soutiens selon l'entente ($)",
    "source_partage": "Source de l'entente entre tous les soutiens",
}


def fenetre(parent, titre):
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


def editer_personne(parent, personne, appliquer):
    d, f, fermer = fenetre(parent, "Fiche personne à charge — 30450")
    identite = {}
    for rang, (nom, texte) in enumerate((("reference", "Référence unique locale (sans NAS)"),
            ("nom", "Nom complet de la personne"), ("naissance", "Date de naissance (AAAA-MM-JJ)"))):
        v = tk.StringVar(value=getattr(personne, nom))
        identite[nom] = v
        ttk.Label(f.corps, text=texte).grid(row=rang, column=0, sticky="w")
        ttk.Entry(f.corps, name=nom + "_5x", textvariable=v).grid(row=rang, column=1, sticky="ew", pady=4)
    variables = {}
    for rang, (nom, texte) in enumerate(LIBELLES.items(), start=3):
        valeur = getattr(personne.profil, nom)
        v = tk.BooleanVar(value=valeur) if type(valeur) is bool else tk.StringVar(value=str(valeur))
        variables[nom] = v
        if type(valeur) is bool:
            ttk.Checkbutton(f.corps, name=nom + "_5x", text=texte, variable=v).grid(
                row=rang, column=0, columnspan=2, sticky="w", pady=4)
        else:
            ttk.Label(f.corps, text=texte, wraplength=460).grid(row=rang, column=0, sticky="w", pady=4)
            w = (ttk.Combobox(f.corps, values=tuple(sorted(LIENS_AUTORISES)), state="readonly",
                textvariable=v, name=nom + "_5x") if nom == "lien_personne" else
                ttk.Entry(f.corps, name=nom + "_5x", textvariable=v))
            w.grid(row=rang, column=1, sticky="ew", pady=4)
    def revoquer(*_):
        for nom in ("valide_par_comptable", "preuve_medicale_ou_t2201_confirmee", "partage_30450_confirme"):
            variables[nom].set(False)
    for v in identite.values():
        v.trace_add("write", revoquer)
    for nom, v in variables.items():
        if nom not in ("valide_par_comptable", "preuve_medicale_ou_t2201_confirmee", "partage_30450_confirme"):
            v.trace_add("write", revoquer)
    for nom in ("preuve_medicale_ou_t2201_confirmee", "partage_30450_confirme"):
        variables[nom].trace_add("write", lambda *_: variables["valide_par_comptable"].set(False))
    def sauver():
        try:
            valeurs = {nom: v.get() for nom, v in variables.items()}
            for champ in fields(Profil):
                if champ.name in valeurs and isinstance(champ.default, Decimal):
                    valeurs[champ.name] = Decimal(valeurs[champ.name].strip().replace(" ", "").replace(",", ".") or "0")
            ident = {nom: v.get().strip() for nom, v in identite.items()}
            valeurs["reference_personne"] = ident["reference"] if valeurs["partage_30450_confirme"] else ""
            nouveau = PersonneAidant30450(**ident, profil=Profil(reclamer_montant=True, **valeurs))
            valider_aidant_naturel_30450_2025(Profil(reclamer_montant=True, valide_par_comptable=True,
                identites_distinctes_confirmees=True, personnes_detaillees=(nouveau,)))
        except (ValueError, InvalidOperation) as erreur:
            messagebox.showerror("Fiche 30450 invalide", str(erreur), parent=d)
            return
        appliquer(nouveau)
        fermer()
    ttk.Button(f.actions, text="Enregistrer la personne", command=sauver).pack(side="right")
    ttk.Button(f.actions, text="Annuler", command=fermer).pack(side="right")


def ouvrir_personnes_30450_2025(parent, profil, appliquer):
    d, f, fermer = fenetre(parent, "Personnes à charge — 30450 / 51120")
    personnes = list(profil.personnes_detaillees)
    if not personnes and profil.reclamer_montant:
        personnes.append(PersonneAidant30450(reference=profil.reference_personne or "personne-1", profil=profil))
    ttk.Label(f.corps, text="Une fiche par personne adulte. Le plafond est calculé séparément selon son revenu; "
        "les parts attribuées aux autres soutiens sont ensuite déduites. "
        "Vérifiez les identités et les exclusions avec les pièces. Une ancienne fiche nécessite un nom et une naissance.",
        wraplength=950).grid(row=0, column=0, columnspan=2, sticky="w", pady=10)
    table = ttk.Treeview(f.corps, name="personnes_5x", columns=("personne",), show="headings", height=8)
    table.heading("personne", text="Référence — nom — naissance — lien")
    table.column("personne", width=950)
    table.grid(row=1, column=0, columnspan=2, sticky="ew")
    identites = tk.BooleanVar(value=profil.identites_distinctes_confirmees)
    valide = tk.BooleanVar(value=bool(profil.personnes_detaillees) and profil.valide_par_comptable)
    def rafraichir():
        table.delete(*table.get_children())
        for i, p in enumerate(personnes):
            table.insert("", "end", iid=str(i), values=(f"{p.reference} — {p.nom} — {p.naissance} — {p.profil.lien_personne}",))
    def changement():
        identites.set(False)
        valide.set(False)
        rafraichir()
    def editer(nouveau):
        if not nouveau and not table.selection():
            return
        i = None if nouveau else int(table.selection()[0])
        def sauver(p):
            if i is None:
                personnes.append(p)
            else:
                personnes[i] = p
            changement()
        editer_personne(d, PersonneAidant30450() if nouveau else personnes[i], sauver)
    def retirer():
        if table.selection():
            del personnes[int(table.selection()[0])]
            changement()
    actions = ttk.Frame(f.corps)
    actions.grid(row=2, column=0, columnspan=2, sticky="w", pady=8)
    for texte, commande in (("Ajouter", lambda: editer(True)), ("Modifier", lambda: editer(False)), ("Retirer", retirer)):
        ttk.Button(actions, text=texte, command=commande).pack(side="left", padx=4)
    ttk.Checkbutton(f.corps, name="identites_5x", text="Personnes distinctes et références rapprochées des pièces",
        variable=identites).grid(row=3, column=0, columnspan=2, sticky="w")
    ttk.Checkbutton(f.corps, name="valide_5x", text="Ensemble des fiches validé par le comptable",
        variable=valide).grid(row=4, column=0, columnspan=2, sticky="w")
    identites.trace_add("write", lambda *_: valide.set(False))
    def sauver():
        try:
            nouveau = (Profil(reclamer_montant=True, valide_par_comptable=valide.get(),
                identites_distinctes_confirmees=identites.get(), personnes_detaillees=tuple(personnes))
                if personnes else Profil())
            valider_aidant_naturel_30450_2025(nouveau)
        except ValueError as erreur:
            messagebox.showerror("Personnes 30450 invalides", str(erreur), parent=d)
            return
        appliquer(nouveau)
        fermer()
    ttk.Button(f.actions, text="Appliquer les personnes", command=sauver).pack(side="right")
    ttk.Button(f.actions, text="Annuler", command=fermer).pack(side="right")
    rafraichir()
