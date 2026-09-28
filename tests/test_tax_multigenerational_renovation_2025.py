from dataclasses import replace
from decimal import Decimal as D

import pytest

from src.comptaprivee.tax_multigenerational_renovation_2025 import (
    CONFIRMATIONS_RENOVATION, LIENS_PROCHE, ROLES_DEMANDEUR,
    DepenseRenovation2025, PartAutreDemandeur2025,
    RenovationMultigenerationnelle2025, RenovationsMultigenerationnelles2025,
    calculer_multigenerationnel_2025, multigenerationnel_depuis_dict,
    multigenerationnel_vers_dict,
)


def depense(**kw):
    return replace(DepenseRenovation2025("2023-01-01", "2023-01-01", "2023-01-01",
        "Entrepreneur exemple", "Construction du logement secondaire", D("60000"),
        source="Facture synthétique A"), **kw)


def renovation(**kw):
    return replace(RenovationMultigenerationnelle2025(
        logement="10 rue Exemple", unite="logement arrière", particulier="Parent A",
        naissance_particulier="1960-12-31", proche="Enfant A", naissance_proche="1990-01-01",
        lien_proche="enfant", role_demandeur="proche propriétaire", source_role="Titre et lien vérifiés",
        date_fin="2025-12-31", source="Dossier et inspection synthétiques", depenses=(depense(),),
        **{n: True for n in CONFIRMATIONS_RENOVATION}), **kw)


def profil(*renovations, **kw):
    return replace(RenovationsMultigenerationnelles2025(renovations or (renovation(),), True, True), **kw)


@pytest.mark.parametrize("brut,aide,autres,base,credit", [
    ("60000", "0", "0", "50000", "7250"),
    ("10000", "0", "0", "10000", "1450"),
    ("10000", "10000", "0", "0", "0"),
    ("60000", "15000", "0", "45000", "6525"),
    ("29000", "0", "33000", "17000", "2465"),
    ("33000", "0", "17000", "33000", "4785"),
    ("60000", "0", "50000", "0", "0"),
    ("0.03", "0", "0", "0.03", "0.00"),
    ("0.04", "0", "0", "0.04", "0.01"),
])
def test_annexe12_plafond_aides_et_partage(brut, aide, autres, base, credit):
    p = profil(renovation(depenses=(depense(montant=D(brut), aide=D(aide)),),
        autres_demandes=(PartAutreDemandeur2025("Autre personne", D(autres), "Accord"),)))
    r = calculer_multigenerationnel_2025(p)
    assert (r.ligne_45354, r.ligne_45355) == (D(base), D(credit))
    assert r.renovations[0].plafond_disponible == D(50000) - D(autres)


def test_deux_renovations_arc_et_arrondi_global():
    a = renovation(depenses=(depense(montant=D(15000)),))
    b = renovation(particulier="Parent B", unite="autre logement",
        depenses=(depense(montant=D(63000), source="Facture B"),))
    r = calculer_multigenerationnel_2025(profil(a, b))
    assert (r.ligne_45354, r.ligne_45355) == (D(65000), D(9425))
    a = replace(a, depenses=(depense(montant=D("0.03")),))
    b = replace(b, depenses=(depense(montant=D("0.03"), source="Facture B"),))
    assert calculer_multigenerationnel_2025(profil(a, b)).ligne_45355 == D("0.01")


@pytest.mark.parametrize("naissance,ciph,admis", [
    ("1960-12-31", False, True), ("1961-01-01", False, False),
    ("1961-01-01", True, True), ("2007-12-31", True, True),
    ("2008-01-01", True, False), ("2026-01-01", True, False),
])
def test_age_et_ciph(naissance, ciph, admis):
    p = profil(renovation(naissance_particulier=naissance, ciph_admissible=ciph,
                         source_ciph="T2201" if ciph else ""))
    if admis:
        assert calculer_multigenerationnel_2025(p).ligne_45355 == D(7250)
    else:
        with pytest.raises(ValueError):
            calculer_multigenerationnel_2025(p)


@pytest.mark.parametrize("lien", LIENS_PROCHE)
@pytest.mark.parametrize("avec_conjoint", [False, True])
def test_liens_familiaux(lien, avec_conjoint):
    assert calculer_multigenerationnel_2025(profil(renovation(lien_proche=lien,
        lien_avec_conjoint=avec_conjoint))).ligne_45355 == D(7250)


