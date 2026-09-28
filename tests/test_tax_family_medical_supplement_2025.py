from dataclasses import replace
from decimal import Decimal as D
import json
import fitz
import pytest

from src.comptaprivee.tax_medical_supplement_2025 import valider_supplement_medical_2025
from src.comptaprivee.tax_medical_expenses_2025 import FraisMedicaux2025
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal, dossier_fiscal_depuis_contenu
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from tests.test_tax_medical_supplement_2025 import profil as individuel, montant, calcul
from tests.test_tax_family_medical_integration_2025 import famille, depense, personne
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_federal_top_up_integration_2025 import verifier_t1


def profil(**kw):
    v = dict(mode_familial=True, situation_conjugale="conjoint", nom_conjoint="Conjoint fictif",
             revenu_net_conjoint=D(10000), source_conjoint="Déclaration et état civil synthétiques",
             donnees_familiales_verifiees=True, sans_conjoint_ni_personne_charge=False)
    v.update(kw)
    return individuel(**v)


def options(p=None):
    return dict(frais_medicaux=FraisMedicaux2025(supplement=p or profil()),
        frais_medicaux_famille=famille(depenses=(depense(montant_paye=D(10000)),)))


@pytest.mark.parametrize("net,conjoint,attendu", [
    ("20000", "10000", "1504"), ("20000", "13294", "1504"),
    ("20000", "14294", "1454"), ("20000", "43374", "0"),
    ("20000", "43373.80", ".01"), ("0", "0", "1504"),
    ("20000", "-10000", "1504"),
])
def test_feuille_federale_deux_colonnes(net, conjoint, attendu):
    r = montant(profil(revenu_net_conjoint=D(conjoint)), revenu_net=D(net))
    assert r.revenu_familial_ajuste == D(net) + max(D(conjoint), D(0))
    assert r.ligne_45200 == D(attendu)


@pytest.mark.parametrize("situation", ["séparation de 90 jours", "conjoint décédé"])
def test_exclusions_conjoint_confirmees(situation):
    r = montant(profil(situation_conjugale=situation, revenu_net_conjoint=D(100000)))
    assert r.revenu_conjoint_retenu == 0
    assert r.revenu_familial_ajuste == D(33294)
    assert r.ligne_45200 == D(1504)


def test_personnes_charge_sans_conjoint_et_travail_individuel():
    p = profil(situation_conjugale="sans conjoint", nom_conjoint="", source_conjoint="", revenu_net_conjoint=D(0))
    assert montant(p).ligne_45200 == D(1504)
    # Le revenu du conjoint ne remplace jamais le minimum de travail du demandeur.
    assert montant(profil(), emploi=D("4389.99")).ligne_45200 == 0


@pytest.mark.parametrize("valeur", [D("NaN"), D("sNaN"), D("Infinity"), D("1e100"), D(".001"), True, 3.5, "10000", None])
def test_revenu_conjoint_strict(valeur):
    with pytest.raises(ValueError):
        montant(profil(revenu_net_conjoint=valeur))


@pytest.mark.parametrize("kw", [
    {"mode_familial": "true"}, {"donnees_familiales_verifiees": 1},
    {"donnees_familiales_verifiees": False}, {"situation_conjugale": ""},
    {"situation_conjugale": "inconnue"}, {"nom_conjoint": None}, {"nom_conjoint": " "},
    {"source_conjoint": ""}, {"source_conjoint": None}, {"sans_conjoint_ni_personne_charge": True},
    {"mode_familial": False}, {"situation_conjugale": "sans conjoint"},
])
def test_contradictions_et_confirmations(kw):
    with pytest.raises(ValueError):
        valider_supplement_medical_2025(profil(**kw))


def test_estimation_base_familiale_credit_unique_et_non_remboursables_inchanges():
    opts = options()
    sans = calcul(_dossier_52000(), frais_medicaux_famille=opts["frais_medicaux_famille"])
    e = calcul(_dossier_52000(), **opts)
    r = e.resultat_supplement_medical
    assert r.ligne_33200 == D(9400)
    assert r.revenu_familial_ajuste == e.revenu.revenu_net_federal + D(10000)
    assert r.ligne_45200 == max(D(1504) - r.reduction_revenu, D(0))
    assert e.federal == sans.federal and e.quebec == sans.quebec and e.revenu == sans.revenu
    assert e.rapprochement.supplement_medical_ligne_45200 == r.ligne_45200
    verifier_t1(e)


