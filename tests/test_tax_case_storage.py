import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
import pytest

from src.comptaprivee.tax_case_storage import (
    charger_dossier_fiscal,
    lister_dossiers_fiscaux,
    nom_fichier_dossier_fiscal,
    sauvegarder_dossier_fiscal,
)
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
from src.comptaprivee.tax_field_validation import DonneeFiscaleValidee
from src.comptaprivee.tax_validated_case import DossierFiscalValide


def _v(doc, typ, case, valeur):
    m = Decimal(valeur)
    return DonneeFiscaleValidee(
        document=Path(doc), type_document=typ, case=case,
        libelle=f"{typ} {case}", valeur_extraite=m,
        valeur_validee=m, corrigee=False, statut="Validé par le comptable",
    )


def _dossier():
    donnees = (
        _v("data/exports/T4.pdf","T4","14","52000"),
        _v("data/exports/T4.pdf","T4","17","3104.00"),
        _v("data/exports/T4.pdf","T4","18","681.20"),
        _v("data/exports/T4.pdf","T4","22","7500"),
        _v("data/exports/T4.pdf","T4","24","52000"),
        _v("data/exports/T4.pdf","T4","26","52000"),
        _v("data/exports/T4.pdf","T4","55","256.88"),
        _v("data/exports/T4.pdf","T4","56","52000"),
        _v("data/exports/RL1.pdf","RL-1","A","52000"),
        _v("data/exports/RL1.pdf","RL-1","B.A","3104.00"),
        _v("data/exports/RL1.pdf","RL-1","C","681.20"),
        _v("data/exports/RL1.pdf","RL-1","E","6200"),
        _v("data/exports/RL1.pdf","RL-1","G","52000"),
        _v("data/exports/RL1.pdf","RL-1","H","256.88"),
        _v("data/exports/RL1.pdf","RL-1","I","52000"),
    )
    return DossierFiscalValide(
        client="Client Test", annee_fiscale=2025, province="Québec",
        documents=(Path("data/exports/T4.pdf"), Path("data/exports/RL1.pdf")),
        donnees_validees=donnees,
    )


def test_nom_fichier_dossier():
    assert nom_fichier_dossier_fiscal(_dossier()) == "Dossier_Fiscal_2025_Client_Test.json"


def test_nom_fichier_nettoie_caracteres():
    nom = nom_fichier_dossier_fiscal(replace(_dossier(), client="Client / Test : Montréal"))
    assert "/" not in nom and ":" not in nom and nom.endswith(".json")


def test_sauvegarde_cree_json(tmp_path):
    p = sauvegarder_dossier_fiscal(_dossier(), destination=tmp_path / "dossier")
    assert p.exists() and p.suffix == ".json"


def test_recharge_identite(tmp_path):
    p = sauvegarder_dossier_fiscal(_dossier(), destination=tmp_path / "d.json")
    x = charger_dossier_fiscal(p)
    assert (x.dossier.client, x.dossier.annee_fiscale, x.dossier.province) == ("Client Test", 2025, "Québec")


def test_recharge_15_valeurs(tmp_path):
    p = sauvegarder_dossier_fiscal(_dossier(), destination=tmp_path / "d.json")
    assert len(charger_dossier_fiscal(p).dossier.donnees_validees) == 15


def test_conserve_decimal_exact(tmp_path):
    p = sauvegarder_dossier_fiscal(_dossier(), destination=tmp_path / "d.json")
    vals = {(d.type_document,d.case):d.valeur_validee for d in charger_dossier_fiscal(p).dossier.donnees_validees}
    assert vals[("T4","17")] == Decimal("3104.00") and vals[("RL-1","H")] == Decimal("256.88")


def test_sauvegarde_resume_estimation(tmp_path):
    d = _dossier()
    p = sauvegarder_dossier_fiscal(d, estimation=calculer_estimation_fiscale_2025(d), destination=tmp_path / "d.json")
    e = charger_dossier_fiscal(p).estimation
    assert e and e.resultat == "Remboursement estimé" and e.montant == Decimal("5611.05")


def test_sauvegarde_rapport_pdf(tmp_path):
    rapport = tmp_path / "rapport.pdf"; rapport.write_bytes(b"%PDF-test")
    p = sauvegarder_dossier_fiscal(_dossier(), rapport_pdf=rapport, destination=tmp_path / "d.json")
    assert charger_dossier_fiscal(p).rapport_pdf == rapport


def test_detecte_documents_manquants(tmp_path):
    p = sauvegarder_dossier_fiscal(_dossier(), destination=tmp_path / "d.json")
    assert len(charger_dossier_fiscal(p).documents_manquants) == 2


def test_liste_dossiers(tmp_path):
    sauvegarder_dossier_fiscal(_dossier(), destination=tmp_path / "a.json")
    sauvegarder_dossier_fiscal(replace(_dossier(), client="Deuxième Client"), destination=tmp_path / "b.json")
    assert len(lister_dossiers_fiscaux(tmp_path)) == 2


def test_liste_ignore_json_invalide(tmp_path):
    (tmp_path / "x.json").write_text("{pas json", encoding="utf-8")
    assert lister_dossiers_fiscaux(tmp_path) == ()


def test_refuse_schema_inconnu(tmp_path):
    p = tmp_path / "d.json"; p.write_text(json.dumps({"schema_version":999}), encoding="utf-8")
    with pytest.raises(ValueError): charger_dossier_fiscal(p)


def test_refuse_statut_invalide(tmp_path):
    p = sauvegarder_dossier_fiscal(_dossier(), destination=tmp_path / "d.json")
    brut = json.loads(p.read_text(encoding="utf-8")); brut["donnees_validees"][0]["statut"] = "Non validé"
    p.write_text(json.dumps(brut, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError): charger_dossier_fiscal(p)


def test_ecrasement_atomique(tmp_path):
    p = tmp_path / "d.json"
    sauvegarder_dossier_fiscal(_dossier(), destination=p)
    sauvegarder_dossier_fiscal(replace(_dossier(), client="Client Modifié"), destination=p)
    assert charger_dossier_fiscal(p).dossier.client == "Client Modifié"
    assert not (tmp_path / "d.json.tmp").exists()

def test_stockage_dossiers_est_ancre_sur_racine_projet():
    from src.comptaprivee.tax_case_storage import (
        DOSSIERS_FISCAUX_DIR,
        PROJECT_ROOT,
    )

    assert PROJECT_ROOT.is_absolute()
    assert DOSSIERS_FISCAUX_DIR.is_absolute()
    assert DOSSIERS_FISCAUX_DIR == (
        PROJECT_ROOT / "data" / "dossiers_fiscaux"
    )


def test_chemin_recharge_independant_du_dossier_courant(
    tmp_path,
    monkeypatch,
):
    from src.comptaprivee.tax_case_storage import (
        PROJECT_ROOT,
        _chemin_depuis_stockage,
    )

    monkeypatch.chdir(tmp_path)

    chemin = _chemin_depuis_stockage(
        "data/exports/rapport_test.pdf"
    )

    assert chemin == (
        PROJECT_ROOT
        / "data"
        / "exports"
        / "rapport_test.pdf"
    )
