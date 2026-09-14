from decimal import Decimal

import pytest

from src.comptaprivee.tax_federal_eligible_dependant_2025 import (
    MONTANT_AIDANT_PERSONNE_CHARGE_2025,
    MontantPersonneChargeAdmissibleFederal2025,
    credit_federal_personne_charge_admissible_2025,
    montant_base_aidant_personne_charge_30400_2025,
    montant_ligne_30400_2025,
    valider_montant_personne_charge_admissible_federal_2025,
)


def _profil_18_plus_infirmite(**modifications):
    valeurs = {
        "reclamer_montant": True,
        "revenu_net_contribuable_ligne_23600": Decimal("52000"),
        "revenu_net_personne_charge_2025": Decimal("12000"),
        "contribuable_resident_canada_toute_annee": True,
        "aucun_epoux_conjoint_2025": True,
        "personne_charge_est_enfant": True,
        "enfant_moins_18_fin_2025": False,
        "aucune_infirmite_enfant": False,
        "personne_charge_18_ans_ou_plus": True,
        "personne_charge_avec_infirmite": True,
        "dependance_due_uniquement_a_infirmite": True,
        "dependance_periode_considerable": True,
        "aidant_naturel_base_2687_inclus": True,
        "preuve_medicale_ou_t2201_confirmee": True,
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
            "Lien familial, résidence, revenu ligne 23600 "
            "et preuve médicale validés"
        ),
    }
    valeurs.update(modifications)
    return MontantPersonneChargeAdmissibleFederal2025(**valeurs)


def test_constante_base_aidant_personne_charge_2025():
    assert MONTANT_AIDANT_PERSONNE_CHARGE_2025 == Decimal("2687")


def test_base_2687_est_incluse():
    profil = _profil_18_plus_infirmite()
    assert montant_base_aidant_personne_charge_30400_2025(
        profil
    ) == Decimal("2687")


def test_ligne_30400_18_plus_infirmite():
    profil = _profil_18_plus_infirmite()
    assert montant_ligne_30400_2025(profil) == Decimal("6816.00")
    assert credit_federal_personne_charge_admissible_2025(
        profil
    ) == Decimal("988.32")


def test_18_plus_exige_infirmite():
    with pytest.raises(ValueError, match="infirmité"):
        valider_montant_personne_charge_admissible_federal_2025(
            _profil_18_plus_infirmite(
                personne_charge_avec_infirmite=False
            )
        )


def test_18_plus_refuse_drapeau_moins_18():
    with pytest.raises(ValueError, match="contradictoire"):
        valider_montant_personne_charge_admissible_federal_2025(
            _profil_18_plus_infirmite(
                enfant_moins_18_fin_2025=True
            )
        )


def test_18_plus_exige_dependance_due_a_infirmite():
    with pytest.raises(ValueError, match="due à l'infirmité"):
        valider_montant_personne_charge_admissible_federal_2025(
            _profil_18_plus_infirmite(
                dependance_due_uniquement_a_infirmite=False
            )
        )


def test_18_plus_exige_dependance_periode_considerable():
    with pytest.raises(ValueError, match="période considérable"):
        valider_montant_personne_charge_admissible_federal_2025(
            _profil_18_plus_infirmite(
                dependance_periode_considerable=False
            )
        )


def test_18_plus_exige_base_2687():
    with pytest.raises(ValueError, match="2 687"):
        valider_montant_personne_charge_admissible_federal_2025(
            _profil_18_plus_infirmite(
                aidant_naturel_base_2687_inclus=False
            )
        )


def test_18_plus_exige_preuve_medicale():
    with pytest.raises(ValueError, match="preuve médicale"):
        valider_montant_personne_charge_admissible_federal_2025(
            _profil_18_plus_infirmite(
                preuve_medicale_ou_t2201_confirmee=False
            )
        )


def test_ancien_profil_moins_18_reste_valide():
    from tests.test_tax_federal_eligible_dependant_2025 import _profil

    valider_montant_personne_charge_admissible_federal_2025(
        _profil()
    )


def test_profil_moins_18_refuse_drapeau_18_plus():
    from tests.test_tax_federal_eligible_dependant_2025 import _profil

    with pytest.raises(ValueError, match="18 ans ou plus"):
        valider_montant_personne_charge_admissible_federal_2025(
            _profil(personne_charge_avec_infirmite=True)
        )
