"""Désignations de scolarité reçues, T1 2025 ligne 32400 (bloc 5H).

Source : ARC, ligne 32400, année 2025; annexe 11, lignes 21–24.
L'annexe 11 du tiers est vérifiée par le comptable, non reconstruite ici.
"""
from dataclasses import dataclass
from decimal import Decimal
from .tax_federal_top_up_2025 import montant_decimal_2025

RELATIONS_SCOLARITE_RECUE = ("parent", "grand_parent", "parent_conjoint", "grand_parent_conjoint")
CONFIRMATIONS_SCOLARITE_RECUE = {
    "valide_par_comptable": "Désignation et lien admissible validés par le comptable",
    "certificat_signe": "Certificat signé désignant ce contribuable comme seul bénéficiaire",
    "annexe11_verifiee": "Déclaration étudiant et annexe 11 de 2025 vérifiées : désignation conforme à 32700",
    "plafond_verifie": "Désignation au plus égale à min(frais courants nets du CCF, 5000) moins frais courants utilisés",
    "aucun_report_anterieur": "Aucun montant d'année antérieure dans le transfert",
    "aucun_credit_conjoint": "Le conjoint de l'étudiant ne réclame pas 30300, 30425 ou 32600 pour lui",
}


@dataclass(frozen=True)
class DesignationScolariteRecue2025:
    reference_etudiant: str = ""
    nom_etudiant: str = ""
    relation: str = ""
    montant_certificat: Decimal = Decimal("0")
    source: str = ""
    valide_par_comptable: bool = False
    certificat_signe: bool = False
    annexe11_verifiee: bool = False
    plafond_verifie: bool = False
    aucun_report_anterieur: bool = False
    aucun_credit_conjoint: bool = False


@dataclass(frozen=True)
class TransfertsScolariteRecus2025:
    designations: tuple[DesignationScolariteRecue2025, ...] = ()


def valider_transferts_scolarite_recus_2025(p: TransfertsScolariteRecus2025) -> TransfertsScolariteRecus2025:
    if not isinstance(p, TransfertsScolariteRecus2025) or type(p.designations) is not tuple:
        raise ValueError("Profil des transferts reçus invalide.")
    references = set()
    for d in p.designations:
        if not isinstance(d, DesignationScolariteRecue2025):
            raise ValueError("Désignation de scolarité invalide.")
        for nom in ("reference_etudiant", "nom_etudiant", "relation", "source"):
            if not isinstance(getattr(d, nom), str) or not getattr(d, nom).strip():
                raise ValueError("Champ obligatoire de la désignation : " + nom)
        reference = d.reference_etudiant.strip().casefold()
        if reference in references:
            raise ValueError("Étudiant compté deux fois : " + d.reference_etudiant)
        references.add(reference)
        if d.relation not in RELATIONS_SCOLARITE_RECUE:
            raise ValueError("Le bénéficiaire doit être un parent ou grand-parent admissible; conjoint : ligne 32600 distincte.")
        if (not isinstance(d.montant_certificat, Decimal) or not d.montant_certificat.is_finite()
                or not Decimal(0) < d.montant_certificat <= Decimal(5000)):
            raise ValueError("La désignation doit être un Decimal fini positif, au plus de 5000 $ par étudiant.")
        montant = montant_decimal_2025(d.montant_certificat, "Montant du certificat")
        if montant != d.montant_certificat:
            raise ValueError("La désignation doit être en cents, positive et au plus de 5000 $ par étudiant.")
        for nom, libelle in CONFIRMATIONS_SCOLARITE_RECUE.items():
            if type(getattr(d, nom)) is not bool or not getattr(d, nom):
                raise ValueError("Confirmation obligatoire : " + libelle)
    return p


def montant_ligne_32400_2025(p: TransfertsScolariteRecus2025) -> Decimal:
    valider_transferts_scolarite_recus_2025(p)
    return sum((d.montant_certificat for d in p.designations), Decimal("0.00"))


def lignes_transferts_scolarite_recus_2025(p: TransfertsScolariteRecus2025) -> list[str]:
    total = montant_ligne_32400_2025(p)
    if not p.designations:
        return []
    lignes = ["", "SCOLARITÉ REÇUE D'ENFANTS / PETITS-ENFANTS — BLOC 5H"]
    for d in p.designations:
        lignes += [f"Étudiant : {d.nom_etudiant} ({d.reference_etudiant}); lien du bénéficiaire : {d.relation}",
            f"Désignation signée : {d.montant_certificat:.2f} $; source : {d.source}",
            "Annexe 11, plafond et bénéficiaire unique vérifiés par le comptable."]
    return lignes + [f"Ligne 32400 : {total:.2f} $; incluse une fois dans 33500.",
        "Crédit non remboursable à 14,5 % dans 33800; compensation 34990 recalculée.",
        "Aucun report chez le bénéficiaire; aucun crédit Québec ou transfert du conjoint calculé ici."]
