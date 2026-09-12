from pathlib import Path


GUI = Path("src/comptaprivee/gui.py")


def _source():
    return GUI.read_text(encoding="utf-8")


def test_gui_importe_personne_vivant_seule():
    texte = _source()
    assert "from .tax_living_alone_2025 import (" in texte
    assert "PersonneVivantSeule2025" in texte
    assert "valider_personne_vivant_seule_2025" in texte


def test_gui_initialise_personne_vivant_seule():
    texte = _source()
    assert texte.count(
        "personne_vivant_seule_courante = "
        "PersonneVivantSeule2025()"
    ) >= 2


def test_gui_dialogue_et_bouton():
    texte = _source()
    assert "def ouvrir_personne_vivant_seule_2025()" in texte
    assert 'text="Personne vivant seule 2025"' in texte
    assert "command=ouvrir_personne_vivant_seule_2025" in texte


def test_gui_affiche_regles_principales():
    texte = _source()
    for terme in (
        "Annexe B / ligne 361",
        "2 128 $",
        "2 627 $",
        "218,92 $",
        "42 090 $",
        "18,75 %",
        "14 %",
    ):
        assert terme in texte


def test_gui_saisit_conditions_profil_simple():
    texte = _source()
    for terme in (
        "Revenu familial net 2025",
        "Aucun conjoint au 31 décembre 2025",
        "Résident du Québec et du Canada toute l'année 2025",
        "Aucun montant pour âge ou revenus de retraite combiné",
        "Documents justificatifs confirmés",
        "Situation validée par le comptable",
    ):
        assert terme in texte


def test_gui_saisit_additionnel_monoparental():
    texte = _source()
    assert "famille monoparentale" in texte
    assert "Enfant majeur aux études admissible confirmé" in texte
    assert "Allocation famille pour décembre 2025" in texte
    assert "Nombre de mois d'Allocation famille reçus en 2025" in texte


def test_gui_construit_et_valide_profil():
    texte = _source()
    assert "PersonneVivantSeule2025(" in texte
    assert "valider_personne_vivant_seule_2025(" in texte


def test_gui_recharge_personne_vivant_seule():
    texte = _source()
    assert "personne_vivant_seule_courante = (" in texte
    assert "enregistrement.personne_vivant_seule" in texte


def test_gui_relit_dans_calcul_et_stockage():
    texte = _source()
    assert texte.count(
        "personne_vivant_seule=personne_vivant_seule_courante,"
    ) == 3
