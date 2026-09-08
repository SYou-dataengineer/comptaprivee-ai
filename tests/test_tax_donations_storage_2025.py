import json
from decimal import Decimal

import pytest

from src.comptaprivee.tax_case_storage import (
    charger_dossier_fiscal,
    lister_dossiers_fiscaux,
    sauvegarder_dossier_fiscal,
)
from src.comptaprivee.tax_donations_2025 import DonsBienfaisance2025
from tests.test_tax_case_storage import _dossier


def _dons_1000():
    return DonsBienfaisance2025(
        montant_admissible_federal=Decimal("1000"),
        montant_admissible_quebec=Decimal("1000"),
        source_federale="Reçu officiel organisme enregistré",
        source_quebec="Reçu officiel organisme enregistré",
        valide_par_comptable=True,
        donataire_reconnu_confirme=True,
        dons_monetaires_2025_uniquement=True,
        aucun_report_anterieur=True,
        inclut_dons_jan_fev_2025=False,
        dons_jan_fev_deja_reclames_2024=False,
    )


def test_dons_roundtrip_json(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        dons_bienfaisance=_dons_1000(),
        destination=tmp_path / "d.json",
    )
    x = charger_dossier_fiscal(p).dons_bienfaisance

    assert x.montant_admissible_federal == Decimal("1000")
    assert x.montant_admissible_quebec == Decimal("1000")
    assert x.source_federale == "Reçu officiel organisme enregistré"
    assert x.source_quebec == "Reçu officiel organisme enregistré"


def test_ancien_json_sans_dons_reste_compatible(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        destination=tmp_path / "ancien.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut.pop("dons_bienfaisance", None)
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    x = charger_dossier_fiscal(p).dons_bienfaisance
    assert x.montant_admissible_federal == Decimal("0")
    assert x.montant_admissible_quebec == Decimal("0")


def test_json_conserve_validations_et_sources(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        dons_bienfaisance=_dons_1000(),
        destination=tmp_path / "d.json",
    )
    dons = json.loads(
        p.read_text(encoding="utf-8")
    )["dons_bienfaisance"]

    assert dons["valide_par_comptable"] is True
    assert dons["donataire_reconnu_confirme"] is True
    assert dons["dons_monetaires_2025_uniquement"] is True
    assert dons["aucun_report_anterieur"] is True
    assert dons["source_federale"] == "Reçu officiel organisme enregistré"
    assert dons["source_quebec"] == "Reçu officiel organisme enregistré"


def test_json_dons_negatifs_refuse(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        dons_bienfaisance=_dons_1000(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["dons_bienfaisance"]["montant_admissible_federal"] = "-10"
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        charger_dossier_fiscal(p)


def test_dons_jan_fev_deja_reclames_2024_refuses_au_chargement(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        dons_bienfaisance=_dons_1000(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["dons_bienfaisance"]["inclut_dons_jan_fev_2025"] = True
    brut["dons_bienfaisance"]["dons_jan_fev_deja_reclames_2024"] = True
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        charger_dossier_fiscal(p)


def test_liste_dossiers_recharge_dons(tmp_path):
    sauvegarder_dossier_fiscal(
        _dossier(),
        dons_bienfaisance=_dons_1000(),
        destination=tmp_path / "d.json",
    )

    dossiers = lister_dossiers_fiscaux(tmp_path)
    assert len(dossiers) == 1
    assert (
        dossiers[0].dons_bienfaisance.montant_admissible_quebec
        == Decimal("1000")
    )
