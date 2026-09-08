from decimal import Decimal

from src.comptaprivee.tax_adjustments_2025 import AjustementReer2025
from src.comptaprivee.tax_calculation_trace_2025 import (
    construire_trace_calcul_fiscal_2025,
    formater_trace_calcul_fiscal_2025,
)
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
from src.comptaprivee.tax_union_dues_2025 import CotisationsSyndicalesProfessionnelles2025
from tests.test_tax_estimation_2025 import _dossier_52000


def _cotisations_600():
    return CotisationsSyndicalesProfessionnelles2025(
        montant_federal_admissible=Decimal("600"),
        montant_quebec_admissible=Decimal("600"),
        source_federale="T4 case 44",
        source_quebec="RL-1 case F",
        valide_par_comptable=True,
        sources_dedoublonnees=True,
    )


def _reer_5000():
    return AjustementReer2025(
        deduction_reer=Decimal("5000"),
        plafond_reer_confirme=Decimal("8000"),
        source_plafond_reer="Avis de cotisation / T1028 ARC",
        valide_par_comptable=True,
    )


def _index(trace, libelle):
    return next(i for i, ligne in enumerate(trace.lignes) if ligne.libelle == libelle)


def test_trace_sans_cotisations_reste_a_17_etapes():
    estimation = calculer_estimation_fiscale_2025(_dossier_52000())
    trace = construire_trace_calcul_fiscal_2025(estimation)
    assert len(trace.lignes) == 17


def test_trace_cotisations_ajoute_deux_etapes():
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(), cotisations_syndicales=_cotisations_600()
    )
    trace = construire_trace_calcul_fiscal_2025(estimation)
    assert len(trace.lignes) == 19
    assert [x.ordre for x in trace.lignes] == list(range(1, 20))


def test_trace_deduction_federale_avant_revenu_imposable():
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(), cotisations_syndicales=_cotisations_600()
    )
    trace = construire_trace_calcul_fiscal_2025(estimation)
    i1 = _index(trace, "Cotisations syndicales/professionnelles — fédéral")
    i2 = _index(trace, "Revenu imposable fédéral")
    assert i1 < i2
    assert trace.lignes[i1].montant == Decimal("600.00")


def test_trace_credit_quebec_avant_impot_preliminaire():
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(), cotisations_syndicales=_cotisations_600()
    )
    trace = construire_trace_calcul_fiscal_2025(estimation)
    i1 = _index(trace, "Crédit cotisations syndicales/professionnelles — Québec")
    i2 = _index(trace, "Impôt Québec préliminaire")
    assert i1 < i2
    assert trace.lignes[i1].montant == Decimal("60.00")


def test_trace_reer_et_cotisations_a_20_etapes():
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        ajustement_reer=_reer_5000(),
        cotisations_syndicales=_cotisations_600(),
    )
    trace = construire_trace_calcul_fiscal_2025(estimation)
    assert len(trace.lignes) == 20
    assert [x.ordre for x in trace.lignes] == list(range(1, 21))
    assert trace.lignes[2].libelle == "Déduction REER/RPAC/RVER validée"
    assert trace.lignes[3].libelle == "Cotisations syndicales/professionnelles — fédéral"
    assert trace.lignes[-1].montant == Decimal("7049.07")


def test_trace_formatee_contient_sources_et_lignes():
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(), cotisations_syndicales=_cotisations_600()
    )
    texte = formater_trace_calcul_fiscal_2025(
        construire_trace_calcul_fiscal_2025(estimation)
    )
    assert "T4 case 44" in texte
    assert "RL-1 case F" in texte
    assert "ligne 21200" in texte
    assert "ligne 397.1" in texte
    assert "10 %" in texte
