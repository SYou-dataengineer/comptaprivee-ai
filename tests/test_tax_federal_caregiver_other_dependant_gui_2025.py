from pathlib import Path

GUI = Path("src/comptaprivee/gui.py")


def _source():
    return GUI.read_text(encoding="utf-8")


def test_gui_importe_30450():
    t = _source()
    assert "from .tax_federal_caregiver_other_dependant_2025 import (" in t
    assert "AidantNaturelAutrePersonneChargeFederal2025" in t
    assert "LIENS_AUTORISES" in t
    assert "valider_aidant_naturel_30450_2025" in t


def test_gui_initialise_30450():
    t = _source()
    assert t.count(
        "aidant_30450_federal_courant = "
        "AidantNaturelAutrePersonneChargeFederal2025()"
    ) >= 2


def test_gui_dialogue_et_bouton_30450():
    t = _source()
    assert "def ouvrir_aidant_30450_federal_2025()" in t
    assert 'text="Aidant 30450 fédéral 2025"' in t
    assert "command=ouvrir_aidant_30450_federal_2025" in t


def test_gui_affiche_regles_30450():
    t = _source()
    for terme in (
        "ligne 30450",
        "ligne 51120",
        "28 798 $",
        "8 601 $",
        "18 ans ou plus",
        "Infirmité physique ou mentale confirmée",
        "Dépendance due à l'infirmité",
        "Dépendance pendant une période considérable",
        "Aucun montant ligne 30300/30400",
        "Aucune pension alimentaire",
        "Aucun partage de la réclamation 30450",
        "Preuve médicale admissible ou T2201 approuvé confirmé",
        "Validation comptable confirmée",
        "ligne 34990",
    ):
        assert terme in t


def test_gui_construit_et_valide_30450():
    t = _source()
    assert "AidantNaturelAutrePersonneChargeFederal2025(" in t
    assert "valider_aidant_naturel_30450_2025(" in t
    assert "revenu_net_personne_ligne_23600=" in t
    assert "lien_personne=" in t


def test_gui_recharge_30450():
    t = _source()
    assert "aidant_30450_federal_courant = (" in t
    assert "enregistrement.aidant_autre_personne_charge_federal" in t


def test_gui_relit_30450_calcul_et_stockage():
    t = _source()
    assert t.count(
        "aidant_autre_personne_charge_federal="
        "aidant_30450_federal_courant,"
    ) >= 3
