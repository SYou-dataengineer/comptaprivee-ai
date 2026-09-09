"""Export PDF local du rapport d'estimation fiscale 2025."""

from pathlib import Path
import re
import textwrap
import fitz

from .tax_estimation_2025 import (
    EstimationFiscale2025,
    formater_montant_estimation,
)
from .tax_medical_expenses_2025 import (
    credit_federal_frais_medicaux_2025,
    credit_quebec_frais_medicaux_2025,
)


def nom_rapport_fiscal_pdf_2025(estimation: EstimationFiscale2025) -> str:
    client = re.sub(r"[^\w-]+", "_", estimation.dossier.client.strip())
    client = re.sub(r"_+", "_", client).strip("_") or "client"
    return (
        f"Estimation_Fiscale_"
        f"{estimation.dossier.annee_fiscale}_{client}.pdf"
    )


def _lignes(estimation: EstimationFiscale2025) -> list[str]:
    b = estimation.base
    r = estimation.revenu
    f = estimation.federal
    q = estimation.quebec
    x = estimation.rapprochement
    medical = estimation.frais_medicaux

    montant = (
        x.remboursement_estime
        if x.remboursement_estime
        else x.solde_estime
    )

    lignes = [
        "ESTIMATION FISCALE 2025 - VALIDATION COMPTABLE OBLIGATOIRE",
        "",
        f"Client : {estimation.dossier.client}",
        f"Année fiscale : {estimation.dossier.annee_fiscale}",
        f"Province : {estimation.dossier.province}",
        "",
        "REVENU",
        (
            "Revenu d'emploi fédéral : "
            f"{formater_montant_estimation(b.revenu_emploi_federal)}"
        ),
        (
            "Revenu net fédéral : "
            f"{formater_montant_estimation(r.revenu_net_federal)}"
        ),
        (
            "Revenu imposable fédéral : "
            f"{formater_montant_estimation(r.revenu_imposable_federal)}"
        ),
        (
            "Revenu d'emploi Québec : "
            f"{formater_montant_estimation(b.revenu_emploi_quebec)}"
        ),
        (
            "Revenu net Québec : "
            f"{formater_montant_estimation(r.revenu_net_quebec)}"
        ),
        (
            "Revenu imposable Québec : "
            f"{formater_montant_estimation(r.revenu_imposable_quebec)}"
        ),
    ]

    if (
        medical.montant_admissible_federal > 0
        or medical.montant_admissible_quebec > 0
    ):
        credit_federal = credit_federal_frais_medicaux_2025(
            medical,
            r.revenu_net_federal,
        )
        credit_quebec = credit_quebec_frais_medicaux_2025(
            medical,
            r.revenu_net_quebec,
        )

        lignes.extend(
            [
                "",
                "FRAIS MÉDICAUX VALIDÉS",
                (
                    "Montant admissible fédéral : "
                    f"{formater_montant_estimation(
                        medical.montant_admissible_federal
                    )}"
                ),
                (
                    "Crédit fédéral - lignes 33099 / 33200 : "
                    f"{formater_montant_estimation(credit_federal)}"
                ),
                f"Source fédérale : {medical.source_federale}",
                (
                    "Montant admissible Québec : "
                    f"{formater_montant_estimation(
                        medical.montant_admissible_quebec
                    )}"
                ),
                (
                    "Crédit Québec - ligne 381 : "
                    f"{formater_montant_estimation(credit_quebec)}"
                ),
                f"Source Québec : {medical.source_quebec}",
                (
                    "Validation comptable : "
                    + (
                        "confirmée"
                        if medical.valide_par_comptable
                        else "non confirmée"
                    )
                ),
                (
                    "Reçus confirmés : "
                    + ("oui" if medical.recus_confirmes else "non")
                ),
                (
                    "Remboursements soustraits : "
                    + (
                        "oui"
                        if medical.remboursements_soustraits
                        else "non"
                    )
                ),
                (
                    "Période de 12 mois se terminant en 2025 : "
                    + (
                        "confirmée"
                        if medical.periode_12_mois_fin_2025_confirmee
                        else "non confirmée"
                    )
                ),
            ]
        )

    lignes.extend(
        [
            "",
            "FÉDÉRAL",
            (
                "Impôt fédéral brut : "
                f"{formater_montant_estimation(f.impot_brut)}"
            ),
            (
                "Crédits non remboursables : "
                f"{formater_montant_estimation(
                    f.credits_non_remboursables
                )}"
            ),
            (
                "Impôt fédéral de base : "
                f"{formater_montant_estimation(
                    x.impot_federal_de_base
                )}"
            ),
            (
                "Abattement Québec (16,5 %) : -"
                f"{formater_montant_estimation(x.abattement_quebec)}"
            ),
            (
                "Impôt fédéral après abattement : "
                f"{formater_montant_estimation(
                    x.impot_federal_apres_abattement
                )}"
            ),
            "",
            "QUÉBEC",
            (
                "Impôt Québec brut : "
                f"{formater_montant_estimation(q.impot_brut)}"
            ),
            (
                "Crédit personnel de base : -"
                f"{formater_montant_estimation(
                    q.credit_personnel_base
                )}"
            ),
            (
                "Impôt Québec préliminaire : "
                f"{formater_montant_estimation(
                    x.impot_quebec_preliminaire
                )}"
            ),
            "",
            "RAPPROCHEMENT",
            (
                "Impôt total préliminaire : "
                f"{formater_montant_estimation(
                    x.impot_total_preliminaire
                )}"
            ),
            (
                "Retenue fédérale T4 : "
                f"{formater_montant_estimation(x.retenue_federale)}"
            ),
            (
                "Retenue Québec RL-1 : "
                f"{formater_montant_estimation(x.retenue_quebec)}"
            ),
            (
                "Retenues totales : "
                f"{formater_montant_estimation(x.retenues_totales)}"
            ),
            "",
            f"RÉSULTAT : {x.resultat}",
            f"Montant : {formater_montant_estimation(montant)}",
            "",
            f"Statut : {x.statut}",
            "",
            "LIMITATIONS ACTUELLES",
        ]
    )

    lignes.extend(f"- {item}" for item in x.limitations)
    lignes.extend(
        [
            "",
            "Aucune donnée n'a quitté l'ordinateur.",
            (
                "Aucune déclaration n'a été transmise à l'ARC "
                "ou à Revenu Québec."
            ),
        ]
    )
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

        doc.set_metadata(
            {
                "title": (
                    "Estimation fiscale 2025 - "
                    f"{estimation.dossier.client}"
                ),
                "author": "ComptaPrivée AI",
                "subject": (
                    "Estimation locale - "
                    "validation comptable obligatoire"
                ),
            }
        )
        doc.save(chemin, garbage=3, deflate=True)
    finally:
        doc.close()

    return chemin
