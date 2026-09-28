from dataclasses import replace
from decimal import Decimal as D
import json
import fitz
import pytest
from src.comptaprivee.tax_tuition_transfer_2025 import (
    TransfertScolariteSortant2025, CONFIRMATIONS_TRANSFERT_SCOLARITE,
    RELATIONS_TRANSFERT_SCOLARITE, valider_transfert_scolarite_sortant_2025,
    calculer_transfert_scolarite_sortant_2025,
)
from src.comptaprivee.tax_tuition_carryforward_2025 import calculer_reports_scolarite_federaux_2025
from src.comptaprivee.tax_tuition_2025 import valider_frais_scolarite_2025
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calcul
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from tests.test_tax_tuition_carryforward_2025 import profil as reports, frais as frais_sans_transfert
from tests.test_tax_workers_benefit_2025 import dossier_20000


def profil(**kw):
    v = dict(montant_designe=D(1000), beneficiaire="Parent fictif", relation="parent",
             source="Certificat T2202 et autorisation fictifs", aucun_credit_conjoint_30300_30425_32600=True,
             **{nom: True for nom in CONFIRMATIONS_TRANSFERT_SCOLARITE})
    v.update(kw)
    return TransfertScolariteSortant2025(**v)


def frais(**kw):
    f = frais_sans_transfert()
    return replace(f, aucun_transfert=False, reports_federaux=replace(f.reports_federaux,
        aucun_transfert_entrant_sortant=False, transfert_sortant=profil(**kw)))


def montant(p=None, frais="6000", utilises="1000"):
    return calculer_transfert_scolarite_sortant_2025(p or profil(), frais_nets_2025=D(frais), frais_2025_utilises=D(utilises))


def test_plafond_avant_soustraction_usage_courant_et_choix_partiel():
    maximum, transfert = montant()
    assert maximum == D(4000)
    assert transfert == D(1000)
    assert montant(profil(montant_designe=D("123.45")))[1] == D("123.45")
    assert montant(profil(montant_designe=D(4000)))[1] == D(4000)
    with pytest.raises(ValueError, match="maximum"):
        montant(profil(montant_designe=D("4000.01")))


def test_zero_et_bornes_frais_utilises():
    assert montant(TransfertScolariteSortant2025(), "6000", "5500") == (D(0), D(0))
    assert montant(TransfertScolariteSortant2025(), "0", "0") == (D(0), D(0))
    assert montant(profil(montant_designe=D(5000)), "6000", "0") == (D(5000), D(5000))
    with pytest.raises(ValueError):
        montant(utilises="6001")
    with pytest.raises(ValueError):
        montant(frais="0", utilises="0")


@pytest.mark.parametrize("relation", RELATIONS_TRANSFERT_SCOLARITE)
def test_liens_admissibles(relation):
    assert montant(profil(relation=relation))[1] == D(1000)


def test_restriction_reclamation_du_conjoint():
    assert montant(profil(relation="conjoint", aucun_credit_conjoint_30300_30425_32600=False))[1] == D(1000)
    for relation in RELATIONS_TRANSFERT_SCOLARITE[1:]:
        with pytest.raises(ValueError, match="30300"):
            montant(profil(relation=relation, aucun_credit_conjoint_30300_30425_32600=False))


@pytest.mark.parametrize("nom", list(CONFIRMATIONS_TRANSFERT_SCOLARITE))
def test_confirmations(nom):
    for v in (False, "true"):
        with pytest.raises(ValueError):
            montant(profil(**{nom: v}))


@pytest.mark.parametrize("valeur", [D(-1), D("NaN"), D("sNaN"), D("Infinity"), D("-Infinity"), D("1.001"), D(5001), "5", 5.0])
def test_montants_invalides(valeur):
    with pytest.raises(ValueError):
        montant(profil(montant_designe=valeur))


@pytest.mark.parametrize("kw", [{"beneficiaire": ""}, {"source": " "}, {"relation": "frere"}, {"relation": None}, {"source": None}, {"aucun_credit_conjoint_30300_30425_32600": 1}])
def test_identification_invalide(kw):
    with pytest.raises(ValueError):
        montant(profil(**kw))


def test_reports_anciens_non_transferables():
    p = reports(report_avis_2024=D(10000), aucun_transfert_entrant_sortant=False, transfert_sortant=profil())
    with pytest.raises(ValueError, match="maximum"):
        calculer_reports_scolarite_federaux_2025(p, frais_nets_2025=D(0), revenu_imposable=D(20000),
            impot_brut=D(2900), base_ligne105=D(19000))


def test_contradictions_et_activation():
    f = frais()
    for p in (replace(f, aucun_transfert=True),
              replace(f, reports_federaux=replace(f.reports_federaux, aucun_transfert_entrant_sortant=True)),
              replace(f, reports_federaux=replace(f.reports_federaux, activer=False))):
        with pytest.raises(ValueError):
            valider_frais_scolarite_2025(p)


