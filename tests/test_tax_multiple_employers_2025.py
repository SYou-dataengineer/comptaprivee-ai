"""7A : exemples fictifs, résultats des formulaires 2025 et garde-fous."""
from dataclasses import replace
from decimal import Decimal as D
from pathlib import Path
import json

import pytest

from src.comptaprivee.tax_employment_qpp_2025 import calculer_rrq_salarie_2025
from src.comptaprivee.tax_engine_input_2025 import consolider_base_fiscale_emploi_2025
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025, formater_estimation_fiscale_2025
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
from tests.test_tax_estimation_2025 import _dossier_52000, _validee
from tests.test_tax_contribution_overpayments_storage_2025 import _profil


def dossier_multiple(revenus=("26000", "26000"), rrq=("1440", "1440"), bb=("0", "0")):
    donnees = []
    for i, (revenu, ba, deuxieme) in enumerate(zip(revenus, rrq, bb), 1):
        r = D(revenu)
        ae = (min(r, D("65700")) * D("0.0131")).quantize(D(".01"))
        rqap = (min(r, D("98000")) * D("0.00494")).quantize(D(".01"))
        # Retenues différentes : deux employeurs réels, pas deux copies identiques.
        for typ, cases in (("T4", {"14":r,"17":ba,"17A":deuxieme,"18":ae,"22":D(1000*i),
                "24":min(r,D("65700")),"26":min(r,D("81200")),"55":rqap,"56":min(r,D("98000"))}),
                ("RL-1", {"A":r,"B.A":ba,"B.B":deuxieme,"C":ae,"E":D(800*i),
                "G":min(r,D("81200")),"H":rqap,"I":min(r,D("98000"))})):
            donnees.extend(_validee(f"Employeur{i}_{typ}.pdf", typ, c, v) for c,v in cases.items())
    return replace(_dossier_52000(), documents=tuple(dict.fromkeys(d.document for d in donnees)),
                   donnees_validees=tuple(donnees))


def profil_multiple(dossier=None):
    b = consolider_base_fiscale_emploi_2025(dossier or dossier_multiple())
    return replace(_profil(), rrq_ba=b.rrq_base_premiere_supplementaire, rrq_bb=b.rrq_deuxieme_supplementaire,
        gains_admissibles_rrq=b.gains_admissibles_rrq, assurance_emploi=b.assurance_emploi,
        gains_assurables_ae=b.gains_assurables_ae, rqap=b.rqap, revenus_assujettis_rqap=b.gains_assurables_rqap,
        multi_employeurs_confirme=True, source="Employeur1 : T4/RL-1; Employeur2 : T4/RL-1; originaux fictifs appariés")


@pytest.mark.parametrize("ba,bb,gains,credit,deduction,qc,exces", [
    ("2880","0","52000","2430","450","450","0"),
    ("3104","0","52000","2619","485","485","0"),
    ("3200","0","52000","2619","485","485","96"),
    ("2700","0","52000","2278.13","421.87","421.88","0"),
    ("4339.20","396","81200","3661.20","1074","1074","0"),
    ("8000","0","104000","3661.20","1074","1074","3264.80"),
    # Transfert d'excédent B.A vers B.B, partie 2b.
    ("4400","0","81200","3661.20","738.80","738.80","0"),
    # Transfert B.B vers base/première lorsque les cotisations B.A sont insuffisantes.
    ("4000","500","81200","3479","1021","1021","0"),
    ("0","0","0","0","0","0","0"),
])
def test_formulaires_rrq(ba,bb,gains,credit,deduction,qc,exces):
    r = calculer_rrq_salarie_2025(D(ba),D(bb),D(gains))
    assert (r.ligne_30800,r.ligne_22215,r.ligne_248,r.excedent) == tuple(map(D,(credit,deduction,qc,exces)))


@pytest.mark.parametrize("m", [D("-1"), D("NaN"), D("Infinity"), 1.5])
def test_entrees_invalides_rrq(m):
    with pytest.raises(ValueError):
        calculer_rrq_salarie_2025(m,D(0),D(0))


