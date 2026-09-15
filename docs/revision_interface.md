# Révision de l'interface locale — septembre 2026

## Bloc 1 : formulaires fiscaux

Les 16 formulaires fiscaux partagent maintenant un corps défilable, une barre
d'actions fixe, des boutons de largeur uniforme répartis selon l'espace disponible,
des textes avec retour à la ligne et des dimensions limitées à celles de l'écran.
Le défilement suit aussi le focus clavier. L'espace principal de l'agent fiscal
est défilable et son menu d'actions utilise plusieurs lignes.

Modules concernés : frais médicaux, scolarité, déficience, accessibilité,
achat d'habitation, aidants 30450/30425/enfant, personne à charge, conjoint,
âge/pension fédéral, âge/retraite Québec, personne vivant seule, cotisations
excédentaires, assurance médicaments et ajustements REER/cotisations/dons.
Les règles de calcul et les formats de sauvegarde ne sont pas modifiés.

## Vérifications effectuées

- Référence avant modification : 1 511 tests réussis, aucun échec ou test ignoré.
- Suite après modification : 1 539 réussis, aucun échec ou test ignoré.
- 28 nouveaux cas : dimensions normales/limites/invalides, défilement,
  focus clavier, nettoyage des bindings, redimensionnement, actions visibles,
  ouverture réelle des formulaires et rejet/effacement d'une saisie médicale invalide.
- Suite complète incluant les tests existants de sauvegarde/rechargement,
  montants nuls, limites et invalides, calculs et interactions entre crédits.
- Application lancée sous Windows; captures locales des 16 formulaires vides
  inspectées à petite taille. Correction du titre tronqué de l'achat d'habitation.
- Facteurs Tk 1, 1,5 et 2 testés sur le composant commun. Cela ne constitue pas
  une validation des réglages DPI Windows 100 %, 150 % et 200 % ni du changement
  d'écran en cours d'utilisation.
- GitHub Actions utilise Xvfb pour exécuter les tests Tkinter sous Linux.
- Captures et journaux restent dans `tmp/`, exclu de Git.

## Audit du reste de l'interface et travaux ouverts

La révision complète de l'application n'est pas terminée. La lecture de `gui.py`
a également relevé des tailles et minima fixes dans les écrans suivants :

| Écran | Point à reprendre |
| --- | --- |
| Accueil | Minimum 900 × 680; barres de commandes horizontales |
| Journal d'audit, éléments à vérifier | Minima fixes et tables larges |
| Historique/exportations, corbeille | Tables, filtres et barres d'actions |
| Paramètres/profil du cabinet | Longs formulaires et petits écrans |
| Tableau de bord et graphiques | Dimensions et commandes des sous-fenêtres |
| Validation des données, dossiers enregistrés | Tables et actions sur petit écran |
| Résultat fiscal, détail du calcul | Tableaux/textes et accès à l'export |

Ces écrans ont été examinés dans le code, mais ne sont pas déclarés validés
visuellement par ce bloc. La validation réelle des DPI Windows, des thèmes,
du contraste et des configurations multi-écrans reste manuelle.

## Procédure à conserver pour les prochains blocs

Ajouter les tests pertinents (normaux, limites, erreurs, non-régression,
persistance et interactions fiscales), puis exécuter `python -m pytest -v`
avec l'environnement du projet. Sous Linux sans écran :
`xvfb-run -a python -m pytest -v`. Aucun test ne doit être désactivé pour
obtenir une suite verte. Signaler les vérifications manuelles restantes.

Avant chaque commit : vérifier les résultats, `git status` et `git diff`,
sélectionner explicitement les fichiers de code/tests/documentation, exclure
toute donnée cliente ou secrète, créer un commit descriptif, pousser vers
`SYou-dataengineer/comptaprivee-ai` et vérifier le résultat de GitHub Actions.
Le compte rendu doit préciser fonctionnalités, design, fichiers, tests et totaux,
commit, push, problèmes ouverts et prochaine étape.
