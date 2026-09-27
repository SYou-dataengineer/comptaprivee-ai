from dataclasses import replace
from decimal import Decimal

import pytest

from src.comptaprivee.tax_income_2025 import RevenuNetImposable2025
from src.comptaprivee.tax_support_payments_2025 import (
    PensionAlimentairePayee2025,
    appliquer_pension_alimentaire_payee_2025,
    lignes_resume_pension_alimentaire_payee_2025,
    valider_pension_alimentaire_payee_2025,
)


ZERO = Decimal("0")


def _revenu() -> RevenuNetImposable2025:
    return RevenuNetImposable2025(
        client="Client Test",
        annee_fiscale=2025,
        province="Québec",
        revenu_total_federal=Decimal("52000"),
        deduction_rrq_amelioree_federale=Decimal("1485"),
        revenu_net_federal=Decimal("50515"),
        revenu_imposable_federal=Decimal("50515"),
        revenu_total_quebec=Decimal("52000"),
        deduction_travailleur_quebec=Decimal("935"),
        deduction_rrq_quebec=Decimal("1485"),
        revenu_net_quebec=Decimal("49580"),
        revenu_imposable_quebec=Decimal("49580"),
        profil="Emploi Québec simple 2025",
        limitations=("Aucune autre déduction de revenu net ou imposable.",),
    )


def _profil(
    total="6000",
    federal="6000",
    quebec="6000",
) -> PensionAlimentairePayee2025:
    return PensionAlimentairePayee2025(
        total_paye_federal_21999=Decimal(total),
        deduction_federale_22000=Decimal(federal),
        deduction_quebec_225=Decimal(quebec),
        source_federale="Ordonnance + preuve de paiements 2025",
        source_quebec="Ordonnance + preuve de paiements 2025",
        valide_par_comptable=True,
        ordonnance_ou_entente_ecrite_confirmee=True,
        paiement_periodique_conjoint_ex_conjoint_confirme=True,
        vie_separee_au_moment_paiement_confirmee=True,
        enregistrement_arc_confirme=True,
        montant_federal_confirme=True,
        montant_quebec_confirme=True,
        aucun_credit_personnel_lie_confirme=True,
    )


def test_profil_vide_est_accepte():
    assert valider_pension_alimentaire_payee_2025(
        PensionAlimentairePayee2025()
    ) == PensionAlimentairePayee2025()


@pytest.mark.parametrize(
    "champ",
    [
        "total_paye_federal_21999",
        "deduction_federale_22000",
        "deduction_quebec_225",
    ],
)
def test_montants_negatifs_refuses(champ):
    profil = replace(PensionAlimentairePayee2025(), **{champ: Decimal("-1")})
    with pytest.raises(ValueError):
        valider_pension_alimentaire_payee_2025(profil)


@pytest.mark.parametrize("valeur", [Decimal("NaN"), Decimal("Infinity")])
@pytest.mark.parametrize(
    "champ",
    [
        "total_paye_federal_21999",
        "deduction_federale_22000",
        "deduction_quebec_225",
    ],
)
def test_montants_non_finis_refuses(champ, valeur):
    profil = replace(PensionAlimentairePayee2025(), **{champ: valeur})
    with pytest.raises(ValueError):
        valider_pension_alimentaire_payee_2025(profil)


def test_montants_sont_arrondis_au_cent():
    valide = valider_pension_alimentaire_payee_2025(
        _profil("6000.005", "6000.004", "5999.994")
    )
    assert valide.total_paye_federal_21999 == Decimal("6000.01")
    assert valide.deduction_federale_22000 == Decimal("6000.00")
    assert valide.deduction_quebec_225 == Decimal("5999.99")


def test_ligne_22000_ne_peut_pas_depasser_21999():
    with pytest.raises(ValueError, match="ne peut pas dépasser"):
        valider_pension_alimentaire_payee_2025(
            _profil(total="5000", federal="6000")
        )


@pytest.mark.parametrize(
    "champ",
    [
        "pension_enfant",
        "regime_avant_mai_1997_ou_t1157",
        "arrerages_ou_retroactif",
        "paiement_forfaitaire",
        "remboursement_pension",
        "frais_juridiques_ou_comptables",
        "plusieurs_beneficiaires",
        "annee_changement_etat_civil_avec_choix_credit",
    ],
)
def test_cas_avances_refuses(champ):
    with pytest.raises(ValueError, match="hors périmètre 4E"):
        valider_pension_alimentaire_payee_2025(
            replace(_profil(), **{champ: True})
        )


