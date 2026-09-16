"""Bloc AE : références T4E/annexe F 2025, indépendance du profil RQAP."""
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
import json

import fitz
import pytest

from src.comptaprivee.tax_employment_insurance_2025 import (
    PrestationsAe2025, consolider_prestations_ae_2025,
    appliquer_recuperation_ae_2025, cotisation_fss_prestations_2025,
)
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025, formater_estimation_fiscale_2025
from src.comptaprivee.tax_field_extractor import extraire_cases_fiscales
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from tests.test_tax_estimation_2025 import _dossier_52000, _validee
from tests.test_tax_parental_benefits_2025 import dossier_rqap
from tests.test_tax_rpp_2025 import profil_rpa
from tests.test_tax_union_dues_integration_2025 import _reer_5000, _cotisations_600


def dossier_ae(brut="40000", regulieres="30000", parentales="5000", remboursement="1000", taux="30"):
    d = _dossier_52000()
    cases = {"7": taux, "14": brut, "15": regulieres, "37": parentales, "30": remboursement, "22": "2500", "23": "3000"}
    return replace(d, documents=d.documents + (Path("T4E.pdf"),), donnees_validees=d.donnees_validees + tuple(
        _validee(Path("T4E.pdf"), "T4E", c, v) for c, v in cases.items()))


def modifier(d, case, montant):
    lignes = tuple(x for x in d.donnees_validees if (x.type_document, x.case) != ("T4E", case))
    return replace(d, donnees_validees=lignes + (_validee(Path("T4E.pdf"), "T4E", case, montant),))


@pytest.mark.parametrize("texte,attendu", [
    ("Case 7 0 %", "0"), ("Box 7 Repayment rate 30%", "30"),
    ("Case 7 Taux de remboursement : 30,00 %", "30.00"),
    ("Case 7 -30 %", "-30"), ("Case 7 15 %", "15"),
])
def test_extraction_taux_avec_libelle(texte, attendu):
    donnees = extraire_cases_fiscales("T4E", texte + "\nCase 14 20000.00", "T4E.pdf")
    assert next(d.valeur for d in donnees if d.case == "7") == Decimal(attendu)


def test_taux_absent_ne_prend_pas_case_suivante():
    donnees = extraire_cases_fiscales("T4E", "Case 7 Taux\nCase 14 30000.00", "T4E.pdf")
    assert not any(d.case == "7" for d in donnees)


@pytest.mark.parametrize("montant", ["NaN", "sNaN", "Infinity", "-1", "0.001", "1000000000"])
def test_montants_refuses(montant):
    with pytest.raises(ValueError, match="Montant AE"):
        consolider_prestations_ae_2025(modifier(dossier_ae(), "14", montant), True)


@pytest.mark.parametrize("case", ["17", "18", "20", "21", "24", "33", "36", "99"])
def test_cas_hors_perimetre(case):
    with pytest.raises(ValueError, match="hors profil"):
        calculer_estimation_fiscale_2025(modifier(dossier_ae(), case, "100"), ae_confirme=True)


@pytest.mark.parametrize("confirmation", [False, None, 1, "true"])
def test_confirmation_requise(confirmation):
    with pytest.raises(ValueError):
        calculer_estimation_fiscale_2025(dossier_ae(), ae_confirme=confirmation)


@pytest.mark.parametrize("case", ["7", "14"])
def test_case_obligatoire(case):
    d = dossier_ae()
    d = replace(d, donnees_validees=tuple(x for x in d.donnees_validees if (x.type_document, x.case) != ("T4E", case)))
    with pytest.raises(ValueError, match="obligatoire"):
        consolider_prestations_ae_2025(d, True)


@pytest.mark.parametrize("taux", ["1", "0.3", "15", "100"])
def test_taux_invalide(taux):
    with pytest.raises(ValueError, match="taux"):
        consolider_prestations_ae_2025(modifier(dossier_ae(), "7", taux), True)


