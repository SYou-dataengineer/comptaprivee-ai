from decimal import Decimal

from src.comptaprivee.tax_calculation_trace_2025 import (
    construire_trace_calcul_fiscal_2025,
    formater_trace_calcul_fiscal_2025,
)
from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_age_pension_integration_2025 import (
    _profil_age_federal,
)


def _trace():
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        credits_federaux_age_pension=_profil_age_federal(),
    )
    return construire_trace_calcul_fiscal_2025(estimation)


def test_trace_ajoute_ligne_age_pension_federal():
    trace = _trace()
    ligne = next(
        x
        for x in trace.lignes
        if x.libelle == "Crédit fédéral — âge / pension"
    )

    assert ligne.section == "FÉDÉRAL"
    assert ligne.montant == Decimal("1178.71")
    assert "ligne 30100" in ligne.source
    assert "Date de naissance validée" in ligne.source


def test_trace_formule_explique_montant_age():
    ligne = next(
        x
        for x in _trace().lignes
        if x.libelle == "Crédit fédéral — âge / pension"
    )

    assert "8\xa0129,05 $" in ligne.formule
    assert "0,00 $" in ligne.formule
    assert "14,5 %" in ligne.formule
    assert "ligne 30100" in ligne.formule


def test_trace_impot_federal_final_mentionne_credit_age():
    trace = _trace()
    ligne = next(
        x
        for x in trace.lignes
        if x.libelle == "Impôt fédéral de base"
    )

    assert "crédit âge/pension lignes 30100/31400" in ligne.formule
    assert ligne.montant == Decimal("3223.19")


def test_trace_numerotation_continue():
    trace = _trace()
    assert [x.ordre for x in trace.lignes] == list(
        range(1, len(trace.lignes) + 1)
    )


def test_trace_sans_age_pension_garde_structure_historique():
    estimation = calculer_estimation_fiscale_2025(_dossier_52000())
    trace = construire_trace_calcul_fiscal_2025(estimation)

    assert not any(
        x.libelle == "Crédit fédéral — âge / pension"
        for x in trace.lignes
    )


def test_trace_formatee_affiche_age_pension_federal():
    texte = formater_trace_calcul_fiscal_2025(_trace())

    assert "Crédit fédéral — âge / pension" in texte
    assert "ARC ligne 30100" in texte
    assert "1\xa0178,71 $" in texte
    assert "Date de naissance validée" in texte
