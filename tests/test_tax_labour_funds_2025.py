from dataclasses import replace
from decimal import Decimal as D

import pytest

from src.comptaprivee.tax_labour_funds_2025 import (
    AcquisitionFonds2025, SituationFonds2025, FondsTravailleurs2025,
    CONFIRMATIONS_FONDS, calculer_fonds_travailleurs_2025,
    fonds_vers_dict, fonds_depuis_dict,
)


def acquisition(**kw):
    v = dict(date_acquisition="2025-06-01", fonds="FTQ A", montant=D(5000), source="RL-10 fictif A")
    v.update(kw)
    return AcquisitionFonds2025(**v)


def personne(**kw):
    v = dict(nom="Client Test", naissance="1980-01-01", revenu_emploi_entreprise=D(52000))
    v.update(kw)
    return SituationFonds2025(**v)


def profil(**kw):
    v = dict(acquisitions=(acquisition(),), contribuable=personne(), source="Validation fictive",
        **{n: True for n in CONFIRMATIONS_FONDS})
    v.update(kw)
    return FondsTravailleurs2025(**v)


def calcul(p=None, **kw):
    return calculer_fonds_travailleurs_2025(p if p is not None else profil(), client="Client Test", **kw)


@pytest.mark.parametrize("cout,credit", [("0.01", "0"), ("100", "15"), ("4999.90", "749.99"),
    ("5000", "750"), ("5000.01", "750"), ("10000", "750")])
def test_taux_15_et_plafond(cout, credit):
    r = calcul(profil(acquisitions=(acquisition(montant=D(cout)),)))
    assert r.ligne_41300 == D(cout)
    assert r.ligne_41400 == D(credit)


def test_aides_et_choix_debut_2026():
    p = profil(acquisitions=(acquisition(montant=D(2500), aide_publique=D(500)),
        acquisition(date_acquisition="2026-03-02", fonds="Fondaction B", montant=D(4000),
            aide_publique=D(1000), cout_reserve_2026=D(1000), source="B")))
    r = calcul(p)
    assert (r.cout_net_total, r.cout_reserve_2026, r.ligne_41300, r.ligne_41400) == (D(5000), D(1000), D(4000), D(600))


def test_credit_2024_soustrait_avant_plafond_2025():
    a = acquisition(date_acquisition="2025-01-01", montant=D(10000), credit_utilise_2024=D(750), source_2024="Déclaration cotisée 2024")
    r = calcul(profil(acquisitions=(a,)))
    assert r.ligne_41300 == D(10000)
    assert r.credit_utilise_2024 == D(750)
    assert r.ligne_41400 == D(750)  # min(750, 1500 - 750), non min(750, 1500) - 750.
    assert calcul(profil(acquisitions=(replace(a, montant=D(5000), credit_utilise_2024=D(200)),))).ligne_41400 == D(550)


def test_ancien_json_et_profil_vide():
    assert fonds_depuis_dict(None) == FondsTravailleurs2025()
    assert calcul(FondsTravailleurs2025(), annee=2024).ligne_41400 == 0
    with pytest.raises(ValueError, match="2025"):
        calcul(annee=2024)


@pytest.mark.parametrize("jour", ["2025-01-01", "2025-03-01", "2025-12-31", "2026-01-01", "2026-03-02"])
def test_dates_acquisition_admises(jour):
    assert calcul(profil(acquisitions=(acquisition(date_acquisition=jour),))).ligne_41400 == 750


@pytest.mark.parametrize("jour", ["2024-12-31", "2026-03-03", "2025-02-30", "20250601", None, 2025])
def test_dates_refusees(jour):
    with pytest.raises(ValueError):
        calcul(profil(acquisitions=(acquisition(date_acquisition=jour),)))