def test_concordance_30300():
    from tests.test_tax_federal_spouse_2025 import _profil
    net = calcul(_dossier_52000()).revenu.revenu_net_federal
    conjoint = _profil(revenu_net_contribuable_ligne_23600=net, revenu_net_conjoint_2025=D(10000))
    e = calcul(_dossier_52000(), montant_conjoint_federal=conjoint, **options())
    verifier_t1(e)
    with pytest.raises(ValueError, match="Revenu net du conjoint divergent"):
        calcul(_dossier_52000(), montant_conjoint_federal=conjoint, **options(profil(revenu_net_conjoint=D(9999))))
    with pytest.raises(ValueError, match="30300/32600"):
        calcul(_dossier_52000(), montant_conjoint_federal=conjoint, **options(profil(situation_conjugale="conjoint décédé")))


def test_concordance_32600_et_stockage(tmp_path):
    from tests.test_tax_spouse_transfer_2025 import profil as transfert
    conjoint = transfert(tmp_path)
    e = calcul(_dossier_52000(), transfert_conjoint=conjoint, **options())
    assert e.resultat_transfert_conjoint.ligne_32600 > 0
    verifier_t1(e)
    f = sauvegarder_dossier_fiscal(e.dossier, estimation=e, destination=tmp_path / "famille.json")
    assert charger_dossier_fiscal(f).frais_medicaux == e.frais_medicaux
    with pytest.raises(ValueError, match="Revenu net du conjoint divergent"):
        calcul(_dossier_52000(), transfert_conjoint=conjoint, **options(profil(revenu_net_conjoint=D(9999))))


@pytest.mark.parametrize("nom", ["Client Test", "Autre conjoint"])
def test_identite_conjoint_sur_recu(nom):
    opts = options()
    opts["frais_medicaux_famille"] = famille(personnes=(personne(lien="conjoint", nom="Conjoint fictif",
        revenu_net_23600=D(0), source_revenu=""),))
    opts["frais_medicaux"] = FraisMedicaux2025(supplement=profil(nom_conjoint=nom))
    with pytest.raises(ValueError, match="conjoint"):
        calcul(_dossier_52000(), **opts)


def test_json_recalcul_donnees_brutes_et_ancien_profil(tmp_path):
    e = calcul(_dossier_52000(), **options())
    f = sauvegarder_dossier_fiscal(e.dossier, estimation=e, destination=tmp_path / "famille.json")
    brut = json.loads(f.read_text(encoding="utf-8"))
    assert brut["frais_medicaux"]["supplement"]["revenu_net_conjoint"] == "10000.00"
    assert "revenu_conjoint_retenu" not in brut["frais_medicaux"]["supplement"]
    c = charger_dossier_fiscal(f)
    assert calcul(c.dossier, frais_medicaux=c.frais_medicaux, frais_medicaux_famille=c.frais_medicaux_famille) == e
    with pytest.raises(ValueError, match="diffère"):
        sauvegarder_dossier_fiscal(e.dossier, estimation=e, frais_medicaux=options(profil(revenu_net_conjoint=D(1)))["frais_medicaux"], destination=f)
    # Un ancien profil individuel sans les nouveaux champs garde sa signification.
    brut["frais_medicaux"]["supplement"] = {k: v for k, v in vars(individuel()).items()
        if k not in {"mode_familial", "situation_conjugale", "nom_conjoint", "revenu_net_conjoint", "source_conjoint", "donnees_familiales_verifiees"}}
    brut.pop("frais_medicaux_famille")
    assert dossier_fiscal_depuis_contenu(brut).frais_medicaux.supplement == individuel()


