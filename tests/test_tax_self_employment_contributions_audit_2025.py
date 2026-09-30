"""Régression du choix ligne par ligne; demi-cents selon la convention logicielle."""
from dataclasses import replace
from decimal import Decimal
import pytest

from tests.test_tax_self_employment_2025 import dossier, entreprise
from src.comptaprivee.tax_rules_2025 import arrondir_cent
from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
from src.comptaprivee.tax_self_employment_contributions_2025 import (
    ProfilCotisationsAutonomes2025, CONFIRMATIONS_7C,
    calculer_cotisations_autonomes_2025,
)


def test_quantification_par_ligne_sans_precision_cachee():
    p=ProfilCotisationsAutonomes2025(activer=True,naissance='1980-01-01',source='Audit fictif',
        **{nom:True for nom in CONFIRMATIONS_7C})
    d=replace(dossier(),entreprises=(entreprise(revenu_brut=Decimal('3500.05')),))
    r=calculer_cotisations_autonomes_2025(d,p)
    u=dict(r.lignes_u)
    assert u['48']==Decimal('.01')
    assert u['71']==Decimal('0.00')
    assert u['99']==Decimal('0.00')
    # Même minimum prescrit, avec conservation des fractions de cent avant report.
    assiette=Decimal('.05')
    sans_arrondi_intermediaire=min(assiette*Decimal('.128'),2*assiette*Decimal('.064'))
    assert sans_arrondi_intermediaire==Decimal('.00640')
    assert arrondir_cent(sans_arrondi_intermediaire)==Decimal('.01')
    assert r.rrq_445 != arrondir_cent(sans_arrondi_intermediaire)


def test_brouillon_ne_leve_pas_le_garde_fou_annuel_7b():
    with pytest.raises(ValueError,match='7C'):
        calculer_estimation_fiscale_2025(dossier())
