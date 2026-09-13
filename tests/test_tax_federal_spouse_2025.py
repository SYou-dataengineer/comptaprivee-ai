from decimal import Decimal

import pytest

from src.comptaprivee.tax_federal_spouse_2025 import (
    SEUIL_PREMIERE_TRANCHE_FEDERALE_2025,
    TAUX_CREDIT_FEDERAL_2025,
    MontantConjointFederal2025,
    credit_federal_montant_conjoint_2025,
    integration_sans_credit_compensatoire_autorisee_2025,
    montant_ligne_30300_2025,
    valider_montant_conjoint_federal_2025,
)


def _profil(**modifications):
    valeurs = {
        "reclamer_montant": True,
        "revenu_net_contribuable_ligne_23600": Decimal("52000"),
        "revenu_net_conjoint_2025": Decimal("5000"),
        "contribuable_resident_canada_toute_annee": True,
        "relation_conjoint_confirmee": True,
        "conjoint_soutenu_2025": True,
        "meme_conjoint_toute_annee_2025": True,
        "aucune_separation_2025": True,
        "conjoint_resident_canada_toute_annee": True,
        "aucun_paiement_pension_alimentaire": True,
        "aucune_infirmite_conjoint": True,
        "un_seul_conjoint_reclame_montant": True,
        "revenu_conjoint_confirme": True,
        "valide_par_comptable": True,
        "source_conjoint": "État civil et revenu du conjoint validés",
    }
    valeurs.update(modifications)
    return MontantConjointFederal2025(**valeurs)


def test_constantes_2025():
    assert TAUX_CREDIT_FEDERAL_2025 == Decimal("0.145")
    assert SEUIL_PREMIERE_TRANCHE_FEDERALE_2025 == Decimal("57375")


def test_profil_vide_est_valide_et_retourne_zero():
    profil = MontantConjointFederal2025()

    assert valider_montant_conjoint_federal_2025(profil) == profil
    assert montant_ligne_30300_2025(profil) == 0
    assert credit_federal_montant_conjoint_2025(profil) == 0


def test_revenu_contribuable_negatif_refuse():
    with pytest.raises(ValueError, match="ligne 23600"):
        valider_montant_conjoint_federal_2025(
            _profil(
                revenu_net_contribuable_ligne_23600=Decimal("-1")
            )
        )


def test_revenu_conjoint_negatif_refuse():
    with pytest.raises(ValueError, match="conjoint"):
        valider_montant_conjoint_federal_2025(
            _profil(revenu_net_conjoint_2025=Decimal("-1"))
        )


@pytest.mark.parametrize(
    "champ,message",
    [
        (
            "contribuable_resident_canada_toute_annee",
            "résident du Canada",
        ),
        (
            "relation_conjoint_confirmee",
            "relation d'époux ou conjoint de fait",
        ),
        (
            "conjoint_soutenu_2025",
            "subvenu aux besoins",
        ),
        (
            "meme_conjoint_toute_annee_2025",
            "changements de conjoint",
        ),
        (
            "aucune_separation_2025",
            "séparations ou réconciliations",
        ),
        (
            "conjoint_resident_canada_toute_annee",
            "non-résident",
        ),
        (
            "aucun_paiement_pension_alimentaire",
            "pension alimentaire",
        ),
        (
            "aucune_infirmite_conjoint",
            "aidant naturel",
        ),
        (
            "un_seul_conjoint_reclame_montant",
            "Un seul époux",
        ),
        (
            "revenu_conjoint_confirme",
            "revenu net 2025 du conjoint",
        ),
        (
            "valide_par_comptable",
            "comptable",
        ),
    ],
)
def test_validations_profil_simple(champ, message):
    with pytest.raises(ValueError, match=message):
        valider_montant_conjoint_federal_2025(
            _profil(**{champ: False})
        )


def test_source_conjoint_obligatoire():
    with pytest.raises(ValueError, match="source"):
        valider_montant_conjoint_federal_2025(
            _profil(source_conjoint=" ")
        )


def test_ligne_30300_a_52000_et_conjoint_5000():
    assert montant_ligne_30300_2025(
        _profil()
    ) == Decimal("11129.00")


def test_credit_federal_a_52000_et_conjoint_5000():
    assert credit_federal_montant_conjoint_2025(
        _profil()
    ) == Decimal("1613.71")


def test_ligne_30300_zero_si_revenu_conjoint_egale_bpa():
    assert montant_ligne_30300_2025(
        _profil(revenu_net_conjoint_2025=Decimal("16129"))
    ) == 0


def test_ligne_30300_zero_si_revenu_conjoint_superieur_bpa():
    assert montant_ligne_30300_2025(
        _profil(revenu_net_conjoint_2025=Decimal("25000"))
    ) == 0


def test_ligne_30300_utilise_bpa_reduit_a_200000():
    assert montant_ligne_30300_2025(
        _profil(
            revenu_net_contribuable_ligne_23600=Decimal("200000"),
            revenu_net_conjoint_2025=Decimal("5000"),
        )
    ) == Decimal("10663.11")


def test_garde_fou_34990_sous_premiere_tranche():
    assert integration_sans_credit_compensatoire_autorisee_2025(
        Decimal("52000")
    ) is True


def test_garde_fou_34990_au_seuil():
    assert integration_sans_credit_compensatoire_autorisee_2025(
        Decimal("57375")
    ) is True


def test_garde_fou_34990_au_dessus():
    assert integration_sans_credit_compensatoire_autorisee_2025(
        Decimal("57375.01")
    ) is False


def test_garde_fou_revenu_imposable_negatif_refuse():
    with pytest.raises(ValueError, match="revenu imposable fédéral"):
        integration_sans_credit_compensatoire_autorisee_2025(
            Decimal("-1")
        )
