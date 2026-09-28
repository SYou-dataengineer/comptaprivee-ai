from dataclasses import replace
from decimal import Decimal as D
import json

import fitz
import pytest

from src.comptaprivee.tax_adoption_2025 import (
    Adoption2025, EnfantAdopte2025, DepenseAdoption2025, CONFIRMATIONS_ADOPTION,
    calculer_adoption_2025, adoption_vers_dict, adoption_depuis_dict,
)
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calcul
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_top_up_integration_2025 import verifier_t1


def depense(**kw):
    v = dict(date_engagement="2024-07-01", categorie="agence", montant=D(22000), source="Facture fictive A")
    v.update(kw)
    return DepenseAdoption2025(**v)


def enfant(**kw):
    v = dict(nom="Enfant fictif", naissance="2015-02-10", inscription="2024-01-01", ordonnance="2025-01-10",
        residence_permanente="2025-02-01", depenses=(depense(),), aides=D(3000), source="Pièces fictives et partage signé")
    v.update(kw)
    return EnfantAdopte2025(**v)


def profil(**kw):
    v = dict(enfants=(enfant(),), **{n: True for n in CONFIRMATIONS_ADOPTION})
    v.update(kw)
    return Adoption2025(**v)


def resultat(**kw):
    return calculer_adoption_2025(profil(enfants=(enfant(**kw),)))


def test_vide_ancien_et_annee():
    assert calculer_adoption_2025(Adoption2025(), 2024).montant_31300 == 0
    assert adoption_depuis_dict(None, 2024) == Adoption2025()
    with pytest.raises(ValueError, match="2025"):
        calculer_adoption_2025(profil(), 2024)


@pytest.mark.parametrize("montant,attendu", [("19579.99", "19579.99"), ("19580", "19580"), ("19580.01", "19580")])
def test_plafond_2025(montant, attendu):
    assert resultat(depenses=(depense(montant=D(montant)),), aides=D(0)).montant_31300 == D(attendu)


def test_aides_exception_partage_et_plusieurs_enfants():
    a = enfant(aides_imposables_non_deductibles=D(1000), part_pourcentage=D(40))
    b = enfant(nom="Autre enfant", depenses=(depense(montant=D(10000), source="Facture B"),), aides=D(2000))
    r = calculer_adoption_2025(profil(enfants=(a, b)))
    assert r.enfants[0].aides_deductibles == D(2000)
    assert r.enfants[0].net == D(20000)
    assert r.enfants[0].base_plafonnee == D(19580)
    assert r.enfants[0].montant_31300 == D(7832)
    assert r.enfants[0].reste_autres_demandeurs == D(11748)
    assert r.montant_31300 == D(15832)
    assert resultat(aides=D(25000)).montant_31300 == 0
    assert resultat(part_pourcentage=D(0)).montant_31300 == 0


def test_periode_min_max_et_frais_de_plusieurs_annees():
    r = resultat(demande_cour="2023-01-01", depenses=(depense(date_engagement="2023-01-01", montant=D(100)),
        depense(date_engagement="2025-02-01", montant=D(200), source="B")), aides=D(0))
    assert r.enfants[0].debut == "2023-01-01" and r.enfants[0].fin == "2025-02-01"
    assert r.montant_31300 == D(300)
    assert resultat(ordonnance="2024-12-01").enfants[0].fin == "2025-02-01"
    assert resultat(residence_permanente="2024-12-01").enfants[0].fin == "2025-01-10"


@pytest.mark.parametrize("champ,valeur", [
    ("naissance", "2007-01-10"), ("naissance", "2026-01-01"), ("naissance", "2015-02-30"),
    ("naissance", "20150210"), ("inscription", ""), ("inscription", None),
    ("ordonnance", "2026-01-01"), ("residence_permanente", "2026-01-01"),
    ("inscription", "2025-03-01"), ("source", " "), ("nom", None),
    ("aides_imposables_non_deductibles", D(3001)), ("part_pourcentage", D("100.01")),
])
def test_enfant_invalide(champ, valeur):
    with pytest.raises(ValueError):
        resultat(**{champ: valeur})


