from .tax_donation_carryforward_2025 import ReportsDonsFederaux2025, valider_reports_dons_federaux_2025
from dataclasses import dataclass
from decimal import Decimal
from .tax_rules_2025 import arrondir_cent
from .tax_federal_top_up_2025 import montant_decimal_2025

ZERO = Decimal("0")
DEUX_CENTS = Decimal("200")
TAUX_FEDERAL_PREMIERS_200_2025 = Decimal("0.145")
TAUX_FEDERAL_EXCEDENT_2025 = Decimal("0.29")
SEUIL_FEDERAL_TAUX_SUPERIEUR_2025 = Decimal("253414")
TAUX_QUEBEC_PREMIERS_200_2025 = Decimal("0.20")
TAUX_QUEBEC_EXCEDENT_SIMPLE_2025 = Decimal("0.24")
SEUIL_QUEBEC_TAUX_SUPERIEUR_2025 = Decimal("129590")


@dataclass(frozen=True)
class DonsBienfaisance2025:
    montant_admissible_federal: Decimal = ZERO
    montant_admissible_quebec: Decimal = ZERO
    source_federale: str = ""
    source_quebec: str = ""
    valide_par_comptable: bool = False
    donataire_reconnu_confirme: bool = False
    dons_monetaires_2025_uniquement: bool = False
    aucun_report_anterieur: bool = False
    inclut_dons_jan_fev_2025: bool = False
    dons_jan_fev_deja_reclames_2024: bool = False
    reports_federaux: ReportsDonsFederaux2025 = ReportsDonsFederaux2025()


def aucun_don_bienfaisance_2025():
    return DonsBienfaisance2025()


def valider_plafond_dons_monetaire_federal_2025(dons, revenu_net_federal):
    """Annexe 9 (25), lignes 6–10 : dons monétaires, sans majoration en nature."""
    valider_dons_bienfaisance_2025(dons)
    net = montant_decimal_2025(revenu_net_federal, "Revenu net fédéral 23600")
    plafond = arrondir_cent(net * Decimal("0.75"))
    if montant_dons_federaux_reclames_2025(dons) > plafond:
        raise ValueError(
            "Les dons monétaires fédéraux réclamés dépassent 75 % du revenu net 23600. "
            "L'excédent nécessite un report, hors du profil actuel."
        )


def valider_dons_bienfaisance_2025(dons):
    valider_reports_dons_federaux_2025(dons.reports_federaux)
    fed = dons.montant_admissible_federal
    qc = dons.montant_admissible_quebec
    for nom, montant in (("Don fédéral", fed), ("Don Québec", qc)):
        if not isinstance(montant, Decimal) or not montant.is_finite():
            raise ValueError(f"{nom} doit être un Decimal fini.")
    if fed < ZERO:
        raise ValueError("Le montant admissible fédéral des dons ne peut pas être négatif.")
    if qc < ZERO:
        raise ValueError("Le montant admissible Québec des dons ne peut pas être négatif.")
    if dons.reports_federaux.activer:
        if dons.reports_federaux.reports and dons.aucun_report_anterieur:
            raise ValueError("Confirmation contradictoire : reports présents et aucun report.")
        disponible = fed + sum((r.montant for r in dons.reports_federaux.reports), ZERO)
        if dons.reports_federaux.montant_reclame > disponible:
            raise ValueError("Réclamation supérieure aux dons disponibles.")
    if fed == ZERO and qc == ZERO:
        return dons
    if not dons.valide_par_comptable:
        raise ValueError("Les dons doivent être validés par le comptable.")
    if not dons.donataire_reconnu_confirme:
        raise ValueError("Le statut de donataire reconnu doit être confirmé.")
    if not dons.dons_monetaires_2025_uniquement:
        raise ValueError("Cette version accepte uniquement les dons monétaires faits en 2025.")
    if not dons.aucun_report_anterieur and not dons.reports_federaux.activer:
        raise ValueError("Cette version n'accepte pas encore les dons reportés d'une année antérieure.")
    if dons.inclut_dons_jan_fev_2025 and dons.dons_jan_fev_deja_reclames_2024:
        raise ValueError("Un don de janvier ou février 2025 déjà demandé en 2024 ne peut pas être demandé de nouveau.")
    if fed > ZERO and not dons.source_federale.strip():
        raise ValueError("La source fédérale du don est obligatoire.")
    if qc > ZERO and not dons.source_quebec.strip():
        raise ValueError("La source Québec du don est obligatoire.")
    return dons


def montant_dons_federaux_reclames_2025(dons):
    valider_dons_bienfaisance_2025(dons)
    return dons.reports_federaux.montant_reclame if dons.reports_federaux.activer else dons.montant_admissible_federal


@dataclass(frozen=True)
class VentilationCreditDons2025:
    base_premiers_200: Decimal
    base_taux_intermediaire: Decimal
    base_taux_superieur: Decimal
    credit_premiers_200: Decimal
    credit_taux_intermediaire: Decimal
    credit_taux_superieur: Decimal

    @property
    def total(self) -> Decimal:
        return self.credit_premiers_200 + self.credit_taux_intermediaire + self.credit_taux_superieur


def _ventiler_credit_dons(montant, revenu, seuil, taux_initial, taux_intermediaire, taux_superieur):
    if not isinstance(revenu, Decimal) or not revenu.is_finite():
        raise ValueError("Le revenu imposable doit être un Decimal fini.")
    if revenu < ZERO:
        raise ValueError("Le revenu imposable ne peut pas être négatif.")
    premiers = min(montant, DEUX_CENTS)
    excedent = max(montant - DEUX_CENTS, ZERO)
    superieur = min(excedent, max(revenu - seuil, ZERO))
    intermediaire = excedent - superieur
    # Chaque ligne monétaire du formulaire est arrondie avant addition.
    return VentilationCreditDons2025(premiers, intermediaire, superieur,
        arrondir_cent(premiers * taux_initial), arrondir_cent(intermediaire * taux_intermediaire),
        arrondir_cent(superieur * taux_superieur))


