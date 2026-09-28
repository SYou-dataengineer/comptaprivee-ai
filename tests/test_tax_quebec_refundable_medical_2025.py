from dataclasses import replace
from decimal import Decimal as D
import json
import fitz
import pytest
from src.comptaprivee.tax_quebec_refundable_medical_2025 import (
    MedicalRemboursableQuebec2025, CONFIRMATIONS_6E, calculer_medical_remboursable_quebec_2025 as moteur,
    medical_remboursable_quebec_vers_dict, medical_remboursable_quebec_depuis_dict)
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calcul, formater_estimation_fiscale_2025
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, dossier_fiscal_depuis_contenu
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from tests.test_tax_estimation_2025 import _dossier_52000, _validee
from tests.test_tax_medical_expenses_integration_2025 import _frais_3000
from tests.test_tax_disability_transfer_2025 import transfert


def profil(**kw):
    return replace(MedicalRemboursableQuebec2025(reclamer=True, naissance="1990-12-31",
        source="Naissance, revenus et pièces médicales fictifs", **{nom: True for nom in CONFIRMATIONS_6E}), **kw)


def frais():
    return replace(_frais_3000(), montant_admissible_federal=D(10000), montant_admissible_quebec=D(10000))


@pytest.mark.parametrize("travail,net,base,credit", [
    ("0", "0", "10000", "0"), ("3749.99", "0", "10000", "0"),
    ("3750", "0", "10000", "1466"), ("3750", "28335", "5864", "1466"),
    ("3750", "28335", "1000.02", "250.01"), ("40000", "29335", "10000", "1416"),
    ("40000", "30000", "4000", "916.75"), ("60000", "57654.80", "10000", ".01"),
    ("60000", "57655", "10000", "0"), ("100000", "100000", "10000", "0"),
    ("10000", "0", "0", "0")])
def test_annexe_b_2025(travail, net, base, credit):
    assert moteur(profil(), salaire=D(travail), revenu_net=D(net), base_381=D(base)).credit_ligne_462 == D(credit)


def test_grille_travail_deductions_et_ancien_emploi():
    r = moteur(profil(), salaire=D(5000), deduction_205=D(500), deduction_207=D(250), avantages_211=D(500), base_381=D(10000))
    assert r.revenu_travail == D(3750) and r.credit_ligne_462 == D(1466)
    assert moteur(profil(), salaire=D(5000), deduction_207=D("1250.01"), base_381=D(10000)).credit_ligne_462 == 0
    assert moteur(profil(), salaire=D(1000), deduction_205=D(1500)).revenu_travail == 0
    with pytest.raises(ValueError, match="211"):
        moteur(profil(), salaire=D(1000), avantages_211=D(1001))


@pytest.mark.parametrize("champ", list(CONFIRMATIONS_6E))
@pytest.mark.parametrize("valeur", [False, "oui", 1])
def test_confirmations(champ, valeur):
    with pytest.raises(ValueError): moteur(profil(**{champ: valeur}))


@pytest.mark.parametrize("naissance", ["2008-01-01", "2025-12-31", "1990-02-30", "19901231", "", None])
def test_date_et_moins18(naissance):
    with pytest.raises(ValueError): moteur(profil(naissance=naissance))


def test_18_ans_et_profil_vide():
    assert moteur(profil(naissance="2007-12-31"), salaire=D(3750), base_381=D(10000)).credit_ligne_462 == D(1466)
    p = MedicalRemboursableQuebec2025()
    assert moteur(p).credit_ligne_462 == 0
    assert medical_remboursable_quebec_depuis_dict(None) == medical_remboursable_quebec_depuis_dict({}) == p
    assert calcul(_dossier_52000(), medical_remboursable_quebec=p) == calcul(_dossier_52000())


@pytest.mark.parametrize("champ", ["salaire", "deduction_205", "deduction_207", "avantages_211", "revenu_net", "base_381"])
@pytest.mark.parametrize("valeur", [D("NaN"), D("sNaN"), D("-1"), D("1.001"), D("1E9999"), True, "100", 1.5])
def test_montants_invalides(champ, valeur):
    with pytest.raises(ValueError): moteur(profil(), **{champ: valeur})


