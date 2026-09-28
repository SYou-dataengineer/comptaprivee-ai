from dataclasses import replace
from decimal import Decimal as D

import pytest

from src.comptaprivee.tax_educator_supplies_2025 import (
    DepenseEducateur2025, FournituresEducateur2025, CONFIRMATIONS_EDUCATEUR,
    CATEGORIES_FOURNITURES, calculer_fournitures_educateur_2025,
    educateur_vers_dict, educateur_depuis_dict,
)


def depense(**kw):
    v = dict(date_paiement="2025-09-01", description="Livres pédagogiques fictifs", categorie="livres", montant=D(1000), source="Facture fictive A")
    v.update(kw)
    return DepenseEducateur2025(**v)


def profil(**kw):
    v = dict(depenses=(depense(),), employeur="École fictive", province_emploi="QC",
        source_qualification="Brevet fictif vérifié", source="Validation fictive",
        **{n: True for n in CONFIRMATIONS_EDUCATEUR})
    v.update(kw)
    return FournituresEducateur2025(**v)


def calcul(p=None, **kw):
    return calculer_fournitures_educateur_2025(p if p is not None else profil(), **kw)


@pytest.mark.parametrize("montant,base,credit", [("0.01", "0.01", "0"), ("0.02", "0.02", "0.01"),
    ("999.98", "999.98", "250"), ("1000", "1000", "250"), ("1000.01", "1000", "250"), ("2000", "1000", "250")])
def test_taux_plafond_arrondi(montant, base, credit):
    r = calcul(profil(depenses=(depense(montant=D(montant)),)))
    assert (r.ligne_46800, r.ligne_46900) == (D(base), D(credit))


@pytest.mark.parametrize("categorie", CATEGORIES_FOURNITURES)
def test_categories_prescrites(categorie):
    assert calcul(profil(depenses=(depense(categorie=categorie),))).ligne_46900 == 250


def test_aides_et_exception_imposable():
    r = calcul(profil(depenses=(depense(aide=D(600), aide_imposable_non_deductible=D(200)),)))
    assert (r.paiements, r.aides_exclues, r.depenses_admissibles, r.ligne_46900) == (D(1000), D(400), D(600), D(150))
    assert calcul(profil(depenses=(depense(aide=D(1000)),))).ligne_46900 == 0


def test_attestation_demandee_et_ordinateur_employeur():
    r = calcul(profil(attestation_demandee=True))
    assert r.attestation_manquante and r.ligne_46800 == 0 and r.ligne_46900 == 0
    assert r.depenses_admissibles == D(1000)
    assert calcul(profil(attestation_demandee=True, attestation_fournie=True, source_attestation="Attestation fictive")).ligne_46900 == D(250)
    assert calcul(profil(ordinateur_employeur_disponible=True)).ligne_46900 == D(250)
    with pytest.raises(ValueError, match="hors classe"):
        calcul(profil(ordinateur_employeur_disponible=True, depenses=(depense(categorie="ordinateurs et tablettes"),)))


def test_rapprochement_t777_obligatoire_si_deduction():
    with pytest.raises(ValueError, match="rapprochement"):
        calcul(deduction_t777=D(100))
    assert calcul(profil(rapprochement_t777="T777 fournitures exclues sur annexe fictive"), deduction_t777=D(100)).ligne_46900 == D(250)


@pytest.mark.parametrize("valeur", [D("NaN"), D("sNaN"), D("Infinity"), D("-Infinity"), D(-1), D("1.001"), D("1e100"), True, "1", None])
@pytest.mark.parametrize("nom", ["montant", "aide", "aide_imposable_non_deductible"])
def test_montants_invalides(nom, valeur):
    with pytest.raises(ValueError):
        calcul(profil(depenses=(depense(**{nom: valeur}),)))


