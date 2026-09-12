from decimal import Decimal

import pytest

from src.comptaprivee.tax_age_retirement_2025 import (
    MontantsAgeRetraite2025,
)
from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
    formater_estimation_fiscale_2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_living_alone_integration_2025 import (
    _profil_simple as _profil_personne_vivant_seule,
)


def _profil_age_retraite(**modifications):
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
        "revenu_familial_net": Decimal("50095.00"),
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


def test_sans_age_retraite_resultat_historique_inchange():
    e = calculer_estimation_fiscale_2025(_dossier_52000())
    assert e.rapprochement.impot_total_preliminaire == Decimal("8088.95")
    assert e.rapprochement.remboursement_estime == Decimal("5611.05")
    assert e.montants_age_retraite == MontantsAgeRetraite2025()


def test_age_retraite_reduit_impot_quebec():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        montants_age_retraite=_profil_age_retraite(),
    )
    assert e.quebec.impot_quebec_preliminaire == Decimal("3590.85")
    assert e.rapprochement.impot_total_preliminaire == Decimal("7266.44")
    assert e.rapprochement.remboursement_estime == Decimal("6433.56")


def test_estimation_conserve_profil_age_retraite():
    profil = _profil_age_retraite()
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        montants_age_retraite=profil,
    )
    assert e.montants_age_retraite == profil


def test_revenu_familial_age_retraite_doit_correspondre_au_revenu_net():
    profil = _profil_age_retraite(
        revenu_familial_net=Decimal("49000")
    )
    with pytest.raises(ValueError, match="revenu familial net"):
        calculer_estimation_fiscale_2025(
            _dossier_52000(),
            montants_age_retraite=profil,
        )


def test_combinaison_personne_seule_et_age_retraite_refusee():
    with pytest.raises(ValueError, match="ne peut pas combiner"):
        calculer_estimation_fiscale_2025(
            _dossier_52000(),
            personne_vivant_seule=_profil_personne_vivant_seule(),
            montants_age_retraite=_profil_age_retraite(),
        )


def test_resume_affiche_age_retraite():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        montants_age_retraite=_profil_age_retraite(),
    )
    resume = formater_estimation_fiscale_2025(e)
    assert "ÂGE / REVENUS DE RETRAITE — QUÉBEC 2025" in resume
    assert "Montant âge — annexe B ligne 22 : 3\xa0906,00 $" in resume
    assert "Montant revenus de retraite : 3\xa0470,00 $" in resume
    assert "Montant annexe B / ligne 361 : 5\xa0875,06 $" in resume
    assert "Crédit Québec : 822,51 $" in resume
    assert "Date de naissance validée" in resume
    assert "RL-2 / feuillet retraite validé" in resume


def test_rapprochement_reconnait_age_retraite():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        montants_age_retraite=_profil_age_retraite(),
    )
    assert (
        "Montants Québec en raison de l'âge ou pour revenus de retraite inclus."
        in e.rapprochement.limitations
    )


def test_profil_age_invalide_bloque_estimation():
    profil = _profil_age_retraite(
        ne_avant_1_janvier_1961=False
    )
    with pytest.raises(ValueError, match="avant le 1er janvier 1961"):
        calculer_estimation_fiscale_2025(
            _dossier_52000(),
            montants_age_retraite=profil,
        )
