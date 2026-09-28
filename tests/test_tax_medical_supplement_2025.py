from dataclasses import replace
from decimal import Decimal as D
import json
import fitz
import pytest
from src.comptaprivee.tax_medical_supplement_2025 import (
    SupplementMedical2025, CONFIRMATIONS_SUPPLEMENT, calculer_supplement_medical_2025,
    valider_supplement_medical_2025,
)
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calcul
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_top_up_integration_2025 import medical, verifier_t1


def profil(**kw):
    v = dict(reclamer=True, age_fin_2025=35, source="Validation dossier médical fictif",
             **{nom: True for nom in CONFIRMATIONS_SUPPLEMENT})
    v.update(kw)
    return SupplementMedical2025(**v)


def montant(p=None, **kw):
    valeurs = dict(emploi=D(4390), deduction_20700=D(0), deduction_21200=D(0),
                   deduction_22900=D(0), revenu_net=D(33294), ligne_33200=D(10000))
    valeurs.update(kw)
    return calculer_supplement_medical_2025(p or profil(), **valeurs)


def frais():
    return replace(medical("10000"), supplement=profil())


def test_vide():
    assert montant(SupplementMedical2025()).ligne_45200 == 0


@pytest.mark.parametrize("travail,net,base,attendu", [
    ("4389.99", "33294", "10000", "0"),
    ("4390", "33294", "10000", "1504"),
    ("4390", "33294", "6016", "1504"),
    ("4390", "33294", "4000", "1000"),
    ("4390", "33294", "0", "0"),
    ("4390", "34294", "10000", "1454"),
    ("4390", "63374", "10000", "0"),
    ("4390", "63373.80", "10000", ".01"),
    ("4390", "33294", "1000.02", "250.01"),
])
def test_bornes_feuille_2025(travail, net, base, attendu):
    assert montant(emploi=D(travail), revenu_net=D(net), ligne_33200=D(base)).ligne_45200 == D(attendu)


def test_deductions_revenu_travail_et_plancher():
    r = montant(emploi=D(5000), deduction_20700=D(500), deduction_21200=D(100), deduction_22900=D(10))
    assert r.revenu_travail == D(4390)
    assert r.ligne_45200 == D(1504)
    assert montant(emploi=D(5000), deduction_20700=D(5001)).revenu_travail == 0
    assert montant(emploi=D(5000), deduction_22900=D("610.01")).ligne_45200 == 0


@pytest.mark.parametrize("champ", ["emploi", "deduction_20700", "deduction_21200", "deduction_22900", "revenu_net", "ligne_33200"])
@pytest.mark.parametrize("valeur", [D(-1), D("NaN"), D("sNaN"), D("Infinity"), D("-Infinity"), 1.5, "3"])
def test_montants_invalides(champ, valeur):
    with pytest.raises(ValueError):
        montant(**{champ: valeur})


@pytest.mark.parametrize("nom", list(CONFIRMATIONS_SUPPLEMENT))
def test_confirmations_obligatoires(nom):
    for valeur in (False, "true"):
        with pytest.raises(ValueError):
            valider_supplement_medical_2025(profil(**{nom: valeur}))


@pytest.mark.parametrize("age", [17, -1, 121, True, "35"])
def test_age_invalide(age):
    with pytest.raises(ValueError):
        montant(profil(age_fin_2025=age))


def test_age_18_source_et_type():
    assert montant(profil(age_fin_2025=18)).ligne_45200 == D(1504)
    for kw in ({"source": ""}, {"source": None}, {"reclamer": 1}):
        with pytest.raises(ValueError):
            montant(profil(**kw))


def test_estimation_credit_unique_et_impots_inchanges():
    avant = calcul(_dossier_52000(), frais_medicaux=medical("10000"))
    e = calcul(_dossier_52000(), frais_medicaux=frais())
    assert e.revenu == avant.revenu
    assert e.federal == avant.federal
    assert e.quebec == avant.quebec
    r = e.resultat_supplement_medical
    assert r.revenu_travail == D(52000)
    assert r.ligne_33200 == dict(e.federal.credits_federaux_complets.montants_par_ligne)["33200"]
    assert r.ligne_45200 > 0
    assert e.rapprochement.supplement_medical_ligne_45200 == r.ligne_45200
    assert e.rapprochement.impot_total_preliminaire == avant.rapprochement.impot_total_preliminaire
    net = lambda x: x.rapprochement.remboursement_estime - x.rapprochement.solde_estime
    assert net(e) - net(avant) == r.ligne_45200
    verifier_t1(e)


