# POST-V1-D — installateur Windows local 1.0.0

Premier installateur **de test local**, non signé, non publié. Aucun tag ni
GitHub Release créé. Le tag stable v1.0.0 reste sur 71f7efe.

Suite de l'audit : [validation distribution POST-V1-E](validation_distribution_windows.md).
Mode d'emploi court : [guide utilisateur Windows](guide_windows.md).

## Artefact validé le 1er octobre 2026

| Élément | Valeur |
| --- | --- |
| Source applicative | 7f3fe534a7a336fbd45d6a97387f1723382905db (message GUI C4 inclus) |
| Bundle, une reconstruction | `dist/post-v1-d/ComptaPriveeAI` |
| Compilateur | Inno Setup 6.7.3, portable dans build/tools |
| Installateur | `dist/installer-1.0.0/ComptaPriveeAI-Setup-1.0.0.exe` |
| Taille | 35 406 324 octets (33,77 Mio) |
| SHA-256 | `4F16FD69CA6C29D91366099F3ABE6843352268E5973ED53AF6AA9245A7F94F6D` |
| Horodatage de construction UTC | 2026-10-01T15:09:33.9055417Z |
| SHA-256 du programme dans le bundle | `2A08A7BC67F6E7B5189FD1A3EE64200C9DA2E374F3510A1122B33CD69A18ABA8` |

La configuration Inno et le script de build sont ajoutés par le commit
POST-V1-D ; ils étaient locaux lors de cette compilation. `build-info.json`,
à côté de l'installateur, enregistre le HEAD, l'état Git, les empreintes et la
taille. Les artefacts et diagnostics restent hors Git.

## Construction répétable

Depuis la racine du dépôt, utiliser Python 3.12 x64 et l'environnement de
build décrit dans [prototype_windows.md](prototype_windows.md). Installer les
dépendances de `requirements-build.txt`. Aucun code fiscal n'est modifié.