@pytest.mark.parametrize("kw", [dict(date_paiement="2024-12-31"), dict(date_paiement="2026-01-01"),
    dict(date_paiement="2025-02-30"), dict(date_paiement="20250901"), dict(date_paiement=None),
    dict(description=""), dict(categorie="meuble"), dict(source=None), dict(source=""),
    dict(montant=D(0)), dict(aide=D(1001)), dict(aide_imposable_non_deductible=D(1))])
def test_depenses_invalides(kw):
    with pytest.raises(ValueError):
        calcul(profil(depenses=(depense(**kw),)))


@pytest.mark.parametrize("nom", list(CONFIRMATIONS_EDUCATEUR))
@pytest.mark.parametrize("valeur", [False, 1, "true"])
def test_confirmations(nom, valeur):
    with pytest.raises(ValueError):
        calcul(profil(**{nom: valeur}))


@pytest.mark.parametrize("kw", [dict(depenses=[]), dict(depenses=(depense(), depense(source=" FACTURE FICTIVE A "))),
    dict(employeur=""), dict(province_emploi="US"), dict(source_qualification=""), dict(source=None),
    dict(attestation_fournie=True), dict(source_attestation="Source sans statut"),
    dict(attestation_demandee=1), dict(ordinateur_employeur_disponible="false")])
def test_profils_invalides(kw):
    with pytest.raises(ValueError):
        calcul(profil(**kw))


def test_vide_annee_et_json_reconstruit():
    assert calcul(FournituresEducateur2025(), annee=2024).ligne_46900 == 0
    assert educateur_depuis_dict(None) == FournituresEducateur2025()
    with pytest.raises(ValueError, match="2025"):
        calcul(annee=2024)
    brut = educateur_vers_dict(profil())
    assert brut["depenses"][0]["montant"] == "1000.00"
    assert "ligne_46900" not in brut
    assert educateur_depuis_dict(brut) == profil()
    for p in (FournituresEducateur2025(source="Incomplet"), FournituresEducateur2025(attestation_demandee=True)):
        with pytest.raises(ValueError):
            calcul(p)


@pytest.mark.parametrize("brut", [True, [], {"inconnu": 1}, {"depenses": {}}, {"depenses": [None]}, {"depenses": [{"inconnu": 1}]}])
def test_json_structure_invalide(brut):
    with pytest.raises(ValueError):
        educateur_depuis_dict(brut)


@pytest.mark.parametrize("valeur", [True, 1.2, None, "NaN", "Infinity", "-1", "1.001", "texte"])
def test_json_montants_invalides(valeur):
    brut = educateur_vers_dict(profil())
    brut["depenses"][0]["montant"] = valeur
    with pytest.raises(ValueError):
        educateur_depuis_dict(brut)


def test_estimation_credit_remboursable_sans_changement_impot():
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as estimation
    from tests.test_tax_estimation_2025 import _dossier_52000
    a = estimation(_dossier_52000())
    e = estimation(_dossier_52000(), fournitures_educateur=profil())
    assert (a.revenu, a.federal, a.quebec) == (e.revenu, e.federal, e.quebec)
    assert e.rapprochement.impot_total_preliminaire == a.rapprochement.impot_total_preliminaire
    assert e.rapprochement.credit_educateur_ligne_46900 == D(250)
    assert e.rapprochement.remboursement_estime - e.rapprochement.solde_estime == a.rapprochement.remboursement_estime - a.rapprochement.solde_estime + D(250)


def test_credit_remboursable_impot_nul_et_cumul_autres_credits():
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
    from src.comptaprivee.tax_reconciliation_2025 import calculer_rapprochement_fiscal_2025 as rapprochement
    from tests.test_tax_estimation_2025 import _dossier_52000
    e = calculer_estimation_fiscale_2025(_dossier_52000())
    f = replace(e.federal, impot_federal_de_base=D(0), credit_etranger_ligne_40500=D(0))
    q = replace(e.quebec, impot_quebec_preliminaire=D(0))
    b = replace(e.base, impot_federal_retenu=D(0), impot_quebec_retenu=D(0))
    r = rapprochement(b, f, q, credit_educateur=D(250), credit_formation=D(100))
    assert r.impot_total_preliminaire == 0 and r.remboursement_estime == D(350)


