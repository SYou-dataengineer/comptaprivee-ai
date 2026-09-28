from dataclasses import replace
from decimal import Decimal as D
import json
import fitz
import pytest
from tests.test_tax_federal_caregiver_child_integration_2025 import _profil_aidant_enfant
from tests.test_tax_federal_eligible_dependant_integration_2025 import _profil_personne_charge
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_top_up_integration_2025 import verifier_t1, dossier_70000, medical
from src.comptaprivee.tax_federal_caregiver_child_2025 import (
    AidantNaturelEnfantMoins18Federal2025 as Profil, EnfantAidant30500 as Enfant,
    montant_ligne_30500_2025 as montant, nombre_enfants_ligne_30499_2025 as nombre,
    credit_federal_aidant_enfant_moins18_2025 as credit,
    valider_aidant_naturel_enfant_moins18_federal_2025 as valider)
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calcul
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, dossier_fiscal_depuis_contenu
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025


def enfants():
    return (Enfant("enfant-a", "Enfant fictif A", "2008-01-01", _profil_aidant_enfant()),
        Enfant("enfant-b", "Enfant fictif B", "2025-12-31", _profil_aidant_enfant()))


def profil(liste=None, **kw):
    return replace(Profil(reclamer_montant=True, valide_par_comptable=True, identites_distinctes_confirmees=True,
        enfants_detailles=enfants() if liste is None else liste), **kw)


def test_deux_enfants_credit_arrondi_une_fois_y_compris_naissance_2025():
    p = profil()
    assert nombre(p) == 2 and montant(p) == D(5374) and credit(p) == D("779.23")
    assert credit(p) != sum(credit(e.profil) for e in p.enfants_detailles)
    assert montant(profil(tuple(reversed(enfants())))) == montant(p)


@pytest.mark.parametrize("kw", [{"reclamer_montant": False}, {"valide_par_comptable": False},
    {"identites_distinctes_confirmees": False}, {"enfant_reclame_30400": True},
    {"enfant_biologique_ou_adopte": 0}, {"source_enfant": "faits concurrents"},
    {"enfants_detailles": list(enfants())}])
def test_enveloppe_invalide(kw):
    with pytest.raises(ValueError): valider(profil(**kw))


@pytest.mark.parametrize("kw", [{"reference": " ENFANT-A "}, {"nom": "ENFANT FICTIF A", "naissance": "2008-01-01"},
    {"reference": ""}, {"nom": ""}, {"naissance": "2007-12-31"}, {"naissance": "2026-01-01"},
    {"naissance": "2010-02-30"}, {"naissance": "20100101"}, {"profil": profil()},
    {"profil": _profil_aidant_enfant(valide_par_comptable="oui")},
    {"profil": _profil_aidant_enfant(reclamer_montant=False)},
    {"profil": _profil_aidant_enfant(aucun_autre_reclamant_30500=False)},
    {"profil": _profil_aidant_enfant(aucun_transfert_conjoint_32600=False)},
    {"profil": _profil_aidant_enfant(aucune_garde_partagee=False)},
    {"profil": _profil_aidant_enfant(aucune_pension_alimentaire=False)},
    {"profil": _profil_aidant_enfant(enfant_avec_deux_parents_toute_annee=False)},
])
def test_fiches_invalides(kw):
    a, b = enfants()
    with pytest.raises(ValueError): valider(profil((a, replace(b, **kw))))


def test_combinaison_30400_ne_devient_pas_implicite():
    with pytest.raises(ValueError, match="Combinaison 30400/30500"):
        calcul(_dossier_52000(), aidant_enfant_federal=profil(),
            personne_charge_admissible_federale=_profil_personne_charge())


def test_estimation_topup_et_recalcul_json(tmp_path):
    d = dossier_70000()
    e = calcul(d, aidant_enfant_federal=profil(), frais_medicaux=medical())
    assert dict(e.federal.credits_federaux_complets.montants_par_ligne)["30500"] == D(5374)
    assert e.federal.top_up_credit > 0
    verifier_t1(e)
    base = calcul(d, frais_medicaux=medical())
    assert e.revenu == base.revenu and e.quebec == base.quebec
    f = sauvegarder_dossier_fiscal(d, estimation=e, destination=tmp_path / "enfants.json")
    c = dossier_fiscal_depuis_contenu(json.loads(f.read_text(encoding="utf-8")))
    assert c.aidant_enfant_federal == profil()
    assert calcul(c.dossier, aidant_enfant_federal=c.aidant_enfant_federal, frais_medicaux=medical()).federal == e.federal
    with pytest.raises(ValueError, match="divergent"):
        sauvegarder_dossier_fiscal(d, estimation=e, aidant_enfant_federal=_profil_aidant_enfant(),
            destination=tmp_path / "refus.json")


