import json
from decimal import Decimal

import pytest

from src.comptaprivee.tax_case_storage import (
    charger_dossier_fiscal,
    lister_dossiers_fiscaux,
    sauvegarder_dossier_fiscal,
)
from src.comptaprivee.tax_federal_home_buyers_2025 import (
    MontantAchatHabitationFederal2025,
)
from tests.test_tax_case_storage import _dossier
from tests.test_tax_federal_home_buyers_2025 import _profil


def test_31270_roundtrip_json(tmp_path):
    profil = _profil()

    p = sauvegarder_dossier_fiscal(
        _dossier(),
        achat_habitation_federal=profil,
        destination=tmp_path / "d.json",
    )

    x = charger_dossier_fiscal(p).achat_habitation_federal

    assert x == profil
    assert x.montant_reclame == Decimal("10000")
    assert x.source_habitation == profil.source_habitation


def test_json_conserve_tous_les_champs_31270(tmp_path):
    profil = _profil()

    p = sauvegarder_dossier_fiscal(
        _dossier(),
        achat_habitation_federal=profil,
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    valeur = brut["achat_habitation_federal"]

    assert valeur["reclamer_montant"] is True
    assert valeur["montant_reclame"] == "10000"
    assert valeur["acquisition_en_2025"] is True
    assert valeur["habitation_admissible"] is True
    assert valeur["habitation_situee_au_canada"] is True
    assert valeur[
        "habitation_enregistree_nom_contribuable_ou_conjoint"
    ] is True
    assert valeur["premier_acheteur_confirme"] is True
    assert valeur[
        "aucune_habitation_possedee_habitee_annee_achat_ou_4_precedentes"
    ] is True
    assert valeur[
        "intention_residence_principale_dans_un_an"
    ] is True
    assert valeur["aucun_partage_du_montant"] is True
    assert valeur["aucune_exception_handicap_utilisee"] is True
    assert valeur["pieces_justificatives_conservees"] is True
    assert valeur["valide_par_comptable"] is True
    assert valeur["source_habitation"]


def test_ancien_json_sans_31270_reste_compatible(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        destination=tmp_path / "ancien.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut.pop("achat_habitation_federal", None)
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    x = charger_dossier_fiscal(p).achat_habitation_federal

    assert x == MontantAchatHabitationFederal2025()


def test_json_type_31270_invalide_est_refuse(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["achat_habitation_federal"] = ["invalide"]
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="31270|habitation"):
        charger_dossier_fiscal(p)


def test_json_montant_31270_negatif_est_refuse(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["achat_habitation_federal"] = {
        "montant_reclame": "-1"
    }
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="31270|négatif"):
        charger_dossier_fiscal(p)


def test_json_montant_31270_superieur_maximum_est_refuse(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        achat_habitation_federal=_profil(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["achat_habitation_federal"][
        "montant_reclame"
    ] = "10000.01"
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="10 000"):
        charger_dossier_fiscal(p)


def test_json_validation_31270_incomplete_est_refusee(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        achat_habitation_federal=_profil(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["achat_habitation_federal"][
        "premier_acheteur_confirme"
    ] = False
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="première habitation"):
        charger_dossier_fiscal(p)


def test_json_source_31270_vide_est_refusee(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        achat_habitation_federal=_profil(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["achat_habitation_federal"]["source_habitation"] = ""
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="source"):
        charger_dossier_fiscal(p)


def test_liste_dossiers_recharge_31270(tmp_path):
    sauvegarder_dossier_fiscal(
        _dossier(),
        achat_habitation_federal=_profil(),
        destination=tmp_path / "d.json",
    )

    dossiers = lister_dossiers_fiscaux(tmp_path)

    assert len(dossiers) == 1
    profil = dossiers[0].achat_habitation_federal
    assert profil.reclamer_montant is True
    assert profil.montant_reclame == Decimal("10000")
    assert profil.premier_acheteur_confirme is True
