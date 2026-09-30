from dataclasses import replace
from decimal import Decimal as D
import json
import fitz
import pytest
from tests.test_tax_quebec_volunteers_2025 import profil
from tests.test_tax_volunteers_2025 import profil as federal
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_workers_benefit_2025 import dossier_20000
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calcul, formater_estimation_fiscale_2025
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, dossier_fiscal_depuis_contenu
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025, formater_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025


@pytest.mark.parametrize("dossier", [_dossier_52000, dossier_20000])
def test_390_reduit_quebec_seulement_pas_de_double_compte(dossier):
    a = calcul(dossier(), benevoles=federal())
    b = calcul(dossier(), benevoles=federal(), volontaires_quebec=profil())
    assert a.federal == b.federal and a.revenu == b.revenu and a.base == b.base
    utilise = min(a.quebec.impot_quebec_preliminaire, D("756.56"))
    assert a.quebec.impot_quebec_preliminaire - b.quebec.impot_quebec_preliminaire == utilise
    assert b.rapprochement.remboursement_estime-b.rapprochement.solde_estime == a.rapprochement.remboursement_estime-a.rapprochement.solde_estime+utilise
    assert a.rapprochement.abattement_quebec == b.rapprochement.abattement_quebec
    assert b.resultat_volontaires_quebec.credit_ligne_390 == D("756.56")


def test_json_recalcul_et_ancien_dossier(tmp_path):
    d = _dossier_52000()
    e = calcul(d, benevoles=federal(), volontaires_quebec=profil())
    f = sauvegarder_dossier_fiscal(d, estimation=e, destination=tmp_path/"390.json")
    brut = json.loads(f.read_text(encoding="utf-8"))
    c = dossier_fiscal_depuis_contenu(brut)
    assert calcul(c.dossier, benevoles=c.benevoles, volontaires_quebec=c.volontaires_quebec) == e
    with pytest.raises(ValueError, match="divergent"):
        sauvegarder_dossier_fiscal(d, estimation=e, volontaires_quebec=profil(source="Autre"), destination=tmp_path/"refus.json")
    brut.pop("volontaires_quebec")
    c = dossier_fiscal_depuis_contenu(brut)
    assert not c.volontaires_quebec.activer
    assert calcul(c.dossier, benevoles=c.benevoles).resultat_volontaires_quebec.credit_ligne_390 == 0


def sorties(e, tmp_path):
    f = exporter_rapport_fiscal_pdf_2025(e, tmp_path/"audit.pdf")
    with fitz.open(f) as pdf:
        texte = " ".join(p.get_text() for p in pdf)
        for p in pdf:
            assert all(0 <= b[0] < b[2] <= p.rect.width for b in p.get_text("blocks"))
    return [" ".join(s.split()) for s in (texte, formater_estimation_fiscale_2025(e), formater_trace_calcul_fiscal_2025(construire_trace_calcul_fiscal_2025(e)))]


def test_390_trace_pdf_audit_et_non_remboursable(tmp_path):
    e = calcul(_dossier_52000(), benevoles=federal(), volontaires_quebec=profil(source="W"*2000))
    for s in sorties(e, tmp_path):
        for attendu in ("Ligne 390", "756.56", "non remboursable", "L-2", "200"):
            assert attendu in s


@pytest.mark.parametrize("frais", ["0", "10000"])
def test_bouclier_signale_pour_garde_seule_meme_credit_nul(tmp_path, frais):
    from tests.test_tax_quebec_childcare_2025 import profil as garde, enfant
    e = calcul(_dossier_52000(), frais_garde_quebec=garde(enfants=(enfant(frais_rl24_e=D(frais)),)))
    assert not e.prime_travail_quebec.activer
    for s in sorties(e, tmp_path):
        assert "Bouclier fiscal 460 non calculé" in s
        assert "2024 nécessaires" in s
    assert e.resultat_garde_quebec.credit_ligne_455 == (D(0) if frais == "0" else D(7100))



def test_390_impot_nul_ne_cree_pas_de_remboursement():
    d = _dossier_52000()
    d = replace(d, donnees_validees=tuple(replace(v, valeur_validee=D(0)) for v in d.donnees_validees))
    e = calcul(d, benevoles=federal(), volontaires_quebec=profil())
    assert e.quebec.impot_quebec_preliminaire == 0
    assert e.resultat_volontaires_quebec.credit_ligne_390 == D("756.56")
    assert e.resultat_volontaires_quebec.reduction_impot_effective == 0
    assert e.rapprochement.remboursement_estime == e.rapprochement.solde_estime == 0
