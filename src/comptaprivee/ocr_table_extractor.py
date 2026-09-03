from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MotOCR:
    texte: str
    gauche: int
    haut: int
    largeur: int
    hauteur: int
    confiance: float = 100.0

    @property
    def droite(self) -> int:
        return self.gauche + self.largeur

    @property
    def centre_x(self) -> float:
        return self.gauche + (self.largeur / 2)

    @property
    def centre_y(self) -> float:
        return self.haut + (self.hauteur / 2)


def _regrouper_mots_par_ligne(
    mots: list[MotOCR],
    tolerance_y: int = 12,
) -> list[list[MotOCR]]:
    utilisables = [
        mot for mot in mots
        if mot.texte.strip() and mot.confiance >= 0
    ]
    utilisables.sort(key=lambda mot: (mot.centre_y, mot.gauche))

    lignes: list[list[MotOCR]] = []

    for mot in utilisables:
        ajoute = False

        for ligne in lignes:
            moyenne_y = sum(m.centre_y for m in ligne) / len(ligne)

            if abs(mot.centre_y - moyenne_y) <= tolerance_y:
                ligne.append(mot)
                ajoute = True
                break

        if not ajoute:
            lignes.append([mot])

    for ligne in lignes:
        ligne.sort(key=lambda mot: mot.gauche)

    return lignes


def _detecter_separations_colonnes(
    lignes: list[list[MotOCR]],
    ecart_minimum: int = 28,
) -> list[float]:
    candidats: list[float] = []

    for ligne in lignes:
        for gauche, droite in zip(ligne, ligne[1:]):
            ecart = droite.gauche - gauche.droite

            if ecart >= ecart_minimum:
                candidats.append(
                    (gauche.droite + droite.gauche) / 2
                )

    if not candidats:
        return []

    candidats.sort()
    groupes: list[list[float]] = []

    for valeur in candidats:
        if not groupes:
            groupes.append([valeur])
            continue

        moyenne = sum(groupes[-1]) / len(groupes[-1])

        if abs(valeur - moyenne) > 24:
            groupes.append([valeur])
        else:
            groupes[-1].append(valeur)

    return [
        sum(groupe) / len(groupe)
        for groupe in groupes
        if len(groupe) >= 2
    ]


def _segmenter_ligne_cellules(
    ligne: list[MotOCR],
    ecart_minimum: int,
) -> list[list[MotOCR]]:
    if not ligne:
        return []

    cellules: list[list[MotOCR]] = [[ligne[0]]]

    for precedent, mot in zip(ligne, ligne[1:]):
        ecart = mot.gauche - precedent.droite

        if ecart >= ecart_minimum:
            cellules.append([mot])
        else:
            cellules[-1].append(mot)

    return cellules


def _ajouter_entetes_comptables_si_manquants(
    tableau: list[list[str]],
) -> list[list[str]]:
    """Ajoute des en-têtes comptables seulement quand ils sont très probables.

    Cette étape sert de filet de sécurité lorsque Tesseract reconnaît bien les
    lignes de données d'un tableau scanné mais rate la ligne d'en-tête.
    """
    import re

    if not tableau:
        return tableau

    nombre_colonnes = max(len(ligne) for ligne in tableau)

    entetes_connus = {
        7: [
            "Date",
            "Fournisseur",
            "No facture",
            "Sous-total",
            "TPS",
            "TVQ",
            "Total",
        ],
        8: [
            "Date",
            "Fournisseur",
            "No facture",
            "Sous-total",
            "TPS",
            "TVQ",
            "Total",
            "Statut",
        ],
    }

    if nombre_colonnes not in entetes_connus:
        return tableau

    premiere = [
        cellule.strip().lower()
        for cellule in tableau[0]
    ]

    marqueurs_entete = {
        "date",
        "fournisseur",
        "facture",
        "no facture",
        "sous-total",
        "subtotal",
        "tps",
        "tvq",
        "total",
        "statut",
    }

    # Une ligne de données peut contenir une valeur comme
    # "Fournisseur A". On ne doit pas la confondre avec l'en-tête
    # "Fournisseur". On utilise donc une comparaison exacte après
    # normalisation, et non une recherche par sous-chaîne.
    premiere_normalisee = {
        cellule.strip().lower().replace(":", "")
        for cellule in premiere
        if cellule.strip()
    }

    if premiere_normalisee & marqueurs_entete:
        return tableau

    date_re = re.compile(
        r"^(?:20\d{2})[-/.](?:0?[1-9]|1[0-2])[-/.](?:0?[1-9]|[12]\d|3[01])$"
    )

    def ressemble_nombre(valeur: str) -> bool:
        texte = valeur.strip()
        if not texte:
            return False

        texte = texte.replace(" ", "")
        texte = texte.replace(",", ".")

        return bool(
            re.fullmatch(
                r"[-+]?\d+(?:\.\d{1,2})?",
                texte,
            )
        )

    def ressemble_ligne_donnees(ligne: list[str]) -> bool:
        if len(ligne) < 7:
            return False

        date_ok = bool(
            date_re.fullmatch(
                ligne[0].strip()
            )
        )

        facture = ligne[2].strip().upper()
        facture_ok = bool(
            re.search(
                r"[A-Z]{2,}[- ]?[A-Z0-9]*\d",
                facture,
            )
        )

        nombres = sum(
            1
            for cellule in ligne[3:7]
            if ressemble_nombre(cellule)
        )

        return date_ok and facture_ok and nombres >= 3

    echantillon = tableau[: min(4, len(tableau))]
    lignes_probables = sum(
        1
        for ligne in echantillon
        if ressemble_ligne_donnees(ligne)
    )

    if lignes_probables < 2:
        return tableau

    entete = entetes_connus[nombre_colonnes]

    return [
        entete,
        *tableau,
    ]


