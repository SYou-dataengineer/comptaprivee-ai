from decimal import Decimal

import pytest

from src.comptaprivee.tax_drug_insurance_2025 import (
    AssuranceMedicamentsQuebec2025,
    COTISATION_MAX_RAMQ_2025,
    SEUIL_LIGNE_48_MAX_SANS_CONJOINT_2025,
    SEUIL_REVENU_SANS_CONJOINT_2025,
    aucune_assurance_medicaments_2025,
    code_exemption_case_449_2025,
    cotisation_assurance_medicaments_2025,
    valider_assurance_medicaments_2025,
)


def _public(**modifications):
    valeurs = {
        "type_couverture": "public",
        "couverture_toute_annee": True,
        "sans_conjoint_31_decembre_2025": True,
        "revenu_ligne_275": Decimal("40000"),
        "revenu_ligne_48_annexe_k": Decimal("10000"),
        "aucun_mois_exempt": True,
        "carte_ramq_valide_2025": True,
        "situation_validee_par_comptable": True,
        "aucun_cas_particulier": True,
        "source": "Annexe K / ligne 447",
        "code_case_449": "",
    }
    valeurs.update(modifications)
    return AssuranceMedicamentsQuebec2025(**valeurs)


def _collectif(**modifications):
    valeurs = {
        "type_couverture": "collectif",
        "couverture_toute_annee": True,
        "sans_conjoint_31_decembre_2025": True,
        "revenu_ligne_275": Decimal("52000"),
        "revenu_ligne_48_annexe_k": Decimal("0"),
        "aucun_mois_exempt": False,
        "carte_ramq_valide_2025": False,
        "situation_validee_par_comptable": True,
        "aucun_cas_particulier": True,
        "source": "Assurance collective employeur",
        "code_case_449": "14",
    }
    valeurs.update(modifications)
    return AssuranceMedicamentsQuebec2025(**valeurs)


def test_profil_vide_est_valide():
    assurance = aucune_assurance_medicaments_2025()
    assert valider_assurance_medicaments_2025(assurance) == assurance
    assert cotisation_assurance_medicaments_2025(assurance) == Decimal("0")


def test_constantes_officielles_2025():
    assert COTISATION_MAX_RAMQ_2025 == Decimal("755.00")
    assert SEUIL_REVENU_SANS_CONJOINT_2025 == Decimal("19890")
    assert SEUIL_LIGNE_48_MAX_SANS_CONJOINT_2025 == Decimal("8181")


@pytest.mark.parametrize(
    "champ",
    ["revenu_ligne_275", "revenu_ligne_48_annexe_k"],
)
def test_montant_negatif_refuse(champ):
    with pytest.raises(ValueError, match="négati"):
        valider_assurance_medicaments_2025(
            _public(**{champ: Decimal("-1")})
        )


def test_type_invalide_refuse():
    with pytest.raises(ValueError, match="collectif.*public"):
        valider_assurance_medicaments_2025(
            _public(type_couverture="autre")
        )


def test_donnees_sans_type_refusees():
    with pytest.raises(ValueError, match="type de couverture"):
        valider_assurance_medicaments_2025(
            AssuranceMedicamentsQuebec2025(
                revenu_ligne_275=Decimal("20000")
            )
        )


def test_validation_comptable_obligatoire():
    with pytest.raises(ValueError, match="comptable"):
        valider_assurance_medicaments_2025(
            _public(situation_validee_par_comptable=False)
        )


def test_couverture_toute_annee_obligatoire():
    with pytest.raises(ValueError, match="toute l'année"):
        valider_assurance_medicaments_2025(
            _public(couverture_toute_annee=False)
        )


def test_profil_avec_conjoint_refuse():
    with pytest.raises(ValueError, match="sans conjoint"):
        valider_assurance_medicaments_2025(
            _public(sans_conjoint_31_decembre_2025=False)
        )


def test_cas_particulier_refuse():
    with pytest.raises(ValueError, match="cas particuliers"):
        valider_assurance_medicaments_2025(
            _public(aucun_cas_particulier=False)
        )


