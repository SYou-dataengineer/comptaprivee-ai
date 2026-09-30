from dataclasses import replace
from decimal import Decimal as D
import pytest
from src.comptaprivee.tax_quebec_volunteers_2025 import (
    CONFIRMATIONS_390, VolontairesQuebec2025, valider_volontaires_quebec_2025,
    calculer_volontaires_quebec_2025, volontaires_vers_dict, volontaires_depuis_dict,
)
from tests.test_tax_volunteers_2025 import profil as federal, activite, dossier as avec87
from tests.test_tax_estimation_2025 import _dossier_52000


def profil(**kw):
    return replace(VolontairesQuebec2025(activer=True, source="Certificats Québec fictifs",
        **{nom: True for nom in CONFIRMATIONS_390}), **kw)


def calcul(p=None, b=None, dossier=None, disponible=D(1000)):
    return calculer_volontaires_quebec_2025(p if p is not None else profil(),
        benevoles=b if b is not None else federal(), dossier=dossier or _dossier_52000(), impot_disponible=disponible)


@pytest.mark.parametrize("choix", ["pompiers", "sauvetage"])
@pytest.mark.parametrize("heures", ["200", "200.01", "300"])
def test_credit_2025_une_fois(choix, heures):
    r = calcul(b=federal(choix=choix, activites=(activite(nature=choix, heures=D(heures)),)))
    assert r.credit_ligne_390 == D("756.56")
    assert r.reduction_impot_effective == D("756.56")
    assert r.heures_admissibles == D(heures)


@pytest.mark.parametrize("disponible,utilise", [("0", "0"), ("1.01", "1.01"), ("756.55", "756.55"), ("756.56", "756.56")])
def test_non_remboursable(disponible, utilise):
    r = calcul(disponible=D(disponible))
    assert r.credit_ligne_390 == D("756.56")
    assert r.reduction_impot_effective == D(utilise)


@pytest.mark.parametrize("champ", CONFIRMATIONS_390)
@pytest.mark.parametrize("valeur", [False, 1, "oui"])
def test_confirmations_quebec_distinctes(champ, valeur):
    with pytest.raises(ValueError):
        calcul(profil(**{champ: valeur}))


@pytest.mark.parametrize("heures", ["0", "199.99"])
def test_heures_insuffisantes_refusees(heures):
    with pytest.raises(ValueError):
        calcul(b=federal(activites=(activite(heures=D(heures)),)))


def test_mixte_et_services_remuneres_refuses():
    with pytest.raises(ValueError, match="seule nature"):
        calcul(b=federal(activites=(activite(), activite(nature="sauvetage", organisme="Autre"))))
    with pytest.raises(ValueError):
        calcul(b=federal(activites=(activite(services_similaires_remuneres=True),)))
    with pytest.raises(ValueError, match="rémunération"):
        calcul(dossier=avec87())
    d = _dossier_52000()
    d = replace(d, donnees_validees=d.donnees_validees + (replace(d.donnees_validees[0], type_document="RL-1", case="L-2", valeur_validee=D(1)),))
    with pytest.raises(ValueError, match="L-2"):
        calcul(dossier=d)


def test_ancien_json_et_choix_manquant():
    from src.comptaprivee.tax_volunteers_2025 import Benevoles2025
    assert volontaires_depuis_dict(volontaires_vers_dict(profil())) == profil()
    assert volontaires_depuis_dict(None) == VolontairesQuebec2025()
    with pytest.raises(ValueError):
        volontaires_depuis_dict({**volontaires_vers_dict(profil()), "credit": "756.56"})
    with pytest.raises(ValueError):
        valider_volontaires_quebec_2025(profil(activer=False))
    with pytest.raises(ValueError, match="5L"):
        calcul(b=Benevoles2025())
    assert calcul(VolontairesQuebec2025()).credit_ligne_390 == 0
