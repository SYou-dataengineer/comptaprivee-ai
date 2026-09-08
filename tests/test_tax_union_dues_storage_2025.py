import json
from decimal import Decimal

import pytest

from src.comptaprivee.tax_case_storage import (
    charger_dossier_fiscal,
    lister_dossiers_fiscaux,
    sauvegarder_dossier_fiscal,
)
from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
)
from src.comptaprivee.tax_union_dues_2025 import (
    CotisationsSyndicalesProfessionnelles2025,
)
from tests.test_tax_case_storage import _dossier


def _cotisations_600():
    return CotisationsSyndicalesProfessionnelles2025(
        montant_federal_admissible=Decimal("600"),
        montant_quebec_admissible=Decimal("600"),
        source_federale="T4 case 44",
        source_quebec="RL-1 case F",
        valide_par_comptable=True,
        sources_dedoublonnees=True,
    )


def test_cotisations_roundtrip_json(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        cotisations_syndicales=_cotisations_600(),
        destination=tmp_path / "d.json",
    )
    x = charger_dossier_fiscal(p).cotisations_syndicales

    assert x.montant_federal_admissible == Decimal("600")
    assert x.montant_quebec_admissible == Decimal("600")
    assert x.source_federale == "T4 case 44"
    assert x.source_quebec == "RL-1 case F"
    assert x.valide_par_comptable is True
    assert x.sources_dedoublonnees is True


def test_ancien_json_sans_cotisations_reste_compatible(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        destination=tmp_path / "ancien.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut.pop("cotisations_syndicales", None)
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    x = charger_dossier_fiscal(p).cotisations_syndicales
    assert x.montant_federal_admissible == Decimal("0")
    assert x.montant_quebec_admissible == Decimal("0")


def test_json_conserve_sources_et_montants(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        cotisations_syndicales=_cotisations_600(),
        destination=tmp_path / "d.json",
    )
    cot = json.loads(
        p.read_text(encoding="utf-8")
    )["cotisations_syndicales"]

    assert cot["montant_federal_admissible"] == "600"
    assert cot["montant_quebec_admissible"] == "600"
    assert cot["source_federale"] == "T4 case 44"
    assert cot["source_quebec"] == "RL-1 case F"


def test_json_cotisations_invalides_refuse(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        cotisations_syndicales=_cotisations_600(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["cotisations_syndicales"][
        "montant_federal_admissible"
    ] = "-10"
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        charger_dossier_fiscal(p)


def test_estimation_et_cotisations_sauvegardees_ensemble(tmp_path):
    dossier = _dossier()
    cot = _cotisations_600()
    estimation = calculer_estimation_fiscale_2025(
        dossier,
        cotisations_syndicales=cot,
    )

    p = sauvegarder_dossier_fiscal(
        dossier,
        estimation=estimation,
        cotisations_syndicales=cot,
        destination=tmp_path / "d.json",
    )
    x = charger_dossier_fiscal(p)

    assert x.estimation is not None
    assert x.estimation.montant == Decimal("5743.70")
    assert (
        x.cotisations_syndicales.montant_federal_admissible
        == Decimal("600")
    )


def test_liste_dossiers_recharge_cotisations(tmp_path):
    sauvegarder_dossier_fiscal(
        _dossier(),
        cotisations_syndicales=_cotisations_600(),
        destination=tmp_path / "d.json",
    )

    dossiers = lister_dossiers_fiscaux(tmp_path)
    assert len(dossiers) == 1
    assert (
        dossiers[0]
        .cotisations_syndicales
        .montant_quebec_admissible
        == Decimal("600")
    )
