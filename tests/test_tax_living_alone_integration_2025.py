from decimal import Decimal

import pytest

from src.comptaprivee.tax_estimation_2025 import (
    calculer_estimation_fiscale_2025,
    formater_estimation_fiscale_2025,
)
from src.comptaprivee.tax_living_alone_2025 import (
    PersonneVivantSeule2025,
)
from tests.test_tax_estimation_2025 import _dossier_52000


def _profil_simple():
    return PersonneVivantSeule2025(
        reclamer_montant=True,
        revenu_familial_net=Decimal("50095.00"),
        personne_vivant_seule_toute_annee=True,
        habitation_maintenue_par_contribuable=True,
        seulement_personnes_autorisees_dans_habitation=True,
        aucun_conjoint_31_decembre_2025=True,
        resident_quebec_canada_toute_annee=True,
        reclamer_additionnel_monoparental=False,
        enfant_majeur_etudes_admissible=False,
        aucun_droit_allocation_famille_decembre=False,
        mois_allocation_famille_2025=0,
        aucun_montant_age_ou_retraite=True,
        documents_justificatifs_confirmes=True,
        valide_par_comptable=True,
        source="Bail et factures validés",
    )


def test_sans_personne_seule_resultat_historique_inchange():
    e = calculer_estimation_fiscale_2025(_dossier_52000())
    assert e.rapprochement.impot_total_preliminaire == Decimal("8088.95")
    assert e.rapprochement.remboursement_estime == Decimal("5611.05")


def test_credit_personne_seule_reduit_impot_quebec():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        personne_vivant_seule=_profil_simple(),
    )
    assert e.quebec.impot_quebec_preliminaire == Decimal("4325.57")
    assert e.rapprochement.impot_total_preliminaire == Decimal("8001.16")
    assert e.rapprochement.remboursement_estime == Decimal("5698.84")


def test_estimation_conserve_profil_personne_seule():
    profil = _profil_simple()
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        personne_vivant_seule=profil,
    )
    assert e.personne_vivant_seule == profil


def test_revenu_familial_doit_correspondre_au_revenu_net_quebec():
    profil = PersonneVivantSeule2025(
        **{
            **_profil_simple().__dict__,
            "revenu_familial_net": Decimal("49000"),
        }
    )
    with pytest.raises(ValueError, match="revenu familial net"):
        calculer_estimation_fiscale_2025(
            _dossier_52000(),
            personne_vivant_seule=profil,
        )


def test_resume_affiche_ligne_361():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        personne_vivant_seule=_profil_simple(),
    )
    resume = formater_estimation_fiscale_2025(e)
    assert "PERSONNE VIVANT SEULE — QUÉBEC 2025" in resume
    assert "Montant annexe B / ligne 361 : 627,06 $" in resume
    assert "Crédit Québec : 87,79 $" in resume
    assert "Bail et factures validés" in resume


def test_rapprochement_ne_dit_plus_aucun_credit_familial():
    e = calculer_estimation_fiscale_2025(
        _dossier_52000(),
        personne_vivant_seule=_profil_simple(),
    )
    assert (
        "Aucun crédit familial, médical, étude ou handicap."
        not in e.rapprochement.limitations
    )
    assert (
        "Aucun crédit médical, étude ou handicap."
        in e.rapprochement.limitations
    )


def test_profil_invalide_bloque_estimation():
    profil = PersonneVivantSeule2025(
        **{
            **_profil_simple().__dict__,
            "documents_justificatifs_confirmes": False,
        }
    )
    with pytest.raises(ValueError, match="documents justificatifs"):
        calculer_estimation_fiscale_2025(
            _dossier_52000(),
            personne_vivant_seule=profil,
        )
