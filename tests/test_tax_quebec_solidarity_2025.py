"""Base 6H uniquement : aucun montant de crédit supposé ou test de barème."""

from dataclasses import replace
from datetime import date
from decimal import Decimal as D
import json

import pytest

from src.comptaprivee.tax_quebec_solidarity_2025 import (
    CONFIRMATIONS_6H, SolidariteQuebec2025, preparer_solidarite_quebec_2025,
    solidarite_quebec_depuis_dict, solidarite_quebec_vers_dict,
    valider_solidarite_quebec_2025,
)


def profil(**changements):
    return replace(SolidariteQuebec2025(
        activer=True, naissance="1980-01-01", source="Pièces fictives vérifiées",
        **{nom: True for nom in CONFIRMATIONS_6H}), **changements)


@pytest.mark.parametrize("seul", [True, False])
def test_periode_de_versement_distincte_de_lannee_fiscale(seul):
    base = preparer_solidarite_quebec_2025(profil(vit_seul_toute_annee=seul), revenu_net_quebec=D("50095.00"))
    assert base.annee_reference == 2025
    assert base.debut_periode == date(2026, 7, 1)
    assert base.fin_periode == date(2027, 6, 30)
    assert base.revenu_familial == D("50095.00")
    assert base.additionnel_vie_seule_a_etudier is seul


def test_age_18_ans_au_31_decembre_2025():
    assert valider_solidarite_quebec_2025(profil(naissance="2007-12-31"))
    with pytest.raises(ValueError, match="18 ans"):
        valider_solidarite_quebec_2025(profil(naissance="2008-01-01"))


@pytest.mark.parametrize("naissance", ["20070101", "2007-02-30", "", "2025-1-1", 2007])
def test_dates_invalides(naissance):
    with pytest.raises(ValueError):
        valider_solidarite_quebec_2025(profil(naissance=naissance))


@pytest.mark.parametrize("champ", CONFIRMATIONS_6H)
@pytest.mark.parametrize("valeur", [False, "oui", 1])
def test_confirmation_manquante_ou_mauvais_type(champ, valeur):
    with pytest.raises(ValueError):
        valider_solidarite_quebec_2025(profil(**{champ: valeur}))


@pytest.mark.parametrize("revenu", [D("NaN"), D("sNaN"), D("Infinity"), D("1E9999"),
    D("-1"), D("0.001"), D("1000000000"), 0, True, 123.45, "1000"])
def test_revenu_non_decimal_ou_hors_limites(revenu):
    with pytest.raises(ValueError, match="275"):
        preparer_solidarite_quebec_2025(profil(), revenu_net_quebec=revenu)


@pytest.mark.parametrize("revenu", [D(0), D("0.01"), D("999999999.99")])
def test_aucun_plafond_de_credit_deduit_du_revenu(revenu):
    assert preparer_solidarite_quebec_2025(profil(), revenu_net_quebec=revenu).revenu_familial == revenu


def test_profil_vide_et_ancien_json():
    vide = SolidariteQuebec2025()
    assert solidarite_quebec_depuis_dict(None) == solidarite_quebec_depuis_dict({}) == vide
    assert preparer_solidarite_quebec_2025(vide, revenu_net_quebec=D(0)) is None


def test_json_ne_contient_que_les_faits():
    p = profil(vit_seul_toute_annee=True)
    brut = json.loads(json.dumps(solidarite_quebec_vers_dict(p)))
    assert solidarite_quebec_depuis_dict(brut) == p
    for champ in ("revenu_familial", "credit", "debut_periode"):
        with pytest.raises(ValueError, match="clés"):
            solidarite_quebec_depuis_dict({**brut, champ: "100"})


@pytest.mark.parametrize("valeur", [[], "", 0, True])
def test_json_non_objet(valeur):
    with pytest.raises(ValueError):
        solidarite_quebec_depuis_dict(valeur)


@pytest.mark.parametrize("changements", [{"activer": 1}, {"vit_seul_toute_annee": "oui"},
    {"source": " "}, {"source": "x\ny"}, {"source": "x" * 2001}])
def test_faits_invalides(changements):
    with pytest.raises(ValueError):
        valider_solidarite_quebec_2025(profil(**changements))


def test_profil_desactive_ne_masque_pas_des_faits():
    with pytest.raises(ValueError, match="Activez"):
        valider_solidarite_quebec_2025(profil(activer=False))


def test_base_utilise_le_revenu_quebec_du_moteur_existant():
    from tests.test_tax_estimation_2025 import _dossier_52000
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025

    d = _dossier_52000()
    estimation = calculer_estimation_fiscale_2025(d)
    base = preparer_solidarite_quebec_2025(profil(), revenu_net_quebec=estimation.revenu.revenu_net_quebec)
    assert base.revenu_familial == D("50095.00")
    assert base.revenu_familial != estimation.revenu.revenu_net_federal
    assert calculer_estimation_fiscale_2025(d) == estimation
