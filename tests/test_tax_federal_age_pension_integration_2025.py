from decimal import Decimal

import pytest

from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
    formater_estimation_fiscale_2025,
)
from src.comptaprivee.tax_federal_age_pension_2025 import (
    CreditsFederauxAgePension2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000


def _profil_age_federal(**modifications):
    valeurs = {
        "reclamer_montant_age": True,
        "age_65_plus_31_decembre_2025": True,
        "revenu_net_ligne_23600": Decimal("51515.00"),
        "reclamer_montant_pension": False,
        "revenu_pension_admissible": Decimal("0"),
        "resident_canada_toute_annee": True,
        "aucune_regle_deces": True,
        "aucun_fractionnement_pension": True,
        "aucun_transfert_conjoint": True,
        "revenu_pension_admissible_confirme": False,
        "valide_par_comptable": True,
        "source_age": "Date de naissance validée",
        "source_pension": "",
    }
    valeurs.update(modifications)
    return CreditsFederauxAgePension2025(**valeurs)


def _profil_pension_federal():
    return CreditsFederauxAgePension2025(
        reclamer_montant_age=False,
        age_65_plus_31_decembre_2025=True,
        revenu_net_ligne_23600=Decimal("51515.00"),
        reclamer_montant_pension=True,
        revenu_pension_admissible=Decimal("2000"),
        resident_canada_toute_annee=True,
        aucune_regle_deces=True,
        aucun_fractionnement_pension=True,
        aucun_transfert_conjoint=True,
        revenu_pension_admissible_confirme=True,
        valide_par_comptable=True,
        source_age="",
        source_pension="T4A / pension validée",
    )


def test_sans_credit_age_federal_resultat_historique_inchange():
    e = calculer_estimation_fiscale_2025(_dossier_52000())
    assert e.federal.impot_federal_de_base == Decimal("4401.90")
    assert e.rapprochement.impot_total_preliminaire == Decimal("8088.95")
    assert e.rapprochement.remboursement_estime == Decimal("5611.05")
    assert e.credits_federaux_age_pension == CreditsFederauxAgePension2025()


def test_age_federal_reduit_impot_federal():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        credits_federaux_age_pension=_profil_age_federal(),
    )
    assert e.federal.impot_federal_de_base == Decimal("3223.19")
    assert e.rapprochement.abattement_quebec == Decimal("531.83")
    assert e.rapprochement.impot_federal_apres_abattement == Decimal("2691.36")
    assert e.rapprochement.impot_total_preliminaire == Decimal("7104.72")
    assert e.rapprochement.remboursement_estime == Decimal("6595.28")


def test_estimation_conserve_profil_age_federal():
    profil = _profil_age_federal()
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        credits_federaux_age_pension=profil,
    )
    assert e.credits_federaux_age_pension == profil


def test_revenu_net_ligne_23600_doit_correspondre():
    profil = _profil_age_federal(
        revenu_net_ligne_23600=Decimal("50000")
    )
    with pytest.raises(ValueError, match="ligne 23600"):
        calculer_estimation_fiscale_2025(
            _dossier_52000(),
            credits_federaux_age_pension=profil,
        )


def test_pension_refusee_tant_que_revenu_non_integre():
    with pytest.raises(
        ValueError,
        match="revenu de pension.*moteur de revenu",
    ):
        calculer_estimation_fiscale_2025(
            _dossier_52000(),
            credits_federaux_age_pension=_profil_pension_federal(),
        )


def test_resume_affiche_age_federal():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        credits_federaux_age_pension=_profil_age_federal(),
    )
    resume = formater_estimation_fiscale_2025(e)
    assert "ÂGE / PENSION — FÉDÉRAL 2025" in resume
    assert "Montant en raison de l'âge — ligne 30100 : 8\xa0129,05 $" in resume
    assert "Crédit fédéral calculé : 1\xa0178,71 $" in resume
    assert "Date de naissance validée" in resume
    assert "Ligne 31400 non réclamée" in resume


def test_rapprochement_reconnait_age_federal():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        credits_federaux_age_pension=_profil_age_federal(),
    )
    assert (
        "Montant fédéral en raison de l'âge ligne 30100 inclus."
        in e.rapprochement.limitations
    )
