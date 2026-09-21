"""Formulaire local 3E, pièces proposées puis confirmées humainement."""
from dataclasses import replace
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .gui_layout import FormulaireDefilant, dimensionner_fenetre, organiser_boutons
from .tax_investment_expenses_2025 import (
    CHAMPS_FRAIS_PLACEMENT, ProfilFraisPlacement2025, extraire_frais_placement_2025,
    empreinte_frais_placement_2025,
)


def ouvrir_frais_placement_2025(parent, profil, dossier, profils, appliquer, extraire_texte):
    dialogue = tk.Toplevel(parent)
    dialogue.title('Frais de placement 2025 (3E)')
    dimensionner_fenetre(dialogue, 850, 700)
    dialogue.transient(parent)
    dialogue.grab_set()
    formulaire = FormulaireDefilant(dialogue)
    cadre = formulaire.corps
    cadre.columnconfigure(0, weight=1)
    textes = (
        'Frais de placement 2025 — Bloc 3E',
        'Un parcours 3A à 3D validé, CAD, titulaire unique, placements non enregistrés. Gestion/garde et intérêts simples payés en 2025, admissibles dans les deux juridictions.',
        '22100 et 231 réduisent le revenu net. Annexe N : excédent des frais ajouté à 260. Report Québec 252 limité au solde vérifié et au surplus des revenus sur les frais. Aucun report fédéral.',
        'FSS recalculé après les frais 231; le report 252 ne réduit pas son assiette. Commissions, PBR et frais de disposition ne doivent jamais être déduits ici.',
        'Exclus : frais de conseil/juridiques/comptables, fonds/T3 intégrés, RL-1 L-4, régimes enregistrés, compte conjoint, étranger, emprunt mixte/refinancé/après vente, assurance vie, pertes antérieures, IMR antérieur et autres cas complexes. Revenus bruts ajustés limités à 177 882 $.',
    )
    for i, texte in enumerate(textes):
        ttk.Label(cadre, text=texte, wraplength=560, justify='left').grid(row=i, column=0, sticky='w', pady=8)
    variables = {}
    for i, (nom, libelle) in enumerate(CHAMPS_FRAIS_PLACEMENT):
        variable = tk.StringVar(value=getattr(profil, nom))
        variables[nom] = variable
        ttk.Label(cadre, text=libelle, wraplength=560).grid(row=6+2*i, column=0, sticky='w', pady=(8,0))
        ttk.Entry(cadre, name=nom+'_frais_placement', textvariable=variable).grid(row=7+2*i, column=0, sticky='ew', pady=4)
    report = tk.BooleanVar(value=profil.report_confirme)
    confirme = tk.BooleanVar(value=profil.confirme)
    tk.Checkbutton(cadre, name='confirmation_report_frais', variable=report, wraplength=560, justify='left',
        text='Je confirme le solde Québec inutilisé, même nul : annexes N et avis depuis 2004, toutes les utilisations prospectives/rétrospectives déduites. Aucun solde fédéral ni perte en capital inclus.').grid(row=23, column=0, sticky='w', pady=12)
    tk.Checkbutton(cadre, name='confirmation_frais_placement', variable=confirme, wraplength=560, justify='left',
        text='Je confirme les pièces, leur paiement en 2025, l’admissibilité et toutes les exclusions ci-dessus. Frais liés au placement déclaré producteur d’intérêts/dividendes. Aucun montant remboursé, capitalisé, intégré à un fonds ou déduit ailleurs. Tout emprunt sert directement et exclusivement ce placement; aucun intérêt après vente. Aucun IMR antérieur.').grid(row=24, column=0, sticky='w', pady=12)

    def revoquer(*_):
        report.set(False)
        confirme.set(False)
    for variable in variables.values():
        variable.trace_add('write', revoquer)
    report.trace_add('write', lambda *_: confirme.set(False))

    def importer():
        chemin = filedialog.askopenfilename(parent=dialogue, title='Pièce justificative des frais 2025')
        if not chemin:
            return
        try:
            propositions = extraire_frais_placement_2025(extraire_texte(Path(chemin)))
        except (ValueError, OSError, RuntimeError) as erreur:
            messagebox.showerror('Extraction frais à vérifier', str(erreur), parent=dialogue)
            return
        # Remplacement complet des deux montants, jamais cumul avec un import précédent.
        for nom in ('gestion', 'interets'):
            variables[nom].set(propositions.get(nom, '0'))
        variables['source'].set(str(Path(chemin)))
        messagebox.showinfo('Propositions à vérifier', 'Vérifiez chaque montant, le compte, le paiement et l’admissibilité sur la pièce complète avant confirmation.', parent=dialogue)

    def valider():
        try:
            if dossier is None:
                raise ValueError('Préparez le dossier puis validez son parcours de placement avant 3E.')
            nouveau = ProfilFraisPlacement2025(**{n:v.get().strip() for n,v in variables.items()},
                confirme=confirme.get(), report_confirme=report.get())
            nouveau = replace(nouveau, empreinte=empreinte_frais_placement_2025(nouveau, dossier, *profils))
            appliquer(nouveau)
        except (ValueError, TypeError) as erreur:
            messagebox.showerror('Frais de placement invalides', str(erreur), parent=dialogue)
            return
        dialogue.destroy()

    ttk.Button(formulaire.actions, text='Importer une pièce', command=importer).pack(side='left')
    ttk.Button(formulaire.actions, text='Valider et appliquer', command=valider).pack(side='right')
    ttk.Button(formulaire.actions, text='Fermer', command=dialogue.destroy).pack(side='right')
    organiser_boutons(formulaire.actions)
    return dialogue
