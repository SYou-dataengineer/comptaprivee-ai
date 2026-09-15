"""RPA services courants : règles, saisie, feuillets et interactions 2025."""
from dataclasses import replace
from decimal import Decimal
import json

import fitz
import pytest

from src.comptaprivee.tax_rpp_2025 import (
    CotisationsRpa2025, montant_rpa_depuis_champ, valider_cotisations_rpa_2025,
    appliquer_cotisations_rpa_2025, verifier_rpa_dossier_2025,
)
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025, formater_estimation_fiscale_2025
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025, formater_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from src.comptaprivee.tax_field_extractor import extraire_cases_fiscales
from tests.test_tax_estimation_2025 import _dossier_52000, _validee
from tests.test_tax_union_dues_integration_2025 import _cotisations_600, _reer_5000
from tests.test_tax_medical_expenses_integration_2025 import _frais_3000


def profil_rpa(**kwargs):
    return replace(CotisationsRpa2025(
        Decimal("3000"), Decimal("3000"), "T4 case 20 - services 2025",
        "RL-1 case D - services 2025", True, True,
    ), **kwargs)


def dossier_rpa():
    d = _dossier_52000()
    return replace(d, donnees_validees=d.donnees_validees + (
        _validee("T4.pdf", "T4", "20", "3000"),
        _validee("RL1.pdf", "RL-1", "D", "3000"),
    ))


@pytest.mark.parametrize("texte,attendu", [("", "0"), ("0", "0"),
    ("3 000,25 $", "3000.25"), ("3\u00a0000,25", "3000.25"), ("3\u202f000.25", "3000.25"), ("0.01", "0.01")])
def test_saisie(texte, attendu):
    assert montant_rpa_depuis_champ(texte) == Decimal(attendu)


@pytest.mark.parametrize("texte", ["-1", "NaN", "Infinity", "-Infinity", "abc", "0.001", "1000000000", "1e99999", True])
def test_saisie_invalide(texte):
    with pytest.raises(ValueError):
        montant_rpa_depuis_champ(texte)


@pytest.mark.parametrize("champ,valeur", [
    ("montant_federal", Decimal("NaN")), ("montant_quebec", Decimal("Infinity")),
    ("montant_federal", Decimal("-1")), ("montant_quebec", Decimal("-1")),
    ("montant_federal", Decimal("3000.001")), ("montant_federal", 3000),
    ("montant_quebec", Decimal("3001")), ("source_federale", " "), ("source_quebec", ""),
    ("source_federale", None), ("source_quebec", "a\nb"), ("source_federale", "x" * 1001),
    ("valide_par_comptable", False), ("valide_par_comptable", "false"),
    ("services_courants_uniquement", False), ("services_courants_uniquement", 1),
])
def test_profil_invalide(champ, valeur):
    with pytest.raises(ValueError):
        valider_cotisations_rpa_2025(profil_rpa(**{champ: valeur}))


def test_pas_de_plafond_3500_pour_services_courants():
    p = profil_rpa(montant_federal=Decimal("12000"), montant_quebec=Decimal("12000"))
    assert valider_cotisations_rpa_2025(p) == p


@pytest.mark.parametrize("type_doc,case", [("T4", "74"), ("T4", "75"), ("RL-1", "D-1"), ("RL-1", "D-2"), ("RL-1", "D-3")])
def test_cas_speciaux_bloquent_meme_sans_profil(type_doc, case):
    d = _dossier_52000()
    document = "T4.pdf" if type_doc == "T4" else "RL1.pdf"
    d = replace(d, donnees_validees=d.donnees_validees + (_validee(document, type_doc, case, "100"),))
    with pytest.raises(ValueError, match="hors profil"):
        calculer_estimation_fiscale_2025(d)


def test_cases_detectees_ne_sont_pas_ignorees():
    with pytest.raises(ValueError, match="correspondre"):
        calculer_estimation_fiscale_2025(dossier_rpa())


def test_cases_et_saisie_ne_sont_pas_additionnees():
    e = calculer_estimation_fiscale_2025(dossier_rpa(), cotisations_rpa=profil_rpa())
    assert e.revenu.revenu_net_federal == Decimal("48515")
    assert e.revenu.revenu_net_quebec == Decimal("47095")
    assert e.revenu.revenu_total_federal == Decimal("52000")
    assert e.revenu.deduction_rrq_quebec == Decimal("485")
    assert e.revenu.deduction_travailleur_quebec == Decimal("1420")
    # 3 000 × 14,5 % × (1 - 16,5 %) + 3 000 × 14 % = 783,225;
    # arrondis par juridiction : économie de 783,23 $.
    assert e.rapprochement.remboursement_estime == Decimal("6394.28")


