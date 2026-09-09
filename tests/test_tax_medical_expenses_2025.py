from decimal import Decimal

import pytest

from src.comptaprivee.tax_federal_2025 import ImpotFederalPreliminaire2025
from src.comptaprivee.tax_medical_expenses_2025 import (
    FraisMedicaux2025,
    aucun_frais_medical_2025,
    appliquer_credit_federal_frais_medicaux_2025,
    appliquer_credit_quebec_frais_medicaux_2025,
    credit_federal_frais_medicaux_2025,
    credit_quebec_frais_medicaux_2025,
    montant_frais_medicaux_federal_apres_seuil_2025,
    montant_frais_medicaux_quebec_apres_seuil_2025,
    valider_frais_medicaux_2025,
)
from src.comptaprivee.tax_quebec_2025 import ImpotQuebecPreliminaire2025


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


def _impot_federal_base(montant="5000"):
    return ImpotFederalPreliminaire2025(
        client="Client Test",
        annee_fiscale=2025,
        revenu_imposable=Decimal("50000"),
        impot_brut=Decimal("7000"),
        montant_personnel_base=Decimal("16129"),
        cotisation_base_rrq=Decimal("3000"),
        assurance_emploi_admissible=Decimal("800"),
        rqap_admissible=Decimal("250"),
        montant_canadien_emploi=Decimal("1471"),
        base_credits_non_remboursables=Decimal("21650"),
        credits_non_remboursables=Decimal("3139.25"),
        impot_federal_de_base=Decimal(montant),
        taux_credit=Decimal("0.145"),
        top_up_credit=Decimal("0"),
        limitations=(
            "Résident du Canada et du Québec pour toute l'année.",
            "Aucun crédit pour handicap, frais médicaux ou scolarité.",
            "Aucun don ni crédit transféré.",
        ),
    )


def _impot_quebec_base(montant="5000"):
    return ImpotQuebecPreliminaire2025(
        client="Client Test",
        annee_fiscale=2025,
        province="Québec",
        revenu_imposable=Decimal("50000"),
        impot_brut=Decimal("8000"),
        montant_personnel_base=Decimal("18571"),
        taux_credit_personnel=Decimal("0.14"),
        credit_personnel_base=Decimal("2600"),
        impot_quebec_preliminaire=Decimal(montant),
        limitations=(
            "Résident du Québec et du Canada pour toute l'année.",
            "Aucun crédit handicap, médical, scolarité ou don.",
            "Aucun remboursement ou solde final calculé.",
        ),
    )


def test_zero_est_accepte():
    x = aucun_frais_medical_2025()
    assert valider_frais_medicaux_2025(x) == x


def test_montant_federal_negatif_refuse():
    with pytest.raises(ValueError):
        valider_frais_medicaux_2025(
            FraisMedicaux2025(
                montant_admissible_federal=Decimal("-1")
            )
        )


def test_montant_quebec_negatif_refuse():
    with pytest.raises(ValueError):
        valider_frais_medicaux_2025(
            FraisMedicaux2025(
                montant_admissible_quebec=Decimal("-1")
            )
        )


def test_validation_comptable_obligatoire():
    x = _frais_valides()
    with pytest.raises(ValueError):
        valider_frais_medicaux_2025(
            FraisMedicaux2025(
                **{**x.__dict__, "valide_par_comptable": False}
            )
        )


def test_recus_obligatoires():
    x = _frais_valides()
    with pytest.raises(ValueError):
        valider_frais_medicaux_2025(
            FraisMedicaux2025(
                **{**x.__dict__, "recus_confirmes": False}
            )
        )


def test_remboursements_doivent_etre_soustraits():
    x = _frais_valides()
    with pytest.raises(ValueError):
        valider_frais_medicaux_2025(
            FraisMedicaux2025(
                **{**x.__dict__, "remboursements_soustraits": False}
            )
        )


def test_periode_12_mois_obligatoire():
    x = _frais_valides()
    with pytest.raises(ValueError):
        valider_frais_medicaux_2025(
            FraisMedicaux2025(
                **{
                    **x.__dict__,
                    "periode_12_mois_fin_2025_confirmee": False,
                }
            )
        )


def test_aucune_periode_deja_reclamee_obligatoire():
    x = _frais_valides()
    with pytest.raises(ValueError):
        valider_frais_medicaux_2025(
            FraisMedicaux2025(
                **{
                    **x.__dict__,
                    "aucune_periode_deja_reclamee": False,
                }
            )
        )


def test_profil_simple_obligatoire():
    x = _frais_valides()
    with pytest.raises(ValueError):
        valider_frais_medicaux_2025(
            FraisMedicaux2025(
                **{
                    **x.__dict__,
                    "profil_individuel_sans_conjoint_dependant": False,
                }
            )
        )


