"""Sauvegardes locales à destinations bornées et restauration avec rollback."""
from __future__ import annotations

from contextlib import closing
import hashlib
import json
import os
import shutil
import sqlite3
import stat
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath

from .database import CHEMIN_BASE_PAR_DEFAUT

DOSSIER_DATA = Path("data")
FICHIER_PARAMETRES = DOSSIER_DATA / "parametres.json"
FICHIER_PROFIL = DOSSIER_DATA / "profil_comptable.json"
VERSION_MANIFESTE = 1
MAX_FICHIER = 128 * 1024 * 1024
MAX_TOTAL = 512 * 1024 * 1024
MAX_ENTREES = 10000
FIXES = {
    "data/comptaprivee.db": "base_comptable",
    "data/parametres.json": "parametres_utilisateurs",
    "data/profil_comptable.json": "profil_utilisateur",
}


def _categorie(nom: str) -> str:
    if not isinstance(nom, str) or not nom or "\\" in nom or ":" in nom or "\x00" in nom:
        raise ValueError("Chemin de sauvegarde interdit.")
    p = PurePosixPath(nom)
    if p.is_absolute() or p.as_posix() != nom or any(v in {".", ".."} or v.endswith((".", " ")) for v in p.parts):
        raise ValueError("Chemin de sauvegarde interdit.")
    if nom in FIXES:
        return FIXES[nom]
    if len(p.parts) == 3 and p.parts[:2] == ("data", "dossiers_fiscaux") and p.suffix == ".json":
        base = p.name.split('.')[0].upper()
        if base not in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(10)), *(f"LPT{i}" for i in range(10))}:
            return "donnees_fiscales"
    raise ValueError("Destination non autorisée dans la sauvegarde.")


def _destination(racine: Path, nom: str) -> Path:
    _categorie(nom)
    cible = racine / nom
    for composant in (cible, *cible.parents):
        if composant.is_symlink() or getattr(composant, "is_junction", lambda: False)():
            raise ValueError("Lien ou jonction interdit dans la destination.")
    if not cible.resolve().is_relative_to(racine.resolve()):
        raise ValueError("Destination hors de la racine.")
    return cible


def _chemin_est_sur(membre: zipfile.ZipInfo) -> bool:
    try:
        _categorie(membre.filename)
        return not membre.is_dir() and stat.S_IFMT(membre.external_attr >> 16) in (0, stat.S_IFREG)
    except ValueError:
        return False


def _fichiers_a_sauvegarder() -> list[Path]:
    # Le stockage fiscal est ancré au projet, contrairement aux anciennes données.
    from .tax_case_storage import DOSSIERS_FISCAUX_DIR
    fichiers = [Path(n) for n in FIXES if Path(n).exists()]
    if DOSSIERS_FISCAUX_DIR.exists():
        fichiers.extend(sorted(DOSSIERS_FISCAUX_DIR.glob("*.json")))
    return fichiers


def _nom_archive(chemin: Path) -> str:
    if chemin.is_absolute():
        return "data/dossiers_fiscaux/" + chemin.name
    return chemin.as_posix()


def _valider_contenu(chemin: Path, nom: str) -> None:
    try:
        if nom.endswith(".json"):
            contenu = json.loads(chemin.read_text(encoding="utf-8"))
            if not isinstance(contenu, dict):
                raise ValueError("Objet JSON requis.")
            if _categorie(nom) == "donnees_fiscales":
                from .tax_case_storage import dossier_fiscal_depuis_contenu
                dossier_fiscal_depuis_contenu(contenu, chemin=chemin, verifier_documents=False)
        else:
            with closing(sqlite3.connect(chemin.resolve().as_uri() + "?mode=ro", uri=True)) as connexion:
                if connexion.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                    raise ValueError("Base SQLite invalide.")
    except (ValueError, OSError, sqlite3.Error) as exc:
        raise ValueError(f"Contenu de sauvegarde invalide : {nom}") from exc


