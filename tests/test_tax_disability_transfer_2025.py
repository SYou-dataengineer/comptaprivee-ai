from decimal import Decimal as D
import pytest
from src.comptaprivee.tax_disability_transfer_2025 import calculer_disponible_handicap_2025


def calcul(**kw):
    valeurs = dict(montant_31600=D(10138), impot_brut=D(2900),
                   montants_par_ligne=(("30000", D(16129)),))
    valeurs.update(kw)
    return calculer_disponible_handicap_2025(**valeurs)


def test_credit_unused_apres_personnel_uniquement():
    r = calcul()
    assert r.credits_avant_handicap == D("2338.71")
    assert r.impot_avant_handicap == D("561.29")
    assert r.credit_handicap == D("1470.01")
    assert r.credit_disponible == D("908.72")
    assert r.base_disponible == D("6267.03")


def test_pas_de_transfert_cree_par_credits_exclus():
    lignes = (("30000", D(16129)), ("31600", D(10138)), ("32300", D(5000)),
              ("33200", D(5000)), ("34900", D(1000)), ("40500", D(1000)),
              ("41000", D(650)), ("41400", D(750)))
    assert calcul(montants_par_ligne=lignes) == calcul()


def test_aucun_impot_et_plafond_handicap():
    r = calcul(impot_brut=D(0), montant_31600=D(16052))
    assert r.base_disponible == D(16052)
    assert r.credit_disponible == D("2327.54")
    assert calcul(impot_brut=D(10000)).base_disponible == 0


def test_ajouts_partie_i_et_compensatoire_recalcule():
    assert calcul(ajouts_impot_partie_i=D(100)).credit_disponible == D("808.72")
    r = calcul(impot_brut=D("12957.50"), montants_par_ligne=(("30000", D(16129)), ("31300", D(68871))))
    assert r.base_ligne_102 == D(85000)
    assert r.credits_avant_handicap == D(12325)
    assert r.compensatoire_avant_handicap == D("138.19")
    assert r.impot_avant_handicap == D("494.31")
    assert r.credit_disponible == D("975.70")


def test_audit_divergence_feuille_31800_et_impot_hypothetique():
    """Rapprochement explicite : les deux expressions ne sont pas équivalentes.

    Feuille ARC 5000-D1 E (25), page 6, lignes 8 à 13 :
    min(31600, max(31600 + base102 - revenu26000, 0)).
    Le calcul retenu selon 118.3(2)d) donne une autre base hors première tranche.
    """
    revenu = D(80000)
    base102 = D(85000)
    handicap = D(10138)
    brut = (D(57375) * D("0.145") + (revenu - D(57375)) * D("0.205"))
    assert brut == D("12957.50")
    feuille = min(handicap, max(handicap + base102 - revenu, D(0)))
    r = calcul(impot_brut=brut, montants_par_ligne=(("30000", D(16129)), ("31300", D(68871))))
    assert feuille == D(10138)
    assert r.base_disponible == D("6728.97")
    assert feuille - r.base_disponible == D("3409.03")


def test_audit_arrondi_base_premiere_tranche():
    # La feuille donne 6267, alors que la conversion du crédit arrondi
    # donne 6267,03. Le crédit arrondi est identique dans cet exemple.
    from src.comptaprivee.tax_rules_2025 import arrondir_cent
    feuille = D(10138) + D(16129) - D(20000)
    r = calcul()
    assert feuille == D(6267)
    assert r.base_disponible == D("6267.03")
    assert arrondir_cent(feuille * D("0.145")) == r.credit_disponible


@pytest.mark.parametrize("nom", ["montant_31600", "impot_brut", "ajouts_impot_partie_i"])
@pytest.mark.parametrize("v", [D("NaN"), D("sNaN"), D("Infinity"), D(-1), D("1.001"), True, "10"])
def test_montants_invalides(nom, v):
    with pytest.raises(ValueError):
        calcul(**{nom: v})


@pytest.mark.parametrize("lignes", [[], (("30000", D(1)), ("30000", D(2))), (("30000", D("NaN")),), (1,)])
def test_lignes_invalides(lignes):
    with pytest.raises(ValueError):
        calcul(montants_par_ligne=lignes)


from dataclasses import replace
import json
from src.comptaprivee.tax_disability_transfer_2025 import (
    TransfertsHandicap2025, TransfertHandicapDependant2025, PartHandicapAutreSoutien2025,
    CONFIRMATIONS_HANDICAP_TRANSFERE, calculer_transferts_handicap_2025,
    instantane_donneur_handicap_2025, valider_transferts_handicap_2025,
    transferts_handicap_vers_dict, transferts_handicap_depuis_dict,
)


@pytest.fixture
def transfert(tmp_path):
    from tests.test_tax_interest_income_2025 import dossier_interets, profil_interets
    from tests.test_tax_disability_minor_2025 import mineur
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
    from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal
    dossier = replace(dossier_interets("10000"), client="Enfant synthétique")
    e = calculer_estimation_fiscale_2025(dossier, profil_interets=profil_interets(), credit_deficience=mineur())
    f = sauvegarder_dossier_fiscal(dossier, estimation=e, profil_interets=profil_interets(), destination=tmp_path / "donneur.json")
    texte = instantane_donneur_handicap_2025(json.loads(f.read_text(encoding="utf-8")))
    return TransfertHandicapDependant2025(reference="Personne A", nom_donneur="Enfant synthétique",
        naissance="2010-02-03", lien="enfant", condition="30450 admissible sans revenu ni condition d'âge du donneur",
        dossier_donneur_json=texte, source="T2201 et autorisation synthétiques", rapprochement_30400_30450="Dépendance documentée",
        **{n: True for n in CONFIRMATIONS_HANDICAP_TRANSFERE})