def ventiler_credit_federal_dons_2025(dons, revenu_imposable_federal):
    """Annexe 9 (25), lignes 13–23; dons monétaires ordinaires seulement."""
    montant = montant_dons_federaux_reclames_2025(dons)
    return _ventiler_credit_dons(montant, revenu_imposable_federal,
        SEUIL_FEDERAL_TAUX_SUPERIEUR_2025, TAUX_FEDERAL_PREMIERS_200_2025,
        TAUX_FEDERAL_EXCEDENT_2025, Decimal("0.33"))


def ventiler_credit_quebec_dons_2025(dons, revenu_imposable_quebec):
    """Grille 395 (2025-12), lignes 1–12; dons en argent de 2025."""
    valider_dons_bienfaisance_2025(dons)
    return _ventiler_credit_dons(dons.montant_admissible_quebec, revenu_imposable_quebec,
        SEUIL_QUEBEC_TAUX_SUPERIEUR_2025, TAUX_QUEBEC_PREMIERS_200_2025,
        TAUX_QUEBEC_EXCEDENT_SIMPLE_2025, Decimal("0.2575"))


def credit_federal_dons_2025(dons, revenu_imposable_federal):
    return ventiler_credit_federal_dons_2025(dons, revenu_imposable_federal).total


def credit_quebec_dons_2025(dons, revenu_imposable_quebec):
    return ventiler_credit_quebec_dons_2025(dons, revenu_imposable_quebec).total


def lignes_credits_dons_2025(dons, revenu_federal, revenu_quebec):
    if not (dons.montant_admissible_federal or dons.montant_admissible_quebec or dons.reports_federaux.activer):
        return []
    f = ventiler_credit_federal_dons_2025(dons, revenu_federal)
    q = ventiler_credit_quebec_dons_2025(dons, revenu_quebec)
    return ["", "CRÉDITS POUR DONS — VENTILATION 2025",
        f"Source fédérale : {dons.source_federale or dons.reports_federaux.source}; validation comptable confirmée",
        f"Source Québec : {dons.source_quebec}",
        f"Dons fédéraux réclamés : {montant_dons_federaux_reclames_2025(dons):.2f} $",
        f"Fédéral : {f.base_premiers_200:.2f} × 14,5 % = {f.credit_premiers_200:.2f}; "
        f"{f.base_taux_intermediaire:.2f} × 29 % = {f.credit_taux_intermediaire:.2f}; "
        f"{f.base_taux_superieur:.2f} × 33 % = {f.credit_taux_superieur:.2f} $",
        f"Base à 33 % : min(dons au-delà de 200, max(26000 - 253414, 0)); 26000 = {revenu_federal:.2f} $",
        f"Crédit fédéral pour dons — ligne 34900 : {f.total:.2f} $",
        f"Québec : {q.base_premiers_200:.2f} × 20 % = {q.credit_premiers_200:.2f}; "
        f"{q.base_taux_intermediaire:.2f} × 24 % = {q.credit_taux_intermediaire:.2f}; "
        f"{q.base_taux_superieur:.2f} × 25,75 % = {q.credit_taux_superieur:.2f} $",
        f"Base à 25,75 % : min(dons au-delà de 200, max(299 - 129590, 0)); 299 = {revenu_quebec:.2f} $",
        f"Crédit Québec pour dons — ligne 395 : {q.total:.2f} $",
        "Crédits non remboursables; arrondi de chaque composante monétaire avant addition."]


from dataclasses import replace

from .tax_federal_2025 import ImpotFederalPreliminaire2025
from .tax_quebec_2025 import ImpotQuebecPreliminaire2025


def appliquer_credit_federal_dons_2025(
    impot: ImpotFederalPreliminaire2025,
    dons: DonsBienfaisance2025,
    revenu_imposable_federal: Decimal,
) -> ImpotFederalPreliminaire2025:
    """Applique le crédit fédéral pour dons après les crédits de base."""
    credit = credit_federal_dons_2025(
        dons,
        revenu_imposable_federal,
    )
    if credit == ZERO:
        return impot

    limitations = tuple(
        texte
        for texte in impot.limitations
        if texte != "Aucun don ni crédit transféré."
    ) + (
        "Crédit fédéral pour dons de bienfaisance admissibles inclus.",
    )

    return replace(
        impot,
        impot_federal_de_base=max(
            arrondir_cent(impot.impot_federal_de_base - credit),
            ZERO,
        ),
        limitations=limitations,
    )


def appliquer_credit_quebec_dons_2025(
    impot: ImpotQuebecPreliminaire2025,
    dons: DonsBienfaisance2025,
    revenu_imposable_quebec: Decimal,
) -> ImpotQuebecPreliminaire2025:
    """Applique le crédit Québec pour dons après les crédits déjà intégrés."""
    credit = credit_quebec_dons_2025(
        dons,
        revenu_imposable_quebec,
    )
    if credit == ZERO:
        return impot

    limitations = tuple(
        texte
        for texte in impot.limitations
        if texte != "Aucun crédit handicap, médical, scolarité ou don."
    ) + (
        "Aucun crédit handicap, médical ou scolarité.",
        "Crédit Québec pour dons de bienfaisance admissibles inclus.",
    )

    return replace(
        impot,
        impot_quebec_preliminaire=max(
            arrondir_cent(impot.impot_quebec_preliminaire - credit),
            ZERO,
        ),
        limitations=limitations,
    )
