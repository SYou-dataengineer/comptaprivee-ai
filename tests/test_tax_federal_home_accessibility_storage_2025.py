
import json
from decimal import Decimal

import pytest

from src.comptaprivee.tax_case_storage import (
    charger_dossier_fiscal,
    lister_dossiers_fiscaux,
    sauvegarder_dossier_fiscal,
)
from src.comptaprivee.tax_federal_home_accessibility_2025 import (
    DepensesAccessibiliteDomiciliaireFederal2025,
)
from tests.test_tax_case_storage import _dossier
from tests.test_tax_federal_home_accessibility_2025 import _profil


def test_31285_roundtrip_json(tmp_path):
    profil = _profil()
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        accessibilite_domiciliaire_federale=profil,
        destination=tmp_path / "d.json",
    )
    x = charger_dossier_fiscal(p).accessibilite_domiciliaire_federale
    assert x == profil
    assert x.depenses_admissibles == Decimal("20000")
    assert x.source_renovation == profil.source_renovation


def test_ancien_json_sans_31285_reste_compatible(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        destination=tmp_path / "ancien.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut.pop("accessibilite_domiciliaire_federale", None)
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    x = charger_dossier_fiscal(p).accessibilite_domiciliaire_federale
    assert x == DepensesAccessibiliteDomiciliaireFederal2025()


def test_json_conserve_les_champs_31285(tmp_path):
    profil = _profil()
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        accessibilite_domiciliaire_federale=profil,
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    v = brut["accessibilite_domiciliaire_federale"]

    assert v["reclamer_montant"] is True
    assert v["depenses_admissibles"] == "20000"
    assert v["demande_pour_soi_meme"] is True
    assert v["age_65_plus_fin_annee"] is True
    assert v["logement_situe_au_canada"] is True
    assert v["logement_propriete_du_contribuable"] is True
    assert v["logement_normalement_habite_par_contribuable"] is True
    assert v["renovation_durable_et_integrante"] is True
    assert v["accessibilite_ou_reduction_risque_confirmee"] is True
    assert v["travaux_et_biens_2025_uniquement"] is True
    assert v["aucune_part_entreprise_ou_location"] is True
    assert v["aucun_partage_de_la_demande"] is True
    assert v["fournisseurs_lies_admissibles_confirme"] is True
    assert v["depenses_non_admissibles_exclues"] is True
    assert v["pieces_justificatives_conservees"] is True
    assert v["valide_par_comptable"] is True
    assert v["source_renovation"] == profil.source_renovation


def test_json_type_31285_invalide_est_refuse(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["accessibilite_domiciliaire_federale"] = ["invalide"]
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="31285|accessibilité"):
        charger_dossier_fiscal(p)


def test_json_depenses_31285_negatives_refusees(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        accessibilite_domiciliaire_federale=_profil(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["accessibilite_domiciliaire_federale"]["depenses_admissibles"] = "-1"
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="négatives"):
        charger_dossier_fiscal(p)


def test_json_depenses_31285_superieures_maximum_refusees(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        accessibilite_domiciliaire_federale=_profil(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["accessibilite_domiciliaire_federale"]["depenses_admissibles"] = "20000.01"
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="20 000"):
        charger_dossier_fiscal(p)


def test_json_age_ciph_revalide(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        accessibilite_domiciliaire_federale=_profil(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    v = brut["accessibilite_domiciliaire_federale"]
    v["age_65_plus_fin_annee"] = False
    v["admissible_ciph"] = False
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="65 ans|CIPH"):
        charger_dossier_fiscal(p)


def test_json_source_31285_vide_est_refusee(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        accessibilite_domiciliaire_federale=_profil(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["accessibilite_domiciliaire_federale"]["source_renovation"] = ""
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="source"):
        charger_dossier_fiscal(p)


def test_liste_dossiers_recharge_31285(tmp_path):
    sauvegarder_dossier_fiscal(
        _dossier(),
        accessibilite_domiciliaire_federale=_profil(),
        destination=tmp_path / "d.json",
    )
    dossiers = lister_dossiers_fiscaux(tmp_path)
    assert len(dossiers) == 1
    profil = dossiers[0].accessibilite_domiciliaire_federale
    assert profil.reclamer_montant is True
    assert profil.depenses_admissibles == Decimal("20000")
