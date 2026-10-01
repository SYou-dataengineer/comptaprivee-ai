from dataclasses import replace
from decimal import Decimal as D
import json
import fitz
import pytest

from tests.test_tax_family_workers_benefit_2025 import profil, famille, enfant
from tests.test_tax_workers_benefit_2025 import dossier_20000, calcul
from tests.test_tax_family_medical_supplement_2025 import options as medical, profil as supplement
from tests.test_tax_federal_top_up_integration_2025 import verifier_t1
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal, dossier_fiscal_depuis_contenu
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_spouse_transfer_2025 import instantane_conjoint_2025


def test_estimation_avances_et_credit_uniques():
    avant = calcul(dossier_20000())
    p = profil(famille(conjoint_avances_base=D(500)), avances_rc210_case10=D(1000), avances_rc210_case11=D(100))
    e = calcul(dossier_20000(), allocation_travailleurs=p)
    r = e.resultat_allocation_travailleurs
    assert r.ligne_45300 == D("5943.38") and r.ligne_41500 == D(1600)
    assert e.revenu == avant.revenu and e.federal == avant.federal and e.quebec == avant.quebec
    assert e.rapprochement.abattement_quebec == avant.rapprochement.abattement_quebec
    net = lambda x: x.rapprochement.remboursement_estime - x.rapprochement.solde_estime
    assert net(e) - net(avant) == D("4343.38")
    verifier_t1(e)


def test_medical_familial_et_prestations_distinctes():
    p = profil(famille(conjoint_revenu_net=D(10000)))
    e = calcul(dossier_20000(), allocation_travailleurs=p, **medical())
    assert e.resultat_allocation_travailleurs.famille.net_familial == D(21835)
    assert e.resultat_supplement_medical.revenu_familial_ajuste == D(29835)
    assert e.resultat_supplement_medical.ligne_45200 == D(1504)
    assert e.resultat_allocation_travailleurs.ligne_45300 > 0
    verifier_t1(e)


@pytest.mark.parametrize("f", [famille(conjoint_nom="Autre"), famille(conjoint_revenu_net=D(9999))])
def test_divergence_supplement_medical(f):
    with pytest.raises(ValueError, match="divergen"):
        calcul(dossier_20000(), allocation_travailleurs=profil(f), **medical())


def test_30300_revenu_et_identite_json(tmp_path):
    from tests.test_tax_federal_spouse_2025 import _profil
    net = calcul(dossier_20000()).revenu.revenu_net_federal
    conjoint = _profil(revenu_net_contribuable_ligne_23600=net, revenu_net_conjoint_2025=D(8000))
    e = calcul(dossier_20000(), allocation_travailleurs=profil(), montant_conjoint_federal=conjoint)
    verifier_t1(e)
    f = sauvegarder_dossier_fiscal(e.dossier, estimation=e, montant_conjoint_federal=conjoint,
        destination=tmp_path / "act.json")
    brut = json.loads(f.read_text(encoding="utf-8"))
    brut["allocation_travailleurs"]["famille"]["conjoint_revenu_net"] = "7999.00"
    with pytest.raises(ValueError, match="divergent"):
        dossier_fiscal_depuis_contenu(brut)


def test_stockage_recalcul_ancien_et_divergence(tmp_path):
    e = calcul(dossier_20000(), allocation_travailleurs=profil())
    f = sauvegarder_dossier_fiscal(e.dossier, estimation=e, destination=tmp_path / "act.json")
    c = charger_dossier_fiscal(f)
    assert c.allocation_travailleurs == e.allocation_travailleurs
    assert calcul(c.dossier, allocation_travailleurs=c.allocation_travailleurs) == e
    brut = json.loads(f.read_text(encoding="utf-8"))
    assert brut["allocation_travailleurs"]["famille"]["conjoint_revenu_net"] == "8000.00"
    assert "exemption_second_revenu" not in brut["allocation_travailleurs"]["famille"]
    with pytest.raises(ValueError, match="diffère"):
        sauvegarder_dossier_fiscal(e.dossier, estimation=e, allocation_travailleurs=profil(famille(conjoint_revenu_net=D(1))), destination=f)
    brut["allocation_travailleurs"].pop("famille")
    brut["allocation_travailleurs"]["sans_conjoint_ni_personne_charge"] = True
    assert not dossier_fiscal_depuis_contenu(brut).allocation_travailleurs.famille.activer