@pytest.mark.parametrize("credit", [D("NaN"), D("sNaN"), D("Infinity"), D(-1), D("250.01"), D("1.001"), True, "250"])
def test_rapprochement_credit_invalide(credit):
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
    from src.comptaprivee.tax_reconciliation_2025 import calculer_rapprochement_fiscal_2025
    from tests.test_tax_estimation_2025 import _dossier_52000
    e = calculer_estimation_fiscale_2025(_dossier_52000())
    with pytest.raises(ValueError):
        calculer_rapprochement_fiscal_2025(e.base, e.federal, e.quebec, credit_educateur=credit)


def test_stockage_recalcul_ancien_et_divergence(tmp_path):
    import json
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as estimation
    from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
    from tests.test_tax_estimation_2025 import _dossier_52000
    e = estimation(_dossier_52000(), fournitures_educateur=profil())
    f = sauvegarder_dossier_fiscal(e.dossier, estimation=e, destination=tmp_path / "educateur.json")
    c = charger_dossier_fiscal(f)
    assert c.fournitures_educateur == profil()
    assert estimation(c.dossier, fournitures_educateur=c.fournitures_educateur) == e
    brut = json.loads(f.read_text(encoding="utf-8"))
    assert "ligne_46900" not in json.dumps(brut["fournitures_educateur"])
    with pytest.raises(ValueError, match="divergent"):
        sauvegarder_dossier_fiscal(e.dossier, estimation=e, fournitures_educateur=FournituresEducateur2025(), destination=f)
    del brut["fournitures_educateur"]
    f.write_text(json.dumps(brut), encoding="utf-8")
    assert charger_dossier_fiscal(f).fournitures_educateur == FournituresEducateur2025()


def test_trace_pdf_attestation_et_formule_resultat(tmp_path):
    import fitz
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as estimation
    from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
    from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
    from tests.test_tax_estimation_2025 import _dossier_52000
    e = estimation(_dossier_52000(), fournitures_educateur=profil())
    t = construire_trace_calcul_fiscal_2025(e)
    assert next(l.montant for l in t.lignes if l.libelle == "Crédit éducateur remboursable — 46900") == D(250)
    assert "46900" in t.formule_resultat
    assert [l.ordre for l in t.lignes] == list(range(1, len(t.lignes) + 1))
    f = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "educateur.pdf")
    with fitz.open(f) as doc:
        texte = "\n".join(p.get_text() for p in doc)
    for v in ("FOURNITURES SCOLAIRES", "46900", "250.00", "Facture fictive A"):
        assert v in texte
    e = estimation(_dossier_52000(), fournitures_educateur=profil(attestation_demandee=True))
    assert e.rapprochement.credit_educateur_ligne_46900 == 0


def test_t777_dans_estimation_et_chargement(tmp_path):
    from src.comptaprivee.tax_employment_expenses_2025 import DepensesEmploi2025
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as estimation
    from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
    from tests.test_tax_estimation_2025 import _dossier_52000
    d = DepensesEmploi2025(deduction_federale_t777=D(100), source_federale="T777 fictif",
        valide_par_comptable=True, salarie_ordinaire_confirme=True, contrat_exige_depenses_confirme=True,
        non_remboursees_confirme=True, t2200_confirme=True, t777_confirme=True)
    with pytest.raises(ValueError, match="rapprochement"):
        estimation(_dossier_52000(), depenses_emploi=d, fournitures_educateur=profil())
    p = profil(rapprochement_t777="Ventilation fictive : fournitures exclues du T777")
    e = estimation(_dossier_52000(), depenses_emploi=d, fournitures_educateur=p)
    f = sauvegarder_dossier_fiscal(e.dossier, estimation=e, destination=tmp_path / "cas.json")
    assert charger_dossier_fiscal(f).fournitures_educateur == p
