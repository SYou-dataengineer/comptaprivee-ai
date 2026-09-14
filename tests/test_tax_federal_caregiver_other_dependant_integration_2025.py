from decimal import Decimal

import pytest

from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
    formater_estimation_fiscale_2025,
)
from src.comptaprivee.tax_federal_caregiver_other_dependant_2025 import (
    AidantNaturelAutrePersonneChargeFederal2025,
    credit_federal_ligne_30450_2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_caregiver_other_dependant_2025 import _profil


def test_integration_30450_reduit_impot_federal():
    dossier = _dossier_52000()
    sans_30450 = calculer_estimation_fiscale_2025(dossier)

    profil = _profil()
    avec_30450 = calculer_estimation_fiscale_2025(
        dossier,
        aidant_autre_personne_charge_federal=profil,
    )

    credit = credit_federal_ligne_30450_2025(profil)
    assert credit == Decimal("550.71")
    assert (
        sans_30450.federal.impot_federal_de_base
        - avec_30450.federal.impot_federal_de_base
    ) == credit
    assert (
        "Montant canadien pour aidant naturel ligne 30450 inclus."
        in avec_30450.rapprochement.limitations
    )


def test_integration_30450_est_preserve_dans_estimation():
    profil = _profil()
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        aidant_autre_personne_charge_federal=profil,
    )

    assert estimation.aidant_autre_personne_charge_federal == profil


def test_integration_30450_resume_fiscal_enrichi():
    profil = _profil()
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        aidant_autre_personne_charge_federal=profil,
    )

    resume = formater_estimation_fiscale_2025(estimation)

    assert (
        "AIDANT NATUREL — AUTRE PERSONNE À CHARGE 18+ — "
        "FÉDÉRAL 2025"
        in resume
    )
    assert "Nombre de personnes à charge — ligne 51120 : 1" in resume
    assert "Montant canadien pour aidant naturel — ligne 30450" in resume
    assert "Crédit fédéral calculé" in resume
    assert "Taux du crédit fédéral 2025 : 14,5 %" in resume
    assert profil.source_personne in resume


def test_integration_30450_profil_vide_ne_change_rien():
    dossier = _dossier_52000()
    sans = calculer_estimation_fiscale_2025(dossier)
    avec_vide = calculer_estimation_fiscale_2025(
        dossier,
        aidant_autre_personne_charge_federal=(
            AidantNaturelAutrePersonneChargeFederal2025()
        ),
    )

    assert (
        sans.federal.impot_federal_de_base
        == avec_vide.federal.impot_federal_de_base
    )
    assert (
        sans.rapprochement.impot_total_preliminaire
        == avec_vide.rapprochement.impot_total_preliminaire
    )


def test_integration_30450_validation_est_recontrolee():
    with pytest.raises(ValueError, match="source"):
        calculer_estimation_fiscale_2025(
            _dossier_52000(),
            aidant_autre_personne_charge_federal=_profil(
                source_personne=" "
            ),
        )


def test_rapprochement_reconnait_30450_comme_credit_familial():
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        aidant_autre_personne_charge_federal=_profil(),
    )

    limitations = " ".join(estimation.rapprochement.limitations)
    assert "ligne 30450 inclus" in limitations
    assert "Aucun crédit familial" not in limitations
