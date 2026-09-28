from dataclasses import replace
from decimal import Decimal as D
import json

import fitz
import pytest

from src.comptaprivee.tax_disability_transfer_2025 import TransfertsHandicap2025
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calculer
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal, dossier_fiscal_depuis_contenu
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from tests.test_tax_disability_transfer_2025 import transfert, ensemble
from tests.test_tax_estimation_2025 import _dossier_52000
from tests.test_tax_disability_2025 import _credit_valide
from tests.test_tax_workers_benefit_2025 import dossier_20000
from tests.test_tax_tuition_carryforward_2025 import frais


def profil_donneur(tmp_path, transfert, revenu, *, mineur=False, adoption=None):
    from tests.test_tax_interest_income_2025 import dossier_interets, profil_interets
    from tests.test_tax_disability_minor_2025 import mineur as handicap_mineur
    from src.comptaprivee.tax_disability_transfer_2025 import instantane_donneur_handicap_2025
    d = replace(dossier_interets(str(revenu)), client="Donneur synthétique")
    handicap = handicap_mineur() if mineur else _credit_valide(quebec=False)
    e = calculer(d, profil_interets=profil_interets(), credit_deficience=handicap, adoption=adoption)
    f = sauvegarder_dossier_fiscal(d, estimation=e, profil_interets=profil_interets(),
        credit_deficience=handicap, destination=tmp_path / "donneur_complet.json")
    t = replace(transfert, nom_donneur=d.client, naissance="2010-02-03" if mineur else "1980-02-03",
        dossier_donneur_json=instantane_donneur_handicap_2025(json.loads(f.read_text(encoding="utf-8"))))
    return e, ensemble(t)


@pytest.mark.parametrize("revenu,mineur,base,credit_utilise,transfert_attendu", [
    ("0", False, "10138", "0", "10138"),
    ("10000", False, "10138", "0", "10138"),
    ("20000", False, "10138", "561.29", "6267.03"),
    ("40000", False, "10138", "1470.01", "0"),
    ("0", True, "16052", "0", "16052"),
    ("20000", True, "16052", "561.29", "12181.03"),
    ("40000", True, "16052", "2327.54", "0"),
])
def test_solde_inutilise_depuis_dossier_reel(tmp_path, transfert, revenu, mineur, base, credit_utilise, transfert_attendu):
    from src.comptaprivee.tax_disability_transfer_2025 import calculer_transferts_handicap_2025
    e, p = profil_donneur(tmp_path, transfert, revenu, mineur=mineur)
    r = calculer_transferts_handicap_2025(p, beneficiaire=p.beneficiaire)
    c = r.donneurs[0].calcul
    assert e.revenu.revenu_net_federal == e.revenu.revenu_imposable_federal == D(revenu)
    assert c.montant_31600 == D(base)
    assert c.credit_utilise == D(credit_utilise)
    assert c.credit_handicap - c.credit_utilise == c.credit_disponible
    assert c.montant_31600 - c.base_utilisee == c.base_disponible == D(transfert_attendu)
    assert r.ligne_31800 == D(transfert_attendu)


def test_reproduction_80000_avec_adoptions_validees(tmp_path, transfert):
    from tests.test_tax_adoption_2025 import profil, enfant, depense
    from src.comptaprivee.tax_disability_transfer_2025 import calculer_transferts_handicap_2025
    # 68871 est un total pour quatre enfants, jamais une dépense par enfant
    # au-delà du plafond de 19580. Tous les éléments sont synthétiques.
    adoption = profil(enfants=tuple(enfant(nom=f"Enfant adopté {i}", aides=D(0),
        depenses=(depense(montant=D(m), source=f"Facture distincte {i}"),))
        for i, m in enumerate(("19580", "19580", "19580", "10131"))))
    e, p = profil_donneur(tmp_path, transfert, "80000", adoption=adoption)
    r = calculer_transferts_handicap_2025(p, beneficiaire=p.beneficiaire)
    c = r.donneurs[0].calcul
    assert e.revenu.revenu_net_federal == e.revenu.revenu_imposable_federal == D(80000)
    assert e.federal.impot_brut == D("12957.50")
    assert e.resultat_adoption.montant_31300 == D(68871)
    assert c.base_ligne_102 == D(85000)
    assert c.credits_avant_handicap == D(12325)
    assert c.compensatoire_avant_handicap == D("138.19")
    assert c.impot_avant_handicap == c.credit_utilise == D("494.31")
    assert c.credit_handicap - c.credit_utilise == D("1470.01") - D("494.31") == D("975.70")
    assert c.montant_31600 - c.base_utilisee == D(10138) - D("3409.03") == D("6728.97")
    assert r.ligne_31800 == D("6728.97")
    # Comparaison exacte, même revenu et même base, sans supplément ni partage.
    feuille = min(c.montant_31600, max(c.montant_31600 + c.base_ligne_102 - e.revenu.revenu_imposable_federal, D(0)))
    assert feuille == D(10138)
    assert not p.transferts[0].autres_parts
    assert not p.transferts[0].conjoint_donneur_reclame
    assert not p.transferts[0].autre_personne_reclame_30400


