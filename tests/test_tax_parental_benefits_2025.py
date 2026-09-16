"""RQAP : montants fictifs, frontières fiscales et chaîne de persistance."""
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
import json

import fitz
import pytest

from src.comptaprivee.tax_parental_benefits_2025 import consolider_prestations_rqap_2025
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025, formater_estimation_fiscale_2025
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
from src.comptaprivee.tax_document_classifier import classifier_document_fiscal
from src.comptaprivee.tax_field_extractor import extraire_cases_fiscales
from src.comptaprivee.tax_field_validation import valider_donnee_fiscale
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from tests.test_tax_estimation_2025 import _dossier_52000, _validee
from tests.test_tax_rpp_2025 import profil_rpa
from tests.test_tax_union_dues_integration_2025 import _reer_5000, _cotisations_600


def dossier_rqap(brut="20000", remboursement="1000"):
    dossier = _dossier_52000()
    lignes = []
    for type_doc, cases in (
        ("T4E", {"14": brut, "36": brut, "22": "1800", "23": "2200", "30": remboursement}),
        ("RL-6", {"A": brut, "D": remboursement, "G": "2200"}),
    ):
        lignes.extend(_validee(Path(type_doc + ".pdf"), type_doc, case, montant) for case, montant in cases.items())
    return replace(dossier, documents=dossier.documents + (Path("T4E.pdf"), Path("RL-6.pdf")), donnees_validees=dossier.donnees_validees + tuple(lignes))


def modifier(dossier, type_doc, case, montant):
    donnees = tuple(d for d in dossier.donnees_validees if (d.type_document, d.case) != (type_doc, case))
    return replace(dossier, donnees_validees=donnees + (_validee(Path(type_doc + ".pdf"), type_doc, case, montant),))


@pytest.mark.parametrize("nom,texte,attendu", [
    ("T4E_2025.pdf", "Box 14 20000.00 Income tax deducted", "T4E"),
    ("scan.pdf", "T4E Statement of employment insurance", "T4E"),
    ("RL-6_2025.pdf", "Revenu Québec Case A 20000.00", "RL-6"),
    ("Relevé 6.pdf", "", "RL-6"),
    ("scan.pdf", "RELEVÉ 6", "RL-6"),
    ("T4E.pdf", "RL-6", "À vérifier"),
    ("T4E.pdf", "T4", "À vérifier"),
    ("RL-60.pdf", "", "Non reconnu"),
])
def test_classification(nom, texte, attendu):
    assert classifier_document_fiscal(nom, texte).type_document == attendu


def test_extraction_validation_et_consolidation():
    base = _dossier_52000()
    t4e = extraire_cases_fiscales("T4E", "T4E Case 7 0 %\nCase 14 20 000,00\nCase 36 20 000,00\nCase 22 1 800,00\nCase 23 2 200,00\nCase 30 1 000,00", "T4E.pdf")
    rl6 = extraire_cases_fiscales("RL6", "RL-6 Case A 20 000,00\nCase D 1 000,00\nCase G 2 200,00", "RL-6.pdf")
    dossier = replace(base, documents=dossier_rqap().documents, donnees_validees=base.donnees_validees + tuple(map(valider_donnee_fiscale, t4e + rl6)))
    assert consolider_prestations_rqap_2025(dossier, True).cotisation_fss == Decimal("8.70")


@pytest.mark.parametrize("type_doc,case", [("T4E", "14"), ("RL-6", "A")])
@pytest.mark.parametrize("texte", ["-100,00", "−100,00", "(100,00)"])
def test_extraction_conserve_signe(type_doc, case, texte):
    assert extraire_cases_fiscales(type_doc, f"Case {case} {texte}", "scan.pdf")[0].valeur == Decimal("-100")


@pytest.mark.parametrize("montant", ["NaN", "Infinity", "-1", "0.001", "1000000000"])
def test_montants_invalides(montant):
    with pytest.raises(ValueError, match="Montant RQAP"):
        consolider_prestations_rqap_2025(modifier(dossier_rqap(), "T4E", "14", montant), True)


@pytest.mark.parametrize("confirmation", [False, None, "true", 1])
def test_confirmation_obligatoire(confirmation):
    with pytest.raises(ValueError):
        calculer_estimation_fiscale_2025(dossier_rqap(), rqap_confirme=confirmation)


@pytest.mark.parametrize("case", ["7", "15", "17", "18", "20", "21", "24", "33", "37", "99"])
def test_cases_hors_profil_refusees(case):
    with pytest.raises(ValueError, match="hors profil"):
        consolider_prestations_rqap_2025(modifier(dossier_rqap(), "T4E", case, "30"), True)


