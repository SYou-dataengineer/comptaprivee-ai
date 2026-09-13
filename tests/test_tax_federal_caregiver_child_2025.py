from decimal import Decimal

import pytest

from src.comptaprivee.tax_federal_caregiver_child_2025 import (
    MONTANT_AIDANT_ENFANT_MOINS_18_2025,
    SEUIL_PREMIERE_TRANCHE_FEDERALE_2025,
    TAUX_CREDIT_FEDERAL_2025,
    AidantNaturelEnfantMoins18Federal2025,
    credit_federal_aidant_enfant_moins18_2025,
    integration_sans_credit_compensatoire_autorisee_2025,
    montant_ligne_30500_2025,
    nombre_enfants_ligne_30499_2025,
    valider_aidant_naturel_enfant_moins18_federal_2025,
)


def _profil(**modifications):
    valeurs = {
        "reclamer_montant": True,
        "enfant_biologique_ou_adopte": True,
        "enfant_moins_18_fin_2025": True,
        "infirmite_physique_ou_mentale": True,
        "dependance_longue_continue_duree_indeterminee": True,
        "besoin_aide_beaucoup_plus_que_meme_age": True,
        "enfant_avec_deux_parents_toute_annee": True,
        "aucune_garde_partagee": True,
        "aucune_pension_alimentaire": True,
        "aucun_autre_reclamant_30500": True,
        "aucun_transfert_conjoint_32600": True,
        "preuve_medicale_ou_t2201_confirmee": True,
        "valide_par_comptable": True,
        "source_enfant": (
            "Lien familial, résidence et preuve médicale validés"
        ),
    }
    valeurs.update(modifications)
    return AidantNaturelEnfantMoins18Federal2025(**valeurs)


def test_constantes_2025():
    assert MONTANT_AIDANT_ENFANT_MOINS_18_2025 == Decimal("2687")
    assert TAUX_CREDIT_FEDERAL_2025 == Decimal("0.145")
    assert SEUIL_PREMIERE_TRANCHE_FEDERALE_2025 == Decimal("57375")


def test_profil_vide_est_valide_et_retourne_zero():
    profil = AidantNaturelEnfantMoins18Federal2025()

    assert (
        valider_aidant_naturel_enfant_moins18_federal_2025(
            profil
        )
        == profil
    )
    assert nombre_enfants_ligne_30499_2025(profil) == 0
    assert montant_ligne_30500_2025(profil) == 0
    assert credit_federal_aidant_enfant_moins18_2025(profil) == 0


@pytest.mark.parametrize(
    "champ,message",
    [
        (
            "enfant_biologique_ou_adopte",
            "enfant biologique",
        ),
        (
            "enfant_moins_18_fin_2025",
            "moins de 18 ans",
        ),
        (
            "infirmite_physique_ou_mentale",
            "infirmité physique ou mentale",
        ),
        (
            "dependance_longue_continue_duree_indeterminee",
            "longue période continue",
        ),
        (
            "besoin_aide_beaucoup_plus_que_meme_age",
            "beaucoup plus d'aide",
        ),
        (
            "enfant_avec_deux_parents_toute_annee",
            "deux parents",
        ),
        (
            "aucune_garde_partagee",
            "garde partagée",
        ),
        (
            "aucune_pension_alimentaire",
            "pension alimentaire",
        ),
        (
            "aucun_autre_reclamant_30500",
            "autre personne",
        ),
        (
            "aucun_transfert_conjoint_32600",
            "transferts",
        ),
        (
            "preuve_medicale_ou_t2201_confirmee",
            "preuve médicale",
        ),
        (
            "valide_par_comptable",
            "comptable",
        ),
    ],
)
def test_validations_profil_simple(champ, message):
    with pytest.raises(ValueError, match=message):
        valider_aidant_naturel_enfant_moins18_federal_2025(
            _profil(**{champ: False})
        )


def test_source_obligatoire():
    with pytest.raises(ValueError, match="source"):
        valider_aidant_naturel_enfant_moins18_federal_2025(
            _profil(source_enfant=" ")
        )


def test_ligne_30499_compte_un_enfant():
    assert nombre_enfants_ligne_30499_2025(_profil()) == 1


def test_ligne_30500_montant_fixe_2025():
    assert montant_ligne_30500_2025(
        _profil()
    ) == Decimal("2687")


def test_credit_federal_2025():
    assert credit_federal_aidant_enfant_moins18_2025(
        _profil()
    ) == Decimal("389.62")


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
