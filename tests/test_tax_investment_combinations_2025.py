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


# --- Bloc 3H-B : intérêts + dividendes + frais de placement ---

def profil_frais_3h_b(
    dossier,
    gestion="500",
    interets="1000",
    solde_quebec="0",
    demande_252="0",
    source_report="",
):
    from src.comptaprivee.tax_capital_gains_2025 import ProfilCapital2025
    from src.comptaprivee.tax_investment_expenses_2025 import (
        ProfilFraisPlacement2025,
        empreinte_frais_placement_2025,
    )

    p = ProfilFraisPlacement2025(
        gestion=gestion,
        interets=interets,
        source="Facture synthétique 3H-B F-2025-1, compte unique",
        paiement="Paiements 2025 vérifiés, frais ventilés",
        utilisation="Placements T5/RL-3 combinés productifs d'intérêts et dividendes",
        solde_quebec=solde_quebec,
        demande_252=demande_252,
        source_report=source_report,
        confirme=True,
        report_confirme=True,
    )
    return replace(
        p,
        empreinte=empreinte_frais_placement_2025(
            p,
            dossier,
            profil_interets(),
            profil_dividendes(),
            ProfilCapital2025(),
        ),
    )


def test_3h_b_applique_frais_aux_deux_revenus():
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025

    d = dossier_combine()
    e = calculer_estimation_fiscale_2025(
        d,
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
        profil_frais_placement=profil_frais_3h_b(d),
    )

    assert e.interets.present
    assert e.dividendes.present
    assert e.frais_placement.present
    assert e.frais_placement.ligne_22100 == D("1500")
    assert e.frais_placement.ligne_231 == D("1500")
    assert e.frais_placement.revenus_n36 == D("22650")
    assert e.revenu.revenu_total_federal == D("22650")
    assert e.revenu.revenu_total_quebec == D("22650")
    assert e.revenu.revenu_net_federal == D("21150")
    assert e.revenu.revenu_net_quebec == D("21150")


def test_3h_b_fss_globale_apres_frais_comptee_une_fois():
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025

    d = dossier_combine()
    e = calculer_estimation_fiscale_2025(
        d,
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
        profil_frais_placement=profil_frais_3h_b(d),
    )

    assert e.frais_placement.assiette_fss == D("18500")
    assert e.frais_placement.cotisation_fss == D("3.70")
    assert e.interets.cotisation_fss == D("3.70")
    assert e.dividendes.cotisation_fss == D("0")
    assert (
        e.interets.cotisation_fss + e.dividendes.cotisation_fss
        == e.frais_placement.cotisation_fss
    )


def test_3h_b_frais_peuvent_ramener_assiette_fss_au_seuil():
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025

    d = dossier_combine()
    e = calculer_estimation_fiscale_2025(
        d,
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
        profil_frais_placement=profil_frais_3h_b(
            d,
            gestion="1870",
            interets="0",
        ),
    )

    assert e.frais_placement.assiette_fss == D("18130")
    assert e.frais_placement.cotisation_fss == D("0")
    assert e.interets.cotisation_fss == D("0")
    assert e.dividendes.cotisation_fss == D("0")


def test_3h_b_refuse_toujours_capital_en_plus():
    from src.comptaprivee.tax_capital_gains_2025 import ProfilCapital2025
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025

    d = dossier_combine()
    with pytest.raises(ValueError, match="3H-A|3H-B|hors périmètre"):
        calculer_estimation_fiscale_2025(
            d,
            profil_interets=profil_interets(),
            profil_dividendes=profil_dividendes(),
            profil_frais_placement=profil_frais_3h_b(d),
            profil_capital=replace(ProfilCapital2025(), confirme=True),
        )


def test_3h_b_sauvegarde_et_rechargement_des_trois_profils(tmp_path):
    from src.comptaprivee.tax_case_storage import (
        charger_dossier_fiscal,
        sauvegarder_dossier_fiscal,
    )

    d = dossier_combine()
    frais = profil_frais_3h_b(d)
    chemin = sauvegarder_dossier_fiscal(
        d,
        destination=tmp_path / "3h_b.json",
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
        profil_frais_placement=frais,
    )

    charge = charger_dossier_fiscal(chemin)
    assert charge.profil_interets == profil_interets()
    assert charge.profil_dividendes == profil_dividendes()
    assert charge.profil_frais_placement == frais