@pytest.mark.parametrize("role", ROLES_DEMANDEUR)
def test_roles_admissibles_sur_pieces(role):
    assert calculer_multigenerationnel_2025(profil(renovation(role_demandeur=role))).ligne_45355 == D(7250)


@pytest.mark.parametrize("nom", CONFIRMATIONS_RENOVATION)
@pytest.mark.parametrize("v", [False, 1, "oui"])
def test_confirmations_obligatoires(nom, v):
    with pytest.raises(ValueError):
        calculer_multigenerationnel_2025(profil(renovation(**{nom: v})))


@pytest.mark.parametrize("nom", ["montant", "aide"])
@pytest.mark.parametrize("v", [D("NaN"), D("sNaN"), D("Infinity"), D("-Infinity"),
    D("-1"), D("1.001"), D("1e100"), "100", True, 1.0])
def test_montants_invalides(nom, v):
    with pytest.raises(ValueError):
        calculer_multigenerationnel_2025(profil(renovation(depenses=(depense(**{nom: v}),))))


@pytest.mark.parametrize("kw", [
    {"montant": D(0)}, {"aide": D(60001)}, {"date_piece": "2026-01-01"},
    {"date_bien_service": "2022-12-31"}, {"date_bien_service": "2026-01-01"},
    {"date_paiement": "2022-12-31"}, {"date_piece": "2025-02-30"},
    {"date_piece": "20250101"}, {"date_piece": 20250101},
    {"fournisseur": ""}, {"description": " "}, {"source": ""},
    {"fournisseur_lie": True}, {"fournisseur_lie": 1}, {"numero_tps": 1},
])
def test_depenses_invalides(kw):
    with pytest.raises(ValueError):
        calculer_multigenerationnel_2025(profil(renovation(depenses=(depense(**kw),))))


def test_dates_loi_application_et_paiement_apres_achevement():
    # Le contrat peut précéder 2023; les biens/services et le paiement doivent
    # être postérieurs à 2022. L'engagement précède la fin des travaux.
    p = profil(renovation(depenses=(depense(date_piece="2022-12-01", date_paiement="2026-02-01"),)))
    assert calculer_multigenerationnel_2025(p).ligne_45355 == D(7250)


def test_fournisseur_lie_et_fiducie_documentes():
    p = profil(renovation(attribution_fiducie=True, source_attribution="Notification et quote-part",
        depenses=(depense(fournisseur_lie=True, numero_tps="Inscription vérifiée"),)))
    assert calculer_multigenerationnel_2025(p).ligne_45355 == D(7250)


@pytest.mark.parametrize("kw", [
    {"date_fin": "2024-12-31"}, {"date_fin": "2026-01-01"},
    {"naissance_proche": "2008-01-01"}, {"lien_proche": "ami"},
    {"proche": " PARENT a "}, {"role_demandeur": "ami propriétaire"},
    {"source_role": ""}, {"logement": ""}, {"unite": ""},
    {"source": ""}, {"source_ciph": "T2201"}, {"ciph_admissible": True},
    {"attribution_fiducie": True}, {"source_attribution": "Notification"},
    {"depenses": []}, {"depenses": ()}, {"autres_demandes": []},
])
def test_renovations_invalides(kw):
    with pytest.raises(ValueError):
        calculer_multigenerationnel_2025(profil(renovation(**kw)))


def test_doublons_personne_logement_et_facture():
    a = renovation()
    for b in (a, replace(a, particulier="B"), replace(a, unite="B"),
              replace(a, particulier="B", unite="B")):
        with pytest.raises(ValueError):
            calculer_multigenerationnel_2025(profil(a, b))
    with pytest.raises(ValueError):
        calculer_multigenerationnel_2025(profil(replace(a, depenses=(depense(), depense(source=" FACTURE synthétique A ")))))


@pytest.mark.parametrize("v", [D("NaN"), D("Infinity"), D(-1), D("1.001"), D(50001), "10", True])
def test_autres_demandes_invalides(v):
    with pytest.raises(ValueError):
        calculer_multigenerationnel_2025(profil(renovation(autres_demandes=(PartAutreDemandeur2025("B", v, "Accord"),))))


