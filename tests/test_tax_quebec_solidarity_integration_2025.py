"""6H prépare des faits; il ne calcule aucun crédit de solidarité."""
from dataclasses import replace
from decimal import Decimal as D
import json

import fitz
import pytest

from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025 as calcul, formater_estimation_fiscale_2025,
)
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, dossier_fiscal_depuis_contenu
from src.comptaprivee.tax_calculation_trace_2025 import (
    construire_trace_calcul_fiscal_2025, formater_trace_calcul_fiscal_2025,
)
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from src.comptaprivee.tax_quebec_solidarity_2025 import SolidariteQuebec2025
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_quebec_solidarity_2025 import profil


@pytest.mark.parametrize("situation", ["remboursement", "solde", "zero"])
@pytest.mark.parametrize("seul", [False, True])
def test_activation_ne_modifie_aucun_impot_ni_remboursement_solde(situation, seul):
    d = _dossier_52000()
    if situation != "remboursement":
        d = replace(d, donnees_validees=tuple(replace(v, valeur_validee=D(0))
            if situation == "zero" or (v.type_document, v.case) in (("T4", "22"), ("RL-1", "E"))
            else v for v in d.donnees_validees))
    avant = calcul(d)
    apres = calcul(d, solidarite_quebec=profil(vit_seul_toute_annee=seul))
    assert apres.federal == avant.federal
    assert apres.quebec == avant.quebec
    assert apres.revenu == avant.revenu
    assert apres.rapprochement == avant.rapprochement
    assert apres.rapprochement.remboursement_estime == avant.rapprochement.remboursement_estime
    assert apres.rapprochement.solde_estime == avant.rapprochement.solde_estime
    if situation == "remboursement":
        assert apres.rapprochement.remboursement_estime > 0
    elif situation == "solde":
        assert apres.rapprochement.solde_estime > 0
    else:
        assert apres.rapprochement.remboursement_estime == apres.rapprochement.solde_estime == 0
    assert apres.base_solidarite_quebec.revenu_familial == apres.revenu.revenu_net_quebec
    # La trace monétaire et sa formule restent strictement identiques.
    t0, t1 = map(construire_trace_calcul_fiscal_2025, (avant, apres))
    assert t0.lignes == t1.lignes
    assert t0.formule_resultat == t1.formule_resultat
    assert t1.preparation_annexe_d and not t0.preparation_annexe_d


def test_revenu_275_recalcule_apres_changement_de_deduction():
    from tests.test_tax_reer_interface_storage_2025 import _reer_5000
    # Un changement de revenu dans les faits ne peut pas figer l'audit 6H.
    d = _dossier_52000()
    e = calcul(d, solidarite_quebec=profil())
    e2 = calcul(d, solidarite_quebec=profil(), ajustement_reer=_reer_5000())
    assert e2.base_solidarite_quebec.revenu_familial == e2.revenu.revenu_net_quebec
    assert e2.base_solidarite_quebec.revenu_familial != e.base_solidarite_quebec.revenu_familial
    assert e.base_solidarite_quebec.revenu_familial == D("50095.00")
    assert e.base_solidarite_quebec.revenu_familial != e.revenu.revenu_net_federal


def test_json_faits_seuls_rechargement_et_ancien_dossier(tmp_path):
    d = _dossier_52000()
    e = calcul(d, solidarite_quebec=profil())
    f = sauvegarder_dossier_fiscal(d, estimation=e, destination=tmp_path / "6h.json")
    brut = json.loads(f.read_text(encoding="utf-8"))
    c = dossier_fiscal_depuis_contenu(brut)
    assert c.solidarite_quebec == profil()
    assert calcul(c.dossier, solidarite_quebec=c.solidarite_quebec) == e
    assert not {"revenu_familial", "credit", "montant", "base_solidarite_quebec"} & brut["solidarite_quebec"].keys()
    with pytest.raises(ValueError, match="divergent"):
        sauvegarder_dossier_fiscal(d, estimation=e, solidarite_quebec=profil(vit_seul_toute_annee=True),
            destination=tmp_path / "refus.json")
    brut.pop("solidarite_quebec")
    ancien = dossier_fiscal_depuis_contenu(brut)
    assert ancien.solidarite_quebec == SolidariteQuebec2025()
    assert calcul(ancien.dossier, solidarite_quebec=ancien.solidarite_quebec) == calcul(d)


@pytest.mark.parametrize("champ,valeur", [("credit", "356"), ("activer", 1), ("citoyennete_confirmee", False)])
def test_chargement_json_refuse_faits_invalides(tmp_path, champ, valeur):
    f = sauvegarder_dossier_fiscal(_dossier_52000(), solidarite_quebec=profil(), destination=tmp_path / "6h.json")
    brut = json.loads(f.read_text(encoding="utf-8"))
    brut["solidarite_quebec"][champ] = valeur
    with pytest.raises(ValueError):
        dossier_fiscal_depuis_contenu(brut)


