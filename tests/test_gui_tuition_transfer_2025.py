import tkinter as tk
from tkinter import ttk
import pytest
from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre, descendants
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from tests.test_gui_training_credit_2025 import ouvrir
from src.comptaprivee.tax_tuition_carryforward_2025 import CONFIRMATIONS_REPORTS_SCOLARITE
from src.comptaprivee.tax_tuition_transfer_2025 import CONFIRMATIONS_TRANSFERT_SCOLARITE


def remplir(d):
    entries = [w for w in descendants(d) if isinstance(w, ttk.Entry)]
    for w, v in zip(entries[:4], ("3000", "T2202 fictif", "0", "")):
        _remplir(w, v)
    for nom, v in (("report_avis_2024_5f", "1000"), ("source_5f", "Avis ARC fictif"),
                   ("montant_designe_5g", "1000"), ("beneficiaire_5g", "Parent fictif"), ("source_5g", "Certificat signé fictif")):
        _remplir(champ(d, nom), v)
    champ(d, "relation_5g").set("parent")
    champ(d, "activer_5f").invoke()
    for w in descendants(d):
        if isinstance(w, tk.Checkbutton) and w.cget("text") not in ("Aucun report antérieur", "Aucun transfert à une autre personne"):
            w.select()
    for nom in CONFIRMATIONS_REPORTS_SCOLARITE:
        if nom != "aucun_transfert_entrant_sortant":
            champ(d, nom + "_5f").invoke()
    for nom in (*CONFIRMATIONS_TRANSFERT_SCOLARITE, "aucun_credit_conjoint_30300_30425_32600"):
        champ(d, nom + "_5g").invoke()


def test_gui_reouverture_effacer(application):
    fiscal, d = ouvrir(application)
    remplir(d)
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    bouton(fiscal, "Frais de scolarité 2025").invoke()
    d = derniere_fenetre(fiscal)
    assert champ(d, "montant_designe_5g").get() == "1000"
    assert champ(d, "relation_5g").get() == "parent"
    bouton(d, "Effacer").invoke()
    assert champ(d, "beneficiaire_5g").get() == ""
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists()
    fiscal.destroy()


@pytest.mark.parametrize("nom", ["montant_designe", "beneficiaire", "source", "relation"])
def test_gui_modification_revoque(application, nom):
    fiscal, d = ouvrir(application)
    remplir(d)
    if nom == "relation":
        champ(d, nom + "_5g").set("conjoint")
    else:
        _remplir(champ(d, nom + "_5g"), "99")
    for confirmation in (*CONFIRMATIONS_TRANSFERT_SCOLARITE, "aucun_credit_conjoint_30300_30425_32600"):
        assert d.getvar(champ(d, confirmation + "_5g").cget("variable")) == 0
    for confirmation in CONFIRMATIONS_REPORTS_SCOLARITE:
        assert d.getvar(champ(d, confirmation + "_5f").cget("variable")) == 0
    bouton(d, "Fermer").invoke()
    fiscal.destroy()