def test_3h_b_rechargement_recalcule_meme_resultat(tmp_path):
    from src.comptaprivee.tax_case_storage import (
        charger_dossier_fiscal,
        sauvegarder_dossier_fiscal,
    )
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025

    d = dossier_combine()
    frais = profil_frais_3h_b(d)
    attendu = calculer_estimation_fiscale_2025(
        d,
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
        profil_frais_placement=frais,
    )

    chemin = sauvegarder_dossier_fiscal(
        d,
        destination=tmp_path / "3h_b_recalcul.json",
        estimation=attendu,
    )
    charge = charger_dossier_fiscal(chemin)
    obtenu = calculer_estimation_fiscale_2025(
        charge.dossier,
        profil_interets=charge.profil_interets,
        profil_dividendes=charge.profil_dividendes,
        profil_frais_placement=charge.profil_frais_placement,
    )

    assert obtenu.revenu == attendu.revenu
    assert obtenu.frais_placement == attendu.frais_placement
    assert obtenu.interets.cotisation_fss == D("3.70")
    assert obtenu.dividendes.cotisation_fss == D("0")
def test_3h_b_resume_trace_pdf_utilisent_assiette_apres_frais(tmp_path):
    import fitz

    from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025, formater_estimation_fiscale_2025
    from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025

    d = dossier_combine()
    e = calculer_estimation_fiscale_2025(
        d,
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
        profil_frais_placement=profil_frais_3h_b(d),
    )

    resume = formater_estimation_fiscale_2025(e)
    assert "BLOC 3H-B" in resume
    assert "18500.00 $" in resume
    assert "130 + 166 + 167 - 231" in resume
    assert "3.70 $" in resume

    trace = construire_trace_calcul_fiscal_2025(e)
    ligne = next(x for x in trace.lignes if x.libelle == "FSS combinée 3H-B ligne 446")
    assert ligne.montant == D("3.70")
    assert "130 + 166 + 167 - 231" in ligne.formule
    assert "252 sans effet" in ligne.formule

    pdf = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "rapport_3h_b.pdf")
    with fitz.open(pdf) as doc:
        texte = chr(10).join(page.get_text() for page in doc)

    assert "BLOC 3H-B" in texte
    assert "18 500,00" in texte or "18500.00" in texte
    assert "3,70" in texte or "3.70" in texte


def test_3h_a_resume_reste_inchange_sans_frais():
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025, formater_estimation_fiscale_2025

    e = calculer_estimation_fiscale_2025(
        dossier_combine(),
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
    )

    resume = formater_estimation_fiscale_2025(e)
    assert "BLOC 3H-A" in resume
    assert "BLOC 3H-B" not in resume
    assert "20000.00 $" in resume
# --- Bloc 3H-C : intérêts + dividendes + gain/perte en capital ---

def dossier_3h_c(produit="6500", courtage="60", emploi=False):
    from tests.test_tax_capital_gains_2025 import dossier_capital

    base = dossier_combine(emploi=emploi)
    cap = dossier_capital(produit=produit, courtage=courtage, emploi=emploi)
    docs_existants = {p.resolve() for p in base.documents}
    docs_capital = tuple(p for p in cap.documents if p.resolve() not in docs_existants)
    donnees_capital = tuple(
        d for d in cap.donnees_validees
        if d.type_document in {"T5008", "RL-18"}
    )
    return replace(
        base,
        documents=base.documents + docs_capital,
        donnees_validees=base.donnees_validees + donnees_capital,
    )


def test_3h_c_applique_interets_dividendes_et_capital():
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
    from tests.test_tax_capital_gains_2025 import profil_capital

    d = dossier_3h_c()
    e = calculer_estimation_fiscale_2025(
        d,
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
        profil_capital=profil_capital(),
    )

    assert e.interets.present
    assert e.dividendes.present
    assert e.capital.present
    assert e.capital.ligne_12700 == D("1220")
    assert e.capital.ligne_139 == D("1220")
    assert e.revenu.revenu_total_federal == D("23870")
    assert e.revenu.revenu_total_quebec == D("23870")


