from decimal import Decimal

from src.comptaprivee.tax_calculation_trace_2025 import (
    construire_trace_calcul_fiscal_2025,
)
from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_home_accessibility_2025 import _profil


def _trace_31285():
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        accessibilite_domiciliaire_federale=_profil(),
    )
    return construire_trace_calcul_fiscal_2025(estimation)


def _ligne_31285(trace):
    lignes = [
        ligne
        for ligne in trace.lignes
        if ligne.libelle
        == "Crédit fédéral — accessibilité domiciliaire"
    ]
    assert len(lignes) == 1
    return lignes[0]


def test_trace_31285_affiche_montant_et_credit():
    trace = _trace_31285()
    ligne = _ligne_31285(trace)

    assert ligne.section == "FÉDÉRAL"
    assert ligne.montant == Decimal("2900.00")
    assert "ARC ligne 31285" in ligne.source
    assert "20\xa0000,00 $" in ligne.formule
    assert "maximum 20 000 $" in ligne.formule
    assert "14,5 %" in ligne.formule


def test_trace_31285_explique_admissibilite():
    ligne = _ligne_31285(_trace_31285())

    for terme in (
        "65 ans ou plus / CIPH",
        "demande pour soi-même",
        "logement situé au Canada",
        "rénovation durable et intégrante",
        "accessibilité / mobilité / réduction du risque",
        "travaux et biens 2025",
        "aucun partage",
        "entreprise/location",
        "fournisseurs liés",
        "pièces justificatives",
    ):
        assert terme in ligne.formule


def test_trace_31285_affiche_source_validation():
    profil = _profil()
    ligne = _ligne_31285(_trace_31285())

    assert profil.source_renovation in ligne.source
    assert "validation comptable" in ligne.source


def test_trace_31285_enrichit_formule_impot_federal():
    trace = _trace_31285()

    ligne_impot = next(
        ligne
        for ligne in trace.lignes
        if ligne.libelle == "Impôt fédéral de base"
    )

    assert "crédit accessibilité domiciliaire ligne 31285" in (
        ligne_impot.formule
    )


def test_trace_31285_numerotation_continue():
    trace = _trace_31285()

    assert [ligne.ordre for ligne in trace.lignes] == list(
        range(1, len(trace.lignes) + 1)
    )


def test_trace_sans_31285_ne_contient_pas_ligne():
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000()
    )
    trace = construire_trace_calcul_fiscal_2025(estimation)

    assert all(
        ligne.libelle
        != "Crédit fédéral — accessibilité domiciliaire"
        for ligne in trace.lignes
    )
