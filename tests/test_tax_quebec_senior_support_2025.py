from dataclasses import replace
from decimal import Decimal as D
import pytest
from src.comptaprivee.tax_quebec_senior_support_2025 import (
    CONFIRMATIONS_6J, SoutienAinesQuebec2025, valider_soutien_aines_quebec_2025,
    calculer_soutien_aines_quebec_2025, soutien_aines_vers_dict, soutien_aines_depuis_dict,
)


def profil(**kw):
    return replace(SoutienAinesQuebec2025(activer=True, naissance="1955-12-31", source="Faits fictifs vérifiés",
        **{nom: True for nom in CONFIRMATIONS_6J}), **kw)


@pytest.mark.parametrize("revenu,credit", [("0", "2000"), ("27834.99", "2000"), ("27835", "2000"),
    ("27835.01", "2000"), ("30000", "1883.09"), ("64872", "0"), ("64872.99", "0"),
    ("64873", "0"), ("64873.01", "0"), ("999999999.99", "0")])
def test_bareme_2025(revenu, credit):
    assert calculer_soutien_aines_quebec_2025(profil(), revenu_net_275=D(revenu)).credit_ligne_463 == D(credit)


@pytest.mark.parametrize("revenu,exacte,cent", [("27835.09", "0.00486", "0"),
    ("27835.10", "0.0054", "0.01"), ("27837.50", "0.135", "0.14")])
def test_precision_et_convention_monetaire_generale(revenu, exacte, cent):
    r = calculer_soutien_aines_quebec_2025(profil(), revenu_net_275=D(revenu))
    assert r.reduction_exacte == D(exacte)
    assert r.reduction_au_cent == D(cent)
    assert r.credit_ligne_463 == D(2000)-D(cent)


@pytest.mark.parametrize("champ", CONFIRMATIONS_6J)
@pytest.mark.parametrize("valeur", [False, 1, "oui"])
def test_confirmations_strictes(champ, valeur):
    with pytest.raises(ValueError):
        valider_soutien_aines_quebec_2025(profil(**{champ: valeur}))


@pytest.mark.parametrize("naissance", ["1956-01-01", "2000-01-01", "19551231", "1955-02-30", "", "1955-1-1"])
def test_age_70_et_iso(naissance):
    with pytest.raises(ValueError):
        valider_soutien_aines_quebec_2025(profil(naissance=naissance))


@pytest.mark.parametrize("v", [D("NaN"), D("sNaN"), D("Infinity"), D("-1"), D("1.001"), D("1e999"), 1, True, "1"])
def test_revenu_invalide(v):
    with pytest.raises(ValueError):
        calculer_soutien_aines_quebec_2025(profil(), revenu_net_275=v)


def test_json_inactif_et_rejet_champs_derives():
    assert soutien_aines_depuis_dict(soutien_aines_vers_dict(profil())) == profil()
    assert soutien_aines_depuis_dict(None) == SoutienAinesQuebec2025()
    with pytest.raises(ValueError):
        soutien_aines_depuis_dict({**soutien_aines_vers_dict(profil()), "credit": "2000"})
    with pytest.raises(ValueError):
        valider_soutien_aines_quebec_2025(profil(activer=False))
    assert calculer_soutien_aines_quebec_2025(SoutienAinesQuebec2025(), revenu_net_275=D(0)).credit_ligne_463 == 0