@pytest.mark.parametrize("mode", ["liste", "identite", "inconnu", "imbrique", "booleen", "sans_nouveaux_champs"])
def test_json_invalide(tmp_path, mode):
    f = sauvegarder_dossier_fiscal(_dossier_52000(), aidant_enfant_federal=profil(), destination=tmp_path / "strict.json")
    brut = json.loads(f.read_text(encoding="utf-8")); p = brut["aidant_enfant_federal"]
    if mode == "liste": p["enfants_detailles"] = {}
    if mode == "identite": p["enfants_detailles"][1]["reference"] = "enfant-a"
    if mode == "inconnu": p["enfants_detailles"][0]["montant_calcule"] = 2687
    if mode == "imbrique": p["enfants_detailles"][0]["profil"]["enfants_detailles"] = [{}]
    if mode == "booleen": p["identites_distinctes_confirmees"] = 1
    if mode == "sans_nouveaux_champs":
        fiche = p["enfants_detailles"][0]["profil"]
        for cle in ("enfants_detailles", "identites_distinctes_confirmees", "enfant_reclame_30400", "reference_enfant"): fiche.pop(cle)
        fiche["valide_par_comptable"] = "oui"
    with pytest.raises(ValueError): dossier_fiscal_depuis_contenu(brut)


def test_trace_pdf_enfants(tmp_path):
    e = calcul(_dossier_52000(), aidant_enfant_federal=profil())
    t = str(construire_trace_calcul_fiscal_2025(e))
    assert "Enfant fictif A" in t and "Enfant fictif B" in t and "5374.00" in t
    f = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "enfants.pdf")
    with fitz.open(f) as pdf:
        texte = "\n".join(p.get_text() for p in pdf)
        for p in pdf:
            assert all(0 <= b[0] < b[2] <= p.rect.width and 0 <= b[1] < b[3] <= p.rect.height for b in p.get_text("blocks"))
    for attendu in ("Enfant fictif A", "Enfant fictif B", "Nombre ligne 30499 : 2", "5374.00", "779.23"):
        assert attendu in texte


def test_ancien_json_sans_liste_et_combinaison_stockee_refusee(tmp_path):
    f = sauvegarder_dossier_fiscal(_dossier_52000(), aidant_enfant_federal=_profil_aidant_enfant(),
        destination=tmp_path / "ancien.json")
    brut = json.loads(f.read_text(encoding="utf-8"))
    brut["aidant_enfant_federal"].pop("enfants_detailles")
    brut["aidant_enfant_federal"].pop("identites_distinctes_confirmees")
    assert dossier_fiscal_depuis_contenu(brut).aidant_enfant_federal == _profil_aidant_enfant()
    with pytest.raises(ValueError, match="Combinaison 30400/30500"):
        sauvegarder_dossier_fiscal(_dossier_52000(), aidant_enfant_federal=profil(),
            personne_charge_admissible_federale=_profil_personne_charge(), destination=tmp_path / "refus.json")
    assert not (tmp_path / "refus.json").exists()
    f = sauvegarder_dossier_fiscal(_dossier_52000(), aidant_enfant_federal=profil(), destination=tmp_path / "enfants.json")
    brut = json.loads(f.read_text(encoding="utf-8"))
    autre = sauvegarder_dossier_fiscal(_dossier_52000(), personne_charge_admissible_federale=_profil_personne_charge(), destination=tmp_path / "parent.json")
    brut["personne_charge_admissible_federale"] = json.loads(autre.read_text(encoding="utf-8"))["personne_charge_admissible_federale"]
    with pytest.raises(ValueError, match="Combinaison 30400/30500"):
        dossier_fiscal_depuis_contenu(brut)
