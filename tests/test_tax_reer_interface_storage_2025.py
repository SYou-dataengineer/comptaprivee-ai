import json
from decimal import Decimal

import pytest

from src.comptaprivee.tax_adjustments_2025 import (
    AjustementReer2025,
    creer_ajustement_reer_depuis_champs_2025,
    normaliser_montant_reer_2025,
)
from src.comptaprivee.tax_case_storage import (
    charger_dossier_fiscal,
    sauvegarder_dossier_fiscal,
)
from tests.test_tax_estimation_2025 import _dossier_52000


def _reer_5000():
    return AjustementReer2025(
        deduction_reer=Decimal("5000.00"),
        plafond_reer_confirme=Decimal("8000.00"),
        source_plafond_reer="Avis de cotisation / T1028 ARC",
        valide_par_comptable=True,
    )


def test_normaliser_montant_reer_format_quebec():
    assert normaliser_montant_reer_2025(
        "5 000,00 $"
    ) == Decimal("5000.00")


def test_normaliser_montant_reer_vide_devient_zero():
    assert normaliser_montant_reer_2025("") == Decimal("0")


def test_normaliser_montant_reer_invalide_est_refuse():
    with pytest.raises(ValueError):
        normaliser_montant_reer_2025("cinq mille")


def test_creer_ajustement_depuis_champs():
    ajustement = creer_ajustement_reer_depuis_champs_2025(
        "5000",
        "8000",
        " Avis de cotisation ARC ",
        True,
    )
    assert ajustement.deduction_reer == Decimal("5000.00")
    assert ajustement.plafond_reer_confirme == Decimal("8000.00")
    assert ajustement.source_plafond_reer == "Avis de cotisation ARC"


def test_creer_ajustement_exige_validation():
    with pytest.raises(ValueError):
        creer_ajustement_reer_depuis_champs_2025(
            "5000",
            "8000",
            "Avis de cotisation ARC",
            False,
        )


def test_stockage_reer_round_trip(tmp_path):
    chemin = sauvegarder_dossier_fiscal(
        _dossier_52000(),
        ajustement_reer=_reer_5000(),
        destination=tmp_path / "dossier.json",
    )
    charge = charger_dossier_fiscal(chemin)
    assert charge.ajustement_reer.deduction_reer == Decimal("5000.00")
    assert charge.ajustement_reer.plafond_reer_confirme == Decimal("8000.00")


def test_stockage_sans_reer_reste_compatible(tmp_path):
    chemin = sauvegarder_dossier_fiscal(
        _dossier_52000(),
        destination=tmp_path / "dossier.json",
    )
    charge = charger_dossier_fiscal(chemin)
    assert charge.ajustement_reer.deduction_reer == Decimal("0")


def test_stockage_reer_conserve_source_et_validation(tmp_path):
    chemin = sauvegarder_dossier_fiscal(
        _dossier_52000(),
        ajustement_reer=_reer_5000(),
        destination=tmp_path / "dossier.json",
    )
    brut = json.loads(chemin.read_text(encoding="utf-8"))
    assert (
        brut["ajustement_reer"]["source_plafond_reer"]
        == "Avis de cotisation / T1028 ARC"
    )
    assert brut["ajustement_reer"]["valide_par_comptable"] is True