def test_3h_c_fss_globale_comptee_une_seule_fois():
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
    from tests.test_tax_capital_gains_2025 import profil_capital

    e = calculer_estimation_fiscale_2025(
        dossier_3h_c(),
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
        profil_capital=profil_capital(),
    )

    assert e.interets.cotisation_fss == D("30.90")
    assert e.dividendes.cotisation_fss == D("0")
    assert e.capital.cotisation_fss == D("0")
    assert (
        e.interets.cotisation_fss
        + e.dividendes.cotisation_fss
        + e.capital.cotisation_fss
    ) == D("30.90")


def test_3h_c_perte_capital_ne_reduit_pas_interets_ni_dividendes():
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
    from tests.test_tax_capital_gains_2025 import profil_capital

    e = calculer_estimation_fiscale_2025(
        dossier_3h_c(produit="3000"),
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
        profil_capital=profil_capital(),
    )

    assert e.capital.perte_nette_2025 == D("530")
    assert e.capital.ligne_139 == D("0")
    assert e.revenu.revenu_total_federal == D("22650")
    assert e.revenu.revenu_total_quebec == D("22650")
    assert e.interets.cotisation_fss == D("18.70")
    assert e.dividendes.cotisation_fss == D("0")
    assert e.capital.cotisation_fss == D("0")


def test_3h_c_refuse_frais_non_confirmes_avant_3h_d():
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
    from src.comptaprivee.tax_investment_expenses_2025 import ProfilFraisPlacement2025
    from tests.test_tax_capital_gains_2025 import profil_capital

    with pytest.raises(ValueError, match="Confirmez les frais de placement"):
        calculer_estimation_fiscale_2025(
            dossier_3h_c(),
            profil_interets=profil_interets(),
            profil_dividendes=profil_dividendes(),
            profil_capital=profil_capital(),
            profil_frais_placement=ProfilFraisPlacement2025(gestion="1"),
        )

def test_3h_c_sauvegarde_et_rechargement_des_trois_profils(tmp_path):
    from src.comptaprivee.tax_case_storage import (
        charger_dossier_fiscal,
        sauvegarder_dossier_fiscal,
    )
    from tests.test_tax_capital_gains_2025 import profil_capital

    d = dossier_3h_c()
    chemin = sauvegarder_dossier_fiscal(
        d,
        destination=tmp_path / "3h_c.json",
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
        profil_capital=profil_capital(),
    )

    charge = charger_dossier_fiscal(chemin)
    assert charge.profil_interets == profil_interets()
    assert charge.profil_dividendes == profil_dividendes()
    assert charge.profil_capital == profil_capital()


def test_3h_c_rechargement_recalcule_meme_resultat(tmp_path):
    from src.comptaprivee.tax_case_storage import (
        charger_dossier_fiscal,
        sauvegarder_dossier_fiscal,
    )
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
    from tests.test_tax_capital_gains_2025 import profil_capital

    d = dossier_3h_c()
    attendu = calculer_estimation_fiscale_2025(
        d,
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
        profil_capital=profil_capital(),
    )
    chemin = sauvegarder_dossier_fiscal(
        d,
        destination=tmp_path / "3h_c_recalcul.json",
        estimation=attendu,
    )
    charge = charger_dossier_fiscal(chemin)
    obtenu = calculer_estimation_fiscale_2025(
        charge.dossier,
        profil_interets=charge.profil_interets,
        profil_dividendes=charge.profil_dividendes,
        profil_capital=charge.profil_capital,
    )

    assert obtenu.revenu == attendu.revenu
    assert obtenu.capital == attendu.capital
    assert obtenu.interets.cotisation_fss == attendu.interets.cotisation_fss


def test_3h_c_stockage_autorise_brouillon_frais_non_confirmes(tmp_path):
    from src.comptaprivee.tax_case_storage import (
        charger_dossier_fiscal,
        sauvegarder_dossier_fiscal,
    )
    from src.comptaprivee.tax_investment_expenses_2025 import ProfilFraisPlacement2025
    from tests.test_tax_capital_gains_2025 import profil_capital

    brouillon = ProfilFraisPlacement2025(gestion="1")
    chemin = sauvegarder_dossier_fiscal(
        dossier_3h_c(),
        destination=tmp_path / "3h_c_frais_brouillon.json",
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
        profil_capital=profil_capital(),
        profil_frais_placement=brouillon,
    )

    charge = charger_dossier_fiscal(chemin)
    assert charge.profil_frais_placement == brouillon
    assert not charge.profil_frais_placement.confirme

