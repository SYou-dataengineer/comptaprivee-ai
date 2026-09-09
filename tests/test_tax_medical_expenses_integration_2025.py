from decimal import Decimal

import pytest

from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
    formater_estimation_fiscale_2025,
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


def test_sans_frais_medicaux_resultat_reste_identique():
    e = calculer_estimation_fiscale_2025(_dossier_52000())
    assert e.rapprochement.impot_total_preliminaire == Decimal("8088.95")
    assert e.rapprochement.remboursement_estime == Decimal("5611.05")
    assert e.frais_medicaux.montant_admissible_federal == Decimal("0")
    assert e.frais_medicaux.montant_admissible_quebec == Decimal("0")


def test_frais_3000_reduisent_impot_federal():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        frais_medicaux=_frais_3000(),
    )
    assert e.federal.impot_federal_de_base == Decimal("4190.99")


def test_frais_3000_reduisent_impot_quebec():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        frais_medicaux=_frais_3000(),
    )
    assert e.quebec.impot_quebec_preliminaire == Decimal("4113.93")


def test_frais_3000_recalculent_remboursement():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        frais_medicaux=_frais_3000(),
    )
    assert e.rapprochement.impot_total_preliminaire == Decimal("7613.41")
    assert e.rapprochement.remboursement_estime == Decimal("6086.59")


def test_estimation_conserve_frais_medicaux_valides():
    frais = _frais_3000()
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        frais_medicaux=frais,
    )
    assert e.frais_medicaux == frais


def test_frais_medicaux_invalides_bloquent_estimation():
    frais = FraisMedicaux2025(
        montant_admissible_federal=Decimal("3000"),
        source_federale="Reçus médicaux",
        valide_par_comptable=False,
        recus_confirmes=True,
        remboursements_soustraits=True,
        periode_12_mois_fin_2025_confirmee=True,
        aucune_periode_deja_reclamee=True,
        profil_individuel_sans_conjoint_dependant=True,
    )
    with pytest.raises(ValueError):
        calculer_estimation_fiscale_2025(
            _dossier_52000(),
            frais_medicaux=frais,
        )


def test_resume_affiche_frais_medicaux_et_credits():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        frais_medicaux=_frais_3000(),
    )
    resume = formater_estimation_fiscale_2025(e)
    assert "FRAIS MÉDICAUX VALIDÉS" in resume
    assert "Crédit fédéral — lignes 33099 / 33200 : 210,91 $" in resume
    assert "Crédit Québec — ligne 381 : 299,43 $" in resume
    assert "6\u00a0086,59 $" in resume


def test_sources_medicales_sont_affichees_dans_resume():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        frais_medicaux=_frais_3000(),
    )
    resume = formater_estimation_fiscale_2025(e)
    assert "Reçus médicaux vérifiés — ARC" in resume
    assert "Reçus médicaux vérifiés — Revenu Québec" in resume