def test_integration_381_net_quebec_et_remboursement_unique():
    d = _dossier_52000(); avant = calcul(d, frais_medicaux=frais())
    e = calcul(d, frais_medicaux=frais(), medical_remboursable_quebec=profil())
    r = e.resultat_medical_remboursable_quebec
    assert r.revenu_familial == D(50095) and r.base_ligne_381 == D("8497.15")
    assert r.credit_ligne_44 == D(1466) and r.reduction_ligne_48 == D(1088)
    assert r.credit_ligne_462 == D(378)
    assert (e.revenu, e.federal, e.quebec) == (avant.revenu, avant.federal, avant.quebec)
    assert e.rapprochement.abattement_quebec == avant.rapprochement.abattement_quebec
    assert e.rapprochement.impot_total_preliminaire == avant.rapprochement.impot_total_preliminaire
    assert e.rapprochement.remboursement_estime - avant.rapprochement.remboursement_estime == D(378)
    assert e.rapprochement.credit_medical_quebec_ligne_462 == D(378)


def test_cumul_supplement_federal_distinct():
    from tests.test_tax_medical_supplement_2025 import profil as federal
    f = replace(frais(), supplement=federal())
    e = calcul(_dossier_52000(), frais_medicaux=f, medical_remboursable_quebec=profil())
    r = e.rapprochement
    assert r.supplement_medical_ligne_45200 == D("592.95")
    assert r.credit_medical_quebec_ligne_462 == D(378)
    assert r.remboursement_estime - r.solde_estime == r.retenues_totales + r.remboursements_cotisations_totaux + D("970.95") - r.impot_total_preliminaire


def test_grille_depuis_dossier_rpa_tp59_case211_sans_syndicat():
    from tests.test_tax_rpp_2025 import dossier_rpa, profil_rpa
    from tests.test_tax_employment_expenses_2025 import _profil as depenses
    from tests.test_tax_union_dues_integration_2025 import _cotisations_600
    d = dossier_rpa()
    d = replace(d, donnees_validees=d.donnees_validees + (_validee("RL1.pdf", "RL-1", "211", "1000"),))
    e = calcul(d, frais_medicaux=frais(), medical_remboursable_quebec=profil(),
        cotisations_rpa=profil_rpa(), depenses_emploi=depenses(), cotisations_syndicales=_cotisations_600())
    assert e.resultat_medical_remboursable_quebec.revenu_travail == D(47000)
    # Les cotisations syndicales 397 ne figurent pas dans la grille Québec 205/207.
    assert e.resultat_medical_remboursable_quebec.revenu_familial == e.revenu.revenu_net_quebec


@pytest.mark.parametrize("valeurs", [("100", "100"), ("-100",), ("52001",)])
def test_case211_dupliquee_negative_ou_superieure_au_salaire(valeurs):
    d = _dossier_52000()
    d = replace(d, donnees_validees=d.donnees_validees + tuple(_validee("RL1.pdf", "RL-1", "211", v) for v in valeurs))
    with pytest.raises(ValueError, match="211"):
        calcul(d, frais_medicaux=frais(), medical_remboursable_quebec=profil())


@pytest.mark.parametrize("credit", [D("1466.01"), D("NaN"), D(-1), "378"])
def test_rapprochement_refuse_credit_invalide(credit):
    from src.comptaprivee.tax_reconciliation_2025 import calculer_rapprochement_fiscal_2025
    e = calcul(_dossier_52000())
    with pytest.raises(ValueError):
        calculer_rapprochement_fiscal_2025(e.base, e.federal, e.quebec, credit_medical_quebec=credit)


