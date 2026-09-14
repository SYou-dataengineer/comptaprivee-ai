import json
from decimal import Decimal

import pytest

from src.comptaprivee.tax_case_storage import (
    charger_dossier_fiscal,
    lister_dossiers_fiscaux,
    sauvegarder_dossier_fiscal,
)
from src.comptaprivee.tax_federal_caregiver_spouse_dependant_2025 import (
    AidantNaturelConjointOuPersonneChargeFederal2025,
)
from tests.test_tax_case_storage import _dossier
from tests.test_tax_federal_caregiver_spouse_dependant_integration_2025 import (
    _30425_conjoint,
    _30425_personne_charge,
)
from tests.test_tax_federal_eligible_dependant_caregiver_base_2025 import (
    _profil_18_plus_infirmite,
)
from tests.test_tax_federal_spouse_caregiver_base_2025 import (
    _profil_infirmite,
)


def test_30425_conjoint_roundtrip_json(tmp_path):
    profil = _30425_conjoint()
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        aidant_conjoint_personne_charge_federal=profil,
        destination=tmp_path / "d.json",
    )

    x = charger_dossier_fiscal(
        p
    ).aidant_conjoint_personne_charge_federal

    assert x == profil
    assert x.revenu_net_personne_ligne_23600 == Decimal("12000")
    assert x.montant_reclame_ligne_30300_ou_30400 == Decimal("6816")


def test_30425_personne_charge_roundtrip_json(tmp_path):
    profil = _30425_personne_charge()
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        aidant_conjoint_personne_charge_federal=profil,
        destination=tmp_path / "d.json",
    )

    x = charger_dossier_fiscal(
        p
    ).aidant_conjoint_personne_charge_federal

    assert x == profil
    assert x.personne_charge_18_ans_ou_plus_si_applicable is True


def test_json_conserve_tous_les_champs_30425(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        aidant_conjoint_personne_charge_federal=_30425_conjoint(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    valeur = brut["aidant_conjoint_personne_charge_federal"]

    assert valeur["reclamer_montant"] is True
    assert valeur["type_personne"] == "conjoint"
    assert valeur["revenu_net_personne_ligne_23600"] == "12000"
    assert valeur["montant_reclame_ligne_30300_ou_30400"] == "6816"
    assert valeur["personne_soutenue_en_2025"] is True
    assert valeur["infirmite_physique_ou_mentale"] is True
    assert valeur["dependance_due_uniquement_a_infirmite"] is True
    assert valeur["dependance_periode_considerable"] is True
    assert valeur["montant_base_2687_inclus"] is True
    assert valeur["un_seul_reclamant_30425"] is True
    assert valeur["aucune_reclamation_partagee"] is True
    assert valeur["preuve_medicale_ou_t2201_confirmee"] is True
    assert valeur["valide_par_comptable"] is True
    assert valeur["source_personne"]


def test_ancien_json_sans_30425_reste_compatible(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        destination=tmp_path / "ancien.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut.pop("aidant_conjoint_personne_charge_federal", None)
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    x = charger_dossier_fiscal(
        p
    ).aidant_conjoint_personne_charge_federal

    assert x == AidantNaturelConjointOuPersonneChargeFederal2025()


def test_json_type_30425_invalide_est_refuse(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["aidant_conjoint_personne_charge_federal"] = ["invalide"]
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="30425|aidant naturel"):
        charger_dossier_fiscal(p)


def test_json_preuve_medicale_30425_incomplete_est_refusee(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        aidant_conjoint_personne_charge_federal=_30425_conjoint(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["aidant_conjoint_personne_charge_federal"][
        "preuve_medicale_ou_t2201_confirmee"
    ] = False
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="preuve médicale"):
        charger_dossier_fiscal(p)


def test_stockage_conserve_nouveaux_champs_conjoint_30300(tmp_path):
    profil = _profil_infirmite(
        revenu_net_contribuable_ligne_23600=Decimal("51515.00")
    )
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        montant_conjoint_federal=profil,
        destination=tmp_path / "d.json",
    )

    x = charger_dossier_fiscal(p).montant_conjoint_federal

    assert x.conjoint_avec_infirmite is True
    assert x.dependance_due_uniquement_a_infirmite is True
    assert x.dependance_periode_considerable is True
    assert x.aidant_naturel_base_2687_inclus is True
    assert x.preuve_medicale_ou_t2201_confirmee is True


def test_stockage_conserve_nouveaux_champs_personne_charge_30400(tmp_path):
    profil = _profil_18_plus_infirmite(
        revenu_net_contribuable_ligne_23600=Decimal("51515.00")
    )
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        personne_charge_admissible_federale=profil,
        destination=tmp_path / "d.json",
    )

    x = charger_dossier_fiscal(
        p
    ).personne_charge_admissible_federale

    assert x.personne_charge_18_ans_ou_plus is True
    assert x.personne_charge_avec_infirmite is True
    assert x.dependance_due_uniquement_a_infirmite is True
    assert x.dependance_periode_considerable is True
    assert x.aidant_naturel_base_2687_inclus is True
    assert x.preuve_medicale_ou_t2201_confirmee is True


def test_liste_dossiers_recharge_30425(tmp_path):
    sauvegarder_dossier_fiscal(
        _dossier(),
        aidant_conjoint_personne_charge_federal=_30425_conjoint(),
        destination=tmp_path / "d.json",
    )

    dossiers = lister_dossiers_fiscaux(tmp_path)

    assert len(dossiers) == 1
    profil = dossiers[0].aidant_conjoint_personne_charge_federal
    assert profil.reclamer_montant is True
    assert profil.type_personne == "conjoint"
