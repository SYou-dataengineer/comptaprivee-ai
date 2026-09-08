from decimal import Decimal

import pytest

from src.comptaprivee.tax_adjustments_2025 import AjustementReer2025
from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
    formater_estimation_fiscale_2025,
)
from src.comptaprivee.tax_union_dues_2025 import (
    CotisationsSyndicalesProfessionnelles2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000


def _cotisations_600():
    return CotisationsSyndicalesProfessionnelles2025(
        montant_federal_admissible=Decimal("600"),
        montant_quebec_admissible=Decimal("600"),
        source_federale="T4 case 44",
        source_quebec="RL-1 case F",
        valide_par_comptable=True,
        sources_dedoublonnees=True,
    )


def _reer_5000():
    return AjustementReer2025(
        deduction_reer=Decimal("5000"),
        plafond_reer_confirme=Decimal("8000"),
        source_plafond_reer="Avis de cotisation / T1028 ARC",
        valide_par_comptable=True,
    )


def test_sans_cotisations_resultat_reste_identique():
    estimation = calculer_estimation_fiscale_2025(_dossier_52000())

    assert estimation.revenu.revenu_imposable_federal == Decimal("51515.00")
    assert estimation.revenu.revenu_imposable_quebec == Decimal("50095.00")
    assert estimation.rapprochement.remboursement_estime == Decimal("5611.05")


def test_cotisations_reduisent_seulement_revenu_federal():
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        cotisations_syndicales=_cotisations_600(),
    )

    assert estimation.revenu.revenu_imposable_federal == Decimal("50915.00")
    assert estimation.revenu.revenu_imposable_quebec == Decimal("50095.00")


def test_credit_quebec_10_pour_cent_est_applique():
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        cotisations_syndicales=_cotisations_600(),
    )

    assert estimation.quebec.impot_quebec_preliminaire == Decimal("4353.36")


def test_remboursement_avec_cotisations_600():
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        cotisations_syndicales=_cotisations_600(),
    )

    assert estimation.rapprochement.impot_total_preliminaire == Decimal("7956.30")
    assert estimation.rapprochement.remboursement_estime == Decimal("5743.70")


def test_reer_et_cotisations_se_combinent_sans_double_effet_quebec():
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        ajustement_reer=_reer_5000(),
        cotisations_syndicales=_cotisations_600(),
    )

    assert estimation.revenu.revenu_imposable_federal == Decimal("45915.00")
    assert estimation.revenu.revenu_imposable_quebec == Decimal("45095.00")
    assert estimation.rapprochement.remboursement_estime == Decimal("7049.07")


def test_estimation_conserve_les_cotisations_validees():
    cotisations = _cotisations_600()
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        cotisations_syndicales=cotisations,
    )

    assert estimation.cotisations_syndicales == cotisations


def test_cotisations_invalides_bloquent_le_calcul():
    cotisations = CotisationsSyndicalesProfessionnelles2025(
        montant_federal_admissible=Decimal("600"),
        source_federale="T4 case 44",
        valide_par_comptable=True,
        sources_dedoublonnees=False,
    )

    with pytest.raises(ValueError):
        calculer_estimation_fiscale_2025(
            _dossier_52000(),
            cotisations_syndicales=cotisations,
        )


def test_resume_affiche_les_deux_traitements_fiscaux():
    estimation = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        cotisations_syndicales=_cotisations_600(),
    )
    texte = formater_estimation_fiscale_2025(estimation)

    assert "Cotisations fédérales — ligne 21200 : 600,00 $" in texte
    assert "Base Québec — ligne 397.1 : 600,00 $" in texte
    assert "Crédit Québec (10 %) : 60,00 $" in texte
    assert "T4 case 44" in texte
    assert "RL-1 case F" in texte
