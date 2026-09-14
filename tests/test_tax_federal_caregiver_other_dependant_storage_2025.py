import json
from decimal import Decimal

import pytest

from src.comptaprivee.tax_case_storage import (
    charger_dossier_fiscal,
    lister_dossiers_fiscaux,
    sauvegarder_dossier_fiscal,
)
from src.comptaprivee.tax_federal_caregiver_other_dependant_2025 import (
    AidantNaturelAutrePersonneChargeFederal2025,
)
from tests.test_tax_case_storage import _dossier
from tests.test_tax_federal_caregiver_other_dependant_2025 import _profil


def test_30450_roundtrip_json(tmp_path):
    profil = _profil()

    p = sauvegarder_dossier_fiscal(
        _dossier(),
        aidant_autre_personne_charge_federal=profil,
        destination=tmp_path / "d.json",
    )

    x = charger_dossier_fiscal(
        p
    ).aidant_autre_personne_charge_federal

    assert x == profil
    assert x.revenu_net_personne_ligne_23600 == Decimal("25000")
    assert x.lien_personne == "parent"


def test_json_conserve_tous_les_champs_30450(tmp_path):
    profil = _profil()

    p = sauvegarder_dossier_fiscal(
        _dossier(),
        aidant_autre_personne_charge_federal=profil,
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    valeur = brut["aidant_autre_personne_charge_federal"]

    assert valeur["reclamer_montant"] is True
    assert valeur["lien_personne"] == "parent"
    assert valeur["revenu_net_personne_ligne_23600"] == "25000"
    assert valeur["age_18_ans_ou_plus"] is True
    assert valeur["personne_soutenue_en_2025"] is True
    assert valeur["infirmite_physique_ou_mentale"] is True
    assert valeur["dependance_due_uniquement_a_infirmite"] is True
    assert valeur["dependance_periode_considerable"] is True
    assert valeur["resident_canada_au_moins_un_moment_2025"] is True
    assert valeur[
        "aucune_reclamation_ligne_30300_30400_pour_personne"
    ] is True
    assert valeur[
        "aucun_paiement_pension_alimentaire_pour_personne"
    ] is True
    assert valeur["aucun_partage_reclamation_30450"] is True
    assert valeur["preuve_medicale_ou_t2201_confirmee"] is True
    assert valeur["valide_par_comptable"] is True
    assert valeur["source_personne"]


def test_ancien_json_sans_30450_reste_compatible(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        destination=tmp_path / "ancien.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut.pop("aidant_autre_personne_charge_federal", None)
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    x = charger_dossier_fiscal(
        p
    ).aidant_autre_personne_charge_federal

    assert x == AidantNaturelAutrePersonneChargeFederal2025()


def test_json_type_30450_invalide_est_refuse(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["aidant_autre_personne_charge_federal"] = ["invalide"]
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="30450|aidant naturel"):
        charger_dossier_fiscal(p)


def test_json_revenu_30450_negatif_est_refuse(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["aidant_autre_personne_charge_federal"] = {
        "revenu_net_personne_ligne_23600": "-1"
    }
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="ligne 23600"):
        charger_dossier_fiscal(p)


def test_json_preuve_medicale_30450_incomplete_est_refusee(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        aidant_autre_personne_charge_federal=_profil(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["aidant_autre_personne_charge_federal"][
        "preuve_medicale_ou_t2201_confirmee"
    ] = False
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="preuve médicale"):
        charger_dossier_fiscal(p)


def test_json_lien_30450_invalide_est_refuse(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        aidant_autre_personne_charge_federal=_profil(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["aidant_autre_personne_charge_federal"][
        "lien_personne"
    ] = "cousin"
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="lien"):
        charger_dossier_fiscal(p)


def test_liste_dossiers_recharge_30450(tmp_path):
    sauvegarder_dossier_fiscal(
        _dossier(),
        aidant_autre_personne_charge_federal=_profil(),
        destination=tmp_path / "d.json",
    )

    dossiers = lister_dossiers_fiscaux(tmp_path)

    assert len(dossiers) == 1
    profil = dossiers[0].aidant_autre_personne_charge_federal
    assert profil.reclamer_montant is True
    assert profil.lien_personne == "parent"
    assert profil.revenu_net_personne_ligne_23600 == Decimal("25000")
