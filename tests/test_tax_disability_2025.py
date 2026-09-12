from decimal import Decimal

import pytest

from src.comptaprivee.tax_disability_2025 import (
    CreditDeficience2025,
    MONTANT_FEDERAL_HANDICAP_2025,
    MONTANT_QUEBEC_DEFICIENCE_2025,
    aucun_credit_deficience_2025,
    appliquer_credit_federal_handicap_2025,
    appliquer_credit_quebec_deficience_2025,
    credit_federal_handicap_2025,
    credit_quebec_deficience_2025,
    valider_credit_deficience_2025,
)
from src.comptaprivee.tax_federal_2025 import (
    ImpotFederalPreliminaire2025,
)
from src.comptaprivee.tax_quebec_2025 import (
    ImpotQuebecPreliminaire2025,
)


ZERO = Decimal("0")


def _credit_valide(
    federal=True,
    quebec=True,
    **modifications,
):
    valeurs = {
        "reclamer_federal": federal,
        "reclamer_quebec": quebec,
        "source_federale": "T2201 / approbation ARC",
        "source_quebec": "Attestation professionnelle Québec",
        "valide_par_comptable": True,
        "age_18_plus_au_1_janvier_2025": True,
        "deficience_12_mois_confirmee": True,
        "profil_soi_meme_resident_quebec": True,
        "ciph_approuve_arc": True,
        "attestation_quebec_confirmee": True,
        "aucun_conflit_soins_prepose_etablissement": True,
        "aucun_transfert_federal": True,
    }
    valeurs.update(modifications)
    return CreditDeficience2025(**valeurs)


def _impot_federal(
    montant="3000",
    limitation=(
        "Aucun crédit pour handicap, frais médicaux ou scolarité."
    ),
):
    return ImpotFederalPreliminaire2025(
        client="Client Test",
        annee_fiscale=2025,
        revenu_imposable=Decimal("52000"),
        impot_brut=Decimal("5000"),
        montant_personnel_base=ZERO,
        cotisation_base_rrq=ZERO,
        assurance_emploi_admissible=ZERO,
        rqap_admissible=ZERO,
        montant_canadien_emploi=ZERO,
        base_credits_non_remboursables=ZERO,
        credits_non_remboursables=ZERO,
        impot_federal_de_base=Decimal(montant),
        taux_credit=Decimal("0.145"),
        top_up_credit=ZERO,
        limitations=(limitation,),
    )


def _impot_quebec(
    montant="3000",
    limitation=(
        "Aucun crédit handicap, médical, scolarité ou don."
    ),
):
    return ImpotQuebecPreliminaire2025(
        client="Client Test",
        annee_fiscale=2025,
        province="Québec",
        revenu_imposable=Decimal("52000"),
        impot_brut=Decimal("5000"),
        montant_personnel_base=ZERO,
        taux_credit_personnel=Decimal("0.14"),
        credit_personnel_base=ZERO,
        impot_quebec_preliminaire=Decimal(montant),
        limitations=(limitation,),
    )


def test_objet_vide_est_valide():
    credit = aucun_credit_deficience_2025()
    assert valider_credit_deficience_2025(credit) == credit


def test_montants_officiels_2025():
    assert MONTANT_FEDERAL_HANDICAP_2025 == Decimal("10138")
    assert MONTANT_QUEBEC_DEFICIENCE_2025 == Decimal("4123")


@pytest.mark.parametrize(
    ("champ", "message"),
    [
        ("valide_par_comptable", "comptable"),
        ("age_18_plus_au_1_janvier_2025", "18 ans"),
        ("deficience_12_mois_confirmee", "12 mois"),
        (
            "profil_soi_meme_resident_quebec",
            "pour soi-même",
        ),
        (
            "aucun_conflit_soins_prepose_etablissement",
            "préposé",
        ),
    ],
)
def test_confirmations_generales_obligatoires(champ, message):
    with pytest.raises(ValueError, match=message):
        valider_credit_deficience_2025(
            _credit_valide(**{champ: False})
        )


def test_ciph_arc_obligatoire_si_federal():
    with pytest.raises(ValueError, match="CIPH"):
        valider_credit_deficience_2025(
            _credit_valide(ciph_approuve_arc=False)
        )


def test_source_federale_obligatoire_si_federal():
    with pytest.raises(ValueError, match="source fédérale"):
        valider_credit_deficience_2025(
            _credit_valide(source_federale=" ")
        )


def test_transfert_federal_hors_profil():
    with pytest.raises(ValueError, match="transfert"):
        valider_credit_deficience_2025(
            _credit_valide(aucun_transfert_federal=False)
        )


