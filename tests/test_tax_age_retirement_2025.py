from decimal import Decimal

import pytest

from src.comptaprivee.tax_age_retirement_2025 import (
    COEFFICIENT_REVENUS_RETRAITE_2025,
    MONTANT_AGE_2025,
    MONTANT_REVENUS_RETRAITE_MAX_2025,
    SEUIL_EXCEDENT_SANS_CONJOINT_2025,
    SEUIL_REDUCTION_ANNEXE_B_2025,
    TAUX_REDUCTION_ANNEXE_B_2025,
    MontantsAgeRetraite2025,
    appliquer_credit_quebec_age_retraite_2025,
    credit_quebec_age_retraite_2025,
    montant_age_2025,
    montant_brut_age_retraite_2025,
    montant_ligne_361_age_retraite_2025,
    montant_revenus_retraite_2025,
    reduction_annexe_b_age_retraite_2025,
    revenu_retraite_net_admissible_2025,
    valider_montants_age_retraite_2025,
)
from src.comptaprivee.tax_quebec_2025 import (
    ImpotQuebecPreliminaire2025,
)


def _profil(**modifications):
    valeurs = {
        "reclamer_age": True,
        "ne_avant_1_janvier_1961": True,
        "reclamer_revenus_retraite": True,
        "revenu_ligne_122": Decimal("3000"),
        "revenu_ligne_123": Decimal("0"),
        "deduction_ligne_250_point_4": Decimal("0"),
        "deduction_ligne_250_point_6": Decimal("0"),
        "deduction_ligne_293": Decimal("0"),
        "deduction_ligne_297_points_9_12": Decimal("0"),
        "transfert_revenus_retraite_ligne_245": Decimal("0"),
        "revenu_familial_net": Decimal("50095"),
        "aucun_conjoint_31_decembre_2025": True,
        "resident_quebec_canada_toute_annee": True,
        "aucun_montant_personne_vivant_seule": True,
        "revenus_retraite_admissibles_confirmes": True,
        "revenus_non_admissibles_exclus": True,
        "valide_par_comptable": True,
        "source_age": "Date de naissance validée",
        "source_retraite": "RL-2 / feuillet retraite validé",
    }
    valeurs.update(modifications)
    return MontantsAgeRetraite2025(**valeurs)


def _impot():
    return ImpotQuebecPreliminaire2025(
        client="Client Test",
        annee_fiscale=2025,
        province="Québec",
        revenu_imposable=Decimal("50000"),
        impot_brut=Decimal("6000"),
        montant_personnel_base=Decimal("18571"),
        taux_credit_personnel=Decimal("0.14"),
        credit_personnel_base=Decimal("2599.94"),
        impot_quebec_preliminaire=Decimal("3400.06"),
        limitations=(
            "Résident du Québec et du Canada pour toute l'année.",
            "Aucun montant pour conjoint, personne à charge ou âge.",
        ),
    )


def test_constantes_officielles_2025():
    assert MONTANT_AGE_2025 == Decimal("3906")
    assert MONTANT_REVENUS_RETRAITE_MAX_2025 == Decimal("3470")
    assert COEFFICIENT_REVENUS_RETRAITE_2025 == Decimal("1.25")
    assert SEUIL_REDUCTION_ANNEXE_B_2025 == Decimal("42090")
    assert TAUX_REDUCTION_ANNEXE_B_2025 == Decimal("0.1875")
    assert SEUIL_EXCEDENT_SANS_CONJOINT_2025 == Decimal("64699")


def test_profil_vide_retourne_zero():
    profil = MontantsAgeRetraite2025()
    assert valider_montants_age_retraite_2025(profil) == profil
    assert montant_age_2025(profil) == 0
    assert montant_revenus_retraite_2025(profil) == 0
    assert montant_ligne_361_age_retraite_2025(profil) == 0
    assert credit_quebec_age_retraite_2025(profil) == 0


