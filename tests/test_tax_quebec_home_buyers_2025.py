from dataclasses import replace
from decimal import Decimal as D
import json
import fitz
import pytest
from src.comptaprivee.tax_quebec_home_buyers_2025 import (
    AchatHabitationQuebec2025, CONFIRMATIONS_6C, calculer_achat_quebec_2025 as moteur,
    achat_quebec_vers_dict, achat_quebec_depuis_dict)
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calcul, formater_estimation_fiscale_2025
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, dossier_fiscal_depuis_contenu
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from tests.test_tax_estimation_2025 import _dossier_52000


def profil(**kw):
    return replace(AchatHabitationQuebec2025(reclamer=True, date_acquisition="2025-06-15",
        reference_habitation="Habitation fictive QC, lot A", credit_demande_autres=D(400),
        source="Acte et entente fictifs vérifiés", **{nom: True for nom in CONFIRMATIONS_6C}), **kw)


@pytest.mark.parametrize("impot,autres,attendu", [("5000", "0", "1400"), ("5000", "400", "1000"),
    ("5000", "1400", "0"), ("3000", "0", "400.06"), ("2599.94", "0", "0"), ("0", "0", "0")])
def test_plafond_impot_et_partage_officiels(impot, autres, attendu):
    r = moteur(profil(credit_demande_autres=D(autres)), impot_401=D(impot), montant_359=D(18571))
    assert r.credit_ligne_27 == D("2599.94")
    assert r.disponible_ligne_37 == D(1400)-D(autres)
    assert r.credit_ligne_396 == D(attendu)


def test_partie51_tient_compte_361_367_391_397():
    r = moteur(profil(), impot_401=D(4000), montant_359=D(18571), montant_361=D(2000),
        montant_367=D(1000), credit_391=D(200), credit_397=D(300))
    assert r.base_ligne_26 == D(21571)
    assert r.credit_ligne_27 == D("3019.94")
    assert r.plafond_impot_ligne_30 == r.credit_ligne_396 == D("480.06")


@pytest.mark.parametrize("champ", list(CONFIRMATIONS_6C))
@pytest.mark.parametrize("v", [False, "oui", 1])
def test_confirmations_obligatoires_et_strictes(champ, v):
    with pytest.raises(ValueError): moteur(profil(**{champ: v}))


@pytest.mark.parametrize("kw", [
    {"credit_demande_autres": D("1400.01")}, {"credit_demande_autres": D("-1")},
    {"credit_demande_autres": D("1.001")}, {"credit_demande_autres": D("NaN")},
    {"credit_demande_autres": D("1E9999")}, {"credit_demande_autres": 2.0},
    {"reclamer": "oui"}, {"reclamer": False}, {"date_acquisition": "2024-12-31"},
    {"date_acquisition": "2026-01-01"}, {"date_acquisition": "2025-02-29"},
    {"date_acquisition": "20250615"}, {"date_acquisition": 2025},
    {"reference_habitation": ""}, {"source": " "}, {"source": None}])
def test_profil_invalide(kw):
    with pytest.raises(ValueError): moteur(profil(**kw))


def test_cumul_federal_independant_et_rapprochement():
    from tests.test_tax_home_buyers_sharing_2025 import profil as federal
    d = _dossier_52000()
    base = calcul(d, achat_habitation_federal=federal())
    e = calcul(d, achat_habitation_federal=federal(), achat_habitation_quebec=profil())
    assert e.revenu == base.revenu and e.federal == base.federal
    assert e.resultat_achat_quebec.credit_ligne_396 == D(1000)
    assert base.quebec.impot_quebec_preliminaire - e.quebec.impot_quebec_preliminaire == D(1000)
    assert e.rapprochement.remboursement_estime - base.rapprochement.remboursement_estime == D(1000)


def test_plafond_distinct_du_solde_apres_medical():
    from tests.test_tax_medical_expenses_integration_2025 import _frais_3000
    frais = replace(_frais_3000(), montant_admissible_quebec=D(30000))
    base = calcul(_dossier_52000(), frais_medicaux=frais)
    e = calcul(_dossier_52000(), frais_medicaux=frais, achat_habitation_quebec=profil())
    assert base.quebec.impot_quebec_preliminaire == e.quebec.impot_quebec_preliminaire == 0
    assert e.resultat_achat_quebec.credit_ligne_396 == D(1000)
    assert e.resultat_achat_quebec.plafond_impot_ligne_30 > D(1000)
    assert e.rapprochement == base.rapprochement


