from dataclasses import replace, fields
from decimal import Decimal as D
import inspect
import json

import pytest

from src.comptaprivee.tax_spouse_transfer_2025 import (
    TransfertConjointFederal2025, CONFIRMATIONS_TRANSFERT_CONJOINT,
    calculer_annexe2_2025, calculer_transfert_conjoint_2025,
    instantane_conjoint_2025, valider_transfert_conjoint_2025,
)
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calcul
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal, DossierFiscalEnregistre
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_interest_income_2025 import dossier_interets, profil_interets
from tests.test_tax_federal_age_pension_integration_2025 import _profil_age_federal
from tests.test_tax_federal_top_up_integration_2025 import verifier_t1


def profil(tmp_path, **kw):
    d = replace(dossier_interets("10000"), client="Conjoint fictif")
    e = calcul(d, profil_interets=profil_interets(),
        credits_federaux_age_pension=_profil_age_federal(revenu_net_ligne_23600=D(10000)))
    f = sauvegarder_dossier_fiscal(d, estimation=e, destination=tmp_path / "conjoint.json",
        credits_federaux_age_pension=e.credits_federaux_age_pension,
        profil_interets=profil_interets())
    valeurs = dict(activer=True, beneficiaire="Client Test", dossier_conjoint_json=instantane_conjoint_2025(json.loads(f.read_text(encoding="utf-8"))),
        source="Dossier synthétique avant transfert et autorisation",
        **{n: True for n in CONFIRMATIONS_TRANSFERT_CONJOINT})
    valeurs.update(kw)
    return TransfertConjointFederal2025(**valeurs)


def annexe(**kw):
    valeurs = dict(revenu_imposable=D(20000), impot_brut=D(2900),
        montants_par_ligne=(("30000", D(16129)), ("30100", D(9028)), ("31400", D(2000))))
    valeurs.update(kw)
    return calculer_annexe2_2025(**valeurs)


def test_annexe_complete_et_reduction():
    r = annexe()
    assert r.total_ligne_6 == D(11028)
    assert r.total_ligne_11 == D(16129)
    assert r.reduction_36100 == D(3871)
    assert r.ligne_32600 == D(7157)


@pytest.mark.parametrize("revenu,brut,equivalent", [("57375", "8319.38", "57375"), ("57375.01", "8319.38", "57375.03"), ("100000", "17057.50", "117637.93")])
def test_equivalent_t1_quebec(revenu, brut, equivalent):
    r = annexe(revenu_imposable=D(revenu), impot_brut=D(brut))
    assert r.equivalent_ligne_7 == D(equivalent)
    assert r.ligne_32600 == 0


def test_ligne100_exclut_autres_credits_et_scolarite_reportee():
    montants = (("30000", D(16129)), ("30100", D(9028)), ("30500", D(2687)),
        ("31400", D(2000)), ("31600", D(10138)), ("30800", D(1000)),
        ("31200", D(200)), ("31205", D(100)), ("31260", D(1471)),
        ("31270", D(1000)), ("31285", D(500)), ("31300", D(300)),
        ("31900", D(999)), ("32400", D(999)), ("30300", D(999)),
        ("32300", D(1200)), ("33200", D(999)))
    r = annexe(montants_par_ligne=montants, scolarite_designee=D(1500))
    assert r.base_ligne_100 == D(4571)
    assert r.total_ligne_6 == D(25353)
    assert r.total_ligne_11 == D(21900)
    assert r.reduction_36100 == 0
    assert r.ligne_32600 == D(25353)


@pytest.mark.parametrize("champ", ["revenu_imposable", "impot_brut", "scolarite_designee"])
@pytest.mark.parametrize("valeur", [D("NaN"), D("sNaN"), D("Infinity"), D("-Infinity"), D(-1), D("1e100"), "1", None])
def test_montants_invalides(champ, valeur):
    with pytest.raises(ValueError):
        annexe(**{champ: valeur})


