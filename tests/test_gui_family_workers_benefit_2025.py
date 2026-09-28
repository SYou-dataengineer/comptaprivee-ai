import pytest
from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from tests.test_gui_workers_benefit_2025 import ouvrir
from src.comptaprivee.tax_workers_benefit_2025 import CONFIRMATIONS_ACT
from src.comptaprivee.tax_family_workers_benefit_2025 import CONFIRMATIONS_FAMILLE_ACT


def cocher(d, nom):
    w = champ(d, nom)
    if not d.getvar(w.cget("variable")):
        w.invoke()


def confirmer(d):
    for nom in CONFIRMATIONS_ACT:
        if nom != "sans_conjoint_ni_personne_charge":
            cocher(d, nom+"_5e")
    for nom in CONFIRMATIONS_FAMILLE_ACT:
        cocher(d, nom+"_5u")


def remplir(d):
    _remplir(champ(d, "age_fin_2025_5e"), "35")
    _remplir(champ(d, "source_5e"), "RC210 et dossier synthétiques")
    cocher(d, "reclamer_base_5e")
    cocher(d, "activer_5u")
    _remplir(champ(d, "conjoint_nom_5u"), "Conjoint fictif")
    cocher(d, "conjoint_resident_5u")
    _remplir(champ(d, "conjoint_revenu_travail_5u"), "8000")
    _remplir(champ(d, "conjoint_revenu_net_5u"), "7000,25")
    _remplir(champ(d, "source_5u"), "Revenus et attribution validés")
    confirmer(d)


def test_famille_reouverture_et_effacement(application):
    fiscal, d = ouvrir(application)
    remplir(d)
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    bouton(fiscal, "Allocation travailleurs 2025 (5E)").invoke()
    d = derniere_fenetre(fiscal)
    assert champ(d, "conjoint_nom_5u").get() == "Conjoint fictif"
    assert champ(d, "conjoint_revenu_net_5u").get() == "7000.25"
    assert d.getvar(champ(d, "activer_5u").cget("variable")) == 1
    bouton(d, "Effacer").invoke()
    assert champ(d, "conjoint_nom_5u").get() == ""
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    fiscal.destroy()


@pytest.mark.parametrize("nom", ["conjoint_nom", "conjoint_revenu_travail", "conjoint_revenu_net", "conjoint_avances_base", "source", "conjoint_ciph", "conjoint_resident"])
def test_modification_revoque_confirmations(application, nom):
    fiscal, d = ouvrir(application)
    remplir(d)
    w = champ(d, nom+"_5u")
    if nom in ("conjoint_ciph", "conjoint_resident"):
        w.invoke()
    else:
        _remplir(w, "100")
    for n in CONFIRMATIONS_ACT:
        assert d.getvar(champ(d, n+"_5e").cget("variable")) == 0
    for n in CONFIRMATIONS_FAMILLE_ACT:
        assert d.getvar(champ(d, n+"_5u").cget("variable")) == 0
    bouton(d, "Fermer").invoke()
    fiscal.destroy()


@pytest.mark.parametrize("valeur", ["NaN", "Infinity", "-1", "0.001", "texte"])
def test_revenu_travail_invalide(application, valeur):
    fiscal, d = ouvrir(application)
    remplir(d)
    _remplir(champ(d, "conjoint_revenu_travail_5u"), valeur)
    confirmer(d)
    bouton(d, "Valider et appliquer").invoke()
    assert d.winfo_exists() and application.messages_test
    bouton(d, "Fermer").invoke()
    fiscal.destroy()


def test_enfant_naissance_revoque_admissibilite(application):
    fiscal, d = ouvrir(application)
    remplir(d)
    _remplir(champ(d, "enfant_nom_5u"), "Enfant fictif")
    _remplir(champ(d, "enfant_naissance_5u"), "2015-01-01")
    cocher(d, "enfant_admissible_confirme_5u")
    confirmer(d)
    _remplir(champ(d, "enfant_naissance_5u"), "2016-01-01")
    assert d.getvar(champ(d, "enfant_admissible_confirme_5u").cget("variable")) == 0
    bouton(d, "Fermer").invoke()
    fiscal.destroy()


def test_conjoint_etudiant_enfant_distinct_persiste_et_revoque(application):
    fiscal, d = ouvrir(application)
    remplir(d)
    cocher(d, "conjoint_etudiant_5u")
    _remplir(champ(d, "conjoint_enfant_nom_5u"), "Enfant du conjoint")
    _remplir(champ(d, "conjoint_enfant_naissance_5u"), "2015-01-01")
    cocher(d, "conjoint_enfant_admissible_confirme_5u")
    confirmer(d)
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    bouton(fiscal, "Allocation travailleurs 2025 (5E)").invoke()
    d = derniere_fenetre(fiscal)
    assert champ(d, "conjoint_enfant_nom_5u").get() == "Enfant du conjoint"
    _remplir(champ(d, "conjoint_enfant_naissance_5u"), "2016-01-01")
    assert d.getvar(champ(d, "conjoint_enfant_admissible_confirme_5u").cget("variable")) == 0
    assert d.getvar(champ(d, "attribution_unique_5u").cget("variable")) == 0
    bouton(d, "Fermer").invoke()
    fiscal.destroy()
