from decimal import Decimal

import pytest

from src.comptaprivee.tax_federal_spouse_2025 import (
    MONTANT_AIDANT_CONJOINT_2025,
    MontantConjointFederal2025,
    credit_federal_montant_conjoint_2025,
    montant_base_aidant_conjoint_30300_2025,
    montant_ligne_30300_2025,
    valider_montant_conjoint_federal_2025,
)


def _profil_infirmite(**modifications):
    valeurs = {
        "reclamer_montant": True,
        "revenu_net_contribuable_ligne_23600": Decimal("52000"),
        "revenu_net_conjoint_2025": Decimal("12000"),
        "contribuable_resident_canada_toute_annee": True,
        "relation_conjoint_confirmee": True,
        "conjoint_soutenu_2025": True,
        "meme_conjoint_toute_annee_2025": True,
        "aucune_separation_2025": True,
        "conjoint_resident_canada_toute_annee": True,
        "aucun_paiement_pension_alimentaire": True,
        "aucune_infirmite_conjoint": False,
        "conjoint_avec_infirmite": True,
        "dependance_due_uniquement_a_infirmite": True,
        "dependance_periode_considerable": True,
        "aidant_naturel_base_2687_inclus": True,
        "preuve_medicale_ou_t2201_confirmee": True,
        "un_seul_conjoint_reclame_montant": True,
        "revenu_conjoint_confirme": True,
        "valide_par_comptable": True,
        "source_conjoint": (
            "État civil, revenu ligne 23600 et preuve médicale validés"
        ),
    }
    valeurs.update(modifications)
    return MontantConjointFederal2025(**valeurs)


def test_constante_base_aidant_conjoint_2025():
    assert MONTANT_AIDANT_CONJOINT_2025 == Decimal("2687")


def test_base_2687_est_incluse_pour_conjoint_avec_infirmite():
    profil = _profil_infirmite()

    assert (
        montant_base_aidant_conjoint_30300_2025(profil)
        == Decimal("2687")
    )


def test_ligne_30300_avec_base_aidant_2687():
    profil = _profil_infirmite()

    assert montant_ligne_30300_2025(profil) == Decimal("6816.00")
    assert credit_federal_montant_conjoint_2025(
        profil
    ) == Decimal("988.32")


def test_infirmite_exige_dependance_due_a_infirmite():
    with pytest.raises(ValueError, match="due à l'infirmité"):
        valider_montant_conjoint_federal_2025(
            _profil_infirmite(
                dependance_due_uniquement_a_infirmite=False
            )
        )


def test_infirmite_exige_dependance_periode_considerable():
    with pytest.raises(ValueError, match="période considérable"):
        valider_montant_conjoint_federal_2025(
            _profil_infirmite(
                dependance_periode_considerable=False
            )
        )


def test_infirmite_exige_base_2687():
    with pytest.raises(ValueError, match="2 687"):
        valider_montant_conjoint_federal_2025(
            _profil_infirmite(
                aidant_naturel_base_2687_inclus=False
            )
        )


def test_infirmite_exige_preuve_medicale_ou_t2201():
    with pytest.raises(ValueError, match="preuve médicale"):
        valider_montant_conjoint_federal_2025(
            _profil_infirmite(
                preuve_medicale_ou_t2201_confirmee=False
            )
        )


def test_drapeaux_infirmite_contradictoires_refuses():
    with pytest.raises(ValueError, match="contradictoire"):
        valider_montant_conjoint_federal_2025(
            _profil_infirmite(
                aucune_infirmite_conjoint=True
            )
        )


def test_profil_sans_infirmite_ne_peut_pas_activer_base_2687():
    profil = _profil_infirmite(
        conjoint_avec_infirmite=False,
        aucune_infirmite_conjoint=True,
        dependance_due_uniquement_a_infirmite=False,
        dependance_periode_considerable=False,
        preuve_medicale_ou_t2201_confirmee=False,
        aidant_naturel_base_2687_inclus=True,
    )

    with pytest.raises(ValueError, match="aidant naturel"):
        valider_montant_conjoint_federal_2025(profil)