def test_cumul_formation_et_supplement():
    from tests.test_tax_training_credit_2025 import frais as formation
    e = calcul(_dossier_52000(), frais_medicaux=frais(), frais_scolarite=formation())
    r = e.rapprochement
    assert r.credit_formation_ligne_45350 == D(750)
    assert r.supplement_medical_ligne_45200 > 0
    assert r.remboursement_estime - r.solde_estime == (r.retenues_totales + r.remboursements_cotisations_totaux
        + D(750) + r.supplement_medical_ligne_45200 - r.impot_total_preliminaire)


def test_stockage_ancien_et_divergence(tmp_path):
    e = calcul(_dossier_52000(), frais_medicaux=frais())
    f = sauvegarder_dossier_fiscal(e.dossier, estimation=e, destination=tmp_path / "cas.json")
    c = charger_dossier_fiscal(f)
    assert c.frais_medicaux == e.frais_medicaux
    assert calcul(c.dossier, frais_medicaux=c.frais_medicaux) == e
    brut = json.loads(f.read_text(encoding="utf-8"))
    assert brut["frais_medicaux"]["supplement"]["reclamer"] is True
    assert "ligne_45200" not in brut["frais_medicaux"]["supplement"]
    with pytest.raises(ValueError, match="diffère"):
        sauvegarder_dossier_fiscal(e.dossier, estimation=e, frais_medicaux=medical("10000"), destination=tmp_path / "refus.json")
    del brut["frais_medicaux"]["supplement"]
    f.write_text(json.dumps(brut), encoding="utf-8")
    assert charger_dossier_fiscal(f).frais_medicaux.supplement == SupplementMedical2025()


@pytest.mark.parametrize("valeur", [{"inconnu": True}, {"reclamer": "true"}, {"age_fin_2025": "35"}, [], {"source": None}])
def test_json_invalide(tmp_path, valeur):
    f = sauvegarder_dossier_fiscal(_dossier_52000(), destination=tmp_path / "cas.json")
    brut = json.loads(f.read_text(encoding="utf-8"))
    brut["frais_medicaux"]["supplement"] = valeur
    f.write_text(json.dumps(brut), encoding="utf-8")
    with pytest.raises(ValueError):
        charger_dossier_fiscal(f)


def test_trace_pdf(tmp_path):
    e = calcul(_dossier_52000(), frais_medicaux=frais())
    trace = construire_trace_calcul_fiscal_2025(e)
    ligne = next(x for x in trace.lignes if x.libelle == "Supplément médical remboursable 45200")
    assert ligne.montant == e.resultat_supplement_medical.ligne_45200
    assert "45200" in trace.formule_resultat
    assert [x.ordre for x in trace.lignes] == list(range(1, len(trace.lignes) + 1))
    f = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "medical.pdf")
    with fitz.open(f) as pdf:
        texte = "\n".join(page.get_text() for page in pdf)
        for page in pdf:
            for x0, y0, x1, y1, *_ in page.get_text("blocks"):
                assert 0 <= x0 < x1 <= page.rect.width
                assert 0 <= y0 < y1 <= page.rect.height
    assert f"Ligne 45200 remboursable : {ligne.montant:.2f}" in texte
    assert "Validation dossier médical fictif" in texte


def test_combinaison_familiale_refusee():
    from tests.test_tax_federal_spouse_2025 import _profil
    net = calcul(_dossier_52000()).revenu.revenu_net_federal
    with pytest.raises(ValueError, match="combinaison familiale"):
        calcul(_dossier_52000(), frais_medicaux=frais(),
               montant_conjoint_federal=_profil(revenu_net_contribuable_ligne_23600=net))


def test_supplement_et_credit_etranger_40500():
    from tests.test_tax_foreign_investment_2025 import dossier, profil as etranger, profil_credit
    d = dossier("1000", "150", emploi=True)
    options = dict(profil_placement_etranger=etranger(), profil_credit_impot_etranger=profil_credit("100", "0"))
    avant = calcul(d, frais_medicaux=medical("10000"), **options)
    apres = calcul(d, frais_medicaux=frais(), **options)
    assert apres.federal == avant.federal
    assert apres.rapprochement.abattement_quebec == avant.rapprochement.abattement_quebec
    verifier_t1(apres)
