from pathlib import Path

import pytest

from src.comptaprivee.tax_case import (
    PROVINCES_PHASE_1,
    annee_fiscale_par_defaut,
    annees_fiscales_disponibles,
    creer_dossier_fiscal,
    normaliser_province,
)


def test_phase1_prend_en_charge_quebec() -> None:
    assert PROVINCES_PHASE_1 == ("Québec",)


@pytest.mark.parametrize("annee_systeme", [2025, 2026, 2027, 2035])
def test_annee_fiscale_par_defaut_independante_horloge(annee_systeme) -> None:
    assert annee_fiscale_par_defaut(annee_systeme) == 2025


def test_annees_fiscales_disponibles_limitees_aux_moteurs_livres() -> None:
    assert annees_fiscales_disponibles(
        2026,
        profondeur=4,
    ) == (2025,)


def test_normaliser_province_accepte_quebec_sans_accent() -> None:
    assert normaliser_province("Quebec") == "Québec"


def test_creer_dossier_exige_client() -> None:
    with pytest.raises(ValueError):
        creer_dossier_fiscal(
            client="   ",
            annee_fiscale=2025,
        )


def test_creer_dossier_normalise_client_et_annee() -> None:
    dossier = creer_dossier_fiscal(
        client="  Marie   Tremblay  ",
        annee_fiscale="2025",
    )

    assert dossier.client == "Marie Tremblay"
    assert dossier.annee_fiscale == 2025
    assert dossier.province == "Québec"


def test_dossier_sans_document_est_brouillon() -> None:
    dossier = creer_dossier_fiscal(
        client="Client Test",
        annee_fiscale=2025,
    )

    assert dossier.documents == ()
    assert dossier.statut == "Brouillon — aucun document importé"


def test_dossier_avec_documents_indique_nombre() -> None:
    dossier = creer_dossier_fiscal(
        client="Client Test",
        annee_fiscale=2025,
        documents=[
            Path("T4_demo.pdf"),
            Path("RL1_demo.pdf"),
        ],
    )

    assert len(dossier.documents) == 2
    assert dossier.statut == "Brouillon — 2 document(s) importé(s)"
