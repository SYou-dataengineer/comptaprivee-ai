from decimal import Decimal

import pytest

from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
    formater_estimation_fiscale_2025,
)
from src.comptaprivee.tax_federal_caregiver_child_2025 import (
    AidantNaturelEnfantMoins18Federal2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_eligible_dependant_integration_2025 import (
    _profil_personne_charge,
)
from tests.test_tax_federal_spouse_integration_2025 import (
    _profil_conjoint,
)


def _profil_aidant_enfant(**modifications):
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


def test_sans_aidant_enfant_resultat_historique_inchange():
    e = calculer_estimation_fiscale_2025(_dossier_52000())

    assert e.federal.impot_federal_de_base == Decimal("4401.90")
    assert e.rapprochement.impot_total_preliminaire == Decimal("8088.95")
    assert e.rapprochement.remboursement_estime == Decimal("5611.05")
    assert (
        e.aidant_enfant_federal
        == AidantNaturelEnfantMoins18Federal2025()
    )


def test_aidant_enfant_reduit_impot_federal():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        aidant_enfant_federal=_profil_aidant_enfant(),
    )

    assert e.federal.impot_federal_de_base == Decimal("4012.28")
    assert e.rapprochement.abattement_quebec == Decimal("662.03")
    assert e.rapprochement.impot_federal_apres_abattement == Decimal("3350.25")
    assert e.rapprochement.impot_total_preliminaire == Decimal("7763.61")
    assert e.rapprochement.remboursement_estime == Decimal("5936.39")


def test_estimation_conserve_profil_aidant_enfant():
    profil = _profil_aidant_enfant()

    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        aidant_enfant_federal=profil,
    )

    assert e.aidant_enfant_federal == profil


def test_combinaison_30400_et_30500_refusee_pour_ce_profil():
    with pytest.raises(ValueError, match="30400.*30500|30500.*30400"):
        calculer_estimation_fiscale_2025(
            _dossier_52000(),
            personne_charge_admissible_federale=_profil_personne_charge(),
            aidant_enfant_federal=_profil_aidant_enfant(),
        )


def test_combinaison_30300_et_30500_supportee():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        montant_conjoint_federal=_profil_conjoint(),
        aidant_enfant_federal=_profil_aidant_enfant(),
    )

    assert e.aidant_enfant_federal.reclamer_montant is True
    assert (
        "Montant canadien pour aidant naturel enfant de moins de 18 ans "
        "ligne 30500 inclus."
        in e.federal.limitations
    )


def test_resume_affiche_aidant_enfant():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        aidant_enfant_federal=_profil_aidant_enfant(),
    )
    resume = formater_estimation_fiscale_2025(e)

    assert (
        "AIDANT NATUREL — ENFANT DE MOINS DE 18 ANS — FÉDÉRAL 2025"
        in resume
    )
    assert "Nombre d'enfants — ligne 30499 : 1" in resume
    assert "ligne 30500 : 2\xa0687,00 $" in resume
    assert "Crédit fédéral calculé : 389,62 $" in resume
    assert "Preuve médicale ou T2201 : confirmée" in resume
    assert (
        "Lien familial, résidence et preuve médicale validés"
        in resume
    )


def test_rapprochement_reconnait_credit_familial_30500():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        aidant_enfant_federal=_profil_aidant_enfant(),
    )

    assert (
        "Montant canadien pour aidant naturel enfant de moins de 18 ans "
        "ligne 30500 inclus."
        in e.rapprochement.limitations
    )
    assert not any(
        texte == "Aucun crédit familial."
        or texte.startswith("Aucun crédit familial,")
        for texte in e.rapprochement.limitations
    )
