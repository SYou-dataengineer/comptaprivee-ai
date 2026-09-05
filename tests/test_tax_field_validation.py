from decimal import Decimal
from pathlib import Path

import pytest

from src.comptaprivee.tax_field_extractor import DonneeFiscaleExtraite
from src.comptaprivee.tax_field_validation import (
    STATUT_CORRIGE_VALIDE,
    STATUT_VALIDE,
    cle_donnee_fiscale,
    corriger_et_valider_donnee_fiscale,
    toutes_donnees_sont_validees,
    valider_donnee_fiscale,
)


def _donnee() -> DonneeFiscaleExtraite:
    return DonneeFiscaleExtraite(
        document=Path("T4_Client.pdf"),
        type_document="T4",
        case="14",
        libelle="Revenu d'emploi",
        valeur=Decimal("52000.00"),
        valeur_brute="52 000,00",
    )


def test_cle_donnee_fiscale_est_stable() -> None:
    assert cle_donnee_fiscale(_donnee()) == (
        "T4_Client.pdf",
        "T4",
        "14",
    )


def test_valider_sans_correction_conserve_valeur() -> None:
    validation = valider_donnee_fiscale(_donnee())

    assert validation.valeur_validee == Decimal("52000.00")
    assert validation.corrigee is False
    assert validation.statut == STATUT_VALIDE


def test_correction_valeur_francaise() -> None:
    validation = corriger_et_valider_donnee_fiscale(
        _donnee(),
        "53 250,75 $",
    )

    assert validation.valeur_validee == Decimal("53250.75")
    assert validation.corrigee is True
    assert validation.statut == STATUT_CORRIGE_VALIDE


def test_correction_decimal() -> None:
    validation = corriger_et_valider_donnee_fiscale(
        _donnee(),
        Decimal("51000.00"),
    )

    assert validation.valeur_validee == Decimal("51000.00")


def test_meme_valeur_corrigee_est_simplement_validee() -> None:
    validation = corriger_et_valider_donnee_fiscale(
        _donnee(),
        "52 000,00",
    )

    assert validation.corrigee is False
    assert validation.statut == STATUT_VALIDE


def test_valeur_negative_est_refusee() -> None:
    with pytest.raises(ValueError):
        corriger_et_valider_donnee_fiscale(
            _donnee(),
            Decimal("-1"),
        )


def test_toutes_donnees_non_validees_retourne_false() -> None:
    donnee = _donnee()

    assert toutes_donnees_sont_validees(
        [donnee],
        {},
    ) is False


def test_toutes_donnees_validees_retourne_true() -> None:
    donnee = _donnee()
    validation = valider_donnee_fiscale(donnee)

    assert toutes_donnees_sont_validees(
        [donnee],
        {
            cle_donnee_fiscale(donnee): validation,
        },
    ) is True
