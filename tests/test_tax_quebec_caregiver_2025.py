from dataclasses import replace
from decimal import Decimal as D
import json
import fitz
import pytest
from src.comptaprivee.tax_quebec_caregiver_2025 import (
    PersonneAidanteQuebec2025, PersonneAideeQuebec2025, CONFIRMATIONS_6G, MODES_AIDANTE,
    calculer_aidante_quebec_2025 as moteur, aidante_quebec_vers_dict, aidante_quebec_depuis_dict)
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calcul, formater_estimation_fiscale_2025
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, dossier_fiscal_depuis_contenu
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from tests.test_tax_estimation_2025 import _dossier_52000


def personne(**kw):
    return replace(PersonneAideeQuebec2025(reference="a", nom="Parent A fictif", naissance="1950-01-01",
        debut="2025-01-01", fin="2025-12-31", adresse="Adresse fictive Québec", revenu_net=D(30000),
        source="Déclaration, bail, naissance, attestation Québec et période fictifs"), **kw)


def profil(**kw):
    return replace(PersonneAidanteQuebec2025(reclamer=True, personnes=(personne(),), source="Dossier et RL-19 fictifs vérifiés",
        **{n: True for n in CONFIRMATIONS_6G}), **kw)


@pytest.mark.parametrize("revenu,reduction", [("0", "0"), ("26520", "0"), ("26520.01", "0"),
    ("26520.04", ".01"), ("30000", "556.80"), ("35857.50", "1494"), ("100000", "1494")])
@pytest.mark.parametrize("mode,maximum", [(MODES_AIDANTE[0], "2988"), (MODES_AIDANTE[1], "1494")])
def test_bornes_revenu_annexe_h(revenu, reduction, mode, maximum):
    e = personne(mode=mode, revenu_net=D(revenu), adresse="" if mode == MODES_AIDANTE[1] else "Adresse fictive")
    r = moteur(profil(personnes=(e,)))
    assert r.personnes[0].reduction_revenu == D(reduction)
    assert r.credit_ligne_462 == D(maximum) - D(reduction)


@pytest.mark.parametrize("revenu", [D(0), D(26520), D(1000000)])
def test_70_ans_sans_reduction_revenu(revenu):
    assert moteur(profil(personnes=(personne(mode=MODES_AIDANTE[2], revenu_net=revenu),))).credit_ligne_462 == D(1494)


@pytest.mark.parametrize("naissance,credit", [("2007-01-01", "2739"), ("2007-06-30", "1494"),
    ("2007-12-01", "0"), ("2006-12-31", "2988")])
def test_18_ans_mois_anniversaire_inclus(naissance, credit):
    assert moteur(profil(personnes=(personne(naissance=naissance, lien="enfant", revenu_net=D(0)),))).credit_ligne_462 == D(credit)


def test_18_ans_arrondi_final_et_decembre_sans_residu():
    e = personne(naissance="2007-06-01", revenu_net=D("26520.06"), lien="enfant")
    r = moteur(profil(personnes=(e,)))
    assert r.personnes[0].reduction_revenu == D(".01")
    assert r.personnes[0].reduction_18_ans == D("1494.00")
    assert r.credit_ligne_462 == D("1493.99")
    assert moteur(profil(personnes=(replace(e, naissance="2007-12-31"),))).credit_ligne_462 == 0


@pytest.mark.parametrize("debut,fin", [("2024-07-01", "2025-07-01"), ("2025-01-01", "2025-12-30"),
    ("2025-07-03", "2026-07-02"), ("2023-12-31", "2025-12-31"), ("2025-12-31", "2025-01-01")])
def test_periodes_insuffisantes_ou_hors_profil(debut, fin):
    with pytest.raises(ValueError, match="Période"):
        moteur(profil(personnes=(personne(debut=debut, fin=fin),)))


@pytest.mark.parametrize("debut,fin", [("2024-07-02", "2025-07-02"), ("2025-07-02", "2026-07-01")])
def test_periode_183_jours_et_continuite(debut, fin):
    assert moteur(profil(personnes=(personne(debut=debut, fin=fin),))).credit_ligne_462 == D("2431.20")


def test_plusieurs_personnes_parts_et_avances_integrales():
    a = personne(credit_autres=D(1000))
    b = personne(reference="b", nom="Parent B fictif", mode=MODES_AIDANTE[2])
    r = moteur(profil(personnes=(a, b), avances_rl19_h=D(5000)))
    assert r.credit_ligne_462 == D("2925.20") and r.avances_ligne_441 == D(5000)
    assert moteur(profil(personnes=(), avances_rl19_h=D(1000))).avances_ligne_441 == D(1000)
    with pytest.raises(ValueError, match="part des autres"):
        moteur(profil(personnes=(replace(a, credit_autres=D("2431.21")),)))


