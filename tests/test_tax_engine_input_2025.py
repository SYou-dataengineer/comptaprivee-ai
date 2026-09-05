from decimal import Decimal
from pathlib import Path

import pytest

from src.comptaprivee.tax_engine_input_2025 import (
    consolider_base_fiscale_emploi_2025,
)
from src.comptaprivee.tax_field_validation import DonneeFiscaleValidee
from src.comptaprivee.tax_validated_case import DossierFiscalValide


def _validee(
    document: str,
    type_document: str,
    case: str,
    valeur: str,
) -> DonneeFiscaleValidee:
    montant = Decimal(valeur)

    return DonneeFiscaleValidee(
        document=Path(document),
        type_document=type_document,
        case=case,
        libelle=f"{type_document} {case}",
        valeur_extraite=montant,
        valeur_validee=montant,
        corrigee=False,
        statut="Validé par le comptable",
    )


def _donnees_completes(
    revenu_t4: str = "52000",
    revenu_rl1: str = "52000",
    rrq_ba: str = "2500",
    rrq_bb: str = "396",
    ae: str = "850",
    rqap: str = "260",
):
    return (
        _validee("T4.pdf", "T4", "14", revenu_t4),
        _validee("T4.pdf", "T4", "17", rrq_ba),
        _validee("T4.pdf", "T4", "17A", rrq_bb),
        _validee("T4.pdf", "T4", "18", ae),
        _validee("T4.pdf", "T4", "22", "7500"),
        _validee("T4.pdf", "T4", "24", "52000"),
        _validee("T4.pdf", "T4", "26", "52000"),
        _validee("T4.pdf", "T4", "55", rqap),
        _validee("T4.pdf", "T4", "56", "52000"),
        _validee("RL1.pdf", "RL-1", "A", revenu_rl1),
        _validee("RL1.pdf", "RL-1", "B.A", rrq_ba),
        _validee("RL1.pdf", "RL-1", "B.B", rrq_bb),
        _validee("RL1.pdf", "RL-1", "C", ae),
        _validee("RL1.pdf", "RL-1", "E", "6200"),
        _validee("RL1.pdf", "RL-1", "G", "52000"),
        _validee("RL1.pdf", "RL-1", "H", rqap),
        _validee("RL1.pdf", "RL-1", "I", "52000"),
    )


def _dossier(
    donnees=None,
    annee: int = 2025,
    province: str = "Québec",
) -> DossierFiscalValide:
    return DossierFiscalValide(
        client="Client Test",
        annee_fiscale=annee,
        province=province,
        documents=(Path("T4.pdf"), Path("RL1.pdf")),
        donnees_validees=(
            tuple(donnees)
            if donnees is not None
            else _donnees_completes()
        ),
    )


def test_consolide_dossier_complet() -> None:
    base = consolider_base_fiscale_emploi_2025(
        _dossier()
    )

    assert base.revenu_emploi_federal == Decimal("52000")
    assert base.revenu_emploi_quebec == Decimal("52000")
    assert base.nombre_t4 == 1
    assert base.nombre_rl1 == 1


def test_ne_double_compte_pas_revenu_t4_et_rl1() -> None:
    base = consolider_base_fiscale_emploi_2025(
        _dossier()
    )

    assert base.revenu_emploi_federal != Decimal("104000")
    assert base.revenu_emploi_quebec != Decimal("104000")


def test_conserve_retenues_federale_et_quebec_separees() -> None:
    base = consolider_base_fiscale_emploi_2025(
        _dossier()
    )

    assert base.impot_federal_retenu == Decimal("7500")
    assert base.impot_quebec_retenu == Decimal("6200")


def test_difference_revenus_t4_rl1_est_permises() -> None:
    base = consolider_base_fiscale_emploi_2025(
        _dossier(
            _donnees_completes(
                revenu_t4="52000",
                revenu_rl1="52750",
            )
        )
    )

    assert base.revenu_emploi_federal == Decimal("52000")
    assert base.revenu_emploi_quebec == Decimal("52750")
    assert len(base.avertissements) == 1


def test_incoherence_rrq_est_refusee() -> None:
    donnees = list(_donnees_completes())
    donnees[10] = _validee(
        "RL1.pdf",
        "RL-1",
        "B.A",
        "2501",
    )

    with pytest.raises(ValueError):
        consolider_base_fiscale_emploi_2025(
            _dossier(donnees)
        )


