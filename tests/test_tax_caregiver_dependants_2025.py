from dataclasses import replace
from decimal import Decimal as D
import json
import fitz
import pytest
from tests.test_tax_federal_caregiver_other_dependant_2025 import _profil
from tests.test_tax_caregiver_sharing_2025 import profil as partage
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_top_up_integration_2025 import verifier_t1, dossier_70000, medical
from src.comptaprivee.tax_federal_caregiver_other_dependant_2025 import (
    AidantNaturelAutrePersonneChargeFederal2025 as Profil, PersonneAidant30450 as Personne,
    montant_ligne_30450_2025 as montant, nombre_personnes_charge_ligne_51120_2025 as nombre,
    credit_federal_ligne_30450_2025 as credit, valider_aidant_naturel_30450_2025 as valider)
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calcul
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, dossier_fiscal_depuis_contenu
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025


def personnes():
    return (Personne("parent-a", "Parent fictif A", "1950-03-04", _profil(revenu_net_personne_ligne_23600=D("0"))),
        Personne("parent-b", "Parent fictif B", "1953-04-05", partage(reference_personne="parent-b")))


def profil(liste=None, **kw):
    p = Profil(reclamer_montant=True, valide_par_comptable=True, identites_distinctes_confirmees=True,
        personnes_detaillees=personnes() if liste is None else liste)
    return replace(p, **kw)


def test_plafond_par_personne_et_partage():
    p = profil()
    assert montant(p) == D("10899") == D(8601) + D(2298)
    assert nombre(p) == 2 and credit(p) == D("1580.36")
    assert montant(profil(tuple(reversed(p.personnes_detaillees)))) == montant(p)


def test_arrondi_unique_sur_base_totale():
    p = profil(tuple(replace(x, profil=_profil(revenu_net_personne_ligne_23600=D("28796.99"))) for x in personnes()))
    assert montant(p) == D("2.02") and credit(p) == D("0.29")
    assert credit(p) != sum(credit(x.profil) for x in p.personnes_detaillees)


def test_51120_exclut_part_entierement_attribuee_ailleurs():
    a, b = personnes()
    p = profil((a, replace(b, profil=replace(b.profil, montant_attribue_autres_soutiens=D("3798")))))
    assert montant(p) == D(8601) and nombre(p) == 1


@pytest.mark.parametrize("kw", [{"reclamer_montant": False}, {"valide_par_comptable": False},
    {"identites_distinctes_confirmees": False}, {"lien_personne": "parent"},
    {"revenu_net_personne_ligne_23600": D(1)}, {"age_18_ans_ou_plus": 0},
    {"personnes_detaillees": list(personnes())}])
def test_enveloppe_invalide(kw):
    with pytest.raises(ValueError):
        valider(profil(**kw))


@pytest.mark.parametrize("kw", [{"reference": " PARENT-A "}, {"nom": " PARENT FICTIF A ", "naissance": "1950-03-04"},
    {"reference": ""}, {"nom": ""}, {"naissance": "2008-01-01"}, {"naissance": "2000-02-30"},
    {"naissance": "20000101"}, {"profil": profil()}, {"profil": _profil(valide_par_comptable="oui")},
    {"profil": _profil(revenu_net_personne_ligne_23600=D("NaN"))},
    {"profil": _profil(reclamer_montant=False)}, {"profil": partage(reference_personne="autre")},
    {"profil": _profil(aucune_reclamation_ligne_30300_30400_pour_personne=False)}])
def test_identites_et_fiches_invalides(kw):
    a, b = personnes()
    with pytest.raises(ValueError):
        valider(profil((a, replace(b, **kw))))


