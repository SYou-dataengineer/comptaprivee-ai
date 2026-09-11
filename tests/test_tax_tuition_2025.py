from decimal import Decimal

import pytest

from src.comptaprivee.tax_federal_2025 import (
    ImpotFederalPreliminaire2025,
)
from src.comptaprivee.tax_quebec_2025 import (
    ImpotQuebecPreliminaire2025,
)
from src.comptaprivee.tax_tuition_2025 import (
    FraisScolarite2025,
    aucun_frais_scolarite_2025,
    appliquer_credit_federal_frais_scolarite_2025,
    appliquer_credit_quebec_frais_scolarite_2025,
    credit_federal_frais_scolarite_2025,
    credit_quebec_frais_scolarite_2025,
    valider_frais_scolarite_2025,
)


ZERO = Decimal("0")


def _frais_valides(
    fed: str = "3000",
    qc: str = "3000",
    **modifications,
) -> FraisScolarite2025:
    valeurs = {
        "montant_admissible_federal": Decimal(fed),
        "montant_admissible_quebec": Decimal(qc),
        "source_federale": "T2202 - établissement admissible",
        "source_quebec": "Reçu officiel - établissement admissible",
        "valide_par_comptable": True,
        "piece_federale_confirmee": True,
        "recu_officiel_quebec_confirme": True,
        "seuil_100_confirme": True,
        "remboursements_soustraits": True,
        "frais_2025_uniquement": True,
        "aucun_report_anterieur": True,
        "aucun_transfert": True,
        "credit_canadien_formation_non_reclame": True,
        "profil_resident_quebec_simple": True,
    }
    valeurs.update(modifications)
    return FraisScolarite2025(**valeurs)


def _impot_federal(
    montant: str = "1000",
    limitation: str = (
        "Aucun crédit pour handicap, frais médicaux ou scolarité."
    ),
) -> ImpotFederalPreliminaire2025:
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
    montant: str = "1000",
    limitation: str = (
        "Aucun crédit handicap, médical, scolarité ou don."
    ),
) -> ImpotQuebecPreliminaire2025:
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


def test_aucun_frais_retourne_objet_vide():
    frais = aucun_frais_scolarite_2025()
    assert frais.montant_admissible_federal == ZERO
    assert frais.montant_admissible_quebec == ZERO


def test_objet_vide_est_valide():
    frais = aucun_frais_scolarite_2025()
    assert valider_frais_scolarite_2025(frais) == frais


def test_montant_federal_negatif_refuse():
    with pytest.raises(ValueError, match="fédéral"):
        valider_frais_scolarite_2025(
            _frais_valides(fed="-1")
        )


def test_montant_quebec_negatif_refuse():
    with pytest.raises(ValueError, match="Québec"):
        valider_frais_scolarite_2025(
            _frais_valides(qc="-1")
        )


def test_montant_federal_de_100_refuse():
    with pytest.raises(ValueError, match="dépasser 100"):
        valider_frais_scolarite_2025(
            _frais_valides(fed="100", qc="0")
        )


def test_montant_quebec_de_100_refuse():
    with pytest.raises(ValueError, match="dépasser 100"):
        valider_frais_scolarite_2025(
            _frais_valides(fed="0", qc="100")
        )


def test_100_01_est_accepte():
    frais = _frais_valides(
        fed="100.01",
        qc="100.01",
    )
    assert valider_frais_scolarite_2025(frais) == frais


@pytest.mark.parametrize(
    ("champ", "message"),
    [
        ("valide_par_comptable", "comptable"),
        ("piece_federale_confirmee", "pièce fédérale"),
        ("recu_officiel_quebec_confirme", "reçu officiel Québec"),
        ("seuil_100_confirme", "seuil minimal"),
        ("remboursements_soustraits", "remboursements"),
        ("frais_2025_uniquement", "2025"),
        ("aucun_report_anterieur", "reportés"),
        ("aucun_transfert", "transferts"),
        (
            "credit_canadien_formation_non_reclame",
            "crédit canadien pour la formation",
        ),
        ("profil_resident_quebec_simple", "résident du Québec"),
    ],
)
def test_confirmations_obligatoires(champ, message):
    with pytest.raises(ValueError, match=message):
        valider_frais_scolarite_2025(
            _frais_valides(**{champ: False})
        )


def test_piece_federale_non_exigee_si_federal_zero():
    frais = _frais_valides(
        fed="0",
        piece_federale_confirmee=False,
        source_federale="",
    )
    assert valider_frais_scolarite_2025(frais) == frais


