from dataclasses import replace
from decimal import Decimal as D
import json
import fitz
import pytest

from tests.test_tax_federal_caregiver_child_integration_2025 import _profil_aidant_enfant
from tests.test_tax_federal_eligible_dependant_integration_2025 import _profil_personne_charge
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_top_up_integration_2025 import verifier_t1, dossier_70000, medical
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calcul
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, dossier_fiscal_depuis_contenu
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025


def profils(**kw):
    p = _profil_personne_charge(enfant_infirmite_ligne30500=True, reference_enfant="Enfant fictif A",
        aucune_infirmite_enfant=False, personne_charge_avec_infirmite=True,
        preuve_medicale_ou_t2201_confirmee=True)
    a = _profil_aidant_enfant(enfant_reclame_30400=True, reference_enfant="Enfant fictif A",
        enfant_avec_deux_parents_toute_annee=False)
    return dict(personne_charge_admissible_federale=replace(p, **kw), aidant_enfant_federal=a)


@pytest.mark.parametrize("revenu,attendu", [("0", "16129"), ("4000", "12129"), ("20000", "0")])
def test_bases_distinctes_sans_double_2687(revenu, attendu):
    d = _dossier_52000()
    e = calcul(d, **profils(revenu_net_personne_charge_2025=D(revenu)))
    lignes = dict(e.federal.credits_federaux_complets.montants_par_ligne)
    assert lignes["30400"] == D(attendu)
    assert lignes["30500"] == D(2687)
    assert e.revenu == calcul(d).revenu and e.quebec == calcul(d).quebec
    verifier_t1(e)


def test_combinaison_topup_effectif():
    d = dossier_70000()
    net = calcul(d).revenu.revenu_net_federal
    e = calcul(d, **profils(revenu_net_contribuable_ligne_23600=net), frais_medicaux=medical())
    assert e.federal.top_up_credit > 0
    verifier_t1(e)


@pytest.mark.parametrize("kw", [
    {"aidant_naturel_base_2687_inclus": True}, {"aucune_infirmite_enfant": True},
    {"preuve_medicale_ou_t2201_confirmee": False}, {"personne_charge_avec_infirmite": False},
    {"enfant_moins_18_fin_2025": False}, {"personne_charge_18_ans_ou_plus": True},
    {"reference_enfant": ""}, {"reference_enfant": "autre"},
    {"valide_par_comptable": "oui"}, {"aucune_garde_partagee": False},
    {"aucun_paiement_pension_alimentaire": False}, {"enfant_infirmite_ligne30500": 1},
])
def test_combinaison_contradictions_refusees(kw):
    with pytest.raises(ValueError):
        calcul(_dossier_52000(), **profils(**kw))


@pytest.mark.parametrize("cle", ["personne_charge_admissible_federale", "aidant_enfant_federal"])
def test_profil_complementaire_obligatoire(cle):
    opts = profils()
    opts.pop(cle)
    with pytest.raises(ValueError, match="deux profils"):
        calcul(_dossier_52000(), **opts)


def test_json_inference_recalcul_divergence_et_ancien(tmp_path):
    e = calcul(_dossier_52000(), **profils())
    f = sauvegarder_dossier_fiscal(e.dossier, estimation=e, destination=tmp_path / "combine.json")
    brut = json.loads(f.read_text(encoding="utf-8"))
    c = dossier_fiscal_depuis_contenu(brut)
    opts = {n: getattr(c, n) for n in profils()}
    assert opts == profils()
    assert calcul(c.dossier, **opts).federal == e.federal
    with pytest.raises(ValueError, match="divergents"):
        sauvegarder_dossier_fiscal(e.dossier, estimation=e,
            aidant_enfant_federal=_profil_aidant_enfant(), destination=tmp_path / "refus.json")
    for n in profils():
        invalide = json.loads(f.read_text(encoding="utf-8"))
        invalide[n]["reference_enfant"] = "Autre enfant"
        with pytest.raises(ValueError, match="divergentes"):
            dossier_fiscal_depuis_contenu(invalide)
    ancien = sauvegarder_dossier_fiscal(e.dossier, destination=tmp_path / "ancien.json")
    brut = json.loads(ancien.read_text(encoding="utf-8"))
    for n, flag in (("personne_charge_admissible_federale", "enfant_infirmite_ligne30500"), ("aidant_enfant_federal", "enfant_reclame_30400")):
        brut[n].pop(flag)
        brut[n].pop("reference_enfant")
    assert not dossier_fiscal_depuis_contenu(brut).aidant_enfant_federal.reclamer_montant


def test_trace_pdf_ne_contredisent_pas_le_profil(tmp_path):
    e = calcul(_dossier_52000(), **profils())
    t = construire_trace_calcul_fiscal_2025(e)
    assert any("même enfant 30400/30500" in x.source for x in t.lignes)
    f = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "combine.pdf")
    with fitz.open(f) as pdf:
        texte = "\n".join(p.get_text() for p in pdf)
        for p in pdf:
            assert all(0 <= b[0] < b[2] <= p.rect.width and 0 <= b[1] < b[3] <= p.rect.height for b in p.get_text("blocks"))
    assert "Enfant fictif A" in texte and "2687 $ uniquement à 30500" in texte
    assert "Aucune déficience de l'enfant : oui" not in texte
    assert "Enfant avec ses deux parents toute l'année 2025 : oui" not in texte


@pytest.mark.parametrize("cle,champ,valeur", [
    ("personne_charge_admissible_federale", "valide_par_comptable", "oui"),
    ("personne_charge_admissible_federale", "source_personne_charge", 123),
    ("personne_charge_admissible_federale", "revenu_net_personne_charge_2025", 1.5),
    ("personne_charge_admissible_federale", "montant_calcule", "2687"),
    ("aidant_enfant_federal", "valide_par_comptable", 1),
    ("aidant_enfant_federal", "source_enfant", True),
    ("aidant_enfant_federal", "montant_calcule", "2687"),
])
def test_json_combine_strict(tmp_path, cle, champ, valeur):
    e = calcul(_dossier_52000(), **profils())
    f = sauvegarder_dossier_fiscal(e.dossier, estimation=e, destination=tmp_path / "strict.json")
    brut = json.loads(f.read_text(encoding="utf-8"))
    brut[cle][champ] = valeur
    with pytest.raises(ValueError):
        dossier_fiscal_depuis_contenu(brut)


def test_sauvegarde_sans_estimation_refuse_attribution_divergente(tmp_path):
    with pytest.raises(ValueError, match="divergentes"):
        sauvegarder_dossier_fiscal(_dossier_52000(), **profils(reference_enfant="Autre"),
            destination=tmp_path / "refus.json")
    assert not (tmp_path / "refus.json").exists()
