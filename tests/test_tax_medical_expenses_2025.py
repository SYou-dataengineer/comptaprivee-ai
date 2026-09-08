from decimal import Decimal
import pytest
from src.comptaprivee.tax_medical_expenses_2025 import (
    FraisMedicaux2025, aucun_frais_medical_2025,
    credit_federal_frais_medicaux_2025, credit_quebec_frais_medicaux_2025,
    montant_frais_medicaux_federal_apres_seuil_2025,
    montant_frais_medicaux_quebec_apres_seuil_2025,
    valider_frais_medicaux_2025,
)


def _frais_valides(montant="3000"):
    return FraisMedicaux2025(
        montant_admissible_federal=Decimal(montant),
        montant_admissible_quebec=Decimal(montant),
        source_federale="Reçus médicaux vérifiés",
        source_quebec="Reçus médicaux vérifiés",
        valide_par_comptable=True,
        recus_confirmes=True,
        remboursements_soustraits=True,
        periode_12_mois_fin_2025_confirmee=True,
        aucune_periode_deja_reclamee=True,
        profil_individuel_sans_conjoint_dependant=True,
    )


def test_zero_est_accepte():
    x = aucun_frais_medical_2025()
    assert valider_frais_medicaux_2025(x) == x


def test_montant_federal_negatif_refuse():
    with pytest.raises(ValueError):
        valider_frais_medicaux_2025(FraisMedicaux2025(montant_admissible_federal=Decimal("-1")))


def test_montant_quebec_negatif_refuse():
    with pytest.raises(ValueError):
        valider_frais_medicaux_2025(FraisMedicaux2025(montant_admissible_quebec=Decimal("-1")))


def test_validation_comptable_obligatoire():
    x = _frais_valides()
    with pytest.raises(ValueError):
        valider_frais_medicaux_2025(FraisMedicaux2025(**{**x.__dict__, "valide_par_comptable": False}))


def test_recus_obligatoires():
    x = _frais_valides()
    with pytest.raises(ValueError):
        valider_frais_medicaux_2025(FraisMedicaux2025(**{**x.__dict__, "recus_confirmes": False}))


def test_remboursements_doivent_etre_soustraits():
    x = _frais_valides()
    with pytest.raises(ValueError):
        valider_frais_medicaux_2025(FraisMedicaux2025(**{**x.__dict__, "remboursements_soustraits": False}))


def test_periode_12_mois_obligatoire():
    x = _frais_valides()
    with pytest.raises(ValueError):
        valider_frais_medicaux_2025(FraisMedicaux2025(**{**x.__dict__, "periode_12_mois_fin_2025_confirmee": False}))


def test_aucune_periode_deja_reclamee_obligatoire():
    x = _frais_valides()
    with pytest.raises(ValueError):
        valider_frais_medicaux_2025(FraisMedicaux2025(**{**x.__dict__, "aucune_periode_deja_reclamee": False}))


def test_profil_simple_obligatoire():
    x = _frais_valides()
    with pytest.raises(ValueError):
        valider_frais_medicaux_2025(FraisMedicaux2025(**{**x.__dict__, "profil_individuel_sans_conjoint_dependant": False}))


def test_source_federale_obligatoire():
    x = _frais_valides()
    with pytest.raises(ValueError):
        valider_frais_medicaux_2025(FraisMedicaux2025(**{**x.__dict__, "source_federale": ""}))


def test_source_quebec_obligatoire():
    x = _frais_valides()
    with pytest.raises(ValueError):
        valider_frais_medicaux_2025(FraisMedicaux2025(**{**x.__dict__, "source_quebec": ""}))


def test_federal_seuil_trois_pour_cent():
    assert montant_frais_medicaux_federal_apres_seuil_2025(_frais_valides("3000"), Decimal("50000")) == Decimal("1500.00")


def test_federal_seuil_plafonne_a_2834():
    assert montant_frais_medicaux_federal_apres_seuil_2025(_frais_valides("5000"), Decimal("100000")) == Decimal("2166.00")


def test_credit_federal_3000_sur_revenu_50000():
    assert credit_federal_frais_medicaux_2025(_frais_valides("3000"), Decimal("50000")) == Decimal("217.50")


def test_credit_federal_zero_si_frais_sous_seuil():
    assert credit_federal_frais_medicaux_2025(_frais_valides("1000"), Decimal("50000")) == Decimal("0.00")


def test_quebec_seuil_trois_pour_cent():
    assert montant_frais_medicaux_quebec_apres_seuil_2025(_frais_valides("3000"), Decimal("50000")) == Decimal("1500.00")


def test_credit_quebec_3000_sur_revenu_50000():
    assert credit_quebec_frais_medicaux_2025(_frais_valides("3000"), Decimal("50000")) == Decimal("300.00")


def test_credit_quebec_zero_si_frais_sous_seuil():
    assert credit_quebec_frais_medicaux_2025(_frais_valides("1000"), Decimal("50000")) == Decimal("0.00")
