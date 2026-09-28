from dataclasses import replace
from decimal import Decimal as D
import json

import fitz
import pytest

from src.comptaprivee.tax_political_contributions_2025 import (
    ContributionsPolitiques2025, RecuPolitique2025, CONFIRMATIONS_POLITIQUES,
    calculer_contributions_politiques_2025, credit_politique_federal_2025,
    politiques_vers_dict, politiques_depuis_dict,
)
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calcul
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from src.comptaprivee.tax_reconciliation_2025 import calculer_rapprochement_fiscal_2025
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_top_up_integration_2025 import verifier_t1


def recu(**kw):
    v = dict(date_paiement="2025-05-01", donateur="contribuable", nom_donateur="Client Test",
        beneficiaire="Parti fictif", type_beneficiaire="parti", montant=D(1400), avantage=D(100), source="Reçu fictif A")
    v.update(kw)
    return RecuPolitique2025(**v)


def profil(**kw):
    v = dict(recus=(recu(),), source="Choix et validation fictifs", **{n: True for n in CONFIRMATIONS_POLITIQUES})
    v.update(kw)
    return ContributionsPolitiques2025(**v)


def resultat(p=None, **kw):
    return calculer_contributions_politiques_2025(p if p is not None else profil(), client="Client Test", **kw)


@pytest.mark.parametrize("montant,attendu", [
    ("0", "0"), ("0.01", "0.01"), ("399.99", "299.99"), ("400", "300"),
    ("400.01", "300.01"), ("749.99", "475.00"), ("750", "475"),
    ("750.01", "475"), ("1000", "558.33"), ("1274.99", "650"), ("1275", "650"), ("1400", "650"),
])
def test_paliers_taux_legal_et_arrondi(montant, attendu):
    assert credit_politique_federal_2025(D(montant)) == D(attendu)


def test_vide_et_annees():
    assert resultat(ContributionsPolitiques2025(), annee=2024).ligne_41000 == 0
    with pytest.raises(ValueError, match="2025"):
        resultat(annee=2024)
    assert resultat(profil(recus=(recu(avantage=D(1400)),))).ligne_40900 == 0


def test_plusieurs_recus_conjoint_et_avantages():
    p = profil(nom_conjoint="Conjoint fictif", recus=(recu(montant=D(400), avantage=D(50)),
        recu(donateur="conjoint", nom_donateur="Conjoint fictif", type_beneficiaire="candidat", source="B", montant=D(500), avantage=D(100))))
    r = resultat(p)
    assert (r.paiements, r.avantages, r.ligne_40900, r.ligne_41000) == (D(900), D(150), D(750), D(475))


@pytest.mark.parametrize("valeur", [D("NaN"), D("sNaN"), D("Infinity"), D("-Infinity"), D(-1), D("1.001"), D("1e100"), "100", None, True])
@pytest.mark.parametrize("nom", ["montant", "avantage"])
def test_montants_invalides(valeur, nom):
    with pytest.raises(ValueError):
        resultat(profil(recus=(recu(**{nom: valeur}),)))


@pytest.mark.parametrize("kw", [dict(date_paiement="2024-12-31"), dict(date_paiement="2026-01-01"),
    dict(date_paiement="2025-02-30"), dict(date_paiement="20250501"), dict(date_paiement=None),
    dict(donateur="parent"), dict(type_beneficiaire="provincial"), dict(source=""),
    dict(nom_donateur="Autre personne"), dict(beneficiaire=None), dict(montant=D(0)), dict(avantage=D(1401))])
def test_recus_invalides(kw):
    with pytest.raises(ValueError):
        resultat(profil(recus=(recu(**kw),)))


@pytest.mark.parametrize("kw", [dict(source=""), dict(source=None), dict(nom_conjoint="Autre"),
    dict(recus=[recu()]), dict(recus=(recu(), recu(source=" REÇU  FICTIF A "))),
    dict(recus=(recu(donateur="conjoint"),)),
    dict(nom_conjoint="Client Test", recus=(recu(donateur="conjoint"),))])
