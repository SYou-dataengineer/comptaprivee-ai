"""Bloc 3H-A : fondation intérêts + dividendes et FSS globale."""
from dataclasses import replace
from decimal import Decimal as D
from pathlib import Path

import pytest

from src.comptaprivee.tax_dividend_income_2025 import ProfilDividendes2025
from src.comptaprivee.tax_interest_income_2025 import ProfilInterets2025
from src.comptaprivee.tax_investment_combinations_2025 import (
    consolider_interets_dividendes_2025,
    detecter_interets_dividendes_2025,
)
from src.comptaprivee.tax_rules_2025 import arrondir_cent
from tests.test_tax_estimation_2025 import _dossier_52000, _validee
from tests.test_tax_pension_income_2025 import modifier


def profil_interets():
    return ProfilInterets2025(
        source="T5/RL-3 combiné 2025 vérifié",
        confirme=True,
    )


def profil_dividendes():
    return ProfilDividendes2025(
        source="T5/RL-3 combiné 2025 vérifié",
        confirme=True,
    )


def dossier_combine(interets="10000", admissibles="5000", ordinaires="5000", emploi=False):
    d = _dossier_52000()
    if not emploi:
        d = replace(d, documents=(), donnees_validees=())

    i = D(interets)
    a = D(admissibles)
    o = D(ordinaires)
    ta = arrondir_cent(a * D("1.38"))
    to = arrondir_cent(o * D("1.15"))

    valeurs = {
        "T5": {
            "13": i,
            "24": a,
            "25": ta,
            "26": arrondir_cent(ta * D(".150198")),
            "10": o,
            "11": to,
            "12": arrondir_cent(to * D(".090301")),
        },
        "RL-3": {
            "D": i,
            "A1": a,
            "A2": o,
            "B": ta + to,
            "C": arrondir_cent(a * D(".161460") + o * D(".039330")),
        },
    }

    return replace(
        d,
        documents=d.documents + (Path("T5-combine.pdf"), Path("RL-3-combine.pdf")),
        donnees_validees=d.donnees_validees
        + tuple(
            _validee(Path(t + "-combine.pdf"), t, c, str(v))
            for t, cases in valeurs.items()
            for c, v in cases.items()
        ),
    )


def test_combinaison_consolide_deux_revenus():
    r = consolider_interets_dividendes_2025(
        dossier_combine(),
        profil_interets(),
        profil_dividendes(),
    )
    assert r.present
    assert r.interets.ligne_12100 == D("10000")
    assert r.interets.ligne_130 == D("10000")
    assert r.dividendes.ligne_166 == D("5000")
    assert r.dividendes.ligne_167 == D("5000")
    assert r.dividendes.ligne_12000 == D("12650")


def test_fss_est_globale_et_non_somme_de_deux_fss():
    r = consolider_interets_dividendes_2025(
        dossier_combine(),
        profil_interets(),
        profil_dividendes(),
    )
    assert r.assiette_fss == D("20000")
    assert r.cotisation_fss == D("18.70")
    assert r.interets.cotisation_fss == D("18.70")
    assert r.dividendes.cotisation_fss == D("0")
    assert (
        r.interets.cotisation_fss + r.dividendes.cotisation_fss
        == r.cotisation_fss
    )


@pytest.mark.parametrize(
    "interets,admissibles,ordinaires,assiette,fss",
    [
        ("8130", "5000", "5000", "18130", "0"),
        ("8131", "5000", "5000", "18131", ".01"),
        ("53130", "5000", "5000", "63130", "150.70"),
    ],
)
def test_seuils_fss_combines(interets, admissibles, ordinaires, assiette, fss):
    r = consolider_interets_dividendes_2025(
        dossier_combine(interets, admissibles, ordinaires),
        profil_interets(),
        profil_dividendes(),
    )
    assert r.assiette_fss == D(assiette)
    assert r.cotisation_fss == D(fss)


def test_avec_emploi_ne_change_pas_assiette_fss_placement():
    sans = consolider_interets_dividendes_2025(
        dossier_combine(emploi=False),
        profil_interets(),
        profil_dividendes(),
    )
    avec = consolider_interets_dividendes_2025(
        dossier_combine(emploi=True),
        profil_interets(),
        profil_dividendes(),
    )
    assert sans.assiette_fss == avec.assiette_fss == D("20000")
    assert sans.cotisation_fss == avec.cotisation_fss == D("18.70")


def test_refuse_autre_case_t5_positive():
    d = modifier(dossier_combine(), "T5", "15", "1")
    with pytest.raises(ValueError, match="non couverte"):
        consolider_interets_dividendes_2025(
            d,
            profil_interets(),
            profil_dividendes(),
        )


def test_refuse_interets_documentes_sans_t5():
    p = replace(
        profil_interets(),
        nature="BANQUE",
        identifiant_source="BANQUE-1",
    )
    with pytest.raises(ValueError, match="T5/RL-3"):
        consolider_interets_dividendes_2025(
            dossier_combine(),
            p,
            profil_dividendes(),
        )


def test_refuse_confirmation_manquante():
    with pytest.raises(ValueError, match="confirmez"):
        consolider_interets_dividendes_2025(
            dossier_combine(),
            replace(profil_interets(), confirme=False),
            profil_dividendes(),
        )


def test_refuse_dividendes_nuls():
    with pytest.raises(ValueError, match="dividendes réels positifs"):
        consolider_interets_dividendes_2025(
            dossier_combine(admissibles="0", ordinaires="0"),
            profil_interets(),
            profil_dividendes(),
        )

