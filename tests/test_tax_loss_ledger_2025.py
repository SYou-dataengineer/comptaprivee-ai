"""7F : faits fictifs; conservation des soldes, plafonds et demandes distinctes."""
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal as D
import json
import pytest

from src.comptaprivee.tax_loss_ledger_2025 import (
    CapaciteReport2025, DemandePerte2025, PerteNonCapital2025,
    PerteNetteCapital2025, RegistrePertes2025, preparer_pertes_2025,
    registre_pertes_depuis_json, registre_pertes_vers_json,
    lignes_preparation_pertes_2025,
)


def perte(capital=False, **kw):
    classe = PerteNetteCapital2025 if capital else PerteNonCapital2025
    valeurs = dict(juridiction='federal', annee_origine=2024, disponible=D('1000'),
        source='Avis et registre fictifs, rapprochement exhaustif',
        historique_confirme=True, exclusions_absentes=True, solde_fiscal_confirme=True,
        demandes=(DemandePerte2025('courant', 2025, D('400')),))
    valeurs.update(kw)
    return classe(**valeurs)


def capacite(**kw):
    valeurs = dict(juridiction='federal', annee_visee=2025,
        revenu_imposable_disponible=D('5000'), gains_imposables_disponibles=D('1500'),
        source='Déclaration fictive et rapprochement des utilisations',
        autres_pertes_appliquees=True, historique_confirme=True,
        sans_rajustement_annexe_n=True, exclusions_absentes=True)
    valeurs.update(kw)
    return CapaciteReport2025(**valeurs)


def registre(p=None, c=None):
    p = p or perte()
    nom = 'pertes_net_capital' if isinstance(p, PerteNetteCapital2025) else 'pertes_non_capital'
    return RegistrePertes2025(**{nom: (p,)}, capacites=(c or capacite(juridiction=p.juridiction),))


@pytest.mark.parametrize('capital', [False, True])
@pytest.mark.parametrize('juridiction', ['federal', 'quebec'])
def test_courant_partiel_et_recalcul_idempotent(capital, juridiction):
    r = registre(perte(capital, juridiction=juridiction))
    avant = registre_pertes_vers_json(r)
    resultat = preparer_pertes_2025(r)
    s, = resultat.soldes
    assert (s.disponible, s.demande, s.restant) == (D('1000'), D('400'), D('600'))
    assert s.derniere_annee_future == (None if capital else 2044)
    assert resultat.deduction('net_capital' if capital else 'non_capital', juridiction) == D('400')
    assert preparer_pertes_2025(r) == resultat
    assert registre_pertes_vers_json(r) == avant


@pytest.mark.parametrize('capital', [False, True])
@pytest.mark.parametrize('juridiction', ['federal', 'quebec'])
@pytest.mark.parametrize('annee', [2022, 2023, 2024])
def test_reports_arriere_sans_modification_de_la_capacite(capital, juridiction, annee):
    p = perte(capital, juridiction=juridiction, annee_origine=2025,
        demandes=(DemandePerte2025('arriere', annee, D('600')),))
    c = capacite(juridiction=juridiction, annee_visee=annee)
    r = registre(p, c)
    resultat = preparer_pertes_2025(r)
    u, = resultat.utilisations
    assert u.annee_visee == annee and u.solde_apres_demande == D('400')
    assert u.formulaire == ('T1A 2025' if juridiction == 'federal' else 'TP-1012.A (2025-10)')
    assert resultat.deduction('net_capital' if capital else 'non_capital', juridiction) == 0
    assert r.capacites == (c,) and c.revenu_imposable_disponible == D('5000')
    assert 'Demande de report rétrospectif préparée' in '\n'.join(lignes_preparation_pertes_2025(r))


def test_trois_reports_partagent_un_seul_solde():
    p = perte(annee_origine=2025, demandes=tuple(
        DemandePerte2025('arriere', annee, D(montant))
        for annee, montant in ((2024, '300'), (2022, '100'), (2023, '200'))))
    r = RegistrePertes2025((p,), capacites=tuple(capacite(annee_visee=y) for y in (2022, 2023, 2024)))
    x = preparer_pertes_2025(r)
    assert [u.solde_apres_demande for u in x.utilisations] == [D('900'), D('700'), D('400')]
    assert x.soldes[0].restant == D('400')


@pytest.mark.parametrize('capital', [False, True])
def test_futur_sans_consommer_et_sans_capacite(capital):
    p = perte(capital, annee_origine=2025, demandes=())
    r = replace(registre(p), capacites=())
    x = preparer_pertes_2025(r)
    assert x.utilisations == ()
    assert x.soldes[0].restant == D('1000')
    assert x.soldes[0].derniere_annee_future == (None if capital else 2045)


@pytest.mark.parametrize('capital', [False, True])
@pytest.mark.parametrize('valeur', [D('NaN'), D('sNaN'), D('Infinity'), D('-Infinity'), D('-1'), D('.001'), 1.0, '1', True])
def test_montants_invalides(capital, valeur):
    with pytest.raises(ValueError, match='Decimal'):
        preparer_pertes_2025(registre(perte(capital, disponible=valeur)))


@pytest.mark.parametrize('champ', ['historique_confirme', 'exclusions_absentes', 'solde_fiscal_confirme'])
@pytest.mark.parametrize('valeur', [False, 1, 'oui'])
def test_confirmations_strictes(champ, valeur):
    with pytest.raises(ValueError, match='confirmation'):
        preparer_pertes_2025(registre(perte(**{champ: valeur})))