def test_profils_invalides(kw):
    with pytest.raises(ValueError):
        resultat(profil(**kw))


@pytest.mark.parametrize("nom", list(CONFIRMATIONS_POLITIQUES))
@pytest.mark.parametrize("valeur", [False, "true", 1])
def test_confirmations(nom, valeur):
    with pytest.raises(ValueError):
        resultat(profil(**{nom: valeur}))


def test_estimation_credit_hors_33500_et_base_abattement():
    a = calcul(_dossier_52000())
    e = calcul(_dossier_52000(), contributions_politiques=profil())
    assert e.revenu == a.revenu and e.federal == a.federal and e.quebec == a.quebec
    assert e.rapprochement.abattement_quebec == a.rapprochement.abattement_quebec
    assert a.rapprochement.impot_total_preliminaire - e.rapprochement.impot_total_preliminaire == D(650)
    assert e.rapprochement.credit_politique_utilise == D(650)
    verifier_t1(e)


def test_impot_faible_avances_act_apres_plafonnement():
    from tests.test_tax_workers_benefit_2025 import dossier_20000, profil as act
    e = calcul(dossier_20000(), contributions_politiques=profil(), allocation_travailleurs=act(avances_rc210_case10=D(500)))
    f = e.rapprochement
    # Impôt brut et crédits sont arrondis séparément avant la soustraction.
    assert f.impot_federal_apres_credit_etranger == D("2876.08") - D("2733.51")
    assert f.credit_politique_utilise == D("142.57")
    assert f.impot_federal_ligne_41700 == 0
    assert f.avances_act_ligne_41500 == D(500)
    assert f.impot_federal_apres_abattement == D(500) - f.abattement_quebec
    verifier_t1(e)


def test_credit_etranger_avant_politique_et_abattement_remboursable_preserve():
    e = calcul(_dossier_52000())
    federal = replace(e.federal, impot_federal_de_base=D(1000), credit_etranger_ligne_40500=D(900))
    r = calculer_rapprochement_fiscal_2025(e.base, federal, e.quebec, credit_politique=D(650))
    assert r.impot_federal_apres_credit_etranger == D(100)
    assert r.credit_politique_utilise == D(100)
    assert r.impot_federal_ligne_41700 == 0
    assert r.abattement_quebec == D(165)
    assert r.impot_federal_apres_abattement == D(-165)


@pytest.mark.parametrize("credit", [D("NaN"), D("sNaN"), D("Infinity"), D(-1), D("650.01"), D("1.001"), D("1e100"), True, "100"])
def test_rapprochement_refuse_credit_invalide(credit):
    e = calcul(_dossier_52000())
    with pytest.raises(ValueError):
        calculer_rapprochement_fiscal_2025(e.base, e.federal, e.quebec, credit_politique=credit)


def test_conjoint_et_act_individuelle_refuses():
    from tests.test_tax_workers_benefit_2025 import dossier_20000, profil as act
    p = profil(nom_conjoint="Conjoint fictif", recus=(recu(donateur="conjoint", nom_donateur="Conjoint fictif"),))
    with pytest.raises(ValueError, match="profil familial"):
        calcul(dossier_20000(), contributions_politiques=p, allocation_travailleurs=act())


def test_stockage_brut_ancien_divergence_et_recalcul(tmp_path):
    e = calcul(_dossier_52000(), contributions_politiques=profil())
    f = sauvegarder_dossier_fiscal(e.dossier, estimation=e, destination=tmp_path / "cas.json")
    c = charger_dossier_fiscal(f)
    assert c.contributions_politiques == profil()
    assert calcul(c.dossier, contributions_politiques=c.contributions_politiques) == e
    brut = json.loads(f.read_text(encoding="utf-8"))
    assert brut["contributions_politiques"]["recus"][0]["montant"] == "1400.00"
    assert "ligne_41000" not in json.dumps(brut["contributions_politiques"])
    with pytest.raises(ValueError, match="divergent"):
        sauvegarder_dossier_fiscal(e.dossier, estimation=e, contributions_politiques=ContributionsPolitiques2025(), destination=f)
    del brut["contributions_politiques"]
    f.write_text(json.dumps(brut), encoding="utf-8")
    assert charger_dossier_fiscal(f).contributions_politiques == ContributionsPolitiques2025()