@pytest.mark.parametrize("nom", ["montant", "aide_publique", "credit_utilise_2024", "cout_reserve_2026"])
@pytest.mark.parametrize("valeur", [D("NaN"), D("sNaN"), D("Infinity"), D("-Infinity"), D(-1), D("1.001"), D("1e100"), "100", None, True])
def test_montants_invalides(nom, valeur):
    with pytest.raises(ValueError):
        calcul(profil(acquisitions=(acquisition(**{nom: valeur}),)))


@pytest.mark.parametrize("kw", [dict(montant=D(0)), dict(aide_publique=D(5001)), dict(fonds="Fédéral seulement"),
    dict(fonds="FTQ B"), dict(regime="FERR"), dict(source=""), dict(source=None), dict(souscripteur="parent"),
    dict(rentier="parent"), dict(souscripteur="conjoint"), dict(regime="REER conjoint"),
    dict(credit_utilise_2024=D(1), source_2024="2024"), dict(source_2024="Sans montant"),
    dict(cout_reserve_2026=D(1)), dict(date_acquisition="2026-01-01", cout_reserve_2026=D(5001)),
    dict(date_acquisition="2025-03-01", credit_utilise_2024=D(1)),
    dict(date_acquisition="2025-03-01", credit_utilise_2024=D(751), source_2024="2024")])
def test_acquisition_invalide(kw):
    with pytest.raises(ValueError):
        calcul(profil(acquisitions=(acquisition(**kw),)))


@pytest.mark.parametrize("naissance,revenu,rente,admis", [
    ("1960-12-31", "52000", False, False), ("1961-01-01", "0", False, True),
    ("1980-12-31", "3500", True, False), ("1981-01-01", "0", True, True),
    ("1980-12-31", "3500.01", True, True), ("1980-12-31", "0", False, True),
])
def test_conditions_provinciales_dates_et_exception_travail(naissance, revenu, rente, admis):
    p = profil(contribuable=personne(naissance=naissance, revenu_emploi_entreprise=D(revenu), rente_retraite=rente))
    if admis:
        assert calcul(p).ligne_41400 == 750
    else:
        with pytest.raises(ValueError, match="provincial"):
            calcul(p)


def test_preretraite_rachat_et_reer_conjoint():
    with pytest.raises(ValueError, match="préretraite"):
        calcul(profil(contribuable=personne(conge_sans_retour=True, revenu_emploi_entreprise=D(3500))))
    with pytest.raises(ValueError, match="Rachat"):
        calcul(profil(contribuable=personne(rachat_demande=True)))
    for souscripteur, rentier in [("contribuable", "conjoint"), ("conjoint", "contribuable")]:
        p = profil(acquisitions=(acquisition(regime="REER conjoint", souscripteur=souscripteur, rentier=rentier),),
            conjoint=personne(nom="Conjoint fictif"))
        assert calcul(p).ligne_41400 == 750
        with pytest.raises(ValueError, match="provincial"):
            calcul(replace(p, conjoint=personne(nom="Conjoint fictif", naissance="1960-12-31")))


@pytest.mark.parametrize("nom", list(CONFIRMATIONS_FONDS))
@pytest.mark.parametrize("valeur", [False, 1, "true"])
def test_confirmations_obligatoires(nom, valeur):
    with pytest.raises(ValueError):
        calcul(profil(**{nom: valeur}))


@pytest.mark.parametrize("kw", [dict(nom=""), dict(nom="Autre"), dict(naissance="2026-01-01"),
    dict(naissance=None), dict(rente_retraite=1), dict(conge_sans_retour=None), dict(rachat_demande="false"),
    dict(revenu_emploi_entreprise=D("NaN")), dict(revenu_emploi_entreprise=D(-1))])
def test_situation_invalide(kw):
    with pytest.raises(ValueError):
        calcul(profil(contribuable=personne(**kw)))


