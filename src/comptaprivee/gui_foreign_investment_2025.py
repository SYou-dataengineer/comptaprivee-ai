"""Formulaire local du Bloc 3G — placements et impôts étrangers 2025."""
import tkinter as tk
from decimal import Decimal, InvalidOperation
from tkinter import messagebox, ttk

from .gui_layout import FormulaireDefilant, dimensionner_fenetre, organiser_boutons
from .tax_foreign_investment_2025 import (
    ProfilCreditImpotEtranger2025,
    ProfilPlacementEtranger2025,
)


def _decimal_champ(texte: str, libelle: str) -> Decimal:
    if not isinstance(texte, str):
        raise ValueError(f"{libelle} invalide.")
    nettoye = texte.strip().replace("\u00a0", "").replace(" ", "").replace(",", ".")
    if not nettoye:
        return Decimal("0")
    try:
        valeur = Decimal(nettoye)
    except (InvalidOperation, ValueError) as erreur:
        raise ValueError(f"{libelle} invalide.") from erreur
    if not valeur.is_finite() or valeur < 0 or valeur != valeur.quantize(Decimal(".01")):
        raise ValueError(f"{libelle} doit être un montant non négatif au cent près.")
    return valeur


def ouvrir_placement_etranger_2025(
    parent,
    profil_placement,
    profil_credit,
    dossier,
    appliquer,
):
    dialogue = tk.Toplevel(parent)
    dialogue.title("Placements et impôts étrangers 2025 (3G)")
    dimensionner_fenetre(dialogue, 860, 720)
    dialogue.transient(parent)
    dialogue.grab_set()

    formulaire = FormulaireDefilant(dialogue)
    cadre = formulaire.corps
    cadre.columnconfigure(0, weight=1)

    textes = (
        "Placements et impôts étrangers 2025 — Bloc 3G",
        "Profil prudent : un seul pays, un seul titulaire, revenu de placement non commercial, paire T5 15/16 + RL-3 F/G, montants déjà en dollars canadiens.",
        "Le revenu étranger brut est ajouté aux lignes 12100 fédérale et 130 Québec. L'impôt étranger payé ne réduit pas ce revenu et n'est pas une retenue canadienne.",
        "Les crédits 40500 et 409 doivent provenir respectivement d'un T2209 et d'un TP-772 2025 vérifiés. Le moteur ne reconstitue pas automatiquement l'intégralité de ces formulaires.",
        "La cotisation FSS ligne 446 est calculée sur le revenu de placement étranger ligne 130. Les obligations T1135 / TP-1079.8.BE doivent être vérifiées séparément.",
        "Exclus : plusieurs pays, compte conjoint, revenu d'entreprise, pension étrangère, gains en capital étrangers, convention fiscale ambiguë, conversion de devise implicite et cas complexes.",
    )
    for i, texte in enumerate(textes):
        ttk.Label(
            cadre,
            text=texte,
            wraplength=590,
            justify="left",
        ).grid(row=i, column=0, sticky="w", pady=7)

    source = tk.StringVar(value=profil_placement.source)
    pays = tk.StringVar(value=profil_placement.pays)
    devise = tk.StringVar(value=profil_placement.devise)
    credit_federal = tk.StringVar(
        value=("" if profil_credit.credit_federal_40500 == 0 else format(profil_credit.credit_federal_40500, "f"))
    )
    credit_quebec = tk.StringVar(
        value=("" if profil_credit.credit_quebec_409 == 0 else format(profil_credit.credit_quebec_409, "f"))
    )
    source_t2209 = tk.StringVar(value=profil_credit.source_t2209)
    source_tp772 = tk.StringVar(value=profil_credit.source_tp772)

    champs = (
        ("source_placement_etranger", "Source / justificatif T5-RL-3", source),
        ("pays_placement_etranger", "Pays étranger", pays),
        ("devise_placement_etranger", "Devise des montants validés", devise),
        ("credit_federal_40500_etranger", "Crédit fédéral confirmé — ligne 40500", credit_federal),
        ("credit_quebec_409_etranger", "Crédit Québec confirmé — ligne 409", credit_quebec),
        ("source_t2209_etranger", "Référence T2209 vérifié", source_t2209),
        ("source_tp772_etranger", "Référence TP-772 vérifié", source_tp772),
    )

    row = 7
    for nom, libelle, variable in champs:
        ttk.Label(cadre, text=libelle, wraplength=590).grid(
            row=row, column=0, sticky="w", pady=(7, 0)
        )
        ttk.Entry(cadre, name=nom, textvariable=variable).grid(
            row=row + 1, column=0, sticky="ew", pady=4
        )
        row += 2

    obligations = tk.BooleanVar(
        value=profil_placement.obligations_biens_etrangers_verifiees
    )
    confirme_placement = tk.BooleanVar(value=profil_placement.confirme)
    confirme_credit = tk.BooleanVar(value=profil_credit.confirme)

    tk.Checkbutton(
        cadre,
        name="confirmation_obligations_etranger",
        variable=obligations,
        wraplength=590,
        justify="left",
        text=(
            "Je confirme avoir vérifié séparément les obligations de déclaration "
            "de biens étrangers T1135 / TP-1079.8.BE applicables au dossier."
        ),
    ).grid(row=row, column=0, sticky="w", pady=10)
    row += 1

    tk.Checkbutton(
        cadre,
        name="confirmation_placement_etranger",
        variable=confirme_placement,
        wraplength=590,
        justify="left",
        text=(
            "Je confirme : un pays, un titulaire, revenu non commercial, montants "
            "déjà en CAD, T5 15/16 et RL-3 F/G appariés, aucun cas exclu."
        ),
    ).grid(row=row, column=0, sticky="w", pady=10)
    row += 1

    tk.Checkbutton(
        cadre,
        name="confirmation_credit_etranger",
        variable=confirme_credit,
        wraplength=590,
        justify="left",
        text=(
            "Je confirme que 40500 et 409 proviennent des formulaires 2025 "
            "T2209 et TP-772 vérifiés; aucune estimation automatique des crédits."
        ),
    ).grid(row=row, column=0, sticky="w", pady=10)

    def revoquer(*_):
        confirme_placement.set(False)
        confirme_credit.set(False)

    for variable in (
        source,
        pays,
        devise,
        credit_federal,
        credit_quebec,
        source_t2209,
        source_tp772,
    ):
        variable.trace_add("write", revoquer)
    obligations.trace_add("write", revoquer)

    def valider():
        try:
            if dossier is None:
                raise ValueError(
                    "Préparez et verrouillez d'abord le dossier fiscal."
                )
            nouveau_placement = ProfilPlacementEtranger2025(
                source=source.get().strip(),
                confirme=confirme_placement.get(),
                pays=pays.get().strip(),
                devise=devise.get().strip(),
                obligations_biens_etrangers_verifiees=obligations.get(),
            )
            nouveau_credit = ProfilCreditImpotEtranger2025(
                credit_federal_40500=_decimal_champ(
                    credit_federal.get(), "Crédit fédéral 40500"
                ),
                credit_quebec_409=_decimal_champ(
                    credit_quebec.get(), "Crédit Québec 409"
                ),
                source_t2209=source_t2209.get().strip(),
                source_tp772=source_tp772.get().strip(),
                confirme=confirme_credit.get(),
            )
            appliquer(nouveau_placement, nouveau_credit)
        except (ValueError, TypeError) as erreur:
            messagebox.showerror(
                "Placement étranger invalide",
                str(erreur),
                parent=dialogue,
            )
            return
        dialogue.destroy()

    ttk.Button(
        formulaire.actions, text="Fermer", command=dialogue.destroy
    ).pack(side="right")
    ttk.Button(
        formulaire.actions,
        text="Valider et appliquer",
        command=valider,
    ).pack(side="right")
    organiser_boutons(formulaire.actions)
    return dialogue