def test_sauvegarde_sans_estimation_identite_refusee(tmp_path):
    with pytest.raises(ValueError, match="différer"):
        sauvegarder_dossier_fiscal(dossier_20000(), allocation_travailleurs=profil(famille(conjoint_nom="Client Test")),
            destination=tmp_path / "refus.json")
    assert not (tmp_path / "refus.json").exists()


def donneur(tmp_path, *, act=False, net="19835", travail="20000"):
    from tests.test_tax_spouse_transfer_2025 import profil as transfert
    from tests.test_tax_federal_age_pension_integration_2025 import _profil_age_federal
    d = replace(dossier_20000(), client="Conjoint fictif")
    if (tmp_path / "donneur.json").exists():
        d = replace(d, case_id=charger_dossier_fiscal(tmp_path / "donneur.json").dossier.case_id)
    opts = {"credits_federaux_age_pension": _profil_age_federal(revenu_net_ligne_23600=D(19835))}
    if act:
        opts["allocation_travailleurs"] = profil(famille(conjoint_nom="Client Test", conjoint_revenu_travail=D(travail),
            conjoint_revenu_net=D(net), conjoint_reclame_base=True), reclamer_base=False)
    else:
        opts.update(medical(supplement(nom_conjoint="Client Test", revenu_net_conjoint=D(net))))
        opts["frais_medicaux_famille"] = replace(opts["frais_medicaux_famille"], demandeur=d.client)
    e = calcul(d, **opts)
    f = sauvegarder_dossier_fiscal(d, estimation=e, credits_federaux_age_pension=e.credits_federaux_age_pension,
        destination=tmp_path / "donneur.json")
    instantane = instantane_conjoint_2025(json.loads(f.read_text(encoding="utf-8")))
    return replace(transfert(tmp_path), dossier_conjoint_json=instantane)


def test_donneur_32600_supplement_familial_et_rapprochement_inverse(tmp_path):
    e = calcul(dossier_20000(), transfert_conjoint=donneur(tmp_path))
    assert e.resultat_transfert_conjoint.ligne_32600 > 0
    assert e.resultat_transfert_conjoint.revenu_beneficiaire_declare_45200 == D(19835)
    verifier_t1(e)
    with pytest.raises(ValueError, match="prestations familiales"):
        calcul(dossier_20000(), transfert_conjoint=donneur(tmp_path, net="19834"))


def test_deux_act_et_transfert_conjoint_verifient_revenus_et_choix(tmp_path):
    p = profil(famille(conjoint_revenu_travail=D(20000), conjoint_revenu_net=D(19835)))
    e = calcul(dossier_20000(), allocation_travailleurs=p, transfert_conjoint=donneur(tmp_path, act=True))
    assert e.resultat_allocation_travailleurs.ligne_45300 > 0
    verifier_t1(e)
    with pytest.raises(ValueError, match="travail du bénéficiaire"):
        calcul(dossier_20000(), allocation_travailleurs=p, transfert_conjoint=donneur(tmp_path, act=True, travail="19999"))
    with pytest.raises(ValueError, match="choix du réclamant"):
        calcul(dossier_20000(), allocation_travailleurs=replace(p, reclamer_base=False), transfert_conjoint=donneur(tmp_path, act=True))
    with pytest.raises(ValueError, match="travail du conjoint ACT divergent"):
        calcul(dossier_20000(), allocation_travailleurs=replace(p, famille=replace(p.famille, conjoint_revenu_travail=D(19999))),
            transfert_conjoint=donneur(tmp_path, act=True))


