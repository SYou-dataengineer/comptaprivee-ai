from dataclasses import replace
from decimal import Decimal as D
import json
import fitz
import pytest
from tests.test_tax_caregiver_children_2025 import enfants, profil as famille
from tests.test_tax_federal_caregiver_child_integration_2025 import _profil_aidant_enfant
from tests.test_tax_interest_income_2025 import dossier_interets, profil_interets
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_top_up_integration_2025 import verifier_t1, dossier_70000, medical
from src.comptaprivee.tax_spouse_transfer_2025 import (
    TransfertConjointFederal2025, CONFIRMATIONS_TRANSFERT_CONJOINT, instantane_conjoint_2025)
from src.comptaprivee.tax_case_storage import (
    sauvegarder_dossier_fiscal, dossier_fiscal_depuis_contenu, _aidant_enfant_federal_vers_dict)
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calcul
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025


def transfert(tmp_path, revenu="10000", profil=None):
    d = replace(dossier_interets(revenu), client="Conjoint fictif")
    p = famille((enfants()[1],)) if profil is None else profil
    f = sauvegarder_dossier_fiscal(d, profil_interets=profil_interets(), aidant_enfant_federal=p,
        destination=tmp_path / "conjoint_enfants.json")
    return TransfertConjointFederal2025(activer=True, beneficiaire="Client Test",
        dossier_conjoint_json=instantane_conjoint_2025(json.loads(f.read_text(encoding="utf-8"))),
        source="Dossiers fictifs : enfants distincts et autorisation vérifiés",
        **{n: True for n in CONFIRMATIONS_TRANSFERT_CONJOINT})


@pytest.mark.parametrize("revenu,reduction,solde", [("0", "0", "2687"), ("10000", "0", "2687"),
    ("17000", "871", "1816"), ("18816", "2687", "0"), ("20000", "3871", "0")])
@pytest.mark.parametrize("inverse", [False, True])
def test_deux_enfants_distincts_et_annexe2(tmp_path, revenu, reduction, solde, inverse):
    a, b = enfants()[::-1] if inverse else enfants()
    propre = famille((a,))
    e = calcul(_dossier_52000(), aidant_enfant_federal=propre, transfert_conjoint=transfert(tmp_path, revenu, famille((b,))))
    r = e.resultat_transfert_conjoint
    assert r.enfant_30500 == D(2687)
    assert r.reduction_36100 == D(reduction)
    assert r.ligne_32600 == D(solde)
    lignes = dict(e.federal.credits_federaux_complets.montants_par_ligne)
    assert lignes["30500"] == D(2687) and lignes["32600"] == D(solde)
    avant = calcul(_dossier_52000(), aidant_enfant_federal=propre)
    assert e.revenu == avant.revenu and e.quebec == avant.quebec
    assert e.federal.credits_federaux_complets.base_ligne_33500 - avant.federal.credits_federaux_complets.base_ligne_33500 == D(solde)
    verifier_t1(e)


@pytest.mark.parametrize("cas", ["meme", "reference", "identite", "ancien_demandeur", "ancien_conjoint"])
def test_doublon_ou_identification_insuffisante_refuse(tmp_path, cas):
    a, b = enfants()
    propre, autre = famille((a,)), famille((b,))
    if cas == "meme": autre = propre
    if cas == "reference": autre = famille((replace(b, reference=" ENFANT-A "),))
    if cas == "identite": autre = famille((replace(a, reference="autre-ref", nom=" ENFANT FICTIF A "),))
    if cas == "ancien_demandeur": propre = _profil_aidant_enfant()
    if cas == "ancien_conjoint": autre = _profil_aidant_enfant()
    p = transfert(tmp_path, profil=autre)
    with pytest.raises(ValueError, match="30500"):
        calcul(_dossier_52000(), aidant_enfant_federal=propre, transfert_conjoint=p)
    with pytest.raises(ValueError, match="30500"):
        sauvegarder_dossier_fiscal(_dossier_52000(), aidant_enfant_federal=propre,
            transfert_conjoint=p, destination=tmp_path / "refus.json")


def test_plusieurs_enfants_et_json_recalcul_injection(tmp_path):
    a, b = enfants()
    c = replace(b, reference="enfant-c", nom="Enfant fictif C")
    propre = famille((a,))
    e = calcul(dossier_70000(), aidant_enfant_federal=propre,
        transfert_conjoint=transfert(tmp_path, profil=famille((b, c))), frais_medicaux=medical())
    assert e.resultat_transfert_conjoint.ligne_32600 == D(5374)
    assert e.federal.top_up_credit > 0
    verifier_t1(e)
    f = sauvegarder_dossier_fiscal(e.dossier, estimation=e, destination=tmp_path / "famille.json")
    brut = json.loads(f.read_text(encoding="utf-8"))
    assert "enfants_30500" not in brut["transfert_conjoint"]
    lu = dossier_fiscal_depuis_contenu(brut)
    assert calcul(lu.dossier, aidant_enfant_federal=lu.aidant_enfant_federal,
        transfert_conjoint=lu.transfert_conjoint, frais_medicaux=medical()).federal == e.federal
    brut["aidant_enfant_federal"] = _aidant_enfant_federal_vers_dict(famille((b,)))
    brut.pop("derniere_estimation", None)
    with pytest.raises(ValueError, match="Même enfant"):
        dossier_fiscal_depuis_contenu(brut)


def test_transfert_ancien_sans_demande_propre_reste_compatible(tmp_path):
    e = calcul(_dossier_52000(), transfert_conjoint=transfert(tmp_path, profil=_profil_aidant_enfant()))
    assert e.resultat_transfert_conjoint.ligne_32600 == D(2687)


def test_trace_pdf_enfants_et_montants_distincts(tmp_path):
    e = calcul(_dossier_52000(), aidant_enfant_federal=famille((enfants()[0],)), transfert_conjoint=transfert(tmp_path))
    texte = str(construire_trace_calcul_fiscal_2025(e))
    assert "Enfant fictif A" in texte and "Enfant fictif B" in texte
    f = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "enfants_conjoints.pdf")
    with fitz.open(f) as pdf:
        texte = "\n".join(p.get_text() for p in pdf)
        assert "Enfant fictif A" in texte and "Enfant fictif B" in texte and "32600" in texte
        for p in pdf:
            assert all(0 <= b[0] < b[2] <= p.rect.width and 0 <= b[1] < b[3] <= p.rect.height for b in p.get_text("blocks"))