def test_annexe_b_combinee_incluse_dans_plafond():
    from tests.test_tax_quebec_schedule_b_2025 import profils
    s, a = profils(); a = replace(a, reclamer_revenus_retraite=False, revenu_ligne_122=D(0))
    e = calcul(_dossier_52000(), personne_vivant_seule=s, montants_age_retraite=a, achat_habitation_quebec=profil())
    assert e.resultat_achat_quebec.base_ligne_26 == D(18571) + D("4533.06")
    assert e.resultat_achat_quebec.credit_ligne_27 == D("3234.57")


def test_redressement_358_et_cotisations_397_dans_plafond():
    from tests.test_tax_replacement_benefits_2025 import dossier_remplacement, profil_remplacement
    from tests.test_tax_union_dues_integration_2025 import _cotisations_600
    e = calcul(dossier_remplacement(emploi=True), profil_remplacement=profil_remplacement(),
        cotisations_syndicales=_cotisations_600(), achat_habitation_quebec=profil())
    r = e.resultat_achat_quebec
    assert r.base_ligne_26 == D(16571)
    assert r.credit_ligne_27 == D("2319.94") and r.autres_credits_ligne_28 == D(60)
    assert r.plafond_impot_ligne_30 == e.quebec.impot_brut - D("2379.94")


def test_partage_deux_dossiers_respecte_plafond_commun():
    a = moteur(profil(credit_demande_autres=D(400)), impot_401=D(5000), montant_359=D(18571))
    b = moteur(profil(credit_demande_autres=a.credit_ligne_396), impot_401=D(5000), montant_359=D(18571))
    assert a.credit_ligne_396 + b.credit_ligne_396 == D(1400)


def test_json_recalcul_ancien_et_divergence(tmp_path):
    d = _dossier_52000(); e = calcul(d, achat_habitation_quebec=profil())
    f = sauvegarder_dossier_fiscal(d, estimation=e, destination=tmp_path / "achat_quebec.json")
    brut = json.loads(f.read_text(encoding="utf-8"))
    c = dossier_fiscal_depuis_contenu(brut)
    assert c.achat_habitation_quebec == profil()
    assert calcul(c.dossier, achat_habitation_quebec=c.achat_habitation_quebec).quebec == e.quebec
    with pytest.raises(ValueError, match="divergent"):
        sauvegarder_dossier_fiscal(d, estimation=e, achat_habitation_quebec=profil(credit_demande_autres=D(0)), destination=tmp_path / "refus.json")
    brut.pop("achat_habitation_quebec")
    assert dossier_fiscal_depuis_contenu(brut).achat_habitation_quebec == AchatHabitationQuebec2025()


@pytest.mark.parametrize("champ,valeur", [("credit_demande_autres", 1.5), ("credit_demande_autres", True),
    ("credit_demande_autres", "NaN"), ("valide_par_comptable", "oui"), ("source", 1), ("credit_derive", "1400")])
def test_json_types_et_cles_stricts(champ, valeur):
    brut = achat_quebec_vers_dict(profil()); brut[champ] = valeur
    with pytest.raises(ValueError): achat_quebec_depuis_dict(brut)


def test_vide_historique():
    p = AchatHabitationQuebec2025()
    assert moteur(p).credit_ligne_396 == 0
    assert achat_quebec_depuis_dict(None) == achat_quebec_depuis_dict({}) == p
    assert calcul(_dossier_52000(), achat_habitation_quebec=p) == calcul(_dossier_52000())


def test_trace_resume_et_pdf(tmp_path):
    e = calcul(_dossier_52000(), achat_habitation_quebec=profil())
    trace = str(construire_trace_calcul_fiscal_2025(e))
    assert "1000" in trace and "396" in trace and "plafond fiscal" in trace
    assert "TP-752.HA / LIGNE 396" in formater_estimation_fiscale_2025(e)
    f = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "achat_quebec_6c.pdf")
    with fitz.open(f) as pdf:
        texte = "\n".join(p.get_text() for p in pdf)
        for p in pdf:
            assert all(0 <= b[0] < b[2] <= p.rect.width and 0 <= b[1] < b[3] <= p.rect.height for b in p.get_text("blocks"))
    for attendu in ("TP-752.HA / LIGNE 396", "1000.00", "400.00", "2025-06-15", "Habitation fictive", "validation comptable"):
        assert attendu in texte
