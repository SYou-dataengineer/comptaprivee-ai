from decimal import Decimal

import pytest

from src.comptaprivee.tax_federal_2025 import ImpotFederalPreliminaire2025
from src.comptaprivee.tax_federal_caregiver_other_dependant_2025 import (
    BASE_CALCUL_30450_2025,
    LIEN_ENFANT,
    LIEN_GRAND_PARENT,
    LIEN_NIECE_NEVEU,
    LIEN_PARENT,
    MAXIMUM_LIGNE_30450_2025,
    SEUIL_PREMIERE_TRANCHE_FEDERALE_2025,
    TAUX_CREDIT_FEDERAL_2025,
    AidantNaturelAutrePersonneChargeFederal2025,
    appliquer_credit_federal_ligne_30450_2025,
    credit_federal_ligne_30450_2025,
    integration_30450_sans_credit_compensatoire_autorisee_2025,
    montant_ligne_30450_2025,
    nombre_personnes_charge_ligne_51120_2025,
    valider_aidant_naturel_30450_2025,
)


def _profil(**modifications):
    valeurs = {
        "reclamer_montant": True,
        "lien_personne": LIEN_PARENT,
        "revenu_net_personne_ligne_23600": Decimal("25000"),
        "age_18_ans_ou_plus": True,
        "personne_soutenue_en_2025": True,
        "infirmite_physique_ou_mentale": True,
        "dependance_due_uniquement_a_infirmite": True,
        "dependance_periode_considerable": True,
        "resident_canada_au_moins_un_moment_2025": True,
        "aucune_reclamation_ligne_30300_30400_pour_personne": True,
        "aucun_paiement_pension_alimentaire_pour_personne": True,
        "aucun_partage_reclamation_30450": True,
        "preuve_medicale_ou_t2201_confirmee": True,
        "valide_par_comptable": True,
        "source_personne": (
            "Lien familial, revenu ligne 23600, résidence et "
            "preuve médicale validés"
        ),
    }
    valeurs.update(modifications)
    return AidantNaturelAutrePersonneChargeFederal2025(**valeurs)


def _impot(impot_de_base=Decimal("2000")):
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


def test_constantes_30450_2025():
    assert BASE_CALCUL_30450_2025 == Decimal("28798")
    assert MAXIMUM_LIGNE_30450_2025 == Decimal("8601")
    assert TAUX_CREDIT_FEDERAL_2025 == Decimal("0.145")
    assert SEUIL_PREMIERE_TRANCHE_FEDERALE_2025 == Decimal("57375")


def test_profil_vide_est_valide_et_retourne_zero():
    profil = AidantNaturelAutrePersonneChargeFederal2025()

    assert valider_aidant_naturel_30450_2025(profil) == profil
    assert montant_ligne_30450_2025(profil) == Decimal("0")
    assert credit_federal_ligne_30450_2025(profil) == Decimal("0.00")
    assert nombre_personnes_charge_ligne_51120_2025(profil) == 0


def test_calcul_revenu_25000():
    profil = _profil()

    assert montant_ligne_30450_2025(profil) == Decimal("3798.00")
    assert credit_federal_ligne_30450_2025(profil) == Decimal("550.71")
    assert nombre_personnes_charge_ligne_51120_2025(profil) == 1


def test_maximum_8601_si_revenu_faible():
    profil = _profil(
        revenu_net_personne_ligne_23600=Decimal("10000")
    )

    assert montant_ligne_30450_2025(profil) == Decimal("8601.00")
    assert credit_federal_ligne_30450_2025(profil) == Decimal("1247.15")


def test_limite_exacte_pour_maximum():
    profil = _profil(
        revenu_net_personne_ligne_23600=Decimal("20197")
    )
    assert montant_ligne_30450_2025(profil) == Decimal("8601.00")


def test_revenu_juste_au_dessus_du_palier_maximum():
    profil = _profil(
        revenu_net_personne_ligne_23600=Decimal("20197.01")
    )
    assert montant_ligne_30450_2025(profil) == Decimal("8600.99")


