from dataclasses import replace
from decimal import Decimal

import pytest

from src.comptaprivee.tax_employment_expenses_2025 import (
    DepensesEmploi2025,
    appliquer_depenses_emploi_2025,
    lignes_resume_depenses_emploi_2025,
    valider_depenses_emploi_2025,
)
from src.comptaprivee.tax_income_2025 import RevenuNetImposable2025


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


def _profil(federal: str = "1200", quebec: str = "1000") -> DepensesEmploi2025:
    return DepensesEmploi2025(
        deduction_federale_t777=Decimal(federal),
        deduction_quebec_tp59=Decimal(quebec),
        source_federale="T2200 + T777 2025",
        source_quebec="TP-64.3 + TP-59 2025",
        valide_par_comptable=True,
        salarie_ordinaire_confirme=True,
        contrat_exige_depenses_confirme=True,
        non_remboursees_confirme=True,
        t2200_confirme=True,
        t777_confirme=True,
        tp_64_3_confirme=True,
        tp_59_confirme=True,
    )


def test_profil_vide_est_accepte():
    assert valider_depenses_emploi_2025(DepensesEmploi2025()) == DepensesEmploi2025()


@pytest.mark.parametrize("champ", ["deduction_federale_t777", "deduction_quebec_tp59"])
def test_montants_negatifs_refuses(champ):
    profil = replace(DepensesEmploi2025(), **{champ: Decimal("-1")})
    with pytest.raises(ValueError):
        valider_depenses_emploi_2025(profil)


@pytest.mark.parametrize("valeur", [Decimal("NaN"), Decimal("Infinity")])
@pytest.mark.parametrize("champ", ["deduction_federale_t777", "deduction_quebec_tp59"])
def test_montants_non_finis_refuses(champ, valeur):
    profil = replace(DepensesEmploi2025(), **{champ: valeur})
    with pytest.raises(ValueError):
        valider_depenses_emploi_2025(profil)


def test_montants_sont_arrondis_au_cent():
    valide = valider_depenses_emploi_2025(_profil("1200.005", "999.994"))
    assert valide.deduction_federale_t777 == Decimal("1200.01")
    assert valide.deduction_quebec_tp59 == Decimal("999.99")


@pytest.mark.parametrize(
    "champ",
    [
        "employe_a_commission",
        "vehicule_ou_cca",
        "voyage_repas_logement",
        "bureau_a_domicile",
        "outils_ou_profil_specialise",
    ],
)
def test_cas_avances_refuses(champ):
    with pytest.raises(ValueError, match="hors périmètre 4C"):
        valider_depenses_emploi_2025(replace(_profil(), **{champ: True}))


@pytest.mark.parametrize(
    "champ",
    [
        "valide_par_comptable",
        "salarie_ordinaire_confirme",
        "contrat_exige_depenses_confirme",
        "non_remboursees_confirme",
    ],
)
def test_confirmations_generales_obligatoires(champ):
    with pytest.raises(ValueError):
        valider_depenses_emploi_2025(replace(_profil(), **{champ: False}))


@pytest.mark.parametrize("champ", ["t2200_confirme", "t777_confirme"])
def test_documents_federaux_obligatoires_si_deduction_federale(champ):
    with pytest.raises(ValueError):
        valider_depenses_emploi_2025(replace(_profil(), **{champ: False}))


@pytest.mark.parametrize("champ", ["tp_64_3_confirme", "tp_59_confirme"])
def test_documents_quebec_obligatoires_si_deduction_quebec(champ):
    with pytest.raises(ValueError):
        valider_depenses_emploi_2025(replace(_profil(), **{champ: False}))


def test_source_federale_obligatoire():
    with pytest.raises(ValueError):
        valider_depenses_emploi_2025(replace(_profil(), source_federale=" "))


def test_source_quebec_obligatoire():
    with pytest.raises(ValueError):
        valider_depenses_emploi_2025(replace(_profil(), source_quebec=" "))


def test_federal_seul_n_exige_pas_documents_quebec():
    profil = replace(
        _profil(quebec="0"),
        source_quebec="",
        tp_64_3_confirme=False,
        tp_59_confirme=False,
    )
    assert valider_depenses_emploi_2025(profil).deduction_federale_t777 == Decimal("1200.00")


def test_quebec_seul_n_exige_pas_documents_federaux():
    profil = replace(
        _profil(federal="0"),
        source_federale="",
        t2200_confirme=False,
        t777_confirme=False,
    )
    assert valider_depenses_emploi_2025(profil).deduction_quebec_tp59 == Decimal("1000.00")


def test_application_reduit_separement_federal_et_quebec():
    revenu = appliquer_depenses_emploi_2025(_revenu(), _profil())
    assert revenu.revenu_total_federal == Decimal("52000")
    assert revenu.revenu_total_quebec == Decimal("52000")
    assert revenu.revenu_net_federal == Decimal("49315.00")
    assert revenu.revenu_imposable_federal == Decimal("49315.00")
    assert revenu.revenu_net_quebec == Decimal("48580.00")
    assert revenu.revenu_imposable_quebec == Decimal("48580.00")


def test_application_ne_modifie_pas_cotisation_rrq():
    avant = _revenu()
    apres = appliquer_depenses_emploi_2025(avant, _profil())
    assert apres.deduction_rrq_amelioree_federale == avant.deduction_rrq_amelioree_federale
    assert apres.deduction_rrq_quebec == avant.deduction_rrq_quebec


def test_application_plafonne_revenus_a_zero():
    revenu = appliquer_depenses_emploi_2025(_revenu(), _profil("999999", "999999"))
    assert revenu.revenu_net_federal == ZERO
    assert revenu.revenu_imposable_federal == ZERO
    assert revenu.revenu_net_quebec == ZERO
    assert revenu.revenu_imposable_quebec == ZERO


def test_application_refuse_autre_annee():
    revenu = replace(_revenu(), annee_fiscale=2024)
    with pytest.raises(ValueError, match="uniquement l'année 2025"):
        appliquer_depenses_emploi_2025(revenu, _profil())


def test_resume_contient_lignes_et_sources():
    texte = "\n".join(lignes_resume_depenses_emploi_2025(_profil()))
    assert "BLOC 4C" in texte
    assert "T777" in texte
    assert "22900" in texte
    assert "TP-59" in texte
    assert "ligne 207, code 07" in texte
    assert "T2200 + T777 2025" in texte
    assert "TP-64.3 + TP-59 2025" in texte


def test_resume_vide_si_aucune_deduction():
    assert lignes_resume_depenses_emploi_2025(DepensesEmploi2025()) == []
