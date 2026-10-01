"""Modèle local minimal d'un dossier fiscal ComptaPrivée AI.

Phase 1 : le dossier est préparé localement et aucune transmission
gouvernementale n'est effectuée.
"""

from dataclasses import dataclass, field
from pathlib import Path
from uuid import UUID, uuid4, uuid5, NAMESPACE_URL


def valider_case_id(valeur: str) -> str:
    if not isinstance(valeur, str):
        raise ValueError("Identifiant de dossier invalide.")
    try:
        identifiant = str(UUID(valeur))
    except (ValueError, AttributeError) as exc:
        raise ValueError("Identifiant de dossier invalide.") from exc
    if valeur != identifiant:
        raise ValueError("Identifiant de dossier non canonique.")
    return identifiant


def case_id_stocke(contenu: dict, chemin: Path) -> str:
    if "case_id" in contenu:
        return valider_case_id(contenu["case_id"])
    # Migration sans ecriture : stable pour le meme ancien fichier.
    if chemin == Path("."):
        return str(uuid4())
    return str(uuid5(NAMESPACE_URL, chemin.resolve().as_uri()))


PROVINCES_PHASE_1 = ("Québec",)


@dataclass(frozen=True)
class DossierFiscal:
    client: str
    annee_fiscale: int
    province: str
    documents: tuple[Path, ...] = field(default_factory=tuple)
    case_id: str = field(default_factory=lambda: str(uuid4()), compare=False, kw_only=True)
    statut: str = "Brouillon — aucun document importé"


ANNEES_FISCALES_SUPPORTEES = (2025,)


def annee_fiscale_par_defaut(annee_courante: int | None = None) -> int:
    """L'horloge ne selectionne jamais un bareme fiscal (argument historique ignore)."""
    return 2025


def annees_fiscales_disponibles(
    annee_courante: int | None = None, *, profondeur: int = 7,
) -> tuple[int, ...]:
    """Expose uniquement les moteurs livres, independamment de l'horloge."""
    if profondeur < 1:
        raise ValueError("La profondeur doit etre d'au moins 1.")
    return ANNEES_FISCALES_SUPPORTEES[:profondeur]


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
    case_id: str | None = None,
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
        case_id=valider_case_id(case_id) if case_id is not None else str(uuid4()),
        statut=statut,
    )
