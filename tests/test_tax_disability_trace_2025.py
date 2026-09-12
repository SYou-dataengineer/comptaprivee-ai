from decimal import Decimal

from src.comptaprivee.tax_calculation_trace_2025 import (
    construire_trace_calcul_fiscal_2025,
)
from src.comptaprivee.tax_disability_2025 import (
    CreditDeficience2025,
)
from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000


def _deficience_complete():
    return CreditDeficience2025(
        reclamer_federal=True,
        reclamer_quebec=True,
        source_federale="T2201 / approbation ARC",
        source_quebec="Attestation professionnelle Québec",
        valide_par_comptable=True,
        age_18_plus_au_1_janvier_2025=True,
        deficience_12_mois_confirmee=True,
        profil_soi_meme_resident_quebec=True,
        ciph_approuve_arc=True,
        attestation_quebec_confirmee=True,
        aucun_conflit_soins_prepose_etablissement=True,
        aucun_transfert_federal=True,
    )


def _trace_avec_deficience():
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        credit_deficience=_deficience_complete(),
    )
    return construire_trace_calcul_fiscal_2025(estimation)


def test_trace_ajoute_deux_lignes_deficience():
    base = construire_trace_calcul_fiscal_2025(
        calculer_estimation_fiscale_2025(_dossier_52000())
    )
    trace = _trace_avec_deficience()

    assert len(trace.lignes) == len(base.lignes) + 2


def test_trace_federal_handicap():
    trace = _trace_avec_deficience()
    ligne = next(
        x
        for x in trace.lignes
        if x.libelle == "Crédit fédéral pour personnes handicapées"
    )

    assert ligne.section == "FÉDÉRAL"
    assert ligne.montant == Decimal("1470.01")
    assert "ligne 31600" in ligne.source
    assert "T2201 / approbation ARC" in ligne.source
    assert "10 138" in ligne.formule
    assert "14,5 %" in ligne.formule


def test_trace_quebec_deficience():
    trace = _trace_avec_deficience()
    ligne = next(
        x
        for x in trace.lignes
        if x.libelle == "Crédit Québec pour déficience grave et prolongée"
    )

    assert ligne.section == "QUÉBEC"
    assert ligne.montant == Decimal("577.22")
    assert "ligne 376" in ligne.source
    assert "Attestation professionnelle Québec" in ligne.source
    assert "4 123" in ligne.formule
    assert "14 %" in ligne.formule


def test_formule_impot_federal_mentionne_handicap():
    trace = _trace_avec_deficience()
    ligne = next(
        x
        for x in trace.lignes
        if x.libelle == "Impôt fédéral de base"
    )

    assert "crédit handicap ligne 31600" in ligne.formule


def test_formule_impot_quebec_mentionne_deficience():
    trace = _trace_avec_deficience()
    ligne = next(
        x
        for x in trace.lignes
        if x.libelle == "Impôt Québec préliminaire"
    )

    assert "crédit déficience ligne 376" in ligne.formule


def test_numerotation_reste_continue():
    trace = _trace_avec_deficience()
    assert [x.ordre for x in trace.lignes] == list(
        range(1, len(trace.lignes) + 1)
    )


def test_resultat_trace_correspond_estimation_handicap():
    trace = _trace_avec_deficience()

    assert trace.resultat == "Remboursement estimé"
    assert trace.montant_resultat == Decimal("7415.73")
