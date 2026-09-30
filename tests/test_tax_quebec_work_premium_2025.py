"""Préparation 6I : aucune règle d'arrondi monétaire présumée."""
from dataclasses import replace
from decimal import Decimal as D

import pytest

from src.comptaprivee.tax_quebec_work_premium_2025 import (
    CONFIRMATIONS_6I, PrimeTravailQuebec2025,
    preparer_prime_travail_quebec_2025, valider_prime_travail_quebec_2025,
)


def profil(**kw):
    return replace(PrimeTravailQuebec2025(activer=True, naissance="1980-01-01",
        source="Justificatifs fictifs", **{nom: True for nom in CONFIRMATIONS_6I}), **kw)


@pytest.mark.parametrize("droit,historique", [(False, False), (True, False), (False, True), (True, True)])
def test_les_deux_voies_adaptees_imposent_comparaison(droit, historique):
    p = profil(droit_376_confirme=droit, prestations_contraintes_2020_2025_confirmees=historique)
    r = preparer_prime_travail_quebec_2025(p, salaire_101=D(20000), avantages_211=D(100), revenu_net_275=D(18000))
    assert r.revenu_travail_ligne_29 == D(19900)
    assert r.revenu_familial_ligne_54 == D(18000)
    assert r.comparer_colonne_adaptee is (droit or historique)


@pytest.mark.parametrize("champ", CONFIRMATIONS_6I)
@pytest.mark.parametrize("valeur", [False, 1, "oui"])
def test_verification_explicite_obligatoire(champ, valeur):
    with pytest.raises(ValueError):
        valider_prime_travail_quebec_2025(profil(**{champ: valeur}))


def test_adulte_fin_2025_et_non_regle_act_19_ans():
    assert valider_prime_travail_quebec_2025(profil(naissance="2007-12-31"))
    with pytest.raises(ValueError, match="18 ans"):
        valider_prime_travail_quebec_2025(profil(naissance="2008-01-01"))


@pytest.mark.parametrize("naissance", ["", "20070101", "2007-02-30", "2007-1-1"])
def test_naissance_invalide(naissance):
    with pytest.raises(ValueError):
        valider_prime_travail_quebec_2025(profil(naissance=naissance))


@pytest.mark.parametrize("v", [D("NaN"), D("sNaN"), D("Infinity"), D("-1"), D("0.001"), D("1E999"), 1, True, "100"])
def test_avances_et_revenus_invalides(v):
    with pytest.raises(ValueError):
        valider_prime_travail_quebec_2025(profil(avances_rl19_a=v))
    for champ in ("salaire_101", "avantages_211", "revenu_net_275"):
        kw = dict(salaire_101=D(20000), avantages_211=D(0), revenu_net_275=D(18000))
        kw[champ] = v
        with pytest.raises(ValueError):
            preparer_prime_travail_quebec_2025(profil(), **kw)


def test_211_superieur_au_salaire_refuse():
    with pytest.raises(ValueError, match="211"):
        preparer_prime_travail_quebec_2025(profil(), salaire_101=D(0), avantages_211=D(1), revenu_net_275=D(0))


def test_desactivation_ne_masque_pas_les_avances():
    with pytest.raises(ValueError, match="Activez"):
        valider_prime_travail_quebec_2025(PrimeTravailQuebec2025(avances_rl19_a=D(500)))
    r = preparer_prime_travail_quebec_2025(profil(avances_rl19_a=D(5000)),
        salaire_101=D(0), avantages_211=D(0), revenu_net_275=D(0))
    assert r.avances_rl19_a == D(5000)


def test_reer_change_275_pas_le_travail_annexe_p():
    from tests.test_tax_workers_benefit_2025 import dossier_20000
    from tests.test_tax_reer_interface_storage_2025 import _reer_5000
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
    bases = []
    for kw in ({}, {"ajustement_reer": _reer_5000()}):
        e = calculer_estimation_fiscale_2025(dossier_20000(), **kw)
        bases.append(preparer_prime_travail_quebec_2025(profil(), salaire_101=e.base.revenu_emploi_quebec,
            avantages_211=D(0), revenu_net_275=e.revenu.revenu_net_quebec))
    assert bases[0].revenu_travail_ligne_29 == bases[1].revenu_travail_ligne_29 == D(20000)
    assert bases[0].revenu_familial_ligne_54 - bases[1].revenu_familial_ligne_54 == D(5000)


