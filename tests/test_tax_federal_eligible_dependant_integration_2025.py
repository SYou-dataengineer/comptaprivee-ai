from decimal import Decimal

import pytest

from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
    formater_estimation_fiscale_2025,
)
from src.comptaprivee.tax_federal_eligible_dependant_2025 import (
    MontantPersonneChargeAdmissibleFederal2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_age_pension_integration_2025 import (
    _profil_age_federal,
)
from tests.test_tax_federal_spouse_integration_2025 import (
    _profil_conjoint,
)


def _profil_personne_charge(**modifications):
    valeurs = {
        "reclamer_montant": True,
        "revenu_net_contribuable_ligne_23600": Decimal("51515.00"),
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


def test_sans_personne_charge_resultat_historique_inchange():
    e = calculer_estimation_fiscale_2025(_dossier_52000())

    assert e.federal.impot_federal_de_base == Decimal("4401.90")
    assert e.rapprochement.impot_total_preliminaire == Decimal("8088.95")
    assert e.rapprochement.remboursement_estime == Decimal("5611.05")
    assert (
        e.personne_charge_admissible_federale
        == MontantPersonneChargeAdmissibleFederal2025()
    )


def test_personne_charge_reduit_impot_federal():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        personne_charge_admissible_federale=_profil_personne_charge(),
    )

    assert e.federal.impot_federal_de_base == Decimal("2643.19")
    assert e.rapprochement.abattement_quebec == Decimal("436.13")
    assert e.rapprochement.impot_federal_apres_abattement == Decimal("2207.06")
    assert e.rapprochement.impot_total_preliminaire == Decimal("6620.42")
    assert e.rapprochement.remboursement_estime == Decimal("7079.58")


def test_estimation_conserve_profil_personne_charge():
    profil = _profil_personne_charge()

    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        personne_charge_admissible_federale=profil,
    )

    assert e.personne_charge_admissible_federale == profil


def test_revenu_net_ligne_23600_doit_correspondre():
    profil = _profil_personne_charge(
        revenu_net_contribuable_ligne_23600=Decimal("50000")
    )

    with pytest.raises(ValueError, match="ligne 23600"):
        calculer_estimation_fiscale_2025(
            _dossier_52000(),
            personne_charge_admissible_federale=profil,
        )


def test_combinaison_30300_et_30400_refusee():
    with pytest.raises(ValueError, match="30300.*30400|30400.*30300"):
        calculer_estimation_fiscale_2025(
            _dossier_52000(),
            montant_conjoint_federal=_profil_conjoint(),
            personne_charge_admissible_federale=_profil_personne_charge(),
        )


def test_combinaison_age_federal_et_30400_supportee():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        credits_federaux_age_pension=_profil_age_federal(),
        personne_charge_admissible_federale=_profil_personne_charge(),
    )

    assert e.federal.impot_federal_de_base == Decimal("1464.48")
    assert e.rapprochement.abattement_quebec == Decimal("241.64")
    assert e.rapprochement.impot_federal_apres_abattement == Decimal("1222.84")
    assert e.rapprochement.impot_total_preliminaire == Decimal("5636.20")
    assert e.rapprochement.remboursement_estime == Decimal("8063.80")


def test_resume_affiche_personne_charge_admissible():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        personne_charge_admissible_federale=_profil_personne_charge(),
    )
    resume = formater_estimation_fiscale_2025(e)

    assert "PERSONNE À CHARGE ADMISSIBLE — FÉDÉRAL 2025" in resume
    assert "Ligne 30400 : 12\xa0129,00 $" in resume
    assert "Crédit fédéral calculé : 1\xa0758,71 $" in resume
    assert "Revenu net de la personne à charge : 4\xa0000,00 $" in resume
    assert "État civil, résidence et revenu de l'enfant validés" in resume


def test_rapprochement_reconnait_credit_familial_30400():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        personne_charge_admissible_federale=_profil_personne_charge(),
    )

    assert (
        "Montant fédéral pour personne à charge admissible "
        "ligne 30400 inclus."
        in e.rapprochement.limitations
    )
    assert not any(
        texte == "Aucun crédit familial."
        or texte.startswith("Aucun crédit familial,")
        for texte in e.rapprochement.limitations
    )