def creer_sauvegarde(destination: str | Path) -> Path:
    destination = Path(destination)
    if destination.suffix.lower() != ".zip":
        raise ValueError("Le fichier de sauvegarde doit avoir l'extension .zip.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent, prefix=".backup-") as temporaire:
        temp = Path(temporaire)
        entrees = []
        archive_temp = temp / "sauvegarde.zip"
        with zipfile.ZipFile(archive_temp, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            total = 0
            for index, fichier in enumerate(_fichiers_a_sauvegarder()):
                nom = _nom_archive(fichier)
                categorie = _categorie(nom)
                # Refuser aussi les liens dans les parents des sources.
                for parent in (fichier, *fichier.parents):
                    if parent.is_symlink() or getattr(parent, "is_junction", lambda: False)():
                        raise ValueError("Source liée interdite.")
                copie = temp / str(index)
                if nom == "data/comptaprivee.db":
                    with closing(sqlite3.connect(fichier.resolve().as_uri() + "?mode=ro", uri=True)) as origine, closing(sqlite3.connect(copie)) as sortie:
                        origine.backup(sortie)
                else:
                    shutil.copyfile(fichier, copie)
                _valider_contenu(copie, nom)
                taille = copie.stat().st_size
                total += taille
                if taille > MAX_FICHIER or total > MAX_TOTAL or index >= MAX_ENTREES:
                    raise ValueError("Sauvegarde trop volumineuse.")
                contenu = copie.read_bytes()
                entrees.append(dict(chemin=nom, categorie=categorie, taille=taille, sha256=hashlib.sha256(contenu).hexdigest()))
                archive.writestr(nom, contenu)
            archive.writestr("manifest.json", json.dumps(dict(version=VERSION_MANIFESTE, application="ComptaPrivée AI", cree_le=datetime.now().isoformat(timespec="seconds"), fichiers=entrees), ensure_ascii=False))
        os.replace(archive_temp, destination)
    return destination


def _lire_archive(archive, nom):
    try:
        return archive.read(nom)
    except (zipfile.BadZipFile, RuntimeError, EOFError) as exc:
        raise ValueError("Contenu ZIP corrompu.") from exc


def _valider_archive(archive: zipfile.ZipFile) -> list[dict]:
    membres = archive.infolist()
    if any(stat.S_IFMT(m.external_attr >> 16) not in (0, stat.S_IFREG) for m in membres):
        raise ValueError("Lien ou type special interdit dans une archive.")
    noms = [m.filename for m in membres]
    if len(membres) > MAX_ENTREES + 1 or len({n.casefold() for n in noms}) != len(noms) or noms.count("manifest.json") != 1:
        raise ValueError("Archive invalide : entrées dupliquées ou manifeste absent.")
    if any(m.file_size > MAX_FICHIER or m.flag_bits & 1 for m in membres) or sum(m.file_size for m in membres) > MAX_TOTAL:
        raise ValueError("Archive trop volumineuse ou chiffrée.")
    if archive.getinfo("manifest.json").file_size > 2 * 1024 * 1024:
        raise ValueError("Manifeste trop volumineux.")
    try:
        manifeste = json.loads(_lire_archive(archive, "manifest.json"))
    except (ValueError, UnicodeError) as exc:
        raise ValueError("Manifeste invalide.") from exc
    if not isinstance(manifeste, dict) or manifeste.get("application") != "ComptaPrivée AI" or not isinstance(manifeste.get("cree_le"), str) or not isinstance(manifeste.get("fichiers"), list):
        raise ValueError("Structure de manifeste invalide.")
    version = manifeste.get("version", 0)
    if type(version) is not int or version not in (0, VERSION_MANIFESTE):
        raise ValueError("Version de manifeste inconnue.")
    autorises = {"application", "cree_le", "fichiers"} | ({"version"} if version else set())
    if set(manifeste) != autorises:
        raise ValueError("Champs de manifeste inconnus.")
    entrees = manifeste["fichiers"]
    if version == 0:
        # Ancien format effectivement émis : seulement les trois fichiers fixes.
        if any(not isinstance(n, str) or n not in FIXES for n in entrees):
            raise ValueError("Ancien manifeste invalide.")
        entrees = [dict(chemin=n, categorie=FIXES[n]) for n in entrees]
    chemins = []
    for entree in entrees:
        if not isinstance(entree, dict) or set(entree) != ({"chemin", "categorie", "taille", "sha256"} if version else {"chemin", "categorie"}):
            raise ValueError("Entrée de manifeste invalide.")
        nom = entree["chemin"]
        if entree["categorie"] != _categorie(nom) or nom not in noms or not _chemin_est_sur(archive.getinfo(nom)):
            raise ValueError("Entrée non autorisée.")
        if version and (type(entree["taille"]) is not int or entree["taille"] != archive.getinfo(nom).file_size or not isinstance(entree["sha256"], str) or len(entree["sha256"]) != 64):
            raise ValueError("Taille ou empreinte invalide.")
        chemins.append(nom)
    if len(set(chemins)) != len(chemins) or set(noms) != {"manifest.json", *chemins}:
        raise ValueError("Archive et manifeste différents.")
    return entrees


def restaurer_sauvegarde(source: str | Path, *, racine: str | Path = ".") -> list[Path]:
    source, racine = Path(source), Path(racine)
    if not source.exists():
        raise FileNotFoundError(f"Sauvegarde introuvable : {source}")
    if source.suffix.lower() != ".zip":
        raise ValueError("La sauvegarde doit être un fichier .zip.")
    try:
        archive_source = zipfile.ZipFile(source)
    except zipfile.BadZipFile as exc:
        raise ValueError("Archive ZIP invalide.") from exc
    # Première phase : aucun changement de données avant validation intégrale.
    with tempfile.TemporaryDirectory(prefix="comptaprivee-validation-") as validation:
        with archive_source as archive:
            entrees = _valider_archive(archive)
            cibles = [_destination(racine, e["chemin"]) for e in entrees]
            for index, entree in enumerate(entrees):
                copie = Path(validation) / str(index)
                contenu = _lire_archive(archive, entree["chemin"])
                if "sha256" in entree and hashlib.sha256(contenu).hexdigest() != entree["sha256"]:
                    raise ValueError("Empreinte de sauvegarde incorrecte.")
                copie.write_bytes(contenu)
                _valider_contenu(copie, entree["chemin"])
        racine.mkdir(parents=True, exist_ok=True)
        # Staging et copies de secours sur le même volume que les destinations.
        transaction = Path(tempfile.mkdtemp(prefix=".restore-", dir=racine))
        modifies = []
        repertoires = []
        conserver = False
        try:
            for index, cible in enumerate(cibles):
                _destination(racine, entrees[index]["chemin"])
                if cible.name == "comptaprivee.db" and any(Path(str(cible) + suffixe).exists() for suffixe in ("-wal", "-shm", "-journal")):
                    raise ValueError("Base active : fermez les autres acces avant restauration.")
                if cible.exists():
                    if not cible.is_file():
                        raise ValueError("Destination non régulière.")
                    if entrees[index]["categorie"] == "donnees_fiscales":
                        from .tax_case import case_id_stocke
                        ancien_json = json.loads(cible.read_text(encoding="utf-8"))
                        nouveau_json = json.loads((Path(validation) / str(index)).read_text(encoding="utf-8"))
                        if not isinstance(ancien_json, dict) or case_id_stocke(ancien_json, cible) != case_id_stocke(nouveau_json, cible):
                            raise ValueError("Restauration refusee : case_id different du dossier existant.")
                    shutil.copy2(cible, transaction / f"ancien-{index}")
                shutil.copy2(Path(validation) / str(index), transaction / f"nouveau-{index}")
            for index, cible in enumerate(cibles):
                _destination(racine, entrees[index]["chemin"])
                parents = []
                parent = cible.parent
                while not parent.exists():
                    parents.append(parent)
                    parent = parent.parent
                for parent in reversed(parents):
                    parent.mkdir()
                    repertoires.append(parent)
                os.replace(transaction / f"nouveau-{index}", cible)
                modifies.append((index, cible))
        except BaseException:
            try:
                for index, cible in reversed(modifies):
                    ancien = transaction / f"ancien-{index}"
                    if ancien.exists():
                        os.replace(ancien, cible)
                    else:
                        cible.unlink()
                for parent in reversed(repertoires):
                    parent.rmdir()
            except BaseException as exc:
                conserver = True
                raise RuntimeError(f"Rollback incomplet : copies de secours conservées dans {transaction}") from exc
            raise
        finally:
            if not conserver:
                shutil.rmtree(transaction)
    return cibles
