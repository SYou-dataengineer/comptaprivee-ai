from decimal import Decimal

import pytest

from src.comptaprivee.tax_living_alone_2025 import (
    MONTANT_ADDITIONNEL_MONOPARENTAL_2025,
    MONTANT_PERSONNE_VIVANT_SEULE_2025,
    REDUCTION_MENSUELLE_ALLOCATION_FAMILLE_2025,
    SEUIL_REDUCTION_ANNEXE_B_2025,
    TAUX_REDUCTION_ANNEXE_B_2025,
    PersonneVivantSeule2025,
    appliquer_credit_quebec_personne_vivant_seule_2025,
    credit_quebec_personne_vivant_seule_2025,
    montant_additionnel_monoparental_2025,
    montant_ligne_361_personne_vivant_seule_2025,
    valider_personne_vivant_seule_2025,
)
from src.comptaprivee.tax_quebec_2025 import (
    ImpotQuebecPreliminaire2025,
)


def _profil(**modifications):
    valeurs = {
        "reclamer_montant": True,
        "revenu_familial_net": Decimal("42090"),
        "personne_vivant_seule_toute_annee": True,
        "habitation_maintenue_par_contribuable": True,
        "seulement_personnes_autorisees_dans_habitation": True,
        "aucun_conjoint_31_decembre_2025": True,
        "resident_quebec_canada_toute_annee": True,
        "reclamer_additionnel_monoparental": False,
        "enfant_majeur_etudes_admissible": False,
        "aucun_droit_allocation_famille_decembre": False,
        "mois_allocation_famille_2025": 0,
        "aucun_montant_age_ou_retraite": True,
        "documents_justificatifs_confirmes": True,
        "valide_par_comptable": True,
        "source": "Bail et factures validés",
    }
    valeurs.update(modifications)
    return PersonneVivantSeule2025(**valeurs)


def _impot():
    return ImpotQuebecPreliminaire2025(
        client="Client Test",
        annee_fiscale=2025,
        province="Québec",
        revenu_imposable=Decimal("50000"),
        impot_brut=Decimal("6000"),
        montant_personnel_base=Decimal("18571"),
        taux_credit_personnel=Decimal("0.14"),
        credit_personnel_base=Decimal("2599.94"),
        impot_quebec_preliminaire=Decimal("3400.06"),
        limitations=(
            "Résident du Québec et du Canada pour toute l'année.",
            "Aucun montant pour conjoint, personne à charge ou âge.",
        ),
    )


def test_constantes_officielles_2025():
    assert MONTANT_PERSONNE_VIVANT_SEULE_2025 == Decimal("2128")
    assert MONTANT_ADDITIONNEL_MONOPARENTAL_2025 == Decimal("2627")
    assert REDUCTION_MENSUELLE_ALLOCATION_FAMILLE_2025 == Decimal("218.92")
    assert SEUIL_REDUCTION_ANNEXE_B_2025 == Decimal("42090")
    assert TAUX_REDUCTION_ANNEXE_B_2025 == Decimal("0.1875")


def test_profil_vide_retourne_zero():
    profil = PersonneVivantSeule2025()
    assert valider_personne_vivant_seule_2025(profil) == profil
    assert montant_ligne_361_personne_vivant_seule_2025(profil) == 0
    assert credit_quebec_personne_vivant_seule_2025(profil) == 0


def test_revenu_negatif_refuse():
    with pytest.raises(ValueError, match="négatif"):
        valider_personne_vivant_seule_2025(
            _profil(revenu_familial_net=Decimal("-1"))
        )


@pytest.mark.parametrize(
    "champ, message",
    [
        ("valide_par_comptable", "comptable"),
        (
            "resident_quebec_canada_toute_annee",
            "résidence Québec/Canada",
        ),
        (
            "aucun_conjoint_31_decembre_2025",
            "sans conjoint",
        ),
        (
            "personne_vivant_seule_toute_annee",
            "toute l'année",
        ),
        (
            "habitation_maintenue_par_contribuable",
            "maintenu l'habitation",
        ),
        (
            "seulement_personnes_autorisees_dans_habitation",
            "personnes permises",
        ),
        (
            "aucun_montant_age_ou_retraite",
            "âge ou revenus de retraite",
        ),
        (
            "documents_justificatifs_confirmes",
            "documents justificatifs",
        ),
    ],
)
def test_confirmations_obligatoires(champ, message):
    with pytest.raises(ValueError, match=message):
        valider_personne_vivant_seule_2025(
            _profil(**{champ: False})
        )


def test_source_obligatoire():
    with pytest.raises(ValueError, match="source"):
        valider_personne_vivant_seule_2025(
            _profil(source=" ")
        )


@pytest.mark.parametrize("mois", [-1, 13])
def test_mois_allocation_famille_hors_limites_refuse(mois):
    with pytest.raises(ValueError, match="compris entre 0 et 12"):
        valider_personne_vivant_seule_2025(
            _profil(mois_allocation_famille_2025=mois)
        )


