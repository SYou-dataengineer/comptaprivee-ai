# ComptaPrivée AI

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

## Lancer le programme

```powershell
python src\comptaprivee\main.py
```

## Exécuter les tests

```powershell
python -m pytest -v
```