def test_incoherence_ae_est_refusee() -> None:
    donnees = list(_donnees_completes())
    donnees[12] = _validee(
        "RL1.pdf",
        "RL-1",
        "C",
        "849",
    )

    with pytest.raises(ValueError):
        consolider_base_fiscale_emploi_2025(
            _dossier(donnees)
        )


def test_incoherence_rqap_est_refusee() -> None:
    donnees = list(_donnees_completes())
    donnees[15] = _validee(
        "RL1.pdf",
        "RL-1",
        "H",
        "259",
    )

    with pytest.raises(ValueError):
        consolider_base_fiscale_emploi_2025(
            _dossier(donnees)
        )


def test_incoherence_gains_rrq_est_refusee() -> None:
    donnees = list(_donnees_completes())
    donnees[14] = _validee(
        "RL1.pdf",
        "RL-1",
        "G",
        "51000",
    )

    with pytest.raises(ValueError):
        consolider_base_fiscale_emploi_2025(
            _dossier(donnees)
        )


def test_revenu_t4_requis() -> None:
    donnees = tuple(
        donnee
        for donnee in _donnees_completes()
        if not (
            donnee.type_document == "T4"
            and donnee.case == "14"
        )
    )

    with pytest.raises(ValueError):
        consolider_base_fiscale_emploi_2025(
            _dossier(donnees)
        )


def test_revenu_rl1_requis() -> None:
    donnees = tuple(
        donnee
        for donnee in _donnees_completes()
        if not (
            donnee.type_document == "RL-1"
            and donnee.case == "A"
        )
    )

    with pytest.raises(ValueError):
        consolider_base_fiscale_emploi_2025(
            _dossier(donnees)
        )


def test_annee_autre_que_2025_refusee() -> None:
    with pytest.raises(ValueError):
        consolider_base_fiscale_emploi_2025(
            _dossier(annee=2024)
        )


def test_province_autre_que_quebec_refusee() -> None:
    with pytest.raises(ValueError):
        consolider_base_fiscale_emploi_2025(
            _dossier(province="Ontario")
        )


def test_rrq_deuxieme_absente_des_deux_cotes_devient_zero() -> None:
    donnees = tuple(
        donnee
        for donnee in _donnees_completes()
        if donnee.case not in {"17A", "B.B"}
    )

    base = consolider_base_fiscale_emploi_2025(
        _dossier(donnees)
    )

    assert base.rrq_deuxieme_supplementaire == Decimal("0")


def test_rrq_deuxieme_presente_un_seul_cote_est_refusee() -> None:
    donnees = tuple(
        donnee
        for donnee in _donnees_completes()
        if not (
            donnee.type_document == "RL-1"
            and donnee.case == "B.B"
        )
    )

    with pytest.raises(ValueError):
        consolider_base_fiscale_emploi_2025(
            _dossier(donnees)
        )


def test_cotisation_excédentaire_produit_avertissement() -> None:
    base = consolider_base_fiscale_emploi_2025(
        _dossier(
            _donnees_completes(
                rrq_ba="4400",
                rrq_bb="400",
                ae="900",
            )
        )
    )

    assert len(base.avertissements) == 3


def test_plusieurs_feuillets_sont_agreges_sans_double_compter() -> None:
    donnees = list(_donnees_completes())

    # On remplace les revenus initiaux par deux feuillets de 26 000 $.
    donnees = [
        donnee
        for donnee in donnees
        if not (
            donnee.case in {"14", "A"}
        )
    ]
    donnees.extend(
        (
            _validee("T4_A.pdf", "T4", "14", "26000"),
            _validee("T4_B.pdf", "T4", "14", "26000"),
            _validee("RL1_A.pdf", "RL-1", "A", "26000"),
            _validee("RL1_B.pdf", "RL-1", "A", "26000"),
        )
    )

    base = consolider_base_fiscale_emploi_2025(
        _dossier(donnees)
    )

    assert base.revenu_emploi_federal == Decimal("52000")
    assert base.revenu_emploi_quebec == Decimal("52000")
    assert base.nombre_t4 == 3
    assert base.nombre_rl1 == 3