@pytest.mark.parametrize("brut", [[], {"inconnu": 1}, {"recus": {}}, {"recus": [None]}, {"recus": [{"inconnu": 1}]}, {"recus_officiels": "true"}])
def test_structure_json_invalide(brut):
    with pytest.raises(ValueError):
        politiques_depuis_dict(brut)


@pytest.mark.parametrize("v", ["NaN", "Infinity", "-1", "1.001", "texte", True, 1.2, None])
def test_montants_json_invalides(v):
    brut = politiques_vers_dict(profil())
    brut["recus"][0]["montant"] = v
    with pytest.raises(ValueError):
        politiques_depuis_dict(brut)


def test_trace_et_pdf(tmp_path):
    e = calcul(_dossier_52000(), contributions_politiques=profil())
    trace = construire_trace_calcul_fiscal_2025(e)
    credit = next(l for l in trace.lignes if l.libelle == "Crédit politique — 41000")
    apres = next(l for l in trace.lignes if l.libelle == "Impôt fédéral après abattement")
    assert credit.montant == D(650) and credit.ordre < apres.ordre
    assert "41000" in apres.formule
    assert [l.ordre for l in trace.lignes] == list(range(1, len(trace.lignes) + 1))
    f = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "rapport.pdf")
    with fitz.open(f) as pdf:
        texte = "\n".join(page.get_text() for page in pdf)
        assert "40900" in texte and "41000" in texte and "650.00" in texte and "Parti fictif" in texte
        for page in pdf:
            for x0, y0, x1, y1, *_ in page.get_text("blocks"):
                assert 0 <= x0 < x1 <= page.rect.width
                assert 0 <= y0 < y1 <= page.rect.height


def test_dossier_conjoint_refuse_recu_deja_reclame(tmp_path):
    from tests.test_tax_spouse_transfer_2025 import profil as transfert
    from src.comptaprivee.tax_spouse_transfer_2025 import instantane_conjoint_2025
    p = transfert(tmp_path)
    brut = json.loads(p.dossier_conjoint_json)
    recu_conjoint = recu(nom_donateur="Conjoint fictif")
    brut["contributions_politiques"] = politiques_vers_dict(profil(recus=(recu_conjoint,)))
    p = replace(p, dossier_conjoint_json=instantane_conjoint_2025(brut))
    revendication = profil(nom_conjoint="Conjoint fictif", recus=(replace(recu_conjoint, donateur="conjoint"),))
    with pytest.raises(ValueError, match="deux dossiers"):
        calcul(_dossier_52000(), contributions_politiques=revendication, transfert_conjoint=p)
    # Un autre reçu du contribuable reste combinable au transfert du conjoint.
    e = calcul(_dossier_52000(), contributions_politiques=profil(recus=(recu(source="Autre reçu"),)), transfert_conjoint=p)
    sans = calcul(_dossier_52000(), transfert_conjoint=p)
    assert e.resultat_transfert_conjoint == sans.resultat_transfert_conjoint
    assert e.resultat_contributions_politiques.ligne_41000 == D(650)
    verifier_t1(e)


def test_identite_conjoint_importe_et_recu_divergents(tmp_path):
    from tests.test_tax_spouse_transfer_2025 import profil as transfert
    politique = profil(nom_conjoint="Autre conjoint", recus=(recu(donateur="conjoint", nom_donateur="Autre conjoint"),))
    with pytest.raises(ValueError, match="diffère"):
        calcul(_dossier_52000(), contributions_politiques=politique, transfert_conjoint=transfert(tmp_path))
