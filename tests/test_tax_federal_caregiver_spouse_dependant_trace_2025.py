from decimal import Decimal

from src.comptaprivee.tax_calculation_trace_2025 import (
    construire_trace_calcul_fiscal_2025,
)
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_caregiver_spouse_dependant_integration_2025 import (
    _30425_conjoint,
    _30425_personne_charge,
)
from tests.test_tax_federal_eligible_dependant_caregiver_base_2025 import (
    _profil_18_plus_infirmite,
)
from tests.test_tax_federal_spouse_caregiver_base_2025 import (
    _profil_infirmite,
)


LIBELLE_30425 = "Crédit fédéral — aidant naturel conjoint / personne à charge"


def _trace_conjoint():
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        montant_conjoint_federal=_profil_infirmite(
            revenu_net_contribuable_ligne_23600=Decimal("51515.00")
        ),
        aidant_conjoint_personne_charge_federal=_30425_conjoint(),
    )
    return construire_trace_calcul_fiscal_2025(estimation)


def _trace_personne_charge():
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        personne_charge_admissible_federale=_profil_18_plus_infirmite(
            revenu_net_contribuable_ligne_23600=Decimal("51515.00")
        ),
        aidant_conjoint_personne_charge_federal=_30425_personne_charge(),
    )
    return construire_trace_calcul_fiscal_2025(estimation)


def _ligne_30425(trace):
    return next(
        ligne
        for ligne in trace.lignes
        if ligne.libelle == LIBELLE_30425
    )


def test_trace_30425_conjoint_affiche_montant_et_credit():
    ligne = _ligne_30425(_trace_conjoint())

    assert ligne.section == "FÉDÉRAL"
    assert ligne.montant == Decimal("258.83")
    assert "Annexe 5 / ligne 30425" in ligne.source
    assert "28 798 $" in ligne.formule
    assert "8 601 $" in ligne.formule
    assert "14,5 %" in ligne.formule
    assert "conjoint" in ligne.formule.lower()
    assert "ligne 30300" in ligne.formule


def test_trace_30425_personne_charge_affiche_montant_et_credit():
    ligne = _ligne_30425(_trace_personne_charge())

    assert ligne.montant == Decimal("258.83")
    assert "personne à charge" in ligne.formule.lower()
    assert "ligne 30400" in ligne.formule


def test_trace_30300_explique_base_aidant_2687():
    trace = _trace_conjoint()
    ligne = next(
        ligne
        for ligne in trace.lignes
        if ligne.libelle == "Crédit fédéral — époux / conjoint"
    )

    assert "2 687 $" in ligne.formule
    assert "aidant naturel" in ligne.formule.lower()
    assert "ligne 30300" in ligne.formule


def test_trace_30400_explique_base_aidant_2687():
    trace = _trace_personne_charge()
    ligne = next(
        ligne
        for ligne in trace.lignes
        if ligne.libelle == "Crédit fédéral — personne à charge admissible"
    )

    assert "2 687 $" in ligne.formule
    assert "aidant naturel" in ligne.formule.lower()
    assert "ligne 30400" in ligne.formule


def test_trace_30425_avant_impot_federal_de_base():
    trace = _trace_conjoint()
    index_30425 = next(
        i for i, ligne in enumerate(trace.lignes)
        if ligne.libelle == LIBELLE_30425
    )
    index_base = next(
        i for i, ligne in enumerate(trace.lignes)
        if ligne.libelle == "Impôt fédéral de base"
    )

    assert index_30425 < index_base


def test_numerotation_trace_reste_continue():
    for trace in (_trace_conjoint(), _trace_personne_charge()):
        assert [ligne.ordre for ligne in trace.lignes] == list(
            range(1, len(trace.lignes) + 1)
        )