def test_remboursable_meme_si_impot_quebec_nul():
    f = replace(frais(), montant_admissible_quebec=D(200000))
    avant = calcul(_dossier_52000(), frais_medicaux=f)
    e = calcul(_dossier_52000(), frais_medicaux=f, medical_remboursable_quebec=profil())
    assert e.quebec.impot_quebec_preliminaire == 0
    assert e.rapprochement.remboursement_estime - avant.rapprochement.remboursement_estime == D(378)


def test_conjoint_et_naissance_contradictoires_refuses():
    from tests.test_tax_federal_spouse_2025 import _profil as conjoint
    net = calcul(_dossier_52000()).revenu.revenu_net_federal
    with pytest.raises(ValueError, match="combinaison familiale"):
        calcul(_dossier_52000(), frais_medicaux=frais(), medical_remboursable_quebec=profil(),
            montant_conjoint_federal=conjoint(revenu_net_contribuable_ligne_23600=net))
    from tests.test_tax_medical_supplement_2025 import profil as federal
    with pytest.raises(ValueError, match="Naissance"):
        calcul(_dossier_52000(), frais_medicaux=replace(frais(), supplement=federal(age_fin_2025=40)), medical_remboursable_quebec=profil())


def test_dependant_handicape_exige_extension_familiale(transfert):
    from tests.test_tax_disability_transfer_2025 import ensemble
    with pytest.raises(ValueError, match="combinaison familiale"):
        calcul(_dossier_52000(), frais_medicaux=frais(), medical_remboursable_quebec=profil(), transferts_handicap=ensemble(transfert))


def test_json_recalcul_ancien_divergence(tmp_path):
    d = _dossier_52000(); e = calcul(d, frais_medicaux=frais(), medical_remboursable_quebec=profil())
    f = sauvegarder_dossier_fiscal(d, estimation=e, destination=tmp_path / "medical_quebec.json")
    brut = json.loads(f.read_text(encoding="utf-8")); c = dossier_fiscal_depuis_contenu(brut)
    assert c.medical_remboursable_quebec == profil()
    assert calcul(c.dossier, frais_medicaux=c.frais_medicaux, medical_remboursable_quebec=c.medical_remboursable_quebec) == e
    assert "credit_ligne_462" not in brut["medical_remboursable_quebec"]
    with pytest.raises(ValueError, match="divergent"):
        sauvegarder_dossier_fiscal(d, estimation=e, medical_remboursable_quebec=profil(naissance="1989-01-01"), destination=tmp_path / "refus.json")
    brut.pop("medical_remboursable_quebec")
    assert dossier_fiscal_depuis_contenu(brut).medical_remboursable_quebec == MedicalRemboursableQuebec2025()


@pytest.mark.parametrize("champ,valeur", [("naissance", 1990), ("valide_par_comptable", "oui"), ("source", 1), ("credit_ligne_462", "1466"), ("reclamer", 1)])
def test_json_strict(champ, valeur):
    brut = medical_remboursable_quebec_vers_dict(profil()); brut[champ] = valeur
    with pytest.raises(ValueError): medical_remboursable_quebec_depuis_dict(brut)


def test_trace_resume_pdf(tmp_path):
    e = calcul(_dossier_52000(), frais_medicaux=frais(), medical_remboursable_quebec=profil())
    t = construire_trace_calcul_fiscal_2025(e)
    assert "462" in t.formule_resultat
    assert [x.ordre for x in t.lignes] == list(range(1, len(t.lignes) + 1))
    assert next(x for x in t.lignes if x.libelle == "Crédit médical remboursable Québec 462").montant == D(378)
    assert "ANNEXE B, PARTIE D" in formater_estimation_fiscale_2025(e)
    f = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "medical_quebec_6e.pdf")
    with fitz.open(f) as pdf:
        texte = "\n".join(p.get_text() for p in pdf)
        for p in pdf:
            assert all(0 <= b[0] < b[2] <= p.rect.width and 0 <= b[1] < b[3] <= p.rect.height for b in p.get_text("blocks"))
    for attendu in ("ANNEXE B, PARTIE D", "378.00", "8497.15", "50095.00", "validation comptable"):
        assert attendu in texte