@pytest.mark.parametrize("kw", [{"naissance": "2008-01-01"}, {"naissance": "20070101"}, {"naissance": "2000-02-30"},
    {"nom": ""}, {"reference": " "}, {"source": ""}, {"mode": "invalide"}, {"lien": "ami sans attestation"},
    {"mode": MODES_AIDANTE[2], "lien": "conjoint"}, {"mode": MODES_AIDANTE[2], "naissance": "1956-01-01"},
    {"adresse": ""}, {"mode": MODES_AIDANTE[1]}, {"debut": 2025}])
def test_fiches_invalides(kw):
    with pytest.raises(ValueError): moteur(profil(personnes=(personne(**kw),)))


@pytest.mark.parametrize("autre", [personne(), personne(reference=" A ", nom="Autre nom"), personne(reference="b", nom=" parent A FICTIF ")])
def test_doublons(autre):
    with pytest.raises(ValueError, match="dupliquée"): moteur(profil(personnes=(personne(), autre)))


@pytest.mark.parametrize("nom", list(CONFIRMATIONS_6G))
@pytest.mark.parametrize("valeur", [False, "oui", 1])
def test_confirmations_strictes(nom, valeur):
    with pytest.raises(ValueError): moteur(profil(**{nom: valeur}))


@pytest.mark.parametrize("valeur", [D("NaN"), D("sNaN"), D("-1"), D("1.001"), D("1E9999"), True, "100", 1.5])
def test_montants_invalides(valeur):
    with pytest.raises(ValueError): moteur(profil(avances_rl19_h=valeur))
    for nom in ("revenu_net", "credit_autres"):
        with pytest.raises(ValueError): moteur(profil(personnes=(personne(**{nom: valeur}),)))


def test_demandeur_ne_peut_etre_sa_personne_aidee():
    with pytest.raises(ValueError, match="différer"): moteur(profil(), demandeur="Parent A fictif")


def test_integration_credit_remboursable_avances_et_cumul_garde():
    from tests.test_tax_quebec_childcare_2025 import profil as garde
    d = _dossier_52000(); avant = calcul(d)
    e = calcul(d, personne_aidante_quebec=profil(avances_rl19_h=D(3000)), frais_garde_quebec=garde(avances_rl19_c=D(8000)))
    assert (e.revenu, e.federal, e.quebec) == (avant.revenu, avant.federal, avant.quebec)
    assert e.rapprochement.credit_aidante_quebec_ligne_462 == D("2431.20")
    assert e.rapprochement.avances_aidante_quebec_ligne_441 == D(3000)
    assert e.rapprochement.avances_garde_quebec_ligne_441 == D(8000)
    assert e.rapprochement.impot_total_preliminaire - avant.rapprochement.impot_total_preliminaire == D(11000)
    assert e.rapprochement.abattement_quebec == avant.rapprochement.abattement_quebec
    net = lambda e: e.rapprochement.remboursement_estime - e.rapprochement.solde_estime
    assert net(e) - net(avant) == D("-1468.80")


def test_credit_non_limite_a_limpot():
    d = _dossier_52000()
    d = replace(d, donnees_validees=tuple(replace(v, valeur_validee=D(0)) for v in d.donnees_validees))
    e = calcul(d, personne_aidante_quebec=profil())
    assert e.rapprochement.remboursement_estime == D("2431.20")


def test_avances_seules_recalculees_apres_rechargement_json(tmp_path):
    d = _dossier_52000()
    avant = calcul(d)
    p = profil(personnes=(), avances_rl19_h=D(5000))
    e = calcul(d, personne_aidante_quebec=p)
    f = sauvegarder_dossier_fiscal(d, estimation=e, destination=tmp_path / "avances.json")
    c = dossier_fiscal_depuis_contenu(json.loads(f.read_text(encoding="utf-8")))
    assert calcul(c.dossier, personne_aidante_quebec=c.personne_aidante_quebec) == e
    assert e.rapprochement.credit_aidante_quebec_ligne_462 == D(0)
    assert e.rapprochement.avances_aidante_quebec_ligne_441 == D(5000)
    assert e.rapprochement.remboursement_estime == avant.rapprochement.remboursement_estime - D(5000)


