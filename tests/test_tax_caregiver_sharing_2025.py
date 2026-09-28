from dataclasses import replace
from decimal import Decimal as D
import json
import fitz
import pytest

from tests.test_tax_federal_caregiver_other_dependant_2025 import _profil
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_top_up_integration_2025 import verifier_t1, dossier_70000, medical
from src.comptaprivee.tax_federal_caregiver_other_dependant_2025 import (
    montant_ligne_30450_2025, nombre_personnes_charge_ligne_51120_2025,
    valider_aidant_naturel_30450_2025)
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calcul
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, dossier_fiscal_depuis_contenu
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025


def profil(**kw):
    p = _profil(aucun_partage_reclamation_30450=False, partage_30450_confirme=True,
        montant_attribue_autres_soutiens=D("1500"), reference_personne="Parent fictif A",
        source_partage="Entente fictive signée des soutiens A et B")
    return replace(p, **kw)


@pytest.mark.parametrize("net,autres,attendu", [
    ("0", "0", "8601"), ("0", "8601", "0"), ("25000", "1500", "2298"),
    ("20197.01", "4300.50", "4300.49"), ("28797.99", "0.01", "0"),
])
def test_plafond_puis_soustraction_sans_double_compte(net, autres, attendu):
    p = profil(revenu_net_personne_ligne_23600=D(net), montant_attribue_autres_soutiens=D(autres))
    assert montant_ligne_30450_2025(p) == D(attendu)
    assert nombre_personnes_charge_ligne_51120_2025(p) == int(D(attendu) > 0)
    complement = replace(p, montant_attribue_autres_soutiens=D(attendu))
    assert montant_ligne_30450_2025(complement) == D(autres)


@pytest.mark.parametrize("kw", [
    {"montant_attribue_autres_soutiens": D("3798.01")},
    {"montant_attribue_autres_soutiens": D("-0.01")},
    {"montant_attribue_autres_soutiens": D("1.001")},
    {"montant_attribue_autres_soutiens": D("NaN")},
    {"montant_attribue_autres_soutiens": 1.5},
    {"partage_30450_confirme": False}, {"partage_30450_confirme": "oui"},
    {"aucun_partage_reclamation_30450": True}, {"reclamer_montant": False},
    {"reference_personne": " "}, {"source_partage": ""},
    {"valide_par_comptable": False}, {"valide_par_comptable": 1},
    {"preuve_medicale_ou_t2201_confirmee": False},
    {"aucune_reclamation_ligne_30300_30400_pour_personne": False},
    {"aucun_paiement_pension_alimentaire_pour_personne": False},
    {"revenu_net_personne_ligne_23600": D("Infinity")},
    {"revenu_net_personne_ligne_23600": D("28798")},
])
def test_partage_invalide_refuse(kw):
    with pytest.raises(ValueError):
        valider_aidant_naturel_30450_2025(profil(**kw))


def test_t1_topup_et_revenus_inchanges():
    d = dossier_70000()
    e = calcul(d, aidant_autre_personne_charge_federal=profil(), frais_medicaux=medical())
    assert dict(e.federal.credits_federaux_complets.montants_par_ligne)["30450"] == D("2298")
    assert e.federal.top_up_credit > 0
    verifier_t1(e)
    base = calcul(d, frais_medicaux=medical())
    assert e.revenu == base.revenu and e.quebec == base.quebec


def test_json_recalcul_inference_et_divergence(tmp_path):
    e = calcul(_dossier_52000(), aidant_autre_personne_charge_federal=profil())
    f = sauvegarder_dossier_fiscal(e.dossier, estimation=e, destination=tmp_path / "partage.json")
    brut = json.loads(f.read_text(encoding="utf-8"))
    c = dossier_fiscal_depuis_contenu(brut)
    assert c.aidant_autre_personne_charge_federal == profil()
    assert calcul(c.dossier, aidant_autre_personne_charge_federal=c.aidant_autre_personne_charge_federal).federal == e.federal
    with pytest.raises(ValueError, match="divergent"):
        sauvegarder_dossier_fiscal(e.dossier, estimation=e, destination=tmp_path / "refus.json",
            aidant_autre_personne_charge_federal=_profil())
    assert not (tmp_path / "refus.json").exists()


@pytest.mark.parametrize("champ,valeur", [
    ("partage_30450_confirme", 1), ("montant_attribue_autres_soutiens", 1.5),
    ("montant_attribue_autres_soutiens", True), ("reference_personne", 123),
    ("valide_par_comptable", "oui"), ("revenu_net_personne_ligne_23600", 0.1),
    ("credit_calcule", "100"), ("source_partage", None),
])
def test_json_strict(tmp_path, champ, valeur):
    f = sauvegarder_dossier_fiscal(_dossier_52000(), aidant_autre_personne_charge_federal=profil(),
        destination=tmp_path / "partage.json")
    brut = json.loads(f.read_text(encoding="utf-8"))
    brut["aidant_autre_personne_charge_federal"][champ] = valeur
    with pytest.raises(ValueError):
        dossier_fiscal_depuis_contenu(brut)


def test_ancien_json_sans_partage(tmp_path):
    f = sauvegarder_dossier_fiscal(_dossier_52000(), aidant_autre_personne_charge_federal=_profil(),
        destination=tmp_path / "ancien.json")
    brut = json.loads(f.read_text(encoding="utf-8"))
    for champ in ("partage_30450_confirme", "montant_attribue_autres_soutiens", "reference_personne", "source_partage"):
        brut["aidant_autre_personne_charge_federal"].pop(champ)
    c = dossier_fiscal_depuis_contenu(brut)
    assert montant_ligne_30450_2025(c.aidant_autre_personne_charge_federal) == D("3798")


def test_trace_pdf_partage(tmp_path):
    e = calcul(_dossier_52000(), aidant_autre_personne_charge_federal=profil())
    trace = construire_trace_calcul_fiscal_2025(e)
    assert "Parent fictif A" in str(trace)
    assert "1500.00" in str(trace) and "2298.00" in str(trace)
    f = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "partage.pdf")
    with fitz.open(f) as pdf:
        texte = "\n".join(p.get_text() for p in pdf)
        for p in pdf:
            assert all(0 <= b[0] < b[2] <= p.rect.width and 0 <= b[1] < b[3] <= p.rect.height for b in p.get_text("blocks"))
    assert "Parent fictif A" in texte and "2298.00" in texte and "1500.00" in texte
    assert "Aucun partage de la réclamation 30450 : oui" not in texte