def test_enfant_peut_utiliser_exception_residence():
    profil = _profil(
        lien_personne=LIEN_ENFANT,
        resident_canada_au_moins_un_moment_2025=False,
    )
    assert montant_ligne_30450_2025(profil) == Decimal("3798.00")


@pytest.mark.parametrize(
    "lien",
    [
        LIEN_PARENT,
        LIEN_GRAND_PARENT,
        LIEN_NIECE_NEVEU,
    ],
)
def test_autres_liens_exigent_residence_canada(lien):
    with pytest.raises(ValueError, match="résidé au Canada"):
        valider_aidant_naturel_30450_2025(
            _profil(
                lien_personne=lien,
                resident_canada_au_moins_un_moment_2025=False,
            )
        )


@pytest.mark.parametrize(
    "champ,valeur,message",
    [
        ("lien_personne", "cousin", "lien"),
        ("age_18_ans_ou_plus", False, "18 ans ou plus"),
        ("personne_soutenue_en_2025", False, "soutenue"),
        ("infirmite_physique_ou_mentale", False, "infirmité"),
        (
            "dependance_due_uniquement_a_infirmite",
            False,
            "dépendance",
        ),
        (
            "dependance_periode_considerable",
            False,
            "période considérable",
        ),
        (
            "aucune_reclamation_ligne_30300_30400_pour_personne",
            False,
            "30300.*30400",
        ),
        (
            "aucun_paiement_pension_alimentaire_pour_personne",
            False,
            "pension alimentaire",
        ),
        (
            "aucun_partage_reclamation_30450",
            False,
            "partage",
        ),
        (
            "preuve_medicale_ou_t2201_confirmee",
            False,
            "preuve médicale",
        ),
        ("valide_par_comptable", False, "comptable"),
    ],
)
def test_validations_profil_simple(champ, valeur, message):
    with pytest.raises(ValueError, match=message):
        valider_aidant_naturel_30450_2025(
            _profil(**{champ: valeur})
        )


def test_revenu_28798_est_refuse():
    with pytest.raises(ValueError, match="inférieur.*28 798"):
        valider_aidant_naturel_30450_2025(
            _profil(
                revenu_net_personne_ligne_23600=Decimal("28798")
            )
        )


def test_revenu_superieur_28798_est_refuse():
    with pytest.raises(ValueError, match="inférieur.*28 798"):
        valider_aidant_naturel_30450_2025(
            _profil(
                revenu_net_personne_ligne_23600=Decimal("30000")
            )
        )


def test_revenu_negatif_refuse_meme_sans_reclamation():
    with pytest.raises(ValueError, match="ligne 23600"):
        valider_aidant_naturel_30450_2025(
            AidantNaturelAutrePersonneChargeFederal2025(
                revenu_net_personne_ligne_23600=Decimal("-1")
            )
        )


def test_source_obligatoire():
    with pytest.raises(ValueError, match="source"):
        valider_aidant_naturel_30450_2025(
            _profil(source_personne=" ")
        )


def test_application_credit_federal():
    resultat = appliquer_credit_federal_ligne_30450_2025(
        _impot(),
        _profil(),
    )

    assert resultat.impot_federal_de_base == Decimal("1449.29")
    assert (
        "Montant canadien pour aidant naturel ligne 30450 inclus."
        in resultat.limitations
    )


def test_application_credit_ne_descend_pas_sous_zero():
    resultat = appliquer_credit_federal_ligne_30450_2025(
        _impot(Decimal("200")),
        _profil(),
    )
    assert resultat.impot_federal_de_base == Decimal("0")


def test_garde_fou_34990():
    assert integration_30450_sans_credit_compensatoire_autorisee_2025(
        Decimal("52000")
    ) is True
    assert integration_30450_sans_credit_compensatoire_autorisee_2025(
        Decimal("57375")
    ) is True
    assert integration_30450_sans_credit_compensatoire_autorisee_2025(
        Decimal("57375.01")
    ) is False


def test_garde_fou_revenu_imposable_negatif_refuse():
    with pytest.raises(ValueError, match="revenu imposable fédéral"):
        integration_30450_sans_credit_compensatoire_autorisee_2025(
            Decimal("-1")
        )
