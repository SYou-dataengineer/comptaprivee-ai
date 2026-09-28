from dataclasses import replace
from decimal import Decimal as D
import json
import fitz
import pytest
from src.comptaprivee.tax_workers_benefit_2025 import (
    AllocationTravailleurs2025, CONFIRMATIONS_ACT, calculer_allocation_travailleurs_2025,
    valider_allocation_travailleurs_2025,
)
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calcul
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_top_up_integration_2025 import verifier_t1


def profil(**kw):
    v = dict(reclamer_base=True, age_fin_2025=35, source="Validation ACT et RC210 fictifs",
             **{nom: True for nom in CONFIRMATIONS_ACT})
    v.update(kw)
    return AllocationTravailleurs2025(**v)


def montant(p=None, travail="20000", net="14170.05"):
    return calculer_allocation_travailleurs_2025(p or profil(), revenu_travail=D(travail), revenu_net=D(net))


def dossier_20000():
    d = _dossier_52000()
    valeurs = {"14": "20000", "17": "1056", "18": "262", "24": "20000", "26": "20000", "55": "98.80", "56": "20000",
               "A": "20000", "B.A": "1056", "C": "262", "G": "20000", "H": "98.80", "I": "20000"}
    return replace(d, donnees_validees=tuple(replace(x, valeur_validee=D(valeurs[x.case]), valeur_extraite=D(valeurs[x.case]))
        if x.case in valeurs else x for x in d.donnees_validees))


def test_vide_et_choix_zero():
    assert montant(AllocationTravailleurs2025()).ligne_45300 == 0
    assert montant(profil(reclamer_base=False, avances_rc210_case10=D(500))).ligne_41500 == 0


@pytest.mark.parametrize("travail,net,attendu", [
    ("2400", "2400", "0"), ("2400.02", "2400.02", ".01"),
    ("12400", "12400", "3730"), ("20000", "14170.05", "3812.06"),
    ("20000", "15170.05", "3612.06"), ("40000", "33230.35", "0"),
    ("40000", "33230.30", ".01"), ("40000", "40000", "0"),
])
def test_base_annexe6_quebec(travail, net, attendu):
    assert montant(travail=travail, net=net).ligne_45300 == D(attendu)


@pytest.mark.parametrize("travail,net,attendu", [
    ("1200", "1200", "0"), ("1200.02", "1200.02", ".01"),
    ("2200", "2200", "400"), ("4000", "33230.35", "851.31"),
    ("40000", "34230.35", "651.31"), ("40000", "37486.90", "0"),
    ("40000", "37486.85", ".01"),
])
def test_supplement_annexe6_quebec(travail, net, attendu):
    p = profil(reclamer_base=False, reclamer_supplement=True, admissibilite_ciph_confirmee=True)
    assert montant(p, travail, net).ligne_45300 == D(attendu)


def test_cumul_et_rc210_plafonne():
    p = profil(reclamer_supplement=True, admissibilite_ciph_confirmee=True,
               avances_rc210_case10=D(1000), avances_rc210_case11=D(400))
    r = montant(p)
    assert r.ligne_45300 == D("4663.37")
    assert r.ligne_41500 == D(1400)
    assert montant(replace(p, avances_rc210_case10=D(9000))).ligne_41500 == r.ligne_45300


@pytest.mark.parametrize("nom", list(CONFIRMATIONS_ACT))
def test_confirmations(nom):
    for v in (False, "true"):
        with pytest.raises(ValueError):
            montant(profil(**{nom: v}))


@pytest.mark.parametrize("champ", ["avances_rc210_case10", "avances_rc210_case11"])
@pytest.mark.parametrize("valeur", [D(-1), D("NaN"), D("sNaN"), D("Infinity"), D("-Infinity"), D("1.001"), 1.5, "5"])
def test_avances_invalides(champ, valeur):
    with pytest.raises(ValueError):
        montant(profil(**{champ: valeur}))


