from pathlib import Path

GUI = Path("src/comptaprivee/gui.py")


def _source():
    return GUI.read_text(encoding="utf-8")


def test_gui_importe_aidant_enfant():
    t = _source()
    assert "from .tax_federal_caregiver_child_2025 import (" in t
    assert "AidantNaturelEnfantMoins18Federal2025" in t
    assert "valider_aidant_naturel_enfant_moins18_federal_2025" in t


def test_gui_initialise_aidant_enfant():
    t = _source()
    assert t.count(
        "aidant_enfant_federal_courant = "
        "AidantNaturelEnfantMoins18Federal2025()"
    ) >= 2


def test_gui_dialogue_et_bouton():
    t = _source()
    assert "def ouvrir_aidant_naturel_enfant_federal_2025()" in t
    assert 'text="Aidant enfant fédéral 2025"' in t
    assert "command=ouvrir_aidant_naturel_enfant_federal_2025" in t


def test_gui_regles_30499_30500():
    t = _source()
    for terme in (
        "lignes 30499 / 30500",
        "2 687 $",
        "14,5 %",
        "Enfant de moins de 18 ans à la fin de 2025",
        "Infirmité physique ou mentale confirmée",
        "Besoin de beaucoup plus d'aide que les enfants du même âge",
        "Aucune garde partagée",
        "Aucune pension alimentaire",
        "Aucun autre réclamant pour la ligne 30500",
        "Aucun transfert au conjoint — ligne 32600",
        "Preuve médicale admissible ou T2201 approuvé confirmé",
        "Validation comptable confirmée",
        "ligne 34990",
        "ligne 30400 + ligne 30500",
    ):
        assert terme in t


def test_gui_construit_et_valide():
    t = _source()
    assert "AidantNaturelEnfantMoins18Federal2025(" in t
    assert "valider_aidant_naturel_enfant_moins18_federal_2025(" in t


def test_gui_recharge_aidant_enfant():
    t = _source()
    assert (
        "aidant_enfant_federal_courant = "
        "enregistrement.aidant_enfant_federal"
    ) in t


def test_gui_relit_dans_calcul_et_stockage():
    t = _source()
    assert t.count(
        "aidant_enfant_federal=aidant_enfant_federal_courant,"
    ) >= 3
