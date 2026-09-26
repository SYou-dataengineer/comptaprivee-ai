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

# --- Priorité 4A : persistance CELIAPP ---

from src.comptaprivee.tax_fhsa_2025 import DeductionCeliapp2025


def _celiapp_4a_stockage():
    return DeductionCeliapp2025(
        deduction=Decimal("5000"),
        cotisations_directes_2025=Decimal("6000"),
        droits_deduction_confirmes=Decimal("8000"),
        source_droits="Annexe 15 / relevé CELIAPP 2025",
        valide_par_comptable=True,
        titulaire_confirme=True,
        residence_canada_quebec_annee_complete=True,
    )


def test_stockage_celiapp_4a_roundtrip_direct(tmp_path):
    profil = _celiapp_4a_stockage()
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        deduction_celiapp=profil,
        destination=tmp_path / "d.json",
    )
    charge = charger_dossier_fiscal(p)
    assert charge.deduction_celiapp == profil


def test_stockage_celiapp_4a_depuis_estimation(tmp_path):
    d = _dossier()
    profil = _celiapp_4a_stockage()
    estimation = calculer_estimation_fiscale_2025(
        d,
        deduction_celiapp=profil,
    )
    p = sauvegarder_dossier_fiscal(
        d,
        estimation=estimation,
        destination=tmp_path / "d.json",
    )
    charge = charger_dossier_fiscal(p)
    assert charge.deduction_celiapp == profil
    assert charge.estimation is not None


def test_stockage_celiapp_4a_refuse_profil_different_estimation(tmp_path):
    d = _dossier()
    estimation = calculer_estimation_fiscale_2025(
        d,
        deduction_celiapp=_celiapp_4a_stockage(),
    )
    autre = replace(
        _celiapp_4a_stockage(),
        deduction=Decimal("4000"),
    )
    with pytest.raises(ValueError, match="CELIAPP diffère"):
        sauvegarder_dossier_fiscal(
            d,
            estimation=estimation,
            deduction_celiapp=autre,
            destination=tmp_path / "d.json",
        )


def test_stockage_ancien_json_sans_celiapp_reste_compatible(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut.pop("deduction_celiapp", None)
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    charge = charger_dossier_fiscal(p)
    assert charge.deduction_celiapp == DeductionCeliapp2025()


def test_stockage_celiapp_invalide_est_refuse_au_rechargement(tmp_path):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["deduction_celiapp"] = {
        "deduction": "5000",
        "cotisations_directes_2025": "1000",
        "droits_deduction_confirmes": "8000",
        "source_droits": "Annexe 15",
        "valide_par_comptable": True,
        "titulaire_confirme": True,
        "residence_canada_quebec_annee_complete": True,
    }
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="cotisations directes"):
        charger_dossier_fiscal(p)

# --- Priorité 4B : persistance frais de garde fédéraux ---

from src.comptaprivee.tax_child_care_2025 import FraisGardeFederaux2025


def _frais_garde_4b_stockage():
    return FraisGardeFederaux2025(
        frais_admissibles_payes=Decimal("6000"),
        revenu_gagne_t778=Decimal("52000"),
        nombre_enfants_moins_7_sans_dtc=1,
        nombre_enfants_7_a_16_ou_infirmes_sans_dtc=0,
        nombre_enfants_dtc=0,
        source="T778 2025 / reçus de garde",
        valide_par_comptable=True,
        services_fournis_en_2025_confirmes=True,
        frais_pour_gagner_revenu_confirmes=True,
        recus_confirmes=True,
        demandeur_seul_ou_revenu_inferieur_confirme=True,
    )


def test_stockage_frais_garde_4b_roundtrip_direct(tmp_path):
    profil = _frais_garde_4b_stockage()
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        frais_garde_federaux=profil,
        destination=tmp_path / "d.json",
    )
    assert charger_dossier_fiscal(p).frais_garde_federaux == profil


def test_stockage_frais_garde_4b_depuis_estimation(tmp_path):
    d = _dossier()
    profil = _frais_garde_4b_stockage()
    estimation = calculer_estimation_fiscale_2025(
        d,
        frais_garde_federaux=profil,
    )
    p = sauvegarder_dossier_fiscal(
        d,
        estimation=estimation,
        destination=tmp_path / "d.json",
    )
    charge = charger_dossier_fiscal(p)
    assert charge.frais_garde_federaux == profil
    assert charge.estimation is not None


