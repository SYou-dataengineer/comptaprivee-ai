from src.comptaprivee.tax_compliance import (
    IA_EXTERNE_AUTORISEE,
    MODE_LOCAL_PAR_DEFAUT,
    TRANSMISSION_ARC_ACTIVE,
    TRANSMISSION_REVENU_QUEBEC_ACTIVE,
    VALIDATION_HUMAINE_OBLIGATOIRE,
    etat_conformite_initial,
    traitement_ia_externe_autorise,
    transmission_autorisee,
)


def test_mode_local_active_par_defaut() -> None:
    assert MODE_LOCAL_PAR_DEFAUT is True
    assert etat_conformite_initial().mode_local is True


def test_validation_humaine_obligatoire() -> None:
    assert VALIDATION_HUMAINE_OBLIGATOIRE is True
    assert (
        etat_conformite_initial().validation_humaine_obligatoire
        is True
    )


def test_transmissions_gouvernementales_desactivees() -> None:
    assert TRANSMISSION_ARC_ACTIVE is False
    assert TRANSMISSION_REVENU_QUEBEC_ACTIVE is False


def test_arc_refuse_sans_validation_humaine() -> None:
    autorisee, raison = transmission_autorisee(
        "ARC",
        validation_humaine_effectuee=False,
    )

    assert autorisee is False
    assert "Validation humaine obligatoire" in raison


def test_arc_reste_bloquee_apres_validation_humaine() -> None:
    autorisee, raison = transmission_autorisee(
        "ARC",
        validation_humaine_effectuee=True,
    )

    assert autorisee is False
    assert "EFILE" in raison


def test_revenu_quebec_reste_bloquee_apres_validation_humaine() -> None:
    autorisee, raison = transmission_autorisee(
        "Revenu Québec",
        validation_humaine_effectuee=True,
    )

    assert autorisee is False
    assert "certification" in raison


def test_ia_externe_desactivee() -> None:
    assert IA_EXTERNE_AUTORISEE is False
    assert traitement_ia_externe_autorise() is False


def test_destination_inconnue_est_refusee() -> None:
    import pytest

    with pytest.raises(ValueError):
        transmission_autorisee(
            "Autre service",
            validation_humaine_effectuee=True,
        )
