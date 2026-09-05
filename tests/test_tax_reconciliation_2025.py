from dataclasses import replace
from decimal import Decimal

import pytest

from src.comptaprivee.tax_engine_input_2025 import BaseFiscaleEmploi2025
from src.comptaprivee.tax_federal_2025 import (
    calculer_impot_federal_preliminaire_2025,
)
from src.comptaprivee.tax_income_2025 import (
    calculer_revenu_net_imposable_2025,
)
from src.comptaprivee.tax_quebec_2025 import (
    calculer_impot_quebec_preliminaire_2025,
)
from src.comptaprivee.tax_reconciliation_2025 import (
    calculer_rapprochement_fiscal_2025,
)


def _base(
    retenue_federal="7500",
    retenue_quebec="6200",
):
    return BaseFiscaleEmploi2025(
        client="Client Test",
        annee_fiscale=2025,
        province="Québec",
        revenu_emploi_federal=Decimal("52000"),
        revenu_emploi_quebec=Decimal("52000"),
        impot_federal_retenu=Decimal(retenue_federal),
        impot_quebec_retenu=Decimal(retenue_quebec),
        rrq_base_premiere_supplementaire=Decimal("3104.00"),
        rrq_deuxieme_supplementaire=Decimal("0"),
        assurance_emploi=Decimal("681.20"),
        gains_assurables_ae=Decimal("52000"),
        gains_admissibles_rrq=Decimal("52000"),
        rqap=Decimal("256.88"),
        gains_assurables_rqap=Decimal("52000"),
        nombre_t4=1,
        nombre_rl1=1,
        avertissements=(),
    )


def _modules(base=None):
    base = base or _base()
    revenu = calculer_revenu_net_imposable_2025(base)
    federal = calculer_impot_federal_preliminaire_2025(
        base,
        revenu,
    )
    quebec = calculer_impot_quebec_preliminaire_2025(
        revenu,
    )
    return base, federal, quebec


def _calc(base=None):
    base, federal, quebec = _modules(base)
    return calculer_rapprochement_fiscal_2025(
        base,
        federal,
        quebec,
    )


def test_abattement_quebec_52000():
    r = _calc()
    assert r.abattement_quebec == Decimal("726.31")


def test_federal_apres_abattement_52000():
    r = _calc()
    assert r.impot_federal_apres_abattement == Decimal("3675.59")


def test_impot_quebec_52000():
    r = _calc()
    assert r.impot_quebec_preliminaire == Decimal("4413.36")


def test_impot_total_preliminaire_52000():
    r = _calc()
    assert r.impot_total_preliminaire == Decimal("8088.95")


def test_retenues_totales_52000():
    r = _calc()
    assert r.retenues_totales == Decimal("13700.00")


def test_remboursement_estime_52000():
    r = _calc()
    assert r.remboursement_estime == Decimal("5611.05")
    assert r.solde_estime == Decimal("0")
    assert r.resultat == "Remboursement estimé"


def test_solde_estime_si_retenues_insuffisantes():
    r = _calc(
        _base(
            retenue_federal="1000",
            retenue_quebec="1000",
        )
    )
    assert r.remboursement_estime == Decimal("0")
    assert r.solde_estime == Decimal("6088.95")
    assert r.resultat == "Solde estimé"


def test_equilibre_estime():
    base = _base(
        retenue_federal="3675.59",
        retenue_quebec="4413.36",
    )
    r = _calc(base)
    assert r.remboursement_estime == Decimal("0")
    assert r.solde_estime == Decimal("0")
    assert r.resultat == "Équilibre estimé"


def test_abattement_ne_depasse_pas_impot_federal():
    r = _calc()
    assert r.abattement_quebec < r.impot_federal_de_base
    assert r.impot_federal_apres_abattement >= Decimal("0")


def test_conserve_retenues_separees():
    r = _calc()
    assert r.retenue_federale == Decimal("7500")
    assert r.retenue_quebec == Decimal("6200")


def test_refuse_client_federal_incoherent():
    base, federal, quebec = _modules()
    federal = replace(federal, client="Autre Client")
    with pytest.raises(ValueError):
        calculer_rapprochement_fiscal_2025(
            base,
            federal,
            quebec,
        )


def test_refuse_client_quebec_incoherent():
    base, federal, quebec = _modules()
    quebec = replace(quebec, client="Autre Client")
    with pytest.raises(ValueError):
        calculer_rapprochement_fiscal_2025(
            base,
            federal,
            quebec,
        )


def test_refuse_annee_incoherente():
    base, federal, quebec = _modules()
    federal = replace(federal, annee_fiscale=2024)
    with pytest.raises(ValueError):
        calculer_rapprochement_fiscal_2025(
            base,
            federal,
            quebec,
        )


def test_statut_validation_obligatoire():
    r = _calc()
    assert "validation comptable obligatoire" in r.statut


def test_limitations_documentees():
    r = _calc()
    assert len(r.limitations) == 9
    assert "Aucune transmission" in r.limitations[-1]
