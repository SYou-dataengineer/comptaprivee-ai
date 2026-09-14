from pathlib import Path

GUI = Path("src/comptaprivee/gui.py")


def _source():
    return GUI.read_text(encoding="utf-8")


def test_gui_importe_31270():
    t = _source()
    assert "from .tax_federal_home_buyers_2025 import (" in t
    assert "MontantAchatHabitationFederal2025" in t
    assert "valider_montant_achat_habitation_2025" in t


def test_gui_initialise_31270():
    t = _source()
    assert t.count(
        "achat_habitation_federal_courant = "
        "MontantAchatHabitationFederal2025()"
    ) >= 2


def test_gui_dialogue_et_bouton_31270():
    t = _source()
    assert "def ouvrir_achat_habitation_federal_2025() -> None:" in t
    assert 'text="Achat habitation 31270"' in t
    assert "command=ouvrir_achat_habitation_federal_2025" in t


def test_gui_affiche_regles_31270():
    t = _source()
    for terme in (
        "ligne fédérale 31270",
        "maximum 10 000 $",
        "crédit fédéral 14,5 %",
        "Acquisition de l'habitation en 2025",
        "Habitation admissible",
        "Habitation située au Canada",
        "Première habitation",
        "quatre années précédentes",
        "résidence ",
        "principale dans un an",
        "Aucun partage du montant ligne 31270",
        "Exception handicap non utilisée",
        "Pièces justificatives",
        "Validation comptable confirmée",
        "ligne 34990",
    ):
        assert terme in t


def test_gui_construit_et_valide_31270():
    t = _source()
    assert "MontantAchatHabitationFederal2025(" in t
    assert "valider_montant_achat_habitation_2025(" in t
    assert "montant_reclame=montant" in t
    assert "source_habitation=source_var.get().strip()" in t


def test_gui_recharge_31270():
    t = _source()
    assert "achat_habitation_federal_courant = (" in t
    assert "enregistrement.achat_habitation_federal" in t


def test_gui_relit_31270_calcul_et_stockage():
    t = _source()
    assert t.count(
        "achat_habitation_federal=achat_habitation_federal_courant,"
    ) >= 3


def test_gui_invalide_estimation_apres_modification_31270():
    t = _source()
    bloc = t[
        t.index("def ouvrir_achat_habitation_federal_2025")
        :t.index("def ouvrir_aidant_30450_federal_2025")
    ]
    assert "derniere_estimation = None" in bloc
    assert "dernier_rapport_pdf = None" in bloc