def test_source_obligatoire():
    with pytest.raises(ValueError, match="source"):
        valider_assurance_medicaments_2025(
            _public(source=" ")
        )


def test_collectif_code_14_cotisation_zero():
    assurance = _collectif(code_case_449="14")
    assert cotisation_assurance_medicaments_2025(assurance) == Decimal("0")
    assert code_exemption_case_449_2025(assurance) == "14"


def test_collectif_code_16_cotisation_zero():
    assurance = _collectif(code_case_449="16")
    assert cotisation_assurance_medicaments_2025(assurance) == Decimal("0")
    assert code_exemption_case_449_2025(assurance) == "16"


def test_collectif_code_invalide_refuse():
    with pytest.raises(ValueError, match="codes 14 ou 16"):
        valider_assurance_medicaments_2025(
            _collectif(code_case_449="32")
        )


def test_public_exige_carte_ramq():
    with pytest.raises(ValueError, match="RAMQ"):
        valider_assurance_medicaments_2025(
            _public(carte_ramq_valide_2025=False)
        )


def test_public_exige_aucun_mois_exempt():
    with pytest.raises(ValueError, match="mois d'exemption"):
        valider_assurance_medicaments_2025(
            _public(aucun_mois_exempt=False)
        )


def test_public_revenu_19890_exempte_code_32():
    assurance = _public(
        revenu_ligne_275=Decimal("19890"),
        revenu_ligne_48_annexe_k=Decimal("0"),
        code_case_449="32",
    )
    assert cotisation_assurance_medicaments_2025(assurance) == Decimal("0")
    assert code_exemption_case_449_2025(assurance) == "32"


def test_public_revenu_sous_seuil_code_32_automatique():
    assurance = _public(
        revenu_ligne_275=Decimal("15000"),
        revenu_ligne_48_annexe_k=Decimal("0"),
        code_case_449="",
    )
    assert cotisation_assurance_medicaments_2025(assurance) == Decimal("0")
    assert code_exemption_case_449_2025(assurance) == "32"


def test_public_bas_revenu_ligne48_non_zero_refusee():
    with pytest.raises(ValueError, match="ligne 48 doit rester à zéro"):
        valider_assurance_medicaments_2025(
            _public(
                revenu_ligne_275=Decimal("19890"),
                revenu_ligne_48_annexe_k=Decimal("1"),
            )
        )


def test_public_haut_revenu_exige_ligne48():
    with pytest.raises(ValueError, match="ligne 48.*obligatoire"):
        valider_assurance_medicaments_2025(
            _public(
                revenu_ligne_275=Decimal("30000"),
                revenu_ligne_48_annexe_k=Decimal("0"),
            )
        )


def test_public_calcul_progressif_refuse_pour_linstant():
    with pytest.raises(ValueError, match="progressif"):
        cotisation_assurance_medicaments_2025(
            _public(
                revenu_ligne_275=Decimal("25000"),
                revenu_ligne_48_annexe_k=Decimal("5000"),
            )
        )


def test_public_ligne48_exactement_8181_reste_progressive():
    with pytest.raises(ValueError, match="progressif"):
        cotisation_assurance_medicaments_2025(
            _public(
                revenu_ligne_48_annexe_k=Decimal("8181")
            )
        )


def test_public_ligne48_superieure_8181_cotisation_max():
    assurance = _public(
        revenu_ligne_48_annexe_k=Decimal("8181.01")
    )
    assert (
        cotisation_assurance_medicaments_2025(assurance)
        == Decimal("755.00")
    )
    assert code_exemption_case_449_2025(assurance) == ""


def test_code_32_refuse_si_revenu_depasse_seuil():
    with pytest.raises(ValueError, match="ne s'applique pas"):
        valider_assurance_medicaments_2025(
            _public(
                revenu_ligne_275=Decimal("40000"),
                revenu_ligne_48_annexe_k=Decimal("10000"),
                code_case_449="32",
            )
        )
