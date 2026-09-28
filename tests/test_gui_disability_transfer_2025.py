from dataclasses import fields
import pytest

from tests.test_gui_block2 import application, racine, bouton, derniere_fenetre
from tests.test_gui_pension_income_2025 import champ
from tests.test_gui_other_deductions_2025 import _remplir
from tests.test_tax_disability_transfer_2025 import transfert
from src.comptaprivee.tax_disability_transfer_2025 import TransfertsHandicap2025, CONFIRMATIONS_HANDICAP_TRANSFERE
from src.comptaprivee.gui_disability_transfer_2025 import ouvrir_transferts_handicap_2025


def confirmer(d):
    for n in CONFIRMATIONS_HANDICAP_TRANSFERE:
        w = champ(d, n + "_5r")
        if not d.getvar(w.cget("variable")):
            w.invoke()


def donneur(parent, transfert, tmp_path, monkeypatch):
    bouton(parent, "Ajouter — donneurs").invoke()
    d = derniere_fenetre(parent)
    for f in fields(transfert):
        if f.name in ("dossier_donneur_json", "autres_parts") or f.name in CONFIRMATIONS_HANDICAP_TRANSFERE:
            continue
        w = champ(d, f.name + "_5r")
        v = getattr(transfert, f.name)
        if f.type is bool:
            if bool(d.getvar(w.cget("variable"))) != v:
                w.invoke()
        elif f.name in ("lien", "condition", "situation_pension"):
            w.set(v)
        else:
            _remplir(w, str(v))
    f = tmp_path / "donneur_gui.json"
    f.write_text(transfert.dossier_donneur_json, encoding="utf-8")
    monkeypatch.setattr("src.comptaprivee.gui_disability_transfer_2025.filedialog.askopenfilename", lambda **kw: str(f))
    bouton(d, "Importer le dossier du donneur").invoke()
    confirmer(d)
    return d


def test_import_reouverture_revocation_et_effacement(application, transfert, tmp_path, monkeypatch):
    recus = []
    ouvrir_transferts_handicap_2025(application, TransfertsHandicap2025(), "Client Test", recus.append)
    d = derniere_fenetre(application)
    enfant = donneur(d, transfert, tmp_path, monkeypatch)
    bouton(enfant, "Enregistrer le donneur").invoke()
    assert not enfant.winfo_exists(), application.messages_test
    bouton(d, "Appliquer les transferts").invoke()
    assert recus[0].transferts == (transfert,)
    ouvrir_transferts_handicap_2025(application, recus[0], "Client Test", recus.append)
    d = derniere_fenetre(application)
    champ(d, "donneurs_5r").selection_set("0")
    bouton(d, "Modifier — donneurs").invoke()
    enfant = derniere_fenetre(d)
    _remplir(champ(enfant, "source_5r"), "Nouvelle pièce")
    assert all(not enfant.getvar(champ(enfant, n + "_5r").cget("variable")) for n in CONFIRMATIONS_HANDICAP_TRANSFERE)
    bouton(enfant, "Enregistrer le donneur").invoke()
    assert enfant.winfo_exists()
    confirmer(enfant)
    bouton(enfant, "Enregistrer le donneur").invoke()
    bouton(d, "Effacer les transferts").invoke()
    assert recus[-1] == TransfertsHandicap2025()


@pytest.mark.parametrize("montant", ["NaN", "Infinity", "-1", "1.001", "16053", "texte"])
def test_parts_invalides(application, transfert, tmp_path, monkeypatch, montant):
    recus = []
    ouvrir_transferts_handicap_2025(application, TransfertsHandicap2025(), "Client Test", recus.append)
    d = derniere_fenetre(application)
    enfant = donneur(d, transfert, tmp_path, monkeypatch)
    champ(enfant, "limiter_demande_5r").invoke()
    _remplir(champ(enfant, "part_demandee_5r"), montant)
    confirmer(enfant)
    bouton(enfant, "Enregistrer le donneur").invoke()
    assert enfant.winfo_exists() and not recus and application.messages_test
    enfant.destroy()
    d.destroy()


def test_bouton_application(application):
    application.ouvrir_agent_fiscal()
    fiscal = derniere_fenetre(application)
    bouton(fiscal, "Transferts handicap 2025 (5R)").invoke()
    d = derniere_fenetre(fiscal)
    bouton(d, "Appliquer les transferts").invoke()
    assert not d.winfo_exists()
    assert "Transferts handicap" in application.statut.get()
    fiscal.destroy()


def test_part_autre_soutien_revoque_et_reduit_demande(application, transfert, tmp_path, monkeypatch):
    recus = []
    ouvrir_transferts_handicap_2025(application, TransfertsHandicap2025(), "Client Test", recus.append)
    d = derniere_fenetre(application)
    enfant = donneur(d, transfert, tmp_path, monkeypatch)
    bouton(enfant, "Ajouter — autres soutiens").invoke()
    part = derniere_fenetre(enfant)
    for nom, valeur in (("personne", "Autre parent"), ("montant_base", "6052"), ("source", "Accord synthétique")):
        _remplir(champ(part, nom + "_5r"), valeur)
    bouton(part, "Enregistrer").invoke()
    assert not part.winfo_exists()
    assert all(not enfant.getvar(champ(enfant, n + "_5r").cget("variable")) for n in CONFIRMATIONS_HANDICAP_TRANSFERE)
    confirmer(enfant)
    bouton(enfant, "Enregistrer le donneur").invoke()
    bouton(d, "Appliquer les transferts").invoke()
    from src.comptaprivee.tax_disability_transfer_2025 import calculer_transferts_handicap_2025
    assert calculer_transferts_handicap_2025(recus[0], beneficiaire="Client Test").ligne_31800 == 10000


def test_reimport_revoque_confirmations(application, transfert, tmp_path, monkeypatch):
    ouvrir_transferts_handicap_2025(application, TransfertsHandicap2025(), "Client Test", lambda p: None)
    d = derniere_fenetre(application)
    enfant = donneur(d, transfert, tmp_path, monkeypatch)
    bouton(enfant, "Importer le dossier du donneur").invoke()
    assert all(not enfant.getvar(champ(enfant, n + "_5r").cget("variable")) for n in CONFIRMATIONS_HANDICAP_TRANSFERE)
    bouton(enfant, "Annuler").invoke()
    assert not champ(d, "donneurs_5r").get_children()
    d.destroy()
