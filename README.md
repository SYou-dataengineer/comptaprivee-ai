# ComptaPrivée AI
[![Tests Python](https://github.com/SYou-dataengineer/comptaprivee-ai/actions/workflows/tests.yml/badge.svg)](https://github.com/SYou-dataengineer/comptaprivee-ai/actions/workflows/tests.yml)

Agent local d’extraction de données depuis des documents comptables.

## Objectif

ComptaPrivée AI aide les comptables à extraire et à valider les données provenant de fichiers PDF, Word et d’images numérisées.

## Confidentialité

- Traitement local des documents
- Aucune donnée cliente envoyée sur Internet
- Documents et exportations exclus du dépôt Git
- Validation humaine avant l’exportation

## État du projet

Première phase :

- environnement Python 3.12 configuré;
- structure initiale créée;
- protection des documents confidentiels configurée;
- premier test automatique réussi.
- extraction locale du texte des fichiers PDF;
- validation du format et des fichiers introuvables;
- quatre tests automatiques réussis.
- interface en ligne de commande;
- facture PDF fictive pour la démonstration;
- chaîne complète d’extraction validée par cinq tests.
- extraction structurée des factures;
- détection du numéro, de la date, du fournisseur et du client;
- extraction du sous-total, de la TPS, de la TVQ et du total;
- prise en charge des montants avec un point ou une virgule.
- export local des données au format CSV;
- compatibilité avec Excel grâce à l’encodage UTF-8;
- protection automatique des fichiers exportés;
- pipeline PDF vers CSV validé par dix tests.
- lecture locale des documents Microsoft Word DOCX;
- lecteur Word pur Python, sans DLL externe;
- prise en charge des documents PDF et Word;
- pipeline Word vers CSV validé automatiquement;
- quatorze tests automatiques réussis.
- OCR local avec Tesseract 5.5.3;
- reconnaissance en français et en anglais;
- prise en charge des images PNG, JPG, JPEG, TIFF et BMP;
- extraction structurée et export CSV depuis une image;
- dix-sept tests automatiques réussis.
- détection automatique des pages PDF sans texte;
- OCR automatique des PDF numérisés;
- traitement mixte des PDF contenant du texte et des pages scannées;
- suppression automatique des images OCR temporaires;
- dix-huit tests automatiques réussis.
- interface graphique Windows entièrement locale;
- sélection de documents PDF, Word et images;
- affichage du texte extrait;
- champs comptables modifiables avant validation;
- export CSV contrôlé par l’utilisateur;
- vingt-six tests automatiques réussis.
## Lancer le programme

Sans document :

```powershell
python -m src.comptaprivee.main
```

Afficher l’aide :

```powershell
python -m src.comptaprivee.main --help
```

## Démonstration avec une facture fictive

Générer la facture :

```powershell
python scripts\creer_facture_demo.py
```

Analyser la facture localement :

```powershell
python -m src.comptaprivee.main data\documents\facture_demo.pdf
```

Le PDF généré est fictif et demeure exclu du dépôt Git.

Exporter les données vers un CSV local :

```powershell
python -m src.comptaprivee.main data\documents\facture_demo.pdf --export-csv data\exports\facture_demo.csv
```
## Démonstration avec un document Word

Générer une facture Word fictive :

```powershell
python scripts\creer_word_demo.py
```

Analyser le document et exporter les données :

```powershell
python -m src.comptaprivee.main data\documents\facture_word_demo.docx --export-csv data\exports\facture_word_demo.csv
```
## Exécuter les tests

```powershell
python -m pytest -v
```

## Prérequis OCR

Tesseract OCR doit être installé localement avec les langues suivantes :

```text
eng
fra
```

Vérifier l’installation :

```powershell
tesseract --version
tesseract --list-langs
```

## Démonstration avec une image

Générer une facture PNG fictive :

```powershell
python scripts\creer_image_demo.py
```

Analyser l’image et exporter les données :

```powershell
python -m src.comptaprivee.main data\documents\facture_image_demo.png --export-csv data\exports\facture_image_demo.csv
```

## PDF numérisés

Lorsqu’une page PDF contient déjà du texte, ComptaPrivée AI utilise l’extraction directe.

Lorsqu’aucun texte n’est détecté, la page est temporairement convertie en image et analysée localement avec Tesseract OCR. Aucun fichier temporaire n’est conservé après le traitement.

## Interface graphique locale

Lancer l’application :

```powershell
python -m src.comptaprivee.gui
```

L’interface permet de :

- sélectionner un document comptable;
- extraire automatiquement son contenu;
- vérifier et corriger les champs détectés;
- exporter les données validées en CSV;
- conserver toutes les informations localement.

## Traitement de plusieurs factures

ComptaPrivée AI peut analyser plusieurs documents dans une seule
opération et regrouper les données extraites dans un fichier CSV.

Les documents peuvent être de formats différents :

- PDF avec texte sélectionnable;
- PDF numérisé traité par OCR;
- document Word DOCX;
- image PNG, JPG, JPEG, TIFF ou BMP.

Exemple de traitement par lot :

```powershell
python -m src.comptaprivee.main --lot data\documents\facture_demo.pdf data\documents\facture_word_demo.docx data\documents\facture_image_demo.png --export-csv data\exports\factures_lot_demo.csv
```

Le traitement demeure entièrement local. Si un document produit une
erreur, les autres documents continuent d’être analysés et les erreurs
sont affichées dans le résumé.

### Traitement par lot dans l’interface

L’interface graphique permet également de sélectionner plusieurs
documents comptables en utilisant le bouton
`Traiter plusieurs documents`.

Après la sélection des fichiers, l’utilisateur choisit le nom du CSV
regroupé. Le dossier `data/exports` est proposé automatiquement.

L’interface affiche ensuite :

- le nombre de documents sélectionnés;
- le nombre de traitements réussis;
- le nombre de documents en erreur;
- les numéros et les totaux des factures détectées;
- le chemin local du fichier CSV créé.

## Validation comptable automatique

Chaque facture extraite est contrôlée localement avant son export.

Le validateur vérifie notamment :

- la présence du numéro, de la date, du fournisseur et du total;
- l’absence de montants négatifs;
- la cohérence entre le sous-total, la TPS, la TVQ et le total;
- que le total n’est pas inférieur au sous-total.

Trois statuts peuvent être produits :

- `VALIDE` : les données sont complètes et cohérentes;
- `À VÉRIFIER` : certains champs sont manquants, mais l’export reste permis;
- `ERREUR` : une incohérence importante bloque l’export de la facture.

Lors d’un traitement par lot, une facture en erreur est exclue du CSV,
mais les autres documents continuent d’être traités.

### Validation dans l’interface graphique

Après l’analyse d’un document, l’interface affiche son statut comptable :

- `VALIDE` en vert;
- `À VÉRIFIER` en orange;
- `ERREUR` en rouge.

L’utilisateur peut corriger les champs et relancer la validation.
Une erreur comptable désactive automatiquement le bouton d’exportation.