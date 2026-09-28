from dataclasses import replace
from decimal import Decimal as D
import json
import fitz
import pytest

from tests.test_tax_family_medical_2025 import profil, personne, depense
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_top_up_integration_2025 import verifier_t1, dossier_70000
from tests.test_tax_medical_expenses_integration_2025 import _frais_3000
from src.comptaprivee.tax_family_medical_2025 import (
    FraisMedicauxFamilleFederaux2025, medical_familial_vers_dict, medical_familial_depuis_dict,
)
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calculer
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal, dossier_fiscal_depuis_contenu
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025


def famille(**kw):
    return profil(demandeur="Client Test", **kw)


def test_estimation_une_inclusion_pas_effet_revenus_quebec():
    d = _dossier_52000()
    e0 = calculer(d)
    e = calculer(d, frais_medicaux_famille=famille())
    verifier_t1(e)
    c = e.federal.credits_federaux_complets
    assert dict(c.montants_par_ligne)["33200"] == D(1400)
    assert c.credit_ligne_33800 - e0.federal.credits_federaux_complets.credit_ligne_33800 == D(203)
    assert e.revenu == e0.revenu and e.quebec == e0.quebec


def test_grands_frais_et_compensatoire():
    e = calculer(dossier_70000(), frais_medicaux_famille=famille(depenses=(depense(montant_paye=D(60000)),)))
    verifier_t1(e)
    assert e.federal.credits_federaux_complets.credit_compensatoire_ligne_34990 > 0


def test_refus_cumul_profil_individuel():
    with pytest.raises(ValueError, match="cumulés"):
        calculer(_dossier_52000(), frais_medicaux=_frais_3000(), frais_medicaux_famille=famille())


def test_refus_quebec_individuel_avec_famille():
    frais = replace(_frais_3000(), montant_admissible_federal=D(0))
    with pytest.raises(ValueError, match="Québec"):
        calculer(_dossier_52000(), frais_medicaux=frais, frais_medicaux_famille=famille())


def test_deux_dependants_seuils_separes_sans_compensation():
    p = famille(personnes=(personne(), personne(reference="autre", nom="Autre parent", revenu_net_23600=D(100000))),
        depenses=(depense(), depense(reference="B", personne="autre", montant_paye=D(100))))
    e = calculer(_dossier_52000(), frais_medicaux_famille=p)
    assert e.resultat_medical_familial.ligne_33199 == D(1400)
    assert e.resultat_medical_familial.personnes[1].montant_admissible == 0


def test_stockage_recalcul_divergence_ancien_json(tmp_path):
    e = calculer(_dossier_52000(), frais_medicaux_famille=famille())
    f = sauvegarder_dossier_fiscal(e.dossier, estimation=e, destination=tmp_path / "medical.json")
    c = charger_dossier_fiscal(f)
    assert c.frais_medicaux_famille == famille()
    assert calculer(c.dossier, frais_medicaux_famille=c.frais_medicaux_famille).resultat_medical_familial == e.resultat_medical_familial
    with pytest.raises(ValueError, match="divergent"):
        sauvegarder_dossier_fiscal(e.dossier, estimation=e, frais_medicaux_famille=FraisMedicauxFamilleFederaux2025(), destination=f)
    brut = json.loads(f.read_text(encoding="utf-8"))
    assert "ligne_33199" not in json.dumps(brut["frais_medicaux_famille"])
    del brut["frais_medicaux_famille"]
    assert dossier_fiscal_depuis_contenu(brut).frais_medicaux_famille == FraisMedicauxFamilleFederaux2025()


@pytest.mark.parametrize("montant", ["NaN", "Infinity", "-1", "0.001", True, 2.5, None])
def test_json_montant_invalide(montant):
    brut = medical_familial_vers_dict(famille())
    brut["depenses"][0]["montant_paye"] = montant
    with pytest.raises(ValueError):
        medical_familial_depuis_dict(brut)


@pytest.mark.parametrize("niveau", ["profil", "personne", "depense"])
def test_json_cles_inconnues(niveau):
    brut = medical_familial_vers_dict(famille())
    cible = brut if niveau == "profil" else brut["personnes" if niveau == "personne" else "depenses"][0]
    cible["inconnue"] = True
    with pytest.raises(ValueError):
        medical_familial_depuis_dict(brut)


def test_trace_et_pdf(tmp_path):
    e = calculer(_dossier_52000(), frais_medicaux_famille=famille())
    t = construire_trace_calcul_fiscal_2025(e)
    medical = next(l for l in t.lignes if l.libelle == "Frais médicaux familiaux — 33200")
    base = next(l for l in t.lignes if l.libelle == "Base ligne 33500")
    assert medical.montant == 1400 and medical.ordre < base.ordre
    f = exporter_rapport_fiscal_pdf_2025(e, destination=tmp_path / "medical_famille.pdf")
    with fitz.open(f) as d:
        texte = "".join(p.get_text() for p in d)
    assert "Parent synthétique" in texte and "33199" in texte
    assert "1400.00" in texte and "Reçu synthétique" in texte