def test_source_federale_obligatoire():
    x = _frais_valides()
    with pytest.raises(ValueError):
        valider_frais_medicaux_2025(
            FraisMedicaux2025(
                **{**x.__dict__, "source_federale": ""}
            )
        )


def test_source_quebec_obligatoire():
    x = _frais_valides()
    with pytest.raises(ValueError):
        valider_frais_medicaux_2025(
            FraisMedicaux2025(
                **{**x.__dict__, "source_quebec": ""}
            )
        )


def test_federal_seuil_trois_pour_cent():
    assert (
        montant_frais_medicaux_federal_apres_seuil_2025(
            _frais_valides("3000"),
            Decimal("50000"),
        )
        == Decimal("1500.00")
    )


def test_federal_seuil_plafonne_a_2834():
    assert (
        montant_frais_medicaux_federal_apres_seuil_2025(
            _frais_valides("5000"),
            Decimal("100000"),
        )
        == Decimal("2166.00")
    )


def test_credit_federal_3000_sur_revenu_50000():
    assert (
        credit_federal_frais_medicaux_2025(
            _frais_valides("3000"),
            Decimal("50000"),
        )
        == Decimal("217.50")
    )


def test_credit_federal_zero_si_frais_sous_seuil():
    assert (
        credit_federal_frais_medicaux_2025(
            _frais_valides("1000"),
            Decimal("50000"),
        )
        == Decimal("0.00")
    )


def test_quebec_seuil_trois_pour_cent():
    assert (
        montant_frais_medicaux_quebec_apres_seuil_2025(
            _frais_valides("3000"),
            Decimal("50000"),
        )
        == Decimal("1500.00")
    )


def test_credit_quebec_3000_sur_revenu_50000():
    assert (
        credit_quebec_frais_medicaux_2025(
            _frais_valides("3000"),
            Decimal("50000"),
        )
        == Decimal("300.00")
    )


def test_credit_quebec_zero_si_frais_sous_seuil():
    assert (
        credit_quebec_frais_medicaux_2025(
            _frais_valides("1000"),
            Decimal("50000"),
        )
        == Decimal("0.00")
    )


def test_appliquer_credit_federal_reduit_impot():
    resultat = appliquer_credit_federal_frais_medicaux_2025(
        _impot_federal_base(),
        _frais_valides("3000"),
        Decimal("50000"),
    )

    assert resultat.impot_federal_de_base == Decimal("4782.50")
    assert (
        "Crédit fédéral pour frais médicaux admissibles inclus."
        in resultat.limitations
    )
    assert (
        "Aucun crédit pour handicap, frais médicaux ou scolarité."
        not in resultat.limitations
    )
    assert "Aucun crédit pour handicap ou scolarité." in resultat.limitations


def test_appliquer_credit_federal_zero_ne_modifie_pas_impot():
    impot = _impot_federal_base()
    resultat = appliquer_credit_federal_frais_medicaux_2025(
        impot,
        _frais_valides("1000"),
        Decimal("50000"),
    )

    assert resultat == impot


def test_appliquer_credit_federal_ne_devient_pas_negatif():
    resultat = appliquer_credit_federal_frais_medicaux_2025(
        _impot_federal_base("100"),
        _frais_valides("3000"),
        Decimal("50000"),
    )

    assert resultat.impot_federal_de_base == Decimal("0")


def test_appliquer_credit_quebec_reduit_impot():
    resultat = appliquer_credit_quebec_frais_medicaux_2025(
        _impot_quebec_base(),
        _frais_valides("3000"),
        Decimal("50000"),
    )

    assert resultat.impot_quebec_preliminaire == Decimal("4700.00")
    assert (
        "Crédit Québec pour frais médicaux admissibles inclus."
        in resultat.limitations
    )
    assert (
        "Aucun crédit handicap, médical, scolarité ou don."
        not in resultat.limitations
    )
    assert (
        "Aucun crédit handicap, scolarité ou don."
        in resultat.limitations
    )


def test_appliquer_credit_quebec_zero_ne_modifie_pas_impot():
    impot = _impot_quebec_base()
    resultat = appliquer_credit_quebec_frais_medicaux_2025(
        impot,
        _frais_valides("1000"),
        Decimal("50000"),
    )

    assert resultat == impot


def test_appliquer_credit_quebec_ne_devient_pas_negatif():
    resultat = appliquer_credit_quebec_frais_medicaux_2025(
        _impot_quebec_base("100"),
        _frais_valides("3000"),
        Decimal("50000"),
    )

    assert resultat.impot_quebec_preliminaire == Decimal("0")
