from decimal import Decimal

import pytest

from src.comptaprivee.tax_federal_caregiver_spouse_dependant_2025 import (
    BASE_CALCUL_30425_2025,
    MAXIMUM_LIGNE_30425_2025,
    MONTANT_BASE_AIDANT_30300_30400_2025,
    REVENU_NET_MIN_30425_2025,
    SEUIL_PREMIERE_TRANCHE_FEDERALE_2025,
    TAUX_CREDIT_FEDERAL_2025,
    TYPE_CONJOINT,
    TYPE_PERSONNE_CHARGE_ADMISSIBLE,
    AidantNaturelConjointOuPersonneChargeFederal2025,
    credit_federal_ligne_30425_2025,
    integration_sans_credit_compensatoire_autorisee_2025,
    montant_brut_avant_30300_30400_ligne_30425_2025,
    montant_ligne_30425_2025,
    valider_aidant_naturel_30425_2025,
)


def _profil_conjoint(**modifications):
    valeurs = {
        "reclamer_montant": True,
        "type_personne": TYPE_CONJOINT,
        "revenu_net_personne_ligne_23600": Decimal("20000"),
        "montant_reclame_ligne_30300_ou_30400": Decimal("3000"),
        "personne_soutenue_en_2025": True,
        "personne_charge_18_ans_ou_plus_si_applicable": False,
        "infirmite_physique_ou_mentale": True,
        "dependance_due_uniquement_a_infirmite": True,
        "dependance_periode_considerable": True,
        "montant_base_2687_inclus": True,
        "un_seul_reclamant_30425": True,
        "aucune_reclamation_partagee": True,
        "preuve_medicale_ou_t2201_confirmee": True,
        "valide_par_comptable": True,
        "source_personne": (
            "État civil, revenu ligne 23600 et preuve médicale validés"
        ),
    }
    valeurs.update(modifications)
    return AidantNaturelConjointOuPersonneChargeFederal2025(**valeurs)


def _profil_personne_charge(**modifications):
    valeurs = {
        "reclamer_montant": True,
        "type_personne": TYPE_PERSONNE_CHARGE_ADMISSIBLE,
        "revenu_net_personne_ligne_23600": Decimal("25000"),
        "montant_reclame_ligne_30300_ou_30400": Decimal("0"),
        "personne_soutenue_en_2025": True,
        "personne_charge_18_ans_ou_plus_si_applicable": True,
        "infirmite_physique_ou_mentale": True,
        "dependance_due_uniquement_a_infirmite": True,
        "dependance_periode_considerable": True,
        "montant_base_2687_inclus": True,
        "un_seul_reclamant_30425": True,
        "aucune_reclamation_partagee": True,
        "preuve_medicale_ou_t2201_confirmee": True,
        "valide_par_comptable": True,
        "source_personne": (
            "Lien familial, revenu ligne 23600 et preuve médicale validés"
        ),
    }
    valeurs.update(modifications)
    return AidantNaturelConjointOuPersonneChargeFederal2025(**valeurs)


def test_constantes_2025():
    assert REVENU_NET_MIN_30425_2025 == Decimal("8624")
    assert BASE_CALCUL_30425_2025 == Decimal("28798")
    assert MAXIMUM_LIGNE_30425_2025 == Decimal("8601")
    assert MONTANT_BASE_AIDANT_30300_30400_2025 == Decimal("2687")
    assert TAUX_CREDIT_FEDERAL_2025 == Decimal("0.145")
    assert SEUIL_PREMIERE_TRANCHE_FEDERALE_2025 == Decimal("57375")


def test_profil_vide_est_valide_et_retourne_zero():
    profil = AidantNaturelConjointOuPersonneChargeFederal2025()

    assert valider_aidant_naturel_30425_2025(profil) == profil
    assert montant_ligne_30425_2025(profil) == 0
    assert credit_federal_ligne_30425_2025(profil) == 0


def test_calcul_conjoint_30425():
    profil = _profil_conjoint()

    assert (
        montant_brut_avant_30300_30400_ligne_30425_2025(profil)
        == Decimal("8601")
    )
    assert montant_ligne_30425_2025(profil) == Decimal("5601")
    assert credit_federal_ligne_30425_2025(profil) == Decimal("812.15")