def test_stockage_frais_garde_4b_refuse_profil_different_estimation(tmp_path):
    d = _dossier()
    profil = _frais_garde_4b_stockage()
    estimation = calculer_estimation_fiscale_2025(
        d,
        frais_garde_federaux=profil,
    )
    autre = replace(profil, frais_admissibles_payes=Decimal("5000"))
    with pytest.raises(ValueError, match="frais de garde fédéraux diffèrent"):
        sauvegarder_dossier_fiscal(
            d,
            estimation=estimation,
            frais_garde_federaux=autre,
            destination=tmp_path / "d.json",
        )


def test_stockage_ancien_json_sans_frais_garde_4b_reste_compatible(tmp_path):
    p = sauvegarder_dossier_fiscal(_dossier(), destination=tmp_path / "d.json")
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut.pop("frais_garde_federaux", None)
    p.write_text(json.dumps(brut, ensure_ascii=False, indent=2), encoding="utf-8")
    assert charger_dossier_fiscal(p).frais_garde_federaux == FraisGardeFederaux2025()


def test_stockage_frais_garde_4b_invalide_est_refuse_au_rechargement(tmp_path):
    p = sauvegarder_dossier_fiscal(_dossier(), destination=tmp_path / "d.json")
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["frais_garde_federaux"] = {
        "frais_admissibles_payes": "6000",
        "revenu_gagne_t778": "52000",
        "nombre_enfants_moins_7_sans_dtc": 1,
        "nombre_enfants_7_a_16_ou_infirmes_sans_dtc": 0,
        "nombre_enfants_dtc": 0,
        "source": "T778 2025",
        "valide_par_comptable": True,
        "services_fournis_en_2025_confirmes": True,
        "frais_pour_gagner_revenu_confirmes": True,
        "recus_confirmes": True,
        "demandeur_seul_ou_revenu_inferieur_confirme": True,
        "garde_partagee": True,
    }
    p.write_text(json.dumps(brut, ensure_ascii=False, indent=2), encoding="utf-8")
    with pytest.raises(ValueError, match="hors périmètre 4B"):
        charger_dossier_fiscal(p)

# --- Priorité 4C : persistance dépenses d'emploi ---

from src.comptaprivee.tax_employment_expenses_2025 import DepensesEmploi2025


def _depenses_emploi_4c_stockage():
    return DepensesEmploi2025(
        deduction_federale_t777=Decimal("1200"),
        deduction_quebec_tp59=Decimal("1000"),
        source_federale="T2200 + T777 2025",
        source_quebec="TP-64.3 + TP-59 2025",
        valide_par_comptable=True,
        salarie_ordinaire_confirme=True,
        contrat_exige_depenses_confirme=True,
        non_remboursees_confirme=True,
        t2200_confirme=True,
        t777_confirme=True,
        tp_64_3_confirme=True,
        tp_59_confirme=True,
    )


def test_stockage_depenses_emploi_4c_roundtrip_direct(tmp_path):
    profil = _depenses_emploi_4c_stockage()
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        depenses_emploi=profil,
        destination=tmp_path / "d.json",
    )
    assert charger_dossier_fiscal(p).depenses_emploi == profil


def test_stockage_depenses_emploi_4c_depuis_estimation(tmp_path):
    d = _dossier()
    profil = _depenses_emploi_4c_stockage()
    estimation = calculer_estimation_fiscale_2025(
        d,
        depenses_emploi=profil,
    )
    p = sauvegarder_dossier_fiscal(
        d,
        estimation=estimation,
        destination=tmp_path / "d.json",
    )
    charge = charger_dossier_fiscal(p)

    assert charge.depenses_emploi == profil
    assert charge.estimation is not None


def test_stockage_depenses_emploi_4c_refuse_profil_different_estimation(
    tmp_path,
):
    d = _dossier()
    profil = _depenses_emploi_4c_stockage()
    estimation = calculer_estimation_fiscale_2025(
        d,
        depenses_emploi=profil,
    )
    autre = replace(
        profil,
        deduction_federale_t777=Decimal("900"),
    )

    with pytest.raises(ValueError, match="dépenses d'emploi diffèrent"):
        sauvegarder_dossier_fiscal(
            d,
            estimation=estimation,
            depenses_emploi=autre,
            destination=tmp_path / "d.json",
        )


def test_stockage_ancien_json_sans_depenses_emploi_4c_reste_compatible(
    tmp_path,
):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut.pop("depenses_emploi", None)
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    assert (
        charger_dossier_fiscal(p).depenses_emploi
        == DepensesEmploi2025()
    )


