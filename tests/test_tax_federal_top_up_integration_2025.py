"""5A : profils existants, ordre T1, sorties et compatibilité JSON."""
from dataclasses import replace
from decimal import Decimal as D, ROUND_HALF_UP
from pathlib import Path
import ast

import fitz
import pytest

from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calcul, formater_estimation_fiscale_2025
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from src.comptaprivee.tax_federal_2025 import finaliser_credits_federaux_2025
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_medical_expenses_integration_2025 import _frais_3000
from tests.test_tax_tuition_integration_2025 import _scolarite_3000
from tests.test_tax_disability_integration_2025 import _deficience_complete
from tests.test_tax_donations_integration_2025 import _dons_1000
from tests.test_tax_federal_age_pension_integration_2025 import _profil_age_federal
from tests.test_tax_federal_spouse_integration_2025 import _profil_conjoint
from tests.test_tax_federal_eligible_dependant_integration_2025 import _profil_personne_charge
from tests.test_tax_federal_caregiver_child_integration_2025 import _profil_aidant_enfant
from tests.test_tax_federal_caregiver_other_dependant_2025 import _profil as autre_aidant
from tests.test_tax_federal_home_buyers_2025 import _profil as achat
from tests.test_tax_federal_home_accessibility_2025 import _profil as acces
from tests.test_tax_federal_spouse_caregiver_base_2025 import _profil_infirmite
from tests.test_tax_federal_caregiver_spouse_dependant_integration_2025 import _30425_conjoint


def cent(x):
    return x.quantize(D(".01"), rounding=ROUND_HALF_UP)


def dossier_70000():
    d = _dossier_52000()
    valeurs = {"14": "70000", "17": "4256", "18": "860.67", "24": "65700", "26": "70000", "55": "345.80", "56": "70000",
               "A": "70000", "B.A": "4256", "C": "860.67", "G": "70000", "H": "345.80", "I": "70000"}
    return replace(d, donnees_validees=tuple(replace(x, valeur_validee=D(valeurs[x.case]), valeur_extraite=D(valeurs[x.case])) if x.case in valeurs else x for x in d.donnees_validees))


def medical(montant="50000"):
    return replace(_frais_3000(), montant_admissible_federal=D(montant), montant_admissible_quebec=D(0))


def verifier_t1(e):
    f = e.federal
    c = f.credits_federaux_complets
    assert c.base_ligne_33500 == sum(dict(c.montants_par_ligne).values())
    assert c.credit_ligne_33800 == cent(c.base_ligne_33500 * D(".145"))
    assert c.credit_compensatoire_ligne_34990 == cent(max(c.credit_ligne_33800 + c.annexe9_ligne22 - D("8319.38"), D(0)) * D(".0345"))
    assert c.total_credits_ligne_35000 == c.credit_ligne_33800 + c.credit_dons_ligne_34900 + c.credit_compensatoire_ligne_34990
    assert f.impot_federal_de_base == max(cent(f.impot_brut - c.total_credits_ligne_35000 - e.dividendes.ligne_40425), D(0))
    assert f.impot_federal_apres_credit_etranger == max(f.impot_federal_de_base - f.credit_etranger_ligne_40500, D(0))
    assert e.rapprochement.abattement_quebec == cent(f.impot_federal_de_base * D(".165"))
    assert f.top_up_credit == c.credit_compensatoire_ligne_34990


@pytest.mark.parametrize("code", ["30100", "30300", "30400", "30425", "31285", "31270", "30450", "30500"])
def test_huit_garde_fous_remplaces_par_calcul_reel(code):
    revenu = D("69335")
    options = {
        "30100": dict(credits_federaux_age_pension=_profil_age_federal(revenu_net_ligne_23600=revenu)),
        "30300": dict(montant_conjoint_federal=_profil_conjoint(revenu_net_contribuable_ligne_23600=revenu)),
        "30400": dict(personne_charge_admissible_federale=_profil_personne_charge(revenu_net_contribuable_ligne_23600=revenu)),
        "30425": dict(montant_conjoint_federal=_profil_infirmite(revenu_net_contribuable_ligne_23600=revenu), aidant_conjoint_personne_charge_federal=_30425_conjoint()),
        "31285": dict(accessibilite_domiciliaire_federale=acces()),
        "31270": dict(achat_habitation_federal=achat()),
        "30450": dict(aidant_autre_personne_charge_federal=autre_aidant()),
        "30500": dict(aidant_enfant_federal=_profil_aidant_enfant()),
    }
    e = calcul(dossier_70000(), **options[code])
    assert e.revenu.revenu_imposable_federal == revenu > D("57375")
    assert dict(e.federal.credits_federaux_complets.montants_par_ligne)[code] > 0
    verifier_t1(e)