def test_sous_cases_et_doublons():
    d = modifier(modifier(dossier_ae(), "26", "800"), "27", "200")
    assert consolider_prestations_ae_2025(d, True).remboursement == 1000
    for invalide in (
        modifier(d, "27", "201"), modifier(d, "15", "36000"), modifier(d, "30", "40001"),
        replace(d, donnees_validees=d.donnees_validees + (d.donnees_validees[-1],)),
        replace(d, documents=d.documents[:-1]),
        replace(d, annee_fiscale=2024), replace(d, province="Ontario"),
        replace(d, donnees_validees=d.donnees_validees[:-1] + (replace(d.donnees_validees[-1], statut="À valider"),)),
        replace(d, donnees_validees=d.donnees_validees + (_validee(Path("second.pdf"), "T4E", "14", "100"),)),
    ):
        with pytest.raises(ValueError):
            consolider_prestations_ae_2025(invalide, True)


@pytest.mark.parametrize("net,regulieres,remboursement,taux,attendu", [
    ("82124.99", "10000", "0", "30", "0"),
    ("82125", "10000", "0", "30", "0"),
    ("82126", "10000", "0", "30", "0.30"),
    ("83125", "10000", "0", "30", "300"),
    ("100000", "10000", "1000", "30", "2700"),
    ("100000", "1000", "2000", "30", "0"),
    ("100000", "10000", "0", "0", "0"),
    ("100000", "0", "0", "30", "0"),
    ("82125.05", "10000", "0", "30", "0.02"),
])
def test_tableau_remboursement_t4e_2025(net, regulieres, remboursement, taux, attendu):
    r = calculer_estimation_fiscale_2025(_dossier_52000()).revenu
    r = replace(r, revenu_net_federal=Decimal(net), revenu_imposable_federal=Decimal(net),
        revenu_net_quebec=Decimal(net), revenu_imposable_quebec=Decimal(net))
    ae = PrestationsAe2025(prestations=Decimal("30000"), regulieres=Decimal(regulieres),
        remboursement=Decimal(remboursement), taux_remboursement=Decimal(taux), present=True)
    apres, ae = appliquer_recuperation_ae_2025(r, ae)
    assert ae.recuperation == Decimal(attendu)
    assert apres.revenu_net_federal == apres.revenu_net_quebec == Decimal(net) - Decimal(attendu)


@pytest.mark.parametrize("assiette,fss", [("18130", "0"), ("18131", "0.01"), ("20000", "18.70"), ("33130", "150"), ("63060", "150"), ("63061", "150.01"), ("148060", "1000")])
def test_fss_seuils(assiette, fss):
    assert cotisation_fss_prestations_2025(Decimal(assiette)) == Decimal(fss)


def test_recuperation_reduit_assiette_fss():
    r = calculer_estimation_fiscale_2025(_dossier_52000()).revenu
    r = replace(r, revenu_net_federal=Decimal("85025"))
    ae = PrestationsAe2025(prestations=Decimal("20000"), regulieres=Decimal("20000"), remboursement=Decimal("1000"), taux_remboursement=Decimal("30"), present=True)
    _, resultat = appliquer_recuperation_ae_2025(r, ae)
    assert resultat.recuperation == Decimal("870")
    assert resultat.cotisation_fss == 0  # 20000 - 1000 - 870 = 18130


def test_integration_recuperation_apres_deductions_et_sans_abattement():
    e = calculer_estimation_fiscale_2025(dossier_ae(), ae_confirme=True)
    assert e.base == calculer_estimation_fiscale_2025(_dossier_52000()).base
    assert e.revenu.revenu_total_federal == e.revenu.revenu_total_quebec == 92000
    assert e.prestations_ae.revenu_avant_recuperation == Decimal("90515")
    assert e.prestations_ae.recuperation == Decimal("2517")
    assert e.revenu.revenu_net_federal == Decimal("87998")
    assert e.revenu.revenu_net_quebec == Decimal("86578")
    f = e.rapprochement
    assert f.retenue_federale == 10000 and f.retenue_quebec == 9200
    assert f.impot_total_preliminaire == f.impot_federal_apres_abattement + f.impot_quebec_preliminaire + Decimal("2517") + Decimal("150")
    assert f.retenues_totales == 19200
    avec = calculer_estimation_fiscale_2025(dossier_ae(), ae_confirme=True,
        cotisations_rpa=profil_rpa(), ajustement_reer=_reer_5000(), cotisations_syndicales=_cotisations_600())
    assert avec.prestations_ae.revenu_avant_recuperation == Decimal("81915")
    assert avec.prestations_ae.recuperation == 0
    assert avec.prestations_ae.cotisation_fss == 150


