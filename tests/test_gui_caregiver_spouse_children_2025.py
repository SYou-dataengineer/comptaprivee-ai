from tkinter import ttk
from src.comptaprivee import gui
from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre, descendants
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from tests.test_gui_caregiver_child_combination_2025 import cocher
from tests.test_gui_spouse_transfer_2025 import confirmer
from tests.test_tax_caregiver_spouse_children_2025 import transfert


def test_import_enfants_et_refus_doublon(application, tmp_path, monkeypatch):
    transfert(tmp_path)
    monkeypatch.setattr(gui.filedialog, "askopenfilename", lambda **kw: str(tmp_path / "conjoint_enfants.json"))
    application.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(application)
    client = next(w for w in descendants(fiscal) if isinstance(w, ttk.Entry) and str(w.cget("width")) == "42")
    _remplir(client, "Client Test")
    bouton(fiscal, "Aidant enfant fédéral 2025").invoke()
    bouton(derniere_fenetre(fiscal), "Plusieurs enfants — profil enregistré").invoke()
    d = derniere_fenetre(fiscal)
    bouton(d, "Ajouter").invoke()
    ed = derniere_fenetre(d)
    for nom, valeur in (("reference", "enfant-b"), ("nom", "Enfant fictif B"), ("naissance", "2025-12-31"),
        ("source_enfant", "Pièces fictives")):
        _remplir(champ(ed, nom + "_5y"), valeur)
    for w in descendants(ed):
        if isinstance(w, ttk.Checkbutton) and w.winfo_name() not in ("valide_par_comptable_5y", "preuve_medicale_ou_t2201_confirmee_5y"):
            cocher(w)
    cocher(champ(ed, "preuve_medicale_ou_t2201_confirmee_5y"))
    cocher(champ(ed, "valide_par_comptable_5y"))
    bouton(ed, "Enregistrer l’enfant").invoke()
    cocher(champ(d, "identites_5y")); cocher(champ(d, "valide_5y"))
    bouton(d, "Appliquer les enfants").invoke()
    bouton(fiscal, "Transfert conjoint 2025 (5K)").invoke()
    d = derniere_fenetre(fiscal)
    bouton(d, "Importer le dossier du conjoint").invoke(); confirmer(d)
    bouton(d, "Valider et appliquer").invoke()
    assert d.winfo_exists()
    assert "Même enfant" in str(application.messages_test[-1])
    bouton(d, "Fermer").invoke()
    # Corriger l'identité propre; le dossier importé conserve l'autre enfant.
    bouton(fiscal, "Aidant enfant fédéral 2025").invoke()
    d = derniere_fenetre(fiscal)
    champ(d, "enfants_5y").selection_set("0"); bouton(d, "Modifier").invoke()
    ed = derniere_fenetre(d)
    _remplir(champ(ed, "reference_5y"), "enfant-a")
    _remplir(champ(ed, "nom_5y"), "Enfant fictif A")
    cocher(champ(ed, "preuve_medicale_ou_t2201_confirmee_5y")); cocher(champ(ed, "valide_par_comptable_5y"))
    bouton(ed, "Enregistrer l’enfant").invoke()
    cocher(champ(d, "identites_5y")); cocher(champ(d, "valide_5y"))
    bouton(d, "Appliquer les enfants").invoke()
    bouton(fiscal, "Transfert conjoint 2025 (5K)").invoke()
    d = derniere_fenetre(fiscal)
    bouton(d, "Importer le dossier du conjoint").invoke(); confirmer(d)
    bouton(d, "Calculer l'annexe 2").invoke()
    apercu = d.getvar(champ(d, "apercu_5k").cget("textvariable"))
    assert "Enfant fictif B" in apercu and "2687.00" in apercu, application.messages_test
    bouton(d, "Valider et appliquer").invoke()
    assert not d.winfo_exists(), application.messages_test
    fiscal.destroy()
