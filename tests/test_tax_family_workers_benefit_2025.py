from dataclasses import replace
from decimal import Decimal as D
import pytest

from src.comptaprivee.tax_family_workers_benefit_2025 import (
    FamilleAllocation2025, CONFIRMATIONS_FAMILLE_ACT, valider_famille_act_2025,
    famille_act_depuis_dict, famille_act_vers_dict,
)
from src.comptaprivee.tax_workers_benefit_2025 import calculer_allocation_travailleurs_2025, valider_allocation_travailleurs_2025
from tests.test_tax_workers_benefit_2025 import profil as individuel


def famille(**kw):
    valeurs = dict(activer=True, conjoint_nom="Conjoint fictif", conjoint_resident=True,
        conjoint_revenu_travail=D(8000), conjoint_revenu_net=D(8000),
        source="Déclarations et choix synthétiques", **{n: True for n in CONFIRMATIONS_FAMILLE_ACT})
    valeurs.update(kw)
    return FamilleAllocation2025(**valeurs)


def sans_conjoint(**kw):
    return famille(conjoint_nom="", conjoint_resident=False, conjoint_revenu_travail=D(0), conjoint_revenu_net=D(0), **kw)


def enfant():
    return dict(enfant_nom="Enfant fictif", enfant_naissance="2015-05-02", enfant_admissible_confirme=True)


def profil(f=None, **kw):
    return individuel(famille=f or famille(), sans_conjoint_ni_personne_charge=False, **kw)


def calcul(p=None, travail="12000", net="12000"):
    return calculer_allocation_travailleurs_2025(p or profil(), revenu_travail=D(travail), revenu_net=D(net))


@pytest.mark.parametrize("f,travail,net,attendu", [
    (famille(), "12000", "12000", "5943.38"),
    (famille(**enfant()), "12000", "12000", "3808.23"),
    (sans_conjoint(**enfant()), "15000", "15000", "1912.31"),
    (sans_conjoint(), "15000", "15000", "3646.07"),
])
def test_quatre_baremes_annexe6(f, travail, net, attendu):
    r = calcul(profil(f), travail, net)
    assert r.ligne_45300 == D(attendu)
    assert r.base == r.famille.base


@pytest.mark.parametrize("travail,net,travail_c,net_c,exemption", [
    ("10000", "2000", "20000", "30000", "2000"),
    ("20000", "30000", "10000", "2000", "2000"),
    ("30000", "40000", "20000", "30000", "16386"),
    ("10000", "30000", "10000", "2000", "2000"),
    ("10000", "2000", "10000", "30000", "10000"),
    ("10000", "30000", "20000", "-100", "10000"),
    ("0", "0", "20000", "20000", "0"),
])
def test_second_revenu_meme_membre_et_egalite(travail, net, travail_c, net_c, exemption):
    r = calcul(profil(famille(conjoint_revenu_travail=D(travail_c), conjoint_revenu_net=D(net_c))), travail, net).famille
    assert r.exemption_second_revenu == D(exemption)
    assert r.net_familial == max(D(net), D(0)) + max(D(net_c), D(0)) - D(exemption)


@pytest.mark.parametrize("conjoint_ciph,attendu", [(False, "651.31"), (True, "751.31")])
def test_supplement_double_ciph(conjoint_ciph, attendu):
    f = famille(conjoint_revenu_travail=D(10000), conjoint_revenu_net=D("52504.09"), conjoint_ciph=conjoint_ciph)
    r = calcul(profil(f, reclamer_supplement=True, admissibilite_ciph_confirmee=True), "10000", "10000")
    assert r.supplement == D(attendu)


def test_supplement_travail_personnel_pas_celui_du_conjoint():
    r = calcul(profil(reclamer_supplement=True, admissibilite_ciph_confirmee=True), "1200", "1200")
    assert r.base > 0 and r.supplement == 0


@pytest.mark.parametrize("kw", [{"conjoint_resident": False}, {"conjoint_etudiant": True, "conjoint_etudiant_sans_dependant_confirme": True}, {"conjoint_detenu": True}, {"conjoint_exempt": True}])
def test_conjoint_non_admissible_exclu_des_revenus_mais_rc210_attribue(kw):
    f = famille(conjoint_revenu_net=D(100000), conjoint_avances_base=D(500), **kw)
    r = calcul(profil(f, avances_rc210_case10=D(100)), "15000", "15000")
    assert not f.conjoint_admissible
    assert r.famille.travail_familial == D(15000)
    assert r.famille.net_familial == D(15000)
    assert r.ligne_45300 == D("3646.07") and r.ligne_41500 == D(600)


