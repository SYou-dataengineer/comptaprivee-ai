"""Export PDF local du rapport d'estimation fiscale 2025."""

from pathlib import Path
import re
import textwrap
import fitz

from .tax_estimation_2025 import (
    EstimationFiscale2025,
    formater_montant_estimation,
)


def nom_rapport_fiscal_pdf_2025(estimation: EstimationFiscale2025) -> str:
    client = re.sub(r"[^\w-]+", "_", estimation.dossier.client.strip())
    client = re.sub(r"_+", "_", client).strip("_") or "client"
    return f"Estimation_Fiscale_{estimation.dossier.annee_fiscale}_{client}.pdf"


def _lignes(estimation: EstimationFiscale2025) -> list[str]:
    b = estimation.base
    r = estimation.revenu
    f = estimation.federal
    q = estimation.quebec
    x = estimation.rapprochement
    montant = x.remboursement_estime if x.remboursement_estime else x.solde_estime

    lignes = [
        "ESTIMATION FISCALE 2025 - VALIDATION COMPTABLE OBLIGATOIRE",
        "",
        f"Client : {estimation.dossier.client}",
        f"Année fiscale : {estimation.dossier.annee_fiscale}",
        f"Province : {estimation.dossier.province}",
        "",
        "REVENU",
        f"Revenu d'emploi fédéral : {formater_montant_estimation(b.revenu_emploi_federal)}",
        f"Revenu net fédéral : {formater_montant_estimation(r.revenu_net_federal)}",
        f"Revenu imposable fédéral : {formater_montant_estimation(r.revenu_imposable_federal)}",
        f"Revenu d'emploi Québec : {formater_montant_estimation(b.revenu_emploi_quebec)}",
        f"Revenu net Québec : {formater_montant_estimation(r.revenu_net_quebec)}",
        f"Revenu imposable Québec : {formater_montant_estimation(r.revenu_imposable_quebec)}",
        "",
        "FÉDÉRAL",
        f"Impôt fédéral brut : {formater_montant_estimation(f.impot_brut)}",
        f"Crédits non remboursables : {formater_montant_estimation(f.credits_non_remboursables)}",
        f"Impôt fédéral de base : {formater_montant_estimation(x.impot_federal_de_base)}",
        f"Abattement Québec (16,5 %) : -{formater_montant_estimation(x.abattement_quebec)}",
        f"Impôt fédéral après abattement : {formater_montant_estimation(x.impot_federal_apres_abattement)}",
        "",
        "QUÉBEC",
        f"Impôt Québec brut : {formater_montant_estimation(q.impot_brut)}",
        f"Crédit personnel de base : -{formater_montant_estimation(q.credit_personnel_base)}",
        f"Impôt Québec préliminaire : {formater_montant_estimation(x.impot_quebec_preliminaire)}",
        "",
        "RAPPROCHEMENT",
        f"Impôt total préliminaire : {formater_montant_estimation(x.impot_total_preliminaire)}",
        f"Retenue fédérale T4 : {formater_montant_estimation(x.retenue_federale)}",
        f"Retenue Québec RL-1 : {formater_montant_estimation(x.retenue_quebec)}",
        f"Retenues totales : {formater_montant_estimation(x.retenues_totales)}",
        "",
        f"RÉSULTAT : {x.resultat}",
        f"Montant : {formater_montant_estimation(montant)}",
        "",
        f"Statut : {x.statut}",
        "",
        "LIMITATIONS ACTUELLES",
    ]
    lignes.extend(f"- {item}" for item in x.limitations)
    lignes.extend([
        "",
        "Aucune donnée n'a quitté l'ordinateur.",
        "Aucune déclaration n'a été transmise à l'ARC ou à Revenu Québec.",
    ])
    return lignes


def exporter_rapport_fiscal_pdf_2025(
    estimation: EstimationFiscale2025,
    destination: str | Path,
) -> Path:
    chemin = Path(destination)
    if chemin.suffix.lower() != ".pdf":
        chemin = chemin.with_suffix(".pdf")
    chemin.parent.mkdir(parents=True, exist_ok=True)

    doc = fitz.open()
    try:
        page = doc.new_page()
        y = 55
        for ligne in _lignes(estimation):
            morceaux = textwrap.wrap(
                ligne,
                width=92,
                break_long_words=False,
            ) or [""]
            for morceau in morceaux:
                if y > 750:
                    page = doc.new_page()
                    y = 55
                page.insert_text(
                    (48, y),
                    morceau,
                    fontsize=10,
                    fontname="helv",
                )
                y += 15
            if not ligne:
                y += 4

        doc.set_metadata({
            "title": f"Estimation fiscale 2025 - {estimation.dossier.client}",
            "author": "ComptaPrivée AI",
            "subject": "Estimation locale - validation comptable obligatoire",
        })
        doc.save(chemin, garbage=3, deflate=True)
    finally:
        doc.close()

    return chemin
