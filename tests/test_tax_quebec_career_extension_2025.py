from dataclasses import replace
from decimal import Decimal as D
from pathlib import Path
import json
import fitz
import pytest
from src.comptaprivee.tax_quebec_career_extension_2025 import (
    ProlongationCarriereQuebec2025, CONFIRMATIONS_6D, calculer_carriere_quebec_2025 as moteur,
    carriere_quebec_vers_dict, carriere_quebec_depuis_dict)
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calcul, formater_estimation_fiscale_2025
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, dossier_fiscal_depuis_contenu
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from tests.test_tax_estimation_2025 import _dossier_52000, _validee


def profil(**kw):
    return replace(ProlongationCarriereQuebec2025(reclamer=True, naissance="1960-12-31",
        source="Naissance et emploi non lié fictifs vérifiés", **{nom: True for nom in CONFIRMATIONS_6D}), **kw)


@pytest.mark.parametrize("salaire,net,brut,reduction,credit", [
    ("0", "0", "0", "0", "0"), ("7500", "7500", "0", "0", "0"),
    ("7500.04", "7500", "0.01", "0", "0.01"), ("10000", "10000", "350", "0", "350"),
    ("20000", "20000", "1750", "0", "1750"), ("60000", "56500", "1750", "0", "1750"),
    ("60000", "60000", "1750", "245", "1505"), ("80000", "80000", "1750", "1645", "105"),
    ("81500", "81500", "1750", "1750", "0"), ("100000", "100000", "1750", "3045", "0")])
def test_parametres_officiels_2025(salaire, net, brut, reduction, credit):
    r = moteur(profil(), salaire=D(salaire), revenu_net=D(net), impot_401=D(5000), montant_359=D(18571))
    assert (r.credit_ligne_35, r.reduction_ligne_39, r.credit_ligne_391) == (D(brut), D(reduction), D(credit))


def test_plafond_impot_et_annexe_b():
    r = moteur(profil(), salaire=D(20000), revenu_net=D(20000), impot_401=D(3000), montant_359=D(18571))
    assert r.credit_ligne_391 == r.plafond_impot_ligne_49 == D("400.06")
    r = moteur(profil(), salaire=D(20000), revenu_net=D(20000), impot_401=D(3000), montant_359=D(18571), montant_361=D(3000))
    assert r.credit_ligne_391 == 0


@pytest.mark.parametrize("champ", list(CONFIRMATIONS_6D))
@pytest.mark.parametrize("v", [False, "oui", 1])
def test_confirmations_et_exclusions(champ, v):
    with pytest.raises(ValueError): moteur(profil(**{champ: v}))


@pytest.mark.parametrize("naissance", ["1961-01-01", "1965-12-31", "2025-01-01", "1960-02-30", "19601231", "", None])
def test_age_60_64_et_date_invalide_refuses(naissance):
    with pytest.raises(ValueError): moteur(profil(naissance=naissance))


@pytest.mark.parametrize("v", [D("NaN"), D("sNaN"), D("-1"), D("1.001"), D("1E9999"), True, "100", 1.5])
def test_montants_recalcules_stricts(v):
    with pytest.raises(ValueError): moteur(profil(), salaire=v)


def test_salaire_net_et_impot_depuis_dossier():
    d = _dossier_52000(); base = calcul(d)
    e = calcul(d, prolongation_carriere_quebec=profil())
    assert e.revenu == base.revenu and e.federal == base.federal
    r = e.resultat_carriere_quebec
    assert r.revenu_travail == D(52000) and r.revenu_net == D(50095)
    assert r.credit_ligne_391 == D(1750)
    assert base.quebec.impot_quebec_preliminaire - e.quebec.impot_quebec_preliminaire == D(1750)
    assert e.rapprochement.remboursement_estime - base.rapprochement.remboursement_estime == D(1750)


def test_reduction_selon_net_et_non_salaire():
    from tests.test_tax_federal_top_up_integration_2025 import dossier_70000
    e = calcul(dossier_70000(), prolongation_carriere_quebec=profil())
    assert e.resultat_carriere_quebec.revenu_net == D(67915)
    assert e.resultat_carriere_quebec.reduction_ligne_39 == D("799.05")
    assert e.resultat_carriere_quebec.credit_ligne_391 == D("950.95")


