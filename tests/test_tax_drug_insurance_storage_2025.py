import json
from decimal import Decimal

import pytest

from src.comptaprivee.tax_case_storage import (
    charger_dossier_fiscal,
    lister_dossiers_fiscaux,
    sauvegarder_dossier_fiscal,
)
from src.comptaprivee.tax_drug_insurance_2025 import (
    AssuranceMedicamentsQuebec2025,
)
from tests.test_tax_case_storage import _dossier


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


def test_assurance_medicaments_roundtrip_json(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        assurance_medicaments=_public_max(),
        destination=tmp_path / "d.json",
    )
    x = charger_dossier_fiscal(p).assurance_medicaments

    assert x.type_couverture == "public"
    assert x.revenu_ligne_275 == Decimal("50095.00")
    assert x.revenu_ligne_48_annexe_k == Decimal("10000")
    assert x.source == "Annexe K / ligne 447 validée"


def test_collectif_roundtrip_conserve_code_449(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        assurance_medicaments=_collectif(),
        destination=tmp_path / "collectif.json",
    )
    x = charger_dossier_fiscal(p).assurance_medicaments

    assert x.type_couverture == "collectif"
    assert x.code_case_449 == "14"
    assert x.couverture_toute_annee is True


def test_ancien_json_sans_assurance_reste_compatible(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        destination=tmp_path / "ancien.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut.pop("assurance_medicaments", None)
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    x = charger_dossier_fiscal(p).assurance_medicaments
    assert x.type_couverture == ""
    assert x.revenu_ligne_275 == Decimal("0")


def test_json_conserve_confirmations_assurance(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        assurance_medicaments=_public_max(),
        destination=tmp_path / "d.json",
    )
    valeur = json.loads(
        p.read_text(encoding="utf-8")
    )["assurance_medicaments"]

    assert valeur["couverture_toute_annee"] is True
    assert valeur["sans_conjoint_31_decembre_2025"] is True
    assert valeur["aucun_mois_exempt"] is True
    assert valeur["carte_ramq_valide_2025"] is True
    assert valeur["situation_validee_par_comptable"] is True
    assert valeur["aucun_cas_particulier"] is True


def test_json_public_incomplet_est_refuse(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        assurance_medicaments=_public_max(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["assurance_medicaments"]["carte_ramq_valide_2025"] = False
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="RAMQ"):
        charger_dossier_fiscal(p)


def test_json_progressif_non_supporte_est_refuse(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        assurance_medicaments=_public_max(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["assurance_medicaments"]["revenu_ligne_48_annexe_k"] = "5000"
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="progressif"):
        charger_dossier_fiscal(p)


def test_liste_dossiers_recharge_assurance(tmp_path):
    sauvegarder_dossier_fiscal(
        _dossier(),
        assurance_medicaments=_public_max(),
        destination=tmp_path / "d.json",
    )

    dossiers = lister_dossiers_fiscaux(tmp_path)
    assert len(dossiers) == 1
    assert dossiers[0].assurance_medicaments.type_couverture == "public"
