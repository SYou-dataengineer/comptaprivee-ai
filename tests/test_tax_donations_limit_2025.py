"""Annexe 9 (25), lignes 6 à 10 : dons monétaires ordinaires sans report."""
from dataclasses import replace
from decimal import Decimal as D
import pytest
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calcul
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_donations_integration_2025 import _dons_1000


def don(montant):
    return replace(_dons_1000(), montant_admissible_federal=D(montant), montant_admissible_quebec=D(0))


def test_plafond_75_pourcent_revenu_net_et_depassement():
    d = _dossier_52000()
    assert calcul(d).revenu.revenu_net_federal == D(51515)
    e = calcul(d, dons_bienfaisance=don("38636.25"))
    assert e.dons_bienfaisance.montant_admissible_federal == D("38636.25")
    for montant in ("38636.26", "40000"):
        with pytest.raises(ValueError, match="75 %"):
            calcul(d, dons_bienfaisance=don(montant))


def test_plafond_utilise_revenu_net_apres_reer():
    from tests.test_tax_donations_integration_2025 import _reer_5000
    d = _dossier_52000()
    assert calcul(d, ajustement_reer=_reer_5000()).revenu.revenu_net_federal == D(46515)
    with pytest.raises(ValueError, match="75 %"):
        calcul(d, ajustement_reer=_reer_5000(), dons_bienfaisance=don("35000"))
    assert calcul(d, ajustement_reer=_reer_5000(), dons_bienfaisance=don("34886.25"))


def test_plafond_federal_non_transpose_au_quebec():
    p = replace(_dons_1000(), montant_admissible_federal=D(0), montant_admissible_quebec=D(40000))
    e = calcul(_dossier_52000(), dons_bienfaisance=p)
    assert e.dons_bienfaisance.montant_admissible_quebec == D(40000)