@pytest.mark.parametrize('demande', [
    DemandePerte2025('courant', 2024, D('1')),
    DemandePerte2025('arriere', 2021, D('1')),
    DemandePerte2025('arriere', 2024, D('1')),
    DemandePerte2025('futur', 2026, D('1')),
    DemandePerte2025('courant', 2025, D('0')),
    DemandePerte2025('courant', 2025, D('1000.01')),
])
def test_demande_invalide(demande):
    with pytest.raises(ValueError):
        preparer_pertes_2025(registre(perte(demandes=(demande,))))


def test_exces_total_sur_plusieurs_reports_refuse():
    p = perte(annee_origine=2025, demandes=tuple(DemandePerte2025('arriere', y, D('400')) for y in (2022, 2023, 2024)))
    with pytest.raises(ValueError, match='solde disponible'):
        preparer_pertes_2025(registre(p))


def test_perte_capital_interdite_sur_revenu_ordinaire():
    with pytest.raises(ValueError, match='revenu ordinaire interdit'):
        preparer_pertes_2025(registre(perte(True), capacite(gains_imposables_disponibles=D('0'))))


def test_deux_natures_ne_peuvent_pas_consommer_deux_fois_imposable():
    r = RegistrePertes2025((perte(),), (perte(True),), (capacite(revenu_imposable_disponible=D('700')),))
    with pytest.raises(ValueError, match='demandes combinées'):
        preparer_pertes_2025(r)


def test_soldes_arc_rq_independants():
    r = RegistrePertes2025((perte(), perte(juridiction='quebec', disponible=D('800'))),
        capacites=(capacite(), capacite(juridiction='quebec')))
    assert [s.restant for s in preparer_pertes_2025(r).soldes] == [D('600'), D('400')]


def test_duplique_et_types_melanges_refuses():
    for r in (RegistrePertes2025((perte(), perte())), RegistrePertes2025((perte(True),))):
        with pytest.raises(ValueError):
            preparer_pertes_2025(r)


@pytest.mark.parametrize('capital', [False, True])
def test_ordre_chronologique_par_nature(capital):
    nom = 'pertes_net_capital' if capital else 'pertes_non_capital'
    r = RegistrePertes2025(**{nom: (perte(capital), perte(capital, annee_origine=2020, demandes=()))}, capacites=(capacite(),))
    with pytest.raises(ValueError, match='plus ancienne'):
        preparer_pertes_2025(r)
    anciens = (perte(capital, annee_origine=2020, disponible=D('100'), demandes=(DemandePerte2025('courant', 2025, D('100')),)), perte(capital))
    assert len(preparer_pertes_2025(replace(r, **{nom: anciens})).soldes) == 2


def test_annexe_n_historique_non_verifiee_refusee():
    with pytest.raises(ValueError, match='annexe N'):
        preparer_pertes_2025(registre(perte(juridiction='quebec'),
            capacite(juridiction='quebec', sans_rajustement_annexe_n=False)))


def test_capacite_et_preuves_requises():
    with pytest.raises(ValueError, match='capacité documentée'):
        preparer_pertes_2025(replace(registre(), capacites=()))
    with pytest.raises(ValueError, match='source documentaire'):
        preparer_pertes_2025(registre(perte(source=' ')))


def test_json_retrocompatible_et_aller_retour(tmp_path):
    assert registre_pertes_depuis_json(None) == registre_pertes_depuis_json({}) == RegistrePertes2025()
    r = RegistrePertes2025((perte(),), (perte(True),), (capacite(),))
    chemin = tmp_path / 'registre_fictif.json'
    chemin.write_text(json.dumps(registre_pertes_vers_json(r)), encoding='utf-8')
    recharge = registre_pertes_depuis_json(json.loads(chemin.read_text(encoding='utf-8')))
    assert recharge == r
    assert preparer_pertes_2025(recharge) == preparer_pertes_2025(r)
    assert isinstance(recharge.pertes_non_capital[0].disponible, D)
    with pytest.raises(FrozenInstanceError):
        recharge.pertes_non_capital[0].disponible = D('0')


@pytest.mark.parametrize('v', [[], {'inconnu': 1}, {'pertes_non_capital': None}, {'capacites': [{}]},
    {'pertes_non_capital': [{'disponible': 100}]}, {'pertes_non_capital': [{'disponible': 'NaN'}]}])
def test_json_corrompu_refuse(v):
    with pytest.raises(ValueError):
        registre_pertes_depuis_json(v)


def test_aucun_revenu_historique_dans_resultat_et_pas_acceptation_fiscale():
    texte = '\n'.join(lignes_preparation_pertes_2025(registre()))
    assert 'ni considérées comme acceptées' in texte
    assert 'aucun revenu net historique' in texte
    assert 'intégration annuelle requise' in texte
    assert 'aucun effet automatique' in texte


@pytest.mark.parametrize('annee,accepte', [(2005,False),(2006,True),(2024,True),(2026,False)])
def test_limites_origine_non_capital(annee, accepte):
    r = registre(perte(annee_origine=annee, demandes=()))
    if accepte:
        assert preparer_pertes_2025(r).soldes[0].derniere_annee_future == annee + 20
    else:
        with pytest.raises(ValueError):preparer_pertes_2025(r)


@pytest.mark.parametrize('taux', [D('sNaN'),D('NaN'),D('Infinity'),D('.6667'),0.5])
def test_taux_historique_non_supporte(taux):
    with pytest.raises(ValueError):
        preparer_pertes_2025(registre(perte(True,taux_inclusion=taux)))
