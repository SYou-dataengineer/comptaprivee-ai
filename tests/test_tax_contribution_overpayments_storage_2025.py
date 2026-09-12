import json
from decimal import Decimal

import pytest

from src.comptaprivee.tax_case_storage import (
    charger_dossier_fiscal,
    lister_dossiers_fiscaux,
    sauvegarder_dossier_fiscal,
)
from src.comptaprivee.tax_contribution_overpayments_2025 import (
    CotisationsExcedentaires2025,
)
from tests.test_tax_case_storage import _dossier


def _profil():
    return CotisationsExcedentaires2025(
        rrq_ba=Decimal("3200.00"),
        rrq_bb=Decimal("0"),
        gains_admissibles_rrq=Decimal("52000"),
        assurance_emploi=Decimal("700.00"),
        gains_assurables_ae=Decimal("52000"),
        rqap=Decimal("300.00"),
        revenus_assujettis_rqap=Decimal("52000"),
        source="T4 / RL-1 validés",
        valide_par_comptable=True,
        resident_quebec_31_decembre_2025=True,
        emploi_quebec_uniquement=True,
        rrq_uniquement_sans_rpc=True,
        aucun_travail_autonome=True,
        profil_rrq_standard_18_64=True,
        aucun_cas_particulier_ae=True,
        aucun_cas_particulier_rqap=True,
        calcul_standard_confirme=True,
    )


def test_cotisations_excedentaires_roundtrip_json(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        cotisations_excedentaires=_profil(),
        destination=tmp_path / "d.json",
    )
    x = charger_dossier_fiscal(p).cotisations_excedentaires

    assert x.rrq_ba == Decimal("3200.00")
    assert x.rrq_bb == Decimal("0")
    assert x.gains_admissibles_rrq == Decimal("52000")
    assert x.assurance_emploi == Decimal("700.00")
    assert x.gains_assurables_ae == Decimal("52000")
    assert x.rqap == Decimal("300.00")
    assert x.revenus_assujettis_rqap == Decimal("52000")
    assert x.source == "T4 / RL-1 validés"


def test_json_conserve_confirmations(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        cotisations_excedentaires=_profil(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    valeur = brut["cotisations_excedentaires"]

    assert valeur["valide_par_comptable"] is True
    assert valeur["resident_quebec_31_decembre_2025"] is True
    assert valeur["emploi_quebec_uniquement"] is True
    assert valeur["rrq_uniquement_sans_rpc"] is True
    assert valeur["aucun_travail_autonome"] is True
    assert valeur["profil_rrq_standard_18_64"] is True
    assert valeur["aucun_cas_particulier_ae"] is True
    assert valeur["aucun_cas_particulier_rqap"] is True
    assert valeur["calcul_standard_confirme"] is True


def test_ancien_json_sans_cotisations_excedentaires_reste_compatible(
    tmp_path,
):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        destination=tmp_path / "ancien.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut.pop("cotisations_excedentaires", None)
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    x = charger_dossier_fiscal(p).cotisations_excedentaires
    assert x == CotisationsExcedentaires2025()


def test_json_montant_negatif_est_refuse(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        cotisations_excedentaires=_profil(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["cotisations_excedentaires"]["assurance_emploi"] = "-1"
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="négatif"):
        charger_dossier_fiscal(p)


def test_json_validation_incomplete_est_refusee(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        cotisations_excedentaires=_profil(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["cotisations_excedentaires"][
        "calcul_standard_confirme"
    ] = False
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="calcul standard"):
        charger_dossier_fiscal(p)


def test_json_type_invalide_est_refuse(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["cotisations_excedentaires"] = ["invalide"]
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="cotisations excédentaires"):
        charger_dossier_fiscal(p)


def test_liste_dossiers_recharge_cotisations_excedentaires(tmp_path):
    sauvegarder_dossier_fiscal(
        _dossier(),
        cotisations_excedentaires=_profil(),
        destination=tmp_path / "d.json",
    )

    dossiers = lister_dossiers_fiscaux(tmp_path)
    assert len(dossiers) == 1
    assert (
        dossiers[0].cotisations_excedentaires.assurance_emploi
        == Decimal("700.00")
    )
