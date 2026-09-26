from dataclasses import replace
from decimal import Decimal

import pytest

from src.comptaprivee.tax_income_2025 import RevenuNetImposable2025
from src.comptaprivee.tax_moving_expenses_2025 import (
    FraisDemenagement2025,
    appliquer_frais_demenagement_2025,
    lignes_resume_frais_demenagement_2025,
    valider_frais_demenagement_2025,
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
    federal: str = "2200",
    quebec: str = "1800",
) -> FraisDemenagement2025:
    return FraisDemenagement2025(
        deduction_federale_t1m=Decimal(federal),
        deduction_quebec_tp348=Decimal(quebec),
        source_federale="T1-M 2025 validé",
        source_quebec="TP-348 2025 validé",
        valide_par_comptable=True,
        salarie_ordinaire_confirme=True,
        demenagement_pour_emploi_confirme=True,
        rapprochement_40km_confirme=True,
        demenagement_interieur_canada_confirme=True,
        remboursements_employeur_pris_en_compte_confirme=True,
        t1m_confirme=True,
        tp348_confirme=True,
    )


def test_profil_vide_est_accepte():
    assert valider_frais_demenagement_2025(
        FraisDemenagement2025()
    ) == FraisDemenagement2025()


@pytest.mark.parametrize(
    "champ",
    ["deduction_federale_t1m", "deduction_quebec_tp348"],
)
def test_montants_negatifs_refuses(champ):
    profil = replace(FraisDemenagement2025(), **{champ: Decimal("-1")})
    with pytest.raises(ValueError):
        valider_frais_demenagement_2025(profil)


@pytest.mark.parametrize("valeur", [Decimal("NaN"), Decimal("Infinity")])
@pytest.mark.parametrize(
    "champ",
    ["deduction_federale_t1m", "deduction_quebec_tp348"],
)
def test_montants_non_finis_refuses(champ, valeur):
    profil = replace(FraisDemenagement2025(), **{champ: valeur})
    with pytest.raises(ValueError):
        valider_frais_demenagement_2025(profil)


def test_montants_sont_arrondis_au_cent():
    valide = valider_frais_demenagement_2025(
        _profil("2200.005", "1799.994")
    )
    assert valide.deduction_federale_t1m == Decimal("2200.01")
    assert valide.deduction_quebec_tp348 == Decimal("1799.99")


@pytest.mark.parametrize(
    "champ",
    [
        "travailleur_autonome",
        "etudiant_temps_plein",
        "demenagement_international",
        "report_annees_anterieures",
        "plusieurs_demenagements_admissibles",
    ],
)
def test_cas_avances_refuses(champ):
    with pytest.raises(ValueError, match="hors périmètre 4D"):
        valider_frais_demenagement_2025(
            replace(_profil(), **{champ: True})
        )


@pytest.mark.parametrize(
    "champ",
    [
        "valide_par_comptable",
        "salarie_ordinaire_confirme",
        "demenagement_pour_emploi_confirme",
        "rapprochement_40km_confirme",
        "demenagement_interieur_canada_confirme",
        "remboursements_employeur_pris_en_compte_confirme",
    ],
)
def test_confirmations_generales_obligatoires(champ):
    with pytest.raises(ValueError):
        valider_frais_demenagement_2025(
            replace(_profil(), **{champ: False})
        )


def test_t1m_obligatoire_si_deduction_federale():
    with pytest.raises(ValueError):
        valider_frais_demenagement_2025(
            replace(_profil(), t1m_confirme=False)
        )


def test_tp348_obligatoire_si_deduction_quebec():
    with pytest.raises(ValueError):
        valider_frais_demenagement_2025(
            replace(_profil(), tp348_confirme=False)
        )


def test_source_federale_obligatoire():
    with pytest.raises(ValueError):
        valider_frais_demenagement_2025(
            replace(_profil(), source_federale=" ")
        )


def test_source_quebec_obligatoire():
    with pytest.raises(ValueError):
        valider_frais_demenagement_2025(
            replace(_profil(), source_quebec=" ")
        )


def test_federal_seul_n_exige_pas_tp348():
    profil = replace(
        _profil(quebec="0"),
        source_quebec="",
        tp348_confirme=False,
    )
    valide = valider_frais_demenagement_2025(profil)
    assert valide.deduction_federale_t1m == Decimal("2200.00")


def test_quebec_seul_n_exige_pas_t1m():
    profil = replace(
        _profil(federal="0"),
        source_federale="",
        t1m_confirme=False,
    )
    valide = valider_frais_demenagement_2025(profil)
    assert valide.deduction_quebec_tp348 == Decimal("1800.00")


def test_application_reduit_separement_federal_et_quebec():
    revenu = appliquer_frais_demenagement_2025(_revenu(), _profil())
    assert revenu.revenu_total_federal == Decimal("52000")
    assert revenu.revenu_total_quebec == Decimal("52000")
    assert revenu.revenu_net_federal == Decimal("48315.00")
    assert revenu.revenu_imposable_federal == Decimal("48315.00")
    assert revenu.revenu_net_quebec == Decimal("47780.00")
    assert revenu.revenu_imposable_quebec == Decimal("47780.00")


def test_application_ne_modifie_pas_cotisation_rrq():
    avant = _revenu()
    apres = appliquer_frais_demenagement_2025(avant, _profil())
    assert (
        apres.deduction_rrq_amelioree_federale
        == avant.deduction_rrq_amelioree_federale
    )
    assert apres.deduction_rrq_quebec == avant.deduction_rrq_quebec


def test_application_plafonne_revenus_a_zero():
    revenu = appliquer_frais_demenagement_2025(
        _revenu(),
        _profil("999999", "999999"),
    )
    assert revenu.revenu_net_federal == ZERO
    assert revenu.revenu_imposable_federal == ZERO
    assert revenu.revenu_net_quebec == ZERO
    assert revenu.revenu_imposable_quebec == ZERO


def test_application_refuse_autre_annee():
    revenu = replace(_revenu(), annee_fiscale=2024)
    with pytest.raises(ValueError, match="uniquement l'année 2025"):
        appliquer_frais_demenagement_2025(revenu, _profil())


def test_application_retire_limitation_generique():
    revenu = appliquer_frais_demenagement_2025(_revenu(), _profil())
    assert (
        "Aucune autre déduction de revenu net ou imposable."
        not in revenu.limitations
    )


def test_resume_contient_lignes_et_sources():
    texte = "\n".join(lignes_resume_frais_demenagement_2025(_profil()))
    assert "BLOC 4D" in texte
    assert "T1-M" in texte
    assert "21900" in texte
    assert "TP-348" in texte
    assert "ligne 228" in texte
    assert "T1-M 2025 validé" in texte
    assert "TP-348 2025 validé" in texte


def test_resume_federal_seul():
    profil = replace(
        _profil(quebec="0"),
        source_quebec="",
        tp348_confirme=False,
    )
    texte = "\n".join(lignes_resume_frais_demenagement_2025(profil))
    assert "21900" in texte
    assert "ligne 228" not in texte


def test_resume_quebec_seul():
    profil = replace(
        _profil(federal="0"),
        source_federale="",
        t1m_confirme=False,
    )
    texte = "\n".join(lignes_resume_frais_demenagement_2025(profil))
    assert "ligne 228" in texte
    assert "21900" not in texte


def test_resume_vide_si_aucune_deduction():
    assert lignes_resume_frais_demenagement_2025(
        FraisDemenagement2025()
    ) == []
