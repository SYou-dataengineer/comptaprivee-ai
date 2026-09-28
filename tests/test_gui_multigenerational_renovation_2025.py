from dataclasses import fields
import pytest

from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from tests.test_tax_multigenerational_renovation_2025 import renovation, depense
from src.comptaprivee.tax_multigenerational_renovation_2025 import CONFIRMATIONS_RENOVATION

BOUTON = "Rénovations multigénérationnelles 2025 (5Q)"


def ouvrir(app):
    app.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(app)
    bouton(fiscal, BOUTON).invoke()
    return fiscal, derniere_fenetre(fiscal)


def remplir(d, objet):
    for f in fields(objet):
        if f.name in ("depenses", "autres_demandes") or f.name in CONFIRMATIONS_RENOVATION:
            continue
        valeur = getattr(objet, f.name)
        w = champ(d, f.name + "_5q")
        if f.type is bool:
            if bool(d.getvar(w.cget("variable"))) != valeur:
                w.invoke()
        elif f.name in ("role_demandeur", "lien_proche"):
            w.set(valeur)
        else:
            _remplir(w, str(valeur))


def confirmer(d):
    for n in CONFIRMATIONS_RENOVATION:
        w = champ(d, n + "_5q")
        if not d.getvar(w.cget("variable")):
            w.invoke()


def ajouter_projet(d):
    bouton(d, "Ajouter — Projets").invoke()
    projet = derniere_fenetre(d)
    remplir(projet, renovation())
    bouton(projet, "Ajouter — Dépenses").invoke()
    piece = derniere_fenetre(projet)
    remplir(piece, depense())
    bouton(piece, "Enregistrer").invoke()
    confirmer(projet)
    bouton(projet, "Enregistrer le projet").invoke()
    assert not projet.winfo_exists()


def test_ajouter_reouvrir_modifier_annuler_et_effacer(application):
    fiscal, d = ouvrir(application)
    ajouter_projet(d)
    for n in ("resident_annee_complete", "profil_ordinaire"):
        champ(d, n + "_5q").invoke()
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    bouton(fiscal, BOUTON).invoke()
    d = derniere_fenetre(fiscal)
    assert champ(d, "renovations_5q").get_children() == ("0",)
    champ(d, "renovations_5q").selection_set("0")
    bouton(d, "Modifier — Projets").invoke()
    projet = derniere_fenetre(d)
    assert all(projet.getvar(champ(projet, n + "_5q").cget("variable")) for n in CONFIRMATIONS_RENOVATION)
    _remplir(champ(projet, "source_5q"), "Nouvelle source")
    assert all(not projet.getvar(champ(projet, n + "_5q").cget("variable")) for n in CONFIRMATIONS_RENOVATION)
    bouton(projet, "Enregistrer le projet").invoke()
    assert projet.winfo_exists()
    bouton(projet, "Annuler").invoke()
    bouton(d, "Modifier — Projets").invoke()
    projet = derniere_fenetre(d)
    assert champ(projet, "source_5q").get() == renovation().source
    champ(projet, "depenses_5q").selection_set("0")
    bouton(projet, "Modifier — Dépenses").invoke()
    piece = derniere_fenetre(projet)
    _remplir(champ(piece, "montant_5q"), "20000")
    bouton(piece, "Enregistrer").invoke()
    assert all(not projet.getvar(champ(projet, n + "_5q").cget("variable")) for n in CONFIRMATIONS_RENOVATION)
    confirmer(projet)
    bouton(projet, "Enregistrer le projet").invoke()
    assert not d.getvar(champ(d, "resident_annee_complete_5q").cget("variable"))
    for n in ("resident_annee_complete", "profil_ordinaire"):
        champ(d, n + "_5q").invoke()
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists()
    bouton(fiscal, BOUTON).invoke()
    d = derniere_fenetre(fiscal)
    bouton(d, "Effacer le profil").invoke()
    bouton(fiscal, BOUTON).invoke()
    d = derniere_fenetre(fiscal)
    assert not champ(d, "renovations_5q").get_children()
    bouton(d, "Fermer").invoke()
    fiscal.destroy()


@pytest.mark.parametrize("montant", ["NaN", "Infinity", "-1", "0", "1.001", "texte"])
def test_montant_invalide(application, montant):
    fiscal, d = ouvrir(application)
    bouton(d, "Ajouter — Projets").invoke()
    projet = derniere_fenetre(d)
    bouton(projet, "Ajouter — Dépenses").invoke()
    piece = derniere_fenetre(projet)
    remplir(piece, depense())
    _remplir(champ(piece, "montant_5q"), montant)
    bouton(piece, "Enregistrer").invoke()
    assert piece.winfo_exists()
    assert not champ(projet, "depenses_5q").get_children()
    assert application.messages_test[-1][0] == "Saisie invalide"
    bouton(piece, "Annuler").invoke()
    bouton(projet, "Annuler").invoke()
    bouton(d, "Fermer").invoke()
    fiscal.destroy()


def test_partage_et_retrait(application):
    fiscal, d = ouvrir(application)
    ajouter_projet(d)
    champ(d, "renovations_5q").selection_set("0")
    bouton(d, "Modifier — Projets").invoke()
    projet = derniere_fenetre(d)
    bouton(projet, "Ajouter — Autres demandeurs").invoke()
    partage = derniere_fenetre(projet)
    for n, v in {"personne": "Autre personne", "base_reclamee": "50001", "source": "Accord synthétique"}.items():
        _remplir(champ(partage, n + "_5q"), v)
    bouton(partage, "Enregistrer").invoke()
    confirmer(projet)
    bouton(projet, "Enregistrer le projet").invoke()
    assert projet.winfo_exists()
    champ(projet, "autres_demandes_5q").selection_set("0")
    bouton(projet, "Modifier — Autres demandeurs").invoke()
    partage = derniere_fenetre(projet)
    _remplir(champ(partage, "base_reclamee_5q"), "20000")
    bouton(partage, "Enregistrer").invoke()
    confirmer(projet)
    bouton(projet, "Enregistrer le projet").invoke()
    assert not projet.winfo_exists()
    champ(d, "renovations_5q").selection_set("0")
    bouton(d, "Retirer — Projets").invoke()
    assert not champ(d, "renovations_5q").get_children()
    bouton(d, "Fermer").invoke()
    fiscal.destroy()


def test_confirmations_lisibles_dans_la_fenetre(application):
    fiscal, d = ouvrir(application)
    bouton(d, "Ajouter — Projets").invoke()
    projet = derniere_fenetre(d)
    projet.update_idletasks()
    for n in CONFIRMATIONS_RENOVATION:
        assert champ(projet, n + "_5q").winfo_reqwidth() <= 980
    bouton(projet, "Annuler").invoke()
    bouton(d, "Fermer").invoke()
    fiscal.destroy()
