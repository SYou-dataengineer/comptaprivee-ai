from pathlib import Path

GUI = Path("src/comptaprivee/gui.py")


def _source():
    return GUI.read_text(encoding="utf-8")


def test_gui_importe_30425():
    t = _source()
    assert "from .tax_federal_caregiver_spouse_dependant_2025 import (" in t
    assert "AidantNaturelConjointOuPersonneChargeFederal2025" in t
    assert "TYPE_CONJOINT" in t
    assert "TYPE_PERSONNE_CHARGE_ADMISSIBLE" in t
    assert "valider_aidant_naturel_30425_2025" in t


def test_gui_initialise_30425():
    t = _source()
    assert t.count(
        "aidant_30425_federal_courant = "
        "AidantNaturelConjointOuPersonneChargeFederal2025()"
    ) >= 2


def test_gui_dialogue_et_bouton_30425():
    t = _source()
    assert "def ouvrir_aidant_30425_federal_2025()" in t
    assert 'text="Aidant 30425 fédéral 2025"' in t
    assert "command=ouvrir_aidant_30425_federal_2025" in t


def test_gui_relit_30300_et_30400():
    t = _source()
    assert "montant_ligne_30300_2025(" in t
    assert "montant_ligne_30400_2025(" in t
    assert "revenu_net_conjoint_2025" in t
    assert "revenu_net_personne_charge_2025" in t
    assert "La ligne 30300 doit être active" in t
    assert "La ligne 30400 doit être active" in t


def test_gui_affiche_regles_30425():
    t = _source()
    for terme in (
        "ligne 30425",
        "Infirmité physique ou mentale confirmée",
        "Dépendance due uniquement à l'infirmité",
        "Dépendance pendant une période considérable",
        "Un seul réclamant pour la ligne 30425",
        "Aucune réclamation partagée",
        "Preuve médicale admissible ou T2201 approuvé confirmé",
        "Validation comptable confirmée",
        "ligne 34990",
    ):
        assert terme in t


def test_gui_construit_et_valide_30425():
    t = _source()
    assert "AidantNaturelConjointOuPersonneChargeFederal2025(" in t
    assert "valider_aidant_naturel_30425_2025(" in t
    assert "montant_base_2687_inclus=base_2687" in t


def test_gui_recharge_30425():
    t = _source()
    assert "aidant_30425_federal_courant = (" in t
    assert "enregistrement.aidant_conjoint_personne_charge_federal" in t


def test_gui_relit_30425_calcul_et_stockage():
    t = _source()
    assert t.count(
        "aidant_conjoint_personne_charge_federal="
        "aidant_30425_federal_courant,"
    ) >= 3
