from dataclasses import replace
from decimal import Decimal as D
import pytest

from tests.test_tax_family_workers_benefit_2025 import famille, enfant, profil, calcul
from src.comptaprivee.tax_family_workers_benefit_2025 import famille_act_vers_dict, famille_act_depuis_dict


def enfant_conjoint(nom="Autre enfant fictif"):
    return dict(conjoint_enfant_nom=nom, conjoint_enfant_naissance="2015-05-02",
                conjoint_enfant_admissible_confirme=True)


@pytest.mark.parametrize("etudiant_a", [False, True])
def test_a_recoit_enfant_b_etudiant_exclu(etudiant_a):
    p = profil(famille(**enfant(), demandeur_etudiant=etudiant_a, conjoint_etudiant=True,
        conjoint_etudiant_sans_dependant_confirme=True),
        pas_etudiant_temps_plein_plus_13_semaines=not etudiant_a)
    r = calcul(p)
    assert r.famille.demandeur_admissible
    assert not r.famille.conjoint_admissible
    assert r.famille.travail_familial == D(12000)
    assert r.famille.net_familial == D(12000)
    assert r.famille.exemption_second_revenu == 0
    assert r.ligne_45300 == D("1920.00")
    assert r.ligne_45300 != D("3808.23")


@pytest.mark.parametrize("etudiant_b", [False, True])
def test_b_recoit_enfant_a_etudiant_exclu(etudiant_b):
    p = profil(famille(**enfant_conjoint(), demandeur_etudiant=True,
        conjoint_etudiant=etudiant_b, conjoint_reclame_base=True),
        pas_etudiant_temps_plein_plus_13_semaines=False, reclamer_base=False,
        reclamer_supplement=True, admissibilite_ciph_confirmee=True,
        avances_rc210_case11=D(200))
    r = calcul(p)
    assert not r.famille.demandeur_admissible
    assert r.famille.conjoint_admissible
    assert r.ligne_45300 == r.ligne_41500 == r.supplement == 0
    # Même foyer vu depuis B : un seul étudiant bénéficie de cet enfant.
    inverse = profil(famille(**enfant(), demandeur_etudiant=etudiant_b,
        conjoint_etudiant=True, conjoint_etudiant_sans_dependant_confirme=True,
        conjoint_revenu_travail=D(12000), conjoint_revenu_net=D(12000)),
        pas_etudiant_temps_plein_plus_13_semaines=not etudiant_b)
    assert calcul(inverse, "8000", "8000").ligne_45300 == D(1120)


def test_autre_enfant_distinct_maintient_exception_des_deux_etudiants():
    f = famille(**enfant(), **enfant_conjoint(), demandeur_etudiant=True, conjoint_etudiant=True)
    r = calcul(profil(f, pas_etudiant_temps_plein_plus_13_semaines=False))
    assert r.famille.demandeur_admissible and r.famille.conjoint_admissible
    assert r.ligne_45300 == D("3808.23")
    assert famille_act_depuis_dict(famille_act_vers_dict(f)) == f


def test_aucun_etudiant_inchange():
    assert calcul(profil(famille(**enfant()))).ligne_45300 == D("3808.23")


@pytest.mark.parametrize("nom", ["Enfant fictif", " ENFANT   FICTIF "])
def test_meme_enfant_interdit_aux_deux_parents(nom):
    f = famille(**enfant(), **enfant_conjoint(nom), demandeur_etudiant=True, conjoint_etudiant=True)
    with pytest.raises(ValueError, match="même enfant"):
        calcul(profil(f, pas_etudiant_temps_plein_plus_13_semaines=False))


def test_122_7_5_une_seule_base_meme_avec_deux_enfants():
    f = famille(**enfant(), **enfant_conjoint(), conjoint_reclame_base=True)
    with pytest.raises(ValueError, match="Deux demandes"):
        calcul(profil(f))


@pytest.mark.parametrize("kw", [
    {"conjoint_enfant_admissible_confirme": False},
    {"conjoint_enfant_naissance": "2006-12-31"},
    {"conjoint_enfant_naissance": "2015-02-30"},
    {"conjoint_enfant_nom": ""},
    {"conjoint_enfant_admissible_confirme": 1},
    {"conjoint_etudiant_sans_dependant_confirme": True},
])
def test_attribution_conjoint_stricte(kw):
    f = famille(**enfant_conjoint(), conjoint_etudiant=True)
    with pytest.raises(ValueError):
        calcul(profil(replace(f, **kw)))


def test_ancien_json_sans_nouveaux_champs():
    brut = famille_act_vers_dict(famille(**enfant()))
    for n in ("demandeur_etudiant", *enfant_conjoint()):
        brut.pop(n)
    assert calcul(profil(famille_act_depuis_dict(brut))).ligne_45300 == D("3808.23")


def test_etudes_contradictoires_et_absence_confirmation_reste_refusee():
    with pytest.raises(ValueError, match="contradictoire"):
        calcul(profil(famille(demandeur_etudiant=True)))
    with pytest.raises(ValueError, match="Confirmation obligatoire"):
        calcul(profil(pas_etudiant_temps_plein_plus_13_semaines=False))