def test_regime_exempte_et_prestations_speciales():
    e = calculer_estimation_fiscale_2025(dossier_ae(taux="0"), ae_confirme=True)
    assert e.prestations_ae.recuperation == 0 and e.revenu.revenu_net_federal == 90515
    e = calculer_estimation_fiscale_2025(dossier_ae(regulieres="0", parentales="20000"), ae_confirme=True)
    assert e.prestations_ae.recuperation == 0
    assert e.prestations_ae.maternite_parentales == 20000  # pas ajoutée au total
    assert e.revenu.revenu_total_federal == 92000


def test_rqap_et_profils_mixtes():
    rqap = calculer_estimation_fiscale_2025(dossier_rqap(), rqap_confirme=True)
    assert rqap.rapprochement.remboursement_estime == Decimal("3191.61")
    assert not rqap.prestations_ae.present
    for kwargs in ({"ae_confirme": True}, {"ae_confirme": True, "rqap_confirme": True}):
        with pytest.raises(ValueError, match="périmètre"):
            calculer_estimation_fiscale_2025(dossier_rqap(), **kwargs)
    with pytest.raises(ValueError, match="Aucun T4E"):
        calculer_estimation_fiscale_2025(_dossier_52000(), ae_confirme=True)


def test_stockage_recalcul_et_ancien_json(tmp_path):
    d = dossier_ae()
    e = calculer_estimation_fiscale_2025(d, ae_confirme=True)
    p = sauvegarder_dossier_fiscal(d, estimation=e, destination=tmp_path / "ae.json")
    charge = charger_dossier_fiscal(p)
    assert charge.ae_confirme and not charge.rqap_confirme
    nouveau = calculer_estimation_fiscale_2025(charge.dossier, ae_confirme=charge.ae_confirme)
    assert nouveau.rapprochement == e.rapprochement and nouveau.prestations_ae == e.prestations_ae
    with pytest.raises(ValueError, match="diffère"):
        sauvegarder_dossier_fiscal(d, estimation=e, ae_confirme=False, destination=p)
    contenu = json.loads(p.read_text(encoding="utf-8"))
    del contenu["ae_confirme"]
    p.write_text(json.dumps(contenu), encoding="utf-8")
    ancien = charger_dossier_fiscal(p)
    assert not ancien.ae_confirme
    with pytest.raises(ValueError, match="Confirmez"):
        calculer_estimation_fiscale_2025(ancien.dossier)


@pytest.mark.parametrize("valeur", [None, "true", 1, [], {}])
def test_confirmation_json_invalide(tmp_path, valeur):
    p = sauvegarder_dossier_fiscal(dossier_ae(), ae_confirme=True, destination=tmp_path / "ae.json")
    c = json.loads(p.read_text(encoding="utf-8"))
    c["ae_confirme"] = valeur
    p.write_text(json.dumps(c), encoding="utf-8")
    with pytest.raises(ValueError, match="booléen"):
        charger_dossier_fiscal(p)


def test_resume_trace_et_pdf(tmp_path):
    e = calculer_estimation_fiscale_2025(dossier_ae(), ae_confirme=True)
    texte = formater_estimation_fiscale_2025(e)
    for numero in ("11900", "11905", "23200", "23500", "42200", "43700", "111", "246", "250", "451", "446"):
        assert numero in texte
    trace = construire_trace_calcul_fiscal_2025(e)
    assert [x.ordre for x in trace.lignes] == list(range(1, len(trace.lignes)+1))
    assert next(x for x in trace.lignes if x.libelle == "Récupération AE 42200").montant == 2517
    assert "sans abattement" in next(x for x in trace.lignes if x.libelle == "Impôt total préliminaire").formule
    p = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "ae.pdf")
    with fitz.open(p) as pdf:
        texte = "\n".join(page.get_text() for page in pdf)
        for mot in ("11905", "23500", "42200", "Retenue Québec RL-1 + T4E", "FSS Québec 446"):
            assert mot in texte
        for page in pdf:
            for x0, y0, x1, y1, *_ in page.get_text("blocks"):
                assert 0 <= x0 < x1 <= page.rect.width
                assert 0 <= y0 < y1 <= page.rect.height