def test_doublons_historique_total_et_profils_incoherents():
    with pytest.raises(ValueError, match="unique"):
        calcul(profil(acquisitions=(acquisition(), acquisition(source=" RL-10  FICTIF A "))))
    a = acquisition(date_acquisition="2025-01-01", credit_utilise_2024=D(400), source_2024="2024")
    with pytest.raises(ValueError, match="total"):
        calcul(profil(acquisitions=(a, replace(a, source="B"))))
    for p in (profil(acquisitions=[]), profil(conjoint=personne(nom="Autre")),
            profil(acquisitions=()), profil(source=""), profil(source=None)):
        with pytest.raises(ValueError):
            calcul(p)


def test_json_brut_sans_resultats_et_reconstruction():
    p = profil(acquisitions=(acquisition(date_acquisition="2025-03-01", credit_utilise_2024=D(100), source_2024="2024"),))
    brut = fonds_vers_dict(p)
    assert "ligne_41400" not in brut and "ligne_41300" not in brut
    assert brut["acquisitions"][0]["credit_utilise_2024"] == "100.00"
    assert fonds_depuis_dict(brut, client="Client Test") == p
    assert calcul(fonds_depuis_dict(brut)).ligne_41400 == D(650)


@pytest.mark.parametrize("valeur", [True, 1.5, None, "NaN", "Infinity", "-1", "1.001"])
def test_json_montants_invalides(valeur):
    brut = fonds_vers_dict(profil())
    brut["acquisitions"][0]["montant"] = valeur
    with pytest.raises(ValueError):
        fonds_depuis_dict(brut)


@pytest.mark.parametrize("brut", [[], True, {"derive": "750"}, {"acquisitions": {}},
    {"contribuable": None}, {"conjoint": {"inconnu": True}}, {"acquisitions": [{"inconnu": "x"}]}])
def test_json_structure_invalide(brut):
    with pytest.raises(ValueError):
        fonds_depuis_dict(brut)


def test_estimation_credit_separe_revenus_et_abattement():
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
    from tests.test_tax_estimation_2025 import _dossier_52000
    from tests.test_tax_political_contributions_2025 import profil as politique
    from tests.test_tax_federal_top_up_integration_2025 import verifier_t1
    a = calculer_estimation_fiscale_2025(_dossier_52000())
    e = calculer_estimation_fiscale_2025(_dossier_52000(), fonds_travailleurs=profil(), contributions_politiques=politique())
    assert (e.revenu, e.federal, e.quebec) == (a.revenu, a.federal, a.quebec)
    assert e.rapprochement.abattement_quebec == a.rapprochement.abattement_quebec
    assert a.rapprochement.impot_total_preliminaire - e.rapprochement.impot_total_preliminaire == D(1400)
    assert e.rapprochement.credits_ligne_41600 == D(1400)
    assert e.rapprochement.credit_politique_utilise == D(650)
    assert e.rapprochement.credit_fonds_utilise == D(750)
    verifier_t1(e)


def test_revenu_de_travail_divergent_refuse():
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
    from tests.test_tax_estimation_2025 import _dossier_52000
    with pytest.raises(ValueError, match="différents"):
        calculer_estimation_fiscale_2025(_dossier_52000(), fonds_travailleurs=profil(
            contribuable=personne(revenu_emploi_entreprise=D(52001))))


def test_rapprochement_conjoint_doublons_et_identite():
    from src.comptaprivee.tax_labour_funds_2025 import verifier_fonds_conjoint_2025
    with pytest.raises(ValueError, match="même acquisition"):
        verifier_fonds_conjoint_2025(profil(), profil(), "Conjoint fictif")
    p = profil(acquisitions=(acquisition(regime="REER conjoint", rentier="conjoint"),),
        conjoint=personne(nom="Conjoint fictif"))
    with pytest.raises(ValueError, match="diffère"):
        verifier_fonds_conjoint_2025(p, FondsTravailleurs2025(), "Autre")
    verifier_fonds_conjoint_2025(p, FondsTravailleurs2025(), "Conjoint fictif")


