# ComptaPrivée AI — v1.0.0

ComptaPrivée AI est une application locale de préparation comptable et fiscale.
Cette version (`1.0.0`) traite les dossiers fiscaux **2025**, fédéral
et Québec, dans les profils documentés et validés par le moteur.

## Année fiscale

**Cette version utilise exclusivement les paramètres et règles fiscales 2025.
Elle ne doit pas être utilisée pour calculer une déclaration 2026.**

2025 reste utilisable pour préparer des dossiers tardifs ou des corrections,
avec validation comptable. Le moteur 2026 sera développé et validé séparément.
L'année civile du poste ne choisit jamais automatiquement un barème : l'interface
propose uniquement 2025. Les moteurs annuels refusent les années non supportées.

## Fonctions disponibles

- Extraction locale de PDF, documents Word DOCX et images ; OCR avec Tesseract.
- Validation et correction humaines des champs avant utilisation fiscale.
- Dossiers fiscaux JSON avec identité UUID stable, sauvegarde et rechargement.
- Estimations fédérales et Québec 2025 dans les profils supportés, calculs Decimal,
  détails de calcul et rapports PDF.
- Exports comptables CSV avec protection des champs textuels contre les formules.
- Sauvegarde/restauration locale contrôlée des données applicatives et fiscales.

Un résultat historique rechargé est **non vérifié** : recalculer à partir des faits
avant de l'utiliser. Réexporter le PDF après recalcul.

## Installer et démarrer sous Windows

Prérequis : Windows, **Python 3.12 64 bits** avec Tk, et Tesseract 5 avec les langues
`fra` et `eng` pour l'OCR. La procédure détaillée, les vérifications et le dépannage
figurent dans [Installation Windows](docs/installation_windows.md).

