from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre
from tests.test_gui_pension_income_2025 import champ


def ouvrir_dialogue(app):
    app.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(app)
    bouton(fiscal, "Autres déductions 2025 (4F)").invoke()
    dialogue = derniere_fenetre(fiscal)
    return fiscal, dialogue


def _remplir(entree, valeur):
    entree.delete(0, "end")
    entree.insert(0, valeur)


def _cocher(dialogue, nom):
    case = champ(dialogue, nom)
    if dialogue.getvar(case.cget("variable")) == 0:
        case.invoke()


def test_gui_autres_deductions_4f_affiche_champs(application):
    fiscal, dialogue = ouvrir_dialogue(application)
    assert champ(dialogue, "deduction_federale_23200_4f").get() == ""
    assert champ(dialogue, "nature_federale_4f").get() == ""
    assert champ(dialogue, "source_federale_4f").get() == ""
    assert champ(dialogue, "deduction_quebec_250_code17_4f").get() == ""
    assert champ(dialogue, "nature_quebec_4f").get() == ""
    assert champ(dialogue, "source_quebec_4f").get() == ""
    bouton(dialogue, "Fermer").invoke()
    fiscal.destroy()


def test_gui_autres_deductions_4f_modification_revoque_confirmations(
    application,
):
    app = application
    fiscal, dialogue = ouvrir_dialogue(app)
    noms = (
        "confirmation_comptable_autres_deductions_4f",
        "confirmation_montant_federal_23200_4f",
        "confirmation_montant_quebec_250_code17_4f",
        "confirmation_aucun_autre_bloc_4f",
    )
    for nom in noms:
        _cocher(dialogue, nom)

    _remplir(champ(dialogue, "deduction_federale_23200_4f"), "1200")
    app.update()

    for nom in noms:
        case = champ(dialogue, nom)
        assert dialogue.getvar(case.cget("variable")) == 0

    bouton(dialogue, "Fermer").invoke()
    fiscal.destroy()


def test_gui_autres_deductions_4f_valide_profil(application):
    app = application
    fiscal, dialogue = ouvrir_dialogue(app)

    _remplir(champ(dialogue, "deduction_federale_23200_4f"), "1200")
    _remplir(
        champ(dialogue, "nature_federale_4f"),
        "Autre montant déductible validé",
    )
    _remplir(
        champ(dialogue, "source_federale_4f"),
        "Pièce fédérale 2025 validée",
    )
    _remplir(champ(dialogue, "deduction_quebec_250_code17_4f"), "900")
    _remplir(
        champ(dialogue, "nature_quebec_4f"),
        "Autre déduction validée code 17",
    )
    _remplir(
        champ(dialogue, "source_quebec_4f"),
        "Pièce Québec 2025 validée",
    )

    for nom in (
        "confirmation_comptable_autres_deductions_4f",
        "confirmation_montant_federal_23200_4f",
        "confirmation_montant_quebec_250_code17_4f",
        "confirmation_aucun_autre_bloc_4f",
    ):
        _cocher(dialogue, nom)

    bouton(dialogue, "Valider et appliquer").invoke()
    assert not dialogue.winfo_exists(), app.messages_test
    fiscal.destroy()
