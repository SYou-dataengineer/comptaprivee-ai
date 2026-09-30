from dataclasses import replace
from decimal import Decimal as D
import pytest
from src.comptaprivee.tax_quebec_home_support_2025 import (
    CONFIRMATIONS_6K, MaintienDomicileQuebec2025, valider_maintien_domicile_quebec_2025,
    calculer_maintien_domicile_quebec_2025, maintien_domicile_vers_dict, maintien_domicile_depuis_dict,
)


def profil(**kw):
    return replace(MaintienDomicileQuebec2025(activer=True, naissance="1950-01-01", source="Bail et reçus fictifs vérifiés",
        loyers_mensuels=(D(1000),)*12, **{nom: True for nom in CONFIRMATIONS_6K}), **kw)


@pytest.mark.parametrize("loyer,base,credit", [("1", "360", "140.40"), ("599.99", "360", "140.40"),
    ("600", "360", "140.40"), ("600.01", "360.01", "140.40"), ("1000", "600", "234.00"),
    ("1199.99", "719.99", "280.80"), ("1200", "720", "280.80"), ("1200.01", "720", "280.80"),
    ("999999999.99", "720", "280.80")])
def test_bornes_loyers_et_taux_2025(loyer, base, credit):
    r = calculer_maintien_domicile_quebec_2025(profil(loyers_mensuels=(D(loyer),)*12), revenu_net_275=D(71010))
    assert r.depenses_ligne_75 == D(base)
    assert r.credit_ligne_458 == D(credit)


def test_douze_loyers_variables_et_precision_interne():
    p = profil(loyers_mensuels=(D("600.01"),)*6+(D("1200.01"),)*6)
    r = calculer_maintien_domicile_quebec_2025(p, revenu_net_275=D(0))
    assert r.loyers_retenus == (D("600.01"),)*6+(D(1200),)*6
    assert r.base_loyers_exacte == D("540.003")
    assert r.depenses_ligne_75 == D("540.00")
    assert r.credit_ligne_458 == D("210.60")


@pytest.mark.parametrize("revenu", ["71010.01", "80000", "999999999.99"])
def test_reduction_hors_perimetre_refusee(revenu):
    with pytest.raises(ValueError, match="71010"):
        calculer_maintien_domicile_quebec_2025(profil(), revenu_net_275=D(revenu))


@pytest.mark.parametrize("champ", CONFIRMATIONS_6K)
@pytest.mark.parametrize("valeur", [False, 1, "oui"])
def test_confirmations_strictes(champ, valeur):
    with pytest.raises(ValueError):
        valider_maintien_domicile_quebec_2025(profil(**{champ: valeur}))


@pytest.mark.parametrize("naissance", ["1955-01-02", "1955-12-31", "1956-01-01", "19500101", "", "1950-02-30"])
def test_anniversaire_durant_annee_hors_profil_et_dates_invalides(naissance):
    with pytest.raises(ValueError):
        valider_maintien_domicile_quebec_2025(profil(naissance=naissance))


def test_70_ans_des_le_premier_janvier():
    assert valider_maintien_domicile_quebec_2025(profil(naissance="1955-01-01"))


@pytest.mark.parametrize("v", [D("NaN"), D("sNaN"), D("Infinity"), D("-1"), D("1.001"), D("1e999"), 1, True, "1"])
def test_montants_invalides(v):
    with pytest.raises(ValueError):
        calculer_maintien_domicile_quebec_2025(profil(), revenu_net_275=v)
    with pytest.raises(ValueError):
        valider_maintien_domicile_quebec_2025(profil(loyers_mensuels=(v,)*12))


@pytest.mark.parametrize("loyers", [(), (D(1000),)*11, (D(1000),)*13, (D(0),)*12, [D(1000)]*12])
def test_annee_complete_loyers_positifs(loyers):
    with pytest.raises(ValueError):
        valider_maintien_domicile_quebec_2025(profil(loyers_mensuels=loyers))


@pytest.mark.parametrize("v", [1, True, "NaN", "1.001", "x", "9"*41])
def test_json_loyers_malformes(v):
    d = maintien_domicile_vers_dict(profil())
    d["loyers_mensuels"][0] = v
    with pytest.raises(ValueError):
        maintien_domicile_depuis_dict(d)


def test_json_inactif_et_derives_refuses():
    assert maintien_domicile_depuis_dict(maintien_domicile_vers_dict(profil())) == profil()
    assert maintien_domicile_depuis_dict(None) == MaintienDomicileQuebec2025()
    with pytest.raises(ValueError):
        maintien_domicile_depuis_dict({**maintien_domicile_vers_dict(profil()), "credit": "234"})
    with pytest.raises(ValueError):
        valider_maintien_domicile_quebec_2025(profil(activer=False))
    assert calculer_maintien_domicile_quebec_2025(MaintienDomicileQuebec2025(), revenu_net_275=D(0)).credit_ligne_458 == 0
