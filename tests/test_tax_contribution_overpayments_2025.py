from decimal import Decimal

import pytest

from src.comptaprivee.tax_contribution_overpayments_2025 import (
    CotisationsExcedentaires2025,
    SEUIL_REVENUS_RQAP_REMBOURSEMENT_COMPLET_2025,
    aucune_cotisation_excedentaire_2025,
    calculer_remboursements_cotisations_2025,
    cotisation_ae_attendue_2025,
    cotisation_rrq_attendue_2025,
    cotisation_rqap_attendue_2025,
    remboursement_assurance_emploi_2025,
    remboursement_rrq_2025,
    remboursement_rqap_2025,
    valider_cotisations_excedentaires_2025,
)


def _profil(**modifications):
    valeurs = {
        "rrq_ba": Decimal("3104.00"),
        "rrq_bb": Decimal("0"),
        "gains_admissibles_rrq": Decimal("52000"),
        "assurance_emploi": Decimal("681.20"),
        "gains_assurables_ae": Decimal("52000"),
        "rqap": Decimal("256.88"),
        "revenus_assujettis_rqap": Decimal("52000"),
        "source": "T4 / RL-1 validés",
        "valide_par_comptable": True,
        "resident_quebec_31_decembre_2025": True,
        "emploi_quebec_uniquement": True,
        "rrq_uniquement_sans_rpc": True,
        "aucun_travail_autonome": True,
        "profil_rrq_standard_18_64": True,
        "aucun_cas_particulier_ae": True,
        "aucun_cas_particulier_rqap": True,
        "calcul_standard_confirme": True,
    }
    valeurs.update(modifications)
    return CotisationsExcedentaires2025(**valeurs)


def test_profil_vide_est_valide_et_zero():
    donnees = aucune_cotisation_excedentaire_2025()
    assert valider_cotisations_excedentaires_2025(donnees) == donnees
    assert calculer_remboursements_cotisations_2025(donnees).total == 0


def test_seuil_rqap_2000():
    assert (
        SEUIL_REVENUS_RQAP_REMBOURSEMENT_COMPLET_2025
        == Decimal("2000")
    )


def test_cotisations_attendues_pour_52000():
    assert cotisation_rrq_attendue_2025(Decimal("52000")) == Decimal("3104.00")
    assert cotisation_ae_attendue_2025(Decimal("52000")) == Decimal("681.20")
    assert cotisation_rqap_attendue_2025(Decimal("52000")) == Decimal("256.88")


def test_cotisations_attendues_plafonnees():
    assert cotisation_rrq_attendue_2025(Decimal("90000")) == Decimal("4735.20")
    assert cotisation_ae_attendue_2025(Decimal("90000")) == Decimal("860.67")
    assert cotisation_rqap_attendue_2025(Decimal("120000")) == Decimal("484.12")


@pytest.mark.parametrize(
    "champ",
    [
        "rrq_ba",
        "rrq_bb",
        "gains_admissibles_rrq",
        "assurance_emploi",
        "gains_assurables_ae",
        "rqap",
        "revenus_assujettis_rqap",
    ],
)
def test_montant_negatif_refuse(champ):
    with pytest.raises(ValueError, match="négatif"):
        valider_cotisations_excedentaires_2025(
            _profil(**{champ: Decimal("-0.01")})
        )


@pytest.mark.parametrize(
    "champ, message",
    [
        ("valide_par_comptable", "comptable"),
        (
            "resident_quebec_31_decembre_2025",
            "résidence au Québec",
        ),
        ("emploi_quebec_uniquement", "emplois exercés au Québec"),
        ("rrq_uniquement_sans_rpc", "sans cotisation au RPC"),
        ("aucun_travail_autonome", "travail autonome"),
        ("profil_rrq_standard_18_64", "18 à 64 ans"),
        (
            "aucun_cas_particulier_ae",
            "cas particuliers d'assurance-emploi",
        ),
        (
            "aucun_cas_particulier_rqap",
            "cas particuliers du RQAP",
        ),
        (
            "calcul_standard_confirme",
            "calcul standard",
        ),
    ],
)
def test_confirmations_obligatoires(champ, message):
    with pytest.raises(ValueError, match=message):
        valider_cotisations_excedentaires_2025(
            _profil(**{champ: False})
        )


def test_source_obligatoire():
    with pytest.raises(ValueError, match="source"):
        valider_cotisations_excedentaires_2025(
            _profil(source=" ")
        )


def test_profil_normal_52000_sans_remboursement():
    resultat = calculer_remboursements_cotisations_2025(_profil())
    assert resultat.rrq_ligne_452 == Decimal("0")
    assert resultat.assurance_emploi_ligne_45000 == Decimal("0")
    assert resultat.rqap_ligne_457 == Decimal("0")
    assert resultat.total == Decimal("0")


def test_rrq_depassement_selon_gains():
    donnees = _profil(rrq_ba=Decimal("3200.00"))
    assert remboursement_rrq_2025(donnees) == Decimal("96.00")


def test_rrq_depassement_au_dessus_du_maximum():
    donnees = _profil(
        rrq_ba=Decimal("4400.00"),
        rrq_bb=Decimal("400.00"),
        gains_admissibles_rrq=Decimal("90000"),
    )
    assert remboursement_rrq_2025(donnees) == Decimal("64.80")


def test_ae_depassement_selon_gains():
    donnees = _profil(assurance_emploi=Decimal("700.00"))
    assert remboursement_assurance_emploi_2025(donnees) == Decimal("18.80")


def test_ae_depassement_au_dessus_du_maximum():
    donnees = _profil(
        assurance_emploi=Decimal("900.00"),
        gains_assurables_ae=Decimal("90000"),
    )
    assert remboursement_assurance_emploi_2025(donnees) == Decimal("39.33")


def test_rqap_depassement_selon_revenus():
    donnees = _profil(rqap=Decimal("300.00"))
    assert remboursement_rqap_2025(donnees) == Decimal("43.12")


def test_rqap_depassement_au_dessus_du_maximum():
    donnees = _profil(
        rqap=Decimal("500.00"),
        revenus_assujettis_rqap=Decimal("120000"),
    )
    assert remboursement_rqap_2025(donnees) == Decimal("15.88")


def test_rqap_revenus_sous_2000_rembourse_tout():
    donnees = _profil(
        rqap=Decimal("8.50"),
        revenus_assujettis_rqap=Decimal("1999.99"),
    )
    assert remboursement_rqap_2025(donnees) == Decimal("8.50")


def test_rqap_revenus_exactement_2000_utilise_calcul_standard():
    donnees = _profil(
        rqap=Decimal("9.88"),
        revenus_assujettis_rqap=Decimal("2000"),
    )
    assert remboursement_rqap_2025(donnees) == Decimal("0")


def test_resultat_combine_les_trois_remboursements():
    donnees = _profil(
        rrq_ba=Decimal("3200.00"),
        assurance_emploi=Decimal("700.00"),
        rqap=Decimal("300.00"),
    )
    resultat = calculer_remboursements_cotisations_2025(donnees)

    assert resultat.rrq_ligne_452 == Decimal("96.00")
    assert resultat.assurance_emploi_ligne_45000 == Decimal("18.80")
    assert resultat.rqap_ligne_457 == Decimal("43.12")
    assert resultat.total == Decimal("157.92")
