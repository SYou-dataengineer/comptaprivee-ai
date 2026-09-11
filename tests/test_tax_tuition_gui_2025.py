from pathlib import Path

GUI = Path("src/comptaprivee/gui.py")


def _source():
    return GUI.read_text(encoding="utf-8")


def test_gui_importe_scolarite():
    texte = _source()
    assert "from .tax_tuition_2025 import (" in texte
    assert "FraisScolarite2025" in texte
    assert "valider_frais_scolarite_2025" in texte


def test_gui_initialise_scolarite():
    texte = _source()
    assert texte.count(
        "frais_scolarite_courants = FraisScolarite2025()"
    ) >= 2


def test_gui_offre_bouton_scolarite():
    texte = _source()
    assert 'text="Frais de scolarité 2025"' in texte
    assert "command=ouvrir_frais_scolarite_2025" in texte


def test_gui_fenetre_scolarite_a_les_confirmations():
    texte = _source()
    assert "Pièce fédérale admissible confirmée" in texte
    assert "Reçu officiel Québec confirmé" in texte
    assert "Seuil de plus de 100 $ confirmé" in texte
    assert "Aucun report antérieur" in texte
    assert "Aucun transfert à une autre personne" in texte
    assert "Crédit canadien pour la formation non réclamé" in texte


def test_gui_valide_scolarite():
    texte = _source()
    assert "nouveaux_frais = FraisScolarite2025(" in texte
    assert "nouveaux_frais = valider_frais_scolarite_2025(" in texte


def test_gui_recharge_scolarite():
    texte = _source()
    assert "enregistrement.frais_scolarite" in texte


def test_gui_transmet_scolarite_aux_calculs():
    texte = _source()
    assert texte.count(
        "frais_scolarite=frais_scolarite_courants,"
    ) >= 3


def test_gui_sauvegarde_scolarite():
    texte = _source()
    assert "sauvegarder_dossier_fiscal(" in texte
    assert "frais_scolarite=frais_scolarite_courants," in texte