def test_rapprochement_aidante_avec_medical_scolarite_et_handicap():
    from tests.test_tax_medical_expenses_2025 import _frais_valides as medical
    from tests.test_tax_tuition_2025 import _frais_valides as scolarite
    from tests.test_tax_disability_2025 import _credit_valide as handicap

    donnees = dict(frais_medicaux=medical(), frais_scolarite=scolarite(),
                   credit_deficience=handicap())
    avant = calcul(_dossier_52000(), **donnees)
    p = profil(personnes=(personne(mode=MODES_AIDANTE[1], adresse=""),))
    e = calcul(_dossier_52000(), personne_aidante_quebec=p, **donnees)

    assert (e.revenu, e.federal, e.quebec) == (avant.revenu, avant.federal, avant.quebec)
    assert e.rapprochement.credit_aidante_quebec_ligne_462 == D("937.20")
    assert e.rapprochement.remboursement_estime - avant.rapprochement.remboursement_estime == D("937.20")
    libelle = "Crédit personne aidante Québec inclus selon les personnes, périodes et parts validées de l'annexe H."
    assert e.rapprochement.limitations.count(libelle) == 1


def instantane(tmp_path, autre):
    from src.comptaprivee.tax_spouse_transfer_2025 import (TransfertConjointFederal2025,
        CONFIRMATIONS_TRANSFERT_CONJOINT, instantane_conjoint_2025)
    d = replace(_dossier_52000(), client="Conjoint fictif")
    e = calcul(d, personne_aidante_quebec=autre)
    f = sauvegarder_dossier_fiscal(d, estimation=e, destination=tmp_path / "conjoint.json")
    return TransfertConjointFederal2025(activer=True, beneficiaire="Client Test", source="Dossier synthétique autorisé",
        dossier_conjoint_json=instantane_conjoint_2025(json.loads(f.read_text(encoding="utf-8"))),
        **{n: True for n in CONFIRMATIONS_TRANSFERT_CONJOINT})


def test_partage_entre_deux_dossiers_recalcules(tmp_path):
    t = instantane(tmp_path, profil(personnes=(personne(credit_autres=D(1000)),)))
    p = profil(personnes=(personne(credit_autres=D("1431.20")),))
    e = calcul(_dossier_52000(), transfert_conjoint=t, personne_aidante_quebec=p)
    assert e.resultat_aidante_quebec.credit_ligne_462 == D(1000)
    assert moteur(e.resultat_transfert_conjoint.aidante_quebec_conjoint).credit_ligne_462 == D("1431.20")
    with pytest.raises(ValueError, match="Parts des aidants"):
        calcul(_dossier_52000(), transfert_conjoint=t, personne_aidante_quebec=profil())
    with pytest.raises(ValueError, match="revenu divergent"):
        calcul(_dossier_52000(), transfert_conjoint=t,
            personne_aidante_quebec=profil(personnes=(personne(revenu_net=D(31000)),)))


def test_personne_aidee_ne_peut_etre_aidante_elle_meme(tmp_path):
    t = instantane(tmp_path, profil(personnes=(personne(nom="Client Test", lien="conjoint", revenu_net=D(50095)),)))
    with pytest.raises(ValueError, match="demandeur lui-même"):
        calcul(_dossier_52000(), transfert_conjoint=t, personne_aidante_quebec=profil())


def test_revenu_du_conjoint_aide_rapproche(tmp_path):
    t = instantane(tmp_path, PersonneAidanteQuebec2025())
    p = profil(personnes=(personne(nom="Conjoint fictif", lien="conjoint", revenu_net=D(50095)),))
    assert calcul(_dossier_52000(), transfert_conjoint=t, personne_aidante_quebec=p).resultat_aidante_quebec.credit_ligne_462 == D(1494)
    with pytest.raises(ValueError, match="revenu Québec divergent"):
        calcul(_dossier_52000(), transfert_conjoint=t,
            personne_aidante_quebec=profil(personnes=(personne(nom="Conjoint fictif", lien="conjoint"),)))


def test_conjoint_aide_refuse_profil_individuel_medical():
    from tests.test_tax_quebec_refundable_medical_2025 import profil as medical
    with pytest.raises(ValueError, match="sans conjoint"):
        calcul(_dossier_52000(), personne_aidante_quebec=profil(personnes=(personne(lien="conjoint"),)), medical_remboursable_quebec=medical())