def test_mois_allocation_famille_doit_etre_entier():
    with pytest.raises(ValueError, match="entier"):
        valider_personne_vivant_seule_2025(
            _profil(mois_allocation_famille_2025=1.5)
        )


def test_montant_base_sans_reduction_au_seuil():
    profil = _profil(revenu_familial_net=Decimal("42090"))
    assert (
        montant_ligne_361_personne_vivant_seule_2025(profil)
        == Decimal("2128.00")
    )


def test_reduction_au_dessus_du_seuil():
    profil = _profil(revenu_familial_net=Decimal("52000"))
    assert (
        montant_ligne_361_personne_vivant_seule_2025(profil)
        == Decimal("269.87")
    )
    assert (
        credit_quebec_personne_vivant_seule_2025(profil)
        == Decimal("37.78")
    )


def test_montant_ne_devient_jamais_negatif():
    profil = _profil(revenu_familial_net=Decimal("100000"))
    assert montant_ligne_361_personne_vivant_seule_2025(profil) == 0


def test_additionnel_monoparental_complet():
    profil = _profil(
        reclamer_additionnel_monoparental=True,
        enfant_majeur_etudes_admissible=True,
        aucun_droit_allocation_famille_decembre=True,
        mois_allocation_famille_2025=0,
    )
    assert (
        montant_additionnel_monoparental_2025(profil)
        == Decimal("2627.00")
    )


def test_additionnel_monoparental_reduit_par_mois():
    profil = _profil(
        reclamer_additionnel_monoparental=True,
        enfant_majeur_etudes_admissible=True,
        aucun_droit_allocation_famille_decembre=True,
        mois_allocation_famille_2025=5,
    )
    assert (
        montant_additionnel_monoparental_2025(profil)
        == Decimal("1532.40")
    )


def test_additionnel_exige_enfant_majeur_etudes():
    with pytest.raises(ValueError, match="enfant majeur"):
        valider_personne_vivant_seule_2025(
            _profil(
                reclamer_additionnel_monoparental=True,
                enfant_majeur_etudes_admissible=False,
                aucun_droit_allocation_famille_decembre=True,
            )
        )


def test_additionnel_exige_absence_allocation_decembre():
    with pytest.raises(ValueError, match="décembre"):
        valider_personne_vivant_seule_2025(
            _profil(
                reclamer_additionnel_monoparental=True,
                enfant_majeur_etudes_admissible=True,
                aucun_droit_allocation_famille_decembre=False,
            )
        )


def test_additionnel_refuse_12_mois_allocation_famille():
    with pytest.raises(ValueError, match="12 mois"):
        valider_personne_vivant_seule_2025(
            _profil(
                reclamer_additionnel_monoparental=True,
                enfant_majeur_etudes_admissible=True,
                aucun_droit_allocation_famille_decembre=True,
                mois_allocation_famille_2025=12,
            )
        )


def test_ligne_361_avec_additionnel_et_reduction_revenu():
    profil = _profil(
        revenu_familial_net=Decimal("52000"),
        reclamer_additionnel_monoparental=True,
        enfant_majeur_etudes_admissible=True,
        aucun_droit_allocation_famille_decembre=True,
        mois_allocation_famille_2025=0,
    )
    assert (
        montant_ligne_361_personne_vivant_seule_2025(profil)
        == Decimal("2896.87")
    )
    assert (
        credit_quebec_personne_vivant_seule_2025(profil)
        == Decimal("405.56")
    )


def test_application_credit_reduit_impot_quebec():
    profil = _profil(revenu_familial_net=Decimal("42090"))
    resultat = appliquer_credit_quebec_personne_vivant_seule_2025(
        _impot(),
        profil,
    )

    assert resultat.impot_quebec_preliminaire == Decimal("3102.14")
    assert (
        "Montant Québec pour personne vivant seule inclus à la ligne 361."
        in resultat.limitations
    )


def test_application_credit_ne_rend_pas_impot_negatif():
    petit_impot = replace_impot = _impot()
    petit_impot = ImpotQuebecPreliminaire2025(
        client=replace_impot.client,
        annee_fiscale=replace_impot.annee_fiscale,
        province=replace_impot.province,
        revenu_imposable=replace_impot.revenu_imposable,
        impot_brut=replace_impot.impot_brut,
        montant_personnel_base=replace_impot.montant_personnel_base,
        taux_credit_personnel=replace_impot.taux_credit_personnel,
        credit_personnel_base=replace_impot.credit_personnel_base,
        impot_quebec_preliminaire=Decimal("50"),
        limitations=replace_impot.limitations,
    )
    profil = _profil(revenu_familial_net=Decimal("42090"))

    resultat = appliquer_credit_quebec_personne_vivant_seule_2025(
        petit_impot,
        profil,
    )
    assert resultat.impot_quebec_preliminaire == Decimal("0")
