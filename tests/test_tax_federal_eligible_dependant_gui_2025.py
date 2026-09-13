from pathlib import Path


GUI = Path("src/comptaprivee/gui.py")


def _source():
    return GUI.read_text(encoding="utf-8")


def test_gui_importe_personne_charge_admissible():
    texte = _source()
    assert "from .tax_federal_eligible_dependant_2025 import (" in texte
    assert "MontantPersonneChargeAdmissibleFederal2025" in texte
    assert (
        "valider_montant_personne_charge_admissible_federal_2025"
        in texte
    )


def test_gui_initialise_personne_charge_admissible():
    texte = _source()
    assert texte.count(
        "personne_charge_admissible_federale_courante = "
        "MontantPersonneChargeAdmissibleFederal2025()"
    ) >= 2


def test_gui_dialogue_et_bouton_personne_charge():
    texte = _source()
    assert (
        "def ouvrir_personne_charge_admissible_federale_2025()"
        in texte
    )
    assert 'text="Personne à charge fédérale 2025"' in texte
    assert (
        "command=ouvrir_personne_charge_admissible_federale_2025"
        in texte
    )


def test_gui_affiche_regles_ligne_30400():
    texte = _source()
    for terme in (
        "ligne 30400",
        "ligne 23600",
        "Revenu net de la personne à charge",
        "Enfant de moins de 18 ans à la fin de 2025",
        "Aucune garde partagée",
        "Aucun paiement de pension alimentaire",
        "Aucune déficience physique ou mentale de l'enfant",
        "Aucun époux ou conjoint de fait pendant toute l'année 2025",
        "Un seul montant ligne 30400 réclamé par le ménage",
        "Aucun autre contribuable ne réclame la ligne 30400",
        "Revenu net de la personne à charge confirmé",
        "Validation comptable confirmée",
        "14,5 %",
        "ligne 34990",
    ):
        assert terme in texte


def test_gui_construit_et_valide_personne_charge():
    texte = _source()
    assert "MontantPersonneChargeAdmissibleFederal2025(" in texte
    assert (
        "valider_montant_personne_charge_admissible_federal_2025("
        in texte
    )


def test_gui_recharge_personne_charge():
    texte = _source()
    assert "personne_charge_admissible_federale_courante = (" in texte
    assert (
        "enregistrement.personne_charge_admissible_federale"
        in texte
    )


def test_gui_relit_personne_charge_dans_calcul_et_stockage():
    texte = _source()
    assert texte.count(
        "personne_charge_admissible_federale="
        "personne_charge_admissible_federale_courante,"
    ) >= 3
