from dataclasses import replace
from decimal import Decimal as D
import fitz
import pytest
from src.comptaprivee.tax_donations_2025 import (
    ventiler_credit_federal_dons_2025 as federal, ventiler_credit_quebec_dons_2025 as quebec,
    DonsBienfaisance2025,
)
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from tests.test_tax_donations_2025 import _dons_valides
from tests.test_tax_interest_income_2025 import calcul, dossier_interets
from tests.test_tax_federal_top_up_integration_2025 import verifier_t1


@pytest.mark.parametrize("revenu,total,base", [
    ("253413.99", "261", "0"), ("253414", "261", "0"), ("253414.01", "261", ".01"),
    ("253514", "265", "100"), ("254214", "293", "800"), ("300000", "293", "800"),
])
def test_federal_bornes_et_portion_revenu(revenu, total, base):
    r = federal(_dons_valides(), D(revenu))
    assert r.total == D(total)
    assert r.base_taux_superieur == D(base)
    assert r.base_premiers_200 + r.base_taux_intermediaire + r.base_taux_superieur == D(1000)


@pytest.mark.parametrize("revenu,total,base", [
    ("129589.99", "232", "0"), ("129590", "232", "0"), ("129590.01", "232", ".01"),
    ("129690", "233.75", "100"), ("130390", "246", "800"), ("300000", "246", "800"),
])
def test_quebec_bornes_et_portion_revenu(revenu, total, base):
    r = quebec(_dons_valides(), D(revenu))
    assert r.total == D(total)
    assert r.base_taux_superieur == D(base)
    assert r.base_premiers_200 + r.base_taux_intermediaire + r.base_taux_superieur == D(1000)


@pytest.mark.parametrize("montant,fed,qc", [("0", "0", "0"), (".01", "0", "0"), ("200", "29", "40"), ("200.01", "29", "40")])
def test_premiers_200_inchanges_a_haut_revenu(montant, fed, qc):
    assert federal(_dons_valides(montant), D(300000)).total == D(fed)
    assert quebec(_dons_valides(montant), D(300000)).total == D(qc)


def test_arrondi_de_chaque_ligne_monetaire():
    f = federal(_dons_valides("200.04"), D("253414.02"))
    assert f.credit_taux_intermediaire == f.credit_taux_superieur == D(".01")
    assert f.total == D("29.02")
    q = quebec(_dons_valides("200.03"), D("129590.01"))
    assert q.credit_taux_intermediaire == q.credit_taux_superieur == 0
    assert q.total == D(40)


def test_estimation_haut_revenu_dons_et_sans_don():
    sans = calcul(dossier_interets("300000"))
    e = calcul(dossier_interets("300000"), dons_bienfaisance=_dons_valides())
    assert e.revenu == sans.revenu
    assert e.federal.credits_federaux_complets.credit_dons_ligne_34900 == D(293)
    assert sans.federal.impot_federal_de_base - e.federal.impot_federal_de_base == D(293)
    assert sans.quebec.impot_quebec_preliminaire - e.quebec.impot_quebec_preliminaire == D(246)
    verifier_t1(e)
    verifier_t1(sans)


def test_reports_utilisent_reclamation_pas_dons_bruts():
    from tests.test_tax_donation_carryforward_2025 import dons
    e = calcul(dossier_interets("300000"), dons_bienfaisance=dons(montant_reclame=D(500)))
    assert e.federal.credits_federaux_complets.credit_dons_ligne_34900 == D(128)
    assert e.federal.credits_federaux_complets.annexe9_ligne22 == D(29)
    assert e.resultat_reports_dons.montant_reclame == D(500)
    verifier_t1(e)


def test_trace_pdf_dons_sans_reports(tmp_path):
    e = calcul(dossier_interets("300000"), dons_bienfaisance=_dons_valides())
    trace = construire_trace_calcul_fiscal_2025(e)
    assert next(x for x in trace.lignes if x.libelle == "Dons fédéraux — base à 33 %").montant == D(800)
    assert next(x for x in trace.lignes if x.libelle == "Dons Québec — base à 25,75 %").montant == D(800)
    assert [x.ordre for x in trace.lignes] == list(range(1, len(trace.lignes) + 1))
    f = exporter_rapport_fiscal_pdf_2025(e, tmp_path / "cas.pdf")
    with fitz.open(f) as pdf:
        texte = "\n".join(p.get_text() for p in pdf)
        for p in pdf:
            for x0, y0, x1, y1, *_ in p.get_text("blocks"):
                assert 0 <= x0 < x1 <= p.rect.width
                assert 0 <= y0 < y1 <= p.rect.height
    assert "ligne 34900 : 293.00" in texte and "ligne 395 : 246.00" in texte
    assert "25,75 %" in texte and "33 %" in texte
    assert "Reçu officiel organisme enregistré" in texte
