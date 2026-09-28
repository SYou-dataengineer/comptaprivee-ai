"""Transfert fédéral sortant de scolarité : annexe 11 (25), lignes 21–25."""
from dataclasses import dataclass
from decimal import Decimal
from .tax_federal_top_up_2025 import montant_decimal_2025

ZERO = Decimal("0")
RELATIONS_TRANSFERT_SCOLARITE = ("conjoint", "parent", "grand_parent", "parent_conjoint", "grand_parent_conjoint")


@dataclass(frozen=True)
class TransfertScolariteSortant2025:
    montant_designe: Decimal = ZERO
    beneficiaire: str = ""
    relation: str = ""
    source: str = ""
    valide_par_comptable: bool = False
    autorisation_signee: bool = False
    beneficiaire_unique_confirme: bool = False
    aucun_transfert_entrant: bool = False
    aucun_credit_conjoint_30300_30425_32600: bool = False

    @property
    def present(self) -> bool:
        return self.montant_designe > ZERO


CONFIRMATIONS_TRANSFERT_SCOLARITE = {
    "valide_par_comptable": "Désignation et lien avec le bénéficiaire validés par le comptable",
    "autorisation_signee": "Autorisation de transfert du certificat de scolarité signée et vérifiée",
    "beneficiaire_unique_confirme": "Un seul bénéficiaire désigné pour ce transfert fédéral",
    "aucun_transfert_entrant": "Aucune désignation reçue à 32400 incluse dans mes propres frais de scolarité",
}
LIBELLE_RESTRICTION_CONJOINT = "Pour un parent/grand-parent : le conjoint ne réclame pas 30300, 30425 ou 32600 pour l'étudiant"


def valider_transfert_scolarite_sortant_2025(p: TransfertScolariteSortant2025) -> TransfertScolariteSortant2025:
    if not isinstance(p, TransfertScolariteSortant2025):
        raise ValueError("Profil de transfert de scolarité invalide.")
    montant = montant_decimal_2025(p.montant_designe, "Montant désigné sur le certificat")
    if montant != p.montant_designe or montant > Decimal(5000):
        raise ValueError("Le montant désigné doit être en cents et ne pas dépasser 5000 $.")
    for nom in ("beneficiaire", "relation", "source"):
        if not isinstance(getattr(p, nom), str):
            raise ValueError("Champ de transfert invalide : " + nom)
    for nom in (*CONFIRMATIONS_TRANSFERT_SCOLARITE, "aucun_credit_conjoint_30300_30425_32600"):
        if type(getattr(p, nom)) is not bool:
            raise ValueError("Confirmation de transfert non booléenne : " + nom)
    if p.present:
        if not p.beneficiaire.strip() or not p.source.strip():
            raise ValueError("Bénéficiaire et source du transfert obligatoires.")
        if p.relation not in RELATIONS_TRANSFERT_SCOLARITE:
            raise ValueError("Lien du bénéficiaire non admissible au transfert de scolarité.")
        for nom, libelle in CONFIRMATIONS_TRANSFERT_SCOLARITE.items():
            if not getattr(p, nom):
                raise ValueError("Confirmation obligatoire : " + libelle)
        if p.relation != "conjoint" and not p.aucun_credit_conjoint_30300_30425_32600:
            raise ValueError(LIBELLE_RESTRICTION_CONJOINT)
    return p


def calculer_transfert_scolarite_sortant_2025(p: TransfertScolariteSortant2025, *,
        frais_nets_2025: Decimal, frais_2025_utilises: Decimal) -> tuple[Decimal, Decimal]:
    valider_transfert_scolarite_sortant_2025(p)
    frais = montant_decimal_2025(frais_nets_2025, "Frais nets 2025")
    utilises = montant_decimal_2025(frais_2025_utilises, "Frais 2025 utilisés")
    if utilises > frais:
        raise ValueError("Frais utilisés supérieurs aux frais disponibles.")
    maximum = max(min(frais, Decimal(5000)) - utilises, ZERO)
    if p.montant_designe > maximum:
        raise ValueError(f"Le transfert désigné dépasse le maximum calculé de {maximum:.2f} $ (annexe 11).")
    return maximum, p.montant_designe


def lignes_transfert_scolarite_sortant_2025(p: TransfertScolariteSortant2025, maximum: Decimal, montant: Decimal) -> list[str]:
    if not p.present:
        return []
    return ["", "TRANSFERT FÉDÉRAL SORTANT DE SCOLARITÉ — BLOC 5G",
        f"Bénéficiaire : {p.beneficiaire}; lien : {p.relation}",
        f"Source et autorisation signée validées par le comptable : {p.source}",
        f"Maximum transférable : min(frais 2025 nets, 5000) - frais 2025 utilisés, plancher zéro = {maximum:.2f} $",
        f"Montant désigné sur le certificat — ligne 32700 : {montant:.2f} $",
        "Le transfert diminue le report futur; aucun report antérieur n'est transféré.",
        "Aucun crédit ajouté au dossier étudiant; le bénéficiaire doit réclamer séparément son transfert."]