def test_credit391_alimente_plafond_achat396():
    from tests.test_tax_quebec_home_buyers_2025 import profil as achat
    base = calcul(_dossier_52000(), achat_habitation_quebec=achat())
    e = calcul(_dossier_52000(), achat_habitation_quebec=achat(), prolongation_carriere_quebec=profil())
    assert e.resultat_achat_quebec.autres_credits_ligne_28 == D(1750)
    assert base.resultat_achat_quebec.plafond_impot_ligne_30 - e.resultat_achat_quebec.plafond_impot_ligne_30 == D(1750)


def test_case211_et_age_pensions_contradictoires_refuses():
    d = _dossier_52000()
    d = replace(d, donnees_validees=d.donnees_validees+(_validee(Path("RL1.pdf"), "RL-1", "211", "1000"),))
    with pytest.raises(ValueError, match="211"): calcul(d, prolongation_carriere_quebec=profil())
    from tests.test_tax_pension_income_2025 import dossier_pensions, profil_pensions
    with pytest.raises(ValueError, match="Naissance 391"):
        calcul(dossier_pensions(), profil_pensions=profil_pensions(age=64), prolongation_carriere_quebec=profil())


def test_json_recalcul_ancien_et_divergence(tmp_path):
    d = _dossier_52000(); e = calcul(d, prolongation_carriere_quebec=profil())
    f = sauvegarder_dossier_fiscal(d, estimation=e, destination=tmp_path / "carriere_quebec.json")
    brut = json.loads(f.read_text(encoding="utf-8")); c = dossier_fiscal_depuis_contenu(brut)
    assert c.prolongation_carriere_quebec == profil()
    assert calcul(c.dossier, prolongation_carriere_quebec=c.prolongation_carriere_quebec).quebec == e.quebec
    with pytest.raises(ValueError, match="divergent"):
        sauvegarder_dossier_fiscal(d, estimation=e, prolongation_carriere_quebec=profil(naissance="1959-01-01"), destination=tmp_path / "refus.json")
    brut.pop("prolongation_carriere_quebec")
    assert dossier_fiscal_depuis_contenu(brut).prolongation_carriere_quebec == ProlongationCarriereQuebec2025()


@pytest.mark.parametrize("champ,valeur", [("naissance", 1960), ("valide_par_comptable", "oui"),
    ("source", 1), ("credit_derive", "1750"), ("reclamer", 1)])
def test_json_types_et_cles_stricts(champ, valeur):
    brut = carriere_quebec_vers_dict(profil()); brut[champ] = valeur
    with pytest.raises(ValueError): carriere_quebec_depuis_dict(brut)


def test_vide_historique_et_65_sans_travail():
    p = ProlongationCarriereQuebec2025()
    assert moteur(p).credit_ligne_391 == moteur(profil()).credit_ligne_391 == 0
    assert carriere_quebec_depuis_dict(None) == carriere_quebec_depuis_dict({}) == p
    assert calcul(_dossier_52000(), prolongation_carriere_quebec=p) == calcul(_dossier_52000())


def test_trace_resume_et_pdf(tmp_path):
    e = calcul(_dossier_52000(), prolongation_carriere_quebec=profil())
    trace = str(construire_trace_calcul_fiscal_2025(e))
    assert "1750" in trace and "391" in trace and "56500" in trace
    assert "TP-752.PC / LIGNE 391" in formater_estimation_fiscale_2025(e)
    f = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "carriere_quebec_6d.pdf")
    with fitz.open(f) as pdf:
        texte = "\n".join(p.get_text() for p in pdf)
        for p in pdf:
            assert all(0 <= b[0] < b[2] <= p.rect.width and 0 <= b[1] < b[3] <= p.rect.height for b in p.get_text("blocks"))
    for attendu in ("TP-752.PC / LIGNE 391", "1750.00", "50095.00", "1960-12-31", "validation comptable"):
        assert attendu in texte