def test_3h_c_resume_trace_pdf_affichent_assiette_globale(tmp_path):
    import fitz

    from src.comptaprivee.tax_calculation_trace_2025 import (
        construire_trace_calcul_fiscal_2025,
    )
    from src.comptaprivee.tax_estimation_2025 import (
        calculer_estimation_fiscale_2025,
        formater_estimation_fiscale_2025,
    )
    from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
    from tests.test_tax_capital_gains_2025 import profil_capital

    e = calculer_estimation_fiscale_2025(
        dossier_3h_c(),
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
        profil_capital=profil_capital(),
    )

    resume = formater_estimation_fiscale_2025(e)
    assert "BLOC 3H-C" in resume
    assert "21220.00 $" in resume
    assert "130 + 166 + 167 + 139" in resume
    assert "30.90 $" in resume

    trace = construire_trace_calcul_fiscal_2025(e)
    ligne = next(
        x for x in trace.lignes
        if x.libelle == "FSS combinée 3H-C ligne 446"
    )
    assert ligne.montant == D("30.90")
    assert "130 + 166 + 167 + 139" in ligne.formule
    assert "perte 2025 non déductible" in ligne.formule

    pdf = exporter_rapport_fiscal_pdf_2025(
        e,
        tmp_path / "rapport_3h_c.pdf",
    )
    with fitz.open(pdf) as doc:
        texte = chr(10).join(page.get_text() for page in doc)

    assert "BLOC 3H-C" in texte
    assert "21 220,00" in texte or "21220.00" in texte
    assert "30,90" in texte or "30.90" in texte


def test_3h_c_perte_resume_garde_assiette_interets_dividendes():
    from src.comptaprivee.tax_estimation_2025 import (
        calculer_estimation_fiscale_2025,
        formater_estimation_fiscale_2025,
    )
    from tests.test_tax_capital_gains_2025 import profil_capital

    e = calculer_estimation_fiscale_2025(
        dossier_3h_c(produit="3000"),
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
        profil_capital=profil_capital(),
    )

    resume = formater_estimation_fiscale_2025(e)
    assert "BLOC 3H-C" in resume
    assert "20000.00 $" in resume
    assert "18.70 $" in resume

# --- Bloc 3H-D : intérêts + dividendes + capital + frais de placement ---

def profil_frais_3h_d(dossier, gestion="1500", interets="0"):
    from src.comptaprivee.tax_investment_expenses_2025 import (
        ProfilFraisPlacement2025,
        empreinte_frais_placement_2025,
    )
    from tests.test_tax_capital_gains_2025 import profil_capital

    p = ProfilFraisPlacement2025(
        gestion=gestion,
        interets=interets,
        source="Facture synthétique 3H-D F-2025-2, compte unique",
        paiement="Paiements 2025 vérifiés, frais ventilés",
        utilisation="Placements canadiens 3H-D productifs de revenus",
        solde_quebec="0",
        demande_252="0",
        source_report="",
        confirme=True,
        report_confirme=True,
    )
    return replace(
        p,
        empreinte=empreinte_frais_placement_2025(
            p,
            dossier,
            profil_interets(),
            profil_dividendes(),
            profil_capital(),
        ),
    )


def test_3h_d_applique_frais_aux_trois_revenus():
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
    from tests.test_tax_capital_gains_2025 import profil_capital

    d = dossier_3h_c()
    e = calculer_estimation_fiscale_2025(
        d,
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
        profil_capital=profil_capital(),
        profil_frais_placement=profil_frais_3h_d(d),
    )

    assert e.interets.present
    assert e.dividendes.present
    assert e.capital.present
    assert e.frais_placement.present
    assert e.frais_placement.ligne_22100 == D("1500")
    assert e.frais_placement.ligne_231 == D("1500")
    assert e.frais_placement.revenus_n36 == D("23870")
    assert e.revenu.revenu_total_federal == D("23870")
    assert e.revenu.revenu_total_quebec == D("23870")
    assert e.revenu.revenu_net_federal == D("22370")
    assert e.revenu.revenu_net_quebec == D("22370")