def test_age_17_ans_dernier_jour():
    assert resultat(naissance="2007-01-11").montant_31300 == D(19000)


@pytest.mark.parametrize("valeur", [D("NaN"), D("sNaN"), D("Infinity"), D("-Infinity"), D(-1), D("0.001"), D("1e100"), "100", True, None])
@pytest.mark.parametrize("champ", ["aides", "aides_imposables_non_deductibles", "part_pourcentage"])
def test_decimal_invalide(champ, valeur):
    with pytest.raises(ValueError):
        resultat(**{champ: valeur})


@pytest.mark.parametrize("kw", [dict(montant=D("NaN")), dict(montant=D(0)), dict(montant=D(-1)),
    dict(montant=D("1.001")), dict(date_engagement="2023-12-31"), dict(date_engagement="2025-02-02"),
    dict(categorie="autre"), dict(source="")])
def test_depense_invalide(kw):
    with pytest.raises(ValueError):
        resultat(depenses=(depense(**kw),))


def test_doublons_enfant_et_piece():
    with pytest.raises(ValueError, match="enfant"):
        calculer_adoption_2025(profil(enfants=(enfant(), enfant(nom=" ENFANT  FICTIF "))))
    with pytest.raises(ValueError, match="Pièce"):
        resultat(depenses=(depense(), depense(source=" facture fictive a ")))
    with pytest.raises(ValueError, match="Pièce"):
        calculer_adoption_2025(profil(enfants=(enfant(), enfant(nom="Autre enfant"))))


@pytest.mark.parametrize("champ", list(CONFIRMATIONS_ADOPTION))
@pytest.mark.parametrize("valeur", [False, "true", 1])
def test_confirmations(champ, valeur):
    with pytest.raises(ValueError):
        calculer_adoption_2025(profil(**{champ: valeur}))


def test_estimation_revenu_inchange_et_chaine_federale():
    avant = calcul(_dossier_52000())
    e = calcul(_dossier_52000(), adoption=profil())
    assert e.revenu == avant.revenu and e.quebec == avant.quebec
    assert dict(e.federal.credits_federaux_complets.montants_par_ligne)["31300"] == D(19000)
    assert e.federal.credits_federaux_complets.base_ligne_33500 - avant.federal.credits_federaux_complets.base_ligne_33500 == D(19000)
    verifier_t1(e)


def test_scolarite_apres_adoption():
    from tests.test_tax_tuition_carryforward_2025 import frais
    from tests.test_tax_workers_benefit_2025 import dossier_20000
    avant = calcul(dossier_20000(), frais_scolarite=frais())
    e = calcul(dossier_20000(), frais_scolarite=frais(), adoption=profil())
    assert avant.resultat_reports_scolarite.ligne_32300 == D("983.20")
    assert e.resultat_reports_scolarite.ligne_32300 == 0
    assert e.resultat_reports_scolarite.report_futur == D(4000)
    verifier_t1(e)


def test_stockage_recalcul_ancien_divergence(tmp_path):
    e = calcul(_dossier_52000(), adoption=profil())
    f = sauvegarder_dossier_fiscal(e.dossier, estimation=e, destination=tmp_path / "cas.json")
    c = charger_dossier_fiscal(f)
    assert c.adoption == profil() and calcul(c.dossier, adoption=c.adoption) == e
    brut = json.loads(f.read_text(encoding="utf-8"))
    assert brut["adoption"]["enfants"][0]["depenses"][0]["montant"] == "22000.00"
    assert "montant_31300" not in json.dumps(brut["adoption"])
    with pytest.raises(ValueError, match="diff"):
        sauvegarder_dossier_fiscal(e.dossier, estimation=e, adoption=Adoption2025(), destination=f)
    del brut["adoption"]
    f.write_text(json.dumps(brut), encoding="utf-8")
    assert charger_dossier_fiscal(f).adoption == Adoption2025()


