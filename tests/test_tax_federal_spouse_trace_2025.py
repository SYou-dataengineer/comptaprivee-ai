from decimal import Decimal

from src.comptaprivee.tax_calculation_trace_2025 import (
    construire_trace_calcul_fiscal_2025,
    formater_trace_calcul_fiscal_2025,
)
from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_spouse_integration_2025 import (
    _profil_conjoint,
)


def _trace():
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        montant_conjoint_federal=_profil_conjoint(),
    )
    return construire_trace_calcul_fiscal_2025(estimation)


def test_trace_ajoute_ligne_conjoint_federal():
    trace = _trace()
    ligne = next(
        x
        for x in trace.lignes
        if x.libelle == "Crédit fédéral — époux / conjoint"
    )

    assert ligne.section == "FÉDÉRAL"
    assert ligne.montant == Decimal("1613.71")
    assert "ligne 30300" in ligne.source
    assert "État civil et revenu du conjoint validés" in ligne.source


def test_trace_formule_explique_ligne_30300():
    ligne = next(
        x
        for x in _trace().lignes
        if x.libelle == "Crédit fédéral — époux / conjoint"
    )

    assert "16\xa0129,00 $" in ligne.formule
    assert "5\xa0000,00 $" in ligne.formule
    assert "11\xa0129,00 $" in ligne.formule
    assert "14,5 %" in ligne.formule


def test_trace_impot_federal_final_mentionne_ligne_30300():
    ligne = next(
        x
        for x in _trace().lignes
        if x.libelle == "Impôt fédéral de base"
    )

    assert "crédit conjoint ligne 30300" in ligne.formule
    assert ligne.montant == Decimal("2788.19")


def test_trace_numerotation_continue():
    trace = _trace()
    assert [x.ordre for x in trace.lignes] == list(
        range(1, len(trace.lignes) + 1)
    )


def test_trace_sans_conjoint_garde_structure_historique():
    estimation = calculer_estimation_fiscale_2025(_dossier_52000())
    trace = construire_trace_calcul_fiscal_2025(estimation)

    assert not any(
        x.libelle == "Crédit fédéral — époux / conjoint"
        for x in trace.lignes
    )


def test_trace_formatee_affiche_conjoint_federal():
    texte = formater_trace_calcul_fiscal_2025(_trace())

    assert "Crédit fédéral — époux / conjoint" in texte
    assert "ARC ligne 30300" in texte
    assert "1\xa0613,71 $" in texte
    assert "État civil et revenu du conjoint validés" in texte
