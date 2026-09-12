from pathlib import Path


GUI = Path("src/comptaprivee/gui.py")


def _source():
    return GUI.read_text(encoding="utf-8")


def test_gui_importe_age_pension_federal():
    texte = _source()
    assert "from .tax_federal_age_pension_2025 import (" in texte
    assert "CreditsFederauxAgePension2025" in texte
    assert "valider_credits_federaux_age_pension_2025" in texte


def test_gui_initialise_age_pension_federal():
    texte = _source()
    assert texte.count(
        "credits_federaux_age_pension_courants = "
        "CreditsFederauxAgePension2025()"
    ) >= 2


def test_gui_dialogue_et_bouton_age_pension_federal():
    texte = _source()
    assert "def ouvrir_age_pension_federal_2025()" in texte
    assert 'text="Âge / pension fédéral 2025"' in texte
    assert "command=ouvrir_age_pension_federal_2025" in texte


def test_gui_affiche_regles_age_pension_federal():
    texte = _source()
    for terme in (
        "ligne 30100",
        "9 028 $",
        "45 522 $",
        "105 709 $",
        "15 %",
        "14,5 %",
        "ligne 31400",
        "2 000 $",
        "ligne 34990",
    ):
        assert terme in texte


def test_gui_saisit_champs_age_pension_federal():
    texte = _source()
    for terme in (
        "65 ans ou plus au 31 décembre 2025",
        "Revenu net fédéral — ligne 23600",
        "Source confirmant l'âge",
        "Revenu de pension admissible",
        "Admissibilité du revenu de pension confirmée",
        "Résident du Canada toute l'année 2025",
        "Aucun fractionnement de pension T1032",
        "Aucun transfert de crédits entre conjoints",
        "Situation validée par le comptable",
    ):
        assert terme in texte


def test_gui_construit_et_valide_age_pension_federal():
    texte = _source()
    assert "CreditsFederauxAgePension2025(" in texte
    assert "valider_credits_federaux_age_pension_2025(" in texte
    assert "La ligne 31400 est préparée" in texte


def test_gui_recharge_age_pension_federal():
    texte = _source()
    assert "credits_federaux_age_pension_courants = (" in texte
    assert "enregistrement.credits_federaux_age_pension" in texte


def test_gui_relit_age_pension_dans_calcul_et_stockage():
    texte = _source()
    assert texte.count(
        "credits_federaux_age_pension="
        "credits_federaux_age_pension_courants,"
    ) == 3