def test_trace_et_pdf_act_familial(tmp_path):
    e = calcul(dossier_20000(), allocation_travailleurs=profil(famille(**enfant())))
    trace = construire_trace_calcul_fiscal_2025(e)
    ligne = next(x for x in trace.lignes if x.libelle == "Exemption du second revenu ACT")
    assert ligne.montant == D(8000) and "même membre" in ligne.formule
    assert [x.ordre for x in trace.lignes] == list(range(1, len(trace.lignes)+1))
    f = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "act_familial.pdf")
    with fitz.open(f) as pdf:
        texte = "\n".join(page.get_text() for page in pdf)
        for page in pdf:
            for x0, y0, x1, y1, *_ in page.get_text("blocks"):
                assert 0 <= x0 < x1 <= page.rect.width and 0 <= y0 < y1 <= page.rect.height
    for mot in ("ACT FAMILIALE", "Conjoint fictif", "Enfant fictif", "3808.23", "8000.00", "41500"):
        assert mot in texte


def test_etudiant_attribution_json_trace_pdf_et_recalcul(tmp_path):
    p = profil(famille(**enfant(), conjoint_etudiant=True,
        conjoint_etudiant_sans_dependant_confirme=True))
    e = calcul(dossier_20000(), allocation_travailleurs=p)
    assert e.resultat_allocation_travailleurs.ligne_45300 == D("945.31")
    fichier = sauvegarder_dossier_fiscal(e.dossier, estimation=e, destination=tmp_path / "etudiant.json")
    charge = dossier_fiscal_depuis_contenu(json.loads(fichier.read_text(encoding="utf-8")))
    assert charge.allocation_travailleurs == p
    assert calcul(charge.dossier, allocation_travailleurs=charge.allocation_travailleurs).resultat_allocation_travailleurs == e.resultat_allocation_travailleurs
    trace = construire_trace_calcul_fiscal_2025(e)
    assert any("122.7(10)" in x.formule and "conjoint : False" in x.formule for x in trace.lignes)
    fichier_pdf = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "etudiant.pdf")
    with fitz.open(fichier_pdf) as pdf:
        texte = "\n".join(page.get_text() for page in pdf)
    assert "945.31" in texte and "Exception étudiante" in texte


def test_attributions_reciproques_dossier_conjoint_32600(tmp_path):
    t = donneur(tmp_path, act=True)
    brut = json.loads(t.dossier_conjoint_json)
    a = brut["allocation_travailleurs"]
    a["pas_etudiant_temps_plein_plus_13_semaines"] = False
    a["famille"].update(demandeur_etudiant=True, conjoint_enfant_nom="Enfant fictif",
        conjoint_enfant_naissance="2015-05-02", conjoint_enfant_admissible_confirme=True)
    t = replace(t, dossier_conjoint_json=json.dumps(brut))
    p = profil(famille(**enfant(), conjoint_etudiant=True,
        conjoint_etudiant_sans_dependant_confirme=True,
        conjoint_revenu_travail=D(20000), conjoint_revenu_net=D(19835)))
    e = calcul(dossier_20000(), allocation_travailleurs=p, transfert_conjoint=t)
    assert e.resultat_allocation_travailleurs.ligne_45300 == D("945.31")
    with pytest.raises(ValueError, match="Attribution des enfants ACT divergente"):
        calcul(dossier_20000(), allocation_travailleurs=replace(p,
            famille=replace(p.famille, enfant_nom="Autre enfant")), transfert_conjoint=t)
    with pytest.raises(ValueError, match="Statuts étudiants ACT divergents"):
        calcul(dossier_20000(), allocation_travailleurs=replace(p,
            famille=replace(p.famille, conjoint_etudiant=False,
                conjoint_etudiant_sans_dependant_confirme=False)), transfert_conjoint=t)