def test_calcul_personne_charge_30425():
    profil = _profil_personne_charge()

    assert (
        montant_brut_avant_30300_30400_ligne_30425_2025(profil)
        == Decimal("3798")
    )
    assert montant_ligne_30425_2025(profil) == Decimal("3798")
    assert credit_federal_ligne_30425_2025(profil) == Decimal("550.71")


def test_montant_ne_devient_pas_negatif():
    profil = _profil_conjoint(
        montant_reclame_ligne_30300_ou_30400=Decimal("9000")
    )
    assert montant_ligne_30425_2025(profil) == Decimal("0")


@pytest.mark.parametrize(
    "champ,valeur,message",
    [
        ("type_personne", "autre", "type de personne"),
        ("personne_soutenue_en_2025", False, "soutenue"),
        ("infirmite_physique_ou_mentale", False, "infirmité"),
        (
            "dependance_due_uniquement_a_infirmite",
            False,
            "dépendance",
        ),
        (
            "dependance_periode_considerable",
            False,
            "période considérable",
        ),
        ("montant_base_2687_inclus", False, "2 687"),
        ("un_seul_reclamant_30425", False, "Une seule personne"),
        (
            "aucune_reclamation_partagee",
            False,
            "divisée ou partagée",
        ),
        (
            "preuve_medicale_ou_t2201_confirmee",
            False,
            "preuve médicale",
        ),
        ("valide_par_comptable", False, "comptable"),
    ],
)
def test_validations_profil_simple(champ, valeur, message):
    with pytest.raises(ValueError, match=message):
        valider_aidant_naturel_30425_2025(
            _profil_conjoint(**{champ: valeur})
        )


def test_personne_charge_doit_avoir_18_ans_ou_plus():
    with pytest.raises(ValueError, match="18 ans ou plus"):
        valider_aidant_naturel_30425_2025(
            _profil_personne_charge(
                personne_charge_18_ans_ou_plus_si_applicable=False
            )
        )


@pytest.mark.parametrize(
    "revenu",
    [
        Decimal("8623.99"),
        Decimal("28798.01"),
    ],
)
def test_revenu_hors_plage_refuse(revenu):
    with pytest.raises(ValueError, match="8 624.*28 798"):
        valider_aidant_naturel_30425_2025(
            _profil_conjoint(
                revenu_net_personne_ligne_23600=revenu
            )
        )


def test_revenu_aux_bornes_est_accepte():
    valider_aidant_naturel_30425_2025(
        _profil_conjoint(
            revenu_net_personne_ligne_23600=Decimal("8624")
        )
    )
    valider_aidant_naturel_30425_2025(
        _profil_conjoint(
            revenu_net_personne_ligne_23600=Decimal("28798")
        )
    )


def test_revenu_negatif_refuse_meme_sans_reclamation():
    with pytest.raises(ValueError, match="ligne 23600"):
        valider_aidant_naturel_30425_2025(
            AidantNaturelConjointOuPersonneChargeFederal2025(
                revenu_net_personne_ligne_23600=Decimal("-1")
            )
        )


def test_montant_30300_30400_negatif_refuse():
    with pytest.raises(ValueError, match="30300 ou 30400"):
        valider_aidant_naturel_30425_2025(
            _profil_conjoint(
                montant_reclame_ligne_30300_ou_30400=Decimal("-1")
            )
        )


def test_source_obligatoire():
    with pytest.raises(ValueError, match="source"):
        valider_aidant_naturel_30425_2025(
            _profil_conjoint(source_personne=" ")
        )


def test_garde_fou_34990():
    assert integration_sans_credit_compensatoire_autorisee_2025(
        Decimal("52000")
    ) is True
    assert integration_sans_credit_compensatoire_autorisee_2025(
        Decimal("57375")
    ) is True
    assert integration_sans_credit_compensatoire_autorisee_2025(
        Decimal("57375.01")
    ) is False


def test_garde_fou_revenu_imposable_negatif_refuse():
    with pytest.raises(ValueError, match="revenu imposable fédéral"):
        integration_sans_credit_compensatoire_autorisee_2025(
            Decimal("-1")
        )
