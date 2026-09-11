from decimal import Decimal

from src.comptaprivee.tax_calculation_trace_2025 import (
    construire_trace_calcul_fiscal_2025,
    formater_trace_calcul_fiscal_2025,
)
from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
)
from src.comptaprivee.tax_tuition_2025 import FraisScolarite2025
from tests.test_tax_estimation_2025 import _dossier_52000


def _scolarite_3000():
    return FraisScolarite2025(
        montant_admissible_federal=Decimal("3000"),
        montant_admissible_quebec=Decimal("3000"),
        source_federale="T2202 - établissement admissible",
        source_quebec="Reçu officiel - établissement admissible",
        valide_par_comptable=True,
        piece_federale_confirmee=True,
        recu_officiel_quebec_confirme=True,
        seuil_100_confirme=True,
        remboursements_soustraits=True,
        frais_2025_uniquement=True,
        aucun_report_anterieur=True,
        aucun_transfert=True,
        credit_canadien_formation_non_reclame=True,
        profil_resident_quebec_simple=True,
    )


def test_trace_scolarite_ajoute_deux_etapes():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        frais_scolarite=_scolarite_3000(),
    )
    trace = construire_trace_calcul_fiscal_2025(e)

    assert len(trace.lignes) == 19
    assert [x.ordre for x in trace.lignes] == list(range(1, 20))


def test_trace_scolarite_affiche_credits():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        frais_scolarite=_scolarite_3000(),
    )
    texte = formater_trace_calcul_fiscal_2025(
        construire_trace_calcul_fiscal_2025(e)
    )

    assert "Crédit fédéral pour frais de scolarité" in texte
    assert "Crédit Québec pour frais de scolarité / examen" in texte
    assert "435,00 $" in texte
    assert "240,00 $" in texte


def test_trace_scolarite_affiche_sources_et_lignes():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        frais_scolarite=_scolarite_3000(),
    )
    texte = formater_trace_calcul_fiscal_2025(
        construire_trace_calcul_fiscal_2025(e)
    )

    assert "ARC annexe 11 / ligne 32300" in texte
    assert "Revenu Québec annexe T / ligne 398" in texte
    assert "T2202 - établissement admissible" in texte
    assert "Reçu officiel - établissement admissible" in texte


def test_trace_scolarite_affiche_taux():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        frais_scolarite=_scolarite_3000(),
    )
    texte = formater_trace_calcul_fiscal_2025(
        construire_trace_calcul_fiscal_2025(e)
    )

    assert "14,5 %" in texte
    assert "8 %" in texte


def test_trace_sans_scolarite_ne_change_pas_nombre_etapes():
    e = calculer_estimation_fiscale_2025(_dossier_52000())
    trace = construire_trace_calcul_fiscal_2025(e)

    assert len(trace.lignes) == 17
    assert "Crédit fédéral pour frais de scolarité" not in (
        formater_trace_calcul_fiscal_2025(trace)
    )
