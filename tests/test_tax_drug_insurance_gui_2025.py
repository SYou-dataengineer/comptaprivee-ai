from pathlib import Path


GUI = Path("src/comptaprivee/gui.py")


def _source():
    return GUI.read_text(encoding="utf-8")


def test_gui_importe_assurance_medicaments():
    texte = _source()
    assert "from .tax_drug_insurance_2025 import (" in texte
    assert "AssuranceMedicamentsQuebec2025" in texte
    assert "valider_assurance_medicaments_2025" in texte


def test_gui_initialise_assurance_medicaments():
    texte = _source()
    assert texte.count(
        "assurance_medicaments_courante = "
        "AssuranceMedicamentsQuebec2025()"
    ) >= 2


def test_gui_dialogue_et_bouton_assurance():
    texte = _source()
    assert "def ouvrir_assurance_medicaments_2025()" in texte
    assert 'text="Assurance médicaments 2025"' in texte
    assert "command=ouvrir_assurance_medicaments_2025" in texte


def test_gui_affiche_lignes_et_seuils_ramq():
    texte = _source()
    assert "ligne 275" in texte
    assert "ligne 48" in texte
    assert "ligne 447" in texte
    assert "19 890 $" in texte
    assert "8 181 $" in texte
    assert "755 $" in texte


def test_gui_controle_case_449_et_ramq():
    texte = _source()
    assert 'values=("", "14", "16", "32")' in texte
    assert "carte RAMQ 2025 confirmée" in texte
    assert "Aucun cas particulier de l'annexe K" in texte


def test_gui_construit_et_valide_assurance():
    texte = _source()
    assert "AssuranceMedicamentsQuebec2025(" in texte
    assert "valider_assurance_medicaments_2025(" in texte


def test_gui_recharge_assurance_medicaments():
    texte = _source()
    assert "assurance_medicaments_courante = (" in texte
    assert "enregistrement.assurance_medicaments" in texte


def test_gui_relit_assurance_dans_calcul_et_stockage():
    texte = _source()
    assert texte.count(
        "assurance_medicaments=assurance_medicaments_courante,"
    ) == 3
