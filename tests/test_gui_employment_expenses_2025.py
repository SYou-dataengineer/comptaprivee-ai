from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre
from tests.test_gui_pension_income_2025 import champ


def ouvrir_dialogue(app):
    app.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(app)
    bouton(fiscal, "Dépenses d'emploi 2025 (4C)").invoke()
    dialogue = derniere_fenetre(fiscal)
    return fiscal, dialogue


def _remplir(entree, valeur):
    entree.delete(0, "end")
    entree.insert(0, valeur)


def _cocher(dialogue, nom):
    case = champ(dialogue, nom)
    if dialogue.getvar(case.cget("variable")) == 0:
        case.invoke()


def test_gui_depenses_emploi_4c_affiche_champs(application):
    fiscal, dialogue = ouvrir_dialogue(application)
    assert champ(dialogue, "deduction_federale_4c").get() == ""
    assert champ(dialogue, "source_federale_4c").get() == ""
    assert champ(dialogue, "deduction_quebec_4c").get() == ""
    assert champ(dialogue, "source_quebec_4c").get() == ""
    bouton(dialogue, "Fermer").invoke()
    fiscal.destroy()


def test_gui_depenses_emploi_4c_modification_revoque_confirmations(application):
    app = application
    fiscal, dialogue = ouvrir_dialogue(app)
    noms = (
        "confirmation_comptable_depenses_emploi_4c",
        "confirmation_salarie_ordinaire_4c",
        "confirmation_contrat_depenses_4c",
        "confirmation_non_remboursees_4c",
        "confirmation_t2200_4c",
        "confirmation_t777_4c",
        "confirmation_tp643_4c",
        "confirmation_tp59_4c",
    )
    for nom in noms:
        _cocher(dialogue, nom)
    _remplir(champ(dialogue, "deduction_federale_4c"), "1200")
    app.update()
    for nom in noms:
        case = champ(dialogue, nom)
        assert dialogue.getvar(case.cget("variable")) == 0
    bouton(dialogue, "Fermer").invoke()
    fiscal.destroy()


def test_gui_depenses_emploi_4c_valide_profil(application):
    app = application
    fiscal, dialogue = ouvrir_dialogue(app)
    _remplir(champ(dialogue, "deduction_federale_4c"), "1200")
    _remplir(champ(dialogue, "source_federale_4c"), "T2200 + T777 2025")
    _remplir(champ(dialogue, "deduction_quebec_4c"), "1000")
    _remplir(champ(dialogue, "source_quebec_4c"), "TP-64.3 + TP-59 2025")
    for nom in (
        "confirmation_comptable_depenses_emploi_4c",
        "confirmation_salarie_ordinaire_4c",
        "confirmation_contrat_depenses_4c",
        "confirmation_non_remboursees_4c",
        "confirmation_t2200_4c",
        "confirmation_t777_4c",
        "confirmation_tp643_4c",
        "confirmation_tp59_4c",
    ):
        _cocher(dialogue, nom)
    bouton(dialogue, "Valider et appliquer").invoke()
    assert not dialogue.winfo_exists(), app.messages_test
    fiscal.destroy()
