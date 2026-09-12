from decimal import Decimal

import pytest

from src.comptaprivee.tax_drug_insurance_2025 import (
    AssuranceMedicamentsQuebec2025,
)
from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
    formater_estimation_fiscale_2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000


def _public_max():
    return AssuranceMedicamentsQuebec2025(
        type_couverture="public",
        couverture_toute_annee=True,
        sans_conjoint_31_decembre_2025=True,
        revenu_ligne_275=Decimal("50095.00"),
        revenu_ligne_48_annexe_k=Decimal("10000"),
        aucun_mois_exempt=True,
        carte_ramq_valide_2025=True,
        situation_validee_par_comptable=True,
        aucun_cas_particulier=True,
        source="Annexe K / ligne 447 validée",
        code_case_449="",
    )


def _collectif():
    return AssuranceMedicamentsQuebec2025(
        type_couverture="collectif",
        couverture_toute_annee=True,
        sans_conjoint_31_decembre_2025=True,
        revenu_ligne_275=Decimal("50095.00"),
        revenu_ligne_48_annexe_k=Decimal("0"),
        aucun_mois_exempt=False,
        carte_ramq_valide_2025=False,
        situation_validee_par_comptable=True,
        aucun_cas_particulier=True,
        source="Assurance collective employeur",
        code_case_449="14",
    )


def test_sans_assurance_resultat_reste_identique():
    e = calculer_estimation_fiscale_2025(_dossier_52000())

    assert e.rapprochement.impot_total_preliminaire == Decimal("8088.95")
    assert e.rapprochement.remboursement_estime == Decimal("5611.05")
    assert e.rapprochement.cotisation_assurance_medicaments == Decimal("0")
    assert e.assurance_medicaments.type_couverture == ""


def test_public_max_ajoute_755_au_total():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        assurance_medicaments=_public_max(),
    )

    assert e.rapprochement.cotisation_assurance_medicaments == Decimal("755.00")
    assert e.rapprochement.impot_total_preliminaire == Decimal("8843.95")
    assert e.rapprochement.remboursement_estime == Decimal("4856.05")


def test_collectif_conserve_cotisation_zero():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        assurance_medicaments=_collectif(),
    )

    assert e.rapprochement.cotisation_assurance_medicaments == Decimal("0")
    assert e.rapprochement.impot_total_preliminaire == Decimal("8088.95")
    assert e.rapprochement.remboursement_estime == Decimal("5611.05")


def test_estimation_conserve_assurance_medicaments():
    assurance = _public_max()
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        assurance_medicaments=assurance,
    )
    assert e.assurance_medicaments == assurance


def test_revenu_ligne_275_doit_correspondre_au_revenu_net_quebec():
    assurance = _public_max()
    assurance = AssuranceMedicamentsQuebec2025(
        **{
            **assurance.__dict__,
            "revenu_ligne_275": Decimal("40000"),
        }
    )

    with pytest.raises(ValueError, match="ligne 275"):
        calculer_estimation_fiscale_2025(
            _dossier_52000(),
            assurance_medicaments=assurance,
        )


def test_calcul_progressif_annexe_k_reste_refuse():
    assurance = _public_max()
    assurance = AssuranceMedicamentsQuebec2025(
        **{
            **assurance.__dict__,
            "revenu_ligne_48_annexe_k": Decimal("5000"),
        }
    )

    with pytest.raises(ValueError, match="progressif"):
        calculer_estimation_fiscale_2025(
            _dossier_52000(),
            assurance_medicaments=assurance,
        )


def test_resume_affiche_assurance_publique():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        assurance_medicaments=_public_max(),
    )
    resume = formater_estimation_fiscale_2025(e)

    assert "ASSURANCE MÉDICAMENTS QUÉBEC VALIDÉE" in resume
    assert "Régime public" in resume
    assert "Cotisation Québec — ligne 447 : 755,00 $" in resume
    assert "Annexe K / ligne 447 validée" in resume
    assert "50\u00a0095,00 $" in resume


def test_resume_affiche_collectif_et_code_14():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        assurance_medicaments=_collectif(),
    )
    resume = formater_estimation_fiscale_2025(e)

    assert "Couverture collective" in resume
    assert "Code d'exemption — case 449 : 14" in resume
    assert "Cotisation Québec — ligne 447 : 0,00 $" in resume


def test_limitation_prime_retiree_quand_cotisation_incluse():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        assurance_medicaments=_public_max(),
    )

    assert (
        "Aucune prime d'assurance médicaments ni contribution Québec additionnelle."
        not in e.rapprochement.limitations
    )
    assert (
        "Cotisation au régime d'assurance médicaments du Québec incluse."
        in e.rapprochement.limitations
    )