def test_recu_quebec_non_exige_si_quebec_zero():
    frais = _frais_valides(
        qc="0",
        recu_officiel_quebec_confirme=False,
        source_quebec="",
    )
    assert valider_frais_scolarite_2025(frais) == frais


def test_source_federale_obligatoire():
    with pytest.raises(ValueError, match="source fédérale"):
        valider_frais_scolarite_2025(
            _frais_valides(source_federale=" ")
        )


def test_source_quebec_obligatoire():
    with pytest.raises(ValueError, match="source Québec"):
        valider_frais_scolarite_2025(
            _frais_valides(source_quebec=" ")
        )


def test_credit_federal_3000():
    assert (
        credit_federal_frais_scolarite_2025(
            _frais_valides()
        )
        == Decimal("435.00")
    )


def test_credit_quebec_3000():
    assert (
        credit_quebec_frais_scolarite_2025(
            _frais_valides()
        )
        == Decimal("240.00")
    )


def test_arrondi_credit_federal():
    assert (
        credit_federal_frais_scolarite_2025(
            _frais_valides(
                fed="1234.56",
                qc="0",
            )
        )
        == Decimal("179.01")
    )


def test_arrondi_credit_quebec():
    assert (
        credit_quebec_frais_scolarite_2025(
            _frais_valides(
                fed="0",
                qc="1234.56",
            )
        )
        == Decimal("98.76")
    )


def test_application_federale_reduit_impot():
    resultat = appliquer_credit_federal_frais_scolarite_2025(
        _impot_federal(),
        _frais_valides(qc="0"),
    )
    assert resultat.impot_federal_de_base == Decimal("565.00")


def test_application_federale_refuse_report_implicite():
    with pytest.raises(ValueError, match="reportée"):
        appliquer_credit_federal_frais_scolarite_2025(
            _impot_federal("100"),
            _frais_valides(qc="0"),
        )


def test_application_federale_met_a_jour_limitation_initiale():
    resultat = appliquer_credit_federal_frais_scolarite_2025(
        _impot_federal(),
        _frais_valides(qc="0"),
    )
    assert (
        "Aucun crédit pour handicap ou frais médicaux."
        in resultat.limitations
    )
    assert (
        "Crédit fédéral pour frais de scolarité admissibles inclus."
        in resultat.limitations
    )


def test_application_federale_apres_medical():
    resultat = appliquer_credit_federal_frais_scolarite_2025(
        _impot_federal(
            limitation="Aucun crédit pour handicap ou scolarité."
        ),
        _frais_valides(qc="0"),
    )
    assert "Aucun crédit pour handicap." in resultat.limitations


def test_application_quebec_reduit_impot():
    resultat = appliquer_credit_quebec_frais_scolarite_2025(
        _impot_quebec(),
        _frais_valides(fed="0"),
    )
    assert resultat.impot_quebec_preliminaire == Decimal("760.00")


def test_application_quebec_refuse_report_implicite():
    with pytest.raises(ValueError, match="reportée"):
        appliquer_credit_quebec_frais_scolarite_2025(
            _impot_quebec("100"),
            _frais_valides(fed="0"),
        )


@pytest.mark.parametrize(
    ("avant", "apres"),
    [
        (
            "Aucun crédit handicap, médical, scolarité ou don.",
            "Aucun crédit handicap, médical ou don.",
        ),
        (
            "Aucun crédit handicap, médical ou scolarité.",
            "Aucun crédit handicap ou médical.",
        ),
        (
            "Aucun crédit handicap, scolarité ou don.",
            "Aucun crédit handicap ou don.",
        ),
        (
            "Aucun crédit handicap ou scolarité.",
            "Aucun crédit handicap.",
        ),
    ],
)
def test_application_quebec_met_a_jour_limitations(avant, apres):
    resultat = appliquer_credit_quebec_frais_scolarite_2025(
        _impot_quebec(limitation=avant),
        _frais_valides(fed="0"),
    )
    assert apres in resultat.limitations
    assert (
        "Crédit Québec pour frais de scolarité ou d'examen "
        "admissibles inclus."
        in resultat.limitations
    )


def test_credit_zero_ne_modifie_pas_impot_federal():
    impot = _impot_federal()
    assert (
        appliquer_credit_federal_frais_scolarite_2025(
            impot,
            aucun_frais_scolarite_2025(),
        )
        is impot
    )


def test_credit_zero_ne_modifie_pas_impot_quebec():
    impot = _impot_quebec()
    assert (
        appliquer_credit_quebec_frais_scolarite_2025(
            impot,
            aucun_frais_scolarite_2025(),
        )
        is impot
    )