Depuis la racine du dépôt dans PowerShell :

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
tesseract --version
tesseract --list-langs
.\.venv\Scripts\python.exe -m src.comptaprivee.gui
```

L'activation du venv n'est pas nécessaire. Depuis les sources, démarrer depuis la
racine pour résoudre le package Python ; les données sont indépendantes du cwd. Aucun chemin personnel du
développeur n'est requis. Il n'y a pas encore d'installateur ni d'exécutable livré.

La commande d'extraction documentaire reste disponible :

```powershell
.\.venv\Scripts\python.exe -m src.comptaprivee.main --help
```

## Préparer un dossier

1. Ouvrir l'Agent fiscal, saisir le client et initialiser un dossier 2025.
2. Importer les pièces ; reconnaître les feuillets et extraire leurs champs.
3. Vérifier chaque valeur avec le document source, corriger puis valider.
4. Compléter les profils pertinents et les confirmations comptables demandées.
5. Calculer l'estimation ; examiner le détail et les garde-fous.
6. Enregistrer le dossier et exporter le rapport PDF après vérification.
7. Créer une sauvegarde locale via les paramètres et en conserver une copie sûre.

Initialiser un dossier crée une nouvelle identité, même pour un homonyme. Pour
poursuivre un dossier existant, utiliser **Dossiers enregistrés → Ouvrir le dossier**.
Ne pas contourner un blocage fiscal par une valeur estimée ou un faux zéro.

## Limites connues v1.0

Ce logiciel ne reproduit pas tous les cas des déclarations T1/TP-1. La couverture
exacte et les exclusions par bloc sont décrites dans
[le référentiel du moteur 2025](docs/moteur_fiscal_2025.md).

Notamment : travail autonome, location et DPA ont des périmètres bornés ; les
profils complexes doivent être préparés hors moteur. Les blocs interprovincial et
IMR préparent les faits et bloquent le calcul annuel quand les formulaires exclus
sont requis. Le décès n'est supporté que dans son profil limité. Les obligations
sur biens étrangers sont préparées sans production automatique des formulaires.
Le crédit de solidarité est une préparation d'admissibilité/annexe D, sans montant
ajouté au remboursement TP-1 2025. La transmission gouvernementale est désactivée.

La validation humaine reste nécessaire : un test vert n'étend pas le périmètre
fiscal supporté et ne remplace pas la vérification des pièces.

- Année fiscale 2025 uniquement ; aucun moteur 2026.
- Aucun calcul complet T2203/TP-22 ni IMR T691/TP-776.42 ; préparation externe
  obligatoire lorsque les garde-fous l'indiquent.
- Aucun décès complexe ni calcul de succession ; déclaration principale bornée seulement.
- DPA locative limitée aux immeubles déjà détenus avant 2025, catégorie 1 régulière,
  sans acquisition, addition, disposition, récupération ni perte finale.
- Travail autonome pur dans le profil publié ; cumul emploi et travail autonome
  hors périmètre annuel actuel, avec refus explicite.
- Résidence partielle hors estimation annuelle ; certains inventaires peuvent être
  préparés sans autoriser pour autant le calcul annuel.
- Dossiers locaux non chiffrés par l'application ; Tesseract externe requis pour l'OCR.
- Certains formulaires officiels restent à préparer hors application, sans transmission
  automatique. Aucun installateur final n'est livré.

## Données, sauvegardes et confidentialité

Les documents et calculs sont traités localement ; aucun envoi fiscal automatique,
service d'IA distant ou télémétrie fiscale n'est utilisé par l'application.
L'installation des dépendances utilise Internet ; elle ne transmet pas les dossiers.

Sous Windows, la racine utilisateur est `%LOCALAPPDATA%\ComptaPriveeAI`.
Sous cette racine, les JSON fiscaux se trouvent dans `data/dossiers_fiscaux/`, la base comptable dans
`data/comptaprivee.db`, les paramètres dans `data/parametres.json` et le profil dans
`data/profil_comptable.json`. Les exports vont par défaut dans `exports/`.
Les pièces peuvent aussi rester à leur emplacement d'import d'origine.

Les anciens dossiers du dépôt ne sont pas déplacés automatiquement. Voir la
[migration contrôlée](docs/migration_donnees_utilisateur.md) avant de reprendre
un dossier existant. La restauration vise uniquement la racine utilisateur.

Les archives de sauvegarde comprennent la base, les paramètres, le profil et les
JSON fiscaux. **Elles n'incluent pas les pièces originales, les exports, le logo
ni la file de révision OCR.** Conserver séparément les pièces nécessaires à l'audit.
La restauration valide les destinations, le manifeste et le contenu avant les
remplacements ; elle dispose d'un rollback en cas d'erreur.

Les fichiers locaux et ZIP ne sont **pas chiffrés par ComptaPrivée AI**. Leur accès
dépend des protections du poste et des sauvegardes choisies. Les dossiers sensibles
sont exclus de Git ; ne jamais forcer leur ajout ni envoyer une sauvegarde dans une
issue. Consulter [les limites de confidentialité](docs/installation_windows.md#confidentialité)
et [les documents de conformité en cours de validation](docs/legal/README.md).

## Validation et état de release

```powershell
.\.venv\Scripts\python.exe -m pytest --capture=sys -q
```

La configuration limite la collecte à `tests/`. Linux CI exécute la suite complète
avec OCR et GUI sous Xvfb. Windows CI exécute les parcours ciblés de persistance,
JSON, CSV, chemins et GUI avec Python 3.12 et `--capture=sys`. Le détail des preuves
et validations encore nécessaires est dans la [checklist release](docs/release_v1_checklist.md).

- [Changelog](CHANGELOG.md)
- [Validation finale FINAL-C2](docs/validation_final_c2.md)
- [Contrat futur multi-années](docs/architecture_multi_annees.md)
- [Installation et dépendances](docs/installation_windows.md)

Le tag v1.0.0 attend une autorisation explicite. Aucun exécutable final n'est livré.