@pytest.mark.parametrize("options", [
    dict(frais_medicaux=medical()),
    dict(frais_medicaux=medical(), credit_deficience=replace(_deficience_complete(), reclamer_quebec=False)),
    dict(frais_scolarite=replace(_scolarite_3000(), montant_admissible_federal=D(40000), montant_admissible_quebec=D(0))),
    dict(frais_medicaux=medical(), dons_bienfaisance=replace(_dons_1000(), montant_admissible_quebec=D(0))),
])
def test_compensatoire_positif_medical_handicap_scolarite_dons(options):
    e = calcul(dossier_70000(), **options)
    assert e.federal.top_up_credit > 0
    verifier_t1(e)
    c = e.federal.credits_federaux_complets
    if "dons_bienfaisance" in options:
        assert c.annexe9_ligne22 == D(29)
        assert c.credit_dons_ligne_34900 == D(261)


def test_pas_de_report_scolarite_ni_double_finalisation():
    with pytest.raises(ValueError, match="report"):
        calcul(dossier_70000(), frais_scolarite=replace(_scolarite_3000(), montant_admissible_federal=D(60000), montant_admissible_quebec=D(0)))
    e = calcul(dossier_70000(), frais_medicaux=medical())
    with pytest.raises(ValueError):
        finaliser_credits_federaux_2025(e.federal, e.federal.credits_federaux_complets)


def test_compensatoire_puis_dividendes_hors_base_33800():
    from tests.test_tax_dividend_income_2025 import dossier_dividendes, profil_dividendes
    e = calcul(dossier_dividendes("10000", "0", True), profil_dividendes=profil_dividendes(), frais_medicaux=medical("40000"))
    assert e.federal.top_up_credit > 0
    assert e.dividendes.ligne_40425 == D("2072.73")
    assert "40425" not in dict(e.federal.credits_federaux_complets.montants_par_ligne)
    verifier_t1(e)


def test_compensatoire_40500_et_abattement_base_fixe():
    from tests.test_tax_foreign_investment_2025 import dossier, profil, profil_credit
    options = dict(profil_placement_etranger=profil(), frais_medicaux=medical("40000"))
    d = dossier("10000", "1500", emploi=True)
    sans = calcul(d, profil_credit_impot_etranger=profil_credit("0", "0"), **options)
    avec = calcul(d, profil_credit_impot_etranger=profil_credit("100", "0"), **options)
    assert avec.federal.top_up_credit > 0
    assert sans.federal.credits_federaux_complets == avec.federal.credits_federaux_complets
    assert sans.federal.impot_federal_de_base == avec.federal.impot_federal_de_base
    assert sans.rapprochement.abattement_quebec == avec.rapprochement.abattement_quebec
    assert sans.rapprochement.impot_total_preliminaire - avec.rapprochement.impot_total_preliminaire == D(100)
    verifier_t1(avec)


def test_trace_pdf_resume_et_json(tmp_path):
    e = calcul(dossier_70000(), frais_medicaux=medical())
    trace = construire_trace_calcul_fiscal_2025(e)
    lignes = {x.libelle: x for x in trace.lignes}
    assert lignes["Ligne 34990"].montant == e.federal.top_up_credit > 0
    assert "8 319,38" in lignes["Ligne 34990"].formule
    assert "3,45 %" in lignes["Ligne 34990"].formule
    assert lignes["Total ligne 35000"].ordre < lignes["Impôt fédéral de base"].ordre < lignes["Abattement Québec"].ordre
    assert [x.ordre for x in trace.lignes] == list(range(1, len(trace.lignes) + 1))
    p = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "5a.pdf")
    with fitz.open(p) as pdf:
        texte = "\n".join(page.get_text() for page in pdf)
        for page in pdf:
            for x0, y0, x1, y1, *_ in page.get_text("blocks"):
                assert 0 <= x0 < x1 <= page.rect.width
                assert 0 <= y0 < y1 <= page.rect.height
    for sortie in (texte, formater_estimation_fiscale_2025(e)):
        assert "CRÉDIT COMPENSATOIRE FÉDÉRAL 2025" in sortie
        assert f"Ligne 34990 : {e.federal.top_up_credit:.2f}" in sortie
        assert "Annexe 9 ligne 22" in sortie
    p = sauvegarder_dossier_fiscal(e.dossier, estimation=e, frais_medicaux=e.frais_medicaux, destination=tmp_path / "5a.json")
    charge = charger_dossier_fiscal(p)
    assert calcul(charge.dossier, frais_medicaux=charge.frais_medicaux) == e
    p = sauvegarder_dossier_fiscal(_dossier_52000(), destination=tmp_path / "ancien.json")
    assert '"credits_federaux_complets"' not in p.read_text(encoding="utf-8")
    ancien = calcul(charger_dossier_fiscal(p).dossier)
    assert ancien.federal.top_up_credit == 0
    assert ancien.rapprochement.impot_total_preliminaire == D("8088.95")


def test_gui_messages_calcules_sans_saisie_34990():
    source = Path("src/comptaprivee/gui.py").read_text(encoding="utf-8")
    arbre = ast.parse(source)
    messages = [n.value for n in ast.walk(arbre) if isinstance(n, ast.Constant) and isinstance(n.value, str) and "34990" in n.value]
    assert len(messages) == 9
    for message in messages:
        assert "calcul" in message.lower()
        assert "garde-fou ligne 34990" not in message.lower()
        assert "restriction de la ligne 34990" not in message.lower()
    assert not any(isinstance(n, ast.Name) and "34990" in n.id for n in ast.walk(arbre))
