import json

import pytest

from src.comptaprivee.tax_case_storage import (
    charger_dossier_fiscal,
    lister_dossiers_fiscaux,
    sauvegarder_dossier_fiscal,
)
from src.comptaprivee.tax_disability_2025 import CreditDeficience2025
from tests.test_tax_case_storage import _dossier


def _deficience_complete():
    return CreditDeficience2025(
        reclamer_federal=True,
        reclamer_quebec=True,
        source_federale="T2201 / approbation ARC",
        source_quebec="Attestation professionnelle Québec",
        valide_par_comptable=True,
        age_18_plus_au_1_janvier_2025=True,
        deficience_12_mois_confirmee=True,
        profil_soi_meme_resident_quebec=True,
        ciph_approuve_arc=True,
        attestation_quebec_confirmee=True,
        aucun_conflit_soins_prepose_etablissement=True,
        aucun_transfert_federal=True,
    )


def test_deficience_roundtrip_json(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        credit_deficience=_deficience_complete(),
        destination=tmp_path / "d.json",
    )
    x = charger_dossier_fiscal(p).credit_deficience

    assert x.reclamer_federal is True
    assert x.reclamer_quebec is True
    assert x.source_federale == "T2201 / approbation ARC"
    assert x.source_quebec == "Attestation professionnelle Québec"


def test_ancien_json_sans_deficience_reste_compatible(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        destination=tmp_path / "ancien.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut.pop("credit_deficience", None)
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    x = charger_dossier_fiscal(p).credit_deficience
    assert x.reclamer_federal is False
    assert x.reclamer_quebec is False


def test_json_conserve_validations_deficience(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        credit_deficience=_deficience_complete(),
        destination=tmp_path / "d.json",
    )
    credit = json.loads(
        p.read_text(encoding="utf-8")
    )["credit_deficience"]

    assert credit["valide_par_comptable"] is True
    assert credit["age_18_plus_au_1_janvier_2025"] is True
    assert credit["deficience_12_mois_confirmee"] is True
    assert credit["profil_soi_meme_resident_quebec"] is True
    assert credit["ciph_approuve_arc"] is True
    assert credit["attestation_quebec_confirmee"] is True
    assert credit["aucun_conflit_soins_prepose_etablissement"] is True
    assert credit["aucun_transfert_federal"] is True


def test_json_deficience_ciph_incomplet_refuse(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        credit_deficience=_deficience_complete(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["credit_deficience"]["ciph_approuve_arc"] = False
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="CIPH"):
        charger_dossier_fiscal(p)


def test_json_deficience_attestation_quebec_incomplete_refuse(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        credit_deficience=_deficience_complete(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["credit_deficience"]["attestation_quebec_confirmee"] = False
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="attestation"):
        charger_dossier_fiscal(p)


def test_liste_dossiers_recharge_deficience(tmp_path):
    sauvegarder_dossier_fiscal(
        _dossier(),
        credit_deficience=_deficience_complete(),
        destination=tmp_path / "d.json",
    )

    dossiers = lister_dossiers_fiscaux(tmp_path)
    assert len(dossiers) == 1
    assert dossiers[0].credit_deficience.reclamer_federal is True
    assert dossiers[0].credit_deficience.reclamer_quebec is True
