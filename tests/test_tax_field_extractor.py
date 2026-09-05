from decimal import Decimal
from pathlib import Path

import pytest

from src.comptaprivee.tax_field_extractor import (
    STATUT_A_VALIDER,
    convertir_montant_fiscal,
    extraire_cases_fiscales,
    formater_montant_fiscal,
)


def test_convertir_montant_francais() -> None:
    assert convertir_montant_fiscal("52 000,00 $") == Decimal("52000.00")


def test_convertir_montant_anglais() -> None:
    assert convertir_montant_fiscal("7,500.00") == Decimal("7500.00")


def test_formater_montant_fiscal() -> None:
    assert formater_montant_fiscal(
        Decimal("52000")
    ) == "52 000,00 $"


def test_extraire_t4_case_14() -> None:
    donnees = extraire_cases_fiscales(
        "T4",
        "Case 14 - Revenu d'emploi\n52 000,00 $",
        "T4_Test.pdf",
    )

    assert len(donnees) == 1
    assert donnees[0].case == "14"
    assert donnees[0].valeur == Decimal("52000.00")


def test_extraire_t4_cases_principales() -> None:
    texte = """
    Case 14 - Revenu d'emploi
    52 000,00 $
    Case 17 - Cotisations RRQ
    2 900,00 $
    Case 18 - Cotisations AE
    850,00 $
    Case 22 - Impôt retenu
    7 500,00 $
    """

    donnees = extraire_cases_fiscales(
        "T4",
        texte,
        "T4_Test.pdf",
    )

    valeurs = {donnee.case: donnee.valeur for donnee in donnees}

    assert valeurs["14"] == Decimal("52000.00")
    assert valeurs["17"] == Decimal("2900.00")
    assert valeurs["18"] == Decimal("850.00")
    assert valeurs["22"] == Decimal("7500.00")


def test_extraire_t4_case_16_si_presente() -> None:
    donnees = extraire_cases_fiscales(
        "T4",
        "Box 16 CPP contributions 3,100.00",
        "T4_Hors_Quebec.pdf",
    )

    assert donnees[0].case == "16"
    assert donnees[0].valeur == Decimal("3100.00")


def test_extraire_rl1_cases_a_c_e() -> None:
    texte = """
    Case A - Revenus d'emploi
    52 000,00 $
    Case C - Assurance emploi
    850,00 $
    Case E - Impôt du Québec retenu
    6 200,00 $
    """

    donnees = extraire_cases_fiscales(
        "RL-1",
        texte,
        "RL1_Test.pdf",
    )

    valeurs = {donnee.case: donnee.valeur for donnee in donnees}

    assert valeurs["A"] == Decimal("52000.00")
    assert valeurs["C"] == Decimal("850.00")
    assert valeurs["E"] == Decimal("6200.00")


def test_extraire_rl1_cases_ba_bb_actuelles() -> None:
    texte = """
    Case B.A - Cotisation de base au RRQ
    2 500,00 $
    Case B.B - Cotisation supplémentaire au RRQ
    400,00 $
    """

    donnees = extraire_cases_fiscales(
        "RL-1",
        texte,
        "RL1_Test.pdf",
    )

    valeurs = {donnee.case: donnee.valeur for donnee in donnees}

    assert valeurs["B.A"] == Decimal("2500.00")
    assert valeurs["B.B"] == Decimal("400.00")


def test_extraire_rl1_case_b_ancienne_forme() -> None:
    donnees = extraire_cases_fiscales(
        "RL-1",
        "Case B - Cotisation RRQ\n2 900,00 $",
        "RL1_Test.pdf",
    )

    assert donnees[0].case == "B"
    assert donnees[0].valeur == Decimal("2900.00")


def test_extraction_conserve_source_et_validation() -> None:
    donnees = extraire_cases_fiscales(
        "T4",
        "Case 22\n7 500,00 $",
        Path("dossier/T4_Client.pdf"),
    )

    donnee = donnees[0]

    assert donnee.document == Path("dossier/T4_Client.pdf")
    assert donnee.type_document == "T4"
    assert donnee.statut == STATUT_A_VALIDER


def test_type_non_pris_en_charge_est_refuse() -> None:
    with pytest.raises(ValueError):
        extraire_cases_fiscales(
            "T5",
            "Case 13 100,00",
            "T5.pdf",
        )


def test_extraire_t4_champs_requis_moteur_2025() -> None:
    texte = """
    Case 24 - Gains assurables AE
    52 000,00 $
    Case 26 - Gains admissibles RPC RRQ
    52 000,00 $
    Case 55 - Cotisations RQAP
    260,00 $
    Case 56 - Gains assurables RQAP
    52 000,00 $
    """

    donnees = extraire_cases_fiscales(
        "T4",
        texte,
        "T4_Moteur_2025.pdf",
    )

    valeurs = {donnee.case: donnee.valeur for donnee in donnees}

    assert valeurs["24"] == Decimal("52000.00")
    assert valeurs["26"] == Decimal("52000.00")
    assert valeurs["55"] == Decimal("260.00")
    assert valeurs["56"] == Decimal("52000.00")


def test_extraire_t4_case_17a_si_presente() -> None:
    donnees = extraire_cases_fiscales(
        "T4",
        "Case 17A - Deuxième cotisation RRQ\n300,00 $",
        "T4_Moteur_2025.pdf",
    )

    assert donnees[0].case == "17A"
    assert donnees[0].valeur == Decimal("300.00")


def test_extraire_rl1_champs_requis_moteur_2025() -> None:
    texte = """
    Case G - Salaire admissible au RRQ
    52 000,00 $
    Case H - Cotisation au RQAP
    260,00 $
    Case I - Salaire admissible au RQAP
    52 000,00 $
    """

    donnees = extraire_cases_fiscales(
        "RL-1",
        texte,
        "RL1_Moteur_2025.pdf",
    )

    valeurs = {donnee.case: donnee.valeur for donnee in donnees}

    assert valeurs["G"] == Decimal("52000.00")
    assert valeurs["H"] == Decimal("260.00")
    assert valeurs["I"] == Decimal("52000.00")


def test_champs_optionnels_absents_ne_creent_pas_de_valeur() -> None:
    donnees = extraire_cases_fiscales(
        "T4",
        "Case 14 - Revenu d'emploi\\n52 000,00 $",
        "T4_Simple.pdf",
    )

    cases = {donnee.case for donnee in donnees}

    assert "14" in cases
    assert "17A" not in cases
    assert "55" not in cases