def ensemble(t):
    return TransfertsHandicap2025("Client Test", (t,))


def resultat(t, **kw):
    return calculer_transferts_handicap_2025(ensemble(t), beneficiaire="Client Test", **kw)


def test_donneur_recalcule_mineur_et_partage(transfert):
    r = resultat(transfert)
    assert r.ligne_31800 == D(16052)
    assert r.donneurs[0].revenu_imposable == D(10000)
    assert r.donneurs[0].calcul.credit_disponible == D("2327.54")
    t = replace(transfert, autres_parts=(PartHandicapAutreSoutien2025("Autre parent", D(6052), "Accord"),))
    assert resultat(t).ligne_31800 == D(10000)
    assert resultat(replace(t, limiter_demande=True, part_demandee=D(8000))).ligne_31800 == D(8000)
    assert resultat(replace(t, limiter_demande=True)).ligne_31800 == 0


@pytest.mark.parametrize("champ", CONFIRMATIONS_HANDICAP_TRANSFERE)
@pytest.mark.parametrize("valeur", [False, "oui", 1])
def test_admissibilite_explicitement_validee(transfert, champ, valeur):
    with pytest.raises(ValueError):
        resultat(replace(transfert, **{champ: valeur}))


@pytest.mark.parametrize("kw", [
    {"nom_donneur": "Client Test"}, {"reference": ""}, {"nom_donneur": "Autre personne"},
    {"lien": "conjoint"}, {"condition": "au choix"}, {"naissance": "2011-02-03"},
    {"naissance": "20100203"}, {"naissance": "2026-01-01"},
    {"source": ""}, {"rapprochement_30400_30450": ""},
    {"conjoint_donneur_reclame": True}, {"autre_personne_reclame_30400": True},
    {"situation_pension": "paiement sans exception"},
    {"situation_pension": "obligations réciproques avec accord"},
    {"part_demandee": D(100)}, {"limiter_demande": True, "part_demandee": D(16053)},
    {"autres_parts": []}, {"lien_avec_conjoint": 1},
])
def test_donnees_et_exclusions(transfert, kw):
    with pytest.raises(ValueError):
        resultat(replace(transfert, **kw))


def test_30400_exclusivite_et_ligne_effective(transfert):
    t = replace(transfert, condition="30400 réclamé")
    assert resultat(t, reclame_30400=True).ligne_31800 == D(16052)
    with pytest.raises(ValueError, match="absente"):
        resultat(t, reclame_30400=False)
    with pytest.raises(ValueError, match="seule"):
        resultat(replace(t, autres_parts=(PartHandicapAutreSoutien2025("Autre soutien", D(1), "Accord"),)))


def test_exceptions_alimentaires(transfert):
    t = replace(transfert, situation_pension="séparation partielle sans déduction 22000", source_pension="Période et jugement")
    assert resultat(t).ligne_31800 == D(16052)
    with pytest.raises(ValueError, match="22000"):
        resultat(t, deduction_22000=D(1))
    t = replace(t, situation_pension="obligations réciproques avec accord")
    assert resultat(t, deduction_22000=D(100)).ligne_31800 == D(16052)


@pytest.mark.parametrize("montant", [D("NaN"), D("Infinity"), D(-1), D("0.001"), D(16053)])
def test_autres_parts_invalides(transfert, montant):
    with pytest.raises(ValueError):
        resultat(replace(transfert, autres_parts=(PartHandicapAutreSoutien2025("Autre parent", montant, "Accord"),)))


def test_profil_vide_identites_et_doublons(transfert):
    assert calculer_transferts_handicap_2025(TransfertsHandicap2025(), beneficiaire="X", annee=2024).ligne_31800 == 0
    with pytest.raises(ValueError):
        calculer_transferts_handicap_2025(ensemble(transfert), beneficiaire="Autre client")
    with pytest.raises(ValueError):
        calculer_transferts_handicap_2025(ensemble(transfert), beneficiaire="Client Test", annee=2024)
    with pytest.raises(ValueError, match="dupliqué"):
        valider_transferts_handicap_2025(TransfertsHandicap2025("Client Test", (transfert, transfert)))


def test_rejet_imbrication_et_resultats_derives(transfert):
    for cle, v in (("transferts_handicap", {"transferts": [{}]}),
                   ("transfert_conjoint", {"activer": True}), ("derniere_estimation", {}), ("rapport_pdf", "x.pdf")):
        brut = json.loads(transfert.dossier_donneur_json)
        brut[cle] = v
        with pytest.raises(ValueError):
            resultat(replace(transfert, dossier_donneur_json=json.dumps(brut)))


def test_roundtrip_brut_et_legacy(transfert):
    p = ensemble(transfert)
    brut = transferts_handicap_vers_dict(p)
    assert transferts_handicap_depuis_dict(brut) == p
    assert transferts_handicap_depuis_dict(None) == TransfertsHandicap2025()
    assert "credit_disponible" not in json.dumps(brut)
    brut["transferts"][0]["inconnue"] = 1
    with pytest.raises(ValueError):
        transferts_handicap_depuis_dict(brut)


@pytest.mark.parametrize("v", ["NaN", "sNaN", "Infinity", "-1", "1.001", True, 1.0, None])
def test_json_montant_invalide(transfert, v):
    brut = transferts_handicap_vers_dict(ensemble(transfert))
    brut["transferts"][0]["part_demandee"] = v
    with pytest.raises(ValueError):
        transferts_handicap_depuis_dict(brut)
