from decimal import Decimal

import pytest

from src.comptaprivee.tax_federal_2025 import ImpotFederalPreliminaire2025
from src.comptaprivee.tax_federal_home_accessibility_2025 import (
    MAXIMUM_DEPENSES_ACCESSIBILITE_2025,
    SEUIL_PREMIERE_TRANCHE_FEDERALE_2025,
    TAUX_CREDIT_FEDERAL_2025,
    DepensesAccessibiliteDomiciliaireFederal2025,
    appliquer_credit_federal_ligne_31285_2025,
    credit_federal_ligne_31285_2025,
    integration_31285_sans_credit_compensatoire_autorisee_2025,
    montant_ligne_31285_2025,
    valider_depenses_accessibilite_domiciliaire_2025,
)


def _profil(**modifications):
    valeurs = {
        "reclamer_montant": True,
        "depenses_admissibles": Decimal("20000"),
        "demande_pour_soi_meme": True,
        "age_65_plus_fin_annee": True,
        "admissible_ciph": False,
        "logement_situe_au_canada": True,
        "logement_propriete_du_contribuable": True,
        "logement_normalement_habite_par_contribuable": True,
        "renovation_durable_et_integrante": True,
        "accessibilite_ou_reduction_risque_confirmee": True,
        "travaux_et_biens_2025_uniquement": True,
        "aucune_part_entreprise_ou_location": True,
        "aucun_partage_de_la_demande": True,
        "fournisseurs_lies_admissibles_confirme": True,
        "depenses_non_admissibles_exclues": True,
        "pieces_justificatives_conservees": True,
        "valide_par_comptable": True,
        "source_renovation": (
            "Factures, reçus, permis et preuve de propriété validés"
        ),
    }
    valeurs.update(modifications)
    return DepensesAccessibiliteDomiciliaireFederal2025(**valeurs)


def _impot(impot_de_base=Decimal("5000")):
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


def test_constantes_31285_2025():
    assert MAXIMUM_DEPENSES_ACCESSIBILITE_2025 == Decimal("20000")
    assert TAUX_CREDIT_FEDERAL_2025 == Decimal("0.145")
    assert SEUIL_PREMIERE_TRANCHE_FEDERALE_2025 == Decimal("57375")


def test_profil_vide_est_valide():
    profil = DepensesAccessibiliteDomiciliaireFederal2025()

    assert valider_depenses_accessibilite_domiciliaire_2025(profil) == profil
    assert montant_ligne_31285_2025(profil) == Decimal("0")
    assert credit_federal_ligne_31285_2025(profil) == Decimal("0.00")


def test_maximum_et_credit_31285():
    profil = _profil()

    assert montant_ligne_31285_2025(profil) == Decimal("20000.00")
    assert credit_federal_ligne_31285_2025(profil) == Decimal("2900.00")


def test_montant_inferieur_est_permis():
    profil = _profil(depenses_admissibles=Decimal("7500"))

    assert montant_ligne_31285_2025(profil) == Decimal("7500.00")
    assert credit_federal_ligne_31285_2025(profil) == Decimal("1087.50")


def test_admissibilite_par_ciph_est_permises():
    profil = _profil(
        age_65_plus_fin_annee=False,
        admissible_ciph=True,
    )

    assert montant_ligne_31285_2025(profil) == Decimal("20000.00")


def test_age_et_ciph_peuvent_etre_vrais_ensemble():
    profil = _profil(
        age_65_plus_fin_annee=True,
        admissible_ciph=True,
    )

    assert montant_ligne_31285_2025(profil) == Decimal("20000.00")


@pytest.mark.parametrize(
    "montant",
    [Decimal("-1"), Decimal("20000.01"), Decimal("25000")],
)
def test_montant_hors_limites_refuse(montant):
    with pytest.raises(ValueError):
        valider_depenses_accessibilite_domiciliaire_2025(
            _profil(depenses_admissibles=montant)
        )


def test_montant_non_nul_sans_reclamation_refuse():
    with pytest.raises(ValueError, match="n'est pas réclamé"):
        valider_depenses_accessibilite_domiciliaire_2025(
            DepensesAccessibiliteDomiciliaireFederal2025(
                depenses_admissibles=Decimal("1000")
            )
        )


def test_age_ou_ciph_obligatoire():
    with pytest.raises(ValueError, match="65 ans|CIPH"):
        valider_depenses_accessibilite_domiciliaire_2025(
            _profil(
                age_65_plus_fin_annee=False,
                admissible_ciph=False,
            )
        )


@pytest.mark.parametrize(
    "champ,message",
    [
        ("demande_pour_soi_meme", "pour lui-même"),
        ("logement_situe_au_canada", "Canada"),
        ("logement_propriete_du_contribuable", "appartienne"),
        (
            "logement_normalement_habite_par_contribuable",
            "normalement habité",
        ),
        (
            "renovation_durable_et_integrante",
            "durable",
        ),
        (
            "accessibilite_ou_reduction_risque_confirmee",
            "accès|mobilité|blessure",
        ),
        (
            "travaux_et_biens_2025_uniquement",
            "2025",
        ),
        (
            "aucune_part_entreprise_ou_location",
            "entreprise/location",
        ),
        (
            "aucun_partage_de_la_demande",
            "partage",
        ),
        (
            "fournisseurs_lies_admissibles_confirme",
            "fournisseurs liés",
        ),
        (
            "depenses_non_admissibles_exclues",
            "non admissibles",
        ),
        (
            "pieces_justificatives_conservees",
            "factures|reçus",
        ),
        ("valide_par_comptable", "comptable"),
    ],
)
def test_validations_profil_simple(champ, message):
    with pytest.raises(ValueError, match=message):
        valider_depenses_accessibilite_domiciliaire_2025(
            _profil(**{champ: False})
        )


def test_source_obligatoire():
    with pytest.raises(ValueError, match="source"):
        valider_depenses_accessibilite_domiciliaire_2025(
            _profil(source_renovation=" ")
        )


def test_application_credit_federal():
    resultat = appliquer_credit_federal_ligne_31285_2025(
        _impot(),
        _profil(),
    )

    assert resultat.impot_federal_de_base == Decimal("2100.00")
    assert (
        "Dépenses pour l'accessibilité domiciliaire ligne 31285 incluses."
        in resultat.limitations
    )


def test_application_ne_descend_pas_sous_zero():
    resultat = appliquer_credit_federal_ligne_31285_2025(
        _impot(Decimal("1000")),
        _profil(),
    )

    assert resultat.impot_federal_de_base == Decimal("0")


def test_garde_fou_34990():
    assert integration_31285_sans_credit_compensatoire_autorisee_2025(
        Decimal("52000")
    ) is True
    assert integration_31285_sans_credit_compensatoire_autorisee_2025(
        Decimal("57375")
    ) is True
    assert integration_31285_sans_credit_compensatoire_autorisee_2025(
        Decimal("57375.01")
    ) is False


def test_garde_fou_revenu_imposable_negatif_refuse():
    with pytest.raises(ValueError, match="revenu imposable fédéral"):
        integration_31285_sans_credit_compensatoire_autorisee_2025(
            Decimal("-1")
        )