@pytest.mark.parametrize("valeur", [True, 10.5, None, "NaN", ".001", "texte", "1e100"])
def test_json_revenu_invalide(tmp_path, valeur):
    e = calcul(_dossier_52000(), **options())
    f = sauvegarder_dossier_fiscal(e.dossier, estimation=e, destination=tmp_path / "famille.json")
    brut = json.loads(f.read_text(encoding="utf-8"))
    brut["frais_medicaux"]["supplement"]["revenu_net_conjoint"] = valeur
    with pytest.raises(ValueError):
        dossier_fiscal_depuis_contenu(brut)


def test_json_identite_contradictoire_refusee(tmp_path):
    e = calcul(_dossier_52000(), **options())
    f = sauvegarder_dossier_fiscal(e.dossier, estimation=e, destination=tmp_path / "famille.json")
    brut = json.loads(f.read_text(encoding="utf-8"))
    brut["frais_medicaux"]["supplement"]["nom_conjoint"] = e.dossier.client
    with pytest.raises(ValueError, match="différer"):
        dossier_fiscal_depuis_contenu(brut)


def test_trace_pdf_famille(tmp_path):
    e = calcul(_dossier_52000(), **options())
    trace = construire_trace_calcul_fiscal_2025(e)
    ligne = next(x for x in trace.lignes if x.libelle == "Revenu familial ajusté 45200")
    assert ligne.montant == e.resultat_supplement_medical.revenu_familial_ajuste
    assert "10000.00" in ligne.formule
    assert [x.ordre for x in trace.lignes] == list(range(1, len(trace.lignes) + 1))
    f = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "supplement_famille.pdf")
    with fitz.open(f) as pdf:
        texte = "\n".join(page.get_text() for page in pdf)
        for page in pdf:
            for x0, y0, x1, y1, *_ in page.get_text("blocks"):
                assert 0 <= x0 < x1 <= page.rect.width and 0 <= y0 < y1 <= page.rect.height
    assert "Conjoint fictif" in texte and "revenu familial" in texte.lower()
    assert "retenu : 10000.00" in texte


def test_personne_charge_30400_compatible_sans_conjoint():
    from tests.test_tax_federal_eligible_dependant_2025 import _profil
    net = calcul(_dossier_52000()).revenu.revenu_net_federal
    personne_charge = _profil(revenu_net_contribuable_ligne_23600=net)
    p = profil(situation_conjugale="sans conjoint", nom_conjoint="", source_conjoint="", revenu_net_conjoint=D(0))
    e = calcul(_dossier_52000(), personne_charge_admissible_federale=personne_charge, **options(p))
    verifier_t1(e)
    with pytest.raises(ValueError, match="30400"):
        calcul(_dossier_52000(), personne_charge_admissible_federale=personne_charge, **options())


def test_recu_politique_conjoint_et_identite():
    from tests.test_tax_political_contributions_2025 import profil as politique, recu
    politique = politique(nom_conjoint="Conjoint fictif", recus=(recu(donateur="conjoint", nom_donateur="Conjoint fictif"),))
    e = calcul(_dossier_52000(), contributions_politiques=politique, **options())
    verifier_t1(e)
    assert e.resultat_supplement_medical.revenu_conjoint_retenu == D(10000)
    with pytest.raises(ValueError, match="Identité"):
        calcul(_dossier_52000(), contributions_politiques=politique, **options(profil(nom_conjoint="Autre")))


def test_act_individuel_refuse_meme_sans_recu_familial():
    from tests.test_tax_workers_benefit_2025 import profil as act
    with pytest.raises(ValueError, match="ACT individuel"):
        calcul(_dossier_52000(), frais_medicaux=FraisMedicaux2025(supplement=profil()), allocation_travailleurs=act())


def test_ancien_agregat_individuel_refuse_pour_famille():
    from tests.test_tax_medical_supplement_2025 import frais
    with pytest.raises(ValueError, match="agrégé"):
        calcul(_dossier_52000(), frais_medicaux=replace(frais(), supplement=profil()))


def test_sauvegarde_sans_estimation_verifie_identite(tmp_path):
    with pytest.raises(ValueError, match="différer"):
        sauvegarder_dossier_fiscal(_dossier_52000(), **options(profil(nom_conjoint="Client Test")),
            destination=tmp_path / "refus.json")
    assert not (tmp_path / "refus.json").exists()
