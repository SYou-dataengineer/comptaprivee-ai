from dataclasses import replace
from decimal import Decimal as D
import json
import fitz
import pytest
from src.comptaprivee.tax_tuition_received_2025 import (
    DesignationScolariteRecue2025, TransfertsScolariteRecus2025, CONFIRMATIONS_SCOLARITE_RECUE,
    RELATIONS_SCOLARITE_RECUE, montant_ligne_32400_2025,
)
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calcul
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_top_up_integration_2025 import verifier_t1


def designation(**kw):
    valeurs = dict(reference_etudiant="ETU-1", nom_etudiant="Étudiant fictif", relation="parent",
        montant_certificat=D(3000), source="Certificat signé et annexe 11 fictifs",
        **{nom: True for nom in CONFIRMATIONS_SCOLARITE_RECUE})
    valeurs.update(kw)
    return DesignationScolariteRecue2025(**valeurs)


def profil(**kw):
    return TransfertsScolariteRecus2025((designation(**kw),))


def test_vide_et_plusieurs_etudiants_plafond_individuel():
    assert montant_ligne_32400_2025(TransfertsScolariteRecus2025()) == 0
    p = TransfertsScolariteRecus2025((designation(montant_certificat=D(5000)),
        designation(reference_etudiant="ETU-2", montant_certificat=D(5000))))
    assert montant_ligne_32400_2025(p) == D(10000)
    assert montant_ligne_32400_2025(profil(montant_certificat=D("0.01"))) == D("0.01")


@pytest.mark.parametrize("relation", RELATIONS_SCOLARITE_RECUE)
def test_relations(relation):
    assert montant_ligne_32400_2025(profil(relation=relation)) == D(3000)


@pytest.mark.parametrize("montant", [D(0), D(-1), D("5000.01"), D("1e100"), D("1.001"), D("NaN"), D("sNaN"), D("Infinity"), D("-Infinity"), "3000", 3000.0])
def test_montants_invalides(montant):
    with pytest.raises(ValueError):
        montant_ligne_32400_2025(profil(montant_certificat=montant))


@pytest.mark.parametrize("nom", CONFIRMATIONS_SCOLARITE_RECUE)
@pytest.mark.parametrize("valeur", [False, "true", 1])
def test_confirmations_strictes(nom, valeur):
    with pytest.raises(ValueError):
        montant_ligne_32400_2025(profil(**{nom: valeur}))


@pytest.mark.parametrize("champ", ["reference_etudiant", "nom_etudiant", "source", "relation"])
@pytest.mark.parametrize("valeur", [" ", None])
def test_identification_obligatoire(champ, valeur):
    with pytest.raises(ValueError):
        montant_ligne_32400_2025(profil(**{champ: valeur}))


def test_conjoint_et_doublon_refuses():
    with pytest.raises(ValueError, match="32600"):
        montant_ligne_32400_2025(profil(relation="conjoint"))
    with pytest.raises(ValueError, match="deux fois"):
        montant_ligne_32400_2025(TransfertsScolariteRecus2025((designation(), designation(reference_etudiant=" etu-1 "))))
    for p in (None, TransfertsScolariteRecus2025([]), TransfertsScolariteRecus2025((None,))):
        with pytest.raises(ValueError):
            montant_ligne_32400_2025(p)


def test_estimation_base_credit_abatement_et_absence_report():
    avant = calcul(_dossier_52000())
    e = calcul(_dossier_52000(), transferts_scolarite_recus=profil())
    c, a = e.federal.credits_federaux_complets, avant.federal.credits_federaux_complets
    assert dict(c.montants_par_ligne)["32400"] == D(3000)
    assert c.base_ligne_33500 - a.base_ligne_33500 == D(3000)
    assert c.credit_ligne_33800 - a.credit_ligne_33800 == D(435)
    assert e.revenu == avant.revenu and e.quebec == avant.quebec
    assert e.resultat_reports_scolarite == avant.resultat_reports_scolarite
    verifier_t1(e)


def test_reports_personnels_et_transfert_sortant_independants():
    from tests.test_tax_tuition_transfer_2025 import frais
    from tests.test_tax_workers_benefit_2025 import dossier_20000
    avant = calcul(dossier_20000(), frais_scolarite=frais())
    e = calcul(dossier_20000(), frais_scolarite=frais(), transferts_scolarite_recus=profil())
    assert e.resultat_reports_scolarite == avant.resultat_reports_scolarite
    assert e.federal.impot_federal_de_base == 0
    assert dict(e.federal.credits_federaux_complets.montants_par_ligne)["32400"] == D(3000)
    verifier_t1(e)


