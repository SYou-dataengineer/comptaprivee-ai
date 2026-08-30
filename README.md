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
## Exécuter les tests

```powershell
python -m pytest -v
```