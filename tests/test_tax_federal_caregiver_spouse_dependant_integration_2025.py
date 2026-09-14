from decimal import Decimal

import pytest

from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
from src.comptaprivee.tax_federal_caregiver_spouse_dependant_2025 import (
    credit_federal_ligne_30425_2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_caregiver_spouse_dependant_2025 import (
    _profil_conjoint,
    _profil_personne_charge,
)
from tests.test_tax_federal_eligible_dependant_caregiver_base_2025 import (
    _profil_18_plus_infirmite,
)
from tests.test_tax_federal_spouse_caregiver_base_2025 import _profil_infirmite


def _30425_conjoint(**modifications):
    valeurs = {
        "revenu_net_personne_ligne_23600": Decimal("12000"),
        "montant_reclame_ligne_30300_ou_30400": Decimal("6816"),
    }
    valeurs.update(modifications)
    return _profil_conjoint(**valeurs)


def _30425_personne_charge(**modifications):
    valeurs = {
        "revenu_net_personne_ligne_23600": Decimal("12000"),
        "montant_reclame_ligne_30300_ou_30400": Decimal("6816"),
    }
    valeurs.update(modifications)
    return _profil_personne_charge(**valeurs)


def test_integration_30425_conjoint_reduit_impot_federal():
    dossier = _dossier_52000()
    conjoint = _profil_infirmite(
        revenu_net_contribuable_ligne_23600=Decimal("51515.00")
    )

    sans_30425 = calculer_estimation_fiscale_2025(
        dossier,
        montant_conjoint_federal=conjoint,
    )
    profil_30425 = _30425_conjoint()
    avec_30425 = calculer_estimation_fiscale_2025(
        dossier,
        montant_conjoint_federal=conjoint,
        aidant_conjoint_personne_charge_federal=profil_30425,
    )

    credit = credit_federal_ligne_30425_2025(profil_30425)
    assert credit == Decimal("258.83")
    assert (
        sans_30425.federal.impot_federal_de_base
        - avec_30425.federal.impot_federal_de_base
    ) == credit
    assert (
        "Montant canadien pour aidant naturel ligne 30425 inclus."
        in avec_30425.rapprochement.limitations
    )


def test_integration_30425_personne_charge_reduit_impot_federal():
    dossier = _dossier_52000()
    personne_charge = _profil_18_plus_infirmite(
        revenu_net_contribuable_ligne_23600=Decimal("51515.00")
    )

    sans_30425 = calculer_estimation_fiscale_2025(
        dossier,
        personne_charge_admissible_federale=personne_charge,
    )
    profil_30425 = _30425_personne_charge()
    avec_30425 = calculer_estimation_fiscale_2025(
        dossier,
        personne_charge_admissible_federale=personne_charge,
        aidant_conjoint_personne_charge_federal=profil_30425,
    )

    credit = credit_federal_ligne_30425_2025(profil_30425)
    assert credit == Decimal("258.83")
    assert (
        sans_30425.federal.impot_federal_de_base
        - avec_30425.federal.impot_federal_de_base
    ) == credit
    assert (
        "Montant canadien pour aidant naturel ligne 30425 inclus."
        in avec_30425.rapprochement.limitations
    )


def test_30425_conjoint_exige_ligne_30300_active():
    with pytest.raises(ValueError, match="30300"):
        calculer_estimation_fiscale_2025(
            _dossier_52000(),
            aidant_conjoint_personne_charge_federal=_30425_conjoint(),
        )


def test_30425_personne_charge_exige_ligne_30400_active():
    with pytest.raises(ValueError, match="30400"):
        calculer_estimation_fiscale_2025(
            _dossier_52000(),
            aidant_conjoint_personne_charge_federal=_30425_personne_charge(),
        )


def test_30425_refuse_montant_source_incoherent():
    with pytest.raises(ValueError, match="30300/30400"):
        calculer_estimation_fiscale_2025(
            _dossier_52000(),
            montant_conjoint_federal=_profil_infirmite(
                revenu_net_contribuable_ligne_23600=Decimal("51515.00")
            ),
            aidant_conjoint_personne_charge_federal=_30425_conjoint(
                montant_reclame_ligne_30300_ou_30400=Decimal("3000")
            ),
        )


def test_30425_refuse_revenu_personne_incoherent():
    with pytest.raises(ValueError, match="revenu net"):
        calculer_estimation_fiscale_2025(
            _dossier_52000(),
            montant_conjoint_federal=_profil_infirmite(
                revenu_net_contribuable_ligne_23600=Decimal("51515.00")
            ),
            aidant_conjoint_personne_charge_federal=_30425_conjoint(
                revenu_net_personne_ligne_23600=Decimal("13000")
            ),
        )
