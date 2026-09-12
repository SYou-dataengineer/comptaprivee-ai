from decimal import Decimal
import pytest

from src.comptaprivee.tax_federal_age_pension_2025 import (
    MONTANT_AGE_FEDERAL_MAX_2025,
    MONTANT_PENSION_FEDERAL_MAX_2025,
    SEUIL_FIN_AGE_FEDERAL_2025,
    SEUIL_PREMIERE_TRANCHE_FEDERALE_2025,
    SEUIL_REDUCTION_AGE_FEDERAL_2025,
    TAUX_CREDIT_FEDERAL_2025,
    TAUX_REDUCTION_AGE_FEDERAL_2025,
    CreditsFederauxAgePension2025,
    base_credits_age_pension_federal_2025,
    credit_federal_age_pension_2025,
    integration_sans_credit_compensatoire_autorisee_2025,
    montant_age_federal_2025,
    montant_pension_federal_2025,
    valider_credits_federaux_age_pension_2025,
)


def _profil(**modifications):
    valeurs = dict(
        reclamer_montant_age=True,
        age_65_plus_31_decembre_2025=True,
        revenu_net_ligne_23600=Decimal("52000"),
        reclamer_montant_pension=True,
        revenu_pension_admissible=Decimal("3000"),
        resident_canada_toute_annee=True,
        aucune_regle_deces=True,
        aucun_fractionnement_pension=True,
        aucun_transfert_conjoint=True,
        revenu_pension_admissible_confirme=True,
        valide_par_comptable=True,
        source_age="Date de naissance validée",
        source_pension="T4A / revenu de pension admissible validé",
    )
    valeurs.update(modifications)
    return CreditsFederauxAgePension2025(**valeurs)


def test_constantes_2025():
    assert MONTANT_AGE_FEDERAL_MAX_2025 == Decimal("9028")
    assert SEUIL_REDUCTION_AGE_FEDERAL_2025 == Decimal("45522")
    assert SEUIL_FIN_AGE_FEDERAL_2025 == Decimal("105709")
    assert TAUX_REDUCTION_AGE_FEDERAL_2025 == Decimal("0.15")
    assert MONTANT_PENSION_FEDERAL_MAX_2025 == Decimal("2000")
    assert TAUX_CREDIT_FEDERAL_2025 == Decimal("0.145")
    assert SEUIL_PREMIERE_TRANCHE_FEDERALE_2025 == Decimal("57375")


def test_profil_vide_zero():
    p = CreditsFederauxAgePension2025()
    assert valider_credits_federaux_age_pension_2025(p) == p
    assert montant_age_federal_2025(p) == 0
    assert montant_pension_federal_2025(p) == 0
    assert credit_federal_age_pension_2025(p) == 0


@pytest.mark.parametrize(
    "champ, valeur, message",
    [
        ("revenu_net_ligne_23600", Decimal("-1"), "ligne 23600"),
        ("revenu_pension_admissible", Decimal("-1"), "pension admissible"),
        ("resident_canada_toute_annee", False, "résidence au Canada"),
        ("age_65_plus_31_decembre_2025", False, "65 ans ou plus"),
        ("aucune_regle_deces", False, "personne décédée"),
        ("aucun_fractionnement_pension", False, "T1032"),
        ("aucun_transfert_conjoint", False, "transfert de crédits"),
        ("valide_par_comptable", False, "comptable"),
    ],
)
def test_validations_generales(champ, valeur, message):
    with pytest.raises(ValueError, match=message):
        valider_credits_federaux_age_pension_2025(
            _profil(**{champ: valeur})
        )


def test_source_age_obligatoire():
    with pytest.raises(ValueError, match="source confirmant l'âge"):
        valider_credits_federaux_age_pension_2025(_profil(source_age=" "))


def test_pension_positive_obligatoire():
    with pytest.raises(ValueError, match="ligne 31400"):
        valider_credits_federaux_age_pension_2025(
            _profil(revenu_pension_admissible=Decimal("0"))
        )


def test_admissibilite_pension_confirmee():
    with pytest.raises(ValueError, match="admissibilité"):
        valider_credits_federaux_age_pension_2025(
            _profil(revenu_pension_admissible_confirme=False)
        )


def test_source_pension_obligatoire():
    with pytest.raises(ValueError, match="source du revenu"):
        valider_credits_federaux_age_pension_2025(_profil(source_pension=" "))


def test_age_maximal_sous_seuil():
    p = _profil(
        revenu_net_ligne_23600=Decimal("45522"),
        reclamer_montant_pension=False,
        revenu_pension_admissible=Decimal("0"),
        source_pension="",
    )
    assert montant_age_federal_2025(p) == Decimal("9028")


def test_age_reduit_a_52000():
    assert montant_age_federal_2025(_profil()) == Decimal("8056.30")


def test_age_nul_a_105709():
    assert montant_age_federal_2025(
        _profil(revenu_net_ligne_23600=Decimal("105709"))
    ) == 0


def test_pension_plafonnee_a_2000():
    assert montant_pension_federal_2025(_profil()) == Decimal("2000")


def test_pension_sous_plafond():
    p = _profil(
        reclamer_montant_age=False,
        source_age="",
        revenu_pension_admissible=Decimal("1250.55"),
    )
    assert montant_pension_federal_2025(p) == Decimal("1250.55")


def test_base_et_credit_a_52000():
    assert base_credits_age_pension_federal_2025(_profil()) == Decimal("10056.30")
    assert credit_federal_age_pension_2025(_profil()) == Decimal("1458.16")


def test_credit_age_seul():
    p = _profil(
        reclamer_montant_pension=False,
        revenu_pension_admissible=Decimal("0"),
        source_pension="",
    )
    assert credit_federal_age_pension_2025(p) == Decimal("1168.16")


def test_credit_pension_seul():
    p = _profil(reclamer_montant_age=False, source_age="")
    assert credit_federal_age_pension_2025(p) == Decimal("290.00")


def test_garde_fou_credit_compensatoire():
    assert integration_sans_credit_compensatoire_autorisee_2025(Decimal("52000"))
    assert integration_sans_credit_compensatoire_autorisee_2025(Decimal("57375"))
    assert not integration_sans_credit_compensatoire_autorisee_2025(Decimal("57375.01"))
    with pytest.raises(ValueError, match="revenu imposable fédéral"):
        integration_sans_credit_compensatoire_autorisee_2025(Decimal("-1"))