@pytest.mark.parametrize("champ", ["revenu_travail", "revenu_net"])
@pytest.mark.parametrize("valeur", [D(-1), D("NaN"), D("sNaN"), D("Infinity"), D("-Infinity"), 1.5, "5"])
def test_revenus_invalides(champ, valeur):
    v = dict(revenu_travail=D(20000), revenu_net=D(20000))
    v[champ] = valeur
    with pytest.raises(ValueError):
        calculer_allocation_travailleurs_2025(profil(), **v)


@pytest.mark.parametrize("age", [18, -1, 121, True, "35"])
def test_age_invalide(age):
    with pytest.raises(ValueError):
        montant(profil(age_fin_2025=age))


def test_age_19_et_source_ciph_types():
    assert montant(profil(age_fin_2025=19)).ligne_45300 == D("3812.06")
    for kw in ({"source": ""}, {"source": None}, {"reclamer_base": 1}, {"reclamer_supplement": True}, {"admissibilite_ciph_confirmee": 1}):
        with pytest.raises(ValueError):
            montant(profil(**kw))


def test_estimation_avances_hors_abattement_et_credit_unique():
    d = dossier_20000()
    avant = calcul(d)
    e = calcul(d, allocation_travailleurs=profil(avances_rc210_case10=D(1000)))
    assert e.revenu == avant.revenu
    assert e.federal == avant.federal
    assert e.quebec == avant.quebec
    r = e.resultat_allocation_travailleurs
    assert r.revenu_travail == D(20000)
    assert r.revenu_net_ajuste == D(19835)
    assert r.ligne_45300 == D("2679.07")
    assert r.ligne_41500 == D(1000)
    assert e.rapprochement.abattement_quebec == avant.rapprochement.abattement_quebec
    assert e.rapprochement.impot_total_preliminaire - avant.rapprochement.impot_total_preliminaire == D(1000)
    net = lambda x: x.rapprochement.remboursement_estime - x.rapprochement.solde_estime
    assert net(e) - net(avant) == D("1679.07")
    verifier_t1(e)


def test_emploi_brut_non_diminue_par_deductions():
    from tests.test_tax_training_credit_2025 import frais as formation
    from tests.test_tax_medical_supplement_2025 import frais as medical
    # 1500 bruts - 750 CCF = 750 utilisables sans report à ce revenu.
    scolarite = replace(formation(frais_canadiens=D(1500)),
                        montant_admissible_federal=D(1500), montant_admissible_quebec=D(1500))
    # 25000 laisse aussi assez d'impôt Québec pour utiliser les frais nets.
    d = dossier_20000()
    valeurs = {"14": "25000", "17": "1376", "18": "327.50", "24": "25000", "26": "25000", "55": "123.50", "56": "25000",
               "A": "25000", "B.A": "1376", "C": "327.50", "G": "25000", "H": "123.50", "I": "25000"}
    d = replace(d, donnees_validees=tuple(replace(x, valeur_validee=D(valeurs[x.case]), valeur_extraite=D(valeurs[x.case]))
        if x.case in valeurs else x for x in d.donnees_validees))
    e = calcul(d, allocation_travailleurs=profil(), frais_scolarite=scolarite, frais_medicaux=medical())
    r = e.rapprochement
    assert e.resultat_allocation_travailleurs.revenu_travail == D(25000)
    assert r.credit_formation_ligne_45350 == D(750)
    assert r.supplement_medical_ligne_45200 == D(1504)
    assert r.remboursement_estime - r.solde_estime == (r.retenues_totales + r.remboursements_cotisations_totaux
        + D(750) + D(1504) + r.allocation_travailleurs_ligne_45300 - r.impot_total_preliminaire)