from src.comptaprivee.tax_quebec_work_premium_2025 import (
    calculer_prime_travail_quebec_2025 as calcul_prime, prime_travail_depuis_dict,
    prime_travail_vers_dict, ResultatPrimeTravailQuebec2025,
)


def calcul(w, f, adaptee=False, avances="0"):
    return calcul_prime(profil(droit_376_confirme=adaptee, avances_rl19_a=D(avances)),
        salaire_101=D(w), avantages_211=D(0), revenu_net_275=D(f))


@pytest.mark.parametrize("travail,famille,adaptee,attendu", [
    ("2400", "0", False, "0"), ("2400.01", "0", False, "0"),
    ("12619.99", "12620", False, "1185.52"), ("12620", "12620", False, "1185.52"),
    ("12620.01", "12620.01", False, "1185.52"),
    ("20000", "18635", False, "584.02"), ("25000", "24474.99", False, "0.02"),
    ("25000", "24475", False, "0"), ("25000", "24475.01", False, "0"),
    ("1200", "0", True, "0"), ("1200.01", "0", True, "0"),
    ("17797.99", "17798", True, "2257.33"), ("17798", "17798", True, "2257.33"),
    ("17798.01", "17798.01", True, "2257.33"),
    ("45000", "40370.99", True, "0.03"), ("45000", "40371", True, "0"),
    ("45000", "40371.01", True, "0"),
])
def test_bornes_et_comparaison(travail, famille, adaptee, attendu):
    r = calcul(travail, famille, adaptee)
    assert r.credit_ligne_456 == D(attendu)
    if adaptee:
        assert r.credit_ligne_456 == max(r.ordinaire.ligne_84, r.adaptee.ligne_84)


@pytest.mark.parametrize("travail,adaptee,exact,cent", [
    ("2400.12", False, "0.01392", "0.01"), ("2400.13", False, "0.01508", "0.02"),
    ("1200.03", True, "0.00408", "0.00"), ("1200.04", True, "0.00544", "0.01"),
])
def test_fraction_cent_76_convention_moteur_non_regle_rq(travail, adaptee, exact, cent):
    r = calcul(travail, "0", adaptee)
    c = r.adaptee if adaptee else r.ordinaire
    assert c.produit_76_exact == D(exact)
    assert c.ligne_76 == D(cent)


@pytest.mark.parametrize("famille,exact,cent,credit", [
    ("18635.04", "601.504", "601.50", "584.02"),
    ("18635.05", "601.505", "601.51", "584.01"),
    ("18635.06", "601.506", "601.51", "584.01"),
])
def test_fraction_et_demi_cent_83_convention_moteur_non_regle_rq(famille, exact, cent, credit):
    r = calcul("20000", famille)
    assert r.ordinaire.produit_83_exact == D(exact)
    assert r.ordinaire.ligne_83 == D(cent)
    assert r.credit_ligne_456 == D(credit)


def test_avances_integrales_meme_si_credit_nul_et_ancien_json():
    r = calcul("50000", "50000", avances="5000.55")
    assert r.credit_ligne_456 == 0
    assert r.avances_ligne_441 == D("5000.55")
    p = profil(avances_rl19_a=D("5000.55"))
    assert prime_travail_depuis_dict(prime_travail_vers_dict(p)) == p
    assert prime_travail_depuis_dict(None) == PrimeTravailQuebec2025()
    assert calcul_prime(PrimeTravailQuebec2025(), salaire_101=D(0), avantages_211=D(0),
        revenu_net_275=D(0)) == ResultatPrimeTravailQuebec2025()


@pytest.mark.parametrize("valeur", [1, True, "NaN", "1.001", "1e999", "x", "9"*41])
def test_json_avances_malformees(valeur):
    d = prime_travail_vers_dict(profil())
    d["avances_rl19_a"] = valeur
    with pytest.raises(ValueError):
        prime_travail_depuis_dict(d)
