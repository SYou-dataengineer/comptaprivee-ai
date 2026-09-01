"""Profil local du cabinet comptable."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path


CHEMIN_PROFIL_PAR_DEFAUT = Path("data") / "profil_comptable.json"


@dataclass(frozen=True)
class ProfilSociete:
    """Coordonnées locales du cabinet comptable."""

    nom_societe: str = ""
    adresse: str = ""
    ville: str = ""
    province: str = ""
    code_postal: str = ""
    telephone: str = ""
    courriel: str = ""
    site_web: str = ""
    neq: str = ""
    numero_tps: str = ""
    numero_tvq: str = ""


def lire_profil_societe(
    chemin: str | Path = CHEMIN_PROFIL_PAR_DEFAUT,
) -> ProfilSociete:
    """Retourne le profil société enregistré localement."""
    fichier = Path(chemin)

    if not fichier.exists():
        return ProfilSociete()

    try:
        donnees = json.loads(
            fichier.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError):
        return ProfilSociete()

    if not isinstance(donnees, dict):
        return ProfilSociete()

    champs = ProfilSociete.__dataclass_fields__.keys()

    valeurs = {
        champ: str(donnees.get(champ, "") or "").strip()
        for champ in champs
    }

    return ProfilSociete(**valeurs)


def enregistrer_profil_societe(
    profil: ProfilSociete,
    chemin: str | Path = CHEMIN_PROFIL_PAR_DEFAUT,
) -> Path:
    """Enregistre localement le profil complet de la société."""
    if not profil.nom_societe.strip():
        raise ValueError(
            "Le nom de la société ne peut pas être vide."
        )

    fichier = Path(chemin)
    fichier.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fichier.write_text(
        json.dumps(
            asdict(profil),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return fichier


def lire_nom_societe(
    chemin: str | Path = CHEMIN_PROFIL_PAR_DEFAUT,
) -> str:
    """Retourne seulement le nom de société."""
    return lire_profil_societe(chemin).nom_societe


def enregistrer_nom_societe(
    nom_societe: str,
    chemin: str | Path = CHEMIN_PROFIL_PAR_DEFAUT,
) -> Path:
    """Compatibilité : enregistre seulement le nom de société."""
    ancien = lire_profil_societe(chemin)

    profil = ProfilSociete(
        nom_societe=nom_societe.strip(),
        adresse=ancien.adresse,
        ville=ancien.ville,
        province=ancien.province,
        code_postal=ancien.code_postal,
        telephone=ancien.telephone,
        courriel=ancien.courriel,
        site_web=ancien.site_web,
        neq=ancien.neq,
        numero_tps=ancien.numero_tps,
        numero_tvq=ancien.numero_tvq,
    )

    return enregistrer_profil_societe(
        profil,
        chemin,
    )


def lignes_coordonnees(
    profil: ProfilSociete,
) -> list[str]:
    """Prépare des lignes compactes pour les rapports PDF."""
    lignes: list[str] = []

    localisation = ", ".join(
        partie
        for partie in (
            profil.ville,
            profil.province,
            profil.code_postal,
        )
        if partie
    )

    if profil.adresse:
        lignes.append(profil.adresse)

    if localisation:
        lignes.append(localisation)

    contacts = " | ".join(
        partie
        for partie in (
            profil.telephone,
            profil.courriel,
        )
        if partie
    )

    if contacts:
        lignes.append(contacts)

    if profil.site_web:
        lignes.append(profil.site_web)

    inscriptions = " | ".join(
        libelle
        for libelle in (
            f"NEQ {profil.neq}" if profil.neq else "",
            f"TPS {profil.numero_tps}" if profil.numero_tps else "",
            f"TVQ {profil.numero_tvq}" if profil.numero_tvq else "",
        )
        if libelle
    )

    if inscriptions:
        lignes.append(inscriptions)

    return lignes
