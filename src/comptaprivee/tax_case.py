"""Modèle local minimal d'un dossier fiscal ComptaPrivée AI.

Phase 1 : le dossier est préparé localement et aucune transmission
gouvernementale n'est effectuée.
"""

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path


PROVINCES_PHASE_1 = ("Québec",)


@dataclass(frozen=True)
class DossierFiscal:
    client: str
    annee_fiscale: int
    province: str
    documents: tuple[Path, ...] = field(default_factory=tuple)
    statut: str = "Brouillon — aucun document importé"


def annee_fiscale_par_defaut(
    annee_courante: int | None = None,
) -> int:
    """Utilise par défaut la dernière année civile terminée."""
    annee = annee_courante or date.today().year
    return annee - 1


def annees_fiscales_disponibles(
    annee_courante: int | None = None,
    *,
    profondeur: int = 7,
) -> tuple[int, ...]:
    """Retourne les années proposées dans l'interface."""
    if profondeur < 1:
        raise ValueError("La profondeur doit être d'au moins 1.")

    annee = annee_courante or date.today().year
    return tuple(range(annee, annee - profondeur, -1))


def normaliser_province(province: str) -> str:
    """Normalise la province prise en charge pendant la Phase 1."""
    valeur = province.strip().casefold()

    if valeur in {"québec", "quebec", "qc"}:
        return "Québec"

    raise ValueError(
        "Phase 1 : seul le Québec est pris en charge."
    )


def creer_dossier_fiscal(
    *,
    client: str,
    annee_fiscale: int | str,
    province: str = "Québec",
    documents=(),
) -> DossierFiscal:
    """Crée un dossier fiscal local après validation minimale."""
    client_normalise = " ".join(client.split())

    if not client_normalise:
        raise ValueError("Le nom du client est obligatoire.")

    try:
        annee = int(annee_fiscale)
    except (TypeError, ValueError) as erreur:
        raise ValueError(
            "L'année fiscale doit être un nombre valide."
        ) from erreur

    if annee < 2000 or annee > 2100:
        raise ValueError(
            "L'année fiscale doit être comprise entre 2000 et 2100."
        )

    province_normalisee = normaliser_province(province)

    chemins = tuple(Path(document) for document in documents)

    if chemins:
        statut = (
            f"Brouillon — {len(chemins)} document(s) importé(s)"
        )
    else:
        statut = "Brouillon — aucun document importé"

    return DossierFiscal(
        client=client_normalise,
        annee_fiscale=annee,
        province=province_normalisee,
        documents=chemins,
        statut=statut,
    )