def test_montants_distincts_et_plafond_quebec():
    e = calculer_estimation_fiscale_2025(_dossier_52000(), cotisations_rpa=profil_rpa(montant_quebec=Decimal("2000")))
    assert e.revenu.revenu_net_federal == Decimal("48515")
    assert e.revenu.revenu_net_quebec == Decimal("48095")


def test_profil_vide_ne_change_aucun_resultat():
    d = _dossier_52000()
    assert calculer_estimation_fiscale_2025(d) == calculer_estimation_fiscale_2025(d, cotisations_rpa=CotisationsRpa2025())
    assert calculer_estimation_fiscale_2025(d).rapprochement.remboursement_estime == Decimal("5611.05")


def test_reer_cotisations_et_medical_recalculent_apres_rpa():
    e = calculer_estimation_fiscale_2025(dossier_rpa(), cotisations_rpa=profil_rpa(),
        ajustement_reer=_reer_5000(), cotisations_syndicales=_cotisations_600(), frais_medicaux=_frais_3000())
    assert e.revenu.revenu_net_federal == Decimal("42915")
    assert e.revenu.revenu_net_quebec == Decimal("42095")
    # Le profil sans RPA mais avec 3 000 $ de REER additionnels doit avoir
    # les mêmes bases, crédits médicaux et impôts, sans altérer le plafond REER.
    reference = calculer_estimation_fiscale_2025(_dossier_52000(),
        ajustement_reer=replace(_reer_5000(), deduction_reer=Decimal("8000")),
        cotisations_syndicales=_cotisations_600(), frais_medicaux=_frais_3000())
    assert e.federal == reference.federal
    assert e.quebec == reference.quebec
    assert e.rapprochement.remboursement_estime == reference.rapprochement.remboursement_estime
    assert e.ajustement_reer.plafond_reer_confirme == Decimal("8000")


def test_revenu_ne_devient_pas_negatif():
    r = calculer_estimation_fiscale_2025(_dossier_52000()).revenu
    r = replace(r, revenu_net_federal=Decimal("10"), revenu_imposable_federal=Decimal("10"),
                revenu_net_quebec=Decimal("20"), revenu_imposable_quebec=Decimal("20"))
    result = appliquer_cotisations_rpa_2025(r, profil_rpa())
    assert result.revenu_net_federal == result.revenu_imposable_federal == 0
    assert result.revenu_net_quebec == result.revenu_imposable_quebec == 0


@pytest.mark.parametrize("champ,valeur", [("annee_fiscale", 2024), ("province", "Ontario")])
def test_hors_annee_province(champ, valeur):
    with pytest.raises(ValueError):
        verifier_rpa_dossier_2025(replace(_dossier_52000(), **{champ: valeur}), profil_rpa())


def test_doublon_case_rpa_refuse():
    d = dossier_rpa()
    d = replace(d, donnees_validees=d.donnees_validees + (d.donnees_validees[-1],))
    with pytest.raises(ValueError, match="dupliquée"):
        verifier_rpa_dossier_2025(d, profil_rpa())


def test_extraction_rpa_et_cases_speciales_sans_confusion():
    t4 = extraire_cases_fiscales("T4", "Box 20 RPP 3,000.00\nCode 74 500.00\nCode 75 0.00", "t4.pdf")
    assert {d.case: d.valeur for d in t4} == {"20": Decimal("3000"), "74": Decimal("500"), "75": Decimal("0")}
    rl = extraire_cases_fiscales("RL-1", "Case D-1 100,00\nCase D 3 000,00\nCase D-2 200,00\nCase D-3 300,00", "rl.pdf")
    assert {d.case: d.valeur for d in rl} == {"D": Decimal("3000"), "D-1": Decimal("100"), "D-2": Decimal("200"), "D-3": Decimal("300")}
    assert not extraire_cases_fiscales("RL-1", "Case D-1 100,00", "rl.pdf")[0].case == "D"


def test_case_vide_ne_prend_pas_montant_code_suivant():
    valeurs = extraire_cases_fiscales("T4", "Box 20\nCode 74 500.00", "t4.pdf")
    assert {d.case for d in valeurs} == {"74"}


@pytest.mark.parametrize("texte", ["-100,00", "−100,00", "(100,00)"])
def test_extraction_rpa_ne_transforme_pas_negatif_en_deduction(texte):
    donnee = extraire_cases_fiscales("T4", "Case 20 " + texte, "t4.pdf")[0]
    assert donnee.valeur == Decimal("-100")


