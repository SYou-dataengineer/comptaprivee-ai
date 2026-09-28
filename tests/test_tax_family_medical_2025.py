from dataclasses import replace
from decimal import Decimal as D
import pytest

from src.comptaprivee.tax_family_medical_2025 import (
    PersonneFraisMedicaux2025 as Personne,
    DepenseMedicaleFamiliale2025 as Depense,
    FraisMedicauxFamilleFederaux2025 as Profil,
    CONFIRMATIONS_MEDICALES_FAMILLE,
    calculer_medical_familial_2025 as calculer,
)


def personne(**kw):
    v = dict(reference="parent", nom="Parent synthétique", naissance="1960-01-01", lien="parent",
        resident_canada_dans_annee=True, revenu_net_23600=D(20000), source_revenu="Déclaration validée",
        source_lien_dependance="Lien et soutien établis")
    v.update(kw)
    return Personne(**v)


def depense(**kw):
    v = dict(reference="Reçu A", personne="parent", date_paiement="2025-03-01", description="Soins admissibles",
             montant_paye=D(2000), source="Reçu synthétique")
    v.update(kw)
    return Depense(**v)


def profil(**kw):
    v = dict(demandeur="Client", debut_periode="2024-07-01", fin_periode="2025-06-30",
             personnes=(personne(),), depenses=(depense(),), **{k: True for k in CONFIRMATIONS_MEDICALES_FAMILLE})
    v.update(kw)
    return Profil(**v)


def resultat(p=None, revenu=D(42000)):
    return calculer(p or profil(), demandeur="Client", revenu_net=revenu)


def test_seuil_propre_33199_et_vide():
    r = resultat()
    assert r.ligne_33099 == 0 and r.ligne_33199 == r.ligne_33200 == D(1400)
    assert r.personnes[0].seuil == D(600)
    assert resultat(Profil()).ligne_33200 == 0


@pytest.mark.parametrize("revenu,seuil", [("0", "0"), ("-100", "0"), ("10000", "300"), ("100000", "2834")])
def test_bornes_revenu_propre(revenu, seuil):
    r = resultat(profil(personnes=(personne(revenu_net_23600=D(revenu)),), depenses=(depense(montant_paye=D(5000)),)))
    assert r.personnes[0].seuil == D(seuil)
    assert r.ligne_33199 == D(5000) - D(seuil)


def test_exemple_arc_groupe_33099_et_enfant_adulte():
    personnes = tuple(personne(reference=ref, nom=nom, naissance=naissance, lien=lien,
        revenu_net_23600=D(0), source_revenu="") for ref, nom, naissance, lien in (
        ("soi", "Client", "1980-01-01", "soi-même"),
        ("conjoint", "Conjointe", "1980-01-01", "conjoint"),
        ("enfant", "Enfant", "2009-01-01", "enfant")))
    personnes += (personne(reference="adulte", nom="Enfant adulte", naissance="2006-01-01", lien="enfant", revenu_net_23600=D(10000)),)
    depenses = tuple(depense(reference=str(i), personne=ref, montant_paye=D(m)) for i, (ref, m) in enumerate(
        (("soi", 2500), ("conjoint", 2000), ("enfant", 1800), ("adulte", 1300))))
    r = resultat(profil(personnes=personnes, depenses=depenses))
    assert r.ligne_33099 == 6300 and r.net_33099 == 5040
    assert r.ligne_33199 == 1000 and r.ligne_33200 == 6040


def test_remboursement_imposable_et_part_externe():
    r = resultat(profil(depenses=(depense(remboursements=D(500), remboursements_imposables_non_deduits=D(100), part_reclamee_ailleurs=D(300)),)))
    assert r.personnes[0].frais_nets == 1300 and r.ligne_33199 == 700


@pytest.mark.parametrize("champ", CONFIRMATIONS_MEDICALES_FAMILLE)
@pytest.mark.parametrize("valeur", [False, 1, "oui"])
def test_confirmations_strictes(champ, valeur):
    with pytest.raises(ValueError):
        resultat(replace(profil(), **{champ: valeur}))


@pytest.mark.parametrize("champ", ["montant_paye", "remboursements", "remboursements_imposables_non_deduits", "part_reclamee_ailleurs"])
@pytest.mark.parametrize("valeur", [D("NaN"), D("Infinity"), D(-1), D(".001"), True, "10"])
def test_montants_stricts(champ, valeur):
    with pytest.raises(ValueError):
        resultat(profil(depenses=(replace(depense(), **{champ: valeur}),)))


@pytest.mark.parametrize("kw", [{"debut_periode": "2024-06-30"}, {"fin_periode": "2026-01-01"},
    {"demandeur": "Autre"}, {"personnes": []}, {"personnes": (personne(), personne())},
    {"depenses": (depense(), depense())}, {"depenses": (depense(date_paiement="2025-07-01"),)},
    {"personnes": (personne(resident_canada_dans_annee=False),)}])
def test_contradictions(kw):
    with pytest.raises(ValueError):
        resultat(profil(**kw))


def test_petit_enfant_mineur_est_33199():
    p = personne(lien="petit-enfant", naissance="2020-01-01", resident_canada_dans_annee=False)
    assert resultat(profil(personnes=(p,))).personnes[0].ligne == "33199"


def test_demandeur_ne_peut_pas_utiliser_un_seuil_de_dependant():
    with pytest.raises(ValueError, match="propre"):
        resultat(profil(personnes=(personne(nom="Client"),)))


@pytest.mark.parametrize("personnes", [(), (personne(),)])
def test_profil_partiellement_vide_refuse(personnes):
    with pytest.raises(ValueError, match="incomplet"):
        resultat(profil(personnes=personnes, depenses=()))
