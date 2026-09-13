from pathlib import Path


GUI = Path("src/comptaprivee/gui.py")


def _source():
    return GUI.read_text(encoding="utf-8")


def test_gui_importe_montant_conjoint_federal():
    texte = _source()
    assert "from .tax_federal_spouse_2025 import (" in texte
    assert "MontantConjointFederal2025" in texte
    assert "valider_montant_conjoint_federal_2025" in texte


def test_gui_initialise_montant_conjoint_federal():
    texte = _source()
    assert texte.count(
        "montant_conjoint_federal_courant = "
        "MontantConjointFederal2025()"
    ) >= 2


def test_gui_dialogue_et_bouton_montant_conjoint():
    texte = _source()
    assert "def ouvrir_montant_conjoint_federal_2025()" in texte
    assert 'text="Conjoint fédéral 2025"' in texte
    assert "command=ouvrir_montant_conjoint_federal_2025" in texte


def test_gui_affiche_regles_montant_conjoint():
    texte = _source()
    for terme in (
        "ligne 30300",
        "ligne 23600",
        "Revenu net du conjoint",
        "Même conjoint toute l'année 2025",
        "Aucune séparation ou réconciliation en 2025",
        "Conjoint résident du Canada toute l'année 2025",
        "Aucun paiement de pension alimentaire",
        "Aucune déficience physique ou mentale du conjoint",
        "Un seul conjoint réclame le montant",
        "Revenu net du conjoint confirmé",
        "Validation comptable confirmée",
        "14,5 %",
        "ligne 34990",
    ):
        assert terme in texte


def test_gui_construit_et_valide_montant_conjoint():
    texte = _source()
    assert "MontantConjointFederal2025(" in texte
    assert "valider_montant_conjoint_federal_2025(" in texte


def test_gui_recharge_montant_conjoint():
    texte = _source()
    assert "montant_conjoint_federal_courant = (" in texte
    assert "enregistrement.montant_conjoint_federal" in texte


def test_gui_relit_montant_conjoint_dans_calcul_et_stockage():
    texte = _source()
    assert texte.count(
        "montant_conjoint_federal=montant_conjoint_federal_courant,"
    ) >= 3
