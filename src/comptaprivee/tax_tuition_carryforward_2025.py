"""Annexe 11 Québec 2025, reports fédéraux (5F) et transferts sortants (5G).

Source : https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5005-s11/5005-s11-25e.pdf
"""
from dataclasses import dataclass
from decimal import Decimal
from .tax_tuition_transfer_2025 import (
    TransfertScolariteSortant2025, valider_transfert_scolarite_sortant_2025,
    calculer_transfert_scolarite_sortant_2025, lignes_transfert_scolarite_sortant_2025,
)
from .tax_federal_top_up_2025 import montant_decimal_2025
from .tax_rules_2025 import arrondir_cent

ZERO = Decimal("0")


@dataclass(frozen=True)
class ReportsScolariteFederaux2025:
    activer: bool = False
    report_avis_2024: Decimal = ZERO
    source: str = ""
    valide_par_comptable: bool = False
    avis_arc_2024_confirme: bool = False
    solde_non_reclame_confirme: bool = False
    aucun_transfert_entrant_sortant: bool = False
    resident_canada_quebec_confirme: bool = False
    aucun_deces_faillite: bool = False
    aucun_report_quebec: bool = False
    transfert_sortant: TransfertScolariteSortant2025 = TransfertScolariteSortant2025()


CONFIRMATIONS_REPORTS_SCOLARITE = {
    "aucun_report_quebec": "Aucun report Québec — non intégré au bloc fédéral 5F",
    "valide_par_comptable": "Reports fédéraux validés par le comptable",
    "avis_arc_2024_confirme": "Dernier avis ARC 2024 vérifié, ou absence de report confirmée",
    "solde_non_reclame_confirme": "Solde fédéral disponible, non déjà réclamé, confirmé",
    "aucun_transfert_entrant_sortant": "Aucun transfert sortant de mes frais; les désignations reçues à 32400 sont séparées",
    "resident_canada_quebec_confirme": "Profil résident Canada/Québec confirmé",
    "aucun_deces_faillite": "Aucun décès ni faillite — traitements hors profil",
}


def valider_reports_scolarite_federaux_2025(p: ReportsScolariteFederaux2025) -> ReportsScolariteFederaux2025:
    if not isinstance(p, ReportsScolariteFederaux2025):
        raise ValueError("Profil de reports scolarité fédéraux invalide.")
    valider_transfert_scolarite_sortant_2025(p.transfert_sortant)
    for nom in ("activer", *CONFIRMATIONS_REPORTS_SCOLARITE):
        if type(getattr(p, nom)) is not bool:
            raise ValueError("Confirmation reports scolarité non booléenne : " + nom)
    if montant_decimal_2025(p.report_avis_2024, "Report scolarité fédéral") != p.report_avis_2024:
        raise ValueError("Le report fédéral doit être exprimé en cents.")
    if not isinstance(p.source, str):
        raise ValueError("Source reports scolarité invalide.")
    if p.report_avis_2024 and not p.activer:
        raise ValueError("Activer le calcul des reports fédéraux pour utiliser le solde.")
    if p.transfert_sortant.present:
        if not p.activer:
            raise ValueError("Activer l'annexe 11 (5F) pour calculer un transfert sortant.")
        if p.aucun_transfert_entrant_sortant:
            raise ValueError("Confirmation contradictoire : transfert sortant présent et aucun transfert.")
    if p.activer:
        if not p.source.strip():
            raise ValueError("Source des reports fédéraux obligatoire.")
        for nom, libelle in CONFIRMATIONS_REPORTS_SCOLARITE.items():
            if nom == "aucun_transfert_entrant_sortant" and p.transfert_sortant.present:
                continue
            if not getattr(p, nom):
                raise ValueError("Confirmation obligatoire : " + libelle)
    return p


@dataclass(frozen=True)
class ResultatReportsScolariteFederaux2025:
    frais_2025_nets: Decimal = ZERO
    capacite_annexe11: Decimal = ZERO
    report_anterieur_utilise: Decimal = ZERO
    frais_2025_utilises: Decimal = ZERO
    ligne_32300: Decimal = ZERO
    report_futur: Decimal = ZERO
    transfert_maximal: Decimal = ZERO
    ligne_32700: Decimal = ZERO

    @property
    def credit_federal(self) -> Decimal:
        return arrondir_cent(self.ligne_32300 * Decimal(".145"))


def calculer_reports_scolarite_federaux_2025(p: ReportsScolariteFederaux2025, *,
        frais_nets_2025: Decimal, revenu_imposable: Decimal, impot_brut: Decimal,
        base_ligne105: Decimal) -> ResultatReportsScolariteFederaux2025:
    valider_reports_scolarite_federaux_2025(p)
    if not p.activer:
        return ResultatReportsScolariteFederaux2025()
    frais, revenu, brut, base = (montant_decimal_2025(v, n) for n, v in (
        ("Frais nets 2025", frais_nets_2025), ("26000", revenu_imposable),
        ("Impôt brut", impot_brut), ("Ligne 105", base_ligne105)))
    equivalent = revenu if revenu <= Decimal(57375) else brut / Decimal(".145")
    capacite = arrondir_cent(max(equivalent - base, ZERO))
    anterieur = min(p.report_avis_2024, capacite)
    courant = min(frais, capacite - anterieur)
    utilise = anterieur + courant
    maximum, transfert = calculer_transfert_scolarite_sortant_2025(
        p.transfert_sortant, frais_nets_2025=frais, frais_2025_utilises=courant,
    )
    return ResultatReportsScolariteFederaux2025(frais, capacite, anterieur, courant,
        utilise, p.report_avis_2024 + frais - utilise - transfert, maximum, transfert)


def lignes_reports_scolarite_federaux_2025(p: ReportsScolariteFederaux2025, r: ResultatReportsScolariteFederaux2025) -> list[str]:
    if not p.activer:
        return []
    return ["", "REPORTS FÉDÉRAUX DE SCOLARITÉ — BLOC 5F",
        f"Source validée par le comptable : {p.source}",
        f"Solde du dernier avis ARC 2024 : {p.report_avis_2024:.2f} $",
        f"Frais 2025 nets après CCF : {r.frais_2025_nets:.2f} $",
        "Annexe 11 : capacité = max(26000 ou impôt brut / 14.5 % - ligne 105, 0).",
        f"Capacité de réclamation : {r.capacite_annexe11:.2f} $",
        f"Report antérieur utilisé en priorité : {r.report_anterieur_utilise:.2f} $",
        f"Frais 2025 utilisés ensuite : {r.frais_2025_utilises:.2f} $",
        f"Ligne 32300 : {r.ligne_32300:.2f} $; crédit à 14.5 % : {r.credit_federal:.2f} $",
        f"Report fédéral futur calculé : {r.report_futur:.2f} $",
        f"Maximum transférable pour les frais courants : {r.transfert_maximal:.2f} $",
        "Solde futur après transfert éventuel, à rapprocher de l'avis ARC; aucun report Québec dans 5F.",
        *lignes_transfert_scolarite_sortant_2025(p.transfert_sortant, r.transfert_maximal, r.ligne_32700)]
