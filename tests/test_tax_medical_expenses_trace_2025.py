from decimal import Decimal

from src.comptaprivee.tax_calculation_trace_2025 import (
    construire_trace_calcul_fiscal_2025,
    formater_trace_calcul_fiscal_2025,
)
from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
)
from src.comptaprivee.tax_medical_expenses_2025 import FraisMedicaux2025
from tests.test_tax_estimation_2025 import _dossier_52000


def _frais_3000():
    return FraisMedicaux2025(
        montant_admissible_federal=Decimal("3000"),
        montant_admissible_quebec=Decimal("3000"),
        source_federale="Reçus médicaux vérifiés — ARC",
        source_quebec="Reçus médicaux vérifiés — Revenu Québec",
        valide_par_comptable=True,
        recus_confirmes=True,
        remboursements_soustraits=True,
        periode_12_mois_fin_2025_confirmee=True,
        aucune_periode_deja_reclamee=True,
        profil_individuel_sans_conjoint_dependant=True,
    )


def test_trace_medicale_ajoute_deux_etapes():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        frais_medicaux=_frais_3000(),
    )
    trace = construire_trace_calcul_fiscal_2025(e)

    assert len(trace.lignes) == 19
    assert [x.ordre for x in trace.lignes] == list(range(1, 20))


def test_trace_medicale_affiche_credit_federal_et_quebec():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        frais_medicaux=_frais_3000(),
    )
    texte = formater_trace_calcul_fiscal_2025(
        construire_trace_calcul_fiscal_2025(e)
    )

    assert "Crédit fédéral pour frais médicaux" in texte
    assert "Crédit Québec pour frais médicaux" in texte
    assert "210,91 $" in texte
    assert "299,43 $" in texte


def test_trace_medicale_affiche_sources_et_seuils():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        frais_medicaux=_frais_3000(),
    )
    texte = formater_trace_calcul_fiscal_2025(
        construire_trace_calcul_fiscal_2025(e)
    )

    assert "ARC lignes 33099 / 33200" in texte
    assert "Revenu Québec ligne 381" in texte
    assert "Reçus médicaux vérifiés — ARC" in texte
    assert "Reçus médicaux vérifiés — Revenu Québec" in texte
    assert "2 834 $" in texte
    assert "3 % du revenu net Québec" in texte


def test_rapprochement_sans_medical_conserve_limitation():
    e = calculer_estimation_fiscale_2025(_dossier_52000())

    assert (
        "Aucun crédit familial, médical, étude ou handicap."
        in e.rapprochement.limitations
    )


def test_rapprochement_avec_medical_retire_fausse_limitation():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        frais_medicaux=_frais_3000(),
    )

    assert (
        "Aucun crédit familial, médical, étude ou handicap."
        not in e.rapprochement.limitations
    )
    assert (
        "Aucun crédit familial, étude ou handicap."
        in e.rapprochement.limitations
    )
