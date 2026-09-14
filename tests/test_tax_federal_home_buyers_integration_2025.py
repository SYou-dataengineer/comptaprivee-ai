from decimal import Decimal

import pytest

from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
    formater_estimation_fiscale_2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_home_buyers_2025 import _profil


def test_integration_31270_reduit_impot_federal_de_1450():
    dossier = _dossier_52000()
    sans = calculer_estimation_fiscale_2025(dossier)
    avec = calculer_estimation_fiscale_2025(
        dossier,
        achat_habitation_federal=_profil(),
    )

    assert (
        sans.federal.impot_federal_de_base
        - avec.federal.impot_federal_de_base
    ) == Decimal("1450.00")


def test_integration_31270_reduit_impot_total_apres_abattement():
    dossier = _dossier_52000()
    sans = calculer_estimation_fiscale_2025(dossier)
    avec = calculer_estimation_fiscale_2025(
        dossier,
        achat_habitation_federal=_profil(),
    )

    assert (
        sans.rapprochement.impot_total_preliminaire
        - avec.rapprochement.impot_total_preliminaire
    ) == Decimal("1210.75")


def test_integration_31270_augmente_remboursement():
    dossier = _dossier_52000()
    sans = calculer_estimation_fiscale_2025(dossier)
    avec = calculer_estimation_fiscale_2025(
        dossier,
        achat_habitation_federal=_profil(),
    )

    assert (
        avec.rapprochement.remboursement_estime
        - sans.rapprochement.remboursement_estime
    ) == Decimal("1210.75")


def test_integration_31270_est_conservee_dans_estimation():
    profil = _profil()
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        achat_habitation_federal=profil,
    )

    assert estimation.achat_habitation_federal == profil


def test_integration_31270_resume_fiscal_enrichi():
    profil = _profil()
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        achat_habitation_federal=profil,
    )

    resume = formater_estimation_fiscale_2025(estimation)

    assert "ACHAT D'UNE HABITATION — FÉDÉRAL 2025" in resume
    assert "Montant réclamé — ligne 31270" in resume
    assert "10\xa0000,00 $" in resume
    assert "Crédit fédéral calculé" in resume
    assert "1\xa0450,00 $" in resume
    assert "Taux du crédit fédéral 2025 : 14,5 %" in resume
    assert "Première habitation" in resume
    assert profil.source_habitation in resume


def test_integration_31270_profil_vide_ne_change_rien():
    dossier = _dossier_52000()
    sans = calculer_estimation_fiscale_2025(dossier)
    avec = calculer_estimation_fiscale_2025(
        dossier,
        achat_habitation_federal=None,
    )

    assert (
        sans.federal.impot_federal_de_base
        == avec.federal.impot_federal_de_base
    )
    assert (
        sans.rapprochement.impot_total_preliminaire
        == avec.rapprochement.impot_total_preliminaire
    )


def test_integration_31270_revalidation_est_active():
    with pytest.raises(ValueError, match="source"):
        calculer_estimation_fiscale_2025(
            _dossier_52000(),
            achat_habitation_federal=_profil(
                source_habitation=" "
            ),
        )


def test_rapprochement_affiche_31270():
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        achat_habitation_federal=_profil(),
    )

    limitations = " ".join(estimation.rapprochement.limitations)

    assert (
        "Montant pour l'achat d'une habitation ligne 31270 inclus."
        in limitations
    )
