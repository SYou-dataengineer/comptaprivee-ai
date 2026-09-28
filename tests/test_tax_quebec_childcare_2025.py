from dataclasses import replace
from decimal import Decimal as D
import json
import fitz
import pytest
from src.comptaprivee.tax_quebec_childcare_2025 import (
    FraisGardeQuebec2025, EnfantGardeQuebec2025, CONFIRMATIONS_6F,
    calculer_garde_quebec_2025 as moteur, garde_quebec_vers_dict, garde_quebec_depuis_dict)
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calcul, formater_estimation_fiscale_2025
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, dossier_fiscal_depuis_contenu
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from tests.test_tax_estimation_2025 import _dossier_52000, _validee


def enfant(**kw):
    return replace(EnfantGardeQuebec2025("enfant-a", "Enfant A fictif", "2020-01-01", "ordinaire", D(10000), "RL-24 et naissance fictifs"), **kw)


def profil(**kw):
    return replace(FraisGardeQuebec2025(reclamer=True, enfants=(enfant(),), source="Famille et RL-19 fictifs vérifiés",
        **{nom: True for nom in CONFIRMATIONS_6F}), **kw)


@pytest.mark.parametrize("net,taux", [("0", ".78"), ("24795", ".78"), ("24795.01", ".75"),
    ("43725", ".75"), ("43725.01", ".74"), ("45340", ".74"), ("45340.01", ".73"),
    ("46970", ".73"), ("46970.01", ".72"), ("48570", ".72"), ("48570.01", ".71"),
    ("50195", ".71"), ("50195.01", ".70"), ("119835", ".70"), ("119835.01", ".67"), ("1000000", ".67")])
def test_bareme_officiel_2025(net, taux):
    r = moteur(profil(), revenu_net=D(net))
    assert r.taux_ligne_92 == D(taux) and r.credit_ligne_455 == D(10000) * D(taux)


@pytest.mark.parametrize("date,categorie,plafond", [("2019-01-01", "ordinaire", 12275),
    ("2018-12-31", "ordinaire", 6180), ("2009-01-01", "ordinaire", 6180),
    ("2000-01-01", "infirmité", 6180), ("2020-01-01", "infirmité", 12275),
    ("1990-01-01", "déficience grave et prolongée", 16800)])
def test_plafonds_age_condition(date, categorie, plafond):
    r = moteur(profil(enfants=(enfant(naissance=date, categorie=categorie, frais_rl24_e=D(20000)),)))
    assert r.plafond_ligne_50 == r.base_ligne_85 == D(plafond)


def test_plafond_familial_non_plafonnement_separe_des_frais():
    p = profil(enfants=(enfant(frais_rl24_e=D(20000)), enfant(reference="b", nom="Enfant B fictif", naissance="2010-01-01", frais_rl24_e=D(0))))
    r = moteur(p, revenu_net=D(50095))
    assert r.frais_ligne_41 == D(20000) and r.base_ligne_85 == D(18455)
    assert r.credit_ligne_455 == D("13103.05")


def test_conjoint_partage_et_avances_non_plafonnees():
    p = profil(conjoint_nom="Conjoint fictif", revenu_net_conjoint=D(20000),
        credit_demande_conjoint=D(2000), source_conjoint="Déclaration 275 et entente", avances_rl19_c=D(6000))
    r = moteur(p, revenu_net=D(50095))
    assert r.revenu_familial_ligne_80 == D(70095)
    assert r.credit_familial_ligne_94 == D(7000) and r.credit_ligne_455 == D(5000)
    assert r.avances_ligne_441 == D(6000)
    with pytest.raises(ValueError, match="part du conjoint"):
        moteur(replace(p, credit_demande_conjoint=D("7000.01")), revenu_net=D(50095))


def test_avances_sans_credit_et_arrondi():
    r = moteur(profil(enfants=(), avances_rl19_c=D(1500)))
    assert r.credit_ligne_455 == 0 and r.avances_ligne_441 == D(1500)
    assert moteur(profil(enfants=(enfant(frais_rl24_e=D("1.02")),))).credit_ligne_455 == D(".80")


@pytest.mark.parametrize("nom", list(CONFIRMATIONS_6F))
@pytest.mark.parametrize("valeur", [False, "oui", 1])
def test_confirmations(nom, valeur):
    with pytest.raises(ValueError): moteur(profil(**{nom: valeur}))


@pytest.mark.parametrize("kw", [{"naissance": "2008-12-31"}, {"naissance": "2026-01-01"},
    {"naissance": "2020-02-30"}, {"naissance": "20200101"}, {"categorie": "DTC fédéral"},
    {"nom": ""}, {"reference": " "}, {"source": ""}, {"naissance": 2020}])