def test_autres_demandes_plafond_cumule_et_doublons():
    for demandes in ((PartAutreDemandeur2025("B", D(30000), "Accord"), PartAutreDemandeur2025("C", D(30000), "Accord")),
                     (PartAutreDemandeur2025("B", D(1), "Accord"), PartAutreDemandeur2025(" b ", D(1), "Accord"))):
        with pytest.raises(ValueError):
            calculer_multigenerationnel_2025(profil(renovation(autres_demandes=demandes)))


def test_profil_vide_legacy_et_annee():
    vide = RenovationsMultigenerationnelles2025()
    assert multigenerationnel_depuis_dict(None) == vide
    assert multigenerationnel_depuis_dict({}) == vide
    assert calculer_multigenerationnel_2025(vide, annee=2024).ligne_45355 == 0
    for p in (profil(resident_annee_complete=False), profil(profil_ordinaire=False), profil(profil_ordinaire=1)):
        with pytest.raises(ValueError):
            calculer_multigenerationnel_2025(p)
    with pytest.raises(ValueError):
        calculer_multigenerationnel_2025(profil(), annee=2024)


def test_rapprochement_medical_accessibilite():
    with pytest.raises(ValueError, match="rapprochement"):
        calculer_multigenerationnel_2025(profil(), autres_frais_reclames=True)
    p = profil(rapprochement_medical_accessibilite="Ventilation distincte vérifiée")
    assert calculer_multigenerationnel_2025(p, autres_frais_reclames=True).ligne_45355 == D(7250)


def test_json_roundtrip_brut_uniquement():
    p = profil(renovation(autres_demandes=(PartAutreDemandeur2025("B", D(10000), "Accord"),)))
    brut = multigenerationnel_vers_dict(p)
    assert brut["renovations"][0]["depenses"][0]["montant"] == "60000.00"
    assert "ligne_45355" not in str(brut)
    assert multigenerationnel_depuis_dict(brut) == p


@pytest.mark.parametrize("niveau", ["profil", "renovation", "depense", "autre"])
def test_json_cles_inconnues(niveau):
    brut = multigenerationnel_vers_dict(profil(renovation(autres_demandes=(PartAutreDemandeur2025("B", D(1), "Accord"),))))
    cibles = {"profil": brut, "renovation": brut["renovations"][0],
              "depense": brut["renovations"][0]["depenses"][0],
              "autre": brut["renovations"][0]["autres_demandes"][0]}
    cibles[niveau]["inconnue"] = True
    with pytest.raises(ValueError):
        multigenerationnel_depuis_dict(brut)


@pytest.mark.parametrize("v", ["NaN", "sNaN", "Infinity", "-1", "0.001", True, 1.0, None])
def test_json_montants_invalides(v):
    brut = multigenerationnel_vers_dict(profil())
    brut["renovations"][0]["depenses"][0]["montant"] = v
    with pytest.raises(ValueError):
        multigenerationnel_depuis_dict(brut)


def test_estimation_remboursable_revenus_et_impots_inchanges():
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as estimation
    from tests.test_tax_estimation_2025 import _dossier_52000
    a = estimation(_dossier_52000())
    e = estimation(_dossier_52000(), renovations_multigenerationnelles=profil())
    assert (a.revenu, a.federal, a.quebec) == (e.revenu, e.federal, e.quebec)
    assert e.rapprochement.impot_total_preliminaire == a.rapprochement.impot_total_preliminaire
    assert e.rapprochement.credit_multigenerationnel_ligne_45355 == D(7250)
    assert e.rapprochement.remboursement_estime - e.rapprochement.solde_estime == a.rapprochement.remboursement_estime - a.rapprochement.solde_estime + D(7250)


def test_json_dossier_inference_divergence_legacy(tmp_path):
    import json
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as estimation
    from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
    from tests.test_tax_estimation_2025 import _dossier_52000
    e = estimation(_dossier_52000(), renovations_multigenerationnelles=profil())
    f = sauvegarder_dossier_fiscal(e.dossier, estimation=e, destination=tmp_path / "renovation.json")
    c = charger_dossier_fiscal(f)
    assert c.renovations_multigenerationnelles == profil()
    assert estimation(c.dossier, renovations_multigenerationnelles=c.renovations_multigenerationnelles) == e
    with pytest.raises(ValueError, match="divergent"):
        sauvegarder_dossier_fiscal(e.dossier, estimation=e,
            renovations_multigenerationnelles=RenovationsMultigenerationnelles2025(), destination=f)
    brut = json.loads(f.read_text(encoding="utf-8"))
    del brut["renovations_multigenerationnelles"]
    f.write_text(json.dumps(brut), encoding="utf-8")
    assert charger_dossier_fiscal(f).renovations_multigenerationnelles == RenovationsMultigenerationnelles2025()