def test_regression_deux_emplois_26000():
    d = dossier_multiple()
    e = calculer_estimation_fiscale_2025(d, cotisations_excedentaires=profil_multiple(d))
    assert e.federal.cotisation_base_rrq == D("2430")
    assert e.revenu.deduction_rrq_amelioree_federale == D("450")
    assert e.revenu.deduction_rrq_quebec == D("450")
    assert e.base.revenu_emploi_federal == e.base.revenu_emploi_quebec == D("52000")
    assert e.base.impot_federal_retenu == D("3000")
    assert e.base.impot_quebec_retenu == D("2400")
    assert len(e.base.feuillets_emploi) == 4
    assert e.rapprochement.remboursement_rrq_excedentaire == 0
    assert "EMPLOYEURS MULTIPLES" in formater_estimation_fiscale_2025(e)


def test_historique_unique_inchange():
    e = calculer_estimation_fiscale_2025(_dossier_52000())
    assert e.federal.cotisation_base_rrq == D("2619")
    assert e.revenu.deduction_rrq_amelioree_federale == D("485")
    assert e.rapprochement.remboursement_estime == D("5611.05")


def test_excedent_multi_et_17a():
    d = dossier_multiple(("81200","81200"),("4339.20","4339.20"),("396","396"))
    e = calculer_estimation_fiscale_2025(d,cotisations_excedentaires=profil_multiple(d))
    assert e.federal.cotisation_base_rrq == D("3661.20")
    assert e.revenu.deduction_rrq_amelioree_federale == D("1074")
    assert e.rapprochement.remboursement_rrq_excedentaire == D("4735.20")
    assert e.rapprochement.remboursement_ae_excedentaire == D("860.67")


def test_employeur_a_zero():
    d = dossier_multiple(("26000","0"),("1440","0"))
    e = calculer_estimation_fiscale_2025(d,cotisations_excedentaires=profil_multiple(d))
    assert e.revenu.deduction_rrq_amelioree_federale == D("225")


def test_confirmation_requise():
    with pytest.raises(ValueError,match="7A.*confirmer"):
        calculer_estimation_fiscale_2025(dossier_multiple())


@pytest.mark.parametrize("case", ["16","16A"])
def test_rpc_refuse(case):
    d = dossier_multiple()
    d = replace(d,donnees_validees=d.donnees_validees+(_validee("Employeur1_T4.pdf","T4",case,"1"),))
    with pytest.raises(ValueError,match="RPC.*RC381"):
        consolider_base_fiscale_emploi_2025(d)


def test_copie_feuillet_refusee():
    d = dossier_multiple()
    donnees = tuple(replace(v,document=Path("copie.pdf")) for v in d.donnees_validees if str(v.document)=="Employeur1_T4.pdf")
    # Remplacer le deuxième T4 par une copie du premier (même nombre de feuillets).
    d = replace(d,donnees_validees=tuple(v for v in d.donnees_validees if str(v.document)!="Employeur2_T4.pdf")+donnees)
    with pytest.raises(ValueError,match="doublon potentiel"):
        consolider_base_fiscale_emploi_2025(d)


def test_case_dupliquee_refusee():
    d = dossier_multiple()
    with pytest.raises(ValueError,match="doublon"):
        consolider_base_fiscale_emploi_2025(replace(d,donnees_validees=d.donnees_validees+(d.donnees_validees[0],)))


def test_cases_manquantes_par_feuillet_non_masquees():
    d = dossier_multiple()
    with pytest.raises(ValueError,match="manquantes"):
        consolider_base_fiscale_emploi_2025(replace(d,donnees_validees=d.donnees_validees[1:]))


def test_json_provenance_roundtrip_et_ancien(tmp_path):
    d = dossier_multiple()
    p = sauvegarder_dossier_fiscal(d,cotisations_excedentaires=profil_multiple(d),destination=tmp_path/"7a.json")
    x = charger_dossier_fiscal(p)
    assert x.cotisations_excedentaires == profil_multiple(d)
    assert x.dossier == d
    e = calculer_estimation_fiscale_2025(x.dossier,cotisations_excedentaires=x.cotisations_excedentaires)
    assert e.federal.cotisation_base_rrq == D("2430")
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["cotisations_excedentaires"].pop("multi_employeurs_confirme")
    p.write_text(json.dumps(brut),encoding="utf-8")
    assert charger_dossier_fiscal(p).cotisations_excedentaires.multi_employeurs_confirme is False


