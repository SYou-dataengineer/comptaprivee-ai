from decimal import Decimal

import pytest

from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
    formater_estimation_fiscale_2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_home_accessibility_2025 import _profil


def test_integration_31285_reduit_impot_federal_de_2900():
    dossier = _dossier_52000()
    sans = calculer_estimation_fiscale_2025(dossier)
    avec = calculer_estimation_fiscale_2025(
        dossier,
        accessibilite_domiciliaire_federale=_profil(),
    )

    assert sans.federal.impot_federal_de_base > Decimal("2900")
    assert (
        sans.federal.impot_federal_de_base
        - avec.federal.impot_federal_de_base
    ) == Decimal("2900.00")


def test_integration_31285_reduit_impot_total_apres_abattement():
    dossier = _dossier_52000()
    sans = calculer_estimation_fiscale_2025(dossier)
    avec = calculer_estimation_fiscale_2025(
        dossier,
        accessibilite_domiciliaire_federale=_profil(),
    )

    assert (
        sans.rapprochement.impot_total_preliminaire
        - avec.rapprochement.impot_total_preliminaire
    ) == Decimal("2421.50")


def test_integration_31285_augmente_remboursement():
    dossier = _dossier_52000()
    sans = calculer_estimation_fiscale_2025(dossier)
    avec = calculer_estimation_fiscale_2025(
        dossier,
        accessibilite_domiciliaire_federale=_profil(),
    )

    assert (
        avec.rapprochement.remboursement_estime
        - sans.rapprochement.remboursement_estime
    ) == Decimal("2421.50")


def test_integration_31285_est_conservee_dans_estimation():
    profil = _profil()
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        accessibilite_domiciliaire_federale=profil,
    )

    assert estimation.accessibilite_domiciliaire_federale == profil


def test_integration_31285_resume_fiscal_enrichi():
    profil = _profil()
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        accessibilite_domiciliaire_federale=profil,
    )

    resume = formater_estimation_fiscale_2025(estimation)

    assert "ACCESSIBILITÉ DOMICILIAIRE — FÉDÉRAL 2025" in resume
    assert "Dépenses admissibles — ligne 31285" in resume
    assert "20\xa0000,00 $" in resume
    assert "Crédit fédéral calculé" in resume
    assert "2\xa0900,00 $" in resume
    assert "Taux du crédit fédéral 2025 : 14,5 %" in resume
    assert "65 ans ou plus / CIPH" in resume
    assert "Rénovation durable et intégrante" in resume
    assert profil.source_renovation in resume


def test_integration_31285_profil_vide_ne_change_rien():
    dossier = _dossier_52000()
    sans = calculer_estimation_fiscale_2025(dossier)
    avec = calculer_estimation_fiscale_2025(
        dossier,
        accessibilite_domiciliaire_federale=None,
    )

    assert (
        sans.federal.impot_federal_de_base
        == avec.federal.impot_federal_de_base
    )
    assert (
        sans.rapprochement.impot_total_preliminaire
        == avec.rapprochement.impot_total_preliminaire
    )


def test_integration_31285_revalidation_est_active():
    with pytest.raises(ValueError, match="source"):
        calculer_estimation_fiscale_2025(
            _dossier_52000(),
            accessibilite_domiciliaire_federale=_profil(
                source_renovation=" "
            ),
        )


def test_integration_31285_garde_fou_34990():
    profil = _profil()

    dossier = _dossier_52000()
    estimation = calculer_estimation_fiscale_2025(
        dossier,
        accessibilite_domiciliaire_federale=profil,
    )

    assert estimation.revenu.revenu_imposable_federal <= Decimal("57375")


def test_rapprochement_affiche_31285():
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        accessibilite_domiciliaire_federale=_profil(),
    )

    limitations = " ".join(estimation.rapprochement.limitations)

    assert (
        "Dépenses pour l'accessibilité domiciliaire ligne 31285 incluses."
        in limitations
    )