def test_trace_pdf_et_ordre(tmp_path):
    import fitz
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as estimation
    from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
    from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
    from tests.test_tax_estimation_2025 import _dossier_52000
    e = estimation(_dossier_52000(), renovations_multigenerationnelles=profil())
    t = construire_trace_calcul_fiscal_2025(e)
    assert next(l.montant for l in t.lignes if l.libelle == "Crédit multigénérationnel remboursable — 45355") == D(7250)
    assert "45355" in t.formule_resultat
    assert [l.ordre for l in t.lignes] == list(range(1, len(t.lignes) + 1))
    fichier = exporter_rapport_fiscal_pdf_2025(e, destination=tmp_path / "rapport.pdf")
    with fitz.open(fichier) as pdf:
        texte = "".join(page.get_text() for page in pdf)
    assert "45355" in texte and "7250.00" in texte and "Facture synthétique A" in texte


@pytest.mark.parametrize("credit", [D("NaN"), D("sNaN"), D("Infinity"), D(-1), D("1.001"), True, "250"])
def test_rapprochement_montant_invalide(credit):
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
    from src.comptaprivee.tax_reconciliation_2025 import calculer_rapprochement_fiscal_2025
    from tests.test_tax_estimation_2025 import _dossier_52000
    e = calculer_estimation_fiscale_2025(_dossier_52000())
    with pytest.raises(ValueError):
        calculer_rapprochement_fiscal_2025(e.base, e.federal, e.quebec, credit_multigenerationnel=credit)


def test_credit_remboursable_impot_nul_cumul_et_plusieurs_renovations():
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
    from src.comptaprivee.tax_reconciliation_2025 import calculer_rapprochement_fiscal_2025
    from tests.test_tax_estimation_2025 import _dossier_52000
    e = calculer_estimation_fiscale_2025(_dossier_52000())
    f = replace(e.federal, impot_federal_de_base=D(0), credit_etranger_ligne_40500=D(0))
    q = replace(e.quebec, impot_quebec_preliminaire=D(0))
    b = replace(e.base, impot_federal_retenu=D(0), impot_quebec_retenu=D(0))
    r = calculer_rapprochement_fiscal_2025(b, f, q,
        credit_multigenerationnel=D(9425), credit_educateur=D(250), credit_formation=D(100))
    assert r.impot_total_preliminaire == 0
    assert r.remboursement_estime == D(9775)


def test_interaction_frais_medicaux_estimation_stockage(tmp_path):
    import json
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as estimation
    from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
    from src.comptaprivee.tax_medical_expenses_2025 import FraisMedicaux2025
    from tests.test_tax_estimation_2025 import _dossier_52000
    frais = FraisMedicaux2025(montant_admissible_federal=D(5000), source_federale="Reçus médicaux distincts",
        valide_par_comptable=True, recus_confirmes=True, remboursements_soustraits=True,
        periode_12_mois_fin_2025_confirmee=True, aucune_periode_deja_reclamee=True,
        profil_individuel_sans_conjoint_dependant=True)
    with pytest.raises(ValueError, match="rapprochement"):
        estimation(_dossier_52000(), frais_medicaux=frais, renovations_multigenerationnelles=profil())
    p = profil(rapprochement_medical_accessibilite="Pièces distinctes vérifiées")
    e = estimation(_dossier_52000(), frais_medicaux=frais, renovations_multigenerationnelles=p)
    f = sauvegarder_dossier_fiscal(e.dossier, estimation=e, destination=tmp_path / "ensemble.json")
    assert charger_dossier_fiscal(f).renovations_multigenerationnelles == p
    brut = json.loads(f.read_text(encoding="utf-8"))
    brut["renovations_multigenerationnelles"]["rapprochement_medical_accessibilite"] = ""
    f.write_text(json.dumps(brut), encoding="utf-8")
    with pytest.raises(ValueError, match="rapprochement"):
        charger_dossier_fiscal(f)