def test_3h_d_fss_apres_frais_comptee_une_seule_fois():
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
    from tests.test_tax_capital_gains_2025 import profil_capital

    d = dossier_3h_c()
    e = calculer_estimation_fiscale_2025(
        d,
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
        profil_capital=profil_capital(),
        profil_frais_placement=profil_frais_3h_d(d),
    )

    assert e.frais_placement.assiette_fss == D("19720")
    assert e.frais_placement.cotisation_fss == D("15.90")
    assert e.interets.cotisation_fss == D("15.90")
    assert e.dividendes.cotisation_fss == D("0")
    assert e.capital.cotisation_fss == D("0")
    assert (
        e.interets.cotisation_fss
        + e.dividendes.cotisation_fss
        + e.capital.cotisation_fss
    ) == D("15.90")


def test_3h_d_refuse_interets_emprunt_avec_capital():
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
    from tests.test_tax_capital_gains_2025 import profil_capital

    d = dossier_3h_c()
    with pytest.raises(ValueError, match="3H-D.*intérêts d.emprunt|intérêts d.emprunt.*3H-D"):
        calculer_estimation_fiscale_2025(
            d,
            profil_interets=profil_interets(),
            profil_dividendes=profil_dividendes(),
            profil_capital=profil_capital(),
            profil_frais_placement=profil_frais_3h_d(
                d,
                gestion="500",
                interets="1000",
            ),
        )

def test_3h_d_sauvegarde_et_rechargement_des_quatre_profils(tmp_path):
    from src.comptaprivee.tax_case_storage import (
        charger_dossier_fiscal,
        sauvegarder_dossier_fiscal,
    )
    from tests.test_tax_capital_gains_2025 import profil_capital

    d = dossier_3h_c()
    frais = profil_frais_3h_d(d)
    chemin = sauvegarder_dossier_fiscal(
        d,
        destination=tmp_path / "3h_d.json",
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
        profil_capital=profil_capital(),
        profil_frais_placement=frais,
    )

    charge = charger_dossier_fiscal(chemin)
    assert charge.profil_interets == profil_interets()
    assert charge.profil_dividendes == profil_dividendes()
    assert charge.profil_capital == profil_capital()
    assert charge.profil_frais_placement == frais


def test_3h_d_rechargement_recalcule_meme_resultat(tmp_path):
    from src.comptaprivee.tax_case_storage import (
        charger_dossier_fiscal,
        sauvegarder_dossier_fiscal,
    )
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
    from tests.test_tax_capital_gains_2025 import profil_capital

    d = dossier_3h_c()
    frais = profil_frais_3h_d(d)
    attendu = calculer_estimation_fiscale_2025(
        d,
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
        profil_capital=profil_capital(),
        profil_frais_placement=frais,
    )
    chemin = sauvegarder_dossier_fiscal(
        d,
        destination=tmp_path / "3h_d_recalcul.json",
        estimation=attendu,
    )
    charge = charger_dossier_fiscal(chemin)
    obtenu = calculer_estimation_fiscale_2025(
        charge.dossier,
        profil_interets=charge.profil_interets,
        profil_dividendes=charge.profil_dividendes,
        profil_capital=charge.profil_capital,
        profil_frais_placement=charge.profil_frais_placement,
    )

    assert obtenu.revenu == attendu.revenu
    assert obtenu.capital == attendu.capital
    assert obtenu.frais_placement == attendu.frais_placement
    assert obtenu.interets.cotisation_fss == attendu.interets.cotisation_fss


def test_3h_d_rechargement_refuse_empreinte_frais_incoherente(tmp_path):
    from src.comptaprivee.tax_case_storage import (
        charger_dossier_fiscal,
        sauvegarder_dossier_fiscal,
    )
    from tests.test_tax_capital_gains_2025 import profil_capital

    d = dossier_3h_c()
    frais = profil_frais_3h_d(d)
    chemin = sauvegarder_dossier_fiscal(
        d,
        destination=tmp_path / "3h_d_empreinte.json",
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
        profil_capital=profil_capital(),
        profil_frais_placement=frais,
    )

    contenu = chemin.read_text(encoding="utf-8")
    contenu = contenu.replace(frais.empreinte, "0" * len(frais.empreinte), 1)
    chemin.write_text(contenu, encoding="utf-8")

    with pytest.raises(ValueError, match="empreinte|frais|profil"):
        charger_dossier_fiscal(chemin)

