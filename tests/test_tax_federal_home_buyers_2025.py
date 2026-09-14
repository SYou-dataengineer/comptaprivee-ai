from decimal import Decimal

import pytest

from src.comptaprivee.tax_federal_2025 import ImpotFederalPreliminaire2025
from src.comptaprivee.tax_federal_home_buyers_2025 import (
    MAXIMUM_LIGNE_31270_2025,
    SEUIL_PREMIERE_TRANCHE_FEDERALE_2025,
    TAUX_CREDIT_FEDERAL_2025,
    MontantAchatHabitationFederal2025,
    appliquer_credit_federal_ligne_31270_2025,
    credit_federal_ligne_31270_2025,
    integration_31270_sans_credit_compensatoire_autorisee_2025,
    montant_ligne_31270_2025,
    valider_montant_achat_habitation_2025,
)


def _profil(**modifications):
    valeurs = {
        "reclamer_montant": True,
        "montant_reclame": Decimal("10000"),
        "acquisition_en_2025": True,
        "habitation_admissible": True,
        "habitation_situee_au_canada": True,
        "habitation_enregistree_nom_contribuable_ou_conjoint": True,
        "premier_acheteur_confirme": True,
        "aucune_habitation_possedee_habitee_annee_achat_ou_4_precedentes": True,
        "intention_residence_principale_dans_un_an": True,
        "aucun_partage_du_montant": True,
        "aucune_exception_handicap_utilisee": True,
        "pieces_justificatives_conservees": True,
        "valide_par_comptable": True,
        "source_habitation": (
            "Acte d'acquisition, registre foncier et occupation validés"
        ),
    }
    valeurs.update(modifications)
    return MontantAchatHabitationFederal2025(**valeurs)


def _impot(impot_de_base=Decimal("3000")):
    return ImpotFederalPreliminaire2025(
        client="Client Test",
        annee_fiscale=2025,
        revenu_imposable=Decimal("52000"),
        impot_brut=Decimal("8000"),
        montant_personnel_base=Decimal("16129"),
        cotisation_base_rrq=Decimal("3000"),
        assurance_emploi_admissible=Decimal("800"),
        rqap_admissible=Decimal("400"),
        montant_canadien_emploi=Decimal("1471"),
        base_credits_non_remboursables=Decimal("21800"),
        credits_non_remboursables=Decimal("3161"),
        impot_federal_de_base=impot_de_base,
        taux_credit=Decimal("0.145"),
        top_up_credit=Decimal("0"),
        limitations=(),
    )


def test_constantes_31270_2025():
    assert MAXIMUM_LIGNE_31270_2025 == Decimal("10000")
    assert TAUX_CREDIT_FEDERAL_2025 == Decimal("0.145")
    assert SEUIL_PREMIERE_TRANCHE_FEDERALE_2025 == Decimal("57375")


def test_profil_vide_est_valide():
    profil = MontantAchatHabitationFederal2025()

    assert valider_montant_achat_habitation_2025(profil) == profil
    assert montant_ligne_31270_2025(profil) == Decimal("0")
    assert credit_federal_ligne_31270_2025(profil) == Decimal("0.00")


def test_montant_maximal_et_credit():
    profil = _profil()

    assert montant_ligne_31270_2025(profil) == Decimal("10000.00")
    assert credit_federal_ligne_31270_2025(profil) == Decimal("1450.00")


def test_montant_inferieur_est_permis():
    profil = _profil(montant_reclame=Decimal("7500"))

    assert montant_ligne_31270_2025(profil) == Decimal("7500.00")
    assert credit_federal_ligne_31270_2025(profil) == Decimal("1087.50")


@pytest.mark.parametrize(
    "montant",
    [Decimal("-1"), Decimal("10000.01"), Decimal("15000")],
)
def test_montant_hors_limites_refuse(montant):
    with pytest.raises(ValueError):
        valider_montant_achat_habitation_2025(
            _profil(montant_reclame=montant)
        )


def test_montant_non_nul_sans_reclamation_refuse():
    with pytest.raises(ValueError, match="n'est pas réclamé"):
        valider_montant_achat_habitation_2025(
            MontantAchatHabitationFederal2025(
                montant_reclame=Decimal("10000")
            )
        )


@pytest.mark.parametrize(
    "champ,message",
    [
        ("acquisition_en_2025", "2025"),
        ("habitation_admissible", "admissible"),
        ("habitation_situee_au_canada", "Canada"),
        (
            "habitation_enregistree_nom_contribuable_ou_conjoint",
            "enregistrée",
        ),
        ("premier_acheteur_confirme", "première habitation"),
        (
            "aucune_habitation_possedee_habitee_annee_achat_ou_4_precedentes",
            "quatre années précédentes",
        ),
        (
            "intention_residence_principale_dans_un_an",
            "résidence principale",
        ),
        ("aucun_partage_du_montant", "partage"),
        (
            "aucune_exception_handicap_utilisee",
            "personnes handicapées",
        ),
        ("pieces_justificatives_conservees", "pièces justificatives"),
        ("valide_par_comptable", "comptable"),
    ],
)
def test_validations_profil_simple(champ, message):
    with pytest.raises(ValueError, match=message):
        valider_montant_achat_habitation_2025(
            _profil(**{champ: False})
        )


def test_source_obligatoire():
    with pytest.raises(ValueError, match="source"):
        valider_montant_achat_habitation_2025(
            _profil(source_habitation=" ")
        )


def test_application_credit_federal():
    resultat = appliquer_credit_federal_ligne_31270_2025(
        _impot(),
        _profil(),
    )

    assert resultat.impot_federal_de_base == Decimal("1550.00")
    assert (
        "Montant pour l'achat d'une habitation ligne 31270 inclus."
        in resultat.limitations
    )


def test_application_ne_descend_pas_sous_zero():
    resultat = appliquer_credit_federal_ligne_31270_2025(
        _impot(Decimal("1000")),
        _profil(),
    )

    assert resultat.impot_federal_de_base == Decimal("0")


def test_garde_fou_34990():
    assert integration_31270_sans_credit_compensatoire_autorisee_2025(
        Decimal("52000")
    ) is True
    assert integration_31270_sans_credit_compensatoire_autorisee_2025(
        Decimal("57375")
    ) is True
    assert integration_31270_sans_credit_compensatoire_autorisee_2025(
        Decimal("57375.01")
    ) is False


def test_garde_fou_revenu_imposable_negatif_refuse():
    with pytest.raises(ValueError, match="revenu imposable fédéral"):
        integration_31270_sans_credit_compensatoire_autorisee_2025(
            Decimal("-1")
        )