def test_stockage_depenses_emploi_4c_invalide_est_refuse_au_rechargement(
    tmp_path,
):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["depenses_emploi"] = {
        "deduction_federale_t777": "1200",
        "deduction_quebec_tp59": "1000",
        "source_federale": "T2200 + T777 2025",
        "source_quebec": "TP-64.3 + TP-59 2025",
        "valide_par_comptable": True,
        "salarie_ordinaire_confirme": True,
        "contrat_exige_depenses_confirme": True,
        "non_remboursees_confirme": True,
        "t2200_confirme": True,
        "t777_confirme": True,
        "tp_64_3_confirme": True,
        "tp_59_confirme": True,
        "employe_a_commission": True,
    }
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="hors périmètre 4C"):
        charger_dossier_fiscal(p)


# --- Priorité 4D : persistance frais de déménagement ---

from src.comptaprivee.tax_moving_expenses_2025 import FraisDemenagement2025


def _frais_demenagement_4d_stockage():
    return FraisDemenagement2025(
        deduction_federale_t1m=Decimal("2200"),
        deduction_quebec_tp348=Decimal("1800"),
        source_federale="T1-M 2025 validé",
        source_quebec="TP-348 2025 validé",
        valide_par_comptable=True,
        salarie_ordinaire_confirme=True,
        demenagement_pour_emploi_confirme=True,
        rapprochement_40km_confirme=True,
        demenagement_interieur_canada_confirme=True,
        remboursements_employeur_pris_en_compte_confirme=True,
        t1m_confirme=True,
        tp348_confirme=True,
    )


def test_stockage_frais_demenagement_4d_roundtrip_direct(tmp_path):
    profil = _frais_demenagement_4d_stockage()
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        frais_demenagement=profil,
        destination=tmp_path / "d.json",
    )
    assert charger_dossier_fiscal(p).frais_demenagement == profil


def test_stockage_frais_demenagement_4d_depuis_estimation(tmp_path):
    d = _dossier()
    profil = _frais_demenagement_4d_stockage()
    estimation = calculer_estimation_fiscale_2025(
        d,
        frais_demenagement=profil,
    )
    p = sauvegarder_dossier_fiscal(
        d,
        estimation=estimation,
        destination=tmp_path / "d.json",
    )
    charge = charger_dossier_fiscal(p)
    assert charge.frais_demenagement == profil
    assert charge.estimation is not None


def test_stockage_frais_demenagement_4d_refuse_profil_different_estimation(
    tmp_path,
):
    d = _dossier()
    profil = _frais_demenagement_4d_stockage()
    estimation = calculer_estimation_fiscale_2025(
        d,
        frais_demenagement=profil,
    )
    autre = replace(
        profil,
        deduction_federale_t1m=Decimal("1700"),
    )
    with pytest.raises(ValueError, match="frais de déménagement diffèrent"):
        sauvegarder_dossier_fiscal(
            d,
            estimation=estimation,
            frais_demenagement=autre,
            destination=tmp_path / "d.json",
        )


def test_stockage_ancien_json_sans_frais_demenagement_4d_reste_compatible(
    tmp_path,
):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut.pop("frais_demenagement", None)
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    assert (
        charger_dossier_fiscal(p).frais_demenagement
        == FraisDemenagement2025()
    )


def test_stockage_frais_demenagement_4d_invalide_est_refuse_au_rechargement(
    tmp_path,
):
    p = sauvegarder_dossier_fiscal(
        _dossier(),
        destination=tmp_path / "d.json",
    )
    brut = json.loads(p.read_text(encoding="utf-8"))
    brut["frais_demenagement"] = {
        "deduction_federale_t1m": "2200",
        "deduction_quebec_tp348": "1800",
        "source_federale": "T1-M 2025 validé",
        "source_quebec": "TP-348 2025 validé",
        "valide_par_comptable": True,
        "salarie_ordinaire_confirme": True,
        "demenagement_pour_emploi_confirme": True,
        "rapprochement_40km_confirme": True,
        "demenagement_interieur_canada_confirme": True,
        "remboursements_employeur_pris_en_compte_confirme": True,
        "t1m_confirme": True,
        "tp348_confirme": True,
        "demenagement_international": True,
    }
    p.write_text(
        json.dumps(brut, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="hors périmètre 4D"):
        charger_dossier_fiscal(p)
