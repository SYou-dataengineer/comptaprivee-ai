import json
from decimal import Decimal

import pytest

from src.comptaprivee.tax_case_storage import (
    charger_dossier_fiscal,
    lister_dossiers_fiscaux,
    sauvegarder_dossier_fiscal,
)
from src.comptaprivee.tax_living_alone_2025 import (
    PersonneVivantSeule2025,
)
from tests.test_tax_case_storage import _dossier


def _profil():
    return PersonneVivantSeule2025(
        reclamer_montant=True,
        revenu_familial_net=Decimal("50095.00"),
        personne_vivant_seule_toute_annee=True,
        habitation_maintenue_par_contribuable=True,
        seulement_personnes_autorisees_dans_habitation=True,
        aucun_conjoint_31_decembre_2025=True,
        resident_quebec_canada_toute_annee=True,
        reclamer_additionnel_monoparental=True,
        enfant_majeur_etudes_admissible=True,
        aucun_droit_allocation_famille_decembre=True,
        mois_allocation_famille_2025=3,
        aucun_montant_age_ou_retraite=True,
        documents_justificatifs_confirmes=True,
        valide_par_comptable=True,
        source="Bail et factures validés",
    )


def test_personne_vivant_seule_roundtrip_json(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        personne_vivant_seule=_profil(),
        destination=tmp_path / "d.json",
    )
    x = charger_dossier_fiscal(p).personne_vivant_seule

    assert x.reclamer_montant is True
    assert x.revenu_familial_net == Decimal("50095.00")
    assert x.reclamer_additionnel_monoparental is True
    assert x.mois_allocation_famille_2025 == 3
    assert x.source == "Bail et factures validés"


def test_json_conserve_confirmations(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        personne_vivant_seule=_profil(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    valeur = brut["personne_vivant_seule"]

    assert valeur["personne_vivant_seule_toute_annee"] is True
    assert valeur["habitation_maintenue_par_contribuable"] is True
    assert valeur["seulement_personnes_autorisees_dans_habitation"] is True
    assert valeur["aucun_conjoint_31_decembre_2025"] is True
    assert valeur["resident_quebec_canada_toute_annee"] is True
    assert valeur["enfant_majeur_etudes_admissible"] is True
    assert valeur["aucun_droit_allocation_famille_decembre"] is True
    assert valeur["aucun_montant_age_ou_retraite"] is True
    assert valeur["documents_justificatifs_confirmes"] is True
    assert valeur["valide_par_comptable"] is True


def test_ancien_json_sans_personne_vivant_seule_reste_compatible(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        destination=tmp_path / "ancien.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut.pop("personne_vivant_seule", None)
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    x = charger_dossier_fiscal(p).personne_vivant_seule
    assert x == PersonneVivantSeule2025()


def test_json_revenu_negatif_est_refuse(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        personne_vivant_seule=_profil(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["personne_vivant_seule"]["revenu_familial_net"] = "-1"
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="négatif"):
        charger_dossier_fiscal(p)


def test_json_validation_incomplete_est_refusee(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        personne_vivant_seule=_profil(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["personne_vivant_seule"][
        "documents_justificatifs_confirmes"
    ] = False
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="documents justificatifs"):
        charger_dossier_fiscal(p)


def test_json_type_invalide_est_refuse(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["personne_vivant_seule"] = ["invalide"]
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="personne vivant seule"):
        charger_dossier_fiscal(p)


def test_liste_dossiers_recharge_personne_vivant_seule(tmp_path):
    sauvegarder_dossier_fiscal(
        _dossier(),
        personne_vivant_seule=_profil(),
        destination=tmp_path / "d.json",
    )

    dossiers = lister_dossiers_fiscaux(tmp_path)
    assert len(dossiers) == 1
    assert dossiers[0].personne_vivant_seule.reclamer_montant is True
    assert (
        dossiers[0].personne_vivant_seule.mois_allocation_famille_2025
        == 3
    )
