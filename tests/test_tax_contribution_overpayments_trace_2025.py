from dataclasses import replace
from decimal import Decimal

from src.comptaprivee.tax_calculation_trace_2025 import (
    construire_trace_calcul_fiscal_2025,
)
from src.comptaprivee.tax_contribution_overpayments_2025 import (
    CotisationsExcedentaires2025,
)
from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000


def _dossier_avec_excedents():
    dossier = _dossier_52000()
    remplacements = {
        ("T4", "17"): Decimal("3200.00"),
        ("RL-1", "B.A"): Decimal("3200.00"),
        ("T4", "18"): Decimal("700.00"),
        ("RL-1", "C"): Decimal("700.00"),
        ("T4", "55"): Decimal("300.00"),
        ("RL-1", "H"): Decimal("300.00"),
    }

    donnees = []
    for donnee in dossier.donnees_validees:
        cle = (donnee.type_document, donnee.case)
        if cle in remplacements:
            montant = remplacements[cle]
            donnee = replace(
                donnee,
                valeur_extraite=montant,
                valeur_validee=montant,
            )
        donnees.append(donnee)

    return replace(
        dossier,
        donnees_validees=tuple(donnees),
    )


def _profil():
    return CotisationsExcedentaires2025(
        rrq_ba=Decimal("3200.00"),
        rrq_bb=Decimal("0"),
        gains_admissibles_rrq=Decimal("52000"),
        assurance_emploi=Decimal("700.00"),
        gains_assurables_ae=Decimal("52000"),
        rqap=Decimal("300.00"),
        revenus_assujettis_rqap=Decimal("52000"),
        source="T4 / RL-1 validés",
        valide_par_comptable=True,
        resident_quebec_31_decembre_2025=True,
        emploi_quebec_uniquement=True,
        rrq_uniquement_sans_rpc=True,
        aucun_travail_autonome=True,
        profil_rrq_standard_18_64=True,
        aucun_cas_particulier_ae=True,
        aucun_cas_particulier_rqap=True,
        calcul_standard_confirme=True,
    )


def _trace():
    estimation = calculer_estimation_fiscale_2025(
        _dossier_avec_excedents(),
        cotisations_excedentaires=_profil(),
    )
    return construire_trace_calcul_fiscal_2025(estimation)


def test_trace_ajoute_trois_lignes():
    base = construire_trace_calcul_fiscal_2025(
        calculer_estimation_fiscale_2025(_dossier_52000())
    )
    trace = _trace()

    assert len(trace.lignes) == len(base.lignes) + 3


def test_trace_rrq_ligne_452():
    trace = _trace()
    ligne = next(
        x
        for x in trace.lignes
        if x.libelle == "Remboursement RRQ excédentaire"
    )

    assert ligne.section == "REMBOURSEMENTS"
    assert ligne.montant == Decimal("96.00")
    assert "ligne 452" in ligne.source
    assert "gains admissibles" in ligne.formule


def test_trace_ae_ligne_45000():
    trace = _trace()
    ligne = next(
        x
        for x in trace.lignes
        if x.libelle == "Remboursement assurance-emploi excédentaire"
    )

    assert ligne.montant == Decimal("18.80")
    assert "ligne 45000" in ligne.source
    assert "gains assurables" in ligne.formule


def test_trace_rqap_ligne_457():
    trace = _trace()
    ligne = next(
        x
        for x in trace.lignes
        if x.libelle == "Remboursement RQAP excédentaire"
    )

    assert ligne.montant == Decimal("43.12")
    assert "ligne 457" in ligne.source
    assert "2 000 $" in ligne.formule


def test_trace_sources_validees():
    trace = _trace()
    remboursements = [
        x
        for x in trace.lignes
        if x.section == "REMBOURSEMENTS"
    ]

    assert len(remboursements) == 3
    assert all("T4 / RL-1 validés" in x.source for x in remboursements)


def test_trace_resultat_inclut_remboursements_cotisations():
    trace = _trace()

    assert trace.resultat == "Remboursement estimé"
    assert trace.montant_resultat == Decimal("5768.97")


def test_trace_formule_resultat_mentionne_remboursements():
    trace = _trace()

    assert (
        "retenues + remboursements cotisations rrq/ae/rqap"
        in trace.formule_resultat.lower()
    )


def test_trace_sans_excedents_garde_formule_historique():
    trace = construire_trace_calcul_fiscal_2025(
        calculer_estimation_fiscale_2025(_dossier_52000())
    )

    assert trace.formule_resultat == (
        "Retenues totales - impôt total préliminaire"
    )


def test_trace_numerotation_continue():
    trace = _trace()

    assert [x.ordre for x in trace.lignes] == list(
        range(1, len(trace.lignes) + 1)
    )
