"""Paramètres locaux de ComptaPrivée AI."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path


CHEMIN_PARAMETRES_PAR_DEFAUT = Path("data") / "parametres.json"

DEVISES = ("CAD", "USD", "EUR")
LANGUES_RAPPORTS = ("Français", "English")
FORMATS_DATE = ("AAAA-MM-JJ", "JJ-MM-AAAA", "MM-JJ-AAAA")
COULEUR_PDF_PAR_DEFAUT = "#1A408C"


@dataclass(frozen=True)
class ParametresApplication:
    """Préférences locales de l'application."""

    devise: str = "CAD"
    langue_rapports: str = "Français"
    format_date: str = "AAAA-MM-JJ"
    couleur_pdf: str = COULEUR_PDF_PAR_DEFAUT


def normaliser_couleur_hex(valeur: str) -> str:
    """Valide et normalise une couleur hexadécimale #RRGGBB."""
    couleur = valeur.strip().upper()

    if len(couleur) != 7 or not couleur.startswith("#"):
        raise ValueError(
            "La couleur doit être au format #RRGGBB."
        )

    try:
        int(couleur[1:], 16)
    except ValueError as erreur:
        raise ValueError(
            "La couleur doit être au format #RRGGBB."
        ) from erreur

    return couleur


def valider_parametres(
    parametres: ParametresApplication,
) -> ParametresApplication:
    """Valide les préférences avant enregistrement."""
    if parametres.devise not in DEVISES:
        raise ValueError("Devise non prise en charge.")

    if parametres.langue_rapports not in LANGUES_RAPPORTS:
        raise ValueError("Langue de rapport non prise en charge.")

    if parametres.format_date not in FORMATS_DATE:
        raise ValueError("Format de date non pris en charge.")

    return ParametresApplication(
        devise=parametres.devise,
        langue_rapports=parametres.langue_rapports,
        format_date=parametres.format_date,
        couleur_pdf=normaliser_couleur_hex(
            parametres.couleur_pdf
        ),
    )


def lire_parametres(
    chemin: str | Path = CHEMIN_PARAMETRES_PAR_DEFAUT,
) -> ParametresApplication:
    """Charge les paramètres locaux ou retourne les valeurs par défaut."""
    fichier = Path(chemin)

    if not fichier.exists():
        return ParametresApplication()

    try:
        donnees = json.loads(
            fichier.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError):
        return ParametresApplication()

    if not isinstance(donnees, dict):
        return ParametresApplication()

    def texte(cle: str, defaut: str) -> str:
        valeur = donnees.get(cle, defaut)
        return str(valeur or defaut).strip()

    candidats = ParametresApplication(
        devise=texte("devise", "CAD"),
        langue_rapports=texte(
            "langue_rapports",
            "Français",
        ),
        format_date=texte(
            "format_date",
            "AAAA-MM-JJ",
        ),
        couleur_pdf=texte(
            "couleur_pdf",
            COULEUR_PDF_PAR_DEFAUT,
        ),
    )

    try:
        return valider_parametres(candidats)
    except ValueError:
        return ParametresApplication()


def enregistrer_parametres(
    parametres: ParametresApplication,
    chemin: str | Path = CHEMIN_PARAMETRES_PAR_DEFAUT,
) -> Path:
    """Enregistre les paramètres uniquement sur l'ordinateur local."""
    valides = valider_parametres(parametres)

    fichier = Path(chemin)
    fichier.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fichier.write_text(
        json.dumps(
            asdict(valides),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return fichier

def couleur_hex_vers_pdf(valeur: str) -> tuple[float, float, float]:
    """Convertit #RRGGBB vers les composantes 0..1 de PyMuPDF."""
    couleur = normaliser_couleur_hex(valeur)
    return tuple(
        int(couleur[index:index + 2], 16) / 255
        for index in (1, 3, 5)
    )


def formater_date_rapport(
    valeur: str | None,
    format_date: str,
) -> str:
    """Formate une date ISO pour les rapports sans modifier les données."""
    if not valeur:
        return "Toutes"

    morceaux = valeur.split("-")

    if len(morceaux) != 3:
        return valeur

    annee, mois, jour = morceaux

    if format_date == "JJ-MM-AAAA":
        return f"{jour}-{mois}-{annee}"

    if format_date == "MM-JJ-AAAA":
        return f"{mois}-{jour}-{annee}"

    return valeur


TEXTES_RAPPORT = {
    "Français": {
        "resume": "RESUME COMPTABLE",
        "periode": "PERIODE ANALYSEE",
        "toutes_periodes": "Toutes les périodes",
        "toutes": "Toutes",
        "au": "au",
        "factures": "FACTURES",
        "sous_total": "SOUS-TOTAL",
        "total": "TOTAL",
        "fournisseur_principal": "FOURNISSEUR PRINCIPAL",
        "controle_anomalies": "CONTROLE DES ANOMALIES",
        "aucune_anomalie": "Aucune anomalie detectee",
        "anomalies": "anomalie(s) detectee(s)",
        "traitement_local": (
            "Traitement local - aucune donnee envoyee sur Internet"
        ),
        "dashboard": "Rapport du tableau de bord comptable",
        "date_debut": "Date debut",
        "date_fin": "Date fin",
        "fournisseur": "Fournisseur",
        "tous_fournisseurs": "Tous les fournisseurs",
        "indicateurs": "Indicateurs",
        "totaux_fournisseur": "Totaux par fournisseur",
        "aucune_facture": (
            "Aucune facture pour les filtres selectionnes."
        ),
    },
    "English": {
        "resume": "ACCOUNTING SUMMARY",
        "periode": "PERIOD ANALYZED",
        "toutes_periodes": "All periods",
        "toutes": "All",
        "au": "to",
        "factures": "INVOICES",
        "sous_total": "SUBTOTAL",
        "total": "TOTAL",
        "fournisseur_principal": "MAIN SUPPLIER",
        "controle_anomalies": "ANOMALY CHECK",
        "aucune_anomalie": "No anomaly detected",
        "anomalies": "anomaly/anomalies detected",
        "traitement_local": (
            "Local processing - no data sent to the Internet"
        ),
        "dashboard": "Accounting dashboard report",
        "date_debut": "Start date",
        "date_fin": "End date",
        "fournisseur": "Supplier",
        "tous_fournisseurs": "All suppliers",
        "indicateurs": "Indicators",
        "totaux_fournisseur": "Totals by supplier",
        "aucune_facture": "No invoice for the selected filters.",
    },
}


def texte_rapport(cle: str, langue: str) -> str:
    """Retourne un libellé de rapport dans la langue configurée."""
    dictionnaire = TEXTES_RAPPORT.get(
        langue,
        TEXTES_RAPPORT["Français"],
    )
    return dictionnaire.get(
        cle,
        TEXTES_RAPPORT["Français"].get(cle, cle),
    )