@pytest.mark.parametrize("type_doc,case", [("T4E", "36"), ("RL-6", "A"), ("T4E", "30"), ("RL-6", "D"), ("T4E", "23"), ("RL-6", "G")])
def test_incoherence_feuillets(type_doc, case):
    with pytest.raises(ValueError, match="incohérent"):
        consolider_prestations_rqap_2025(modifier(dossier_rqap(), type_doc, case, "1"), True)


@pytest.mark.parametrize("type_doc,case", [("T4E", "14"), ("T4E", "36"), ("RL-6", "A")])
def test_case_requise_manquante(type_doc, case):
    dossier = dossier_rqap()
    dossier = replace(dossier, donnees_validees=tuple(d for d in dossier.donnees_validees if (d.type_document, d.case) != (type_doc, case)))
    with pytest.raises(ValueError, match="obligatoire"):
        consolider_prestations_rqap_2025(dossier, True)


def test_remboursement_et_sous_cases():
    dossier = modifier(modifier(dossier_rqap(), "T4E", "26", "800"), "T4E", "27", "200")
    assert consolider_prestations_rqap_2025(dossier, True).remboursement == 1000
    with pytest.raises(ValueError, match="case 30"):
        consolider_prestations_rqap_2025(modifier(dossier, "T4E", "27", "201"), True)
    with pytest.raises(ValueError, match="supérieur"):
        consolider_prestations_rqap_2025(dossier_rqap("100", "101"), True)


@pytest.mark.parametrize("brut,remboursement,fss", [
    ("0", "0", "0"), ("18129.99", "0", "0"), ("18130", "0", "0"),
    ("18131", "0", "0.01"), ("20000", "1000", "8.70"),
    ("33130", "0", "150"), ("63060", "0", "150"),
    ("63061", "0", "150.01"), ("148060", "0", "1000"),
    ("200000", "0", "1000"), ("20000", "20000", "0"),
])
def test_fss_annexe_f_2025(brut, remboursement, fss):
    assert consolider_prestations_rqap_2025(dossier_rqap(brut, remboursement), True).cotisation_fss == Decimal(fss)


def test_doublons_sources_et_annee():
    dossier = dossier_rqap()
    for mauvais in (
        replace(dossier, donnees_validees=dossier.donnees_validees + (dossier.donnees_validees[-1],)),
        replace(dossier, documents=dossier.documents[:-1]),
        replace(dossier, annee_fiscale=2024),
        replace(dossier, province="Ontario"),
        replace(dossier, donnees_validees=dossier.donnees_validees[:-1] + (replace(dossier.donnees_validees[-1], statut="À valider"),)),
        replace(dossier, donnees_validees=dossier.donnees_validees + (_validee(Path("second.pdf"), "T4E", "14", "100"),)),
    ):
        with pytest.raises(ValueError):
            consolider_prestations_rqap_2025(mauvais, True)


def test_revenu_retenues_sans_double_comptage_et_deductions():
    base = calculer_estimation_fiscale_2025(_dossier_52000())
    estimation = calculer_estimation_fiscale_2025(dossier_rqap(), rqap_confirme=True)
    assert estimation.base == base.base  # salaire, cotisations et gains assurables inchangés
    r = estimation.revenu
    assert r.revenu_total_federal == r.revenu_total_quebec == Decimal("72000")
    assert r.revenu_net_federal == Decimal("70515")
    assert r.revenu_net_quebec == Decimal("69095")
    final = estimation.rapprochement
    assert final.retenue_federale == 9300
    assert final.retenue_quebec == 8400  # RL-6 G et T4E 23 comptés une seule fois
    assert final.retenues_totales == 17700
    assert final.impot_total_preliminaire == final.impot_federal_apres_abattement + final.impot_quebec_preliminaire + Decimal("8.70")
    avec = calculer_estimation_fiscale_2025(dossier_rqap(), rqap_confirme=True, cotisations_rpa=profil_rpa(), ajustement_reer=_reer_5000(), cotisations_syndicales=_cotisations_600())
    assert avec.revenu.revenu_net_federal == Decimal("61915")
    assert avec.revenu.revenu_net_quebec == Decimal("61095")
    assert avec.prestations_rqap.cotisation_fss == Decimal("8.70")  # REER/RPA ne réduisent pas le FSS


def test_profil_absent_preserve_reference():
    estimation = calculer_estimation_fiscale_2025(_dossier_52000())
    assert not estimation.prestations_rqap.present
    assert estimation.rapprochement.remboursement_estime == Decimal("5611.05")
    with pytest.raises(ValueError, match="Aucun T4E"):
        consolider_prestations_rqap_2025(_dossier_52000(), True)


