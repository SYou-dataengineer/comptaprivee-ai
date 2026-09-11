import json
from decimal import Decimal

import pytest

from src.comptaprivee.tax_case_storage import (
    charger_dossier_fiscal,
    lister_dossiers_fiscaux,
    sauvegarder_dossier_fiscal,
)
from src.comptaprivee.tax_tuition_2025 import FraisScolarite2025
from tests.test_tax_case_storage import _dossier


def _scolarite_3000():
    return FraisScolarite2025(
        montant_admissible_federal=Decimal("3000"),
        montant_admissible_quebec=Decimal("3000"),
        source_federale="T2202 - établissement admissible",
        source_quebec="Reçu officiel - établissement admissible",
        valide_par_comptable=True,
        piece_federale_confirmee=True,
        recu_officiel_quebec_confirme=True,
        seuil_100_confirme=True,
        remboursements_soustraits=True,
        frais_2025_uniquement=True,
        aucun_report_anterieur=True,
        aucun_transfert=True,
        credit_canadien_formation_non_reclame=True,
        profil_resident_quebec_simple=True,
    )


def test_scolarite_roundtrip_json(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        frais_scolarite=_scolarite_3000(),
        destination=tmp_path / "d.json",
    )
    x = charger_dossier_fiscal(p).frais_scolarite
    assert x.montant_admissible_federal == Decimal("3000")
    assert x.montant_admissible_quebec == Decimal("3000")


def test_ancien_json_sans_scolarite_reste_compatible(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        destination=tmp_path / "ancien.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut.pop("frais_scolarite", None)
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    x = charger_dossier_fiscal(p).frais_scolarite
    assert x.montant_admissible_federal == Decimal("0")
    assert x.montant_admissible_quebec == Decimal("0")


def test_json_conserve_validations_scolarite(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        frais_scolarite=_scolarite_3000(),
        destination=tmp_path / "d.json",
    )
    frais = json.loads(
        p.read_text(encoding="utf-8")
    )["frais_scolarite"]
    assert frais["valide_par_comptable"] is True
    assert frais["piece_federale_confirmee"] is True
    assert frais["recu_officiel_quebec_confirme"] is True
    assert frais["seuil_100_confirme"] is True
    assert frais["remboursements_soustraits"] is True
    assert frais["frais_2025_uniquement"] is True
    assert frais["aucun_report_anterieur"] is True
    assert frais["aucun_transfert"] is True
    assert frais["credit_canadien_formation_non_reclame"] is True
    assert frais["profil_resident_quebec_simple"] is True


def test_json_scolarite_negative_refusee(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        frais_scolarite=_scolarite_3000(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["frais_scolarite"]["montant_admissible_federal"] = "-10"
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        charger_dossier_fiscal(p)


def test_json_scolarite_validation_incomplete_refusee(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        frais_scolarite=_scolarite_3000(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["frais_scolarite"]["seuil_100_confirme"] = False
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        charger_dossier_fiscal(p)


def test_liste_dossiers_recharge_scolarite(tmp_path):
    sauvegarder_dossier_fiscal(
        _dossier(),
        frais_scolarite=_scolarite_3000(),
        destination=tmp_path / "d.json",
    )
    dossiers = lister_dossiers_fiscaux(tmp_path)
    assert len(dossiers) == 1
    assert (
        dossiers[0].frais_scolarite.montant_admissible_quebec
        == Decimal("3000")
    )
