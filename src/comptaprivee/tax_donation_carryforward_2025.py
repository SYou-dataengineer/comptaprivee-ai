"""Reports de dons monétaires fédéraux : annexe 9 (25), bloc 5I.

Source : ARC 2025, ligne 34900, how-much-claim; annexe 9 lignes 6–10.
Les dons antérieurs précèdent les courants; les plus anciens sont utilisés
les premiers pour éviter leur expiration (choix de répartition du logiciel).
"""
from dataclasses import dataclass
from decimal import Decimal
from .tax_rules_2025 import arrondir_cent
from .tax_federal_top_up_2025 import montant_decimal_2025

ZERO = Decimal("0")


@dataclass(frozen=True)
class ReportDonFederal2025:
    annee: int
    montant: Decimal
    source: str


@dataclass(frozen=True)
class ReportsDonsFederaux2025:
    activer: bool = False
    reports: tuple[ReportDonFederal2025, ...] = ()
    montant_reclame: Decimal = ZERO
    source: str = ""
    valide_par_comptable: bool = False
    recus_et_soldes_confirmes: bool = False
    montants_non_reclames_confirmes: bool = False
    dons_monetaires_ordinaires: bool = False
    aucun_regime_special: bool = False
    aucun_report_quebec: bool = False
    choix_reclamation_confirme: bool = False


CONFIRMATIONS_REPORTS_DONS = {
    "valide_par_comptable": "Reports et choix validés par le comptable",
    "recus_et_soldes_confirmes": "Reçus, années et soldes fédéraux vérifiés sur pièces",
    "montants_non_reclames_confirmes": "Aucun montant déjà réclamé, y compris janvier/février 2025 réclamé en 2024",
    "dons_monetaires_ordinaires": "Dons monétaires ordinaires à des donataires reconnus seulement",
    "aucun_regime_special": "Aucun décès, don en nature, écologique/culturel, régime américain ou abri fiscal",
    "aucun_report_quebec": "Aucun report Québec inclus dans ce profil fédéral",
    "choix_reclamation_confirme": "Montant de dons choisi pour 2025 confirmé; aucun crédit calculé saisi",
}


def _montant(v, libelle):
    if not isinstance(v, Decimal) or not v.is_finite() or v < ZERO:
        raise ValueError(libelle + " doit être un Decimal fini non négatif.")
    try:
        arrondi = arrondir_cent(v)
    except ArithmeticError as erreur:
        raise ValueError(libelle + " dépasse la précision monétaire prise en charge.") from erreur
    if arrondi != v:
        raise ValueError(libelle + " doit être au cent près.")
    return v


def valider_reports_dons_federaux_2025(p: ReportsDonsFederaux2025) -> ReportsDonsFederaux2025:
    if not isinstance(p, ReportsDonsFederaux2025):
        raise ValueError("Profil reports de dons invalide.")
    for nom in ("activer", *CONFIRMATIONS_REPORTS_DONS):
        if type(getattr(p, nom)) is not bool:
            raise ValueError("Confirmation non booléenne : " + nom)
    _montant(p.montant_reclame, "Dons choisis pour la réclamation")
    if not isinstance(p.source, str) or type(p.reports) is not tuple:
        raise ValueError("Source ou liste des reports invalide.")
    annees = set()
    for r in p.reports:
        if not isinstance(r, ReportDonFederal2025) or type(r.annee) is not int or not 2020 <= r.annee <= 2024:
            raise ValueError("Les reports fédéraux doivent dater de 2020 à 2024.")
        if r.annee in annees:
            raise ValueError("Année de report comptée deux fois.")
        annees.add(r.annee)
        _montant(r.montant, "Solde de dons")
        if r.montant == ZERO or not isinstance(r.source, str) or not r.source.strip():
            raise ValueError("Solde positif et source par année obligatoires.")
    if not p.activer and (p.reports or p.montant_reclame):
        raise ValueError("Activer le calcul des reports de dons.")
    if p.activer:
        if not p.source.strip():
            raise ValueError("Source du choix de réclamation obligatoire.")
        for nom, libelle in CONFIRMATIONS_REPORTS_DONS.items():
            if not getattr(p, nom):
                raise ValueError("Confirmation obligatoire : " + libelle)
    return p


@dataclass(frozen=True)
class ResultatReportsDonsFederaux2025:
    disponible: Decimal = ZERO
    plafond_75: Decimal = ZERO
    montant_reclame: Decimal = ZERO
    utilisations: tuple[tuple[int, Decimal], ...] = ()
    reports_futurs: tuple[tuple[int, Decimal], ...] = ()
    expiration_2020: Decimal = ZERO


def calculer_reports_dons_federaux_2025(p: ReportsDonsFederaux2025, *,
        dons_2025: Decimal, revenu_net: Decimal) -> ResultatReportsDonsFederaux2025:
    valider_reports_dons_federaux_2025(p)
    if not p.activer:
        return ResultatReportsDonsFederaux2025()
    courant = _montant(dons_2025, "Dons courants")
    net = montant_decimal_2025(revenu_net, "Revenu net 23600")
    disponible = courant + sum((r.montant for r in p.reports), ZERO)
    plafond = arrondir_cent(net * Decimal("0.75"))
    if p.montant_reclame > min(disponible, plafond):
        raise ValueError("La réclamation dépasse les dons disponibles ou 75 % du revenu net 23600.")
    reste = p.montant_reclame
    utilisations, reports = [], []
    expire = ZERO
    for annee, solde in sorted([(r.annee, r.montant) for r in p.reports] + [(2025, courant)]):
        utilise = min(solde, reste)
        reste -= utilise
        if utilise:
            utilisations.append((annee, utilise))
        reliquat = solde - utilise
        if annee == 2020:
            expire = reliquat
        elif reliquat:
            reports.append((annee, reliquat))
    return ResultatReportsDonsFederaux2025(disponible, plafond, p.montant_reclame,
        tuple(utilisations), tuple(reports), expire)


def lignes_reports_dons_federaux_2025(p: ReportsDonsFederaux2025, r: ResultatReportsDonsFederaux2025) -> list[str]:
    if not p.activer:
        return []
    lignes = ["", "REPORTS DE DONS FÉDÉRAUX — BLOC 5I",
        f"Choix validé par le comptable : {p.source}",
        f"Dons disponibles, courants et antérieurs : {r.disponible:.2f} $",
        f"Plafond : revenu net 23600 × 75 % = {r.plafond_75:.2f} $",
        f"Dons choisis pour la réclamation : {r.montant_reclame:.2f} $ (base du crédit 34900)"]
    lignes += [f"Solde antérieur {x.annee} : {x.montant:.2f} $; source : {x.source}" for x in p.reports]
    lignes += [f"Dons {a} utilisés : {m:.2f} $" for a, m in r.utilisations]
    lignes += [f"Dons {a} reportables après 2025 : {m:.2f} $ (dernière année : {a + 5})" for a, m in r.reports_futurs]
    return lignes + [f"Solde 2020 expirant après 2025, non reportable : {r.expiration_2020:.2f} $",
        "Répartition : anciens avant courants, plus anciens d'abord. Aucun report Québec calculé."]
