from decimal import Decimal

from src.comptaprivee.tax_calculation_trace_2025 import (
    construire_trace_calcul_fiscal_2025,
)
from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_caregiver_other_dependant_2025 import (
    _profil,
)


LIBELLE_30450 = (
    "Crédit fédéral — aidant naturel autre personne à charge"
)


def _trace_30450():
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        aidant_autre_personne_charge_federal=_profil(),
    )
    return construire_trace_calcul_fiscal_2025(estimation)


def _ligne_30450(trace):
    return next(
        ligne
        for ligne in trace.lignes
        if ligne.libelle == LIBELLE_30450
    )


def test_trace_30450_affiche_montant_et_credit():
    ligne = _ligne_30450(_trace_30450())

    assert ligne.section == "FÉDÉRAL"
    assert ligne.montant == Decimal("550.71")
    assert "Annexe 5 / ligne 30450" in ligne.source
    formule = ligne.formule.replace("\xa0", " ").replace("\u202f", " ")
    assert "28 798 $" in formule
    assert "25 000,00 $" in formule
    assert "3 798,00 $" in formule
    assert "8 601 $" in formule
    assert "14,5 %" in formule


def test_trace_30450_affiche_ligne_51120():
    ligne = _ligne_30450(_trace_30450())

    assert "ligne 51120" in ligne.formule
    assert "1 personne" in ligne.formule


def test_trace_30450_explique_gardes_fiscaux():
    ligne = _ligne_30450(_trace_30450())

    formule = ligne.formule.lower()
    assert "30300/30400" in formule
    assert "pension alimentaire" in formule
    assert "partage" in formule
    assert "preuve médicale" in formule or "t2201" in formule


def test_trace_30450_contient_source_validation():
    ligne = _ligne_30450(_trace_30450())

    assert "validation comptable" in ligne.source
    assert "Lien familial" in ligne.source


def test_trace_30450_avant_impot_federal_de_base():
    trace = _trace_30450()
    index_30450 = next(
        i for i, ligne in enumerate(trace.lignes)
        if ligne.libelle == LIBELLE_30450
    )
    index_base = next(
        i for i, ligne in enumerate(trace.lignes)
        if ligne.libelle == "Impôt fédéral de base"
    )

    assert index_30450 < index_base


def test_numerotation_trace_30450_reste_continue():
    trace = _trace_30450()

    assert [ligne.ordre for ligne in trace.lignes] == list(
        range(1, len(trace.lignes) + 1)
    )


def test_trace_sans_30450_ne_contient_pas_ligne_30450():
    estimation = calculer_estimation_fiscale_2025(_dossier_52000())
    trace = construire_trace_calcul_fiscal_2025(estimation)

    assert all(
        ligne.libelle != LIBELLE_30450
        for ligne in trace.lignes
    )
