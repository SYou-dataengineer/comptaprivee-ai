from decimal import Decimal

import pytest

from src.comptaprivee.tax_adjustments_2025 import AjustementReer2025
from src.comptaprivee.tax_calculation_trace_2025 import (
    construire_trace_calcul_fiscal_2025,
    formater_trace_calcul_fiscal_2025,
)
from src.comptaprivee.tax_donations_2025 import DonsBienfaisance2025
from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
    formater_estimation_fiscale_2025,
)
from src.comptaprivee.tax_union_dues_2025 import (
    CotisationsSyndicalesProfessionnelles2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000


def _dons_1000():
    return DonsBienfaisance2025(
        montant_admissible_federal=Decimal("1000"),
        montant_admissible_quebec=Decimal("1000"),
        source_federale="Reçu officiel organisme enregistré",
        source_quebec="Reçu officiel organisme enregistré",
        valide_par_comptable=True,
        donataire_reconnu_confirme=True,
        dons_monetaires_2025_uniquement=True,
        aucun_report_anterieur=True,
    )


def _reer_5000():
    return AjustementReer2025(
        deduction_reer=Decimal("5000"),
        plafond_reer_confirme=Decimal("8000"),
        source_plafond_reer="Avis de cotisation / T1028 ARC",
        valide_par_comptable=True,
    )


def _cotisations_600():
    return CotisationsSyndicalesProfessionnelles2025(
        montant_federal_admissible=Decimal("600"),
        montant_quebec_admissible=Decimal("600"),
        source_federale="T4 case 44",
        source_quebec="RL-1 case F",
        valide_par_comptable=True,
        sources_dedoublonnees=True,
    )


def test_sans_dons_resultat_reste_identique():
    e = calculer_estimation_fiscale_2025(_dossier_52000())
    assert e.rapprochement.remboursement_estime == Decimal("5611.05")
    assert e.dons_bienfaisance.montant_admissible_federal == Decimal("0")


def test_don_1000_reduit_impot_federal_de_base():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        dons_bienfaisance=_dons_1000(),
    )
    assert e.federal.impot_federal_de_base == Decimal("4140.90")


def test_don_1000_reduit_impot_quebec():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        dons_bienfaisance=_dons_1000(),
    )
    assert e.quebec.impot_quebec_preliminaire == Decimal("4181.36")


def test_don_1000_recalcule_remboursement():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        dons_bienfaisance=_dons_1000(),
    )
    assert e.rapprochement.impot_total_preliminaire == Decimal("7639.01")
    assert e.rapprochement.remboursement_estime == Decimal("6060.99")


def test_reer_cotisations_et_dons_se_combinent():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        ajustement_reer=_reer_5000(),
        cotisations_syndicales=_cotisations_600(),
        dons_bienfaisance=_dons_1000(),
    )
    assert e.federal.impot_federal_de_base == Decimal("3328.90")
    assert e.quebec.impot_quebec_preliminaire == Decimal("3421.36")
    assert e.rapprochement.impot_total_preliminaire == Decimal("6200.99")
    assert e.rapprochement.remboursement_estime == Decimal("7499.01")


def test_estimation_conserve_les_dons_valides():
    dons = _dons_1000()
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        dons_bienfaisance=dons,
    )
    assert e.dons_bienfaisance == dons


def test_dons_invalides_bloquent_le_calcul():
    dons = DonsBienfaisance2025(
        montant_admissible_federal=Decimal("1000"),
        source_federale="Reçu officiel",
        valide_par_comptable=False,
        donataire_reconnu_confirme=True,
        dons_monetaires_2025_uniquement=True,
        aucun_report_anterieur=True,
    )
    with pytest.raises(ValueError):
        calculer_estimation_fiscale_2025(
            _dossier_52000(),
            dons_bienfaisance=dons,
        )


def test_resume_et_trace_affichent_dons_et_resultat_combine():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        ajustement_reer=_reer_5000(),
        cotisations_syndicales=_cotisations_600(),
        dons_bienfaisance=_dons_1000(),
    )
    resume = formater_estimation_fiscale_2025(e)
    trace = construire_trace_calcul_fiscal_2025(e)
    texte_trace = formater_trace_calcul_fiscal_2025(trace)

    assert "DONS DE BIENFAISANCE VALIDÉS" in resume
    assert "Crédit fédéral — ligne 34900 : 261,00 $" in resume
    assert "Crédit Québec — ligne 395 : 232,00 $" in resume
    assert "7\u00a0499,01 $" in resume

    assert len(trace.lignes) == 22
    assert [x.ordre for x in trace.lignes] == list(range(1, 23))
    assert "Crédit fédéral pour dons" in texte_trace
    assert "Crédit Québec pour dons" in texte_trace
    assert "7\u00a0499,01 $" in texte_trace