def test_estimation_revenus_topup_et_json(tmp_path):
    d = dossier_70000()
    e = calcul(d, aidant_autre_personne_charge_federal=profil(), frais_medicaux=medical())
    assert dict(e.federal.credits_federaux_complets.montants_par_ligne)["30450"] == D(10899)
    verifier_t1(e)
    assert e.federal.top_up_credit > 0
    base = calcul(d, frais_medicaux=medical())
    assert e.revenu == base.revenu and e.quebec == base.quebec
    f = sauvegarder_dossier_fiscal(d, estimation=e, destination=tmp_path / "personnes.json")
    brut = json.loads(f.read_text(encoding="utf-8"))
    c = dossier_fiscal_depuis_contenu(brut)
    assert c.aidant_autre_personne_charge_federal == profil()
    assert calcul(d, aidant_autre_personne_charge_federal=c.aidant_autre_personne_charge_federal,
        frais_medicaux=medical()).federal == e.federal
    with pytest.raises(ValueError, match="divergent"):
        sauvegarder_dossier_fiscal(d, estimation=e, destination=tmp_path / "refus.json",
            aidant_autre_personne_charge_federal=_profil())


@pytest.mark.parametrize("mode", ["liste", "inconnu", "booleen", "imbrique", "identite", "decimal"])
def test_json_corrompu(tmp_path, mode):
    f = sauvegarder_dossier_fiscal(_dossier_52000(), aidant_autre_personne_charge_federal=profil(),
        destination=tmp_path / "strict.json")
    brut = json.loads(f.read_text(encoding="utf-8"))
    p = brut["aidant_autre_personne_charge_federal"]
    if mode == "liste": p["personnes_detaillees"] = {}
    if mode == "inconnu": p["personnes_detaillees"][0]["montant_calcule"] = "8601"
    if mode == "booleen": p["identites_distinctes_confirmees"] = 1
    if mode == "imbrique": p["personnes_detaillees"][0]["profil"]["personnes_detaillees"] = [{"reference": "x"}]
    if mode == "identite": p["personnes_detaillees"][1]["reference"] = "parent-a"
    if mode == "decimal": p["personnes_detaillees"][0]["profil"]["revenu_net_personne_ligne_23600"] = 0.1
    with pytest.raises(ValueError): dossier_fiscal_depuis_contenu(brut)


def test_trace_pdf_individuels(tmp_path):
    e = calcul(_dossier_52000(), aidant_autre_personne_charge_federal=profil())
    t = str(construire_trace_calcul_fiscal_2025(e))
    assert "Parent fictif A" in t and "Parent fictif B" in t and "10899.00" in t
    f = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "personnes.pdf")
    with fitz.open(f) as pdf:
        texte = "\n".join(p.get_text() for p in pdf)
        for p in pdf:
            assert all(0 <= b[0] < b[2] <= p.rect.width and 0 <= b[1] < b[3] <= p.rect.height for b in p.get_text("blocks"))
    for attendu in ("Parent fictif A", "Parent fictif B", "10899.00", "Nombre ligne 51120 : 2"):
        assert attendu in texte
    assert "une seule autre personne" not in texte


def test_age_limite_et_exception_residence_enfant():
    a = Personne("enfant", "Enfant fictif", "2007-12-31", _profil(lien_personne="enfant",
        resident_canada_au_moins_un_moment_2025=False))
    assert montant(profil((a,))) == D("3798")
    with pytest.raises(ValueError, match="résidé au Canada"):
        valider(profil((replace(a, profil=replace(a.profil, lien_personne="parent")),)))


def test_fiche_detaillee_sans_champs_recents_reste_stricte(tmp_path):
    f = sauvegarder_dossier_fiscal(_dossier_52000(), aidant_autre_personne_charge_federal=profil(),
        destination=tmp_path / "strict_ancien_format.json")
    brut = json.loads(f.read_text(encoding="utf-8"))
    p = brut["aidant_autre_personne_charge_federal"]["personnes_detaillees"][0]["profil"]
    for champ in ("partage_30450_confirme", "montant_attribue_autres_soutiens", "reference_personne", "source_partage",
                  "personnes_detaillees", "identites_distinctes_confirmees"):
        p.pop(champ)
    p["valide_par_comptable"] = "oui"
    with pytest.raises(ValueError, match="Confirmation 30450 invalide"):
        dossier_fiscal_depuis_contenu(brut)