def reconstruire_tableau_depuis_mots(
    mots: list[MotOCR],
    tolerance_y: int = 18,
    ecart_minimum: int = 55,
) -> list[list[str]]:
    """Reconstruit un tableau OCR en utilisant des ancres de colonnes stables.

    Les lignes de données répétées servent à apprendre la position des colonnes.
    Les autres lignes proches du tableau (par exemple l'en-tête) sont ensuite
    remappées vers ces mêmes colonnes, ce qui permet de conserver des cellules
    multi-mots comme « No facture ».
    """
    from collections import Counter
    from statistics import median

    lignes = _regrouper_mots_par_ligne(
        mots,
        tolerance_y=tolerance_y,
    )

    if len(lignes) < 2:
        return []

    lignes_cellules: list[tuple[list[MotOCR], list[list[MotOCR]]]] = []

    for ligne in lignes:
        cellules = _segmenter_ligne_cellules(
            ligne,
            ecart_minimum=ecart_minimum,
        )
        if cellules:
            lignes_cellules.append((ligne, cellules))

    comptes = Counter(
        len(cellules)
        for _, cellules in lignes_cellules
        if len(cellules) >= 2
    )

    if not comptes:
        return []

    nombre_colonnes, frequence = max(
        comptes.items(),
        key=lambda item: (item[1], item[0]),
    )

    if frequence < 2:
        return []

    references = [
        (ligne, cellules)
        for ligne, cellules in lignes_cellules
        if len(cellules) == nombre_colonnes
    ]

    if len(references) < 2:
        return []

    def centre_cellule(cellule: list[MotOCR]) -> float:
        gauche = min(mot.gauche for mot in cellule)
        droite = max(mot.droite for mot in cellule)
        return (gauche + droite) / 2

    ancres: list[float] = []

    for index_colonne in range(nombre_colonnes):
        centres = [
            centre_cellule(cellules[index_colonne])
            for _, cellules in references
        ]
        ancres.append(
            sum(centres) / len(centres)
        )

    y_references = sorted(
        sum(mot.centre_y for mot in ligne) / len(ligne)
        for ligne, _ in references
    )

    if len(y_references) >= 2:
        ecarts_y = [
            suivant - precedent
            for precedent, suivant in zip(
                y_references,
                y_references[1:],
            )
            if suivant > precedent
        ]
        pas_ligne = median(ecarts_y) if ecarts_y else 60
    else:
        pas_ligne = 60

    y_min = y_references[0] - (pas_ligne * 1.6)
    y_max = y_references[-1] + (pas_ligne * 0.75)

    tableau: list[tuple[float, list[str]]] = []

    for ligne in lignes:
        y_ligne = sum(
            mot.centre_y for mot in ligne
        ) / len(ligne)

        if not (y_min <= y_ligne <= y_max):
            continue

        cellules_ancres: list[list[MotOCR]] = [
            [] for _ in range(nombre_colonnes)
        ]

        for mot in ligne:
            index = min(
                range(nombre_colonnes),
                key=lambda i: abs(
                    mot.centre_x - ancres[i]
                ),
            )
            cellules_ancres[index].append(mot)

        valeurs: list[str] = []
        occupees = 0

        for cellule in cellules_ancres:
            cellule.sort(key=lambda mot: mot.gauche)
            valeur = " ".join(
                mot.texte.strip()
                for mot in cellule
                if mot.texte.strip()
            ).strip()

            if valeur:
                occupees += 1

            valeurs.append(valeur)

        minimum_occupees = max(
            2,
            nombre_colonnes - 2,
        )

        if occupees >= minimum_occupees:
            tableau.append(
                (y_ligne, valeurs)
            )

    tableau.sort(key=lambda item: item[0])

    lignes_finales = [
        valeurs
        for _, valeurs in tableau
    ]

    if len(lignes_finales) < 2:
        return []

    return _ajouter_entetes_comptables_si_manquants(
        lignes_finales
    )