def test_revenu_familial_negatif_refuse():
    with pytest.raises(ValueError, match="revenu familial net"):
        valider_montants_age_retraite_2025(
            _profil(revenu_familial_net=Decimal("-1"))
        )


@pytest.mark.parametrize(
    "champ",
    [
        "revenu_ligne_122",
        "revenu_ligne_123",
        "deduction_ligne_250_point_4",
        "deduction_ligne_250_point_6",
        "deduction_ligne_293",
        "deduction_ligne_297_points_9_12",
        "transfert_revenus_retraite_ligne_245",
    ],
)
def test_montants_retraite_negatifs_refuses(champ):
    with pytest.raises(ValueError, match="ne peuvent pas être négatifs"):
        valider_montants_age_retraite_2025(
            _profil(**{champ: Decimal("-0.01")})
        )


def test_validation_comptable_obligatoire():
    with pytest.raises(ValueError, match="comptable"):
        valider_montants_age_retraite_2025(
            _profil(valide_par_comptable=False)
        )


def test_residence_complete_obligatoire():
    with pytest.raises(ValueError, match="résidence Québec/Canada"):
        valider_montants_age_retraite_2025(
            _profil(resident_quebec_canada_toute_annee=False)
        )


def test_profil_simple_refuse_conjoint():
    with pytest.raises(ValueError, match="sans conjoint"):
        valider_montants_age_retraite_2025(
            _profil(aucun_conjoint_31_decembre_2025=False)
        )


def test_combinaison_personne_vivant_seule_refusee_pour_maintenant():
    with pytest.raises(ValueError, match="personne vivant seule"):
        valider_montants_age_retraite_2025(
            _profil(aucun_montant_personne_vivant_seule=False)
        )


def test_age_exige_naissance_avant_1961():
    with pytest.raises(ValueError, match="avant le 1er janvier 1961"):
        valider_montants_age_retraite_2025(
            _profil(ne_avant_1_janvier_1961=False)
        )


def test_source_age_obligatoire():
    with pytest.raises(ValueError, match="source confirmant l'âge"):
        valider_montants_age_retraite_2025(
            _profil(source_age=" ")
        )


def test_retraite_exige_revenu_positif():
    with pytest.raises(ValueError, match="ligne 122 ou 123"):
        valider_montants_age_retraite_2025(
            _profil(
                revenu_ligne_122=Decimal("0"),
                revenu_ligne_123=Decimal("0"),
            )
        )


def test_ligne_123_refusee_dans_profil_sans_conjoint():
    with pytest.raises(ValueError, match="ligne 123"):
        valider_montants_age_retraite_2025(
            _profil(revenu_ligne_123=Decimal("100"))
        )


def test_transfert_retraite_refuse_dans_profil_simple():
    with pytest.raises(ValueError, match="transfert"):
        valider_montants_age_retraite_2025(
            _profil(
                transfert_revenus_retraite_ligne_245=Decimal("100")
            )
        )


def test_admissibilite_revenus_retraite_obligatoire():
    with pytest.raises(ValueError, match="admissibilité"):
        valider_montants_age_retraite_2025(
            _profil(revenus_retraite_admissibles_confirmes=False)
        )


def test_revenus_non_admissibles_doivent_etre_exclus():
    with pytest.raises(ValueError, match="PSV, RRQ et RPC"):
        valider_montants_age_retraite_2025(
            _profil(revenus_non_admissibles_exclus=False)
        )


def test_source_retraite_obligatoire():
    with pytest.raises(ValueError, match="source des revenus"):
        valider_montants_age_retraite_2025(
            _profil(source_retraite=" ")
        )


def test_deductions_ne_peuvent_pas_depasser_revenus():
    with pytest.raises(ValueError, match="dépasser les revenus"):
        valider_montants_age_retraite_2025(
            _profil(
                revenu_ligne_122=Decimal("1000"),
                deduction_ligne_250_point_4=Decimal("1000.01"),
            )
        )


