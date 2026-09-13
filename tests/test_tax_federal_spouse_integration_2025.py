from decimal import Decimal

import pytest

from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
    formater_estimation_fiscale_2025,
)
from src.comptaprivee.tax_federal_spouse_2025 import (
    MontantConjointFederal2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_age_pension_integration_2025 import (
    _profil_age_federal,
)


def _profil_conjoint(**modifications):
    valeurs = {
        "reclamer_montant": True,
        "revenu_net_contribuable_ligne_23600": Decimal("51515.00"),
        "revenu_net_conjoint_2025": Decimal("5000"),
        "contribuable_resident_canada_toute_annee": True,
        "relation_conjoint_confirmee": True,
        "conjoint_soutenu_2025": True,
        "meme_conjoint_toute_annee_2025": True,
        "aucune_separation_2025": True,
        "conjoint_resident_canada_toute_annee": True,
        "aucun_paiement_pension_alimentaire": True,
        "aucune_infirmite_conjoint": True,
        "un_seul_conjoint_reclame_montant": True,
        "revenu_conjoint_confirme": True,
        "valide_par_comptable": True,
        "source_conjoint": "État civil et revenu du conjoint validés",
    }
    valeurs.update(modifications)
    return MontantConjointFederal2025(**valeurs)


def test_sans_montant_conjoint_resultat_historique_inchange():
    e = calculer_estimation_fiscale_2025(_dossier_52000())

    assert e.federal.impot_federal_de_base == Decimal("4401.90")
    assert e.rapprochement.impot_total_preliminaire == Decimal("8088.95")
    assert e.rapprochement.remboursement_estime == Decimal("5611.05")
    assert e.montant_conjoint_federal == MontantConjointFederal2025()


def test_montant_conjoint_reduit_impot_federal():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        montant_conjoint_federal=_profil_conjoint(),
    )

    assert e.federal.impot_federal_de_base == Decimal("2788.19")
    assert e.rapprochement.abattement_quebec == Decimal("460.05")
    assert e.rapprochement.impot_federal_apres_abattement == Decimal("2328.14")
    assert e.rapprochement.impot_total_preliminaire == Decimal("6741.50")
    assert e.rapprochement.remboursement_estime == Decimal("6958.50")


def test_estimation_conserve_profil_conjoint():
    profil = _profil_conjoint()

    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        montant_conjoint_federal=profil,
    )

    assert e.montant_conjoint_federal == profil


def test_revenu_net_ligne_23600_doit_correspondre():
    profil = _profil_conjoint(
        revenu_net_contribuable_ligne_23600=Decimal("50000")
    )

    with pytest.raises(ValueError, match="ligne 23600"):
        calculer_estimation_fiscale_2025(
            _dossier_52000(),
            montant_conjoint_federal=profil,
        )


def test_resume_affiche_montant_conjoint_federal():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        montant_conjoint_federal=_profil_conjoint(),
    )
    resume = formater_estimation_fiscale_2025(e)

    assert "ÉPOUX / CONJOINT DE FAIT — FÉDÉRAL 2025" in resume
    assert "Ligne 30300 : 11\xa0129,00 $" in resume
    assert "Crédit fédéral calculé : 1\xa0613,71 $" in resume
    assert "Revenu net du conjoint : 5\xa0000,00 $" in resume
    assert "État civil et revenu du conjoint validés" in resume


def test_rapprochement_reconnait_montant_conjoint():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        montant_conjoint_federal=_profil_conjoint(),
    )

    assert (
        "Montant fédéral pour époux ou conjoint de fait "
        "ligne 30300 inclus."
        in e.rapprochement.limitations
    )
    assert not any(
        texte == "Aucun crédit familial."
        or texte.startswith("Aucun crédit familial,")
        for texte in e.rapprochement.limitations
    )


def test_combinaison_age_et_conjoint_federal_supportee():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        credits_federaux_age_pension=_profil_age_federal(),
        montant_conjoint_federal=_profil_conjoint(),
    )

    assert e.federal.impot_federal_de_base == Decimal("1609.48")
    assert e.rapprochement.abattement_quebec == Decimal("265.56")
    assert e.rapprochement.impot_federal_apres_abattement == Decimal("1343.92")
    assert e.rapprochement.impot_total_preliminaire == Decimal("5757.28")
    assert e.rapprochement.remboursement_estime == Decimal("7942.72")


def test_garde_fou_34990_reste_actif():
    profil = _profil_conjoint(
        revenu_net_contribuable_ligne_23600=Decimal("60000")
    )

    with pytest.raises(ValueError, match="ligne 23600"):
        calculer_estimation_fiscale_2025(
            _dossier_52000(),
            montant_conjoint_federal=profil,
        )
