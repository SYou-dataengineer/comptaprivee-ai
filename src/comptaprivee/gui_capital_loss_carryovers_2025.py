"""Confirmation locale du registre de pertes 3F."""
from dataclasses import replace
import tkinter as tk
from tkinter import messagebox, ttk
from .gui_layout import FormulaireDefilant, dimensionner_fenetre, organiser_boutons
from .tax_capital_loss_carryovers_2025 import (
    CHAMPS_REPORTS_PERTES, ProfilReportsPertes2025, empreinte_reports_pertes_2025,
)


def ouvrir_reports_pertes_2025(
    parent,
    profil,
    dossier,
    capital,
    frais,
    appliquer,
    profils_combinaison=(),
):
    dialogue = tk.Toplevel(parent)
    combinaison_3h_e = (
        len(profils_combinaison) == 2
        and all(getattr(p, 'confirme', False) for p in profils_combinaison)
        and getattr(capital, 'confirme', False)
        and frais == type(frais)()
    )
    dialogue.title(
        'Reports de pertes en capital 2025 (3F / 3H-E)'
        if combinaison_3h_e
        else 'Reports de pertes en capital 2025 (3F)'
    )
    dimensionner_fenetre(dialogue, 850, 700)
    dialogue.transient(parent)
    dialogue.grab_set()
    formulaire = FormulaireDefilant(dialogue)
    cadre = formulaire.corps
    cadre.columnconfigure(0, weight=1)
    textes = (
        (
            'Reports de pertes en capital 2025 — Bloc 3F / combinaison 3H-E'
            if combinaison_3h_e
            else 'Reports de pertes en capital 2025 — Bloc 3F'
        ),
        (
            'Combinaison 3H-E active : intérêts + dividendes + capital + reports de pertes. '
            'Les reports 25300/290 réduisent uniquement le revenu imposable et ne modifient '
            'ni le revenu total/net ni la FSS.'
            if combinaison_3h_e
            else 'Vente 3D validée, avec ou sans emploi et frais 3E. Pertes ordinaires 2004–2024 : soldes NETS au taux 50 %, séparés ARC/Québec, après toutes utilisations. Ne pas saisir des pertes brutes ni diviser encore par deux.'
        ),
        'Exemple de registre : 2018;1000;800 | 2024;500;600. Année, solde fédéral, solde Québec. Les plus anciennes pertes sont utilisées automatiquement en premier dans chaque juridiction. Vide seulement si aucun solde.',
        '25300 et 290 limités aux gains imposables 12700/139 et aux soldes. Seul le revenu imposable change : revenu net, revenu total, retenues et FSS restent inchangés. Annexe N : 276 peut réintégrer une partie de 290; une demande 252 excessive sera refusée.',
        'Perte 2025 tirée exclusivement du calcul 3D : ajout unique au registre futur, à rapprocher des avis. Aucun report rétrospectif ni formulaire officiel transmis.',
        'Exclus : soldes avant 2004, taux historiques, PDTPE/ABIL, biens précieux/personnels, exonérations, décès, étranger, conjoint, pertes apparentes, corrections pendantes, IMR non couvert et cas complexes.',
    )
    for i, texte in enumerate(textes):
        ttk.Label(cadre,text=texte,wraplength=560,justify='left').grid(row=i,column=0,sticky='w',pady=8)
    variables = {}
    for i,(nom,libelle) in enumerate(CHAMPS_REPORTS_PERTES):
        variable=tk.StringVar(value=getattr(profil,nom));variables[nom]=variable
        ttk.Label(cadre,text=libelle,wraplength=560).grid(row=6+2*i,column=0,sticky='w',pady=(8,0))
        ttk.Entry(cadre,name=nom+'_reports_pertes',textvariable=variable).grid(row=7+2*i,column=0,sticky='ew',pady=4)
    historique=tk.BooleanVar(value=profil.historique_confirme)
    confirme=tk.BooleanVar(value=profil.confirme)
    tk.Checkbutton(cadre,name='confirmation_historique_pertes',variable=historique,wraplength=560,justify='left',text='Je confirme l’historique exhaustif, les avis ARC/RQ et toutes utilisations prospectives/rétrospectives antérieures. Soldes nets 50 % distincts, y compris les zéros; aucun solde plus ancien ni cas exclu omis.').grid(row=16,column=0,sticky='w',pady=12)
    tk.Checkbutton(cadre,name='confirmation_reports_pertes',variable=confirme,wraplength=560,justify='left',text='Je confirme les demandes 2025 et toutes les exclusions. La perte courante n’est pas saisie dans les soldes antérieurs. Aucun report rétrospectif demandé, aucune perte déjà consommée réutilisée, aucun IMR antérieur. Les clôtures restent à rapprocher des avis.').grid(row=17,column=0,sticky='w',pady=12)
    def revoquer(*_):
        historique.set(False);confirme.set(False)
    for variable in variables.values():variable.trace_add('write',revoquer)
    historique.trace_add('write',lambda *_:confirme.set(False))
    def valider():
        try:
            if dossier is None:raise ValueError('Préparez le dossier et confirmez la vente 3D avant 3F.')
            nouveau=ProfilReportsPertes2025(**{n:v.get().strip() for n,v in variables.items()},historique_confirme=historique.get(),confirme=confirme.get())
            nouveau=replace(nouveau,empreinte=empreinte_reports_pertes_2025(nouveau,dossier,capital,frais))
            appliquer(nouveau)
        except (ValueError,TypeError) as erreur:
            messagebox.showerror('Reports de pertes invalides',str(erreur),parent=dialogue);return
        dialogue.destroy()
    ttk.Button(formulaire.actions,text='Fermer',command=dialogue.destroy).pack(side='right')
    ttk.Button(formulaire.actions,text='Valider et appliquer',command=valider).pack(side='right')
    organiser_boutons(formulaire.actions)
    return dialogue
