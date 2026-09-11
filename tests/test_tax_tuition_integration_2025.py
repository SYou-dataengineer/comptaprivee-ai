from decimal import Decimal

import pytest

from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
    formater_estimation_fiscale_2025,
)
from src.comptaprivee.tax_tuition_2025 import FraisScolarite2025
from tests.test_tax_estimation_2025 import _dossier_52000


def _scolarite_3000():
    return FraisScolarite2025(
        montant_admissible_federal=Decimal("3000"),
        montant_admissible_quebec=Decimal("3000"),
        source_federale="T2202 - établissement admissible",
        source_quebec="Reçu officiel - établissement admissible",
        valide_par_comptable=True,
        piece_federale_confirmee=True,
        recu_officiel_quebec_confirme=True,
        seuil_100_confirme=True,
        remboursements_soustraits=True,
        frais_2025_uniquement=True,
        aucun_report_anterieur=True,
        aucun_transfert=True,
        credit_canadien_formation_non_reclame=True,
        profil_resident_quebec_simple=True,
    )


def test_sans_scolarite_resultat_reste_identique():
    e = calculer_estimation_fiscale_2025(_dossier_52000())
    assert e.rapprochement.impot_total_preliminaire == Decimal("8088.95")
    assert e.rapprochement.remboursement_estime == Decimal("5611.05")
    assert e.frais_scolarite.montant_admissible_federal == Decimal("0")
    assert e.frais_scolarite.montant_admissible_quebec == Decimal("0")


def test_scolarite_3000_reduit_impot_federal():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        frais_scolarite=_scolarite_3000(),
    )
    assert e.federal.impot_federal_de_base == Decimal("3966.90")


def test_scolarite_3000_reduit_impot_quebec():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        frais_scolarite=_scolarite_3000(),
    )
    assert e.quebec.impot_quebec_preliminaire == Decimal("4173.36")


def test_scolarite_3000_recalcule_remboursement():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        frais_scolarite=_scolarite_3000(),
    )
    assert e.rapprochement.impot_total_preliminaire == Decimal("7485.72")
    assert e.rapprochement.remboursement_estime == Decimal("6214.28")


def test_estimation_conserve_scolarite_validee():
    frais = _scolarite_3000()
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        frais_scolarite=frais,
    )
    assert e.frais_scolarite == frais


def test_scolarite_invalide_bloque_estimation():
    frais = FraisScolarite2025(
        montant_admissible_federal=Decimal("3000"),
        source_federale="T2202",
        valide_par_comptable=False,
        piece_federale_confirmee=True,
        seuil_100_confirme=True,
        remboursements_soustraits=True,
        frais_2025_uniquement=True,
        aucun_report_anterieur=True,
        aucun_transfert=True,
        credit_canadien_formation_non_reclame=True,
        profil_resident_quebec_simple=True,
    )
    with pytest.raises(ValueError):
        calculer_estimation_fiscale_2025(
            _dossier_52000(),
            frais_scolarite=frais,
        )


def test_resume_affiche_scolarite_et_credits():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        frais_scolarite=_scolarite_3000(),
    )
    resume = formater_estimation_fiscale_2025(e)
    assert "FRAIS DE SCOLARITÉ / EXAMEN VALIDÉS" in resume
    assert "Crédit fédéral — ligne 32300 : 435,00 $" in resume
    assert "Crédit Québec — ligne 398 : 240,00 $" in resume
    assert "6\u00a0214,28 $" in resume


def test_sources_scolarite_affichees_dans_resume():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        frais_scolarite=_scolarite_3000(),
    )
    resume = formater_estimation_fiscale_2025(e)
    assert "T2202 - établissement admissible" in resume
    assert "Reçu officiel - établissement admissible" in resume


def test_limitation_rapprochement_reconnait_scolarite():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        frais_scolarite=_scolarite_3000(),
    )
    assert (
        "Aucun crédit familial, médical ou handicap."
        in e.rapprochement.limitations
    )
    assert (
        "Aucun crédit familial, médical, étude ou handicap."
        not in e.rapprochement.limitations
    )
