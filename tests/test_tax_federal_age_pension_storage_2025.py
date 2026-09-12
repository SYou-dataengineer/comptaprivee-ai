import json
from decimal import Decimal

import pytest

from src.comptaprivee.tax_case_storage import (
    charger_dossier_fiscal,
    lister_dossiers_fiscaux,
    sauvegarder_dossier_fiscal,
)
from src.comptaprivee.tax_federal_age_pension_2025 import (
    CreditsFederauxAgePension2025,
)
from tests.test_tax_case_storage import _dossier
from tests.test_tax_federal_age_pension_integration_2025 import (
    _profil_age_federal,
)


def test_age_pension_federal_roundtrip_json(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        credits_federaux_age_pension=_profil_age_federal(),
        destination=tmp_path / "d.json",
    )
    x = charger_dossier_fiscal(p).credits_federaux_age_pension

    assert x.reclamer_montant_age is True
    assert x.age_65_plus_31_decembre_2025 is True
    assert x.revenu_net_ligne_23600 == Decimal("51515.00")
    assert x.reclamer_montant_pension is False
    assert x.revenu_pension_admissible == Decimal("0")
    assert x.source_age == "Date de naissance validée"


def test_json_conserve_champs_age_pension_federal(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        credits_federaux_age_pension=_profil_age_federal(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    valeur = brut["credits_federaux_age_pension"]

    assert valeur["reclamer_montant_age"] is True
    assert valeur["age_65_plus_31_decembre_2025"] is True
    assert valeur["revenu_net_ligne_23600"] == "51515.00"
    assert valeur["reclamer_montant_pension"] is False
    assert valeur["revenu_pension_admissible"] == "0"
    assert valeur["resident_canada_toute_annee"] is True
    assert valeur["aucune_regle_deces"] is True
    assert valeur["aucun_fractionnement_pension"] is True
    assert valeur["aucun_transfert_conjoint"] is True
    assert valeur["revenu_pension_admissible_confirme"] is False
    assert valeur["valide_par_comptable"] is True
    assert valeur["source_age"] == "Date de naissance validée"
    assert valeur["source_pension"] == ""


def test_ancien_json_sans_age_pension_federal_reste_compatible(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        destination=tmp_path / "ancien.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut.pop("credits_federaux_age_pension", None)
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    x = charger_dossier_fiscal(p).credits_federaux_age_pension
    assert x == CreditsFederauxAgePension2025()


def test_json_revenu_net_federal_negatif_est_refuse(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        credits_federaux_age_pension=_profil_age_federal(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["credits_federaux_age_pension"][
        "revenu_net_ligne_23600"
    ] = "-1"
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="ligne 23600"):
        charger_dossier_fiscal(p)


def test_json_validation_fractionnement_incomplete_est_refusee(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        credits_federaux_age_pension=_profil_age_federal(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["credits_federaux_age_pension"][
        "aucun_fractionnement_pension"
    ] = False
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="T1032"):
        charger_dossier_fiscal(p)


def test_json_type_age_pension_federal_invalide_est_refuse(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["credits_federaux_age_pension"] = ["invalide"]
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="âge/pension fédéral"):
        charger_dossier_fiscal(p)


def test_liste_dossiers_recharge_age_pension_federal(tmp_path):
    sauvegarder_dossier_fiscal(
        _dossier(),
        credits_federaux_age_pension=_profil_age_federal(),
        destination=tmp_path / "d.json",
    )

    dossiers = lister_dossiers_fiscaux(tmp_path)

    assert len(dossiers) == 1
    assert (
        dossiers[0]
        .credits_federaux_age_pension
        .reclamer_montant_age
        is True
    )
    assert (
        dossiers[0]
        .credits_federaux_age_pension
        .revenu_net_ligne_23600
        == Decimal("51515.00")
    )
