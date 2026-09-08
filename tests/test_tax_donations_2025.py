from decimal import Decimal
import pytest
from src.comptaprivee.tax_donations_2025 import (
    DonsBienfaisance2025,
    aucun_don_bienfaisance_2025,
    credit_federal_dons_2025,
    credit_quebec_dons_2025,
    valider_dons_bienfaisance_2025,
)


def _dons_valides(montant="1000"):
    return DonsBienfaisance2025(
        montant_admissible_federal=Decimal(montant),
        montant_admissible_quebec=Decimal(montant),
        source_federale="Reçu officiel organisme enregistré",
        source_quebec="Reçu officiel organisme enregistré",
        valide_par_comptable=True,
        donataire_reconnu_confirme=True,
        dons_monetaires_2025_uniquement=True,
        aucun_report_anterieur=True,
    )


def test_zero_est_accepte():
    x = aucun_don_bienfaisance_2025()
    assert valider_dons_bienfaisance_2025(x) == x


def test_montant_federal_negatif_refuse():
    with pytest.raises(ValueError):
        valider_dons_bienfaisance_2025(
            DonsBienfaisance2025(montant_admissible_federal=Decimal("-1"))
        )


def test_montant_quebec_negatif_refuse():
    with pytest.raises(ValueError):
        valider_dons_bienfaisance_2025(
            DonsBienfaisance2025(montant_admissible_quebec=Decimal("-1"))
        )


def test_validation_comptable_obligatoire():
    x = _dons_valides()
    with pytest.raises(ValueError):
        valider_dons_bienfaisance_2025(
            DonsBienfaisance2025(**{**x.__dict__, "valide_par_comptable": False})
        )


def test_donataire_reconnu_obligatoire():
    x = _dons_valides()
    with pytest.raises(ValueError):
        valider_dons_bienfaisance_2025(
            DonsBienfaisance2025(**{**x.__dict__, "donataire_reconnu_confirme": False})
        )


def test_dons_monetaires_2025_uniquement_obligatoire():
    x = _dons_valides()
    with pytest.raises(ValueError):
        valider_dons_bienfaisance_2025(
            DonsBienfaisance2025(**{**x.__dict__, "dons_monetaires_2025_uniquement": False})
        )


def test_report_anterieur_refuse():
    x = _dons_valides()
    with pytest.raises(ValueError):
        valider_dons_bienfaisance_2025(
            DonsBienfaisance2025(**{**x.__dict__, "aucun_report_anterieur": False})
        )


def test_source_federale_obligatoire():
    x = _dons_valides()
    with pytest.raises(ValueError):
        valider_dons_bienfaisance_2025(
            DonsBienfaisance2025(**{**x.__dict__, "source_federale": ""})
        )


def test_source_quebec_obligatoire():
    x = _dons_valides()
    with pytest.raises(ValueError):
        valider_dons_bienfaisance_2025(
            DonsBienfaisance2025(**{**x.__dict__, "source_quebec": ""})
        )


def test_don_jan_fev_deja_reclame_2024_refuse():
    x = _dons_valides()
    with pytest.raises(ValueError):
        valider_dons_bienfaisance_2025(
            DonsBienfaisance2025(
                **{
                    **x.__dict__,
                    "inclut_dons_jan_fev_2025": True,
                    "dons_jan_fev_deja_reclames_2024": True,
                }
            )
        )


def test_credit_federal_100():
    assert credit_federal_dons_2025(
        _dons_valides("100"), Decimal("52000")
    ) == Decimal("14.50")


def test_credit_federal_1000():
    assert credit_federal_dons_2025(
        _dons_valides("1000"), Decimal("52000")
    ) == Decimal("261.00")


def test_credit_federal_revenu_tres_eleve_refuse():
    with pytest.raises(ValueError):
        credit_federal_dons_2025(
            _dons_valides("1000"), Decimal("253414.01")
        )


def test_credit_quebec_100():
    assert credit_quebec_dons_2025(
        _dons_valides("100"), Decimal("52000")
    ) == Decimal("20.00")


def test_credit_quebec_1000():
    assert credit_quebec_dons_2025(
        _dons_valides("1000"), Decimal("52000")
    ) == Decimal("232.00")


def test_credit_quebec_revenu_tres_eleve_refuse():
    with pytest.raises(ValueError):
        credit_quebec_dons_2025(
            _dons_valides("1000"), Decimal("129590.01")
        )
