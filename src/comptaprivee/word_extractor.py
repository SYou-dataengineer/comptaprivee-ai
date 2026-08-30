"""Extraction locale du texte des documents Microsoft Word DOCX."""

from pathlib import Path
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile


ESPACE_NOM_WORD = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
}


def extraire_texte_word(chemin_fichier: str | Path) -> str:
    """Extrait localement le texte d'un document Word DOCX."""
    chemin = Path(chemin_fichier)

    if chemin.suffix.lower() != ".docx":
        raise ValueError("Le fichier doit être au format DOCX.")

    if not chemin.exists():
        raise FileNotFoundError(f"Fichier introuvable : {chemin}")

    try:
        with ZipFile(chemin) as archive:
            contenu_xml = archive.read("word/document.xml")
    except (BadZipFile, KeyError) as erreur:
        raise ValueError("Le document Word est invalide.") from erreur

    try:
        racine = ElementTree.fromstring(contenu_xml)
    except ElementTree.ParseError as erreur:
        raise ValueError("Le contenu XML du document Word est invalide.") from erreur

    paragraphes: list[str] = []

    for paragraphe in racine.findall(".//w:p", ESPACE_NOM_WORD):
        fragments = [
            noeud.text or ""
            for noeud in paragraphe.findall(".//w:t", ESPACE_NOM_WORD)
        ]
        texte = "".join(fragments).strip()

        if texte:
            paragraphes.append(texte)

    return "\n".join(paragraphes)