@pytest.mark.parametrize("brut", [[], {"inconnu": 1}, {"enfants": {}}, {"enfants": [None]},
    {"enfants": [{"inconnu": 1}]}, {"enfants": [{"depenses": [None]}]}, {"valide_par_comptable": "true"}])
def test_json_structure_invalide(brut):
    with pytest.raises(ValueError):
        adoption_depuis_dict(brut)


@pytest.mark.parametrize("v", ["NaN", "Infinity", "-1", "0.001", "texte", True, 1.2, None])
def test_json_montants_invalides(v):
    brut = adoption_vers_dict(profil())
    brut["enfants"][0]["aides"] = v
    with pytest.raises(ValueError):
        adoption_depuis_dict(brut)


def test_trace_et_pdf(tmp_path):
    e = calcul(_dossier_52000(), adoption=profil())
    trace = construire_trace_calcul_fiscal_2025(e)
    assert next(l for l in trace.lignes if l.libelle == "Adoption — ligne 31300").montant == D(19000)
    assert [l.ordre for l in trace.lignes] == list(range(1, len(trace.lignes) + 1))
    f = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "rapport.pdf")
    with fitz.open(f) as pdf:
        texte = "\n".join(page.get_text() for page in pdf)
        assert "31300" in texte and "19000.00" in texte and "Facture fictive A" in texte
        for page in pdf:
            for x0, y0, x1, y1, *_ in page.get_text("blocks"):
                assert 0 <= x0 < x1 <= page.rect.width
                assert 0 <= y0 < y1 <= page.rect.height


def test_annexe2_et_plafond_commun_des_deux_conjoints(tmp_path):
    from tests.test_tax_spouse_transfer_2025 import profil as transfert
    from tests.test_tax_interest_income_2025 import dossier_interets, profil_interets
    from tests.test_tax_federal_age_pension_integration_2025 import _profil_age_federal
    from src.comptaprivee.tax_spouse_transfer_2025 import instantane_conjoint_2025
    d = replace(dossier_interets("25000"), client="Conjoint fictif")
    a = _profil_age_federal(revenu_net_ligne_23600=D(25000))
    f = sauvegarder_dossier_fiscal(d, adoption=profil(enfants=(enfant(part_pourcentage=D(40)),)),
        profil_interets=profil_interets(), credits_federaux_age_pension=a, destination=tmp_path / "donneur.json")
    p = replace(transfert(tmp_path), dossier_conjoint_json=instantane_conjoint_2025(json.loads(f.read_text(encoding="utf-8"))))
    e = calcul(_dossier_52000(), transfert_conjoint=p, adoption=profil(enfants=(enfant(part_pourcentage=D(60)),)))
    assert e.resultat_transfert_conjoint.base_ligne_100 == D(7600)
    assert e.resultat_transfert_conjoint.reduction_36100 == D(1271)
    assert e.resultat_transfert_conjoint.ligne_32600 == D(7757)
    assert e.resultat_adoption.montant_31300 == D(11400)
    verifier_t1(e)
    with pytest.raises(ValueError, match="maximum commun"):
        calcul(_dossier_52000(), transfert_conjoint=p, adoption=profil())


def test_arrondi_partage_ne_permet_pas_un_cent_en_double():
    from src.comptaprivee.tax_adoption_2025 import verifier_partage_adoption_2025
    p = profil(enfants=(enfant(depenses=(depense(montant=D("0.01")),), aides=D(0), part_pourcentage=D(50)),))
    assert calculer_adoption_2025(p).montant_31300 == D("0.01")
    with pytest.raises(ValueError, match="maximum commun"):
        verifier_partage_adoption_2025(p, p)


def test_demandes_debut_toutes_avant_fin():
    with pytest.raises(ValueError, match="période"):
        resultat(demande_cour="2026-01-01")