def test_estimation_transfert_diminue_uniquement_report_futur():
    avant = calcul(dossier_20000(), frais_scolarite=frais_sans_transfert())
    e = calcul(dossier_20000(), frais_scolarite=frais())
    assert e.revenu == avant.revenu and e.federal == avant.federal and e.quebec == avant.quebec
    assert e.rapprochement == avant.rapprochement
    r = e.resultat_reports_scolarite
    assert r.ligne_32300 == D("983.20")
    assert r.ligne_32700 == D(1000)
    assert r.transfert_maximal == D(3000)
    assert r.report_futur == D("2016.80")
    assert avant.resultat_reports_scolarite.report_futur - r.report_futur == D(1000)
    assert "32700" not in dict(e.federal.credits_federaux_complets.montants_par_ligne)


def test_formation_reduit_le_plafond_avant_transfert():
    from tests.test_tax_training_credit_2025 import frais as frais_formation
    from tests.test_tax_estimation_2025 import _dossier_52000
    f = replace(frais_formation(), aucun_report_anterieur=False, aucun_transfert=False,
        reports_federaux=reports(report_avis_2024=D(100000),
            aucun_transfert_entrant_sortant=False, transfert_sortant=profil()))
    e = calcul(_dossier_52000(), frais_scolarite=f)
    r = e.resultat_reports_scolarite
    assert r.frais_2025_nets == D(2250)
    assert r.frais_2025_utilises == 0
    assert r.transfert_maximal == D(2250)
    assert r.ligne_32700 == D(1000)
    assert r.report_futur == D(100000) + D(2250) - r.ligne_32300 - D(1000)
    trop = replace(f, reports_federaux=replace(f.reports_federaux,
        transfert_sortant=profil(montant_designe=D("2250.01"))))
    with pytest.raises(ValueError, match="maximum"):
        calcul(_dossier_52000(), frais_scolarite=trop)


def test_stockage_ancien_divergence(tmp_path):
    e = calcul(dossier_20000(), frais_scolarite=frais())
    f = sauvegarder_dossier_fiscal(e.dossier, estimation=e, destination=tmp_path / "cas.json")
    c = charger_dossier_fiscal(f)
    assert c.frais_scolarite == e.frais_scolarite
    assert calcul(c.dossier, frais_scolarite=c.frais_scolarite) == e
    brut = json.loads(f.read_text(encoding="utf-8"))
    p = brut["frais_scolarite"]["reports_federaux"]
    assert p["transfert_sortant"]["montant_designe"] == "1000.00"
    assert "transfert_maximal" not in p
    with pytest.raises(ValueError, match="diffère"):
        sauvegarder_dossier_fiscal(e.dossier, estimation=e, frais_scolarite=frais_sans_transfert(), destination=tmp_path / "refus.json")
    del p["transfert_sortant"]
    p["aucun_transfert_entrant_sortant"] = True
    brut["frais_scolarite"]["aucun_transfert"] = True
    f.write_text(json.dumps(brut), encoding="utf-8")
    assert charger_dossier_fiscal(f).frais_scolarite.reports_federaux.transfert_sortant == TransfertScolariteSortant2025()


@pytest.mark.parametrize("valeur", [{"inconnu": 1}, {"montant_designe": "NaN"}, {"autorisation_signee": "true"}, []])
def test_json_invalide(tmp_path, valeur):
    f = sauvegarder_dossier_fiscal(dossier_20000(), frais_scolarite=frais_sans_transfert(), destination=tmp_path / "cas.json")
    brut = json.loads(f.read_text(encoding="utf-8"))
    brut["frais_scolarite"]["reports_federaux"]["transfert_sortant"] = valeur
    f.write_text(json.dumps(brut), encoding="utf-8")
    with pytest.raises(ValueError):
        charger_dossier_fiscal(f)


def test_trace_pdf(tmp_path):
    e = calcul(dossier_20000(), frais_scolarite=frais())
    trace = construire_trace_calcul_fiscal_2025(e)
    assert next(x for x in trace.lignes if x.libelle == "Transfert sortant 32700").montant == D(1000)
    assert [x.ordre for x in trace.lignes] == list(range(1, len(trace.lignes) + 1))
    f = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "transfert.pdf")
    with fitz.open(f) as pdf:
        texte = "\n".join(page.get_text() for page in pdf)
        for page in pdf:
            for x0, y0, x1, y1, *_ in page.get_text("blocks"):
                assert 0 <= x0 < x1 <= page.rect.width
                assert 0 <= y0 < y1 <= page.rect.height
    assert "Parent fictif" in texte
    assert "ligne 32700 : 1000.00" in texte
    assert "Report fédéral futur calculé : 2016.80" in texte
