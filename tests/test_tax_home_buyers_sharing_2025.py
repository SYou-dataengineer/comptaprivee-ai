from dataclasses import replace
from decimal import Decimal as D
import json
import fitz
import pytest
from tests.test_tax_federal_home_buyers_2025 import _profil
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_top_up_integration_2025 import verifier_t1, dossier_70000, medical
from src.comptaprivee.tax_federal_home_buyers_2025 import (
    montant_ligne_31270_2025 as montant, valider_montant_achat_habitation_2025 as valider)
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calcul
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, dossier_fiscal_depuis_contenu
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025


def profil(**kw):
    p = _profil(montant_reclame=D(0), aucun_partage_du_montant=False, partage_31270_confirme=True,
        montant_attribue_autres_acquereurs=D(4000), autres_acquereurs_admissibles_confirmes=True,
        reference_habitation="Habitation fictive A", source_partage="Entente fictive des acquéreurs admissibles A et B")
    return replace(p, **kw)


@pytest.mark.parametrize("autres,attendu", [("0", "10000"), ("4000", "6000"), ("9999.99", "0.01"), ("10000", "0")])
def test_solde_commun_et_part_complementaire(autres, attendu):
    p = profil(montant_attribue_autres_acquereurs=D(autres))
    assert montant(p) == D(attendu)
    assert montant(replace(p, montant_attribue_autres_acquereurs=D(attendu))) + montant(p) == D(10000)


@pytest.mark.parametrize("kw", [
    {"montant_attribue_autres_acquereurs": D("10000.01")}, {"montant_attribue_autres_acquereurs": D("-0.01")},
    {"montant_attribue_autres_acquereurs": D("1.001")}, {"montant_attribue_autres_acquereurs": D("NaN")},
    {"montant_attribue_autres_acquereurs": 1.5}, {"autres_acquereurs_admissibles_confirmes": False},
    {"autres_acquereurs_admissibles_confirmes": "oui"}, {"partage_31270_confirme": False},
    {"partage_31270_confirme": 1}, {"montant_reclame": D(6000)},
    {"montant_reclame": D("1E9999")}, {"montant_reclame": D("sNaN")}, {"aucun_partage_du_montant": True},
    {"reclamer_montant": False}, {"reference_habitation": ""}, {"source_partage": " "},
    {"valide_par_comptable": False}, {"premier_acheteur_confirme": False},
    {"habitation_enregistree_nom_contribuable_ou_conjoint": False},
    {"aucune_exception_handicap_utilisee": False}, {"source_habitation": 1},
])
def test_partage_non_admissible_ou_contradictoire_refuse(kw):
    with pytest.raises(ValueError): valider(profil(**kw))


def test_estimation_topup_et_json(tmp_path):
    d = dossier_70000()
    e = calcul(d, achat_habitation_federal=profil(), frais_medicaux=medical())
    assert dict(e.federal.credits_federaux_complets.montants_par_ligne)["31270"] == D(6000)
    assert e.federal.top_up_credit > 0
    verifier_t1(e)
    base = calcul(d, frais_medicaux=medical())
    assert e.revenu == base.revenu and e.quebec == base.quebec
    f = sauvegarder_dossier_fiscal(d, estimation=e, destination=tmp_path / "partage_habitation.json")
    brut = json.loads(f.read_text(encoding="utf-8"))
    assert brut["achat_habitation_federal"]["montant_reclame"] == "0"
    c = dossier_fiscal_depuis_contenu(brut)
    assert c.achat_habitation_federal == profil()
    assert calcul(c.dossier, achat_habitation_federal=c.achat_habitation_federal, frais_medicaux=medical()).federal == e.federal
    with pytest.raises(ValueError, match="divergent"):
        sauvegarder_dossier_fiscal(d, estimation=e, achat_habitation_federal=_profil(), destination=tmp_path / "refus.json")


@pytest.mark.parametrize("champ,valeur", [("partage_31270_confirme", "oui"), ("autres_acquereurs_admissibles_confirmes", 1),
    ("montant_attribue_autres_acquereurs", 1.5), ("montant_attribue_autres_acquereurs", True),
    ("reference_habitation", 123), ("valide_par_comptable", "oui"), ("montant_calcule", "6000")])
def test_json_strict(tmp_path, champ, valeur):
    f = sauvegarder_dossier_fiscal(_dossier_52000(), achat_habitation_federal=profil(), destination=tmp_path / "strict.json")
    brut = json.loads(f.read_text(encoding="utf-8")); brut["achat_habitation_federal"][champ] = valeur
    with pytest.raises(ValueError): dossier_fiscal_depuis_contenu(brut)


def test_ancien_json_non_partage_conserve_son_montant(tmp_path):
    f = sauvegarder_dossier_fiscal(_dossier_52000(), achat_habitation_federal=_profil(montant_reclame=D(5000)), destination=tmp_path / "ancien.json")
    brut = json.loads(f.read_text(encoding="utf-8"))
    for nom in ("partage_31270_confirme", "montant_attribue_autres_acquereurs", "autres_acquereurs_admissibles_confirmes", "reference_habitation", "source_partage"):
        brut["achat_habitation_federal"].pop(nom)
    assert montant(dossier_fiscal_depuis_contenu(brut).achat_habitation_federal) == D(5000)


def test_trace_pdf_partage(tmp_path):
    e = calcul(_dossier_52000(), achat_habitation_federal=profil())
    t = str(construire_trace_calcul_fiscal_2025(e))
    assert "Habitation fictive A" in t and "4000.00" in t and "6000.00" in t
    f = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "partage_habitation.pdf")
    with fitz.open(f) as pdf:
        texte = "\n".join(p.get_text() for p in pdf)
        for p in pdf:
            assert all(0 <= b[0] < b[2] <= p.rect.width and 0 <= b[1] < b[3] <= p.rect.height for b in p.get_text("blocks"))
    assert "Habitation fictive A" in texte and "6000.00" in texte
    assert "Aucun partage du montant ligne 31270 : oui" not in texte