def test_3h_d_resume_trace_pdf_affichent_assiette_apres_frais(tmp_path):
    import fitz

    from src.comptaprivee.tax_calculation_trace_2025 import (
        construire_trace_calcul_fiscal_2025,
    )
    from src.comptaprivee.tax_estimation_2025 import (
        calculer_estimation_fiscale_2025,
        formater_estimation_fiscale_2025,
    )
    from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
    from tests.test_tax_capital_gains_2025 import profil_capital

    d = dossier_3h_c()
    e = calculer_estimation_fiscale_2025(
        d,
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
        profil_capital=profil_capital(),
        profil_frais_placement=profil_frais_3h_d(d),
    )

    resume = formater_estimation_fiscale_2025(e)
    assert "BLOC 3H-D" in resume
    assert "19720.00 $" in resume
    assert "130 + 166 + 167 + 139 - 231" in resume
    assert "15.90 $" in resume

    trace = construire_trace_calcul_fiscal_2025(e)
    ligne = next(
        x for x in trace.lignes
        if x.libelle == "FSS combinée 3H-D ligne 446"
    )
    assert ligne.montant == D("15.90")
    assert "130 + 166 + 167 + 139 - 231" in ligne.formule
    assert "252 sans effet" in ligne.formule

    pdf = exporter_rapport_fiscal_pdf_2025(
        e,
        tmp_path / "rapport_3h_d.pdf",
    )
    with fitz.open(pdf) as doc:
        texte = chr(10).join(page.get_text() for page in doc)

    assert "BLOC 3H-D" in texte
    assert "19 720,00" in texte or "19720.00" in texte
    assert "15,90" in texte or "15.90" in texte


def test_3h_d_perte_capital_et_frais_ne_reduisent_pas_autres_revenus():
    from src.comptaprivee.tax_estimation_2025 import (
        calculer_estimation_fiscale_2025,
        formater_estimation_fiscale_2025,
    )
    from tests.test_tax_capital_gains_2025 import profil_capital

    d = dossier_3h_c(produit="3000")
    e = calculer_estimation_fiscale_2025(
        d,
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
        profil_capital=profil_capital(),
        profil_frais_placement=profil_frais_3h_d(d),
    )

    assert e.capital.ligne_139 == D("0")
    assert e.capital.perte_nette_2025 == D("530")
    assert e.frais_placement.assiette_fss == D("18500")
    assert e.interets.cotisation_fss == D("3.70")
    assert e.dividendes.cotisation_fss == D("0")
    assert e.capital.cotisation_fss == D("0")

    resume = formater_estimation_fiscale_2025(e)
    assert "BLOC 3H-D" in resume
    assert "18500.00 $" in resume
    assert "3.70 $" in resume

# --- Bloc 3H-E : intérêts + dividendes + capital + reports de pertes ---

def test_3h_e_applique_reports_sans_modifier_total_net_ou_fss():
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
    from tests.test_tax_capital_gains_2025 import profil_capital
    from tests.test_tax_capital_loss_carryovers_2025 import profil_pertes

    d = dossier_3h_c()
    pertes = profil_pertes(
        d,
        demande_federale="1000",
        demande_quebec="800",
    )
    e = calculer_estimation_fiscale_2025(
        d,
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
        profil_capital=profil_capital(),
        profil_reports_pertes=pertes,
    )

    assert e.reports_pertes.present
    assert e.reports_pertes.ligne_25300 == D("1000")
    assert e.reports_pertes.ligne_290 == D("800")
    assert e.revenu.revenu_total_federal == D("23870")
    assert e.revenu.revenu_total_quebec == D("23870")
    assert e.revenu.revenu_net_federal == D("23870")
    assert e.revenu.revenu_net_quebec == D("23870")
    assert e.revenu.revenu_imposable_federal == D("22870")
    assert e.revenu.revenu_imposable_quebec == D("23070")
    assert e.interets.cotisation_fss == D("30.90")
    assert e.dividendes.cotisation_fss == D("0")
    assert e.capital.cotisation_fss == D("0")


