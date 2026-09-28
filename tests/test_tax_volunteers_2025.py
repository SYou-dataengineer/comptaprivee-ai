from dataclasses import replace
from decimal import Decimal as D
from pathlib import Path
import json

import fitz
import pytest

from src.comptaprivee.tax_volunteers_2025 import (
    ActiviteBenevole2025, Benevoles2025, CONFIRMATIONS_BENEVOLES, calculer_benevoles_2025,
)
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calcul
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
from src.comptaprivee.tax_field_extractor import extraire_cases_fiscales
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from tests.test_tax_estimation_2025 import _dossier_52000, _validee
from tests.test_tax_federal_top_up_integration_2025 import verifier_t1


def activite(**kw):
    v = dict(organisme="Service fictif", nature="pompiers", heures=D(200), source="Certificat du chef fictif",
        organisme_admissible=True, services_similaires_remuneres=False)
    v.update(kw)
    return ActiviteBenevole2025(**v)


def profil(**kw):
    v = dict(choix="pompiers", activites=(activite(),), source="Choix et feuillets fictifs",
        **{n: True for n in CONFIRMATIONS_BENEVOLES})
    v.update(kw)
    return Benevoles2025(**v)


def dossier(montant="1000"):
    d = _dossier_52000()
    t4 = next(x.document for x in d.donnees_validees if x.type_document == "T4")
    return replace(d, donnees_validees=d.donnees_validees + (_validee(t4, "T4", "87", montant),))


def resultat(p=None, d=None):
    return calculer_benevoles_2025(p if p is not None else profil(), d if d is not None else dossier())


def test_vide_et_ancien_dossier_autre_annee_sans_bloc():
    assert resultat(Benevoles2025(), _dossier_52000()).base_credit == 0
    assert resultat(Benevoles2025(), replace(_dossier_52000(), annee_fiscale=2024)).base_credit == 0
    with pytest.raises(ValueError, match="2025"):
        resultat(d=replace(dossier(), annee_fiscale=2024))


@pytest.mark.parametrize("heures,admis", [("199.99", False), ("200", True), ("200.01", True)])
def test_seuil_200(heures, admis):
    p = profil(activites=(activite(heures=D(heures)),))
    if admis:
        assert resultat(p).base_credit == D(6000)
    else:
        with pytest.raises(ValueError, match="200 heures"):
            resultat(p)


@pytest.mark.parametrize("choix,ligne", [("pompiers", "31220"), ("sauvetage", "31240")])
def test_combinaison_heures_et_un_seul_credit(choix, ligne):
    p = profil(choix=choix, activites=(activite(heures=D(110)), activite(organisme="Sauvetage fictif", nature="sauvetage", heures=D(90))))
    r = resultat(p)
    assert r.ligne_credit == ligne and r.base_credit == D(6000)
    assert r.reintegration_10100 == D(1000) and r.exemption_10105 == 0


def test_exoneration_sans_heures_et_sans_credit():
    r = resultat(profil(choix="exoneration", activites=(), heures_certifiees=False, aucun_double_compte=False))
    assert r.exemption_10105 == D(1000)
    assert r.base_credit == r.reintegration_10100 == 0
    assert r.ligne_credit == ""


@pytest.mark.parametrize("modification", [{"services_similaires_remuneres": True}, {"organisme_admissible": False}])
def test_organisme_exclu_ne_contribue_pas_au_seuil(modification):
    p = profil(activites=(activite(heures=D(100)), activite(organisme="Organisme exclu", **modification)))
    with pytest.raises(ValueError, match="200 heures"):
        resultat(p)
    r = resultat(replace(p, activites=(activite(), p.activites[1])))
    assert r.heures_pompiers == D(200) and r.heures_exclues == D(200)


def test_choix_activite_sans_heures_et_doublons_refuses():
    for p in (profil(choix="sauvetage"), profil(activites=(activite(), activite(organisme=" service fictif "))), profil(choix="les_deux")):
        with pytest.raises(ValueError):
            resultat(p)


@pytest.mark.parametrize("valeur", [D("NaN"), D("sNaN"), D("Infinity"), D("-Infinity"), D(-1), D(0), D("1.001"), D(8761), D("1e100"), "200", None, True])
def test_heures_invalides(valeur):
    with pytest.raises(ValueError):
        resultat(profil(activites=(activite(heures=valeur),)))


