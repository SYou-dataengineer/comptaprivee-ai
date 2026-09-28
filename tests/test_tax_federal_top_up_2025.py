"""Feuille 5000-D1 (25), annexe 9 et agrégats T1 : calculs indépendants."""
from decimal import Decimal as D, ROUND_HALF_UP

import pytest

from src.comptaprivee.tax_federal_top_up_2025 import (
    calculer_annexe9_ligne22_2025, calculer_base_33500_2025,
    calculer_credit_compensatoire_2025, calculer_credits_non_remboursables_2025,
    calculer_ligne_33800_2025, valider_scolarite_sans_report_2025,
)


@pytest.mark.parametrize("credit,dons,attendu", [
    ("0", "0", "0.00"), ("8319.37", "0", "0.00"),
    ("8319.38", "0", "0.00"), ("8319.39", "0", "0.00"),
    ("8319.52", "0", "0.00"), ("8319.53", "0", "0.01"),
    ("8290.38", "29", "0.00"), ("8290.53", "29", "0.01"),
    ("10000", "0", "57.98"), ("10000", "29", "58.98"),
])
def test_formule_seuil_et_exemple_officiel(credit, dons, attendu):
    # Exemple des notes explicatives Finances 2025 : 10 000 $ -> 57,98 $.
    assert calculer_credit_compensatoire_2025(D(credit), D(dons)) == D(attendu)


@pytest.mark.parametrize("dons,attendu", [("0", "0"), ("100", "14.50"), ("200", "29"), ("1000", "29")])
def test_annexe9_ligne22_premiers_200(dons, attendu):
    assert calculer_annexe9_ligne22_2025(D(dons)) == D(attendu)


@pytest.mark.parametrize("valeur", [D("NaN"), D("Infinity"), D("-Infinity"), D("-0.01"), 100, 1.5, "100"])
def test_montants_decimal_finis_non_negatifs(valeur):
    with pytest.raises(ValueError):
        calculer_credit_compensatoire_2025(valeur, D(0))
    with pytest.raises(ValueError):
        calculer_credit_compensatoire_2025(D(0), valeur)
    with pytest.raises(ValueError):
        calculer_base_33500_2025((("30000", valeur),))


def test_refus_credit_dons_total_comme_ligne22():
    with pytest.raises(ValueError, match="29,00"):
        calculer_credit_compensatoire_2025(D(10000), D(261))
    with pytest.raises(ValueError, match="incluse"):
        calculer_credits_non_remboursables_2025((), D(29), D(0))


@pytest.mark.parametrize("lignes", [(("40425", D(100)),), (("40500", D(100)),), (("30000", D(100)), ("30000", D(100)))])
def test_exclusion_credits_ulterieurs_et_doublons(lignes):
    with pytest.raises(ValueError, match="comptée deux fois"):
        calculer_base_33500_2025(lignes)


def test_arrondi_global_et_application_unique():
    r = calculer_credits_non_remboursables_2025(
        (("30000", D("21157.08")), ("30300", D("11129"))), D(29), D(261),
    )
    assert r.base_ligne_33500 == D("32286.08")
    assert r.credit_ligne_33800 == D("4681.48")
    assert r.total_credits_ligne_35000 == D("4942.48")
    assert calculer_ligne_33800_2025(D("1")) == D("0.15")
    assert D("0.145").quantize(D(".01"), rounding=ROUND_HALF_UP) == D(".15")


def test_annexe11_limite_sans_report_independante_du_compensatoire():
    assert valider_scolarite_sans_report_2025(D(30000), D(70000), D(11000), D(22000)) == D(30000)
    with pytest.raises(ValueError, match="report"):
        valider_scolarite_sans_report_2025(D(60000), D(70000), D(11000), D(22000))
    assert valider_scolarite_sans_report_2025(D(30000), D(52000), D(7540), D(22000)) == D(30000)
    with pytest.raises(ValueError, match="report"):
        valider_scolarite_sans_report_2025(D("30000.01"), D(52000), D(7540), D(22000))