def test_3h_e_plafond_reports_reste_lie_au_gain_capital():
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
    from tests.test_tax_capital_gains_2025 import profil_capital
    from tests.test_tax_capital_loss_carryovers_2025 import profil_pertes

    d = dossier_3h_c()
    pertes = profil_pertes(
        d,
        demande_federale="1220.01",
        demande_quebec="0",
    )

    with pytest.raises(ValueError, match="25300 dépasse"):
        calculer_estimation_fiscale_2025(
            d,
            profil_interets=profil_interets(),
            profil_dividendes=profil_dividendes(),
            profil_capital=profil_capital(),
            profil_reports_pertes=pertes,
        )


def test_3h_e_refuse_encore_frais_et_reports_ensemble():
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
    from tests.test_tax_capital_gains_2025 import profil_capital
    from tests.test_tax_capital_loss_carryovers_2025 import profil_pertes

    d = dossier_3h_c()
    frais = profil_frais_3h_d(d)
    pertes = profil_pertes(
        d,
        frais=frais,
        demande_federale="1000",
        demande_quebec="800",
    )

    with pytest.raises(ValueError, match="3H-F"):
        calculer_estimation_fiscale_2025(
            d,
            profil_interets=profil_interets(),
            profil_dividendes=profil_dividendes(),
            profil_capital=profil_capital(),
            profil_frais_placement=frais,
            profil_reports_pertes=pertes,
        )

def test_3h_e_stockage_recharge_cinq_profils_et_recalcule(tmp_path):
    from src.comptaprivee.tax_case_storage import (
        charger_dossier_fiscal,
        sauvegarder_dossier_fiscal,
    )
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
    from src.comptaprivee.tax_investment_expenses_2025 import ProfilFraisPlacement2025
    from tests.test_tax_capital_gains_2025 import profil_capital
    from tests.test_tax_capital_loss_carryovers_2025 import profil_pertes

    d = dossier_3h_c()
    pertes = profil_pertes(
        d,
        demande_federale="1000",
        demande_quebec="800",
    )
    attendu = calculer_estimation_fiscale_2025(
        d,
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
        profil_capital=profil_capital(),
        profil_reports_pertes=pertes,
    )
    chemin = sauvegarder_dossier_fiscal(
        d,
        destination=tmp_path / "3h_e.json",
        estimation=attendu,
    )

    charge = charger_dossier_fiscal(chemin)
    assert charge.profil_interets == profil_interets()
    assert charge.profil_dividendes == profil_dividendes()
    assert charge.profil_capital == profil_capital()
    assert charge.profil_frais_placement == ProfilFraisPlacement2025()
    assert charge.profil_reports_pertes == pertes

    obtenu = calculer_estimation_fiscale_2025(
        charge.dossier,
        profil_interets=charge.profil_interets,
        profil_dividendes=charge.profil_dividendes,
        profil_capital=charge.profil_capital,
        profil_frais_placement=charge.profil_frais_placement,
        profil_reports_pertes=charge.profil_reports_pertes,
    )
    assert obtenu.revenu == attendu.revenu
    assert obtenu.reports_pertes == attendu.reports_pertes
    assert obtenu.interets.cotisation_fss == attendu.interets.cotisation_fss


def test_3h_e_stockage_direct_accepte_reports_confirmes(tmp_path):
    from src.comptaprivee.tax_case_storage import (
        charger_dossier_fiscal,
        sauvegarder_dossier_fiscal,
    )
    from tests.test_tax_capital_gains_2025 import profil_capital
    from tests.test_tax_capital_loss_carryovers_2025 import profil_pertes

    d = dossier_3h_c()
    pertes = profil_pertes(
        d,
        demande_federale="1000",
        demande_quebec="800",
    )
    chemin = sauvegarder_dossier_fiscal(
        d,
        destination=tmp_path / "3h_e_direct.json",
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
        profil_capital=profil_capital(),
        profil_reports_pertes=pertes,
    )
    charge = charger_dossier_fiscal(chemin)
    assert charge.profil_reports_pertes == pertes


def test_3h_e_stockage_refuse_reports_sans_capital(tmp_path):
    from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal
    from tests.test_tax_capital_loss_carryovers_2025 import profil_pertes

    d = dossier_combine()
    pertes = profil_pertes(
        d,
        demande_federale="0",
        demande_quebec="0",
    )
    with pytest.raises(ValueError, match="3H-E"):
        sauvegarder_dossier_fiscal(
            d,
            destination=tmp_path / "3h_e_sans_capital.json",
            profil_interets=profil_interets(),
            profil_dividendes=profil_dividendes(),
            profil_reports_pertes=pertes,
        )


