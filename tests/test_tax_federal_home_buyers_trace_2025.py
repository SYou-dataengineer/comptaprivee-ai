from decimal import Decimal

from src.comptaprivee.tax_calculation_trace_2025 import (
    construire_trace_calcul_fiscal_2025,
)
from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_home_buyers_2025 import _profil


LIBELLE_31270 = "Crédit fédéral — achat d'une habitation"


def _trace_31270():
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        achat_habitation_federal=_profil(),
    )
    return construire_trace_calcul_fiscal_2025(estimation)


def _ligne_31270(trace):
    return next(
        ligne
        for ligne in trace.lignes
        if ligne.libelle == LIBELLE_31270
    )


def _normaliser(texte):
    return texte.replace("\xa0", " ").replace("\u202f", " ")


def test_trace_31270_affiche_montant_et_credit():
    ligne = _ligne_31270(_trace_31270())
    formule = _normaliser(ligne.formule)

    assert ligne.section == "FÉDÉRAL"
    assert ligne.montant == Decimal("1450.00")
    assert "ligne 31270" in ligne.source
    assert "10 000,00 $" in formule
    assert "14,5 %" in formule
    assert "maximum 10 000 $" in formule.lower()


def test_trace_31270_affiche_conditions_principales():
    ligne = _ligne_31270(_trace_31270())
    formule = _normaliser(ligne.formule).lower()

    assert "première habitation" in formule
    assert "année de l'achat" in formule
    assert "quatre années précédentes" in formule
    assert "résidence principale" in formule
    assert "un an" in formule


def test_trace_31270_affiche_restrictions_profil_simple():
    ligne = _ligne_31270(_trace_31270())
    formule = _normaliser(ligne.formule).lower()

    assert "aucun partage" in formule
    assert "exception handicap non utilisée" in formule
    assert "pièces justificatives" in formule
    assert "validation comptable" in ligne.source.lower()


def test_trace_31270_contient_source_validation():
    profil = _profil()
    ligne = _ligne_31270(_trace_31270())

    assert profil.source_habitation in ligne.source
    assert "validation comptable" in ligne.source.lower()


def test_trace_31270_avant_impot_federal_de_base():
    trace = _trace_31270()
    index_31270 = next(
        i for i, ligne in enumerate(trace.lignes)
        if ligne.libelle == LIBELLE_31270
    )
    index_base = next(
        i for i, ligne in enumerate(trace.lignes)
        if ligne.libelle == "Impôt fédéral de base"
    )

    assert index_31270 < index_base


def test_numerotation_trace_31270_reste_continue():
    trace = _trace_31270()

    assert [ligne.ordre for ligne in trace.lignes] == list(
        range(1, len(trace.lignes) + 1)
    )


def test_trace_sans_31270_ne_contient_pas_ligne_31270():
    estimation = calculer_estimation_fiscale_2025(_dossier_52000())
    trace = construire_trace_calcul_fiscal_2025(estimation)

    assert all(
        ligne.libelle != LIBELLE_31270
        for ligne in trace.lignes
    )