def test_lignes_dupliquees_et_plafonds():
    for kw in (dict(montants_par_ligne=(("30000", D(1)), ("30000", D(1)))),
               dict(montants_par_ligne=(("31400", D(2001)),)), dict(scolarite_designee=D(5001))):
        with pytest.raises(ValueError):
            annexe(**kw)


def test_profil_vide():
    assert calculer_transfert_conjoint_2025(TransfertConjointFederal2025(), beneficiaire="Client").ligne_32600 == 0


@pytest.mark.parametrize("nom", CONFIRMATIONS_TRANSFERT_CONJOINT)
@pytest.mark.parametrize("valeur", [False, 1, "true"])
def test_confirmations(tmp_path, nom, valeur):
    with pytest.raises(ValueError):
        valider_transfert_conjoint_2025(profil(tmp_path, **{nom: valeur}))


def test_recalcul_et_estimation_sans_changement_revenus_quebec(tmp_path, monkeypatch):
    p = profil(tmp_path)
    from pathlib import Path
    with monkeypatch.context() as controle:
        controle.setattr(Path, "exists", lambda *args: pytest.fail("Le recalcul ne doit pas lire les pièces sources"))
        e = calcul(_dossier_52000(), transfert_conjoint=p)
    avant = calcul(_dossier_52000())
    assert e.resultat_transfert_conjoint.ligne_32600 == D(9028)
    assert e.revenu == avant.revenu and e.quebec == avant.quebec
    assert dict(e.federal.credits_federaux_complets.montants_par_ligne)["32600"] == D(9028)
    assert e.federal.credits_federaux_complets.base_ligne_33500 - avant.federal.credits_federaux_complets.base_ligne_33500 == D(9028)
    verifier_t1(e)


def test_stockage_entrees_seules_ancien_json_et_divergence(tmp_path):
    p = profil(tmp_path)
    e = calcul(_dossier_52000(), transfert_conjoint=p)
    f = sauvegarder_dossier_fiscal(e.dossier, estimation=e, destination=tmp_path / "cas.json")
    c = charger_dossier_fiscal(f)
    assert c.transfert_conjoint == p
    assert calcul(c.dossier, transfert_conjoint=c.transfert_conjoint) == e
    contenu = json.loads(f.read_text(encoding="utf-8"))
    assert "ligne_32600" not in contenu["transfert_conjoint"]
    assert "derniere_estimation" not in json.loads(p.dossier_conjoint_json)
    with pytest.raises(ValueError, match="diffère"):
        sauvegarder_dossier_fiscal(e.dossier, estimation=e, transfert_conjoint=TransfertConjointFederal2025(), destination=f)
    del contenu["transfert_conjoint"]
    f.write_text(json.dumps(contenu), encoding="utf-8")
    assert charger_dossier_fiscal(f).transfert_conjoint == TransfertConjointFederal2025()


def test_adaptateur_couvre_tous_les_profils_moteur():
    meta = {"chemin", "sauvegarde_le", "estimation", "rapport_pdf", "documents_manquants"}
    assert {f.name for f in fields(DossierFiscalEnregistre)} - meta == set(inspect.signature(calcul).parameters)


def test_identite_et_recursion_refusees(tmp_path):
    p = profil(tmp_path)
    with pytest.raises(ValueError, match="distinctes"):
        calculer_transfert_conjoint_2025(replace(p, beneficiaire="Conjoint fictif"), beneficiaire=" conjoint fictif ")
    brut = json.loads(p.dossier_conjoint_json)
    brut["transfert_conjoint"] = {"activer": True}
    with pytest.raises(ValueError, match="imbriqué"):
        instantane_conjoint_2025(brut)


def test_beneficiaire_change_et_revenu_30300_incoherent(tmp_path):
    from tests.test_tax_federal_spouse_2025 import _profil
    p = profil(tmp_path)
    with pytest.raises(ValueError, match="bénéficiaire"):
        calcul(replace(_dossier_52000(), client="Autre personne"), transfert_conjoint=p)
    with pytest.raises(ValueError, match="revenu du conjoint"):
        calcul(_dossier_52000(), transfert_conjoint=p, montant_conjoint_federal=_profil(
            revenu_net_contribuable_ligne_23600=D(51515), revenu_net_conjoint_2025=D(9999)))
    e = calcul(_dossier_52000(), transfert_conjoint=p, montant_conjoint_federal=_profil(
        revenu_net_contribuable_ligne_23600=D(51515), revenu_net_conjoint_2025=D(10000)))
    assert e.resultat_transfert_conjoint.ligne_32600 == D(9028)
    verifier_t1(e)