@pytest.mark.parametrize(
    "champ",
    [
        "valide_par_comptable",
        "ordonnance_ou_entente_ecrite_confirmee",
        "paiement_periodique_conjoint_ex_conjoint_confirme",
        "vie_separee_au_moment_paiement_confirmee",
        "aucun_credit_personnel_lie_confirme",
    ],
)
def test_confirmations_generales_obligatoires(champ):
    with pytest.raises(ValueError):
        valider_pension_alimentaire_payee_2025(
            replace(_profil(), **{champ: False})
        )


def test_enregistrement_arc_obligatoire_si_montant_federal():
    with pytest.raises(ValueError):
        valider_pension_alimentaire_payee_2025(
            replace(_profil(), enregistrement_arc_confirme=False)
        )


def test_confirmation_federale_obligatoire():
    with pytest.raises(ValueError):
        valider_pension_alimentaire_payee_2025(
            replace(_profil(), montant_federal_confirme=False)
        )


def test_confirmation_quebec_obligatoire():
    with pytest.raises(ValueError):
        valider_pension_alimentaire_payee_2025(
            replace(_profil(), montant_quebec_confirme=False)
        )


def test_source_federale_obligatoire():
    with pytest.raises(ValueError):
        valider_pension_alimentaire_payee_2025(
            replace(_profil(), source_federale=" ")
        )


def test_source_quebec_obligatoire():
    with pytest.raises(ValueError):
        valider_pension_alimentaire_payee_2025(
            replace(_profil(), source_quebec=" ")
        )


def test_federal_seul_n_exige_pas_confirmation_quebec():
    profil = replace(
        _profil(quebec="0"),
        source_quebec="",
        montant_quebec_confirme=False,
    )
    valide = valider_pension_alimentaire_payee_2025(profil)
    assert valide.deduction_federale_22000 == Decimal("6000.00")


def test_application_reduit_separement_federal_et_quebec():
    revenu = appliquer_pension_alimentaire_payee_2025(
        _revenu(),
        _profil(),
    )
    assert revenu.revenu_total_federal == Decimal("52000")
    assert revenu.revenu_total_quebec == Decimal("52000")
    assert revenu.revenu_net_federal == Decimal("44515.00")
    assert revenu.revenu_imposable_federal == Decimal("44515.00")
    assert revenu.revenu_net_quebec == Decimal("43580.00")
    assert revenu.revenu_imposable_quebec == Decimal("43580.00")


def test_ligne_21999_seule_est_informationnelle():
    revenu = appliquer_pension_alimentaire_payee_2025(
        _revenu(),
        _profil(total="6000", federal="0", quebec="0"),
    )
    assert revenu.revenu_net_federal == Decimal("50515")
    assert revenu.revenu_net_quebec == Decimal("49580")


def test_application_plafonne_revenus_a_zero():
    revenu = appliquer_pension_alimentaire_payee_2025(
        _revenu(),
        _profil(total="999999", federal="999999", quebec="999999"),
    )
    assert revenu.revenu_net_federal == ZERO
    assert revenu.revenu_imposable_federal == ZERO
    assert revenu.revenu_net_quebec == ZERO
    assert revenu.revenu_imposable_quebec == ZERO


def test_application_refuse_autre_annee():
    revenu = replace(_revenu(), annee_fiscale=2024)
    with pytest.raises(ValueError, match="uniquement l'année 2025"):
        appliquer_pension_alimentaire_payee_2025(revenu, _profil())


def test_resume_contient_lignes_et_sources():
    texte = "\n".join(lignes_resume_pension_alimentaire_payee_2025(_profil()))
    assert "BLOC 4E" in texte
    assert "21999" in texte
    assert "22000" in texte
    assert "ligne 225" in texte
    assert "6000.00 $" in texte
    assert "Ordonnance + preuve de paiements 2025" in texte


def test_resume_vide_si_aucun_montant():
    assert lignes_resume_pension_alimentaire_payee_2025(
        PensionAlimentairePayee2025()
    ) == []