def test_attribution_rc210_base_au_conjoint_supplement_personnel():
    f = famille(conjoint_reclame_base=True, conjoint_avances_base=D(500))
    p = profil(f, reclamer_base=False, reclamer_supplement=True, admissibilite_ciph_confirmee=True,
               avances_rc210_case10=D(1000), avances_rc210_case11=D(200))
    r = calcul(p)
    assert r.ligne_45300 == D("851.31") and r.ligne_41500 == D(200)
    assert r.famille.avances_base_retenues == 0


def test_avances_si_aucune_base_demandee_choix_et_plafond():
    p = profil(famille(avances_base_attribuees_demandeur=True, conjoint_avances_base=D(500)),
        reclamer_base=False, reclamer_supplement=True, admissibilite_ciph_confirmee=True,
        avances_rc210_case10=D(1000), avances_rc210_case11=D(200))
    assert calcul(p).ligne_41500 == D("851.31")
    assert calcul(replace(p, reclamer_supplement=False)).ligne_41500 == 0
    # Sans conjoint, les avances de base personnelles restent incluses à l'étape 4.
    p = replace(p, famille=sans_conjoint(**enfant()))
    assert calcul(p).ligne_41500 == D("851.31")


def test_moins_19_ans_et_exception_etudiante_parent():
    assert calcul(profil(age_fin_2025=18)).ligne_45300 > 0
    p = profil(sans_conjoint(**enfant()), age_fin_2025=18, pas_etudiant_temps_plein_plus_13_semaines=False)
    assert calcul(p).ligne_45300 > 0
    with pytest.raises(ValueError, match="19 ans"):
        calcul(profil(sans_conjoint(), age_fin_2025=18))


@pytest.mark.parametrize("champ", ["conjoint_revenu_travail", "conjoint_revenu_net", "conjoint_avances_base"])
@pytest.mark.parametrize("valeur", [D("NaN"), D("Infinity"), D("sNaN"), D(".001"), D("1e100"), True, 2.5, "10", None])
def test_montants_stricts(champ, valeur):
    with pytest.raises(ValueError):
        valider_famille_act_2025(famille(**{champ: valeur}))


@pytest.mark.parametrize("nom", list(CONFIRMATIONS_FAMILLE_ACT))
@pytest.mark.parametrize("valeur", [False, "true", 1])
def test_confirmations(nom, valeur):
    with pytest.raises(ValueError):
        valider_famille_act_2025(famille(**{nom: valeur}))


@pytest.mark.parametrize("kw", [
    {"activer": False}, {"conjoint_nom": ""}, {"conjoint_nom": None},
    {"source": ""}, {"conjoint_resident": "true"}, {"conjoint_revenu_travail": D(-1)},
    {"conjoint_avances_base": D(-1)}, {"enfant_naissance": "2010-01-01"},
    {"conjoint_reclame_base": True, "avances_base_attribuees_demandeur": True},
    {"conjoint_reclame_base": True, "conjoint_resident": False},
    {"conjoint_etudiant": True}, {"conjoint_etudiant_sans_dependant_confirme": True},
])
def test_contradictions(kw):
    with pytest.raises(ValueError):
        valider_famille_act_2025(famille(**kw))


@pytest.mark.parametrize("naissance", ["2006-12-31", "2026-01-01", "2015-5-2", "2015-02-30"])
def test_enfant_age_date(naissance):
    with pytest.raises(ValueError):
        valider_famille_act_2025(famille(**{**enfant(), "enfant_naissance": naissance}))


def test_refus_double_demande_et_confirmation_individuelle():
    with pytest.raises(ValueError, match="Deux demandes"):
        calcul(profil(famille(conjoint_reclame_base=True)))
    with pytest.raises(ValueError, match="individuelle"):
        calcul(replace(profil(), sans_conjoint_ni_personne_charge=True))


def test_json_rond_retour_et_vide():
    f = famille(conjoint_revenu_net=D(-100))
    brut = famille_act_vers_dict(f)
    assert brut["conjoint_revenu_net"] == "-100.00"
    assert famille_act_depuis_dict(brut) == f
    assert famille_act_depuis_dict(None) == FamilleAllocation2025()
    with pytest.raises(ValueError):
        famille_act_depuis_dict({**brut, "montant_calcule": "100"})


@pytest.mark.parametrize("valeur", [True, 10.5, None, "NaN", "invalid", ".001"])
def test_json_invalide(valeur):
    brut = famille_act_vers_dict(famille())
    brut["conjoint_revenu_net"] = valeur
    with pytest.raises(ValueError):
        famille_act_depuis_dict(brut)
