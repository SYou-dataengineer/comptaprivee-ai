from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre
from tests.test_gui_pension_income_2025 import champ


def ouvrir_dialogue(app):
    app.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(app)
    bouton(fiscal, "Frais de déménagement 2025 (4D)").invoke()
    dialogue = derniere_fenetre(fiscal)
    return fiscal, dialogue


def _remplir(entree, valeur):
    entree.delete(0, "end")
    entree.insert(0, valeur)


def _cocher(dialogue, nom):
    case = champ(dialogue, nom)
    if dialogue.getvar(case.cget("variable")) == 0:
        case.invoke()


def test_gui_frais_demenagement_4d_affiche_champs(application):
    fiscal, dialogue = ouvrir_dialogue(application)
    assert champ(dialogue, "deduction_federale_4d").get() == ""
    assert champ(dialogue, "source_federale_4d").get() == ""
    assert champ(dialogue, "deduction_quebec_4d").get() == ""
    assert champ(dialogue, "source_quebec_4d").get() == ""
    bouton(dialogue, "Fermer").invoke()
    fiscal.destroy()


def test_gui_frais_demenagement_4d_modification_revoque_confirmations(
    application,
):
    app = application
    fiscal, dialogue = ouvrir_dialogue(app)
    noms = (
        "confirmation_comptable_frais_demenagement_4d",
        "confirmation_salarie_ordinaire_4d",
        "confirmation_demenagement_emploi_4d",
        "confirmation_40km_4d",
        "confirmation_interieur_canada_4d",
        "confirmation_remboursements_employeur_4d",
        "confirmation_t1m_4d",
        "confirmation_tp348_4d",
    )
    for nom in noms:
        _cocher(dialogue, nom)
    _remplir(champ(dialogue, "deduction_federale_4d"), "2200")
    app.update()
    for nom in noms:
        case = champ(dialogue, nom)
        assert dialogue.getvar(case.cget("variable")) == 0
    bouton(dialogue, "Fermer").invoke()
    fiscal.destroy()


def test_gui_frais_demenagement_4d_valide_profil(application):
    app = application
    fiscal, dialogue = ouvrir_dialogue(app)
    _remplir(champ(dialogue, "deduction_federale_4d"), "2200")
    _remplir(champ(dialogue, "source_federale_4d"), "T1-M 2025 validé")
    _remplir(champ(dialogue, "deduction_quebec_4d"), "1800")
    _remplir(champ(dialogue, "source_quebec_4d"), "TP-348 2025 validé")

    for nom in (
        "confirmation_comptable_frais_demenagement_4d",
        "confirmation_salarie_ordinaire_4d",
        "confirmation_demenagement_emploi_4d",
        "confirmation_40km_4d",
        "confirmation_interieur_canada_4d",
        "confirmation_remboursements_employeur_4d",
        "confirmation_t1m_4d",
        "confirmation_tp348_4d",
    ):
        _cocher(dialogue, nom)

    bouton(dialogue, "Valider et appliquer").invoke()
    assert not dialogue.winfo_exists(), app.messages_test
    fiscal.destroy()