def test_scolarite_designee_conjoint_recalculee_et_autre_destinataire_refuse(tmp_path):
    from tests.test_tax_tuition_transfer_2025 import frais
    from tests.test_tax_workers_benefit_2025 import dossier_20000
    d = replace(dossier_20000(), client="Étudiant conjoint")
    for destinataire, relation in (("Client Test", "conjoint"), ("Autre", "conjoint"), ("Client Test", "parent")):
        f = sauvegarder_dossier_fiscal(d, frais_scolarite=frais(beneficiaire=destinataire, relation=relation),
            destination=tmp_path / "etudiant.json")
        p = replace(profil(tmp_path), dossier_conjoint_json=instantane_conjoint_2025(json.loads(f.read_text(encoding="utf-8"))))
        if destinataire == "Client Test" and relation == "conjoint":
            e = calcul(_dossier_52000(), transfert_conjoint=p)
            assert e.resultat_transfert_conjoint.scolarite_36000 == D(1000)
            assert e.resultat_transfert_conjoint.ligne_32600 == D(1000)
            assert e.resultat_reports_scolarite.ligne_32300 == 0
            verifier_t1(e)
        else:
            with pytest.raises(ValueError, match="désignation"):
                calcul(_dossier_52000(), transfert_conjoint=p)


@pytest.mark.parametrize("brut", [[], {"inconnu": 1}, {"activer": "true"}, {"source": 42}])
def test_json_profil_invalide(tmp_path, brut):
    f = sauvegarder_dossier_fiscal(_dossier_52000(), destination=tmp_path / "cas.json")
    contenu = json.loads(f.read_text(encoding="utf-8"))
    contenu["transfert_conjoint"] = brut
    f.write_text(json.dumps(contenu), encoding="utf-8")
    with pytest.raises(ValueError):
        charger_dossier_fiscal(f)


def test_snapshot_pas_de_resume_derivé_ni_dossier_autre_annee(tmp_path):
    p = profil(tmp_path)
    brut = json.loads(p.dossier_conjoint_json)
    brut["derniere_estimation"] = {"montant": "999999"}
    with pytest.raises(ValueError, match="dérivé"):
        valider_transfert_conjoint_2025(replace(p, dossier_conjoint_json=json.dumps(brut)))
    brut.pop("derniere_estimation")
    brut["annee_fiscale"] = 2024
    with pytest.raises(ValueError, match="2025"):
        calcul(_dossier_52000(), transfert_conjoint=replace(p, dossier_conjoint_json=json.dumps(brut)))


def test_trace_pdf_et_resume(tmp_path):
    import fitz
    from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
    from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
    from src.comptaprivee.tax_estimation_2025 import formater_estimation_fiscale_2025
    e = calcul(_dossier_52000(), transfert_conjoint=profil(tmp_path))
    trace = construire_trace_calcul_fiscal_2025(e)
    assert next(l for l in trace.lignes if l.libelle == "Transfert du conjoint — ligne 32600").montant == D(9028)
    assert [l.ordre for l in trace.lignes] == list(range(1, len(trace.lignes) + 1))
    assert "32600" in formater_estimation_fiscale_2025(e)
    f = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "rapport.pdf")
    with fitz.open(f) as pdf:
        texte = "\n".join(page.get_text() for page in pdf)
        assert "Conjoint fictif" in texte and "9028.00" in texte and "36100" in texte
        for page in pdf:
            for x0, y0, x1, y1, *_ in page.get_text("blocks"):
                assert 0 <= x0 < x1 <= page.rect.width
                assert 0 <= y0 < y1 <= page.rect.height
