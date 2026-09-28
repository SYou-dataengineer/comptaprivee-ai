from dataclasses import replace
from decimal import Decimal

import pytest

from src.comptaprivee.tax_income_2025 import RevenuNetImposable2025
from src.comptaprivee.tax_other_deductions_2025 import (
    AutresDeductions2025,
    appliquer_autres_deductions_2025,
    lignes_resume_autres_deductions_2025,
    valider_autres_deductions_2025,
)


ZERO = Decimal("0")


def _revenu() -> RevenuNetImposable2025:
    return RevenuNetImposable2025(
        client="Client Test",
        annee_fiscale=2025,
        province="Québec",
        revenu_total_federal=Decimal("52000"),
        deduction_rrq_amelioree_federale=Decimal("1485"),
        revenu_net_federal=Decimal("50515"),
        revenu_imposable_federal=Decimal("50515"),
        revenu_total_quebec=Decimal("52000"),
        deduction_travailleur_quebec=Decimal("935"),
        deduction_rrq_quebec=Decimal("1485"),
        revenu_net_quebec=Decimal("49580"),
        revenu_imposable_quebec=Decimal("49580"),
        profil="Emploi Québec simple 2025",
        limitations=("Aucune autre déduction de revenu net ou imposable.",),
    )


def _profil(
    federal="1200",
    quebec="900",
) -> AutresDeductions2025:
    return AutresDeductions2025(
        deduction_federale_23200=Decimal(federal),
        deduction_quebec_250_code17=Decimal(quebec),
        nature_federale="Autre montant déductible validé",
        nature_quebec="Autre déduction validée code 17",
        source_federale="Pièce fédérale 2025 validée",
        source_quebec="Pièce Québec 2025 validée",
        valide_par_comptable=True,
        montant_federal_deja_etabli_confirme=True,
        montant_quebec_deja_etabli_confirme=True,
        aucune_autre_ligne_ou_bloc_applicable_confirme=True,
    )


def test_profil_vide_est_accepte():
    assert valider_autres_deductions_2025(
        AutresDeductions2025()
    ) == AutresDeductions2025()


@pytest.mark.parametrize(
    "champ",
    [
        "deduction_federale_23200",
        "deduction_quebec_250_code17",
    ],
)
def test_montants_negatifs_refuses(champ):
    profil = replace(AutresDeductions2025(), **{champ: Decimal("-1")})
    with pytest.raises(ValueError):
        valider_autres_deductions_2025(profil)


@pytest.mark.parametrize("valeur", [Decimal("NaN"), Decimal("Infinity")])
@pytest.mark.parametrize(
    "champ",
    [
        "deduction_federale_23200",
        "deduction_quebec_250_code17",
    ],
)
def test_montants_non_finis_refuses(champ, valeur):
    profil = replace(AutresDeductions2025(), **{champ: valeur})
    with pytest.raises(ValueError):
        valider_autres_deductions_2025(profil)


def test_montants_arrondis_au_cent():
    valide = valider_autres_deductions_2025(
        _profil("1200.005", "899.994")
    )
    assert valide.deduction_federale_23200 == Decimal("1200.01")
    assert valide.deduction_quebec_250_code17 == Decimal("899.99")


@pytest.mark.parametrize(
    "champ",
    [
        "remboursement_ae_ou_rqap",
        "recuperation_prestations_sociales_23500",
        "retrait_reer_ou_t3012a",
        "frais_juridiques",
        "remboursement_pension_alimentaire",
        "transfert_ou_cotisations_inutilisees_regime",
        "soutien_personne_handicapee",
        "celiapp_montant_deja_inclus",
        "abri_fiscal_ou_revenu_fractionne",
        "autre_traitement_specialise",
    ],
)
def test_cas_hors_perimetre_refuses(champ):
    with pytest.raises(ValueError, match="hors périmètre 4F"):
        valider_autres_deductions_2025(
            replace(_profil(), **{champ: True})
        )


def test_validation_comptable_obligatoire():
    with pytest.raises(ValueError, match="validées par le comptable"):
        valider_autres_deductions_2025(
            replace(_profil(), valide_par_comptable=False)
        )


