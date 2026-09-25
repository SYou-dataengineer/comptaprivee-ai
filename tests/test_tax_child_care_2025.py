from decimal import Decimal

import pytest

from src.comptaprivee.tax_child_care_2025 import (
    FraisGardeFederaux2025,
    appliquer_frais_garde_federaux_2025,
    deduction_frais_garde_federale_2025,
    lignes_resume_frais_garde_federaux_2025,
    limite_deux_tiers_revenu_gagne_2025,
    plafond_enfants_frais_garde_2025,
    valider_frais_garde_federaux_2025,
)
from src.comptaprivee.tax_income_2025 import RevenuNetImposable2025


def D(v):
    return Decimal(v)


def profil_valide(
    frais="9000",
    revenu_gagne="45000",
    moins_7=1,
    sept_16=1,
    dtc=0,
):
    return FraisGardeFederaux2025(
        frais_admissibles_payes=D(frais),
        revenu_gagne_t778=D(revenu_gagne),
        nombre_enfants_moins_7_sans_dtc=moins_7,
        nombre_enfants_7_a_16_ou_infirmes_sans_dtc=sept_16,
        nombre_enfants_dtc=dtc,
        source="T778 2025 + reçus de garde",
        valide_par_comptable=True,
        services_fournis_en_2025_confirmes=True,
        frais_pour_gagner_revenu_confirmes=True,
        recus_confirmes=True,
        demandeur_seul_ou_revenu_inferieur_confirme=True,
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


def test_4b_zero_est_accepte():
    p = FraisGardeFederaux2025()
    assert valider_frais_garde_federaux_2025(p) == p
    assert deduction_frais_garde_federale_2025(p) == D("0")


@pytest.mark.parametrize(
    "champ",
    ["frais_admissibles_payes", "revenu_gagne_t778"],
)
def test_4b_refuse_montants_negatifs(champ):
    valeurs = profil_valide().__dict__.copy()
    valeurs[champ] = D("-1")
    with pytest.raises(ValueError):
        valider_frais_garde_federaux_2025(
            FraisGardeFederaux2025(**valeurs)
        )


@pytest.mark.parametrize(
    "champ",
    [
        "nombre_enfants_moins_7_sans_dtc",
        "nombre_enfants_7_a_16_ou_infirmes_sans_dtc",
        "nombre_enfants_dtc",
    ],
)
def test_4b_refuse_nombre_enfants_negatif(champ):
    valeurs = profil_valide().__dict__.copy()
    valeurs[champ] = -1
    with pytest.raises(ValueError):
        valider_frais_garde_federaux_2025(
            FraisGardeFederaux2025(**valeurs)
        )


def test_4b_plafonds_enfants_8000_5000_11000():
    p = profil_valide(frais="50000", moins_7=1, sept_16=1, dtc=1)
    assert plafond_enfants_frais_garde_2025(p) == D("24000.00")


def test_4b_limite_deux_tiers_revenu_gagne():
    p = profil_valide(revenu_gagne="30000")
    assert limite_deux_tiers_revenu_gagne_2025(p) == D("20000.00")


def test_4b_deduction_limitee_par_frais_payes():
    p = profil_valide(frais="7000", revenu_gagne="60000")
    assert deduction_frais_garde_federale_2025(p) == D("7000.00")


def test_4b_deduction_limitee_par_plafond_enfants():
    p = profil_valide(
        frais="20000",
        revenu_gagne="60000",
        moins_7=1,
        sept_16=0,
    )
    assert deduction_frais_garde_federale_2025(p) == D("8000.00")


def test_4b_deduction_limitee_par_deux_tiers_revenu():
    p = profil_valide(
        frais="15000",
        revenu_gagne="9000",
        moins_7=2,
        sept_16=0,
    )
    assert deduction_frais_garde_federale_2025(p) == D("6000.00")


@pytest.mark.parametrize(
    "champ",
    [
        "valide_par_comptable",
        "services_fournis_en_2025_confirmes",
        "frais_pour_gagner_revenu_confirmes",
        "recus_confirmes",
        "demandeur_seul_ou_revenu_inferieur_confirme",
    ],
)
def test_4b_exige_confirmations(champ):
    valeurs = profil_valide().__dict__.copy()
    valeurs[champ] = False
    with pytest.raises(ValueError):
        valider_frais_garde_federaux_2025(
            FraisGardeFederaux2025(**valeurs)
        )


def test_4b_exige_source():
    valeurs = profil_valide().__dict__.copy()
    valeurs["source"] = "  "
    with pytest.raises(ValueError, match="source"):
        valider_frais_garde_federaux_2025(
            FraisGardeFederaux2025(**valeurs)
        )


def test_4b_exige_au_moins_un_enfant():
    p = profil_valide(moins_7=0, sept_16=0, dtc=0)
    with pytest.raises(ValueError, match="enfant admissible"):
        valider_frais_garde_federaux_2025(p)


@pytest.mark.parametrize(
    "champ",
    [
        "partie_c_requise",
        "partie_d_requise",
        "camp_avec_hebergement",
        "garde_partagee",
        "repartition_entre_contribuables",
        "demandeur_revenu_superieur",
    ],
)
def test_4b_refuse_cas_avances(champ):
    valeurs = profil_valide().__dict__.copy()
    valeurs[champ] = True
    with pytest.raises(ValueError, match="hors périmètre 4B"):
        valider_frais_garde_federaux_2025(
            FraisGardeFederaux2025(**valeurs)
        )


def test_4b_applique_uniquement_au_federal():
    r = appliquer_frais_garde_federaux_2025(
        revenu(),
        profil_valide(frais="7000", revenu_gagne="60000"),
    )
    assert r.revenu_total_federal == D("52000")
    assert r.revenu_net_federal == D("44515.00")
    assert r.revenu_imposable_federal == D("44515.00")

    assert r.revenu_total_quebec == D("52000")
    assert r.revenu_net_quebec == D("50095")
    assert r.revenu_imposable_quebec == D("50095")


def test_4b_ne_descend_jamais_sous_zero():
    base = revenu()
    base = base.__class__(
        **{
            **base.__dict__,
            "revenu_net_federal": D("3000"),
            "revenu_imposable_federal": D("3000"),
        }
    )
    r = appliquer_frais_garde_federaux_2025(
        base,
        profil_valide(frais="8000", revenu_gagne="60000"),
    )
    assert r.revenu_net_federal == D("0")
    assert r.revenu_imposable_federal == D("0")


def test_4b_resume_affiche_t778_21400_limites_et_source():
    lignes = lignes_resume_frais_garde_federaux_2025(
        profil_valide(frais="9000", revenu_gagne="45000")
    )
    texte = "\n".join(lignes)
    assert "BLOC 4B" in texte
    assert "T778" in texte
    assert "21400" in texte
    assert "9000.00 $" in texte
    assert "13000.00 $" in texte
    assert "30000.00 $" in texte
    assert "T778 2025 + reçus de garde" in texte
