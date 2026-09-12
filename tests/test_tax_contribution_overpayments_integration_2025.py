from dataclasses import replace
from decimal import Decimal

import pytest

from src.comptaprivee.tax_contribution_overpayments_2025 import (
    CotisationsExcedentaires2025,
)
from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
    formater_estimation_fiscale_2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000


def _dossier_avec_excedents():
    dossier = _dossier_52000()
    remplacements = {
        ("T4", "17"): Decimal("3200.00"),
        ("RL-1", "B.A"): Decimal("3200.00"),
        ("T4", "18"): Decimal("700.00"),
        ("RL-1", "C"): Decimal("700.00"),
        ("T4", "55"): Decimal("300.00"),
        ("RL-1", "H"): Decimal("300.00"),
    }

    donnees = []
    for donnee in dossier.donnees_validees:
        cle = (donnee.type_document, donnee.case)
        if cle in remplacements:
            montant = remplacements[cle]
            donnee = replace(
                donnee,
                valeur_extraite=montant,
                valeur_validee=montant,
            )
        donnees.append(donnee)

    return replace(
        dossier,
        donnees_validees=tuple(donnees),
    )


def _profil_excedentaire():
    return CotisationsExcedentaires2025(
        rrq_ba=Decimal("3200.00"),
        rrq_bb=Decimal("0"),
        gains_admissibles_rrq=Decimal("52000"),
        assurance_emploi=Decimal("700.00"),
        gains_assurables_ae=Decimal("52000"),
        rqap=Decimal("300.00"),
        revenus_assujettis_rqap=Decimal("52000"),
        source="T4 / RL-1 validés",
        valide_par_comptable=True,
        resident_quebec_31_decembre_2025=True,
        emploi_quebec_uniquement=True,
        rrq_uniquement_sans_rpc=True,
        aucun_travail_autonome=True,
        profil_rrq_standard_18_64=True,
        aucun_cas_particulier_ae=True,
        aucun_cas_particulier_rqap=True,
        calcul_standard_confirme=True,
    )


def test_sans_cotisations_excedentaires_resultat_reste_identique():
    e = calculer_estimation_fiscale_2025(_dossier_52000())

    assert e.rapprochement.impot_total_preliminaire == Decimal("8088.95")
    assert e.rapprochement.remboursement_estime == Decimal("5611.05")
    assert e.rapprochement.remboursements_cotisations_totaux == Decimal("0")


def test_dossier_excedentaire_sans_validation_reste_refuse():
    with pytest.raises(ValueError, match="incohérente"):
        calculer_estimation_fiscale_2025(
            _dossier_avec_excedents()
        )


def test_excedents_valides_augmentent_remboursement():
    e = calculer_estimation_fiscale_2025(
        _dossier_avec_excedents(),
        cotisations_excedentaires=_profil_excedentaire(),
    )

    r = e.rapprochement
    assert r.remboursement_rrq_excedentaire == Decimal("96.00")
    assert r.remboursement_ae_excedentaire == Decimal("18.80")
    assert r.remboursement_rqap_excedentaire == Decimal("43.12")
    assert r.remboursements_cotisations_totaux == Decimal("157.92")
    assert r.impot_total_preliminaire == Decimal("8088.95")
    assert r.remboursement_estime == Decimal("5768.97")


def test_estimation_conserve_profil_cotisations_excedentaires():
    profil = _profil_excedentaire()
    e = calculer_estimation_fiscale_2025(
        _dossier_avec_excedents(),
        cotisations_excedentaires=profil,
    )
    assert e.cotisations_excedentaires == profil


def test_profil_doit_correspondre_aux_cotisations_du_dossier():
    profil = replace(
        _profil_excedentaire(),
        rrq_ba=Decimal("3199.00"),
    )
    with pytest.raises(ValueError, match="RRQ B.A.*correspondre"):
        calculer_estimation_fiscale_2025(
            _dossier_avec_excedents(),
            cotisations_excedentaires=profil,
        )


def test_profil_doit_correspondre_aux_gains_du_dossier():
    profil = replace(
        _profil_excedentaire(),
        gains_assurables_ae=Decimal("51000"),
    )
    with pytest.raises(ValueError, match="gains assurables AE.*correspondre"):
        calculer_estimation_fiscale_2025(
            _dossier_avec_excedents(),
            cotisations_excedentaires=profil,
        )


def test_credit_federal_n_utilise_pas_les_cotisations_remboursees():
    e = calculer_estimation_fiscale_2025(
        _dossier_avec_excedents(),
        cotisations_excedentaires=_profil_excedentaire(),
    )

    assert e.federal.assurance_emploi_admissible == Decimal("681.20")
    assert e.federal.rqap_admissible == Decimal("256.88")


def test_resume_affiche_trois_remboursements():
    e = calculer_estimation_fiscale_2025(
        _dossier_avec_excedents(),
        cotisations_excedentaires=_profil_excedentaire(),
    )
    resume = formater_estimation_fiscale_2025(e)

    assert "COTISATIONS EXCÉDENTAIRES VALIDÉES" in resume
    assert "RRQ — ligne Québec 452 : 96,00 $" in resume
    assert "Assurance-emploi — ligne fédérale 45000 : 18,80 $" in resume
    assert "RQAP — ligne Québec 457 : 43,12 $" in resume
    assert "Total remboursable : 157,92 $" in resume
    assert "T4 / RL-1 validés" in resume


def test_limitation_remboursements_est_remplacee():
    e = calculer_estimation_fiscale_2025(
        _dossier_avec_excedents(),
        cotisations_excedentaires=_profil_excedentaire(),
    )

    assert (
        "Remboursements de cotisations excédentaires RRQ/AE/RQAP inclus."
        in e.rapprochement.limitations
    )
    assert (
        "Aucun remboursement de cotisations excédentaires RRQ/AE/RQAP."
        not in e.rapprochement.limitations
    )
