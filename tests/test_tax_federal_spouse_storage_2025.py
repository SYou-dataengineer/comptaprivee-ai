import json
from decimal import Decimal

import pytest

from src.comptaprivee.tax_case_storage import (
    charger_dossier_fiscal,
    lister_dossiers_fiscaux,
    sauvegarder_dossier_fiscal,
)
from src.comptaprivee.tax_federal_spouse_2025 import (
    MontantConjointFederal2025,
)
from tests.test_tax_case_storage import _dossier
from tests.test_tax_federal_spouse_integration_2025 import (
    _profil_conjoint,
)


def test_montant_conjoint_roundtrip_json(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        montant_conjoint_federal=_profil_conjoint(),
        destination=tmp_path / "d.json",
    )

    x = charger_dossier_fiscal(p).montant_conjoint_federal

    assert x.reclamer_montant is True
    assert x.revenu_net_contribuable_ligne_23600 == Decimal("51515.00")
    assert x.revenu_net_conjoint_2025 == Decimal("5000")
    assert x.relation_conjoint_confirmee is True
    assert x.valide_par_comptable is True
    assert x.source_conjoint == "État civil et revenu du conjoint validés"


def test_json_conserve_tous_les_champs_conjoint(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        montant_conjoint_federal=_profil_conjoint(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    valeur = brut["montant_conjoint_federal"]

    assert valeur["reclamer_montant"] is True
    assert valeur["revenu_net_contribuable_ligne_23600"] == "51515.00"
    assert valeur["revenu_net_conjoint_2025"] == "5000"
    assert valeur["contribuable_resident_canada_toute_annee"] is True
    assert valeur["relation_conjoint_confirmee"] is True
    assert valeur["conjoint_soutenu_2025"] is True
    assert valeur["meme_conjoint_toute_annee_2025"] is True
    assert valeur["aucune_separation_2025"] is True
    assert valeur["conjoint_resident_canada_toute_annee"] is True
    assert valeur["aucun_paiement_pension_alimentaire"] is True
    assert valeur["aucune_infirmite_conjoint"] is True
    assert valeur["un_seul_conjoint_reclame_montant"] is True
    assert valeur["revenu_conjoint_confirme"] is True
    assert valeur["valide_par_comptable"] is True
    assert (
        valeur["source_conjoint"]
        == "État civil et revenu du conjoint validés"
    )


def test_ancien_json_sans_montant_conjoint_reste_compatible(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        destination=tmp_path / "ancien.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut.pop("montant_conjoint_federal", None)
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    x = charger_dossier_fiscal(p).montant_conjoint_federal
    assert x == MontantConjointFederal2025()


def test_json_revenu_conjoint_negatif_est_refuse(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        montant_conjoint_federal=_profil_conjoint(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["montant_conjoint_federal"]["revenu_net_conjoint_2025"] = "-1"
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="conjoint"):
        charger_dossier_fiscal(p)


def test_json_validation_relation_conjoint_incomplete_est_refusee(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        montant_conjoint_federal=_profil_conjoint(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["montant_conjoint_federal"][
        "relation_conjoint_confirmee"
    ] = False
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="relation"):
        charger_dossier_fiscal(p)


def test_json_type_montant_conjoint_invalide_est_refuse(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["montant_conjoint_federal"] = ["invalide"]
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="conjoint"):
        charger_dossier_fiscal(p)


def test_liste_dossiers_recharge_montant_conjoint(tmp_path):
    sauvegarder_dossier_fiscal(
        _dossier(),
        montant_conjoint_federal=_profil_conjoint(),
        destination=tmp_path / "d.json",
    )

    dossiers = lister_dossiers_fiscaux(tmp_path)

    assert len(dossiers) == 1
    assert dossiers[0].montant_conjoint_federal.reclamer_montant is True
    assert (
        dossiers[0].montant_conjoint_federal.revenu_net_conjoint_2025
        == Decimal("5000")
    )
