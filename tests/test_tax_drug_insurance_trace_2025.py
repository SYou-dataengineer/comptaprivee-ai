from decimal import Decimal

from src.comptaprivee.tax_calculation_trace_2025 import (
    construire_trace_calcul_fiscal_2025,
)
from src.comptaprivee.tax_drug_insurance_2025 import (
    AssuranceMedicamentsQuebec2025,
)
from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000


def _public_max():
    return AssuranceMedicamentsQuebec2025(
        type_couverture="public",
        couverture_toute_annee=True,
        sans_conjoint_31_decembre_2025=True,
        revenu_ligne_275=Decimal("50095.00"),
        revenu_ligne_48_annexe_k=Decimal("10000"),
        aucun_mois_exempt=True,
        carte_ramq_valide_2025=True,
        situation_validee_par_comptable=True,
        aucun_cas_particulier=True,
        source="Annexe K / ligne 447 validée",
        code_case_449="",
    )


def _collectif():
    return AssuranceMedicamentsQuebec2025(
        type_couverture="collectif",
        couverture_toute_annee=True,
        sans_conjoint_31_decembre_2025=True,
        revenu_ligne_275=Decimal("50095.00"),
        revenu_ligne_48_annexe_k=Decimal("0"),
        aucun_mois_exempt=False,
        carte_ramq_valide_2025=False,
        situation_validee_par_comptable=True,
        aucun_cas_particulier=True,
        source="Assurance collective employeur",
        code_case_449="14",
    )


def _trace(assurance):
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        assurance_medicaments=assurance,
    )
    return construire_trace_calcul_fiscal_2025(estimation)


def test_trace_public_ajoute_une_ligne():
    base = construire_trace_calcul_fiscal_2025(
        calculer_estimation_fiscale_2025(_dossier_52000())
    )
    trace = _trace(_public_max())

    assert len(trace.lignes) == len(base.lignes) + 1


def test_trace_public_affiche_ligne_447():
    trace = _trace(_public_max())
    ligne = next(
        x
        for x in trace.lignes
        if x.libelle == "Cotisation assurance médicaments Québec"
    )

    assert ligne.section == "QUÉBEC"
    assert ligne.montant == Decimal("755.00")
    assert "annexe K / ligne 447" in ligne.source
    assert "Annexe K / ligne 447 validée" in ligne.source
    assert "755 $" in ligne.formule
    assert "8 181 $" in ligne.formule


def test_trace_public_place_cotisation_avant_total():
    trace = _trace(_public_max())

    i_cotisation = next(
        i
        for i, x in enumerate(trace.lignes)
        if x.libelle == "Cotisation assurance médicaments Québec"
    )
    i_total = next(
        i
        for i, x in enumerate(trace.lignes)
        if x.libelle == "Impôt total préliminaire"
    )

    assert i_cotisation < i_total


def test_trace_total_mentionne_ligne_447():
    trace = _trace(_public_max())
    ligne = next(
        x
        for x in trace.lignes
        if x.libelle == "Impôt total préliminaire"
    )

    assert "cotisation assurance médicaments ligne 447" in ligne.formule
    assert ligne.montant == Decimal("8843.95")


def test_trace_resultat_public_correspond_estimation():
    trace = _trace(_public_max())

    assert trace.resultat == "Remboursement estimé"
    assert trace.montant_resultat == Decimal("4856.05")


def test_trace_collectif_affiche_zero_et_code_14():
    trace = _trace(_collectif())
    ligne = next(
        x
        for x in trace.lignes
        if x.libelle == "Cotisation assurance médicaments Québec"
    )

    assert ligne.montant == Decimal("0")
    assert "code 14" in ligne.formule
    assert "couverture collective" in ligne.formule.lower()


def test_trace_sans_assurance_ne_modifie_pas_formule_total():
    trace = construire_trace_calcul_fiscal_2025(
        calculer_estimation_fiscale_2025(_dossier_52000())
    )
    ligne = next(
        x
        for x in trace.lignes
        if x.libelle == "Impôt total préliminaire"
    )

    assert ligne.formule == "Impôt fédéral après abattement + impôt Québec"


def test_trace_numerotation_reste_continue():
    trace = _trace(_public_max())
    assert [x.ordre for x in trace.lignes] == list(
        range(1, len(trace.lignes) + 1)
    )