def test_attestation_quebec_obligatoire_si_quebec():
    with pytest.raises(ValueError, match="attestation"):
        valider_credit_deficience_2025(
            _credit_valide(attestation_quebec_confirmee=False)
        )


def test_source_quebec_obligatoire_si_quebec():
    with pytest.raises(ValueError, match="source Québec"):
        valider_credit_deficience_2025(
            _credit_valide(source_quebec=" ")
        )


def test_federal_non_reclame_nexige_pas_ciph():
    credit = _credit_valide(
        federal=False,
        ciph_approuve_arc=False,
        source_federale="",
        aucun_transfert_federal=False,
    )
    assert valider_credit_deficience_2025(credit) == credit


def test_quebec_non_reclame_nexige_pas_attestation():
    credit = _credit_valide(
        quebec=False,
        attestation_quebec_confirmee=False,
        source_quebec="",
    )
    assert valider_credit_deficience_2025(credit) == credit


def test_credit_federal_2025():
    assert (
        credit_federal_handicap_2025(
            _credit_valide(quebec=False)
        )
        == Decimal("1470.01")
    )


def test_credit_quebec_2025():
    assert (
        credit_quebec_deficience_2025(
            _credit_valide(federal=False)
        )
        == Decimal("577.22")
    )


def test_credit_non_reclame_vaut_zero():
    credit = aucun_credit_deficience_2025()
    assert credit_federal_handicap_2025(credit) == ZERO
    assert credit_quebec_deficience_2025(credit) == ZERO


def test_application_federale_reduit_impot():
    resultat = appliquer_credit_federal_handicap_2025(
        _impot_federal(),
        _credit_valide(quebec=False),
    )
    assert resultat.impot_federal_de_base == Decimal("1529.99")


def test_application_federale_plancher_zero():
    resultat = appliquer_credit_federal_handicap_2025(
        _impot_federal("1000"),
        _credit_valide(quebec=False),
    )
    assert resultat.impot_federal_de_base == ZERO


def test_application_federale_met_a_jour_limitation_initiale():
    resultat = appliquer_credit_federal_handicap_2025(
        _impot_federal(),
        _credit_valide(quebec=False),
    )
    assert (
        "Aucun crédit pour frais médicaux ou scolarité."
        in resultat.limitations
    )
    assert (
        "Crédit fédéral pour personnes handicapées inclus."
        in resultat.limitations
    )


def test_application_federale_apres_medical_et_scolarite():
    resultat = appliquer_credit_federal_handicap_2025(
        _impot_federal(
            limitation="Aucun crédit pour handicap."
        ),
        _credit_valide(quebec=False),
    )
    assert "Aucun crédit pour handicap." not in resultat.limitations


def test_application_quebec_reduit_impot():
    resultat = appliquer_credit_quebec_deficience_2025(
        _impot_quebec(),
        _credit_valide(federal=False),
    )
    assert resultat.impot_quebec_preliminaire == Decimal("2422.78")


def test_application_quebec_plancher_zero():
    resultat = appliquer_credit_quebec_deficience_2025(
        _impot_quebec("500"),
        _credit_valide(federal=False),
    )
    assert resultat.impot_quebec_preliminaire == ZERO


@pytest.mark.parametrize(
    ("avant", "apres"),
    [
        (
            "Aucun crédit handicap, médical, scolarité ou don.",
            "Aucun crédit médical, scolarité ou don.",
        ),
        (
            "Aucun crédit handicap, médical ou don.",
            "Aucun crédit médical ou don.",
        ),
        (
            "Aucun crédit handicap, scolarité ou don.",
            "Aucun crédit scolarité ou don.",
        ),
        (
            "Aucun crédit handicap ou don.",
            "Aucun crédit don.",
        ),
    ],
)
def test_application_quebec_met_a_jour_limitation(avant, apres):
    resultat = appliquer_credit_quebec_deficience_2025(
        _impot_quebec(limitation=avant),
        _credit_valide(federal=False),
    )
    assert apres in resultat.limitations
    assert (
        "Crédit Québec pour déficience grave et prolongée inclus."
        in resultat.limitations
    )


def test_application_zero_retourne_meme_objet_federal():
    impot = _impot_federal()
    assert (
        appliquer_credit_federal_handicap_2025(
            impot,
            aucun_credit_deficience_2025(),
        )
        is impot
    )


def test_application_zero_retourne_meme_objet_quebec():
    impot = _impot_quebec()
    assert (
        appliquer_credit_quebec_deficience_2025(
            impot,
            aucun_credit_deficience_2025(),
        )
        is impot
    )
