from decimal import Decimal

import pytest

from src.comptaprivee.tax_engine_input_2025 import BaseFiscaleEmploi2025
from src.comptaprivee.tax_income_2025 import (
    calculer_cotisations_attendues_2025,
    calculer_revenu_net_imposable_2025,
    verifier_profil_emploi_simple_2025,
)


def _base(
    revenu_federal: str = "52000",
    revenu_quebec: str = "52000",
    rrq_ba: str = "3104.00",
    rrq_bb: str = "0",
    ae: str = "681.20",
    gains_ae: str = "52000",
    gains_rrq: str = "52000",
    rqap: str = "256.88",
    gains_rqap: str = "52000",
    nombre_t4: int = 1,
    nombre_rl1: int = 1,
    annee: int = 2025,
    province: str = "Québec",
) -> BaseFiscaleEmploi2025:
    return BaseFiscaleEmploi2025(
        client="Client Test",
        annee_fiscale=annee,
        province=province,
        revenu_emploi_federal=Decimal(revenu_federal),
        revenu_emploi_quebec=Decimal(revenu_quebec),
        impot_federal_retenu=Decimal("7500"),
        impot_quebec_retenu=Decimal("6200"),
        rrq_base_premiere_supplementaire=Decimal(rrq_ba),
        rrq_deuxieme_supplementaire=Decimal(rrq_bb),
        assurance_emploi=Decimal(ae),
        gains_assurables_ae=Decimal(gains_ae),
        gains_admissibles_rrq=Decimal(gains_rrq),
        rqap=Decimal(rqap),
        gains_assurables_rqap=Decimal(gains_rqap),
        nombre_t4=nombre_t4,
        nombre_rl1=nombre_rl1,
        avertissements=(),
    )


def test_cotisations_normales_52000() -> None:
    r = calculer_cotisations_attendues_2025(_base())
    assert r.rrq_ba == Decimal("3104.00")
    assert r.rrq_bb == Decimal("0.00")
    assert r.assurance_emploi == Decimal("681.20")
    assert r.rqap == Decimal("256.88")


def test_premiere_cotisation_supplementaire_52000() -> None:
    r = calculer_cotisations_attendues_2025(_base())
    assert r.rrq_premiere_supplementaire == Decimal("485.00")


def test_revenu_net_federal_52000() -> None:
    r = calculer_revenu_net_imposable_2025(_base())
    assert r.deduction_rrq_amelioree_federale == Decimal("485.00")
    assert r.revenu_net_federal == Decimal("51515.00")


def test_revenu_imposable_federal_egal_net_phase1() -> None:
    r = calculer_revenu_net_imposable_2025(_base())
    assert r.revenu_imposable_federal == r.revenu_net_federal


def test_revenu_net_quebec_52000() -> None:
    r = calculer_revenu_net_imposable_2025(_base())
    assert r.deduction_travailleur_quebec == Decimal("1420.00")
    assert r.deduction_rrq_quebec == Decimal("485.00")
    assert r.revenu_net_quebec == Decimal("50095.00")


def test_revenu_imposable_quebec_egal_net_phase1() -> None:
    r = calculer_revenu_net_imposable_2025(_base())
    assert r.revenu_imposable_quebec == r.revenu_net_quebec


def test_revenus_federal_quebec_restent_separes() -> None:
    r = calculer_revenu_net_imposable_2025(
        _base(revenu_federal="52000", revenu_quebec="52750")
    )
    assert r.revenu_total_federal == Decimal("52000")
    assert r.revenu_total_quebec == Decimal("52750")


def test_cotisations_maximales_a_81200() -> None:
    r = calculer_cotisations_attendues_2025(
        _base(
            revenu_federal="81200", revenu_quebec="81200",
            rrq_ba="4339.20", rrq_bb="396.00",
            ae="860.67", gains_ae="81200", gains_rrq="81200",
            rqap="401.13", gains_rqap="81200",
        )
    )
    assert r.rrq_ba == Decimal("4339.20")
    assert r.rrq_bb == Decimal("396.00")
    assert r.assurance_emploi == Decimal("860.67")
    assert r.rqap == Decimal("401.13")


def test_deduction_rrq_maximale_1074() -> None:
    r = calculer_revenu_net_imposable_2025(
        _base(
            revenu_federal="81200", revenu_quebec="81200",
            rrq_ba="4339.20", rrq_bb="396.00",
            ae="860.67", gains_ae="81200", gains_rrq="81200",
            rqap="401.13", gains_rqap="81200",
        )
    )
    assert r.deduction_rrq_amelioree_federale == Decimal("1074.00")


def test_sous_exemption_rrq() -> None:
    r = calculer_cotisations_attendues_2025(
        _base(
            revenu_federal="3000", revenu_quebec="3000",
            rrq_ba="0", rrq_bb="0",
            ae="39.30", gains_ae="3000", gains_rrq="3000",
            rqap="14.82", gains_rqap="3000",
        )
    )
    assert r.rrq_ba == Decimal("0.00")
    assert r.rrq_premiere_supplementaire == Decimal("0.00")


def test_deduction_travailleur_non_plafonnee() -> None:
    r = calculer_revenu_net_imposable_2025(
        _base(
            revenu_federal="10000", revenu_quebec="10000",
            rrq_ba="416.00", rrq_bb="0",
            ae="131.00", gains_ae="10000", gains_rrq="10000",
            rqap="49.40", gains_rqap="10000",
        )
    )
    assert r.deduction_travailleur_quebec == Decimal("600.00")


def test_refuse_plusieurs_t4() -> None:
    with pytest.raises(ValueError):
        verifier_profil_emploi_simple_2025(_base(nombre_t4=2))


def test_refuse_plusieurs_rl1() -> None:
    with pytest.raises(ValueError):
        verifier_profil_emploi_simple_2025(_base(nombre_rl1=2))


def test_refuse_mauvaise_cotisation_rrq_ba() -> None:
    with pytest.raises(ValueError):
        verifier_profil_emploi_simple_2025(_base(rrq_ba="2500"))


def test_refuse_mauvaise_cotisation_rrq_bb() -> None:
    with pytest.raises(ValueError):
        verifier_profil_emploi_simple_2025(_base(rrq_bb="396"))


def test_refuse_mauvaise_cotisation_ae() -> None:
    with pytest.raises(ValueError):
        verifier_profil_emploi_simple_2025(_base(ae="850"))


def test_refuse_mauvaise_cotisation_rqap() -> None:
    with pytest.raises(ValueError):
        verifier_profil_emploi_simple_2025(_base(rqap="300"))


def test_refuse_annee_non_2025() -> None:
    with pytest.raises(ValueError):
        verifier_profil_emploi_simple_2025(_base(annee=2024))


def test_refuse_province_non_quebec() -> None:
    with pytest.raises(ValueError):
        verifier_profil_emploi_simple_2025(_base(province="Ontario"))


def test_profil_documente_ses_limites() -> None:
    r = calculer_revenu_net_imposable_2025(_base())
    assert r.profil == "Emploi Québec simple 2025"
    assert len(r.limitations) == 6