def test_trace_pdf_provenance(tmp_path):
    import fitz
    from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025, formater_trace_calcul_fiscal_2025
    from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
    e = calculer_estimation_fiscale_2025(dossier_multiple(),cotisations_excedentaires=profil_multiple())
    trace = formater_trace_calcul_fiscal_2025(construire_trace_calcul_fiscal_2025(e))
    assert "Ligne 30800" in trace and "2430.00" in trace and "22215" in trace
    p = tmp_path/"7a.pdf"
    exporter_rapport_fiscal_pdf_2025(e,p)
    with fitz.open(p) as pdf:
        texte = "\n".join(page.get_text() for page in pdf)
    assert "Employeur1_T4.pdf" in texte and "Employeur2_RL-1.pdf" in texte
    assert "2430.00" in texte and "450.00" in texte


def test_prime_travail_utilise_275_corrige():
    from tests.test_tax_quebec_work_premium_2025 import profil
    d = dossier_multiple(("10000","10000"),("416","416"))
    e = calculer_estimation_fiscale_2025(d,cotisations_excedentaires=profil_multiple(d),prime_travail_quebec=profil())
    assert e.revenu.deduction_rrq_quebec == D("130")
    assert e.revenu.revenu_net_quebec == D("18670")
    assert e.resultat_prime_travail_quebec.base.revenu_familial_ligne_54 == D("18670")
    assert e.resultat_prime_travail_quebec.credit_ligne_456 == D("580.52")


@pytest.mark.parametrize("naissance", ["1950-01-01","2007-12-31"])
def test_age_contradictoire_avec_autre_profil(naissance):
    from tests.test_tax_quebec_work_premium_2025 import profil
    with pytest.raises(ValueError,match="naissance incompatible"):
        calculer_estimation_fiscale_2025(dossier_multiple(),cotisations_excedentaires=profil_multiple(),
            prime_travail_quebec=profil(naissance=naissance))


def test_depenses_emploi_non_attribuees_refusees():
    from src.comptaprivee.tax_employment_expenses_2025 import DepensesEmploi2025
    with pytest.raises(ValueError,match="T2200/T777"):
        calculer_estimation_fiscale_2025(dossier_multiple(),cotisations_excedentaires=profil_multiple(),
            depenses_emploi=DepensesEmploi2025(deduction_federale_t777=D("100")))


def test_profil_montants_desynchronises_refuse():
    with pytest.raises(ValueError,match="correspondre exactement"):
        calculer_estimation_fiscale_2025(dossier_multiple(),
            cotisations_excedentaires=replace(profil_multiple(),rrq_ba=D("3104")))


def test_incoherences_compensees_entre_employeurs_refusees():
    d = dossier_multiple()
    valeurs = tuple(replace(v,valeur_validee=v.valeur_validee+(D("100") if "Employeur1" in str(v.document) else D("-100")))
        if v.type_document == "RL-1" and v.case == "B.A" else v for v in d.donnees_validees)
    with pytest.raises(ValueError,match="par feuillet"):
        consolider_base_fiscale_emploi_2025(replace(d,donnees_validees=valeurs))


@pytest.mark.parametrize("valeur", ["false",1,None])
def test_confirmation_json_stricte(valeur,tmp_path):
    p = sauvegarder_dossier_fiscal(dossier_multiple(),cotisations_excedentaires=profil_multiple(),destination=tmp_path/"invalid.json")
    brut=json.loads(p.read_text(encoding="utf-8"))
    brut["cotisations_excedentaires"]["multi_employeurs_confirme"]=valeur
    p.write_text(json.dumps(brut),encoding="utf-8")
    with pytest.raises(ValueError,match="booléen"):
        charger_dossier_fiscal(p)


@pytest.mark.parametrize("revenus,ae,rqap", [(("1000","1000"),"26.20","0"),(("900","1000"),"24.89","9.39")])
def test_petits_revenus_remboursements(revenus,ae,rqap):
    d=dossier_multiple(revenus,("0","0"))
    e=calculer_estimation_fiscale_2025(d,cotisations_excedentaires=profil_multiple(d))
    assert e.rapprochement.remboursement_ae_excedentaire==D(ae)
    assert e.rapprochement.remboursement_rqap_excedentaire==D(rqap)


def test_excedent_rrq_inferieur_au_maximum_annuel():
    d=dossier_multiple(rrq=("1600","1600"))
    e=calculer_estimation_fiscale_2025(d,cotisations_excedentaires=profil_multiple(d))
    assert e.rapprochement.remboursement_rrq_excedentaire==D("96")
