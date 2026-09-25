from decimal import Decimal

import pytest

from src.comptaprivee.tax_fhsa_2025 import (
    DeductionCeliapp2025,
    appliquer_deduction_celiapp_2025,
    lignes_resume_celiapp_2025,
    valider_deduction_celiapp_2025,
)
from src.comptaprivee.tax_income_2025 import RevenuNetImposable2025


def D(v):
    return Decimal(v)


def profil_valide(deduction="5000", cotisations="6000", droits="8000"):
    return DeductionCeliapp2025(
        deduction=D(deduction),
        cotisations_directes_2025=D(cotisations),
        droits_deduction_confirmes=D(droits),
        source_droits="Annexe 15 / relevé CELIAPP 2025",
        valide_par_comptable=True,
        titulaire_confirme=True,
        residence_canada_quebec_annee_complete=True,
    )


def revenu():
    return RevenuNetImposable2025(
        client="Test",
        annee_fiscale=2025,
        province="Québec",
        revenu_total_federal=D("52000"),
        deduction_rrq_amelioree_federale=D("485"),
        revenu_net_federal=D("51515"),
        revenu_imposable_federal=D("51515"),
        revenu_total_quebec=D("52000"),
        deduction_travailleur_quebec=D("1420"),
        deduction_rrq_quebec=D("485"),
        revenu_net_quebec=D("50095"),
        revenu_imposable_quebec=D("50095"),
        profil="Emploi simple",
        limitations=("Aucune autre déduction de revenu net ou imposable.",),
    )


def test_4a_zero_est_accepte():
    p = DeductionCeliapp2025()
    assert valider_deduction_celiapp_2025(p) == p


@pytest.mark.parametrize(
    "champ",
    ["deduction", "cotisations_directes_2025", "droits_deduction_confirmes"],
)
def test_4a_refuse_montants_negatifs(champ):
    valeurs = dict(
        deduction=D("1000"),
        cotisations_directes_2025=D("1000"),
        droits_deduction_confirmes=D("1000"),
        source_droits="Annexe 15",
        valide_par_comptable=True,
        titulaire_confirme=True,
        residence_canada_quebec_annee_complete=True,
    )
    valeurs[champ] = D("-1")
    with pytest.raises(ValueError):
        valider_deduction_celiapp_2025(DeductionCeliapp2025(**valeurs))


def test_4a_refuse_deduction_superieure_cotisations_directes():
    with pytest.raises(ValueError, match="cotisations directes"):
        valider_deduction_celiapp_2025(
            profil_valide(deduction="7000", cotisations="6000", droits="8000")
        )


def test_4a_refuse_deduction_superieure_droits_confirmes():
    with pytest.raises(ValueError, match="droits de déduction"):
        valider_deduction_celiapp_2025(
            profil_valide(deduction="7000", cotisations="8000", droits="6000")
        )


@pytest.mark.parametrize(
    "champ",
    [
        "inclut_cotisations_inutilisees_anterieures",
        "inclut_transfert_reer",
        "retrait_2025",
        "excedent_2025",
    ],
)
def test_4a_refuse_cas_avances(champ):
    p = profil_valide()
    valeurs = p.__dict__.copy()
    valeurs[champ] = True
    with pytest.raises(ValueError, match="hors périmètre 4A"):
        valider_deduction_celiapp_2025(DeductionCeliapp2025(**valeurs))


def test_4a_exige_source_et_confirmations():
    base = profil_valide()
    for changements in (
        {"source_droits": ""},
        {"valide_par_comptable": False},
        {"titulaire_confirme": False},
        {"residence_canada_quebec_annee_complete": False},
    ):
        valeurs = base.__dict__.copy()
        valeurs.update(changements)
        with pytest.raises(ValueError):
            valider_deduction_celiapp_2025(DeductionCeliapp2025(**valeurs))


def test_4a_applique_5000_aux_revenus_net_et_imposable():
    r = appliquer_deduction_celiapp_2025(revenu(), profil_valide())
    assert r.revenu_total_federal == D("52000")
    assert r.revenu_total_quebec == D("52000")
    assert r.revenu_net_federal == D("46515")
    assert r.revenu_imposable_federal == D("46515")
    assert r.revenu_net_quebec == D("45095")
    assert r.revenu_imposable_quebec == D("45095")


def test_4a_ne_descend_jamais_sous_zero():
    r = appliquer_deduction_celiapp_2025(
        revenu(),
        profil_valide(deduction="60000", cotisations="60000", droits="60000"),
    )
    assert r.revenu_net_federal == D("0")
    assert r.revenu_imposable_federal == D("0")
    assert r.revenu_net_quebec == D("0")
    assert r.revenu_imposable_quebec == D("0")


def test_4a_resume_affiche_20805_215_et_source():
    lignes = lignes_resume_celiapp_2025(profil_valide())
    texte = "\n".join(lignes)
    assert "BLOC 4A" in texte
    assert "20805" in texte
    assert "215" in texte
    assert "5000.00 $" in texte
    assert "Annexe 15 / relevé CELIAPP 2025" in texte
