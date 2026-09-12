from pathlib import Path


GUI = Path("src/comptaprivee/gui.py")


def _source():
    return GUI.read_text(encoding="utf-8")


def test_gui_importe_credit_deficience():
    texte = _source()
    assert "from .tax_disability_2025 import (" in texte
    assert "CreditDeficience2025" in texte
    assert "valider_credit_deficience_2025" in texte


def test_gui_initialise_credit_deficience():
    texte = _source()
    assert texte.count(
        "credit_deficience_courant = CreditDeficience2025()"
    ) >= 2


def test_gui_dialogue_et_bouton_deficience():
    texte = _source()
    assert "def ouvrir_credit_deficience_2025()" in texte
    assert 'text="Handicap / déficience 2025"' in texte
    assert "command=ouvrir_credit_deficience_2025" in texte


def test_gui_affiche_lignes_et_montants():
    texte = _source()
    assert "ligne 31600" in texte
    assert "10 138 $" in texte
    assert "ligne 376" in texte
    assert "4 123 $" in texte


def test_gui_controle_ciph_et_attestation():
    texte = _source()
    assert "CIPH / T2201 approuvé par l'ARC" in texte
    assert "Attestation professionnelle Québec confirmée" in texte
    assert "aucun_transfert_federal" in texte


def test_gui_construit_et_valide_credit():
    texte = _source()
    assert "nouveau_credit = CreditDeficience2025(" in texte
    assert "nouveau_credit = valider_credit_deficience_2025(" in texte


def test_gui_recharge_credit_deficience():
    texte = _source()
    assert "credit_deficience_courant = (" in texte
    assert "enregistrement.credit_deficience" in texte


def test_gui_relit_credit_dans_calcul_et_stockage():
    texte = _source()
    assert texte.count(
        "credit_deficience=credit_deficience_courant,"
    ) >= 3
