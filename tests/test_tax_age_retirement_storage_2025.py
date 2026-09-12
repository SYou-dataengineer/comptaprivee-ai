import json
from decimal import Decimal

import pytest

from src.comptaprivee.tax_age_retirement_2025 import (
    MontantsAgeRetraite2025,
)
from src.comptaprivee.tax_case_storage import (
    charger_dossier_fiscal,
    lister_dossiers_fiscaux,
    sauvegarder_dossier_fiscal,
)
from tests.test_tax_age_retirement_integration_2025 import (
    _profil_age_retraite,
)
from tests.test_tax_case_storage import _dossier


def test_age_retraite_roundtrip_json(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        montants_age_retraite=_profil_age_retraite(),
        destination=tmp_path / "d.json",
    )
    x = charger_dossier_fiscal(p).montants_age_retraite

    assert x.reclamer_age is True
    assert x.ne_avant_1_janvier_1961 is True
    assert x.reclamer_revenus_retraite is True
    assert x.revenu_ligne_122 == Decimal("3000")
    assert x.revenu_familial_net == Decimal("50095.00")
    assert x.source_age == "Date de naissance validée"
    assert x.source_retraite == "RL-2 / feuillet retraite validé"


def test_json_conserve_champs_age_retraite(tmp_path):
    profil = _profil_age_retraite(
        deduction_ligne_250_point_4=Decimal("10"),
        deduction_ligne_250_point_6=Decimal("20"),
        deduction_ligne_293=Decimal("30"),
        deduction_ligne_297_points_9_12=Decimal("40"),
    )
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        montants_age_retraite=profil,
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    valeur = brut["montants_age_retraite"]

    assert valeur["reclamer_age"] is True
    assert valeur["ne_avant_1_janvier_1961"] is True
    assert valeur["reclamer_revenus_retraite"] is True
    assert valeur["deduction_ligne_250_point_4"] == "10"
    assert valeur["deduction_ligne_250_point_6"] == "20"
    assert valeur["deduction_ligne_293"] == "30"
    assert valeur["deduction_ligne_297_points_9_12"] == "40"
    assert valeur["aucun_conjoint_31_decembre_2025"] is True
    assert valeur["resident_quebec_canada_toute_annee"] is True
    assert valeur["aucun_montant_personne_vivant_seule"] is True
    assert valeur["revenus_retraite_admissibles_confirmes"] is True
    assert valeur["revenus_non_admissibles_exclus"] is True
    assert valeur["valide_par_comptable"] is True


def test_ancien_json_sans_age_retraite_reste_compatible(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        destination=tmp_path / "ancien.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut.pop("montants_age_retraite", None)
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    x = charger_dossier_fiscal(p).montants_age_retraite
    assert x == MontantsAgeRetraite2025()


def test_json_revenu_familial_negatif_est_refuse(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        montants_age_retraite=_profil_age_retraite(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["montants_age_retraite"]["revenu_familial_net"] = "-1"
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="revenu familial net"):
        charger_dossier_fiscal(p)


def test_json_validation_retraite_incomplete_est_refusee(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        montants_age_retraite=_profil_age_retraite(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["montants_age_retraite"][
        "revenus_non_admissibles_exclus"
    ] = False
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="PSV, RRQ et RPC"):
        charger_dossier_fiscal(p)


def test_json_type_age_retraite_invalide_est_refuse(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["montants_age_retraite"] = ["invalide"]
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="âge/retraite"):
        charger_dossier_fiscal(p)


def test_liste_dossiers_recharge_age_retraite(tmp_path):
    sauvegarder_dossier_fiscal(
        _dossier(),
        montants_age_retraite=_profil_age_retraite(),
        destination=tmp_path / "d.json",
    )

    dossiers = lister_dossiers_fiscaux(tmp_path)
    assert len(dossiers) == 1
    assert dossiers[0].montants_age_retraite.reclamer_age is True
    assert (
        dossiers[0].montants_age_retraite.revenu_ligne_122
        == Decimal("3000")
    )