def _pretraiter_image_tableau(
    chemin_image: str,
) -> str:
    # Supprime les longues lignes horizontales / verticales avec Pillow
    # uniquement. Cela évite la dépendance OpenCV sous Windows.
    import tempfile

    try:
        from PIL import Image
    except ImportError as erreur:
        raise RuntimeError(
            "Pillow est requis pour le prétraitement des tableaux scannés."
        ) from erreur

    source = Path(chemin_image)

    if not source.exists():
        raise FileNotFoundError(
            f"Image introuvable : {source}"
        )

    try:
        image = Image.open(source).convert("L")
    except Exception as erreur:
        # Si une image de test / mock n'est pas décodable,
        # laisser le moteur OCR travailler directement dessus.
        return str(source)

    largeur, hauteur = image.size
    pixels = image.load()

    seuil_noir = 180

    # Détecter les longues lignes horizontales.
    lignes_h: list[int] = []
    seuil_h = max(30, int(largeur * 0.22))

    for y in range(hauteur):
        nb_noirs = 0
        for x in range(largeur):
            if pixels[x, y] < seuil_noir:
                nb_noirs += 1

        if nb_noirs >= seuil_h:
            lignes_h.append(y)

    # Détecter les longues lignes verticales.
    lignes_v: list[int] = []
    seuil_v = max(30, int(hauteur * 0.22))

    for x in range(largeur):
        nb_noirs = 0
        for y in range(hauteur):
            if pixels[x, y] < seuil_noir:
                nb_noirs += 1

        if nb_noirs >= seuil_v:
            lignes_v.append(x)

    # Effacer avec une petite marge pour retirer l'épaisseur des traits.
    for y in lignes_h:
        for yy in range(max(0, y - 2), min(hauteur, y + 3)):
            for x in range(largeur):
                pixels[x, yy] = 255

    for x in lignes_v:
        for xx in range(max(0, x - 2), min(largeur, x + 3)):
            for y in range(hauteur):
                pixels[xx, y] = 255

    with tempfile.NamedTemporaryFile(
        suffix=".png",
        delete=False,
    ) as fichier_temp:
        destination = Path(fichier_temp.name)

    image.save(destination)

    return str(destination)


def extraire_mots_image_tesseract(
    chemin_image: str,
    *,
    langues: str = "fra+eng",
) -> list[MotOCR]:
    """Extrait les mots OCR et leurs coordonnées via Tesseract TSV."""
    import csv
    import io
    import os
    import shutil
    import subprocess
    from pathlib import Path

    image = Path(chemin_image)

    if not image.exists():
        raise FileNotFoundError(
            f"Image introuvable : {image}"
        )

    executable = (
        os.environ.get("TESSERACT_CMD")
        or shutil.which("tesseract")
    )

    if not executable:
        raise RuntimeError(
            "Tesseract OCR est introuvable. "
            "Installez Tesseract ou définissez TESSERACT_CMD."
        )

    commande = [
        executable,
        str(image),
        "stdout",
        "-l",
        langues,
        "--psm",
        "11",
        "-c",
        "preserve_interword_spaces=1",
        "-c",
        "tessedit_create_tsv=1",
    ]

    resultat = subprocess.run(
        commande,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    if resultat.returncode != 0:
        message = (
            resultat.stderr.strip()
            or "Erreur OCR Tesseract inconnue."
        )
        raise RuntimeError(
            f"Échec de Tesseract OCR : {message}"
        )

    lecteur = csv.DictReader(
        io.StringIO(resultat.stdout),
        delimiter="\t",
    )

    mots: list[MotOCR] = []

    for ligne in lecteur:
        texte = (ligne.get("text") or "").strip()

        if not texte:
            continue

        try:
            confiance = float(ligne.get("conf") or -1)
            gauche = int(ligne.get("left") or 0)
            haut = int(ligne.get("top") or 0)
            largeur = int(ligne.get("width") or 0)
            hauteur = int(ligne.get("height") or 0)
        except (TypeError, ValueError):
            continue

        if confiance < 0:
            continue

        mots.append(
            MotOCR(
                texte=texte,
                gauche=gauche,
                haut=haut,
                largeur=largeur,
                hauteur=hauteur,
                confiance=confiance,
            )
        )

    return mots


def extraire_tableau_image_tesseract(
    chemin_image: str,
    *,
    langues: str = "fra+eng",
    tolerance_y: int = 12,
    ecart_minimum: int = 28,
) -> list[list[str]]:
    """OCR + reconstruction d'un tableau depuis une image scannée."""
    import os

    image_pretraitee = _pretraiter_image_tableau(
        chemin_image,
    )

    try:
        mots = extraire_mots_image_tesseract(
            image_pretraitee,
            langues=langues,
        )

        return reconstruire_tableau_depuis_mots(
            mots,
            tolerance_y=tolerance_y,
            ecart_minimum=ecart_minimum,
        )

    finally:
        try:
            os.unlink(image_pretraitee)
        except OSError:
            pass
