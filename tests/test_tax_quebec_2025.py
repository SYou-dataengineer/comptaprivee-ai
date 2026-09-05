from dataclasses import replace
from decimal import Decimal

import pytest

from src.comptaprivee.tax_engine_input_2025 import (
    BaseFiscaleEmploi2025,
)
from src.comptaprivee.tax_income_2025 import (
    calculer_revenu_net_imposable_2025,
)
from src.comptaprivee.tax_quebec_2025 import (
    QUEBEC_BASIC_CREDIT_RATE_2025,
    calculer_impot_quebec_preliminaire_2025,
)


def _base(
    revenu="52000",
    rrq_ba="3104.00",
    rrq_bb="0",
    ae="681.20",
    gains_ae="52000",
    gains_rrq="52000",
    rqap="256.88",
    gains_rqap="52000",
):
    return BaseFiscaleEmploi2025(
        client="Client Test",
        annee_fiscale=2025,
        province="Québec",
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
        nombre_t4=1,
        nombre_rl1=1,
        avertissements=(),
    )


def _revenu(base=None):
    return calculer_revenu_net_imposable_2025(
        base or _base()
    )


def _calc(base=None):
    return calculer_impot_quebec_preliminaire_2025(
        _revenu(base)
    )


def test_taux_credit_personnel_2025():
    assert QUEBEC_BASIC_CREDIT_RATE_2025 == Decimal("0.14")


def test_revenu_imposable_52000():
    assert _calc().revenu_imposable == Decimal("50095.00")


def test_impot_brut_52000():
    assert _calc().impot_brut == Decimal("7013.30")


def test_montant_personnel_base_2025():
    assert _calc().montant_personnel_base == Decimal("18571")


def test_credit_personnel_base_2025():
    assert _calc().credit_personnel_base == Decimal("2599.94")


def test_impot_quebec_preliminaire_52000():
    assert (
        _calc().impot_quebec_preliminaire
        == Decimal("4413.36")
    )


def test_impot_quebec_ne_devient_pas_negatif():
    base = _base(
        revenu="3000",
        rrq_ba="0",
        rrq_bb="0",
        ae="39.30",
        gains_ae="3000",
        gains_rrq="3000",
        rqap="14.82",
        gains_rqap="3000",
    )
    assert _calc(base).impot_quebec_preliminaire == Decimal("0")


def test_deuxieme_tranche_quebec():
    base = _base(
        revenu="60000",
        rrq_ba="3616.00",
        rrq_bb="0",
        ae="786.00",
        gains_ae="60000",
        gains_rrq="60000",
        rqap="296.40",
        gains_rqap="60000",
    )
    r = _calc(base)
    assert r.revenu_imposable > Decimal("53255")
    assert r.impot_brut > Decimal("7455.70")


def test_refuse_annee_non_2025():
    revenu = replace(
        _revenu(),
        annee_fiscale=2024,
    )
    with pytest.raises(ValueError):
        calculer_impot_quebec_preliminaire_2025(revenu)


def test_refuse_province_non_quebec():
    revenu = replace(
        _revenu(),
        province="Ontario",
    )
    with pytest.raises(ValueError):
        calculer_impot_quebec_preliminaire_2025(revenu)


def test_conserve_identite_client():
    r = _calc()
    assert r.client == "Client Test"
    assert r.annee_fiscale == 2025
    assert r.province == "Québec"


def test_limitations_documentees():
    r = _calc()
    assert len(r.limitations) == 8


def test_limitation_rrq_rqap_ae_pas_double_credit():
    r = _calc()
    assert "RRQ, RQAP et AE" in r.limitations[2]


def test_limitation_cnesst_saaq():
    r = _calc()
    assert "CNESST/SAAQ" in r.limitations[5]


def test_credit_personnel_est_exactement_14_pourcent_bpa():
    r = _calc()
    assert (
        r.credit_personnel_base
        == (Decimal("18571") * Decimal("0.14"))
    )
