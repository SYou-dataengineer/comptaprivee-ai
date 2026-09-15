from pathlib import Path


GUI = Path("src/comptaprivee/gui.py")


def _source():
    return GUI.read_text(encoding="utf-8")


def test_gui_importe_31285():
    t = _source()
    assert "DepensesAccessibiliteDomiciliaireFederal2025" in t
    assert "valider_depenses_accessibilite_domiciliaire_2025" in t


def test_gui_etat_31285_initialise_et_reinitialise():
    t = _source()
    assert (
        t.count(
            "accessibilite_domiciliaire_federale_courante = "
            "DepensesAccessibiliteDomiciliaireFederal2025()"
        )
        >= 2
    )


def test_gui_dialogue_et_bouton_31285():
    t = _source()
    assert (
        "def ouvrir_accessibilite_domiciliaire_federale_2025() -> None:"
        in t
    )
    assert 'text="Accessibilité domicile 31285"' in t
    assert (
        "command=ouvrir_accessibilite_domiciliaire_federale_2025"
        in t
    )


def test_gui_affiche_regles_31285():
    t = _source()
    for terme in (
        "Dépenses admissibles — maximum 20 000 $",
        "65 ans ou plus à la fin de 2025",
        "Admissible au CIPH en 2025",
        "Logement situé au Canada",
        "Logement appartenant au contribuable",
        "Rénovation durable et intégrante",
        "Accessibilité / mobilité / réduction du risque",
        "Travaux et biens de 2025 uniquement",
        "Aucune part entreprise/location",
        "Aucun partage de la demande",
        "Fournisseurs liés : règles confirmées",
        "Dépenses non admissibles exclues",
        "Pièces justificatives conservées",
        "Validation comptable confirmée",
    ):
        assert terme in t


def test_gui_construit_et_valide_profil_31285():
    t = _source()
    assert (
        "profil = DepensesAccessibiliteDomiciliaireFederal2025("
        in t
    )
    normalise = "".join(t.split())
    assert (
        "valider_depenses_accessibilite_domiciliaire_2025(profil)"
        in normalise
    )


def test_gui_recharge_31285():
    t = _source()
    assert (
        "enregistrement.accessibilite_domiciliaire_federale"
        in t
    )


def test_gui_relie_calcul_et_sauvegarde_31285():
    t = _source()
    assert (
        t.count(
            "accessibilite_domiciliaire_federale="
            "accessibilite_domiciliaire_federale_courante,"
        )
        >= 3
    )
