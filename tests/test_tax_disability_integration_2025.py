from decimal import Decimal

import pytest

from src.comptaprivee.tax_disability_2025 import (
    CreditDeficience2025,
)
from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
    formater_estimation_fiscale_2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000


def _deficience_complete():
    return CreditDeficience2025(
        reclamer_federal=True,
        reclamer_quebec=True,
        source_federale="T2201 / approbation ARC",
        source_quebec="Attestation professionnelle Québec",
        valide_par_comptable=True,
        age_18_plus_au_1_janvier_2025=True,
        deficience_12_mois_confirmee=True,
        profil_soi_meme_resident_quebec=True,
        ciph_approuve_arc=True,
        attestation_quebec_confirmee=True,
        aucun_conflit_soins_prepose_etablissement=True,
        aucun_transfert_federal=True,
    )


def test_sans_deficience_resultat_reste_identique():
    e = calculer_estimation_fiscale_2025(_dossier_52000())

    assert e.rapprochement.impot_total_preliminaire == Decimal("8088.95")
    assert e.rapprochement.remboursement_estime == Decimal("5611.05")
    assert e.credit_deficience.reclamer_federal is False
    assert e.credit_deficience.reclamer_quebec is False


def test_deficience_complete_reduit_impot_federal():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        credit_deficience=_deficience_complete(),
    )

    assert e.federal.impot_federal_de_base == Decimal("2931.89")


def test_deficience_complete_reduit_impot_quebec():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        credit_deficience=_deficience_complete(),
    )

    assert e.quebec.impot_quebec_preliminaire == Decimal("3836.14")


def test_deficience_complete_recalcule_remboursement():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        credit_deficience=_deficience_complete(),
    )

    assert e.rapprochement.impot_total_preliminaire == Decimal("6284.27")
    assert e.rapprochement.remboursement_estime == Decimal("7415.73")


def test_estimation_conserve_credit_deficience():
    credit = _deficience_complete()

    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        credit_deficience=credit,
    )

    assert e.credit_deficience == credit


def test_deficience_invalide_bloque_estimation():
    credit = CreditDeficience2025(
        reclamer_federal=True,
        valide_par_comptable=True,
        age_18_plus_au_1_janvier_2025=True,
        deficience_12_mois_confirmee=True,
        profil_soi_meme_resident_quebec=True,
        ciph_approuve_arc=False,
        aucun_conflit_soins_prepose_etablissement=True,
        aucun_transfert_federal=True,
        source_federale="T2201",
    )

    with pytest.raises(ValueError, match="CIPH"):
        calculer_estimation_fiscale_2025(
            _dossier_52000(),
            credit_deficience=credit,
        )


def test_resume_affiche_deficience_et_credits():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        credit_deficience=_deficience_complete(),
    )
    resume = formater_estimation_fiscale_2025(e)

    assert "HANDICAP / DÉFICIENCE VALIDÉ(E)" in resume
    assert "Crédit fédéral — ligne 31600 : 1\u00a0470,01 $" in resume
    assert "Crédit Québec — ligne 376 : 577,22 $" in resume
    assert "7\u00a0415,73 $" in resume


def test_resume_affiche_sources_deficience():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        credit_deficience=_deficience_complete(),
    )
    resume = formater_estimation_fiscale_2025(e)

    assert "T2201 / approbation ARC" in resume
    assert "Attestation professionnelle Québec" in resume


def test_limitation_rapprochement_reconnait_handicap():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        credit_deficience=_deficience_complete(),
    )

    assert (
        "Aucun crédit familial, médical ou étude."
        in e.rapprochement.limitations
    )
    assert (
        "Aucun crédit familial, médical, étude ou handicap."
        not in e.rapprochement.limitations
    )