def test_ordre_etranger_politique_fonds_avances_abattement():
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
    from src.comptaprivee.tax_reconciliation_2025 import calculer_rapprochement_fiscal_2025
    from tests.test_tax_estimation_2025 import _dossier_52000
    e = calculer_estimation_fiscale_2025(_dossier_52000())
    f = replace(e.federal, impot_federal_de_base=D(1000), credit_etranger_ligne_40500=D(300))
    r = calculer_rapprochement_fiscal_2025(e.base, f, e.quebec, credit_politique=D(650), credit_fonds=D(750),
        allocation_travailleurs=D(500), avances_act=D(500))
    assert r.credit_politique_utilise == D(650)
    assert r.credit_fonds_utilise == D(50)
    assert r.impot_federal_ligne_41700 == 0
    assert r.avances_act_ligne_41500 == D(500)
    assert r.abattement_quebec == D(165)
    assert r.impot_federal_apres_abattement == D(335)


@pytest.mark.parametrize("credit", [D("NaN"), D("Infinity"), D(-1), D("750.01"), D("1.001"), True, "100"])
def test_rapprochement_refuse_credit_fonds_invalide(credit):
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
    from src.comptaprivee.tax_reconciliation_2025 import calculer_rapprochement_fiscal_2025
    from tests.test_tax_estimation_2025 import _dossier_52000
    e = calculer_estimation_fiscale_2025(_dossier_52000())
    with pytest.raises(ValueError):
        calculer_rapprochement_fiscal_2025(e.base, e.federal, e.quebec, credit_fonds=credit)


def test_stockage_brut_recalcul_ancien_json_divergence(tmp_path):
    import json
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
    from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
    from tests.test_tax_estimation_2025 import _dossier_52000
    e = calculer_estimation_fiscale_2025(_dossier_52000(), fonds_travailleurs=profil())
    f = sauvegarder_dossier_fiscal(e.dossier, estimation=e, destination=tmp_path / "fonds.json")
    c = charger_dossier_fiscal(f)
    assert c.fonds_travailleurs == profil()
    assert calculer_estimation_fiscale_2025(c.dossier, fonds_travailleurs=c.fonds_travailleurs) == e
    brut = json.loads(f.read_text(encoding="utf-8"))
    assert "ligne_41400" not in json.dumps(brut["fonds_travailleurs"])
    with pytest.raises(ValueError, match="divergent"):
        sauvegarder_dossier_fiscal(e.dossier, estimation=e, fonds_travailleurs=FondsTravailleurs2025(), destination=f)
    del brut["fonds_travailleurs"]
    f.write_text(json.dumps(brut), encoding="utf-8")
    assert charger_dossier_fiscal(f).fonds_travailleurs == FondsTravailleurs2025()


def test_trace_pdf_et_credit_politique_total_correct(tmp_path):
    import fitz
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
    from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
    from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
    from tests.test_tax_estimation_2025 import _dossier_52000
    from tests.test_tax_political_contributions_2025 import profil as politique
    e = calculer_estimation_fiscale_2025(_dossier_52000(), fonds_travailleurs=profil(), contributions_politiques=politique())
    t = construire_trace_calcul_fiscal_2025(e)
    assert next(l.montant for l in t.lignes if l.libelle == "Fonds de travailleurs — 41400") == D(750)
    assert next(l.montant for l in t.lignes if l.libelle == "Total des crédits — 41600") == D(1400)
    noms = [l.libelle for l in t.lignes]
    assert noms.index("Crédit politique — 41000") < noms.index("Fonds de travailleurs — 41400") < noms.index("Impôt fédéral après abattement")
    pdf = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "fonds.pdf")
    with fitz.open(pdf) as document:
        texte = "\n".join(page.get_text() for page in document)
    for contenu in ("FONDS DE TRAVAILLEURS", "41300", "41400", "750.00", "41600 : 1400.00", "RL-10 fictif A"):
        assert contenu in texte
