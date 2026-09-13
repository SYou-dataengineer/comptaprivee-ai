import json
from decimal import Decimal

import pytest

from src.comptaprivee.tax_case_storage import (
    charger_dossier_fiscal,
    lister_dossiers_fiscaux,
    sauvegarder_dossier_fiscal,
)
from src.comptaprivee.tax_federal_eligible_dependant_2025 import (
    MontantPersonneChargeAdmissibleFederal2025,
)
from tests.test_tax_case_storage import _dossier
from tests.test_tax_federal_eligible_dependant_integration_2025 import (
    _profil_personne_charge,
)


def test_personne_charge_roundtrip_json(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        personne_charge_admissible_federale=_profil_personne_charge(),
        destination=tmp_path / "d.json",
    )

    x = (
        charger_dossier_fiscal(p)
        .personne_charge_admissible_federale
    )

    assert x.reclamer_montant is True
    assert (
        x.revenu_net_contribuable_ligne_23600
        == Decimal("51515.00")
    )
    assert (
        x.revenu_net_personne_charge_2025
        == Decimal("4000")
    )
    assert x.personne_charge_est_enfant is True
    assert x.enfant_moins_18_fin_2025 is True
    assert x.valide_par_comptable is True
    assert (
        x.source_personne_charge
        == "État civil, résidence et revenu de l'enfant validés"
    )


def test_json_conserve_tous_les_champs_personne_charge(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        personne_charge_admissible_federale=_profil_personne_charge(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    valeur = brut["personne_charge_admissible_federale"]

    assert valeur["reclamer_montant"] is True
    assert (
        valeur["revenu_net_contribuable_ligne_23600"]
        == "51515.00"
    )
    assert valeur["revenu_net_personne_charge_2025"] == "4000"
    assert (
        valeur["contribuable_resident_canada_toute_annee"]
        is True
    )
    assert valeur["aucun_epoux_conjoint_2025"] is True
    assert valeur["personne_charge_est_enfant"] is True
    assert valeur["enfant_moins_18_fin_2025"] is True
    assert valeur["aucune_infirmite_enfant"] is True
    assert valeur["enfant_soutenu_2025"] is True
    assert valeur["enfant_a_vecu_avec_contribuable"] is True
    assert valeur["habitation_maintenue_par_contribuable"] is True
    assert valeur["enfant_resident_canada_toute_annee"] is True
    assert valeur["aucune_garde_partagee"] is True
    assert valeur["aucun_paiement_pension_alimentaire"] is True
    assert valeur["un_seul_montant_30400_par_menage"] is True
    assert valeur["aucun_autre_reclamant_30400"] is True
    assert valeur["revenu_personne_charge_confirme"] is True
    assert valeur["valide_par_comptable"] is True
    assert (
        valeur["source_personne_charge"]
        == "État civil, résidence et revenu de l'enfant validés"
    )


def test_ancien_json_sans_personne_charge_reste_compatible(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        destination=tmp_path / "ancien.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut.pop("personne_charge_admissible_federale", None)
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    x = (
        charger_dossier_fiscal(p)
        .personne_charge_admissible_federale
    )
    assert x == MontantPersonneChargeAdmissibleFederal2025()


def test_json_revenu_personne_charge_negatif_refuse(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        personne_charge_admissible_federale=_profil_personne_charge(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["personne_charge_admissible_federale"][
        "revenu_net_personne_charge_2025"
    ] = "-1"
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="personne à charge"):
        charger_dossier_fiscal(p)


def test_json_validation_garde_partagee_incomplete_est_refusee(
    tmp_path,
):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        personne_charge_admissible_federale=_profil_personne_charge(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["personne_charge_admissible_federale"][
        "aucune_garde_partagee"
    ] = False
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="garde partagée"):
        charger_dossier_fiscal(p)


def test_json_type_personne_charge_invalide_est_refuse(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["personne_charge_admissible_federale"] = ["invalide"]
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="personne à charge"):
        charger_dossier_fiscal(p)


def test_liste_dossiers_recharge_personne_charge(tmp_path):
    sauvegarder_dossier_fiscal(
        _dossier(),
        personne_charge_admissible_federale=_profil_personne_charge(),
        destination=tmp_path / "d.json",
    )

    dossiers = lister_dossiers_fiscaux(tmp_path)

    assert len(dossiers) == 1
    profil = dossiers[0].personne_charge_admissible_federale
    assert profil.reclamer_montant is True
    assert (
        profil.revenu_net_personne_charge_2025
        == Decimal("4000")
    )