def test_31800_une_fois_et_own_31600(transfert):
    d = _dossier_52000()
    e0 = calculer(d, credit_deficience=_credit_valide(quebec=False))
    e = calculer(d, credit_deficience=_credit_valide(quebec=False), transferts_handicap=ensemble(transfert))
    c = e.federal.credits_federaux_complets
    assert dict(c.montants_par_ligne)["31800"] == D(16052)
    assert dict(c.montants_par_ligne)["31600"] == D(10138)
    assert c.base_ligne_33500 - e0.federal.credits_federaux_complets.base_ligne_33500 == D(16052)
    assert c.credit_ligne_33800 - e0.federal.credits_federaux_complets.credit_ligne_33800 == D("2327.54")
    assert e.revenu == e0.revenu and e.quebec == e0.quebec


def test_31800_avant_reports_scolarite(transfert):
    d = dossier_20000()
    p = replace(ensemble(transfert), beneficiaire=d.client)
    e0 = calculer(d, frais_scolarite=frais())
    e = calculer(d, frais_scolarite=frais(), transferts_handicap=p)
    assert e0.resultat_reports_scolarite.report_anterieur_utilise == D("983.20")
    assert e.resultat_reports_scolarite.report_anterieur_utilise == 0
    assert e.resultat_reports_scolarite.report_futur == D(4000)


def test_stockage_inference_recalcul_legacy_divergence(transfert, tmp_path):
    e = calculer(_dossier_52000(), transferts_handicap=ensemble(transfert))
    f = sauvegarder_dossier_fiscal(e.dossier, estimation=e, destination=tmp_path / "beneficiaire.json")
    c = charger_dossier_fiscal(f)
    assert c.transferts_handicap == e.transferts_handicap
    assert calculer(c.dossier, transferts_handicap=c.transferts_handicap).resultat_transferts_handicap == e.resultat_transferts_handicap
    brut = json.loads(f.read_text(encoding="utf-8"))
    assert "resultat_transferts_handicap" not in brut
    assert set(brut["transferts_handicap"]) == {"beneficiaire", "transferts"}
    with pytest.raises(ValueError, match="divergent"):
        sauvegarder_dossier_fiscal(e.dossier, estimation=e, transferts_handicap=TransfertsHandicap2025(), destination=f)
    del brut["transferts_handicap"]
    assert dossier_fiscal_depuis_contenu(brut).transferts_handicap == TransfertsHandicap2025()


@pytest.mark.parametrize("champ,valeur", [("nom_donneur", "Inconnu"), ("naissance", "2012-01-01"),
    ("condition", "30400 réclamé"), ("condition", "30450 réclamé")])
def test_reload_revalide_le_donneur_et_les_lignes(transfert, tmp_path, champ, valeur):
    e = calculer(_dossier_52000(), transferts_handicap=ensemble(transfert))
    f = sauvegarder_dossier_fiscal(e.dossier, estimation=e, destination=tmp_path / "brut.json")
    brut = json.loads(f.read_text(encoding="utf-8"))
    brut["transferts_handicap"]["transferts"][0][champ] = valeur
    with pytest.raises(ValueError):
        dossier_fiscal_depuis_contenu(brut)


def test_trace_et_pdf(transfert, tmp_path):
    e = calculer(_dossier_52000(), transferts_handicap=ensemble(transfert))
    trace = construire_trace_calcul_fiscal_2025(e)
    t = next(l for l in trace.lignes if l.libelle == "Handicap transféré — ligne 31800")
    base = next(l for l in trace.lignes if l.libelle == "Base ligne 33500")
    assert t.montant == D(16052) and t.ordre < base.ordre
    assert [l.ordre for l in trace.lignes] == list(range(1, len(trace.lignes) + 1))
    f = exporter_rapport_fiscal_pdf_2025(e, destination=tmp_path / "31800.pdf")
    with fitz.open(f) as doc:
        texte = "".join(p.get_text() for p in doc)
    assert "Enfant synthétique" in texte and "T2201" in texte
    assert "16052.00" in texte and "2327.54" in texte and "31800" in texte