def test_stockage_recalcul_ancien_json_divergence(tmp_path):
    e = calcul(_dossier_52000(), transferts_scolarite_recus=profil())
    fichier = sauvegarder_dossier_fiscal(e.dossier, estimation=e, destination=tmp_path / "cas.json")
    c = charger_dossier_fiscal(fichier)
    assert c.transferts_scolarite_recus == profil()
    assert calcul(c.dossier, transferts_scolarite_recus=c.transferts_scolarite_recus) == e
    brut = json.loads(fichier.read_text(encoding="utf-8"))
    assert brut["transferts_scolarite_recus"]["designations"][0]["montant_certificat"] == "3000.00"
    assert "ligne_32400" not in brut["transferts_scolarite_recus"]
    with pytest.raises(ValueError, match="diffère"):
        sauvegarder_dossier_fiscal(e.dossier, estimation=e, transferts_scolarite_recus=TransfertsScolariteRecus2025(), destination=tmp_path / "refus.json")
    del brut["transferts_scolarite_recus"]
    fichier.write_text(json.dumps(brut), encoding="utf-8")
    assert charger_dossier_fiscal(fichier).transferts_scolarite_recus == TransfertsScolariteRecus2025()


@pytest.mark.parametrize("valeur", [[], {"inconnu": 1}, {"designations": {}}, {"designations": [None]}, {"designations": [{"inconnu": 1}]}])
def test_json_structure_invalide(tmp_path, valeur):
    fichier = sauvegarder_dossier_fiscal(_dossier_52000(), destination=tmp_path / "cas.json")
    brut = json.loads(fichier.read_text(encoding="utf-8"))
    brut["transferts_scolarite_recus"] = valeur
    fichier.write_text(json.dumps(brut), encoding="utf-8")
    with pytest.raises(ValueError):
        charger_dossier_fiscal(fichier)


@pytest.mark.parametrize("champ,valeur", [("montant_certificat", "NaN"), ("certificat_signe", "true"), ("relation", "conjoint")])
def test_json_donnees_invalides(tmp_path, champ, valeur):
    fichier = sauvegarder_dossier_fiscal(_dossier_52000(), transferts_scolarite_recus=profil(), destination=tmp_path / "cas.json")
    brut = json.loads(fichier.read_text(encoding="utf-8"))
    brut["transferts_scolarite_recus"]["designations"][0][champ] = valeur
    fichier.write_text(json.dumps(brut), encoding="utf-8")
    with pytest.raises(ValueError):
        charger_dossier_fiscal(fichier)


def test_trace_et_pdf(tmp_path):
    e = calcul(_dossier_52000(), transferts_scolarite_recus=profil())
    trace = construire_trace_calcul_fiscal_2025(e)
    assert next(x for x in trace.lignes if x.libelle == "Scolarité reçue 32400").montant == D(3000)
    assert [x.ordre for x in trace.lignes] == list(range(1, len(trace.lignes) + 1))
    fichier = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "cas.pdf")
    with fitz.open(fichier) as pdf:
        texte = "\n".join(p.get_text() for p in pdf)
        for p in pdf:
            for x0, y0, x1, y1, *_ in p.get_text("blocks"):
                assert 0 <= x0 < x1 <= p.rect.width
                assert 0 <= y0 < y1 <= p.rect.height
    assert "Ligne 32400 : 3000.00" in texte
    assert "Étudiant fictif" in texte and "Certificat signé et annexe 11 fictifs" in texte


def test_plusieurs_designations_recalculent_credit_compensatoire():
    p = TransfertsScolariteRecus2025(tuple(designation(reference_etudiant=f"E{i}", montant_certificat=D(5000)) for i in range(12)))
    e = calcul(_dossier_52000(), transferts_scolarite_recus=p)
    c = e.federal.credits_federaux_complets
    assert dict(c.montants_par_ligne)["32400"] == D(60000)
    assert c.credit_compensatoire_ligne_34990 > 0
    assert e.federal.impot_federal_de_base == 0
    assert e.resultat_reports_scolarite.report_futur == 0
    verifier_t1(e)