def test_famille_refusee():
    from tests.test_tax_federal_spouse_2025 import _profil
    net = calcul(dossier_20000()).revenu.revenu_net_federal
    with pytest.raises(ValueError, match="combinaison familiale"):
        calcul(dossier_20000(), allocation_travailleurs=profil(),
               montant_conjoint_federal=_profil(revenu_net_contribuable_ligne_23600=net))


def test_stockage_ancien_et_divergence(tmp_path):
    e = calcul(dossier_20000(), allocation_travailleurs=profil(avances_rc210_case10=D(1000)))
    f = sauvegarder_dossier_fiscal(e.dossier, estimation=e, destination=tmp_path / "cas.json")
    c = charger_dossier_fiscal(f)
    assert c.allocation_travailleurs == e.allocation_travailleurs
    assert calcul(c.dossier, allocation_travailleurs=c.allocation_travailleurs) == e
    brut = json.loads(f.read_text(encoding="utf-8"))
    assert brut["allocation_travailleurs"]["avances_rc210_case10"] == "1000.00"
    assert "ligne_45300" not in brut["allocation_travailleurs"]
    with pytest.raises(ValueError, match="diffère"):
        sauvegarder_dossier_fiscal(e.dossier, estimation=e, allocation_travailleurs=AllocationTravailleurs2025(), destination=tmp_path / "refus.json")
    del brut["allocation_travailleurs"]
    f.write_text(json.dumps(brut), encoding="utf-8")
    assert charger_dossier_fiscal(f).allocation_travailleurs == AllocationTravailleurs2025()


@pytest.mark.parametrize("valeur", [{"inconnu": True}, {"reclamer_base": "true"}, {"age_fin_2025": "35"}, [], {"source": None}, {"avances_rc210_case10": "NaN"}])
def test_json_invalide(tmp_path, valeur):
    f = sauvegarder_dossier_fiscal(dossier_20000(), destination=tmp_path / "cas.json")
    brut = json.loads(f.read_text(encoding="utf-8"))
    brut["allocation_travailleurs"] = valeur
    f.write_text(json.dumps(brut), encoding="utf-8")
    with pytest.raises(ValueError):
        charger_dossier_fiscal(f)


def test_trace_pdf(tmp_path):
    e = calcul(dossier_20000(), allocation_travailleurs=profil(avances_rc210_case10=D(1000)))
    trace = construire_trace_calcul_fiscal_2025(e)
    ligne = next(x for x in trace.lignes if x.libelle == "ACT remboursable 45300")
    assert ligne.montant == D("2679.07")
    assert "45300" in trace.formule_resultat and "41500" in trace.formule_resultat
    assert [x.ordre for x in trace.lignes] == list(range(1, len(trace.lignes) + 1))
    f = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "act.pdf")
    with fitz.open(f) as pdf:
        texte = "\n".join(page.get_text() for page in pdf)
        for page in pdf:
            for x0, y0, x1, y1, *_ in page.get_text("blocks"):
                assert 0 <= x0 < x1 <= page.rect.width
                assert 0 <= y0 < y1 <= page.rect.height
    assert "Ligne 45300 remboursable : 2679.07" in texte
    assert "Ligne 41500 : min(45300, avances RC210) = 1000.00" in texte


def test_act_positive_avec_credit_etranger():
    from tests.test_tax_foreign_investment_2025 import dossier, profil as etranger, profil_credit
    emploi = dossier_20000()
    placement = dossier("1000", "150")
    d = replace(emploi, documents=emploi.documents + placement.documents,
                donnees_validees=emploi.donnees_validees + placement.donnees_validees)
    options = dict(profil_placement_etranger=etranger(), profil_credit_impot_etranger=profil_credit("100", "0"))
    avant = calcul(d, **options)
    e = calcul(d, allocation_travailleurs=profil(avances_rc210_case10=D(500)), **options)
    assert e.resultat_allocation_travailleurs.ligne_45300 > 0
    assert e.federal == avant.federal
    assert e.rapprochement.abattement_quebec == avant.rapprochement.abattement_quebec
    verifier_t1(e)