def test_3h_e_stockage_refuse_frais_et_reports_ensemble(tmp_path):
    from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal
    from tests.test_tax_capital_gains_2025 import profil_capital
    from tests.test_tax_capital_loss_carryovers_2025 import profil_pertes

    d = dossier_3h_c()
    frais = profil_frais_3h_d(d)
    pertes = profil_pertes(
        d,
        frais=frais,
        demande_federale="1000",
        demande_quebec="800",
    )
    with pytest.raises(ValueError, match="3H-F"):
        sauvegarder_dossier_fiscal(
            d,
            destination=tmp_path / "3h_f_reserve.json",
            profil_interets=profil_interets(),
            profil_dividendes=profil_dividendes(),
            profil_capital=profil_capital(),
            profil_frais_placement=frais,
            profil_reports_pertes=pertes,
        )


def test_3h_e_rechargement_refuse_empreinte_reports_alteree(tmp_path):
    from src.comptaprivee.tax_case_storage import (
        charger_dossier_fiscal,
        sauvegarder_dossier_fiscal,
    )
    from tests.test_tax_capital_gains_2025 import profil_capital
    from tests.test_tax_capital_loss_carryovers_2025 import profil_pertes

    d = dossier_3h_c()
    pertes = profil_pertes(
        d,
        demande_federale="1000",
        demande_quebec="800",
    )
    chemin = sauvegarder_dossier_fiscal(
        d,
        destination=tmp_path / "3h_e_empreinte.json",
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
        profil_capital=profil_capital(),
        profil_reports_pertes=pertes,
    )

    contenu = chemin.read_text(encoding="utf-8")
    contenu = contenu.replace(pertes.empreinte, "0" * len(pertes.empreinte), 1)
    chemin.write_text(contenu, encoding="utf-8")

    with pytest.raises(ValueError, match="Confirmation reports de pertes périmée"):
        charger_dossier_fiscal(chemin)

def test_3h_e_resume_et_trace_identifient_bloc_sans_modifier_fss():
    from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
    from src.comptaprivee.tax_estimation_2025 import (
        calculer_estimation_fiscale_2025,
        formater_estimation_fiscale_2025,
    )
    from tests.test_tax_capital_gains_2025 import profil_capital
    from tests.test_tax_capital_loss_carryovers_2025 import profil_pertes

    d = dossier_3h_c()
    pertes = profil_pertes(
        d,
        demande_federale="1000",
        demande_quebec="800",
    )
    e = calculer_estimation_fiscale_2025(
        d,
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
        profil_capital=profil_capital(),
        profil_reports_pertes=pertes,
    )

    resume = formater_estimation_fiscale_2025(e)
    assert "BLOC 3H-E" in resume
    assert "reports 25300/290 sans effet FSS" in resume
    assert "30.90 $" in resume
    assert e.revenu.revenu_imposable_federal == D("22870")
    assert e.revenu.revenu_imposable_quebec == D("23070")

    trace = construire_trace_calcul_fiscal_2025(e)
    ligne = next(
        x for x in trace.lignes
        if x.libelle == "FSS combinée 3H-E ligne 446"
    )
    assert ligne.montant == D("30.90")
    assert "reports 25300/290 sans effet" in ligne.formule


def test_3h_e_pdf_identifie_bloc_et_reports(tmp_path):
    import fitz

    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
    from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
    from tests.test_tax_capital_gains_2025 import profil_capital
    from tests.test_tax_capital_loss_carryovers_2025 import profil_pertes

    d = dossier_3h_c()
    pertes = profil_pertes(
        d,
        demande_federale="1000",
        demande_quebec="800",
    )
    e = calculer_estimation_fiscale_2025(
        d,
        profil_interets=profil_interets(),
        profil_dividendes=profil_dividendes(),
        profil_capital=profil_capital(),
        profil_reports_pertes=pertes,
    )

    pdf = exporter_rapport_fiscal_pdf_2025(
        e,
        tmp_path / "rapport_3h_e.pdf",
    )
    with fitz.open(pdf) as doc:
        texte = chr(10).join(page.get_text() for page in doc)

    assert "BLOC 3H-E" in texte
    assert "25300" in texte
    assert "290" in texte
    assert "30,90" in texte or "30.90" in texte