@pytest.mark.parametrize("nom", CONFIRMATIONS_BENEVOLES)
@pytest.mark.parametrize("valeur", [False, "true", 1])
def test_confirmations_strictes(nom, valeur):
    with pytest.raises(ValueError):
        resultat(profil(**{nom: valeur}))


@pytest.mark.parametrize("valeur", ["NaN", "sNaN", "Infinity", "-1", "1000.01", "0.001"])
def test_case87_invalide(valeur):
    with pytest.raises(ValueError):
        resultat(d=dossier(valeur))


def test_case87_choix_source_statut_et_doublons():
    d = dossier()
    with pytest.raises(ValueError, match="choix explicite"):
        calcul(d)
    for invalide in (
        replace(d, donnees_validees=d.donnees_validees + (d.donnees_validees[-1],)),
        replace(d, donnees_validees=d.donnees_validees[:-1] + (replace(d.donnees_validees[-1], statut="À vérifier"),)),
        replace(d, donnees_validees=d.donnees_validees[:-1] + (replace(d.donnees_validees[-1], document=Path("inconnu.pdf")),)),
        replace(d, donnees_validees=tuple(x for x in d.donnees_validees if (x.type_document, x.case) != ("T4", "14"))),
    ):
        with pytest.raises(ValueError):
            resultat(d=invalide)


@pytest.mark.parametrize("mot", ["Case", "Box", "Code"])
def test_extraction_case87(mot):
    cases = extraire_cases_fiscales("T4", f"{mot} 87 1 000,00\nBox 14 52000.00", "fictif.pdf")
    assert {x.case: x.valeur for x in cases} == {"87": D(1000), "14": D(52000)}


def test_estimation_reintegration_separee_et_choix_exclusif():
    avant = calcul(_dossier_52000())
    e = calcul(dossier(), benevoles=profil())
    assert e.base.revenu_emploi_federal == D(53000)
    assert e.revenu.revenu_total_federal == D(53000)
    assert e.revenu.revenu_net_federal == D(52515)
    assert e.base.revenu_emploi_quebec == D(52000)
    assert e.quebec == avant.quebec
    assert e.base.gains_admissibles_rrq == avant.base.gains_admissibles_rrq
    assert dict(e.federal.credits_federaux_complets.montants_par_ligne)["31220"] == D(6000)
    assert "31240" not in dict(e.federal.credits_federaux_complets.montants_par_ligne)
    verifier_t1(e)
    exonere = calcul(dossier(), benevoles=profil(choix="exoneration", activites=()))
    assert exonere.revenu == avant.revenu and exonere.federal == avant.federal
    assert exonere.resultat_benevoles.exemption_10105 == D(1000)


def test_stockage_ancien_json_divergence_et_resultats_non_persistes(tmp_path):
    e = calcul(dossier(), benevoles=profil())
    f = sauvegarder_dossier_fiscal(e.dossier, estimation=e, destination=tmp_path / "cas.json")
    c = charger_dossier_fiscal(f)
    assert c.benevoles == profil()
    assert calcul(c.dossier, benevoles=c.benevoles) == e
    brut = json.loads(f.read_text(encoding="utf-8"))
    assert brut["benevoles"]["activites"][0]["heures"] == "200.00"
    assert "base_credit" not in brut["benevoles"]
    with pytest.raises(ValueError, match="diffère"):
        sauvegarder_dossier_fiscal(e.dossier, estimation=e, benevoles=profil(choix="exoneration"), destination=f)
    f = sauvegarder_dossier_fiscal(_dossier_52000(), destination=tmp_path / "ancien.json")
    brut = json.loads(f.read_text(encoding="utf-8"))
    del brut["benevoles"]
    f.write_text(json.dumps(brut), encoding="utf-8")
    assert charger_dossier_fiscal(f).benevoles == Benevoles2025()