def test_cohabitation_et_personne_seule_distinctes():
    from tests.test_tax_living_alone_integration_2025 import _profil_simple
    with pytest.raises(ValueError, match="Cohabitation"):
        calcul(_dossier_52000(), personne_aidante_quebec=profil(), personne_vivant_seule=_profil_simple())
    p = profil(personnes=(personne(mode=MODES_AIDANTE[1], adresse=""),))
    e = calcul(_dossier_52000(), personne_aidante_quebec=p, personne_vivant_seule=_profil_simple())
    assert e.resultat_aidante_quebec.credit_ligne_462 == D("937.20")


def test_revenu_conjoint_commun_avec_garde():
    from tests.test_tax_quebec_childcare_2025 import profil as garde
    g = garde(conjoint_nom="Conjoint fictif", revenu_net_conjoint=D(30000), source_conjoint="Déclaration fictive")
    p = profil(personnes=(personne(nom="Conjoint fictif", lien="conjoint"),))
    assert calcul(_dossier_52000(), personne_aidante_quebec=p, frais_garde_quebec=g).resultat_aidante_quebec.credit_ligne_462 == D("2431.20")
    with pytest.raises(ValueError, match="Revenu Québec"):
        calcul(_dossier_52000(), personne_aidante_quebec=p, frais_garde_quebec=replace(g, revenu_net_conjoint=D(31000)))


def test_json_recalcul_retrocompatibilite_et_divergence(tmp_path):
    d = _dossier_52000(); e = calcul(d, personne_aidante_quebec=profil())
    f = sauvegarder_dossier_fiscal(d, estimation=e, destination=tmp_path / "aidante.json")
    brut = json.loads(f.read_text(encoding="utf-8")); c = dossier_fiscal_depuis_contenu(brut)
    assert c.personne_aidante_quebec == profil()
    assert calcul(c.dossier, personne_aidante_quebec=c.personne_aidante_quebec) == e
    assert "credit_ligne_462" not in brut["personne_aidante_quebec"]
    with pytest.raises(ValueError, match="divergent"):
        sauvegarder_dossier_fiscal(d, estimation=e, personne_aidante_quebec=profil(avances_rl19_h=D(1)), destination=tmp_path / "refus.json")
    brut.pop("personne_aidante_quebec")
    assert dossier_fiscal_depuis_contenu(brut).personne_aidante_quebec == PersonneAidanteQuebec2025()


@pytest.mark.parametrize("champ,valeur", [("personnes", {}), ("valide_par_comptable", "oui"), ("source", 1),
    ("credit_ligne_462", "2988"), ("reclamer", 1), ("avances_rl19_h", 100)])
def test_json_strict(champ, valeur):
    brut = aidante_quebec_vers_dict(profil()); brut[champ] = valeur
    with pytest.raises(ValueError): aidante_quebec_depuis_dict(brut)


def test_json_personne_et_profil_vide():
    brut = aidante_quebec_vers_dict(profil()); brut["personnes"][0]["credit"] = "1494"
    with pytest.raises(ValueError): aidante_quebec_depuis_dict(brut)
    assert aidante_quebec_depuis_dict(None) == aidante_quebec_depuis_dict({}) == PersonneAidanteQuebec2025()
    assert calcul(_dossier_52000(), personne_aidante_quebec=PersonneAidanteQuebec2025()) == calcul(_dossier_52000())


def test_trace_resume_pdf(tmp_path):
    e = calcul(_dossier_52000(), personne_aidante_quebec=profil(avances_rl19_h=D(3000)))
    t = construire_trace_calcul_fiscal_2025(e)
    assert "462" in t.formule_resultat and "441" in t.formule_resultat
    assert [x.ordre for x in t.lignes] == list(range(1, len(t.lignes) + 1))
    assert next(x for x in t.lignes if x.libelle == "Crédit personne aidante Québec 462").montant == D("2431.20")
    assert "RL-19 H" in next(x for x in t.lignes if x.libelle == "Impôt total préliminaire").formule
    assert "ANNEXE H / LIGNE 462" in formater_estimation_fiscale_2025(e)
    f = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "aidante_quebec_6g.pdf")
    with fitz.open(f) as pdf:
        texte = "\n".join(p.get_text() for p in pdf)
        for p in pdf:
            assert all(0 <= b[0] < b[2] <= p.rect.width and 0 <= b[1] < b[3] <= p.rect.height for b in p.get_text("blocks"))
    for attendu in ("ANNEXE H / LIGNE 462", "2431.20", "3000.00", "556.80", "Parent A fictif", "validation comptable"):
        assert attendu in texte