def test_credit_age_exige_revenu_actualise_apres_rpa():
    from tests.test_tax_federal_age_pension_integration_2025 import _profil_age_federal
    with pytest.raises(ValueError, match="correspondre"):
        calculer_estimation_fiscale_2025(dossier_rpa(), cotisations_rpa=profil_rpa(),
            credits_federaux_age_pension=_profil_age_federal())
    e = calculer_estimation_fiscale_2025(dossier_rpa(), cotisations_rpa=profil_rpa(),
        credits_federaux_age_pension=_profil_age_federal(revenu_net_ligne_23600=Decimal("48515")))
    assert e.rapprochement.remboursement_estime > Decimal("6394.28")


def test_sauvegarde_rechargement_et_recalcul(tmp_path):
    e = calculer_estimation_fiscale_2025(dossier_rpa(), cotisations_rpa=profil_rpa())
    path = sauvegarder_dossier_fiscal(e.dossier, estimation=e, destination=tmp_path / "dossier.json")
    charge = charger_dossier_fiscal(path)
    assert charge.cotisations_rpa == profil_rpa()
    nouveau = calculer_estimation_fiscale_2025(charge.dossier, cotisations_rpa=charge.cotisations_rpa)
    assert nouveau.revenu == e.revenu
    assert nouveau.rapprochement == e.rapprochement


def test_ancien_dossier_sans_rpa(tmp_path):
    path = sauvegarder_dossier_fiscal(_dossier_52000(), destination=tmp_path / "ancien.json")
    contenu = json.loads(path.read_text(encoding="utf-8"))
    del contenu["cotisations_rpa"]
    path.write_text(json.dumps(contenu), encoding="utf-8")
    assert charger_dossier_fiscal(path).cotisations_rpa == CotisationsRpa2025()


@pytest.mark.parametrize("champ,valeur", [("montant_federal", "NaN"), ("valide_par_comptable", "false"),
    ("services_courants_uniquement", 1), ("source_federale", None), ("montant_quebec", "3001")])
def test_json_corrompu_refuse(tmp_path, champ, valeur):
    path = sauvegarder_dossier_fiscal(dossier_rpa(), cotisations_rpa=profil_rpa(), destination=tmp_path / "dossier.json")
    contenu = json.loads(path.read_text(encoding="utf-8"))
    contenu["cotisations_rpa"][champ] = valeur
    path.write_text(json.dumps(contenu), encoding="utf-8")
    with pytest.raises(ValueError):
        charger_dossier_fiscal(path)


def test_estimation_et_profil_sauvegarde_incoherents_refuses(tmp_path):
    e = calculer_estimation_fiscale_2025(_dossier_52000())
    with pytest.raises(ValueError, match="estimation"):
        sauvegarder_dossier_fiscal(e.dossier, estimation=e, cotisations_rpa=profil_rpa(), destination=tmp_path / "d.json")
    assert not (tmp_path / "d.json").exists()


def test_resume_trace_et_pdf(tmp_path):
    e = calculer_estimation_fiscale_2025(dossier_rpa(), cotisations_rpa=profil_rpa())
    resume = formater_estimation_fiscale_2025(e)
    trace = formater_trace_calcul_fiscal_2025(construire_trace_calcul_fiscal_2025(e))
    for texte in (resume, trace):
        assert "20700" in texte and "205" in texte
        assert profil_rpa().source_federale in texte
        assert profil_rpa().source_quebec in texte
        assert "3\u00a0000,00" in texte
    chemin = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "rpa.pdf")
    with fitz.open(chemin) as pdf:
        texte = "".join(page.get_text() for page in pdf)
        assert "20700" in texte and "205" in texte and "RPA" in texte
        assert "6 394,28" in texte


def test_pdf_sources_longues_restent_dans_la_page(tmp_path):
    e = calculer_estimation_fiscale_2025(dossier_rpa(), cotisations_rpa=profil_rpa(source_federale="W" * 1000))
    chemin = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "source-longue.pdf")
    with fitz.open(chemin) as pdf:
        texte = "".join(page.get_text() for page in pdf)
        assert texte.count("W") == 1000
        assert all(word[2] <= page.rect.width - 20 for page in pdf for word in page.get_text("words"))


@pytest.mark.parametrize("contenu_rpa", [None, [], {}, {"champ_inconnu": "0"}])
def test_structure_json_rpa_invalide(tmp_path, contenu_rpa):
    path = sauvegarder_dossier_fiscal(_dossier_52000(), destination=tmp_path / "d.json")
    contenu = json.loads(path.read_text(encoding="utf-8"))
    contenu["cotisations_rpa"] = contenu_rpa
    path.write_text(json.dumps(contenu), encoding="utf-8")
    with pytest.raises(ValueError):
        charger_dossier_fiscal(path)
