from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre
from tests.test_gui_pension_income_2025 import champ


def ouvrir_dialogue(app):
    app.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(app)
    bouton(fiscal, "Pension alimentaire 2025 (4E)").invoke()
    dialogue = derniere_fenetre(fiscal)
    return fiscal, dialogue


def _remplir(entree, valeur):
    entree.delete(0, "end")
    entree.insert(0, valeur)


def _cocher(dialogue, nom):
    case = champ(dialogue, nom)
    if dialogue.getvar(case.cget("variable")) == 0:
        case.invoke()


def test_gui_pension_alimentaire_4e_affiche_champs(application):
    fiscal, dialogue = ouvrir_dialogue(application)
    assert champ(dialogue, "total_paye_21999_4e").get() == ""
    assert champ(dialogue, "deduction_federale_22000_4e").get() == ""
    assert champ(dialogue, "source_federale_4e").get() == ""
    assert champ(dialogue, "deduction_quebec_225_4e").get() == ""
    assert champ(dialogue, "source_quebec_4e").get() == ""
    bouton(dialogue, "Fermer").invoke()
    fiscal.destroy()


def test_gui_pension_alimentaire_4e_modification_revoque_confirmations(
    application,
):
    app = application
    fiscal, dialogue = ouvrir_dialogue(app)
    noms = (
        "confirmation_comptable_pension_4e",
        "confirmation_ordonnance_entente_4e",
        "confirmation_paiement_periodique_conjoint_4e",
        "confirmation_vie_separee_4e",
        "confirmation_enregistrement_arc_4e",
        "confirmation_montant_federal_4e",
        "confirmation_montant_quebec_4e",
        "confirmation_aucun_credit_personnel_lie_4e",
    )
    for nom in noms:
        _cocher(dialogue, nom)

    _remplir(champ(dialogue, "total_paye_21999_4e"), "6000")
    app.update()

    for nom in noms:
        case = champ(dialogue, nom)
        assert dialogue.getvar(case.cget("variable")) == 0

    bouton(dialogue, "Fermer").invoke()
    fiscal.destroy()


def test_gui_pension_alimentaire_4e_valide_profil(application):
    app = application
    fiscal, dialogue = ouvrir_dialogue(app)

    _remplir(champ(dialogue, "total_paye_21999_4e"), "6000")
    _remplir(champ(dialogue, "deduction_federale_22000_4e"), "6000")
    _remplir(champ(dialogue, "source_federale_4e"), "Ordonnance + paiements 2025")
    _remplir(champ(dialogue, "deduction_quebec_225_4e"), "6000")
    _remplir(champ(dialogue, "source_quebec_4e"), "Ordonnance + paiements 2025")

    for nom in (
        "confirmation_comptable_pension_4e",
        "confirmation_ordonnance_entente_4e",
        "confirmation_paiement_periodique_conjoint_4e",
        "confirmation_vie_separee_4e",
        "confirmation_enregistrement_arc_4e",
        "confirmation_montant_federal_4e",
        "confirmation_montant_quebec_4e",
        "confirmation_aucun_credit_personnel_lie_4e",
    ):
        _cocher(dialogue, nom)

    bouton(dialogue, "Valider et appliquer").invoke()
    assert not dialogue.winfo_exists(), app.messages_test
    fiscal.destroy()