def test_montant_age_3906():
    profil = _profil(reclamer_revenus_retraite=False)
    assert montant_age_2025(profil) == Decimal("3906")


def test_revenu_retraite_net_admissible():
    profil = _profil(
        reclamer_age=False,
        revenu_ligne_122=Decimal("2000"),
        deduction_ligne_250_point_4=Decimal("250"),
        deduction_ligne_293=Decimal("150"),
        source_age="",
    )
    assert (
        revenu_retraite_net_admissible_2025(profil)
        == Decimal("1600.00")
    )


def test_retraite_multipliee_par_1_25():
    profil = _profil(
        reclamer_age=False,
        revenu_ligne_122=Decimal("2000"),
        source_age="",
    )
    assert montant_revenus_retraite_2025(profil) == Decimal("2500.00")


def test_retraite_plafonnee_a_3470():
    profil = _profil(
        reclamer_age=False,
        revenu_ligne_122=Decimal("3000"),
        source_age="",
    )
    assert montant_revenus_retraite_2025(profil) == Decimal("3470")


def test_montant_brut_age_et_retraite():
    profil = _profil()
    assert montant_brut_age_retraite_2025(profil) == Decimal("7376.00")


def test_reduction_annexe_b_a_50095():
    profil = _profil()
    assert reduction_annexe_b_age_retraite_2025(
        profil
    ) == Decimal("1500.94")


def test_ligne_361_age_et_retraite():
    profil = _profil()
    assert montant_ligne_361_age_retraite_2025(
        profil
    ) == Decimal("5875.06")
    assert credit_quebec_age_retraite_2025(
        profil
    ) == Decimal("822.51")


def test_age_seul_a_50095():
    profil = _profil(
        reclamer_revenus_retraite=False,
        revenu_ligne_122=Decimal("0"),
        source_retraite="",
    )
    assert montant_ligne_361_age_retraite_2025(
        profil
    ) == Decimal("2405.06")
    assert credit_quebec_age_retraite_2025(
        profil
    ) == Decimal("336.71")


def test_retraite_seule_a_50095():
    profil = _profil(
        reclamer_age=False,
        source_age="",
    )
    assert montant_ligne_361_age_retraite_2025(
        profil
    ) == Decimal("1969.06")
    assert credit_quebec_age_retraite_2025(
        profil
    ) == Decimal("275.67")


def test_revenu_tres_eleve_annule_montant():
    profil = _profil(
        revenu_familial_net=Decimal("120000"),
    )
    assert montant_ligne_361_age_retraite_2025(profil) == 0
    assert credit_quebec_age_retraite_2025(profil) == 0


def test_application_credit_reduit_impot_quebec():
    resultat = appliquer_credit_quebec_age_retraite_2025(
        _impot(),
        _profil(),
    )
    assert resultat.impot_quebec_preliminaire == Decimal("2577.55")
    assert (
        "Montants Québec en raison de l'âge ou pour revenus de retraite "
        "inclus à la ligne 361."
        in resultat.limitations
    )


def test_application_ne_rend_pas_impot_negatif():
    impot = _impot()
    petit = ImpotQuebecPreliminaire2025(
        client=impot.client,
        annee_fiscale=impot.annee_fiscale,
        province=impot.province,
        revenu_imposable=impot.revenu_imposable,
        impot_brut=impot.impot_brut,
        montant_personnel_base=impot.montant_personnel_base,
        taux_credit_personnel=impot.taux_credit_personnel,
        credit_personnel_base=impot.credit_personnel_base,
        impot_quebec_preliminaire=Decimal("100"),
        limitations=impot.limitations,
    )
    resultat = appliquer_credit_quebec_age_retraite_2025(
        petit,
        _profil(),
    )
    assert resultat.impot_quebec_preliminaire == Decimal("0")
