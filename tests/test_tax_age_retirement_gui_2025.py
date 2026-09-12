from pathlib import Path


GUI = Path("src/comptaprivee/gui.py")


def _source():
    return GUI.read_text(encoding="utf-8")


def test_gui_importe_age_retraite():
    texte = _source()
    assert "from .tax_age_retirement_2025 import (" in texte
    assert "MontantsAgeRetraite2025" in texte
    assert "valider_montants_age_retraite_2025" in texte


def test_gui_initialise_age_retraite():
    texte = _source()
    assert texte.count(
        "montants_age_retraite_courants = "
        "MontantsAgeRetraite2025()"
    ) >= 2


def test_gui_dialogue_et_bouton_age_retraite():
    texte = _source()
    assert "def ouvrir_age_retraite_2025()" in texte
    assert 'text="Âge / retraite 2025"' in texte
    assert "command=ouvrir_age_retraite_2025" in texte


def test_gui_affiche_regles_age_retraite():
    texte = _source()
    for terme in (
        "Annexe B / ligne 361",
        "3 906 $",
        "3 470 $",
        "1,25",
        "42 090 $",
        "18,75 %",
        "14 %",
    ):
        assert terme in texte


def test_gui_saisit_champs_age_retraite():
    texte = _source()
    for terme in (
        "Né avant le 1er janvier 1961",
        "ligne 122",
        "ligne 123",
        "ligne 250 point 4",
        "ligne 250 point 6",
        "ligne 293",
        "ligne 297 points 9 à 12",
        "ligne 245",
        "Revenu familial net 2025",
        "Aucun conjoint au 31 décembre 2025",
        "Aucun montant pour personne vivant seule combiné",
        "PSV, RRQ et RPC exclus des revenus admissibles",
        "Situation validée par le comptable",
    ):
        assert terme in texte


def test_gui_construit_et_valide_age_retraite():
    texte = _source()
    assert "MontantsAgeRetraite2025(" in texte
    assert "valider_montants_age_retraite_2025(" in texte


def test_gui_bloque_combinaison_personne_vivant_seule():
    texte = _source()
    assert "personne_vivant_seule_courante.reclamer_montant" in texte
    assert "même réduction de l'annexe B" in texte


def test_gui_recharge_age_retraite():
    texte = _source()
    assert "montants_age_retraite_courants = (" in texte
    assert "enregistrement.montants_age_retraite" in texte


def test_gui_relit_age_retraite_dans_calcul_et_stockage():
    texte = _source()
    assert texte.count(
        "montants_age_retraite=montants_age_retraite_courants,"
    ) == 3
