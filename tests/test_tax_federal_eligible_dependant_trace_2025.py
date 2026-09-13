from decimal import Decimal

from src.comptaprivee.tax_calculation_trace_2025 import (
    construire_trace_calcul_fiscal_2025,
)
from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_eligible_dependant_integration_2025 import (
    _profil_personne_charge,
)


LIBELLE = "Crédit fédéral — personne à charge admissible"


def _trace():
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        personne_charge_admissible_federale=_profil_personne_charge(),
    )
    return construire_trace_calcul_fiscal_2025(estimation)


def _ligne():
    trace = _trace()
    return next(
        ligne
        for ligne in trace.lignes
        if ligne.libelle == LIBELLE
    )


def test_trace_ajoute_ligne_30400():
    ligne = _ligne()

    assert ligne.section == "FÉDÉRAL"
    assert ligne.montant == Decimal("1758.71")


def test_trace_source_ligne_30400():
    ligne = _ligne()

    assert "ARC annexe 5 / ligne 30400" in ligne.source
    assert "validation comptable" in ligne.source
    assert (
        "État civil, résidence et revenu de l'enfant validés"
        in ligne.source
    )


def test_trace_formule_ligne_30400():
    ligne = _ligne()

    assert "Montant personnel fédéral" in ligne.formule
    assert "16\xa0129,00 $" in ligne.formule
    assert "revenu net de la personne à charge" in ligne.formule
    assert "4\xa0000,00 $" in ligne.formule
    assert "ligne 30400" in ligne.formule
    assert "12\xa0129,00 $" in ligne.formule
    assert "14,5 %" in ligne.formule


def test_trace_formule_impot_federal_mentionne_30400():
    trace = _trace()
    ligne_impot = next(
        ligne
        for ligne in trace.lignes
        if ligne.libelle == "Impôt fédéral de base"
    )

    assert "ligne 30400" in ligne_impot.formule
    assert "personne à charge admissible" in ligne_impot.formule


def test_trace_numerotation_continue():
    trace = _trace()

    assert [ligne.ordre for ligne in trace.lignes] == list(
        range(1, len(trace.lignes) + 1)
    )


def test_trace_sans_profil_ne_montre_pas_ligne_30400():
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000()
    )
    trace = construire_trace_calcul_fiscal_2025(estimation)

    assert all(
        ligne.libelle != LIBELLE
        for ligne in trace.lignes
    )
