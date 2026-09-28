from dataclasses import replace
from decimal import Decimal as D
import json
import fitz
import pytest
from tests.test_tax_federal_home_accessibility_2025 import _profil
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_top_up_integration_2025 import verifier_t1, dossier_70000, medical
from src.comptaprivee.tax_federal_home_accessibility_2025 import (
    montant_ligne_31285_2025 as montant, valider_depenses_accessibilite_domiciliaire_2025 as valider)
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calcul
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, dossier_fiscal_depuis_contenu
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025


def profil(**kw):
    p = _profil(depenses_admissibles=D(25000), aucun_partage_de_la_demande=False, partage_31285_confirme=True,
        montant_reclame_autres=D(4000), autres_participants_admissibles_confirmes=True, logement_unique_2025_confirme=True,
        reference_logement="Logement fictif A", source_partage="Entente fictive A/B admissibles, seul logement en 2025")
    return replace(p, **kw)


@pytest.mark.parametrize("total,autres,attendu", [("25000", "0", "20000"), ("25000", "4000", "16000"),
    ("12000", "4000", "8000"), ("12000", "12000", "0"), ("25000", "19999.99", "0.01"),
    ("20000", "20000", "0"), ("0.01", "0", "0.01")])
def test_feuille_federale_plafond_avant_partage(total, autres, attendu):
    p = profil(depenses_admissibles=D(total), montant_reclame_autres=D(autres))
    assert montant(p) == D(attendu)
    assert montant(p) + montant(replace(p, montant_reclame_autres=D(attendu))) == min(D(total), D(20000))


@pytest.mark.parametrize("kw", [
    {"montant_reclame_autres": D("20000.01")}, {"montant_reclame_autres": D("-0.01")},
    {"montant_reclame_autres": D("1.001")}, {"montant_reclame_autres": D("NaN")},
    {"montant_reclame_autres": 1.5}, {"autres_participants_admissibles_confirmes": False},
    {"autres_participants_admissibles_confirmes": "oui"}, {"partage_31285_confirme": False},
    {"partage_31285_confirme": 1}, {"depenses_admissibles": D(3999)},
    {"depenses_admissibles": D("1E9999")}, {"depenses_admissibles": D("sNaN")},
    {"depenses_admissibles": D(0)}, {"depenses_admissibles": D("25000.001")},
    {"aucun_partage_de_la_demande": True}, {"logement_unique_2025_confirme": False},
    {"logement_unique_2025_confirme": 1}, {"reclamer_montant": False},
    {"reference_logement": ""}, {"source_partage": " "}, {"valide_par_comptable": False},
    {"demande_pour_soi_meme": False}, {"logement_propriete_du_contribuable": False},
    {"age_65_plus_fin_annee": False}, {"aucune_part_entreprise_ou_location": False}, {"source_renovation": 1},
])
def test_partage_non_admissible_ou_contradictoire_refuse(kw):
    with pytest.raises(ValueError): valider(profil(**kw))


def test_estimation_topup_et_json(tmp_path):
    d = dossier_70000()
    e = calcul(d, accessibilite_domiciliaire_federale=profil(), frais_medicaux=medical())
    assert dict(e.federal.credits_federaux_complets.montants_par_ligne)["31285"] == D(16000)
    assert e.federal.top_up_credit > 0
    verifier_t1(e)
    base = calcul(d, frais_medicaux=medical())
    assert e.revenu == base.revenu and e.quebec == base.quebec
    f = sauvegarder_dossier_fiscal(d, estimation=e, destination=tmp_path / "partage_accessibilite.json")
    brut = json.loads(f.read_text(encoding="utf-8"))
    assert brut["accessibilite_domiciliaire_federale"]["depenses_admissibles"] == "25000"
    c = dossier_fiscal_depuis_contenu(brut)
    assert c.accessibilite_domiciliaire_federale == profil()
    assert calcul(c.dossier, accessibilite_domiciliaire_federale=c.accessibilite_domiciliaire_federale, frais_medicaux=medical()).federal == e.federal
    with pytest.raises(ValueError, match="divergent"):
        sauvegarder_dossier_fiscal(d, estimation=e, accessibilite_domiciliaire_federale=_profil(), destination=tmp_path / "refus.json")


@pytest.mark.parametrize("champ,valeur", [("partage_31285_confirme", "oui"), ("autres_participants_admissibles_confirmes", 1),
    ("montant_reclame_autres", 1.5), ("montant_reclame_autres", True),
    ("reference_logement", 123), ("valide_par_comptable", "oui"), ("montant_calcule", "6000")])
def test_json_strict(tmp_path, champ, valeur):
    f = sauvegarder_dossier_fiscal(_dossier_52000(), accessibilite_domiciliaire_federale=profil(), destination=tmp_path / "strict.json")
    brut = json.loads(f.read_text(encoding="utf-8")); brut["accessibilite_domiciliaire_federale"][champ] = valeur
    with pytest.raises(ValueError): dossier_fiscal_depuis_contenu(brut)


def test_ancien_json_non_partage_conserve_son_montant(tmp_path):
    f = sauvegarder_dossier_fiscal(_dossier_52000(), accessibilite_domiciliaire_federale=_profil(depenses_admissibles=D(5000)), destination=tmp_path / "ancien.json")
    brut = json.loads(f.read_text(encoding="utf-8"))
    for nom in ("partage_31285_confirme", "montant_reclame_autres", "autres_participants_admissibles_confirmes", "reference_logement", "source_partage", "logement_unique_2025_confirme"):
        brut["accessibilite_domiciliaire_federale"].pop(nom)
    assert montant(dossier_fiscal_depuis_contenu(brut).accessibilite_domiciliaire_federale) == D(5000)


def test_trace_pdf_partage(tmp_path):
    e = calcul(_dossier_52000(), accessibilite_domiciliaire_federale=profil())
    t = str(construire_trace_calcul_fiscal_2025(e))
    assert "Logement fictif A" in t and "4000.00" in t and "16000.00" in t
    f = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "partage_accessibilite.pdf")
    with fitz.open(f) as pdf:
        texte = "\n".join(p.get_text() for p in pdf)
        for p in pdf:
            assert all(0 <= b[0] < b[2] <= p.rect.width and 0 <= b[1] < b[3] <= p.rect.height for b in p.get_text("blocks"))
    assert "Logement fictif A" in texte and "16000.00" in texte
    assert "Aucun partage de la demande ligne 31285 : oui" not in texte


def test_ciph_et_cumul_medical_2025_conserves():
    p = profil(age_65_plus_fin_annee=False, admissible_ciph=True)
    e = calcul(dossier_70000(), accessibilite_domiciliaire_federale=p, frais_medicaux=medical())
    lignes = dict(e.federal.credits_federaux_complets.montants_par_ligne)
    assert lignes["31285"] == D(16000)
    assert lignes["33200"] > 0
    verifier_t1(e)