def test_confirmation_aucun_autre_bloc_obligatoire():
    with pytest.raises(ValueError, match="aucune autre ligne"):
        valider_autres_deductions_2025(
            replace(
                _profil(),
                aucune_autre_ligne_ou_bloc_applicable_confirme=False,
            )
        )


def test_confirmation_federale_obligatoire():
    with pytest.raises(ValueError, match="fédéral ligne 23200"):
        valider_autres_deductions_2025(
            replace(
                _profil(),
                montant_federal_deja_etabli_confirme=False,
            )
        )


def test_confirmation_quebec_obligatoire():
    with pytest.raises(ValueError, match="Québec ligne 250 code 17"):
        valider_autres_deductions_2025(
            replace(
                _profil(),
                montant_quebec_deja_etabli_confirme=False,
            )
        )


def test_nature_federale_obligatoire():
    with pytest.raises(ValueError, match="nature de la déduction fédérale"):
        valider_autres_deductions_2025(
            replace(_profil(), nature_federale=" ")
        )


def test_nature_quebec_obligatoire():
    with pytest.raises(ValueError, match="nature de la déduction Québec"):
        valider_autres_deductions_2025(
            replace(_profil(), nature_quebec=" ")
        )


def test_source_federale_obligatoire():
    with pytest.raises(ValueError, match="source fédérale"):
        valider_autres_deductions_2025(
            replace(_profil(), source_federale=" ")
        )


def test_source_quebec_obligatoire():
    with pytest.raises(ValueError, match="source Québec"):
        valider_autres_deductions_2025(
            replace(_profil(), source_quebec=" ")
        )


def test_federal_seul_n_exige_pas_quebec():
    profil = replace(
        _profil(quebec="0"),
        nature_quebec="",
        source_quebec="",
        montant_quebec_deja_etabli_confirme=False,
    )
    valide = valider_autres_deductions_2025(profil)
    assert valide.deduction_federale_23200 == Decimal("1200.00")


def test_quebec_seul_n_exige_pas_federal():
    profil = replace(
        _profil(federal="0"),
        nature_federale="",
        source_federale="",
        montant_federal_deja_etabli_confirme=False,
    )
    valide = valider_autres_deductions_2025(profil)
    assert valide.deduction_quebec_250_code17 == Decimal("900.00")


def test_application_reduit_separement_federal_et_quebec():
    revenu = appliquer_autres_deductions_2025(
        _revenu(),
        _profil(),
    )
    assert revenu.revenu_total_federal == Decimal("52000")
    assert revenu.revenu_total_quebec == Decimal("52000")
    assert revenu.revenu_net_federal == Decimal("49315.00")
    assert revenu.revenu_imposable_federal == Decimal("49315.00")
    assert revenu.revenu_net_quebec == Decimal("48680.00")
    assert revenu.revenu_imposable_quebec == Decimal("48680.00")


def test_application_plafonne_a_zero():
    revenu = appliquer_autres_deductions_2025(
        _revenu(),
        _profil("999999", "999999"),
    )
    assert revenu.revenu_net_federal == ZERO
    assert revenu.revenu_imposable_federal == ZERO
    assert revenu.revenu_net_quebec == ZERO
    assert revenu.revenu_imposable_quebec == ZERO


def test_application_refuse_autre_annee():
    with pytest.raises(ValueError, match="uniquement l'année 2025"):
        appliquer_autres_deductions_2025(
            replace(_revenu(), annee_fiscale=2024),
            _profil(),
        )


def test_resume_contient_lignes_natures_et_sources():
    texte = "\n".join(lignes_resume_autres_deductions_2025(_profil()))
    assert "BLOC 4F" in texte
    assert "ligne 23200" in texte
    assert "ligne 250, code 17" in texte
    assert "case 249" in texte
    assert "1200.00 $" in texte
    assert "900.00 $" in texte
    assert "Autre montant déductible validé" in texte
    assert "Pièce Québec 2025 validée" in texte


def test_resume_vide_si_aucun_montant():
    assert lignes_resume_autres_deductions_2025(
        AutresDeductions2025()
    ) == []