def test_fiche_invalide(kw):
    with pytest.raises(ValueError): moteur(profil(enfants=(enfant(**kw),)))


@pytest.mark.parametrize("autre", [enfant(), enfant(reference=" ENFANT-A ", nom="Autre enfant"), enfant(reference="b", nom=" enfant a FICTIF ")])
def test_enfant_duplique(autre):
    with pytest.raises(ValueError, match="dupliqué"): moteur(profil(enfants=(enfant(), autre)))


@pytest.mark.parametrize("valeur", [D("NaN"), D("sNaN"), D("-1"), D("1.001"), D("1E9999"), True, "100", 1.5])
def test_montants_invalides(valeur):
    with pytest.raises(ValueError): moteur(profil(avances_rl19_c=valeur))
    with pytest.raises(ValueError): moteur(profil(), revenu_net=valeur)
    with pytest.raises(ValueError): moteur(profil(enfants=(enfant(frais_rl24_e=valeur),)))


def test_donnees_conjoint_sans_identite_et_demandeur_identique():
    with pytest.raises(ValueError, match="sans conjoint"): moteur(profil(revenu_net_conjoint=D(1)))
    with pytest.raises(ValueError, match="source"): moteur(profil(conjoint_nom="Conjoint fictif"))
    with pytest.raises(ValueError, match="différer"): moteur(profil(), demandeur="Enfant A fictif")


def test_integration_revenus_impots_abattement_et_avances():
    d = _dossier_52000(); avant = calcul(d)
    e = calcul(d, frais_garde_quebec=profil(avances_rl19_c=D(8000)))
    assert (e.revenu, e.federal, e.quebec) == (avant.revenu, avant.federal, avant.quebec)
    assert e.resultat_garde_quebec.revenu_familial_ligne_80 == D(50095)
    assert e.rapprochement.credit_garde_quebec_ligne_455 == D(7100)
    assert e.rapprochement.avances_garde_quebec_ligne_441 == D(8000)
    assert not any("Aucun crédit familial" in x for x in e.rapprochement.limitations)
    assert e.rapprochement.abattement_quebec == avant.rapprochement.abattement_quebec
    assert e.rapprochement.impot_total_preliminaire - avant.rapprochement.impot_total_preliminaire == D(8000)
    net = lambda e: e.rapprochement.remboursement_estime - e.rapprochement.solde_estime
    assert net(e) - net(avant) == D(-900)


def test_deduction_federale_distincte():
    from tests.test_tax_child_care_2025 import profil_valide
    p = profil_valide(frais="10000", revenu_gagne="52000", moins_7=1, sept_16=0)
    e = calcul(_dossier_52000(), frais_garde_federaux=p, frais_garde_quebec=profil())
    assert e.revenu.revenu_net_federal == D(43515)
    assert e.revenu.revenu_net_quebec == D(50095)
    assert e.resultat_garde_quebec.credit_ligne_455 == D(7100)


def test_profils_individuels_et_aides_detectees_refuses():
    from tests.test_tax_quebec_refundable_medical_2025 import profil as medical
    with pytest.raises(ValueError, match="individuels"):
        calcul(_dossier_52000(), frais_garde_quebec=profil(), medical_remboursable_quebec=medical())
    d = _dossier_52000()
    d = replace(d, donnees_validees=d.donnees_validees + (_validee("RL1.pdf", "RL-1", "201", "100"),))
    with pytest.raises(ValueError, match="201/J"): calcul(d, frais_garde_quebec=profil())


@pytest.fixture
def couple(tmp_path):
    from src.comptaprivee.tax_spouse_transfer_2025 import (TransfertConjointFederal2025, CONFIRMATIONS_TRANSFERT_CONJOINT, instantane_conjoint_2025)
    d = replace(_dossier_52000(), client="Conjoint fictif")
    autre = profil(conjoint_nom="Client Test", revenu_net_conjoint=D(50095), credit_demande_conjoint=D(5000), source_conjoint="Déclaration fictive et entente")
    e = calcul(d, frais_garde_quebec=autre)
    assert e.resultat_garde_quebec.credit_ligne_455 == D(2000)
    f = sauvegarder_dossier_fiscal(d, estimation=e, destination=tmp_path / "conjoint.json")
    t = TransfertConjointFederal2025(activer=True, beneficiaire="Client Test", source="Dossier conjoint fictif",
        dossier_conjoint_json=instantane_conjoint_2025(json.loads(f.read_text(encoding="utf-8"))),
        **{nom: True for nom in CONFIRMATIONS_TRANSFERT_CONJOINT})
    propre = profil(conjoint_nom="Conjoint fictif", revenu_net_conjoint=D(50095), credit_demande_conjoint=D(2000), source_conjoint="Déclaration fictive et entente")
    return t, propre