def test_estimation_3h_a_applique_interets_et_dividendes():
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025

    e = calculer_estimation_fiscale_2025(
        dossier_combine(),
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
    )

    assert e.interets.present
    assert e.dividendes.present
    assert e.revenu.revenu_total_federal == D("22650")
    assert e.revenu.revenu_total_quebec == D("22650")
    assert e.revenu.revenu_net_federal == D("22650")
    assert e.revenu.revenu_net_quebec == D("22650")


def test_estimation_3h_a_fss_unique_globale():
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025

    e = calculer_estimation_fiscale_2025(
        dossier_combine(),
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
    )

    assert e.interets.cotisation_fss == D("18.70")
    assert e.dividendes.cotisation_fss == D("0")
    assert e.rapprochement.impot_total_preliminaire >= D("18.70")


def test_estimation_3h_a_applique_credits_dividendes():
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025

    e = calculer_estimation_fiscale_2025(
        dossier_combine(),
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
    )

    assert e.dividendes.ligne_40425 > 0
    assert e.dividendes.ligne_415 > 0


def test_estimation_3h_a_avec_emploi():
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025

    e = calculer_estimation_fiscale_2025(
        dossier_combine(emploi=True),
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
    )

    assert e.revenu.revenu_total_federal == D("74650")
    assert e.revenu.revenu_total_quebec == D("74650")
    assert e.interets.cotisation_fss == D("18.70")
    assert e.dividendes.cotisation_fss == D("0")


def test_estimation_3h_a_refuse_autre_parcours():
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
    from src.comptaprivee.tax_foreign_investment_2025 import (
        ProfilPlacementEtranger2025,
        ProfilCreditImpotEtranger2025,
    )

    with pytest.raises(ValueError, match="3H-A"):
        calculer_estimation_fiscale_2025(
            dossier_combine(),
            profil_interets=profil_interets(),
            profil_dividendes=profil_dividendes(),
            profil_placement_etranger=ProfilPlacementEtranger2025(
                source="étranger",
                confirme=True,
                pays="États-Unis",
                devise="CAD",
                obligations_biens_etrangers_verifiees=True,
            ),
            profil_credit_impot_etranger=ProfilCreditImpotEtranger2025(
                credit_federal_40500=D("0"),
                credit_quebec_409=D("0"),
                source_t2209="T2209 vérifié",
                source_tp772="TP-772 vérifié",
                confirme=True,
            ),
        )

def test_detection_3h_a_exige_les_deux_profils_confirmes():
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025

    # Une case dividendes ajoutée à un dossier intérêts ne doit pas détourner
    # automatiquement le parcours 3A historique vers 3H-A.
    d = modifier(dossier_combine(interets="10000", admissibles="0", ordinaires="0"), "T5", "10", "1")
    with pytest.raises(ValueError, match="hors périmètre"):
        calculer_estimation_fiscale_2025(
            d,
            profil_interets=profil_interets(),
        )

    # Symétriquement, une case intérêts isolée dans un dossier dividendes
    # doit rester dans le garde-fou historique 3C, sans être détournée vers 3H-A.
    d2 = modifier(dossier_combine(interets="0", admissibles="5000", ordinaires="5000"), "T5", "13", "1")
    with pytest.raises(ValueError) as erreur:
        calculer_estimation_fiscale_2025(
            d2,
            profil_dividendes=profil_dividendes(),
        )
    assert "3H-A" not in str(erreur.value)

def test_resume_trace_pdf_3h_a(tmp_path):
    import fitz
    from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025, formater_estimation_fiscale_2025
    from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025

    e = calculer_estimation_fiscale_2025(
        dossier_combine(),
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
    )

    resume = formater_estimation_fiscale_2025(e)
    assert "COMBINAISON CONTRÔLÉE 2025 — BLOC 3H-A" in resume
    assert "Assiette FSS globale 446" in resume
    assert "20000.00 $" in resume
    assert "18.70 $" in resume

    trace = construire_trace_calcul_fiscal_2025(e)
    ligne = next(x for x in trace.lignes if x.libelle == "FSS combinée 3H-A ligne 446")
    assert ligne.montant == D("18.70")
    assert "130 + 166 + 167" in ligne.formule

    pdf = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "rapport_3h_a.pdf")
    with fitz.open(pdf) as doc:
        texte = "\n".join(page.get_text() for page in doc)
    assert "COMBINAISON CONTRÔLÉE 2025" in texte
    assert "BLOC 3H-A" in texte
    assert "FSS globale 446" in texte

@pytest.mark.parametrize("valeur", ["NaN", "sNaN", "Infinity", "-Infinity"])
def test_detection_3h_a_ignore_montant_non_fini_hors_parcours(valeur):
    d = modifier(dossier_combine(), "T4A(P)", "20", valeur)
    assert detecter_interets_dividendes_2025(d)


def test_detection_3h_a_montant_non_fini_relevant_ne_leve_pas():
    d = modifier(dossier_combine(), "T5", "13", "sNaN")
    # RL-3 D reste valide et non nul dans dossier_combine(), donc le
    # parcours intérêts est encore détectable. Le contrat important ici
    # est surtout de ne plus lever decimal.InvalidOperation.
    assert detecter_interets_dividendes_2025(d) is True


def test_detection_3h_a_deux_cases_interets_non_finies_ne_detecte_pas():
    d = modifier(dossier_combine(), "T5", "13", "sNaN")
    d = modifier(d, "RL-3", "D", "sNaN")
    assert detecter_interets_dividendes_2025(d) is False
