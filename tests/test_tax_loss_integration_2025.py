"""7F : montants courants recalculés, JSON, rapports et régressions 7A–7E."""
from dataclasses import replace
from decimal import Decimal as D
import json
import fitz
import pytest
from tests.test_tax_loss_ledger_2025 import perte, capacite
from tests.test_tax_capital_gains_2025 import dossier_capital, profil_capital
from tests.test_tax_case_storage import _dossier
from tests.test_tax_rental_income_2025 import dossier_location
from tests.test_tax_self_employment_contributions_2025 import dossier_7c
from src.comptaprivee.tax_loss_ledger_2025 import RegistrePertes2025, DemandePerte2025
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025 as calcul, formater_estimation_fiscale_2025
from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
from src.comptaprivee.tax_calculation_trace_2025 import construire_trace_calcul_fiscal_2025, formater_trace_calcul_fiscal_2025


def pertes():
    return RegistrePertes2025((perte(), perte(juridiction='quebec')))


@pytest.mark.parametrize('fabrique', [_dossier, dossier_location, dossier_7c])
def test_non_capital_reduit_imposable_pas_revenu_net(fabrique):
    d = fabrique()
    base = calcul(d)
    e = calcul(replace(d, registre_pertes=pertes()))
    for j in ('federal', 'quebec'):
        for n in ('total', 'net'):
            assert getattr(e.revenu, f'revenu_{n}_{j}') == getattr(base.revenu, f'revenu_{n}_{j}')
        assert getattr(e.revenu, 'revenu_imposable_' + j) == getattr(base.revenu, 'revenu_imposable_' + j) - D('400')
    assert e.base == base.base
    assert e.location == base.location
    assert e.cotisations_autonomes == base.cotisations_autonomes
    assert calcul(e.dossier) == e
    for texte in (formater_estimation_fiscale_2025(e), formater_trace_calcul_fiscal_2025(construire_trace_calcul_fiscal_2025(e))):
        assert '25200' in texte and '289' in texte
        assert '275 inchangés' in texte


def test_capital_courant_et_aucun_double_3f():
    d = dossier_capital()
    r = RegistrePertes2025(pertes_net_capital=(perte(True), perte(True, juridiction='quebec')))
    base = calcul(d, profil_capital=profil_capital())
    e = calcul(replace(d, registre_pertes=r), profil_capital=profil_capital())
    assert e.revenu.revenu_imposable_federal == base.revenu.revenu_imposable_federal - 400
    assert e.revenu.revenu_net_quebec == base.revenu.revenu_net_quebec
    from tests.test_tax_capital_loss_carryovers_2025 import profil_pertes
    with pytest.raises(ValueError, match='double comptage'):
        calcul(e.dossier, profil_capital=profil_capital(), profil_reports_pertes=profil_pertes(e.dossier))


def test_capacite_saisie_ne_remplace_pas_calcul_annuel():
    r = RegistrePertes2025(pertes_net_capital=(perte(True),), capacites=(capacite(gains_imposables_disponibles=D('999999')),))
    with pytest.raises(ValueError, match='revenu ordinaire interdit'):
        calcul(replace(_dossier(), registre_pertes=r))


def test_arriere_capital_rapproche_et_aucun_effet_sur_solde_courant():
    d = dossier_capital('3000')
    p = perte(True, annee_origine=2025, disponible=D('530'),
        demandes=(DemandePerte2025('arriere', 2024, D('200')),))
    r = RegistrePertes2025(pertes_net_capital=(p, replace(p, juridiction='quebec')),
        capacites=(capacite(annee_visee=2024), capacite(juridiction='quebec', annee_visee=2024)))
    base = calcul(d, profil_capital=profil_capital())
    e = calcul(replace(d, registre_pertes=r), profil_capital=profil_capital())
    assert e.revenu == base.revenu and e.federal == base.federal and e.quebec == base.quebec
    assert replace(e.rapprochement, limitations=base.rapprochement.limitations) == base.rapprochement
    assert "aucun report de perte" not in " ".join(e.rapprochement.limitations)
    assert "suivi dans le registre 7F" in formater_estimation_fiscale_2025(e)
    assert all(s.restant == D('330') for s in e.pertes_7f.soldes)
    with pytest.raises(ValueError, match='différent'):
        calcul(replace(d, registre_pertes=replace(r, pertes_net_capital=(replace(p, disponible=D('531')),))), profil_capital=profil_capital())


def test_non_capital_2025_externe_ne_permet_pas_estimation_incoherente():
    p = perte(annee_origine=2025, demandes=())
    with pytest.raises(ValueError, match='préparation séparée'):
        calcul(replace(_dossier(), registre_pertes=RegistrePertes2025((p,))))


def test_json_dossier_ancien_nouveau_pdf(tmp_path):
    d = replace(_dossier(), registre_pertes=pertes())
    e = calcul(d)
    chemin = sauvegarder_dossier_fiscal(d, destination=tmp_path / 'fictif.json', estimation=e)
    recharge = charger_dossier_fiscal(chemin)
    assert recharge.dossier == d
    assert calcul(recharge.dossier) == e
    contenu = json.loads(chemin.read_text(encoding='utf-8'))
    contenu.pop('registre_pertes')
    chemin.write_text(json.dumps(contenu), encoding='utf-8')
    assert charger_dossier_fiscal(chemin).dossier.registre_pertes == RegistrePertes2025()
    pdf = exporter_rapport_fiscal_pdf_2025(e, tmp_path / 'fictif.pdf')
    with fitz.open(pdf) as document:
        texte = '\n'.join(page.get_text() for page in document)
    assert 'PERTES ET REPORTS 2025' in texte and '25200' in texte and '289' in texte
