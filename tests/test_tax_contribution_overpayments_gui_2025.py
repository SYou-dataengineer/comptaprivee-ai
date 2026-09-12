from pathlib import Path


GUI = Path("src/comptaprivee/gui.py")


def _source():
    return GUI.read_text(encoding="utf-8")


def test_gui_importe_cotisations_excedentaires():
    texte = _source()
    assert "from .tax_contribution_overpayments_2025 import (" in texte
    assert "CotisationsExcedentaires2025" in texte
    assert "valider_cotisations_excedentaires_2025" in texte


def test_gui_initialise_cotisations_excedentaires():
    texte = _source()
    assert texte.count(
        "cotisations_excedentaires_courantes = "
        "CotisationsExcedentaires2025()"
    ) >= 2


def test_gui_dialogue_et_bouton():
    texte = _source()
    assert "def ouvrir_cotisations_excedentaires_2025()" in texte
    assert 'text="Cotisations excédentaires 2025"' in texte
    assert "command=ouvrir_cotisations_excedentaires_2025" in texte


def test_gui_affiche_trois_lignes_remboursement():
    texte = _source()
    assert "ligne Québec 452" in texte
    assert "ligne fédérale 45000" in texte
    assert "ligne Québec 457" in texte


def test_gui_saisit_montants_et_gains():
    texte = _source()
    for terme in (
        "RRQ B.A payé",
        "RRQ B.B payé",
        "Gains admissibles RRQ",
        "Assurance-emploi payée",
        "Gains assurables AE",
        "RQAP payé",
        "Revenus assujettis RQAP",
    ):
        assert terme in texte


def test_gui_controle_profil_simple():
    texte = _source()
    assert "Résident du Québec au 31 décembre 2025" in texte
    assert "RRQ uniquement, sans RPC" in texte
    assert "Aucun travail autonome" in texte
    assert "Profil RRQ standard 18 à 64 ans toute l'année" in texte


def test_gui_construit_et_valide_profil():
    texte = _source()
    assert "CotisationsExcedentaires2025(" in texte
    assert "valider_cotisations_excedentaires_2025(" in texte


def test_gui_recharge_cotisations_excedentaires():
    texte = _source()
    assert "cotisations_excedentaires_courantes = (" in texte
    assert "enregistrement.cotisations_excedentaires" in texte


def test_gui_relit_dans_calcul_et_stockage():
    texte = _source()
    assert texte.count(
        "cotisations_excedentaires="
        "cotisations_excedentaires_courantes,"
    ) == 3
