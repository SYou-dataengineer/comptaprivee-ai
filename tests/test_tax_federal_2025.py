from dataclasses import replace
from decimal import Decimal

import pytest

from src.comptaprivee.tax_engine_input_2025 import BaseFiscaleEmploi2025
from src.comptaprivee.tax_federal_2025 import (
    FEDERAL_CREDIT_RATE_2025,
    calculer_impot_federal_preliminaire_2025,
)
from src.comptaprivee.tax_income_2025 import calculer_revenu_net_imposable_2025


def _base(revenu="52000", rrq_ba="3104.00", rrq_bb="0",
          ae="681.20", gains_ae="52000", gains_rrq="52000",
          rqap="256.88", gains_rqap="52000"):
    return BaseFiscaleEmploi2025(
        client="Client Test", annee_fiscale=2025, province="Québec",
        revenu_emploi_federal=Decimal(revenu),
        revenu_emploi_quebec=Decimal(revenu),
        impot_federal_retenu=Decimal("7500"),
        impot_quebec_retenu=Decimal("6200"),
        rrq_base_premiere_supplementaire=Decimal(rrq_ba),
        rrq_deuxieme_supplementaire=Decimal(rrq_bb),
        assurance_emploi=Decimal(ae),
        gains_assurables_ae=Decimal(gains_ae),
        gains_admissibles_rrq=Decimal(gains_rrq),
        rqap=Decimal(rqap),
        gains_assurables_rqap=Decimal(gains_rqap),
        nombre_t4=1, nombre_rl1=1, avertissements=(),
    )


def _calc(base=None):
    base = base or _base()
    revenu = calculer_revenu_net_imposable_2025(base)
    return calculer_impot_federal_preliminaire_2025(base, revenu)


def test_taux_credit_2025():
    assert FEDERAL_CREDIT_RATE_2025 == Decimal("0.145")


def test_impot_brut_52000():
    r = _calc()
    assert r.revenu_imposable == Decimal("51515.00")
    assert r.impot_brut == Decimal("7469.68")


def test_bpa_52000():
    assert _calc().montant_personnel_base == Decimal("16129")


def test_rrq_base_52000():
    assert _calc().cotisation_base_rrq == Decimal("2619.00")


def test_ae_52000():
    assert _calc().assurance_emploi_admissible == Decimal("681.20")


def test_rqap_52000():
    assert _calc().rqap_admissible == Decimal("256.88")


def test_montant_emploi_52000():
    assert _calc().montant_canadien_emploi == Decimal("1471")


def test_base_credits_52000():
    assert _calc().base_credits_non_remboursables == Decimal("21157.08")


def test_credits_52000():
    assert _calc().credits_non_remboursables == Decimal("3067.78")


def test_impot_federal_base_52000():
    assert _calc().impot_federal_de_base == Decimal("4401.90")


def test_top_up_zero_profil_simple():
    assert _calc().top_up_credit == Decimal("0")


def test_ae_rqap_non_admissibles_sous_2000():
    base = _base(
        revenu="1900", rrq_ba="0", rrq_bb="0",
        ae="24.89", gains_ae="1900", gains_rrq="1900",
        rqap="9.39", gains_rqap="1900",
    )
    revenu = calculer_revenu_net_imposable_2025(base)
    r = calculer_impot_federal_preliminaire_2025(base, revenu)
    assert r.assurance_emploi_admissible == Decimal("0")
    assert r.rqap_admissible == Decimal("0")


def test_impot_jamais_negatif():
    base = _base(
        revenu="3000", rrq_ba="0", rrq_bb="0",
        ae="39.30", gains_ae="3000", gains_rrq="3000",
        rqap="14.82", gains_rqap="3000",
    )
    assert _calc(base).impot_federal_de_base == Decimal("0")


def test_refuse_client_incoherent():
    base = _base()
    revenu = calculer_revenu_net_imposable_2025(base)
    revenu = replace(revenu, client="Autre Client")
    with pytest.raises(ValueError):
        calculer_impot_federal_preliminaire_2025(base, revenu)


def test_limitations_documentees():
    r = _calc()
    assert len(r.limitations) == 7
    assert "Abattement Québec" in r.limitations[5]