def test_deux_dossiers_recalcules_meme_pool(couple):
    t, p = couple
    e = calcul(_dossier_52000(), transfert_conjoint=t, frais_garde_quebec=p)
    assert e.resultat_garde_quebec.credit_ligne_455 == D(5000)
    assert e.resultat_transfert_conjoint.credit_garde_quebec_conjoint == D(2000)
    assert e.resultat_garde_quebec.credit_ligne_455 + e.resultat_transfert_conjoint.credit_garde_quebec_conjoint == D(7000)


@pytest.mark.parametrize("kw", [{"revenu_net_conjoint": D(50096)}, {"conjoint_nom": "Autre conjoint"},
    {"credit_demande_conjoint": D(1999)}, {"enfants": (enfant(frais_rl24_e=D(11000)),)}])
def test_divergences_dossier_conjoint(couple, kw):
    t, p = couple
    with pytest.raises(ValueError): calcul(_dossier_52000(), transfert_conjoint=t, frais_garde_quebec=replace(p, **kw))


def test_json_recalcul_ancien_divergence(tmp_path):
    d = _dossier_52000(); e = calcul(d, frais_garde_quebec=profil())
    f = sauvegarder_dossier_fiscal(d, estimation=e, destination=tmp_path / "garde_quebec.json")
    brut = json.loads(f.read_text(encoding="utf-8")); c = dossier_fiscal_depuis_contenu(brut)
    assert c.frais_garde_quebec == profil()
    assert calcul(c.dossier, frais_garde_quebec=c.frais_garde_quebec) == e
    assert "credit_ligne_455" not in brut["frais_garde_quebec"]
    with pytest.raises(ValueError, match="divergent"):
        sauvegarder_dossier_fiscal(d, estimation=e, frais_garde_quebec=profil(avances_rl19_c=D(1)), destination=tmp_path / "refus.json")
    brut.pop("frais_garde_quebec")
    assert dossier_fiscal_depuis_contenu(brut).frais_garde_quebec == FraisGardeQuebec2025()


@pytest.mark.parametrize("champ,valeur", [("enfants", {}), ("valide_par_comptable", "oui"), ("source", 1),
    ("credit_ligne_455", "7100"), ("reclamer", 1), ("avances_rl19_c", 100)])
def test_json_strict(champ, valeur):
    brut = garde_quebec_vers_dict(profil()); brut[champ] = valeur
    with pytest.raises(ValueError): garde_quebec_depuis_dict(brut)


def test_json_enfant_cles_inconnues_et_historique():
    brut = garde_quebec_vers_dict(profil()); brut["enfants"][0]["plafond"] = "12275"
    with pytest.raises(ValueError): garde_quebec_depuis_dict(brut)
    assert garde_quebec_depuis_dict(None) == garde_quebec_depuis_dict({}) == FraisGardeQuebec2025()
    assert calcul(_dossier_52000(), frais_garde_quebec=FraisGardeQuebec2025()) == calcul(_dossier_52000())


def test_trace_resume_pdf(tmp_path):
    e = calcul(_dossier_52000(), frais_garde_quebec=profil(avances_rl19_c=D(8000)))
    t = construire_trace_calcul_fiscal_2025(e)
    assert "455" in t.formule_resultat and "441" in t.formule_resultat
    assert [x.ordre for x in t.lignes] == list(range(1, len(t.lignes) + 1))
    assert next(x for x in t.lignes if x.libelle == "Crédit garde Québec 455").montant == D(7100)
    assert "441" in next(x for x in t.lignes if x.libelle == "Impôt total préliminaire").formule
    assert "ANNEXE C / LIGNE 455" in formater_estimation_fiscale_2025(e)
    f = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "garde_quebec_6f.pdf")
    with fitz.open(f) as pdf:
        texte = "\n".join(p.get_text() for p in pdf)
        for p in pdf:
            assert all(0 <= b[0] < b[2] <= p.rect.width and 0 <= b[1] < b[3] <= p.rect.height for b in p.get_text("blocks"))
    for attendu in ("ANNEXE C / LIGNE 455", "7100.00", "8000.00", "50095.00", "validation comptable"):
        assert attendu in texte
