from decimal import Decimal
from pathlib import Path

import pytest

from src.comptaprivee.tax_case import creer_dossier_fiscal
from src.comptaprivee.tax_field_extractor import DonneeFiscaleExtraite
from src.comptaprivee.tax_field_validation import (
    DonneeFiscaleValidee,
    cle_donnee_fiscale,
    corriger_et_valider_donnee_fiscale,
    valider_donnee_fiscale,
)
from src.comptaprivee.tax_validated_case import (
    STATUT_DOSSIER_VALIDE,
    construire_dossier_fiscal_valide,
)


def _dossier():
    return creer_dossier_fiscal(
        client="Client Test",
        annee_fiscale=2025,
        province="Québec",
        documents=[
            Path("T4_Test.pdf"),
            Path("RL1_Test.pdf"),
        ],
    )


def _donnee_t4() -> DonneeFiscaleExtraite:
    return DonneeFiscaleExtraite(
        document=Path("T4_Test.pdf"),
        type_document="T4",
        case="14",
        libelle="Revenu d'emploi",
        valeur=Decimal("52000.00"),
        valeur_brute="52 000,00",
    )


def _donnee_rl1() -> DonneeFiscaleExtraite:
    return DonneeFiscaleExtraite(
        document=Path("RL1_Test.pdf"),
        type_document="RL-1",
        case="E",
        libelle="Impôt du Québec retenu",
        valeur=Decimal("6200.00"),
        valeur_brute="6 200,00",
    )


def test_refuse_dossier_sans_donnees_extraites() -> None:
    with pytest.raises(ValueError):
        construire_dossier_fiscal_valide(
            _dossier(),
            [],
            {},
        )


def test_refuse_validation_partielle() -> None:
    t4 = _donnee_t4()
    rl1 = _donnee_rl1()

    with pytest.raises(ValueError):
        construire_dossier_fiscal_valide(
            _dossier(),
            [t4, rl1],
            {
                cle_donnee_fiscale(t4):
                    valider_donnee_fiscale(t4),
            },
        )


def test_construit_dossier_quand_tout_est_valide() -> None:
    t4 = _donnee_t4()
    rl1 = _donnee_rl1()

    validations = {
        cle_donnee_fiscale(t4):
            valider_donnee_fiscale(t4),
        cle_donnee_fiscale(rl1):
            valider_donnee_fiscale(rl1),
    }

    dossier = construire_dossier_fiscal_valide(
        _dossier(),
        [t4, rl1],
        validations,
    )

    assert len(dossier.donnees_validees) == 2
    assert dossier.statut == STATUT_DOSSIER_VALIDE


def test_conserve_valeur_corrigee_validee() -> None:
    t4 = _donnee_t4()
    validation = corriger_et_valider_donnee_fiscale(
        t4,
        "53 000,00 $",
    )

    dossier = construire_dossier_fiscal_valide(
        _dossier(),
        [t4],
        {
            cle_donnee_fiscale(t4): validation,
        },
    )

    assert (
        dossier.donnees_validees[0].valeur_validee
        == Decimal("53000.00")
    )


def test_conserve_identite_du_dossier() -> None:
    t4 = _donnee_t4()

    dossier = construire_dossier_fiscal_valide(
        _dossier(),
        [t4],
        {
            cle_donnee_fiscale(t4):
                valider_donnee_fiscale(t4),
        },
    )

    assert dossier.client == "Client Test"
    assert dossier.annee_fiscale == 2025
    assert dossier.province == "Québec"


def test_conserve_documents_du_dossier() -> None:
    t4 = _donnee_t4()

    dossier = construire_dossier_fiscal_valide(
        _dossier(),
        [t4],
        {
            cle_donnee_fiscale(t4):
                valider_donnee_fiscale(t4),
        },
    )

    assert dossier.documents == (
        Path("T4_Test.pdf"),
        Path("RL1_Test.pdf"),
    )


def test_refuse_donnees_dupliquees() -> None:
    t4 = _donnee_t4()
    validation = valider_donnee_fiscale(t4)

    with pytest.raises(ValueError):
        construire_dossier_fiscal_valide(
            _dossier(),
            [t4, t4],
            {
                cle_donnee_fiscale(t4): validation,
            },
        )


def test_refuse_validation_qui_ne_correspond_pas_source() -> None:
    t4 = _donnee_t4()
    cle = cle_donnee_fiscale(t4)

    validation_incoherente = DonneeFiscaleValidee(
        document=Path("Autre_T4.pdf"),
        type_document="T4",
        case="14",
        libelle="Revenu d'emploi",
        valeur_extraite=Decimal("52000.00"),
        valeur_validee=Decimal("52000.00"),
        corrigee=False,
        statut="Validé par le comptable",
    )

    with pytest.raises(ValueError):
        construire_dossier_fiscal_valide(
            _dossier(),
            [t4],
            {
                cle: validation_incoherente,
            },
        )
