from decimal import Decimal

from src.comptaprivee.tax_calculation_trace_2025 import (
    construire_trace_calcul_fiscal_2025,
)
from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_caregiver_child_integration_2025 import (
    _profil_aidant_enfant,
)


LIBELLE = "Crédit fédéral — aidant naturel enfant de moins de 18 ans"


def _trace():
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        aidant_enfant_federal=_profil_aidant_enfant(),
    )
    return construire_trace_calcul_fiscal_2025(estimation)


def _ligne():
    trace = _trace()
    return next(
        ligne
        for ligne in trace.lignes
        if ligne.libelle == LIBELLE
    )


def test_trace_ajoute_ligne_30499_30500():
    ligne = _ligne()

    assert ligne.section == "FÉDÉRAL"
    assert ligne.montant == Decimal("389.62")


def test_trace_source_lignes_30499_30500():
    ligne = _ligne()

    assert "ARC lignes 30499 / 30500" in ligne.source
    assert "validation comptable" in ligne.source
    assert (
        "Lien familial, résidence et preuve médicale validés"
        in ligne.source
    )


def test_trace_formule_aidant_enfant():
    ligne = _ligne()

    assert "1 enfant admissible" in ligne.formule
    assert "2\xa0687,00 $" in ligne.formule
    assert "14,5 %" in ligne.formule
    assert "preuve médicale ou T2201" in ligne.formule
    assert "aucune garde partagée" in ligne.formule
    assert "aucune pension alimentaire" in ligne.formule


def test_trace_formule_impot_federal_mentionne_30500():
    trace = _trace()
    ligne_impot = next(
        ligne
        for ligne in trace.lignes
        if ligne.libelle == "Impôt fédéral de base"
    )

    assert "ligne 30500" in ligne_impot.formule
    assert "aidant naturel" in ligne_impot.formule


def test_trace_numerotation_continue():
    trace = _trace()

    assert [ligne.ordre for ligne in trace.lignes] == list(
        range(1, len(trace.lignes) + 1)
    )


def test_trace_sans_profil_ne_montre_pas_ligne_30500():
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000()
    )
    trace = construire_trace_calcul_fiscal_2025(estimation)

    assert all(
        ligne.libelle != LIBELLE
        for ligne in trace.lignes
    )
