import json
from decimal import Decimal

import pytest

from src.comptaprivee.tax_case_storage import (
    charger_dossier_fiscal,
    lister_dossiers_fiscaux,
    sauvegarder_dossier_fiscal,
)
from src.comptaprivee.tax_medical_expenses_2025 import FraisMedicaux2025
from tests.test_tax_case_storage import _dossier


def _frais_3000():
    return FraisMedicaux2025(
        montant_admissible_federal=Decimal("3000"),
        montant_admissible_quebec=Decimal("3000"),
        source_federale="Reçus médicaux vérifiés — ARC",
        source_quebec="Reçus médicaux vérifiés — Revenu Québec",
        valide_par_comptable=True,
        recus_confirmes=True,
        remboursements_soustraits=True,
        periode_12_mois_fin_2025_confirmee=True,
        aucune_periode_deja_reclamee=True,
        profil_individuel_sans_conjoint_dependant=True,
    )


def test_frais_medicaux_roundtrip_json(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        frais_medicaux=_frais_3000(),
        destination=tmp_path / "d.json",
    )
    x = charger_dossier_fiscal(p).frais_medicaux

    assert x.montant_admissible_federal == Decimal("3000")
    assert x.montant_admissible_quebec == Decimal("3000")
    assert x.source_federale == "Reçus médicaux vérifiés — ARC"
    assert x.source_quebec == "Reçus médicaux vérifiés — Revenu Québec"


def test_ancien_json_sans_frais_medicaux_reste_compatible(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        destination=tmp_path / "ancien.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut.pop("frais_medicaux", None)
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    x = charger_dossier_fiscal(p).frais_medicaux
    assert x.montant_admissible_federal == Decimal("0")
    assert x.montant_admissible_quebec == Decimal("0")


def test_json_conserve_validations_medicales(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        frais_medicaux=_frais_3000(),
        destination=tmp_path / "d.json",
    )
    frais = json.loads(
        p.read_text(encoding="utf-8")
    )["frais_medicaux"]

    assert frais["valide_par_comptable"] is True
    assert frais["recus_confirmes"] is True
    assert frais["remboursements_soustraits"] is True
    assert frais["periode_12_mois_fin_2025_confirmee"] is True
    assert frais["aucune_periode_deja_reclamee"] is True
    assert frais["profil_individuel_sans_conjoint_dependant"] is True


def test_json_frais_medicaux_negatifs_refuses(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        frais_medicaux=_frais_3000(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["frais_medicaux"]["montant_admissible_federal"] = "-10"
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        charger_dossier_fiscal(p)


def test_json_frais_medicaux_validation_incomplete_refusee(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        frais_medicaux=_frais_3000(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["frais_medicaux"]["recus_confirmes"] = False
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        charger_dossier_fiscal(p)


def test_liste_dossiers_recharge_frais_medicaux(tmp_path):
    sauvegarder_dossier_fiscal(
        _dossier(),
        frais_medicaux=_frais_3000(),
        destination=tmp_path / "d.json",
    )

    dossiers = lister_dossiers_fiscaux(tmp_path)
    assert len(dossiers) == 1
    assert (
        dossiers[0].frais_medicaux.montant_admissible_quebec
        == Decimal("3000")
    )
