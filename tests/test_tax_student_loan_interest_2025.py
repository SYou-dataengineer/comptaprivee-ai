from dataclasses import replace
from decimal import Decimal as D

import pytest

from src.comptaprivee.tax_student_loan_interest_2025 import (
    CONFIRMATIONS_5B, InteretsPretEtudiant2025, repartir_interets_pret_etudiant_2025,
    valider_interets_pret_etudiant_2025,
)


def profil(**modifications):
    valeurs = dict(interets_payes_2025=D("1000"), montant_reclame_31900=D("1000"),
                   source="Relevé gouvernemental 2025 et historique vérifiés",
                   **{nom: True for nom in CONFIRMATIONS_5B})
    valeurs.update(modifications)
    return InteretsPretEtudiant2025(**valeurs)


def test_vide_sans_confirmations():
    p = InteretsPretEtudiant2025()
    assert valider_interets_pret_etudiant_2025(p) == p
    assert repartir_interets_pret_etudiant_2025(p).total_disponible == 0


@pytest.mark.parametrize("payeur", ["contribuable", "parent apparenté"])
def test_interets_payes_par_emprunteur_ou_personne_apparentee(payeur):
    p = profil(source=f"Paiement documenté par {payeur}, emprunteur légal confirmé")
    r = repartir_interets_pret_etudiant_2025(p)
    assert r.ligne_31900 == D("1000")
    assert r.utilises_par_annee == ((2025, D("1000")),)
    assert r.non_reclames_par_annee == ()


@pytest.mark.parametrize("nom", list(CONFIRMATIONS_5B))
def test_exclusions_et_confirmations_obligatoires(nom):
    with pytest.raises(ValueError, match="Confirmation obligatoire"):
        valider_interets_pret_etudiant_2025(profil(**{nom: False}))
    with pytest.raises(ValueError, match="booléenne"):
        valider_interets_pret_etudiant_2025(profil(**{nom: "true"}))


@pytest.mark.parametrize("montant", [D("-1"), D("NaN"), D("sNaN"), D("Infinity"), D("-Infinity"), "100", 1.5])
@pytest.mark.parametrize("champ", ["interets_payes_2025", "montant_reclame_31900", "reports"])
def test_montants_invalides(montant, champ):
    valeur = ((2024, montant),) if champ == "reports" else montant
    with pytest.raises(ValueError):
        valider_interets_pret_etudiant_2025(profil(**{champ: valeur}))


@pytest.mark.parametrize("source", ["", "  ", None])
def test_source_absente(source):
    with pytest.raises(ValueError):
        valider_interets_pret_etudiant_2025(profil(source=source))


@pytest.mark.parametrize("annee", [2019, 2025, 2026, "2020", True])
def test_report_hors_fenetre(annee):
    with pytest.raises(ValueError, match="fenêtre"):
        valider_interets_pret_etudiant_2025(profil(reports=((annee, D(10)),)))


@pytest.mark.parametrize("annee", [2020, 2021, 2022, 2023, 2024])
def test_chaque_annee_admissible(annee):
    r = repartir_interets_pret_etudiant_2025(profil(interets_payes_2025=D(0), reports=((annee, D(100)),), montant_reclame_31900=D(60)))
    assert r.utilises_par_annee == ((annee, D(60)),)
    assert r.non_reclames_par_annee == ((annee, D(40)),)
    assert r.non_reclame_2020_expirant == (D(40) if annee == 2020 else D(0))
    assert r.non_reclames_encore_reportables_2026 == (D(0) if annee == 2020 else D(40))


def test_ordre_ancien_recent_et_ouverture_immuable():
    p = profil(reports=((2024, D(400)), (2020, D(200)), (2022, D(300))), montant_reclame_31900=D(650))
    r = repartir_interets_pret_etudiant_2025(p)
    assert r.utilises_par_annee == ((2020, D(200)), (2022, D(300)), (2024, D(150)))
    assert r.non_reclames_par_annee == ((2024, D(250)), (2025, D(1000)))
    assert p.reports[0] == (2024, D(400))
    assert r.total_disponible == r.ligne_31900 + sum(m for _, m in r.non_reclames_par_annee)


def test_pas_de_reclamation_automatique_et_aucun_plafond_fixe():
    p = profil(interets_payes_2025=D("1000000"), montant_reclame_31900=D(0), reports=((2020, D(100)),))
    r = repartir_interets_pret_etudiant_2025(p)
    assert r.utilises_par_annee == ()
    assert r.non_reclames_par_annee == ((2020, D(100)), (2025, D(1000000)))
    assert repartir_interets_pret_etudiant_2025(replace(p, montant_reclame_31900=D(1000100))).ligne_31900 == D(1000100)


def test_reclamation_superieure_et_report_duplique_refuses():
    with pytest.raises(ValueError, match="dépasse"):
        valider_interets_pret_etudiant_2025(profil(montant_reclame_31900=D(1001)))
    with pytest.raises(ValueError, match="dupliquée"):
        valider_interets_pret_etudiant_2025(profil(reports=((2020, D(1)), (2020, D(1)))))


def test_arrondi_decimal_au_cent():
    p = valider_interets_pret_etudiant_2025(profil(interets_payes_2025=D("1000.005"), montant_reclame_31900=D("1000.005")))
    assert p.interets_payes_2025 == p.montant_reclame_31900 == D("1000.01")