@pytest.mark.parametrize("brut", [[], {"inconnu": 1}, {"activites": {}}, {"activites": [{"inconnu": 1}]}, {"activites": [None]}, {"choix_confirme": "true"}])
def test_json_invalide(tmp_path, brut):
    f = sauvegarder_dossier_fiscal(_dossier_52000(), destination=tmp_path / "cas.json")
    contenu = json.loads(f.read_text(encoding="utf-8"))
    contenu["benevoles"] = brut
    f.write_text(json.dumps(contenu), encoding="utf-8")
    with pytest.raises(ValueError):
        charger_dossier_fiscal(f)


def test_trace_et_pdf(tmp_path):
    e = calcul(dossier(), benevoles=profil())
    trace = construire_trace_calcul_fiscal_2025(e)
    assert "14 + 87" in trace.lignes[0].source
    assert trace.lignes[0].montant == D(53000)
    assert next(l for l in trace.lignes if l.libelle == "Case 87 réintégrée à 10100").montant == D(1000)
    assert next(l for l in trace.lignes if l.libelle == "Base bénévoles — ligne 31220").montant == D(6000)
    assert [l.ordre for l in trace.lignes] == list(range(1, len(trace.lignes) + 1))
    f = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "rapport.pdf")
    with fitz.open(f) as pdf:
        texte = "\n".join(page.get_text() for page in pdf)
        assert "31220" in texte and "6000.00" in texte and "Service fictif" in texte and "10105" in texte
        for page in pdf:
            for x0, y0, x1, y1, *_ in page.get_text("blocks"):
                assert 0 <= x0 < x1 <= page.rect.width
                assert 0 <= y0 < y1 <= page.rect.height


def test_scolarite_traitee_apres_la_base_benevoles():
    from tests.test_tax_tuition_carryforward_2025 import frais
    from tests.test_tax_workers_benefit_2025 import dossier_20000
    avant = calcul(dossier_20000(), frais_scolarite=frais())
    e = calcul(dossier_20000(), frais_scolarite=frais(), benevoles=profil())
    assert avant.resultat_reports_scolarite.ligne_32300 == D("983.20")
    assert e.resultat_reports_scolarite.ligne_32300 == 0
    assert e.resultat_reports_scolarite.report_futur == D(4000)
    verifier_t1(e)


def test_case87_entre_dans_le_revenu_utilise_pour_act():
    from tests.test_tax_workers_benefit_2025 import dossier_20000, profil as act
    d = dossier_20000()
    t4 = next(x.document for x in d.donnees_validees if x.type_document == "T4")
    d = replace(d, donnees_validees=d.donnees_validees + (_validee(t4, "T4", "87", "1000"),))
    avant = calcul(d, benevoles=profil(choix="exoneration"), allocation_travailleurs=act())
    e = calcul(d, benevoles=profil(), allocation_travailleurs=act())
    assert e.base.revenu_emploi_federal == D(21000)
    assert e.revenu.revenu_net_federal == D(20835)
    assert avant.resultat_allocation_travailleurs.ligne_45300 - e.resultat_allocation_travailleurs.ligne_45300 == D(200)
    verifier_t1(e)


def test_transfert_conjoint_rejoue_benevoles_dans_ligne100(tmp_path):
    from tests.test_tax_spouse_transfer_2025 import profil as transfert
    from tests.test_tax_interest_income_2025 import dossier_interets, profil_interets
    from tests.test_tax_federal_age_pension_integration_2025 import _profil_age_federal
    from src.comptaprivee.tax_spouse_transfer_2025 import instantane_conjoint_2025
    d = replace(dossier_interets("25000"), client="Conjoint fictif")
    a = _profil_age_federal(revenu_net_ligne_23600=D(25000))
    f = sauvegarder_dossier_fiscal(d, benevoles=profil(), profil_interets=profil_interets(),
        credits_federaux_age_pension=a, destination=tmp_path / "donneur.json")
    p = replace(transfert(tmp_path), dossier_conjoint_json=instantane_conjoint_2025(json.loads(f.read_text(encoding="utf-8"))))
    e = calcul(_dossier_52000(), transfert_conjoint=p)
    assert e.resultat_transfert_conjoint.base_ligne_100 == D(6000)
    assert e.resultat_transfert_conjoint.reduction_36100 == D(2871)
    assert e.resultat_transfert_conjoint.ligne_32600 == D(6157)
    verifier_t1(e)
