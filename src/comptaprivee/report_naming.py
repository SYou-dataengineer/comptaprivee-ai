"""Nommage professionnel des fichiers de rapports."""

import re
import unicodedata
from datetime import date


def nettoyer_nom_fichier(valeur: str) -> str:
    texte = unicodedata.normalize("NFKD", valeur or "")
    texte = "".join(
        c for c in texte if not unicodedata.combining(c)
    )
    texte = re.sub(r"[^A-Za-z0-9]+", "_", texte)
    return texte.strip("_") or "Cabinet"


def nom_fichier_rapport(
    societe: str,
    type_rapport: str,
    extension: str,
    *,
    date_debut: str | None = None,
    date_fin: str | None = None,
    date_reference: date | None = None,
) -> str:
    cabinet = nettoyer_nom_fichier(societe)
    rapport = nettoyer_nom_fichier(type_rapport)

    debut = (date_debut or "").strip()
    fin = (date_fin or "").strip()

    if debut and fin:
        periode = f"{debut}_au_{fin}"
    elif debut:
        periode = f"depuis_{debut}"
    elif fin:
        periode = f"jusquau_{fin}"
    else:
        reference = date_reference or date.today()
        periode = reference.isoformat()

    suffixe = extension.strip().lower().lstrip(".")
    if not suffixe:
        raise ValueError("Une extension de fichier est requise.")

    return f"{cabinet}_{rapport}_{periode}.{suffixe}"
