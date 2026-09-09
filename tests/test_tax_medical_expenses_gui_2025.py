from pathlib import Path


GUI = Path("src/comptaprivee/gui.py")


def _source():
    return GUI.read_text(encoding="utf-8")


def test_gui_importe_frais_medicaux():
    texte = _source()
    assert "from .tax_medical_expenses_2025 import (" in texte
    assert "FraisMedicaux2025" in texte
    assert "valider_frais_medicaux_2025" in texte


def test_gui_initialise_frais_medicaux():
    texte = _source()
    assert texte.count(
        "frais_medicaux_courants = FraisMedicaux2025()"
    ) >= 2


def test_gui_offre_bouton_frais_medicaux():
    texte = _source()
    assert 'text="Frais médicaux 2025"' in texte
    assert "command=ouvrir_frais_medicaux_2025" in texte


def test_gui_fenetre_medicale_a_les_confirmations():
    texte = _source()
    assert "Reçus et pièces justificatives confirmés" in texte
    assert "Remboursements reçus ou à recevoir déjà soustraits" in texte
    assert "Période de 12 mois se terminant en 2025 confirmée" in texte
    assert "Profil individuel sans conjoint ni personne à charge" in texte


def test_gui_valide_frais_medicaux():
    texte = _source()
    assert "nouveaux_frais = FraisMedicaux2025(" in texte
    assert "nouveaux_frais = valider_frais_medicaux_2025(" in texte


def test_gui_recharge_frais_medicaux():
    texte = _source()
    assert "enregistrement.frais_medicaux" in texte


def test_gui_transmet_frais_aux_calculs():
    texte = _source()
    assert texte.count(
        "frais_medicaux=frais_medicaux_courants,"
    ) >= 3


def test_gui_sauvegarde_frais_medicaux():
    texte = _source()
    assert "sauvegarder_dossier_fiscal(" in texte
    assert "frais_medicaux=frais_medicaux_courants," in texte


def test_gui_recalcul_secours_conserve_dons():
    texte = _source()
    assert texte.count(
        "dons_bienfaisance=dons_bienfaisance_courants,"
    ) >= 2
    assert "dons_bienfaisance=(" in texte
