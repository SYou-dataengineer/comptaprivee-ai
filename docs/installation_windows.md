# Installation Windows depuis les sources

## Environnement de référence

- Python **3.12 64 bits**, avec `pip`, `venv` et Tcl/Tk. Référence locale validée :
  Python 3.12.10. Les autres versions Python ne sont pas déclarées supportées.
- Les dépendances directes sont fixées dans `requirements.txt`, dont Pillow 11.3.0
  déjà utilisé dans les validations. `pywin32` est installé uniquement sous Windows.
- Tesseract 5, langues `fra` et `eng`, est une dépendance externe pour l'OCR.
  Référence locale observée : Tesseract 5.5.3.20260724. Les binaires OCR ne sont pas
  embarqués ; noter la version de l'installation choisie.
- Word installé peut être nécessaire aux conversions qui utilisent son automation
  Windows ; il n'est pas requis pour lire un DOCX ni pour calculer un dossier fiscal.

## Installation Python

Installer Python 3.12 depuis [python.org](https://www.python.org/downloads/windows/)
avec Tcl/Tk. Vérifier `py -3.12 --version`. Ouvrir PowerShell dans la racine du dépôt
(clone ou archive source extraite, y compris dans un chemin avec espaces/accents).

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -c "import tkinter, fitz, docx, openpyxl, PIL; print('Imports OK')"
```

Ne pas utiliser `pip install .` comme procédure de cette version : `pyproject.toml`
porte des métadonnées et la configuration pytest, sans migration de l'installation
historique. `requirements.txt` reste la référence de l'environnement applicatif.
Les dépendances transitives et les binaires OCR ne constituent pas encore une
archive d'installation entièrement verrouillée et utilisable hors ligne.

## Installer Tesseract et les langues

Suivre la section Windows de la [documentation officielle Tesseract](https://tesseract-ocr.github.io/tessdoc/Installation.html#windows),
qui référence les distributions Windows d'UB Mannheim. Installer les données de
langues française et anglaise. Ajouter le dossier contenant `tesseract.exe` au
`PATH` utilisateur, puis ouvrir un nouveau terminal.

```powershell
Get-Command tesseract
tesseract --version
tesseract --list-langs
```

La liste doit contenir `eng` et `fra`. Si les données sont installées séparément,
configurer `TESSDATA_PREFIX` vers le dossier contenant leurs fichiers `.traineddata`.
Ce chemin dépend de l'installation de l'utilisateur ; aucun chemin du développeur
n'est nécessaire. Ne pas définir cette variable vers un dossier inexistant.

## Lancement

Toujours depuis la racine du projet :

```powershell
.\.venv\Scripts\python.exe -m src.comptaprivee.gui
```

Pour vérifier la CLI documentaire :

```powershell
.\.venv\Scripts\python.exe -m src.comptaprivee.main --help
```

L'application ne choisit que 2025 pour les calculs livrés. Ne pas utiliser un dossier
2026 avec les règles 2025, même si l'ordinateur est en 2026 ou 2027.

## Données et sauvegardes

La base, les paramètres et certains exports utilisent des chemins relatifs au
répertoire de lancement. Les dossiers fiscaux sont ancrés sur la racine du projet.
Cette asymétrie impose de lancer depuis la racine ; elle est documentée sans
changer le stockage dans cette préparation de release.

Utiliser les commandes de sauvegarde/restauration des paramètres. Choisir une
archive ZIP en dehors du dépôt. Sauvegarder aussi les pièces sources séparément.
Fermer les autres instances avant restauration. Une base avec journal/WAL/SHM
présent est refusée. Après restauration, redémarrer l'application.

Les remplacements sont atomiques par fichier, pas pour l'ensemble de l'archive en
cas de coupure électrique. Une erreur déclenche un rollback ; si celui-ci échoue,
le message indique où les copies de secours `.restore-*` ont été conservées.
Ne pas les supprimer avant récupération des données.

## Confidentialité

Pas d'envoi automatique des données fiscales, pas d'API d'IA distante dans le
parcours fiscal examiné. L'OCR et la génération des rapports s'exécutent localement.
Les JSON, SQLite, ZIP, PDF et fichiers temporaires ne sont pas chiffrés par le
logiciel. Protéger les comptes utilisateurs, le disque et les supports de sauvegarde.
Les temporaires sont nettoyés en fonctionnement normal ; un arrêt brutal peut en
laisser sur le poste. Les garanties de permissions/chiffrement dépendent du système.

`.gitignore` exclut les données applicatives, documents, exports, variables secrètes
et temporaires. Cela ne protège pas contre un ajout forcé ou une pièce copiée sous
un autre chemin : vérifier les fichiers indexés avant chaque publication.
Les documents de conformité restent des brouillons à valider avant commercialisation.

## Tests et diagnostic

```powershell
.\.venv\Scripts\python.exe -m pytest --capture=sys -q
```

Les tests GUI Windows utilisent `--capture=sys`. Pour un problème d'environnement,
conserver le message exact et vérifier Python/Tk/Tesseract avant de modifier le
produit. La CI Windows teste directement Tk et une sélection de parcours GUI ;
elle n'installe pas Tesseract. L'OCR est couvert par la CI Linux et la validation
locale Windows avec Tesseract. Une machine Windows vierge complète, hors poste de
développement, reste une validation release distincte d'un venv neuf.

### Avertissements connus

- Interne : `cell.font.copy` openpyxl remplacé par `copy.copy` puis modification
  de `bold`, sans changer les autres attributs de police.
- Externes : cinq avertissements SWIG/PyMuPDF concernant `__module__` peuvent
  rester. Ils ne sont ni masqués ni corrigés en modifiant la dépendance.
- CI : actions checkout v4/setup-python v5 signalent la transition Node 20 → 24 ;
  l'image `ubuntu-latest` annonce aussi une migration. Suivi ultérieur, sans
  changement simultané des actions dans cette session.

Source du schéma CI : [documentation GitHub Actions Python](https://docs.github.com/en/actions/tutorials/build-and-test-code/python).