def test_vie_seule_annexe_b_et_cohabitation_annexe_h():
    from tests.test_tax_living_alone_integration_2025 import _profil_simple
    from tests.test_tax_quebec_caregiver_2025 import profil as aidante
    d = _dossier_52000()
    with pytest.raises(ValueError, match="vie seule"):
        calcul(d, solidarite_quebec=profil(), personne_vivant_seule=_profil_simple())
    e = calcul(d, solidarite_quebec=profil(vit_seul_toute_annee=True), personne_vivant_seule=_profil_simple())
    assert e.quebec == calcul(d, personne_vivant_seule=_profil_simple()).quebec
    with pytest.raises(ValueError, match="cohabitation"):
        calcul(d, solidarite_quebec=profil(vit_seul_toute_annee=True), personne_aidante_quebec=aidante())
    assert calcul(d, solidarite_quebec=profil(), personne_aidante_quebec=aidante()).base_solidarite_quebec


def test_profils_conjoint_et_enfants_refuses():
    from tests.test_tax_quebec_childcare_2025 import profil as garde
    from tests.test_tax_quebec_caregiver_2025 import profil as aidante, personne
    for autres in (
        {"frais_garde_quebec": garde()},
        {"personne_aidante_quebec": aidante(personnes=(personne(lien="conjoint"),))},
        {"personne_aidante_quebec": aidante(personnes=(personne(lien="enfant"),))},
    ):
        with pytest.raises(ValueError, match="Solidarité 6H.*familiale"):
            calcul(_dossier_52000(), solidarite_quebec=profil(), **autres)


def test_naissance_croisee_avec_medical_quebec():
    from tests.test_tax_quebec_refundable_medical_2025 import profil as medical
    with pytest.raises(ValueError, match="Naissance solidarité"):
        calcul(_dossier_52000(), solidarite_quebec=profil(), medical_remboursable_quebec=medical())
    assert calcul(_dossier_52000(), solidarite_quebec=profil(naissance="1990-12-31"),
        medical_remboursable_quebec=medical()).base_solidarite_quebec


def test_act_individuel_coherent_et_act_familial_exclu():
    from tests.test_tax_workers_benefit_2025 import profil as act, dossier_20000
    from tests.test_tax_family_workers_benefit_2025 import profil as act_familial
    d = dossier_20000()
    with pytest.raises(ValueError, match="Naissance solidarité"):
        calcul(d, solidarite_quebec=profil(), allocation_travailleurs=act())
    p = profil(naissance="1990-12-31")
    e = calcul(d, solidarite_quebec=p, allocation_travailleurs=act())
    assert e.rapprochement == calcul(d, allocation_travailleurs=act()).rapprochement
    with pytest.raises(ValueError, match="Solidarité 6H.*familiale"):
        calcul(d, solidarite_quebec=p, allocation_travailleurs=act_familial())


def test_transfert_conjoint_exclu(tmp_path):
    from tests.test_tax_quebec_caregiver_2025 import instantane
    from src.comptaprivee.tax_quebec_caregiver_2025 import PersonneAidanteQuebec2025
    t = instantane(tmp_path, PersonneAidanteQuebec2025())
    with pytest.raises(ValueError, match="Solidarité 6H.*familiale"):
        calcul(_dossier_52000(), solidarite_quebec=profil(), transfert_conjoint=t)


def test_source_longue_reste_lisible_dans_pdf(tmp_path):
    e = calcul(_dossier_52000(), solidarite_quebec=profil(source="W" * 2000))
    f = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "source_longue.pdf")
    with fitz.open(f) as pdf:
        for p in pdf:
            assert all(0 <= b[0] < b[2] <= p.rect.width for b in p.get_text("blocks"))


def test_resume_trace_pdf_explicitent_preparation_sans_montant(tmp_path):
    e = calcul(_dossier_52000(), solidarite_quebec=profil(vit_seul_toute_annee=True))
    trace = formater_trace_calcul_fiscal_2025(construire_trace_calcul_fiscal_2025(e))
    resume = formater_estimation_fiscale_2025(e)
    f = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "solidarite_6h.pdf")
    with fitz.open(f) as pdf:
        texte = " ".join(p.get_text() for p in pdf)
        for p in pdf:
            assert all(0 <= b[0] < b[2] <= p.rect.width and 0 <= b[1] < b[3] <= p.rect.height
                for b in p.get_text("blocks"))
    for sortie in (trace, resume, texte):
        sortie = " ".join(sortie.split())
        for attendu in ("juillet 2026 à juin 2027", "Faits 2025", "Composante TVQ demandée",
                "admissibilité préparée", "50095.00", "Montant monétaire non calculé par ComptaPrivée AI",
                "Montant final déterminé séparément par Revenu Québec",
                "Aucun effet sur le remboursement/solde TP-1 2025", "Pièces fictives vérifiées"):
            assert attendu in sortie


def test_profil_inactif_ne_modifie_pas_resume_trace():
    e = calcul(_dossier_52000())
    assert not e.base_solidarite_quebec
    assert "PRÉPARATION ANNEXE D" not in formater_estimation_fiscale_2025(e)
    assert not construire_trace_calcul_fiscal_2025(e).preparation_annexe_d
