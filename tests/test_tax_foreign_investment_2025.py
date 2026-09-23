"""Tests unitaires préparatoires du Bloc 3G.

Ces tests valident seulement le nouveau consolidateur T5/RL-3 étranger.
L'intégration à l'orchestrateur, au crédit T2209/TP-772, à la GUI et au PDF
sera ajoutée dans les étapes suivantes.
"""
from dataclasses import replace
from decimal import Decimal as D
from pathlib import Path

import pytest

from src.comptaprivee.tax_foreign_investment_2025 import (
    ProfilPlacementEtranger2025,
    consolider_placement_etranger_2025,
    detecter_placement_etranger_2025,
    valider_profil_placement_etranger_2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000, _validee


def profil():
    return ProfilPlacementEtranger2025(
        source="T5/RL-3 synthétiques vérifiés",
        confirme=True,
        pays="États-Unis",
        devise="CAD",
        obligations_biens_etrangers_verifiees=True,
    )


def dossier(revenu="1000.00", impot="150.00", emploi=False):
    d = _dossier_52000()
    if not emploi:
        d = replace(d, documents=(), donnees_validees=())
    docs = (Path("T5-etranger.pdf"), Path("RL-3-etranger.pdf"))
    vals = (
        _validee(docs[0], "T5", "15", revenu),
        _validee(docs[0], "T5", "16", impot),
        _validee(docs[1], "RL-3", "F", revenu),
        _validee(docs[1], "RL-3", "G", impot),
    )
    return replace(
        d,
        documents=d.documents + docs,
        donnees_validees=d.donnees_validees + vals,
    )


@pytest.mark.parametrize("emploi", [False, True])
def test_consolidation_pairage(emploi):
    p = consolider_placement_etranger_2025(dossier(emploi=emploi), profil())
    assert p.present
    assert p.revenu_brut_federal == D("1000.00")
    assert p.revenu_brut_quebec == D("1000.00")
    assert p.impot_etranger_federal == D("150.00")
    assert p.impot_etranger_quebec == D("150.00")
    assert p.pays == "États-Unis"


def test_detection():
    assert detecter_placement_etranger_2025(dossier())
    d = _dossier_52000()
    assert not detecter_placement_etranger_2025(d)


@pytest.mark.parametrize(
    "champ,valeur",
    [
        ("confirme", 1),
        ("titulaire_unique", 1),
        ("devise", "USD"),
        ("pays", ""),
        ("source", ""),
        ("obligations_biens_etrangers_verifiees", False),
        ("aucun_compte_conjoint", False),
        ("aucune_entreprise", False),
        ("aucune_pension_etrangere", False),
        ("aucun_gain_capital_etranger", False),
        ("aucune_situation_multi_pays", False),
        ("revenu_non_commercial", False),
        ("aucun_revenu_exonere_convention", False),
    ],
)
def test_profils_refuses(champ, valeur):
    with pytest.raises(ValueError):
        valider_profil_placement_etranger_2025(replace(profil(), **{champ: valeur}))


@pytest.mark.parametrize(
    "revenu,impot",
    [
        ("-1.00", "0.00"),
        ("NaN", "0.00"),
        ("Infinity", "0.00"),
        ("0.001", "0.00"),
        ("1000000000.00", "0.00"),
        ("100.00", "-1.00"),
        ("100.00", "NaN"),
        ("100.00", "0.001"),
    ],
)
def test_montants_invalides(revenu, impot):
    with pytest.raises(ValueError):
        consolider_placement_etranger_2025(dossier(revenu, impot), profil())


def test_impot_superieur_revenu_refuse():
    with pytest.raises(ValueError, match="supérieur au revenu brut"):
        consolider_placement_etranger_2025(dossier("100.00", "101.00"), profil())


def test_t5_rl3_revenu_divergent_refuse():
    d = dossier()
    vals = list(d.donnees_validees)
    vals[-2] = replace(vals[-2], valeur_validee=D("999.00"))
    with pytest.raises(ValueError, match="T5 15 et RL-3 F"):
        consolider_placement_etranger_2025(
            replace(d, donnees_validees=tuple(vals)), profil()
        )


def test_t5_rl3_impot_divergent_refuse():
    d = dossier()
    vals = list(d.donnees_validees)
    vals[-1] = replace(vals[-1], valeur_validee=D("149.00"))
    with pytest.raises(ValueError, match="T5 16 et RL-3 G"):
        consolider_placement_etranger_2025(
            replace(d, donnees_validees=tuple(vals)), profil()
        )


def test_case_obligatoire_manquante_refusee():
    d = dossier()
    with pytest.raises(ValueError, match="obligatoires"):
        consolider_placement_etranger_2025(
            replace(d, donnees_validees=d.donnees_validees[:-1]), profil()
        )


def test_document_sans_donnees_refuse():
    d = dossier()
    with pytest.raises(ValueError, match="Chaque pièce"):
        consolider_placement_etranger_2025(
            replace(d, documents=d.documents + (Path("autre.pdf"),)), profil()
        )


def test_confirmation_obligatoire():
    with pytest.raises(ValueError, match="Confirmez"):
        consolider_placement_etranger_2025(
            dossier(), replace(profil(), confirme=False)
        )


def test_appliquer_revenu_etranger_sans_reduire_par_impot():
    from src.comptaprivee.tax_foreign_investment_2025 import (
        appliquer_placement_etranger_2025,
    )
    from src.comptaprivee.tax_income_2025 import RevenuNetImposable2025

    base = RevenuNetImposable2025(
        client="Client test",
        annee_fiscale=2025,
        province="Québec",
        revenu_total_federal=D("10000"),
        deduction_rrq_amelioree_federale=D("0"),
        revenu_net_federal=D("9000"),
        revenu_imposable_federal=D("8000"),
        revenu_total_quebec=D("10000"),
        deduction_travailleur_quebec=D("0"),
        deduction_rrq_quebec=D("0"),
        revenu_net_quebec=D("9000"),
        revenu_imposable_quebec=D("8000"),
        profil="Test",
        limitations=(),
    )
    placement = consolider_placement_etranger_2025(
        dossier("1000.00", "150.00"), profil()
    )
    r = appliquer_placement_etranger_2025(base, placement)

    assert r.revenu_total_federal == D("11000")
    assert r.revenu_net_federal == D("10000")
    assert r.revenu_imposable_federal == D("9000")
    assert r.revenu_total_quebec == D("11000")
    assert r.revenu_net_quebec == D("10000")
    assert r.revenu_imposable_quebec == D("9000")
    assert r.revenu_total_federal != D("10850")


def test_appliquer_absent_ne_change_pas_revenu():
    from src.comptaprivee.tax_foreign_investment_2025 import (
        PlacementEtranger2025,
        appliquer_placement_etranger_2025,
    )
    from src.comptaprivee.tax_income_2025 import RevenuNetImposable2025

    base = RevenuNetImposable2025(
        client="Client test",
        annee_fiscale=2025,
        province="Québec",
        revenu_total_federal=D("0"),
        deduction_rrq_amelioree_federale=D("0"),
        revenu_net_federal=D("0"),
        revenu_imposable_federal=D("0"),
        revenu_total_quebec=D("0"),
        deduction_travailleur_quebec=D("0"),
        deduction_rrq_quebec=D("0"),
        revenu_net_quebec=D("0"),
        revenu_imposable_quebec=D("0"),
        profil="Test",
        limitations=(),
    )
    assert appliquer_placement_etranger_2025(base, PlacementEtranger2025()) == base


def test_resume_placement_etranger():
    from src.comptaprivee.tax_foreign_investment_2025 import (
        lignes_resume_placement_etranger_2025,
    )

    placement = consolider_placement_etranger_2025(dossier(), profil())
    texte = "\n".join(lignes_resume_placement_etranger_2025(placement, profil()))
    assert "BLOC 3G" in texte
    assert "12100" in texte
    assert "130" in texte
    assert "T2209/40500" in texte
    assert "TP-772/409" in texte
    assert "T1135/TP-1079.8.BE" in texte


def profil_credit(federal="100.00", quebec="50.00"):
    from src.comptaprivee.tax_foreign_investment_2025 import (
        ProfilCreditImpotEtranger2025,
    )
    return ProfilCreditImpotEtranger2025(
        credit_federal_40500=D(federal),
        credit_quebec_409=D(quebec),
        source_t2209="T2209 2025 synthétique vérifié",
        source_tp772="TP-772 2025 synthétique vérifié",
        confirme=True,
    )


def test_credit_etranger_confirme_et_plafonds_evidents():
    from src.comptaprivee.tax_foreign_investment_2025 import (
        consolider_credit_impot_etranger_2025,
    )
    placement = consolider_placement_etranger_2025(
        dossier("1000.00", "150.00"), profil()
    )
    c = consolider_credit_impot_etranger_2025(
        placement, profil_credit("100.00", "50.00")
    )
    assert c.ligne_40500 == D("100.00")
    assert c.ligne_409 == D("50.00")
    assert c.present


@pytest.mark.parametrize(
    "federal,quebec,message",
    [
        ("151.00", "0.00", "40500"),
        ("100.00", "51.00", "409"),
    ],
)
def test_credit_etranger_depasse_garde_fou_refuse(federal, quebec, message):
    from src.comptaprivee.tax_foreign_investment_2025 import (
        consolider_credit_impot_etranger_2025,
    )
    placement = consolider_placement_etranger_2025(
        dossier("1000.00", "150.00"), profil()
    )
    with pytest.raises(ValueError, match=message):
        consolider_credit_impot_etranger_2025(
            placement, profil_credit(federal, quebec)
        )


@pytest.mark.parametrize(
    "champ,valeur",
    [
        ("confirme", False),
        ("source_t2209", ""),
        ("source_tp772", ""),
        ("credit_federal_40500", D("-1.00")),
        ("credit_quebec_409", D("0.001")),
    ],
)
def test_profil_credit_etranger_invalide(champ, valeur):
    from src.comptaprivee.tax_foreign_investment_2025 import (
        consolider_credit_impot_etranger_2025,
    )
    placement = consolider_placement_etranger_2025(
        dossier("1000.00", "150.00"), profil()
    )
    with pytest.raises(ValueError):
        consolider_credit_impot_etranger_2025(
            placement, replace(profil_credit(), **{champ: valeur})
        )


def test_appliquer_credits_non_remboursables():
    from src.comptaprivee.tax_foreign_investment_2025 import (
        appliquer_credit_impot_etranger_2025,
        consolider_credit_impot_etranger_2025,
    )
    from src.comptaprivee.tax_federal_2025 import ImpotFederalPreliminaire2025
    from src.comptaprivee.tax_quebec_2025 import ImpotQuebecPreliminaire2025

    f = ImpotFederalPreliminaire2025(
        client="Client test",
        annee_fiscale=2025,
        revenu_imposable=D("10000"),
        impot_brut=D("1000"),
        montant_personnel_base=D("0"),
        cotisation_base_rrq=D("0"),
        assurance_emploi_admissible=D("0"),
        rqap_admissible=D("0"),
        montant_canadien_emploi=D("0"),
        base_credits_non_remboursables=D("0"),
        credits_non_remboursables=D("0"),
        impot_federal_de_base=D("80"),
        taux_credit=D("0.145"),
        top_up_credit=D("0"),
        limitations=(),
    )
    q = ImpotQuebecPreliminaire2025(
        client="Client test",
        annee_fiscale=2025,
        province="Québec",
        revenu_imposable=D("10000"),
        impot_brut=D("1000"),
        montant_personnel_base=D("0"),
        taux_credit_personnel=D("0.14"),
        credit_personnel_base=D("0"),
        impot_quebec_preliminaire=D("30"),
        limitations=(),
    )
    placement = consolider_placement_etranger_2025(
        dossier("1000.00", "150.00"), profil()
    )
    c = consolider_credit_impot_etranger_2025(
        placement, profil_credit("100.00", "50.00")
    )
    f2, q2 = appliquer_credit_impot_etranger_2025(f, q, c)
    assert f2.impot_federal_de_base == D("0")
    assert q2.impot_quebec_preliminaire == D("0")


def test_resume_credit_etranger():
    from src.comptaprivee.tax_foreign_investment_2025 import (
        consolider_credit_impot_etranger_2025,
        lignes_resume_credit_impot_etranger_2025,
    )
    placement = consolider_placement_etranger_2025(
        dossier("1000.00", "150.00"), profil()
    )
    pc = profil_credit("100.00", "50.00")
    c = consolider_credit_impot_etranger_2025(placement, pc)
    texte = "\n".join(lignes_resume_credit_impot_etranger_2025(c, pc))
    assert "40500" in texte
    assert "409" in texte
    assert "T2209" in texte
    assert "TP-772" in texte

def test_integration_estimation_3g_sans_emploi():
    from src.comptaprivee.tax_estimation_2025 import (
        calculer_estimation_fiscale_2025,
        formater_estimation_fiscale_2025,
    )

    e = calculer_estimation_fiscale_2025(
        dossier("10000.00", "1500.00"),
        profil_placement_etranger=profil(),
        profil_credit_impot_etranger=profil_credit("0.00", "0.00"),
    )
    assert e.placement_etranger.present
    assert e.credit_impot_etranger.present
    assert e.revenu.revenu_total_federal == D("10000.00")
    assert e.revenu.revenu_total_quebec == D("10000.00")
    assert e.revenu.revenu_net_federal == D("10000.00")
    assert e.revenu.revenu_net_quebec == D("10000.00")
    assert e.revenu.revenu_imposable_federal == D("10000.00")
    assert e.revenu.revenu_imposable_quebec == D("10000.00")
    texte = formater_estimation_fiscale_2025(e)
    assert "PLACEMENT ÉTRANGER 2025" in texte
    assert "CRÉDITS POUR IMPÔT ÉTRANGER 2025" in texte


def test_integration_estimation_3g_avec_emploi_et_credits():
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025

    d = dossier("10000.00", "1500.00", emploi=True)
    sans_credit = calculer_estimation_fiscale_2025(
        d,
        profil_placement_etranger=profil(),
        profil_credit_impot_etranger=profil_credit("0.00", "0.00"),
    )
    avec_credit = calculer_estimation_fiscale_2025(
        d,
        profil_placement_etranger=profil(),
        profil_credit_impot_etranger=profil_credit("100.00", "50.00"),
    )

    assert avec_credit.revenu.revenu_total_federal == D("62000.00")
    assert avec_credit.revenu.revenu_total_quebec == D("62000.00")
    assert (
        sans_credit.federal.impot_federal_de_base
        - avec_credit.federal.impot_federal_de_base
        == D("100.00")
    )
    assert (
        sans_credit.quebec.impot_quebec_preliminaire
        - avec_credit.quebec.impot_quebec_preliminaire
        == D("50.00")
    )


def test_3g_ne_tombe_pas_dans_parcours_interets_3a():
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025

    e = calculer_estimation_fiscale_2025(
        dossier("1000.00", "150.00"),
        profil_placement_etranger=profil(),
        profil_credit_impot_etranger=profil_credit("0.00", "0.00"),
    )
    assert e.placement_etranger.present
    assert not e.interets.present


def test_3g_refuse_profil_interets_en_meme_temps():
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
    from src.comptaprivee.tax_interest_income_2025 import ProfilInterets2025

    with pytest.raises(ValueError, match="hors périmètre 3G"):
        calculer_estimation_fiscale_2025(
            dossier("1000.00", "150.00"),
            profil_placement_etranger=profil(),
            profil_credit_impot_etranger=profil_credit("0.00", "0.00"),
            profil_interets=ProfilInterets2025(
                source="Autre placement",
                confirme=True,
            ),
        )

def test_stockage_rechargement_3g(tmp_path):
    import json
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
    from src.comptaprivee.tax_case_storage import (
        sauvegarder_dossier_fiscal,
        charger_dossier_fiscal,
    )

    e = calculer_estimation_fiscale_2025(
        dossier("10000.00", "1500.00", emploi=True),
        profil_placement_etranger=profil(),
        profil_credit_impot_etranger=profil_credit("100.00", "50.00"),
    )
    chemin = sauvegarder_dossier_fiscal(
        e.dossier,
        estimation=e,
        destination=tmp_path / "dossier_3g.json",
    )
    brut = json.loads(chemin.read_text(encoding="utf-8"))
    assert brut["profil_placement_etranger"]["pays"] == "États-Unis"
    assert brut["profil_credit_impot_etranger"]["credit_federal_40500"] == "100.00"
    assert brut["profil_credit_impot_etranger"]["credit_quebec_409"] == "50.00"

    charge = charger_dossier_fiscal(chemin)
    assert charge.profil_placement_etranger == profil()
    assert charge.profil_credit_impot_etranger == profil_credit("100.00", "50.00")

    recalcule = calculer_estimation_fiscale_2025(
        charge.dossier,
        profil_placement_etranger=charge.profil_placement_etranger,
        profil_credit_impot_etranger=charge.profil_credit_impot_etranger,
    )
    assert recalcule.revenu == e.revenu
    assert recalcule.federal == e.federal
    assert recalcule.quebec == e.quebec


def test_stockage_ancien_json_sans_3g_reste_compatible(tmp_path):
    import json
    from src.comptaprivee.tax_case_storage import (
        sauvegarder_dossier_fiscal,
        charger_dossier_fiscal,
    )
    from tests.test_tax_estimation_2025 import _dossier_52000
    from src.comptaprivee.tax_foreign_investment_2025 import (
        ProfilPlacementEtranger2025,
        ProfilCreditImpotEtranger2025,
    )

    chemin = sauvegarder_dossier_fiscal(
        _dossier_52000(),
        destination=tmp_path / "ancien.json",
    )
    brut = json.loads(chemin.read_text(encoding="utf-8"))
    brut.pop("profil_placement_etranger", None)
    brut.pop("profil_credit_impot_etranger", None)
    chemin.write_text(json.dumps(brut), encoding="utf-8")

    charge = charger_dossier_fiscal(chemin)
    assert charge.profil_placement_etranger == ProfilPlacementEtranger2025()
    assert charge.profil_credit_impot_etranger == ProfilCreditImpotEtranger2025()


def test_stockage_refuse_profil_3g_different_estimation(tmp_path):
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
    from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal

    e = calculer_estimation_fiscale_2025(
        dossier("1000.00", "150.00"),
        profil_placement_etranger=profil(),
        profil_credit_impot_etranger=profil_credit("100.00", "50.00"),
    )
    with pytest.raises(ValueError, match="placement étranger"):
        sauvegarder_dossier_fiscal(
            e.dossier,
            estimation=e,
            profil_placement_etranger=replace(profil(), pays="France"),
            destination=tmp_path / "different.json",
        )

def test_3g_fss_sur_revenu_placement_etranger_ligne_130():
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025

    e = calculer_estimation_fiscale_2025(
        dossier("20000.00", "3000.00"),
        profil_placement_etranger=profil(),
        profil_credit_impot_etranger=profil_credit("0.00", "0.00"),
    )
    # Même barème Annexe F que les autres revenus de placement ligne 130.
    assert e.placement_etranger.cotisation_fss == D("18.70")
    assert e.rapprochement.impot_total_preliminaire >= D("18.70")

def test_trace_3g_contient_revenu_credits_et_fss():
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
    from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025

    e = calculer_estimation_fiscale_2025(
        dossier("20000.00", "3000.00"),
        profil_placement_etranger=profil(),
        profil_credit_impot_etranger=profil_credit("100.00", "50.00"),
    )
    trace = construire_trace_calcul_fiscal_2025(e)
    texte = "\n".join(
        f"{x.section} | {x.libelle} | {x.source} | {x.formule} | {x.montant}"
        for x in trace.lignes
    )
    assert "Placement étranger ligne 12100" in texte
    assert "Placement étranger ligne 130" in texte
    assert "Crédit impôt étranger ligne 40500" in texte
    assert "Crédit impôt étranger ligne 409" in texte
    assert "FSS placement étranger ligne 446" in texte
    assert "T2209" in texte
    assert "TP-772" in texte


def test_pdf_3g_contient_revenu_credits_et_fss(tmp_path):
    import fitz
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
    from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025

    e = calculer_estimation_fiscale_2025(
        dossier("20000.00", "3000.00"),
        profil_placement_etranger=profil(),
        profil_credit_impot_etranger=profil_credit("100.00", "50.00"),
    )
    chemin = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "rapport_3g.pdf")
    with fitz.open(chemin) as doc:
        texte = "\n".join(page.get_text() for page in doc)

    assert "PLACEMENT ÉTRANGER 2025" in texte
    assert "CRÉDITS POUR IMPÔT ÉTRANGER 2025" in texte
    assert "12100" in texte
    assert "40500" in texte
    assert "409" in texte
    assert "FSS Québec 446" in texte