def test_sauvegarde_rechargement_recalcul_et_ancien_json(tmp_path):
    dossier = dossier_rqap()
    estimation = calculer_estimation_fiscale_2025(dossier, rqap_confirme=True)
    chemin = sauvegarder_dossier_fiscal(dossier, estimation=estimation, destination=tmp_path / "dossier.json")
    charge = charger_dossier_fiscal(chemin)
    assert charge.rqap_confirme is True
    recalcule = calculer_estimation_fiscale_2025(charge.dossier, rqap_confirme=charge.rqap_confirme)
    assert recalcule.revenu == estimation.revenu
    assert recalcule.rapprochement == estimation.rapprochement
    with pytest.raises(ValueError, match="diffère"):
        sauvegarder_dossier_fiscal(dossier, estimation=estimation, rqap_confirme=False, destination=chemin)
    contenu = json.loads(chemin.read_text(encoding="utf-8"))
    del contenu["rqap_confirme"]
    chemin.write_text(json.dumps(contenu), encoding="utf-8")
    charge = charger_dossier_fiscal(chemin)
    assert charge.rqap_confirme is False
    with pytest.raises(ValueError, match="Confirmez"):
        calculer_estimation_fiscale_2025(charge.dossier)


@pytest.mark.parametrize("mauvais", [None, "true", 1, {}, []])
def test_confirmation_json_corrompue(tmp_path, mauvais):
    chemin = sauvegarder_dossier_fiscal(dossier_rqap(), rqap_confirme=True, destination=tmp_path / "dossier.json")
    contenu = json.loads(chemin.read_text(encoding="utf-8"))
    contenu["rqap_confirme"] = mauvais
    chemin.write_text(json.dumps(contenu), encoding="utf-8")
    with pytest.raises(ValueError, match="booléen"):
        charger_dossier_fiscal(chemin)


def test_resume_trace_pdf(tmp_path):
    estimation = calculer_estimation_fiscale_2025(dossier_rqap(), rqap_confirme=True)
    resume = formater_estimation_fiscale_2025(estimation)
    for ligne in ("11900", "11905", "23200", "246", "446", "43700", "451"):
        assert ligne in resume
    trace = construire_trace_calcul_fiscal_2025(estimation)
    assert [l.ordre for l in trace.lignes] == list(range(1, len(trace.lignes) + 1))
    assert next(l for l in trace.lignes if l.libelle == "FSS ligne 446").montant == Decimal("8.70")
    assert "11900" in next(l for l in trace.lignes if l.libelle == "Revenu imposable fédéral").formule
    pdf = exporter_rapport_fiscal_pdf_2025(estimation, tmp_path / "rqap.pdf")
    with fitz.open(pdf) as doc:
        texte = "\n".join(page.get_text() for page in doc)
        for attendu in ("11905", "23200", "446", "Retenue fédérale T4 + T4E", "Retenue Québec RL-1 + RL-6"):
            assert attendu in texte
        for page in doc:
            for x0, y0, x1, y1, *_ in page.get_text("blocks"):
                assert 0 <= x0 < x1 <= page.rect.width
                assert 0 <= y0 < y1 <= page.rect.height


def test_credits_medicaux_utilisent_le_nouveau_revenu_net():
    from tests.test_tax_medical_expenses_integration_2025 import _frais_3000
    dossier = dossier_rqap("2000", "100")
    sans = calculer_estimation_fiscale_2025(dossier, rqap_confirme=True)
    avec = calculer_estimation_fiscale_2025(dossier, rqap_confirme=True, frais_medicaux=_frais_3000())
    assert sans.revenu.revenu_net_federal == Decimal("53415")
    assert sans.federal.impot_federal_de_base - avec.federal.impot_federal_de_base == Decimal("202.64")
    assert sans.quebec.impot_quebec_preliminaire - avec.quebec.impot_quebec_preliminaire == Decimal("288.03")


def test_credit_age_exige_revalidation_du_revenu():
    from tests.test_tax_federal_age_pension_integration_2025 import _profil_age_federal
    dossier = dossier_rqap("2000", "100")
    with pytest.raises(ValueError, match="revenu net"):
        calculer_estimation_fiscale_2025(dossier, rqap_confirme=True, credits_federaux_age_pension=_profil_age_federal())
    estimation = calculer_estimation_fiscale_2025(dossier, rqap_confirme=True,
        credits_federaux_age_pension=_profil_age_federal(revenu_net_ligne_23600=Decimal("53415")))
    assert estimation.revenu.revenu_net_federal == Decimal("53415")


def test_autre_feuillet_ne_peut_pas_etre_ignore():
    dossier = dossier_rqap()
    dossier = replace(dossier, donnees_validees=dossier.donnees_validees + (_validee(Path("T4A.pdf"), "T4A", "016", "5000"),))
    with pytest.raises(ValueError, match="hors périmètre"):
        calculer_estimation_fiscale_2025(dossier, rqap_confirme=True)
