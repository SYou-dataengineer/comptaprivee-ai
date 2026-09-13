import json

import pytest

from src.comptaprivee.tax_case_storage import (
    charger_dossier_fiscal,
    lister_dossiers_fiscaux,
    sauvegarder_dossier_fiscal,
)
from src.comptaprivee.tax_federal_caregiver_child_2025 import (
    AidantNaturelEnfantMoins18Federal2025,
)
from tests.test_tax_case_storage import _dossier
from tests.test_tax_federal_caregiver_child_integration_2025 import (
    _profil_aidant_enfant,
)


def test_aidant_enfant_roundtrip_json(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        aidant_enfant_federal=_profil_aidant_enfant(),
        destination=tmp_path / "d.json",
    )

    x = charger_dossier_fiscal(p).aidant_enfant_federal

    assert x.reclamer_montant is True
    assert x.enfant_biologique_ou_adopte is True
    assert x.enfant_moins_18_fin_2025 is True
    assert x.infirmite_physique_ou_mentale is True
    assert x.dependance_longue_continue_duree_indeterminee is True
    assert x.besoin_aide_beaucoup_plus_que_meme_age is True
    assert x.enfant_avec_deux_parents_toute_annee is True
    assert x.aucune_garde_partagee is True
    assert x.aucune_pension_alimentaire is True
    assert x.aucun_autre_reclamant_30500 is True
    assert x.aucun_transfert_conjoint_32600 is True
    assert x.preuve_medicale_ou_t2201_confirmee is True
    assert x.valide_par_comptable is True
    assert (
        x.source_enfant
        == "Lien familial, résidence et preuve médicale validés"
    )


def test_json_conserve_tous_les_champs_aidant_enfant(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        aidant_enfant_federal=_profil_aidant_enfant(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    valeur = brut["aidant_enfant_federal"]

    assert valeur["reclamer_montant"] is True
    assert valeur["enfant_biologique_ou_adopte"] is True
    assert valeur["enfant_moins_18_fin_2025"] is True
    assert valeur["infirmite_physique_ou_mentale"] is True
    assert (
        valeur["dependance_longue_continue_duree_indeterminee"]
        is True
    )
    assert (
        valeur["besoin_aide_beaucoup_plus_que_meme_age"]
        is True
    )
    assert (
        valeur["enfant_avec_deux_parents_toute_annee"]
        is True
    )
    assert valeur["aucune_garde_partagee"] is True
    assert valeur["aucune_pension_alimentaire"] is True
    assert valeur["aucun_autre_reclamant_30500"] is True
    assert valeur["aucun_transfert_conjoint_32600"] is True
    assert valeur["preuve_medicale_ou_t2201_confirmee"] is True
    assert valeur["valide_par_comptable"] is True
    assert (
        valeur["source_enfant"]
        == "Lien familial, résidence et preuve médicale validés"
    )


def test_ancien_json_sans_aidant_enfant_reste_compatible(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        destination=tmp_path / "ancien.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut.pop("aidant_enfant_federal", None)
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    x = charger_dossier_fiscal(p).aidant_enfant_federal

    assert x == AidantNaturelEnfantMoins18Federal2025()


def test_json_type_aidant_enfant_invalide_est_refuse(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["aidant_enfant_federal"] = ["invalide"]
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="aidant naturel"):
        charger_dossier_fiscal(p)


def test_json_preuve_medicale_incomplete_est_refusee(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        aidant_enfant_federal=_profil_aidant_enfant(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["aidant_enfant_federal"][
        "preuve_medicale_ou_t2201_confirmee"
    ] = False
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="preuve médicale"):
        charger_dossier_fiscal(p)


def test_json_garde_partagee_non_supportee_est_refusee(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        aidant_enfant_federal=_profil_aidant_enfant(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["aidant_enfant_federal"]["aucune_garde_partagee"] = False
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="garde partagée"):
        charger_dossier_fiscal(p)


def test_liste_dossiers_recharge_aidant_enfant(tmp_path):
    sauvegarder_dossier_fiscal(
        _dossier(),
        aidant_enfant_federal=_profil_aidant_enfant(),
        destination=tmp_path / "d.json",
    )

    dossiers = lister_dossiers_fiscaux(tmp_path)

    assert len(dossiers) == 1
    profil = dossiers[0].aidant_enfant_federal
    assert profil.reclamer_montant is True
    assert profil.preuve_medicale_ou_t2201_confirmee is True
