from decimal import Decimal

import pytest

from src.comptaprivee.tax_federal_eligible_dependant_2025 import (
    SEUIL_PREMIERE_TRANCHE_FEDERALE_2025,
    TAUX_CREDIT_FEDERAL_2025,
    MontantPersonneChargeAdmissibleFederal2025,
    credit_federal_personne_charge_admissible_2025,
    integration_sans_credit_compensatoire_autorisee_2025,
    montant_ligne_30400_2025,
    valider_montant_personne_charge_admissible_federal_2025,
)


def _profil(**modifications):
    valeurs = {
        "reclamer_montant": True,
        "revenu_net_contribuable_ligne_23600": Decimal("52000"),
        "revenu_net_personne_charge_2025": Decimal("4000"),
        "contribuable_resident_canada_toute_annee": True,
        "aucun_epoux_conjoint_2025": True,
        "personne_charge_est_enfant": True,
        "enfant_moins_18_fin_2025": True,
        "aucune_infirmite_enfant": True,
        "enfant_soutenu_2025": True,
        "enfant_a_vecu_avec_contribuable": True,
        "habitation_maintenue_par_contribuable": True,
        "enfant_resident_canada_toute_annee": True,
        "aucune_garde_partagee": True,
        "aucun_paiement_pension_alimentaire": True,
        "un_seul_montant_30400_par_menage": True,
        "aucun_autre_reclamant_30400": True,
        "revenu_personne_charge_confirme": True,
        "valide_par_comptable": True,
        "source_personne_charge": (
            "État civil, résidence et revenu de l'enfant validés"
        ),
    }
    valeurs.update(modifications)
    return MontantPersonneChargeAdmissibleFederal2025(**valeurs)


def test_constantes_2025():
    assert TAUX_CREDIT_FEDERAL_2025 == Decimal("0.145")
    assert SEUIL_PREMIERE_TRANCHE_FEDERALE_2025 == Decimal("57375")


def test_profil_vide_est_valide_et_retourne_zero():
    profil = MontantPersonneChargeAdmissibleFederal2025()

    assert (
        valider_montant_personne_charge_admissible_federal_2025(
            profil
        )
        == profil
    )
    assert montant_ligne_30400_2025(profil) == 0
    assert credit_federal_personne_charge_admissible_2025(profil) == 0


def test_revenu_contribuable_negatif_refuse():
    with pytest.raises(ValueError, match="ligne 23600"):
        valider_montant_personne_charge_admissible_federal_2025(
            _profil(
                revenu_net_contribuable_ligne_23600=Decimal("-1")
            )
        )


def test_revenu_personne_charge_negatif_refuse():
    with pytest.raises(ValueError, match="personne à charge"):
        valider_montant_personne_charge_admissible_federal_2025(
            _profil(
                revenu_net_personne_charge_2025=Decimal("-1")
            )
        )


@pytest.mark.parametrize(
    "champ,message",
    [
        (
            "contribuable_resident_canada_toute_annee",
            "résident du Canada",
        ),
        (
            "aucun_epoux_conjoint_2025",
            "sans époux ni conjoint",
        ),
        (
            "personne_charge_est_enfant",
            "enfant du contribuable",
        ),
        (
            "enfant_moins_18_fin_2025",
            "moins de 18 ans",
        ),
        (
            "aucune_infirmite_enfant",
            "aidant naturel",
        ),
        (
            "enfant_soutenu_2025",
            "subvenu aux besoins",
        ),
        (
            "enfant_a_vecu_avec_contribuable",
            "vécu avec le contribuable",
        ),
        (
            "habitation_maintenue_par_contribuable",
            "maintenu l'habitation",
        ),
        (
            "enfant_resident_canada_toute_annee",
            "résident du Canada",
        ),
        (
            "aucune_garde_partagee",
            "garde partagée",
        ),
        (
            "aucun_paiement_pension_alimentaire",
            "pension alimentaire",
        ),
        (
            "un_seul_montant_30400_par_menage",
            "Un seul montant",
        ),
        (
            "aucun_autre_reclamant_30400",
            "Aucun autre contribuable",
        ),
        (
            "revenu_personne_charge_confirme",
            "revenu net 2025",
        ),
        (
            "valide_par_comptable",
            "comptable",
        ),
    ],
)
def test_validations_profil_simple(champ, message):
    with pytest.raises(ValueError, match=message):
        valider_montant_personne_charge_admissible_federal_2025(
            _profil(**{champ: False})
        )


def test_source_obligatoire():
    with pytest.raises(ValueError, match="source"):
        valider_montant_personne_charge_admissible_federal_2025(
            _profil(source_personne_charge=" ")
        )


def test_ligne_30400_a_52000_et_enfant_4000():
    assert montant_ligne_30400_2025(
        _profil()
    ) == Decimal("12129.00")


def test_credit_federal_a_52000_et_enfant_4000():
    assert credit_federal_personne_charge_admissible_2025(
        _profil()
    ) == Decimal("1758.71")


def test_ligne_30400_zero_si_revenu_enfant_egale_bpa():
    assert montant_ligne_30400_2025(
        _profil(
            revenu_net_personne_charge_2025=Decimal("16129")
        )
    ) == 0


def test_ligne_30400_zero_si_revenu_enfant_superieur_bpa():
    assert montant_ligne_30400_2025(
        _profil(
            revenu_net_personne_charge_2025=Decimal("25000")
        )
    ) == 0


def test_ligne_30400_utilise_bpa_reduit_a_200000():
    assert montant_ligne_30400_2025(
        _profil(
            revenu_net_contribuable_ligne_23600=Decimal("200000"),
            revenu_net_personne_charge_2025=Decimal("4000"),
        )
    ) == Decimal("11663.11")


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
