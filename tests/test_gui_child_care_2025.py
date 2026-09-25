from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre
from tests.test_gui_pension_income_2025 import champ


def ouvrir_dialogue(app):
    app.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(app)
    bouton(fiscal, "Frais de garde 2025 (4B)").invoke()
    dialogue = derniere_fenetre(fiscal)
    return fiscal, dialogue


def _remplir(entree, valeur):
    entree.delete(0, "end")
    entree.insert(0, valeur)


def _cocher(dialogue, nom):
    case = champ(dialogue, nom)
    if dialogue.getvar(case.cget("variable")) == 0:
        case.invoke()


def test_gui_frais_garde_4b_affiche_champs(application):
    fiscal, dialogue = ouvrir_dialogue(application)
    assert champ(dialogue, "frais_garde_payes_4b").get() == ""
    assert champ(dialogue, "revenu_gagne_t778_4b").get() == ""
    assert champ(dialogue, "enfants_moins_7_4b").get() == ""
    assert champ(dialogue, "enfants_7_16_4b").get() == ""
    assert champ(dialogue, "enfants_dtc_4b").get() == ""
    assert champ(dialogue, "source_frais_garde_4b").get() == ""
    bouton(dialogue, "Fermer").invoke()
    fiscal.destroy()


def test_gui_frais_garde_4b_modification_revoque_confirmations(application):
    app = application
    fiscal, dialogue = ouvrir_dialogue(app)
    noms = (
        "confirmation_frais_garde_comptable_4b",
        "confirmation_services_2025_4b",
        "confirmation_gagner_revenu_4b",
        "confirmation_recus_frais_garde_4b",
        "confirmation_demandeur_frais_garde_4b",
    )
    for nom in noms:
        _cocher(dialogue, nom)
    _remplir(champ(dialogue, "frais_garde_payes_4b"), "6000")
    app.update()
    for nom in noms:
        case = champ(dialogue, nom)
        assert dialogue.getvar(case.cget("variable")) == 0
    bouton(dialogue, "Fermer").invoke()
    fiscal.destroy()


def test_gui_frais_garde_4b_valide_profil(application):
    app = application
    fiscal, dialogue = ouvrir_dialogue(app)
    _remplir(champ(dialogue, "frais_garde_payes_4b"), "6000")
    _remplir(champ(dialogue, "revenu_gagne_t778_4b"), "52000")
    _remplir(champ(dialogue, "enfants_moins_7_4b"), "1")
    _remplir(
        champ(dialogue, "source_frais_garde_4b"),
        "T778 2025 / reçus de garde",
    )
    for nom in (
        "confirmation_frais_garde_comptable_4b",
        "confirmation_services_2025_4b",
        "confirmation_gagner_revenu_4b",
        "confirmation_recus_frais_garde_4b",
        "confirmation_demandeur_frais_garde_4b",
    ):
        _cocher(dialogue, nom)
    bouton(dialogue, "Valider et appliquer").invoke()
    assert not dialogue.winfo_exists(), app.messages_test
    fiscal.destroy()