Installer ou préparer **Inno Setup 6.7.3** depuis le
[site officiel](https://jrsoftware.org/isdl.php). Vérifier la signature
Authenticode valide de **Pyrsys B.V.** avant exécution, conformément aux
[instructions officielles](https://jrsoftware.org/isdl-verify.php).
Le paquet utilisé ici a pour SHA-256
`9C73C3BAE7ED48D44112A0F48E66742C00090BDB5BEF71D9D3C056C66E97B732`.
Son mode `/PORTABLE=1 /CURRENTUSER /NOICONS`, avec destination dans build/tools,
évite l'installation globale du compilateur et les associations de fichiers.

```powershell
.\scripts\build_windows.ps1 -Destination 'dist/post-v1-d'
.\scripts\build_installer.ps1 `
  -Bundle 'dist/post-v1-d/ComptaPriveeAI' `
  -ISCC 'build/tools/inno-6.7.3/ISCC.exe' `
  -Destination 'dist/installer-1.0.0'
```

Les scripts refusent d'écraser les artefacts existants : choisir de nouveaux
sous-dossiers dist pour une construction ultérieure. Le script Inno est
`installer/ComptaPriveeAI.iss`. La version stable vient de pyproject.toml.
La sortie doit rester sous dist et hors du bundle. Les fichiers de données
usuels, .env et répertoires de développement ne sont pas acceptés dans l'entrée.
Ce contrôle complète l'inspection ; ce n'est pas un scanner universel de secrets.
Les dépendances transitives et horodatages ne garantissent pas une identité
binaire entre deux builds ; comparer les empreintes de chaque artefact produit.

## Installation, droits et raccourcis

- Windows 10/11 x64 ; ARM64 exclu de ce premier périmètre.
- Produit : **ComptaPrivée AI**. Le champ éditeur reprend ce nom, faute de
  société légale documentée ; ce champ n'est pas une identité certifiée.
- Installation par défaut pour tous les utilisateurs dans
  `C:\Program Files\ComptaPriveeAI`, avec élévation Windows standard.
- Le choix d'une installation pour l'utilisateur courant est proposé par Inno,
  sans demande d'administration ; ce mode alternatif n'a pas été validé ici.
  Les [constantes auto](https://jrsoftware.org/ishelp/topic_consts.htm) et
  [droits Inno](https://jrsoftware.org/ishelp/topic_setup_privilegesrequired.htm)
  déterminent le chemin et les droits selon ce choix.
- Raccourci Menu Démarrer dans le groupe ComptaPrivée AI ; raccourci Bureau
  facultatif, décoché par défaut. Tous deux pointent vers ComptaPriveeAI.exe,
  sans argument, sans console, avec répertoire de travail du programme.
- Le manifeste du programme a été inspecté : `asInvoker`. Le programme et les
  raccourcis sont lancés sans élévation. Aucun lancement automatique par Setup
  n'est configuré, pour éviter d'ouvrir un dossier avec le compte administrateur.
- Aucune icône produit .ico autorisée n'existait : icônes standard conservées.

## Données, désinstallation et versions futures

Setup n'installe que le bundle. Aucune entrée Files, Run ou UninstallDelete ne
cible `%LOCALAPPDATA%\ComptaPriveeAI`. L'application crée elle-même ce dossier.
La désinstallation enlève les fichiers enregistrés du programme et les
raccourcis, **sans effacer les dossiers fiscaux, SQLite, paramètres, exports,
sauvegardes ou logs**. La suppression éventuelle de données doit rester une
opération volontaire distincte, hors de cet installateur.

AppId stable : `{87DDB3EA-57D0-41CB-9B76-981F4C68E931}`. Le conserver pour 1.0.1
et les mises à jour ultérieures ; version du produit et bundle doivent changer
ensemble. La réinstallation 1.0.0 remplace le programme sans toucher aux données.
Une future 1.0.1 devra être testée avec ses propres fichiers, y compris les
éventuelles dépendances retirées : elle n'a pas été simulée avec un faux numéro.
Aucun auto-update. Fermer l'application avant installation/désinstallation ;
Inno peut demander sa fermeture via Restart Manager, sans mode de fermeture forcée.

## Dépendances externes et signature

Tesseract n'est pas embarqué. Il est requis uniquement pour l'OCR images/scans,
avec fra+eng recommandé. Les PDF textuels fonctionnent sans lui. Aucun
téléchargement automatique. Word/Excel ne sont pas embarqués et ne sont pas
nécessaires au lancement ; les conversions COM demandent l'application Office
correspondante et signalent son absence.

Installateur et programme non signés. Aucun blocage SmartScreen/WDAC n'a été
observé lors de ce cycle ; cela ne garantit pas l'acceptation sur une autre
machine. Aucune protection n'a été modifiée ou contournée. Le blocage r3 et le
refus ZIP P2 restent décrits dans [prototype_windows.md](prototype_windows.md).
Envisager une signature de code avant distribution commerciale publique.

## Validation locale réalisée

Profil exclusivement fictif : `tmp/POST-V1-D profil fictif/ComptaPriveeAI`,
substitué à LOCALAPPDATA pour les lancements, sans changement de registre des
chemins utilisateur. Aucun dossier réel utilisé. Le programme est installé
dans le vrai Program Files ; les raccourcis communs ont été créés pour le test.

| Contrôle | Résultat |
| --- | --- |
| Installation et réinstallation 1.0.0 | code sortie 0 |
| Profil utilisateur inexistant | pas créé par l'installateur ; création par l'application |
| Profil existant | empreintes de tous les fichiers identiques après réinstallation |
| Lancement direct et par Menu Démarrer/Bureau | GUI présente, fermeture normale, code 0 |
| Diagnostic du programme installé | faits fiscaux fictifs 2025, PDF, CSV, JSON, trois ZIP et restauration réussis |
| OCR accessible | fra+eng OK |
| Tesseract retiré du PATH sur un profil neuf | message clair, PDF textuel et GUI fonctionnels |
| Office absent | échec COM simulé correctement signalé ; Office réellement absent non testé sur ce poste |
| Désinstallation | code 0, fichiers et raccourcis retirés ; log « Removed all? Yes », sans redémarrage |
| Données après désinstallation | intégralement conservées, empreintes identiques |
| Réinstallation après désinstallation | code 0, empreintes identiques avant relancement |
| Dossier fiscal après relancement | même case_id fictif, accessible et recalculé |

Pendant la désinstallation, le répertoire programme a brièvement subsisté le
temps du nettoyage différé d'Inno ; son journal confirme ensuite le retrait.
La dernière installation reste présente pour les essais ; aucune instance de
l'application n'est laissée ouverte.

Inspection : les **1 016 fichiers** installés du payload correspondent aux
empreintes du bundle après usage. Seuls `unins000.exe` et `unins000.dat` sont
ajoutés. Aucune DB, archive client, .env, dépôt Git ou suite de tests détectée.
Les modèles DOCX et base_library.zip sont des ressources légitimes. Cette
inspection n'est pas une certification exhaustive des binaires tiers.
Le code GUI embarqué a été lu dans l'archive PyInstaller : message C4 confirmé.
La table PYZ ne contient pas pytest/tests ; la recherche de signatures usuelles
de jetons GitHub et clés privées dans les ressources texte n'a rien détecté.

Validation source : **38 tests ciblés réussis, 5 warnings SWIG/PyMuPDF**.
Garde-fous du script vérifiés : sortie hors dist refusée, sortie dans le bundle
refusée, installateur existant préservé. `git diff --check` propre. Pas de full
suite locale : seuls packaging, configuration et documentation sont modifiés.
La CI Linux/Windows valide le commit de ces fichiers.

**GO pour essais Windows locaux contrôlés. NO-GO pour distribution commerciale
publique à ce stade** : pas de signature ni de validation sur une machine
propre indépendante. Les limites v1 et prérequis externes restent applicables.
Aucune GitHub Release ni modification du tag stable.
